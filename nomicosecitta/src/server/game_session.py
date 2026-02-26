import asyncio
from src.common.constants import (
    GAME_MODE_CLASSIC, GAME_MODE_CLASSIC_PLUS,
    TARGET_SCORE, VOTING_DURATION, SCORE_DISPLAY_DELAY,
    POINTS_UNIQUE_CATEGORY, POINTS_UNIQUE_WORD, POINTS_SHARED_WORD, POINTS_INVALID,
)
from src.common.message import Message, MessageType, GameState
from src.server.round_manager import RoundManager


class GameSession:
    """
    Handle game logic.
    """

    def __init__(self, server):
        self.server = server
        self.state = GameState.LOBBY

        # Round state (reset each round)
        self.current_round: RoundManager | None = None
        self.received_answers: dict[str, dict] = {}
        self.received_votes: dict[str, dict] = {}
        self.round_data: dict[str, dict] = {}
        self.words_to_vote: dict[str, dict] = {}

        # Session state (persists across rounds)
        self.scores: dict[str, int] = {}
        self.old_letters: set[str] = set()
        self.current_round_number: int = 0
        self.current_settings: dict = {}
        self.round_time: int = 60

        # Async tasks
        self._timer_task: asyncio.Task | None = None
        self._voting_timer_task: asyncio.Task | None = None

    async def start_game(self, request_username: str, settings: dict):
        """Handle game start request from admin."""
        if self.state != GameState.LOBBY:
            return False, "Game already in progress"

        if request_username != self.server.get_admin():
            return False, "Only the admin can start the game"

        if self.server.get_active_count() < 1:
            return False, "Not enough players"

        peermap_msg = Message(
            type=MessageType.EVT_PEER_MAP,
            sender="SERVER",
            payload={"peermap": self.server.get_peer_map()}
        )
        await self.server.broadcast(peermap_msg)
        print(f"[GAME] Peermap sent: {peermap_msg.payload['peermap']}")

        for username in self.server.get_active_usernames():
            self.scores.setdefault(username, 0)

        self.current_settings = dict(settings)
        await self._launch_round(settings)
        return True, "Game started"

    async def _launch_round(self, settings: dict):
        """Build and broadcast a new round."""
        self.state = GameState.WAITING_INPUT
        self._reset_round_state()

        mode = settings.get("mode", GAME_MODE_CLASSIC)
        num_extra = int(settings.get("num_extra_categories", 2))
        aggregated = self.server.get_aggregated_categories(num_extra)

        if mode == GAME_MODE_CLASSIC:
            final_categories = ["Nomi", "Cose", "Città"]
        elif mode == GAME_MODE_CLASSIC_PLUS:
            final_categories = ["Nomi", "Cose", "Città"] + aggregated
        else:
            final_categories = aggregated if aggregated else ["Nomi", "Cose", "Città"]

        settings_for_round = dict(settings)
        settings_for_round["selected_categories"] = (
            aggregated if mode != GAME_MODE_CLASSIC else []
        )
        self.server.reset_category_votes()

        self.current_round = RoundManager(settings_for_round, self.old_letters)
        self.current_round.categories = final_categories
        self.old_letters.add(self.current_round.letter)
        self.round_time = int(settings.get("round_time", 60))
        self.current_round_number += 1

        print(
            f"[GAME] Round {self.current_round_number}: "
            f"letter={self.current_round.letter}, categories={final_categories}"
        )

        await self.server.broadcast(Message(
            type=MessageType.EVT_ROUND_START,
            sender="SERVER",
            payload={
                "letter": self.current_round.letter,
                "categories": final_categories,
                "duration": self.round_time,
                "round_number": self.current_round_number,
            }
        ))

        self._timer_task = asyncio.create_task(
            self.current_round.start_timer(callback_on_end=self._end_round)
        )

    async def receive_answers(self, username: str, words: dict):
        if self.state != GameState.WAITING_INPUT:
            print(f"[WARN] Answers from {username} rejected: wrong state ({self.state}).")
            return

        self.received_answers[username] = words
        print(f"[GAME] Answers received from {username}. "
              f"({len(self.received_answers)}/{self.server.get_active_count()})")

        if len(self.received_answers) >= self.server.get_active_count():
            print("[GAME] All players submitted — cancelling timer.")
            if self._timer_task and not self._timer_task.done():
                self._timer_task.cancel()
            self._process_initial_validation()
            await self._start_voting_phase()

    def _process_initial_validation(self):
        target_letter = self.current_round.letter.upper()

        for category in self.current_round.categories:
            self.round_data[category] = {}
            self.words_to_vote[category] = {}

            for user, user_words in self.received_answers.items():
                word = str(user_words.get(category, "")).strip().upper()
                if not word or not word.startswith(target_letter):
                    self.round_data[category][user] = {
                        "word": word,
                        "status": "INVALID",
                        "score": 0,
                    }
                else:
                    self.round_data[category][user] = {
                        "word": word,
                        "status": "PENDING_VOTE",
                        "score": 0,
                    }
                    self.words_to_vote[category][user] = word

        print(f"[GAME] Initial validation done. words_to_vote={self.words_to_vote}")

    async def _start_voting_phase(self):
        self.state = GameState.VOTING

        await self.server.broadcast(Message(
            type=MessageType.EVT_VOTING_START,
            sender="SERVER",
            payload={"words_to_vote": self.words_to_vote}
        ))

        self._voting_timer_task = asyncio.create_task(
            self._voting_timeout()
        )

    async def _voting_timeout(self):
        try:
            await asyncio.sleep(VOTING_DURATION)
            if self.state == GameState.VOTING:
                print("[GAME] Voting timer expired — forcing finalization.")
                await self._finalize_round()
        except asyncio.CancelledError:
            pass

    async def _end_round(self):
        print("[GAME] Input timer expired.")
        if self.state != GameState.WAITING_INPUT:
            return

        self.state = GameState.VOTING
        await self.server.broadcast(Message(
            type=MessageType.EVT_ROUND_END,
            sender="SERVER",
            payload={"reason": "TIME_UP"}
        ))
        self._process_initial_validation()
        await self._start_voting_phase()

    async def receive_votes(self, username: str, votes: dict):
        if self.state != GameState.VOTING:
            print(f"[WARN] Votes from {username} rejected: wrong state ({self.state}).")
            return

        self.received_votes[username] = votes
        print(f"[GAME] Votes received from {username}. "
              f"({len(self.received_votes)}/{self.server.get_active_count()})")

        if len(self.received_votes) >= self.server.get_active_count():
            print("[GAME] All players voted — finalizing round.")
            if self._voting_timer_task and not self._voting_timer_task.done():
                self._voting_timer_task.cancel()
            await self._finalize_round()

    def _aggregate_votes(self) -> dict[str, dict[str, bool]]:
        """
        Apply majority rule to the collected votes.

        Rules:
          - Words already marked INVALID by syntactic check → always False.
          - PENDING_VOTE words → majority of received votes (True > 50 %).
          - PENDING_VOTE words with no votes received → default True (benefit of doubt).
        """
        tally: dict[str, dict[str, list[bool]]] = {}
        for category, users in self.round_data.items():
            tally[category] = {user: [] for user in users}

        for voter_votes in self.received_votes.values():
            for category, user_votes in voter_votes.items():
                if category not in tally:
                    continue
                for target_user, is_valid in user_votes.items():
                    if target_user in tally[category]:
                        tally[category][target_user].append(bool(is_valid))

        # Resolve majority
        result: dict[str, dict[str, bool]] = {}
        for category, users in tally.items():
            result[category] = {}
            for user, vote_list in users.items():
                if self.round_data[category][user]["status"] == "INVALID":
                    result[category][user] = False
                elif not vote_list:
                    result[category][user] = True
                else:
                    valid_count = sum(1 for v in vote_list if v)
                    result[category][user] = valid_count > len(vote_list) / 2

        print(f"[GAME] Aggregated votes: {result}")
        return result

    def _calculate_scores(self, validated: dict[str, dict[str, bool]]) -> dict[str, int]:
        """
        Assign points according to the scoring rules in the report:
          - 15 pts → only player with a valid answer in the category
          - 10 pts → valid, word unique among all valid answers in the category
          -  5 pts → valid, but same word as at least one other valid answer
          -  0 pts → invalid
        """
        round_scores: dict[str, int] = {
            user: 0 for user in self.server.get_active_usernames()
        }

        for category, user_valid in validated.items():
            valid_words: dict[str, str] = {}
            for user, is_valid in user_valid.items():
                if is_valid:
                    word = self.round_data[category][user]["word"]
                    valid_words[user] = word

            num_valid = len(valid_words)

            for user, word in valid_words.items():
                if num_valid == 1:
                    pts = POINTS_UNIQUE_CATEGORY
                else:
                    same_word_count = sum(
                        1 for w in valid_words.values() if w == word
                    )
                    pts = POINTS_SHARED_WORD if same_word_count > 1 else POINTS_UNIQUE_WORD

                round_scores[user] = round_scores.get(user, 0) + pts
                self.round_data[category][user]["score"] = pts

        print(f"[GAME] Round scores: {round_scores}")
        return round_scores

    async def _finalize_round(self):
        """
        Aggregate votes → calculate scores → broadcast → check win condition.
        """
        if self.state != GameState.VOTING:
            return  # Guard against double-call

        self.state = GameState.SCORING

        validated = self._aggregate_votes()
        round_scores = self._calculate_scores(validated)

        for user, pts in round_scores.items():
            self.scores[user] = self.scores.get(user, 0) + pts

        print(f"[GAME] Global scores: {self.scores}")

        await self.server.broadcast(Message(
            type=MessageType.EVT_SCORE_UPDATE,
            sender="SERVER",
            payload={
                "round_scores": round_scores,
                "scores": dict(self.scores),
                "round_data": self.round_data,
                "round_number": self.current_round_number,
            }
        ))

        winner = next(
            (user for user, score in self.scores.items() if score >= TARGET_SCORE),
            None
        )

        if winner:
            self.state = GameState.ENDED
            print(f"[GAME] {winner} wins with {self.scores[winner]} points!")
            await self.server.broadcast(Message(
                type=MessageType.EVT_GAME_OVER,
                sender="SERVER",
                payload={
                    "scores": dict(self.scores),
                    "winner": winner,
                }
            ))
        else:
            await asyncio.sleep(SCORE_DISPLAY_DELAY)
            await self._launch_round(self.current_settings)

    def _reset_round_state(self):
        self.received_answers = {}
        self.received_votes = {}
        self.round_data = {}
        self.words_to_vote = {}

    async def handle_player_disconnection(self, username: str):
        """Handle a player dropping mid-game."""
        print(f"[GAME] Player {username} disconnected during state {self.state}.")
        active_count = self.server.get_active_count()

        if self.state == GameState.WAITING_INPUT:
            if len(self.received_answers) >= active_count and active_count > 0:
                if self._timer_task and not self._timer_task.done():
                    self._timer_task.cancel()
                self._process_initial_validation()
                await self._start_voting_phase()

        elif self.state == GameState.VOTING:
            if len(self.received_votes) >= active_count and active_count > 0:
                if self._voting_timer_task and not self._voting_timer_task.done():
                    self._voting_timer_task.cancel()
                await self._finalize_round()

    async def sync_reconnecting_client(self, client_handler):
        """Send current state to a reconnecting client."""
        await client_handler.send(Message(
            type=MessageType.EVT_PEER_MAP,
            sender="SERVER",
            payload={"peermap": self.server.get_peer_map()}
        ).to_bytes())

        await client_handler.send(Message(
            type=MessageType.EVT_ROUND_START,
            sender="SERVER",
            payload={
                "letter": self.current_round.letter,
                "categories": self.current_round.categories,
                "duration": 0,
                "round_number": self.current_round_number,
            }
        ).to_bytes())

        if self.state == GameState.VOTING:
            await client_handler.send(Message(
                type=MessageType.EVT_VOTING_START,
                sender="SERVER",
                payload={"words_to_vote": self.words_to_vote}
            ).to_bytes())