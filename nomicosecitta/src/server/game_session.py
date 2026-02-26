import asyncio
import time
from src.common.constants import GAME_MODE_CLASSIC, GAME_MODE_CLASSIC_PLUS
from src.common.message import Message, MessageType, GameState
from src.server.round_manager import RoundManager

class GameSession:
    """
    Handle game logic.
    """
    def __init__(self, server):
        self.server = server
        self.state = GameState.LOBBY
        self.old_letters = set()
        self.current_round = None
        self.received_answers = {}
        self.round_data = {}
        self.words_to_vote = {}
        self.current_round_number = 0
        self._timer_task = None
        self.round_start_time = 0.0

    async def start_game(self, request_username, settings):
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
            payload={
                "peermap": self.server.get_peer_map()
            }
        )
        await self.server.broadcast(peermap_msg)
        print(f"[GAME] Peermap sent: {peermap_msg.payload['peermap']}")

        self.state = GameState.WAITING_INPUT

        mode = settings.get("mode", GAME_MODE_CLASSIC)
        num_extra = int(settings.get("num_extra_categories", 2))

        aggregated = self.server.get_aggregated_categories(num_extra)

        if mode == GAME_MODE_CLASSIC:
            final_categories = ["Nomi", "Cose ", "Città"]
        elif mode == GAME_MODE_CLASSIC_PLUS:
            final_categories = ["Nomi", "Cose ", "Città"] + aggregated
        else:
            final_categories = aggregated if aggregated else ["Nomi", "Cose ", "Città"]

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
            f"[GAME] Starting round {self.current_round_number}: "
            f"Letter {self.current_round.letter}, Categories {final_categories}"
        )
        
        start_msg = Message(
            type=MessageType.EVT_ROUND_START,
            sender="SERVER",
            payload={
                "letter": self.current_round.letter,
                "categories": final_categories,
                "duration": self.round_time,
                "round_number": self.current_round_number,
            }
        )
        await self.server.broadcast(start_msg)
        self.round_start_time = time.time()
        self._timer_task = asyncio.create_task(
            self.current_round.start_timer(callback_on_end=self._end_round)
        )

        return True, "Game started"

    async def receive_answers(self, username, words):
        if self.state != GameState.WAITING_INPUT:
            print(f"[WARN] Submit of {username} rejected: outside time limit.")
            return

        self.received_answers[username] = words
        print(f"[GAME] Received answers from {username}.")
        total_players = self.server.get_active_count()
        
        if len(self.received_answers) >= total_players:
            print("[GAME] All players submitted early!")
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
                        "score": 0
                    }
                else:
                    self.round_data[category][user] = {
                        "word": word, 
                        "status": "PENDING_VOTE",
                        "score": 0
                    }
                    self.words_to_vote[category][user] = word
        
        print(f"[GAME] Initial validation completed. Data: {self.round_data}")

    async def _start_voting_phase(self):
        self.state = GameState.VOTING
        vote_msg = Message(
            type=MessageType.EVT_VOTING_START,
            sender="SERVER",
            payload={"words_to_vote": self.words_to_vote}
        )
        await self.server.broadcast(vote_msg)
        
        #TODO: move after vote processing is implemented
        #self.received_answers= {}
        #self.words_to_vote = {}

    async def _end_round(self):
        """End time: change WAITING_INPUT -> VOTING/SCORING"""
        print("[GAME] Time is up!")
        self.state = GameState.VOTING

        end_msg = Message(
            type=MessageType.EVT_ROUND_END,
            sender="SERVER",
            payload={"reason": "TIME_UP"}
        )
        await self.server.broadcast(end_msg)

        self._process_initial_validation()
        await self._start_voting_phase()

    async def handle_player_disconnection(self, username):
        """Manage player disconnection during the game."""
        print(f"[GAME] Handling disconnection of {username} during state {self.state}")
        active_count = self.server.get_active_count()

        if self.state == GameState.WAITING_INPUT:
            if len(self.received_answers) >= active_count:
                if self._timer_task and not self._timer_task.done():
                    self._timer_task.cancel()
                self._process_initial_validation()
                await self._start_voting_phase()

        elif self.state == GameState.VOTING:
                #TODO: Implement early vote processing if needed
                pass

    async def sync_reconnecting_client(self, client_handler):
        peermap_msg = Message(
            type=MessageType.EVT_PEER_MAP,
            sender="SERVER",
            payload={"peermap": self.server.get_peer_map()}
        )
        await self.server.broadcast(peermap_msg)
        
        time_passed = time.time() - self.round_start_time
        time_left = int(self.round_time - time_passed)
        if time_left < 0:
            time_left = 0

        sync_msg = Message(
            type=MessageType.EVT_ROUND_START,
            sender="SERVER",
            payload={
                "letter": self.current_round.letter,
                "categories": self.current_round.categories,
                "duration": time_left,
                "round_number": self.current_round_number
            }
        )
        await client_handler.send(sync_msg.to_bytes())

        if self.state == GameState.VOTING:
            vote_msg = Message(
                type=MessageType.EVT_VOTING_START,
                sender="SERVER",
                payload={"words_to_vote": self.words_to_vote}
            )
            await client_handler.send(vote_msg.to_bytes())
