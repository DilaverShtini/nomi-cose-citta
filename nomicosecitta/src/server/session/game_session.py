import asyncio
import time

from src.common.constants import (
    GAME_MODE_CLASSIC, GAME_MODE_CLASSIC_PLUS, GAME_MODE_FREE,
    TARGET_SCORE, SCORE_DISPLAY_DELAY,
    VOTING_SMALL_DURATION, VOTING_MEDIUM_DURATION,
    VOTING_LONG_DURATION, VOTING_LONG_LONG_DURATION
)
from src.common.message import Message, MessageType, GameState
from src.server.round_manager import RoundManager
from src.server.session.answer_validator import AnswerValidator
from src.server.session.voting_aggregator import VotingAggregator
from src.server.session.scoring_engine import ScoringEngine
from src.server.session.timer_manager import TimerManager


class GameSession:
    """
    Handle game logic.
    """

    def __init__(self, server):
        self.server = server

        self._validator  = AnswerValidator()
        self._aggregator = VotingAggregator()
        self._scorer     = ScoringEngine()
        self._timers     = TimerManager()

        self.current_round:    RoundManager | None = None
        self.received_answers: dict[str, dict]     = {}
        self.received_votes:   dict[str, dict]     = {}
        self.round_data:       dict[str, dict]     = {}
        self.words_to_vote:    dict[str, dict]     = {}

        self.state                   = GameState.LOBBY
        self.scores:                 dict[str, int] = {}
        self.old_letters:            set[str]       = set()
        self.current_round_number:   int            = 0
        self.current_settings:       dict           = {}
        self.round_time:             int            = 60
        self.round_start_time:       float          = 0.0
        self.current_voting_duration: int           = VOTING_SMALL_DURATION
        self.voting_start_time:      float          = 0.0

    #  Public API

    async def start_game(self, request_username: str, settings: dict):
        """Gestisce la richiesta di avvio partita inviata dall'admin."""
        if self.state != GameState.LOBBY:
            return False, "Game already in progress"
        if request_username != self.server.get_admin():
            return False, "Only the admin can start the game"
        if self.server.get_active_count() < 1:
            return False, "Not enough players"

        mode      = settings.get("mode", GAME_MODE_CLASSIC)
        num_extra = int(settings.get("num_extra_categories", 2))
        if mode != GAME_MODE_CLASSIC:
            if not self.server.get_aggregated_categories(num_extra):
                return (
                    False,
                    "At least one extra category must be selected by the players "
                    "before starting in this game mode.",
                )

        await self.server.broadcast(Message(
            type=MessageType.EVT_PEER_MAP,
            sender="SERVER",
            payload={"peermap": self.server.get_peer_map()},
        ))
        print(f"[SESSION] Peermap sent: {self.server.get_peer_map()}")

        for username in self.server.get_active_usernames():
            self.scores.setdefault(username, 0)

        self.current_settings = dict(settings)
        self.server._expected_players = set(self.server.get_active_usernames())
        self.server.save_state()

        await self._launch_round(settings)
        return True, "Game started"

    async def receive_answers(self, username: str, words: dict):
        if self.state != GameState.WAITING_INPUT:
            print(f"[SESSION] Answers from {username} rejected (state={self.state}).")
            return

        self.received_answers[username] = words
        print(f"[SESSION] Answers from {username} "
              f"({len(self.received_answers)}/{self.server.get_active_count()})")

        if len(self.received_answers) >= self.server.get_active_count():
            print("[SESSION] All players submitted — cancelling timer.")
            self._timers.cancel_round_timer()
            self._run_initial_validation()
            await self._start_voting_phase()

    async def receive_votes(self, username: str, votes: dict):
        if self.state != GameState.VOTING:
            print(f"[SESSION] Votes from {username} rejected (state={self.state}).")
            return

        self.received_votes[username] = votes
        print(f"[SESSION] Votes from {username} "
              f"({len(self.received_votes)}/{self.server.get_active_count()})")
        self.server.save_state()

        if len(self.received_votes) >= self.server.get_active_count():
            print("[SESSION] All players voted — finalising round.")
            self._timers.cancel_voting_timer()
            await self._finalise_round()

    async def handle_player_disconnection(self, username: str):
        print(f"[SESSION] {username} disconnected during state={self.state}.")
        if getattr(self.server, 'is_shutting_down', False):
            return

        active_count = self.server.get_active_count()
        if active_count == 0:
            asyncio.create_task(self._delayed_reset())
            return

        if self.state == GameState.WAITING_INPUT:
            if len(self.received_answers) >= active_count:
                self._timers.cancel_round_timer()
                self._run_initial_validation()
                await self._start_voting_phase()

        elif self.state == GameState.VOTING:
            if len(self.received_votes) >= active_count:
                self._timers.cancel_voting_timer()
                await self._finalise_round()

    async def sync_reconnecting_client(self, client_handler):
        await self.server.broadcast(Message(
            type=MessageType.EVT_PEER_MAP,
            sender="SERVER",
            payload={"peermap": self.server.get_peer_map()},
        ))

        if self.state == GameState.WAITING_INPUT:
            elapsed   = time.time() - self.round_start_time
            time_left = max(0, int(self.round_time - elapsed))
            await client_handler.send(Message(
                type=MessageType.EVT_ROUND_START,
                sender="SERVER",
                payload={
                    "letter":       self.current_round.letter,
                    "categories":   self.current_round.categories,
                    "duration":     time_left,
                    "round_number": self.current_round_number,
                    "is_recovery":  True,
                },
            ).to_bytes())

        if self.scores:
            await client_handler.send(Message(
                type=MessageType.EVT_SCORE_UPDATE,
                sender="SERVER",
                payload={
                    "round_scores": {},
                    "scores": dict(self.scores),
                    "round_data": {},
                    "round_number": self.current_round_number,
                    "is_recovery": True,
                }
            ).to_bytes())

        if self.state == GameState.VOTING:
            elapsed   = time.time() - self.voting_start_time
            time_left = max(0, int(self.current_voting_duration - elapsed))
            await client_handler.send(Message(
                type=MessageType.EVT_VOTING_START,
                sender="SERVER",
                payload={
                    "words_to_vote": self.words_to_vote,
                    "duration":      time_left,
                    "is_recovery":  True,
                    "letter":        self.current_round.letter,
                    "round_number":  self.current_round_number
                },
            ).to_bytes())

    def reset(self):
        self.state = GameState.LOBBY
        self.old_letters.clear()
        self.current_round = None
        self.scores.clear()
        self.current_round_number = 0
        self._reset_round_state()
        self._timers.cancel_all()
        self.server.reset_category_votes()

    def restore_from_state(self, session_data: dict):
        print("[SESSION] Restoring state from snapshot…")

        state_name = session_data.get("state", "LOBBY")
        self.state                   = GameState[state_name]
        self.current_round_number    = session_data.get("round_number", 0)
        self.scores                  = session_data.get("scores", {})
        self.old_letters             = set(session_data.get("old_letters", []))
        self.round_time              = session_data.get("round_time", 60)
        self.current_settings        = session_data.get("current_settings", {})
        self.current_voting_duration = session_data.get(
            "current_voting_duration", VOTING_SMALL_DURATION)

        round_info = session_data.get("current_round")
        if round_info:
            self.current_round            = RoundManager(self.current_settings, self.old_letters)
            self.current_round.letter     = round_info.get("letter", "A")
            self.current_round.categories = round_info.get("categories", [])

        self.received_answers = session_data.get("received_answers", {})
        self.received_votes   = session_data.get("received_votes",   {})
        self.round_data       = session_data.get("round_data",       {})
        self.words_to_vote    = session_data.get("words_to_vote",    {})

        DOWNTIME_COMPENSATION = 5.0
        now = time.time()

        saved_round_start = session_data.get("round_start_time", 0)
        if saved_round_start > 0:
            self.round_start_time = saved_round_start + DOWNTIME_COMPENSATION
        else:
            self.round_start_time = now - session_data.get("round_time_passed", 0)

        saved_voting_start = session_data.get("voting_start_time", 0)
        if saved_voting_start > 0:
            self.voting_start_time = saved_voting_start + DOWNTIME_COMPENSATION
        else:
            self.voting_start_time = now - session_data.get("voting_time_passed", 0)

        round_remaining  = 0.0
        voting_remaining = 0.0

        if self.state == GameState.WAITING_INPUT:
            passed = now - self.round_start_time
            round_remaining = max(
                0.0, min(float(self.round_time) - passed, float(self.round_time))
            )

        elif self.state == GameState.VOTING:
            passed = now - self.voting_start_time
            voting_remaining = max(
                0.0,
                min(float(self.current_voting_duration) - passed,
                    float(self.current_voting_duration)),
            )

        self._timers.restore(
            state_name       = self.state.name,
            round_remaining  = round_remaining,
            voting_remaining = voting_remaining,
            round_callback   = self._end_round,
            voting_callback  = self._on_voting_timeout,
        )

        print(f"[SESSION] Session restored. Status: {self.state.name}")

    async def _launch_round(self, settings: dict):
        self.state = GameState.WAITING_INPUT
        self._reset_round_state()

        mode      = settings.get("mode", GAME_MODE_CLASSIC)
        num_extra = int(settings.get("num_extra_categories", 1))

        aggregated = (
            settings.get("selected_categories")
            or self.server.get_aggregated_categories(num_extra)
        )
        self.current_settings["selected_categories"] = aggregated

        if mode == GAME_MODE_CLASSIC:
            final_categories = ["Name", "Things", "Cities"]
        elif mode == GAME_MODE_CLASSIC_PLUS:
            final_categories = ["Name", "Things", "Cities"] + aggregated
        elif mode == GAME_MODE_FREE:
            final_categories = aggregated

        settings_for_round = {
            **settings,
            "selected_categories": aggregated if mode != GAME_MODE_CLASSIC else [],
        }
        self.server.reset_category_votes()

        self.current_round            = RoundManager(settings_for_round, self.old_letters)
        self.current_round.categories = final_categories
        self.old_letters.add(self.current_round.letter)
        self.round_time            = int(settings.get("round_time", 60))
        self.current_round_number += 1
        self.round_start_time      = time.time()
        self.server.save_state()

        print(f"[SESSION] Round {self.current_round_number}: "
              f"letter={self.current_round.letter}, categories={final_categories}")

        self._timers.start_round_timer(
            self.current_round.start_timer(callback_on_end=self._end_round)
        )

        await self.server.broadcast(Message(
            type=MessageType.EVT_ROUND_START,
            sender="SERVER",
            payload={
                "letter":       self.current_round.letter,
                "categories":   final_categories,
                "duration":     self.round_time,
                "round_number": self.current_round_number,
            },
        ))

    def _run_initial_validation(self):
        self.round_data, self.words_to_vote = self._validator.validate(
            self.received_answers,
            self.current_round.categories,
            self.current_round.letter,
        )
        print(f"[SESSION] Validation done. Sending words to vote.")

    def _get_voting_duration(self) -> int:
        n = len(self.current_round.categories)
        if n <= 3: return VOTING_SMALL_DURATION
        if n <= 5: return VOTING_MEDIUM_DURATION
        if n <= 7: return VOTING_LONG_DURATION
        return VOTING_LONG_LONG_DURATION

    async def _start_voting_phase(self):
        self.state                   = GameState.VOTING
        self.voting_start_time       = time.time()
        self.current_voting_duration = self._get_voting_duration()

        await self.server.broadcast(Message(
            type=MessageType.EVT_VOTING_START,
            sender="SERVER",
            payload={
                "words_to_vote": self.words_to_vote,
                "duration":      self.current_voting_duration,
            },
        ))
        self.server.save_state()
        self._timers.start_voting_timer(
            self.current_voting_duration, self._on_voting_timeout
        )

    async def _on_voting_timeout(self):
        if self.state == GameState.VOTING:
            print("[SESSION] Voting timer expired.")
            await self._finalise_round()

    async def _end_round(self):
        if self.state != GameState.WAITING_INPUT:
            return
        await self.server.broadcast(Message(
            type=MessageType.EVT_ROUND_END,
            sender="SERVER",
            payload={"reason": "TIME_UP"},
        ))

        async def _wait_for_stragglers():
            await asyncio.sleep(3)
            if self.state == GameState.WAITING_INPUT:
                self._run_initial_validation()
                await self._start_voting_phase()

        asyncio.create_task(_wait_for_stragglers())

    async def _finalise_round(self):
        if self.state != GameState.VOTING:
            return

        self.state = GameState.SCORING

        try:
            validated    = self._aggregator.aggregate(self.round_data, self.received_votes)
            round_scores = self._scorer.calculate_points(
                self.round_data, validated, self.server.get_active_usernames()
            )
        except Exception as e:
            import traceback
            print(f"[SESSION] CRITICAL ERROR during scoring: {e}")
            traceback.print_exc()
            self.reset()
            self.server.save_state()
            return

        for user, pts in round_scores.items():
            self.scores[user] = self.scores.get(user, 0) + pts

        self.server.save_state()

        await self.server.broadcast(Message(
            type=MessageType.EVT_SCORE_UPDATE,
            sender="SERVER",
            payload={
                "round_scores": round_scores,
                "scores":       dict(self.scores),
                "round_data":   self.round_data,
                "round_number": self.current_round_number,
                "is_recovery": False
            },
        ))

        winner = next(
            (u for u, s in self.scores.items() if s >= TARGET_SCORE), None
        )
        if winner:
            self.state = GameState.ENDED
            print(f"[SESSION] {winner} wins!")
            await self.server.broadcast(Message(
                type=MessageType.EVT_GAME_OVER,
                sender="SERVER",
                payload={"scores": dict(self.scores), "winner": winner},
            ))
            self.reset()
            self.server.save_state()
        else:
            await asyncio.sleep(SCORE_DISPLAY_DELAY)
            await self._launch_round(self.current_settings)

    def _reset_round_state(self):
        self.received_answers = {}
        self.received_votes   = {}
        self.round_data       = {}
        self.words_to_vote    = {}

    async def _delayed_reset(self):
        await asyncio.sleep(2)
        if (self.server.get_active_count() == 0
                and not getattr(self.server, 'is_shutting_down', False)):
            print("[SESSION] No players remaining — resetting to LOBBY.")
            self.reset()
            self.server.save_state()
