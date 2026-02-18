import asyncio
import random
import string
from src.common.message import Message, MessageType, GameState
from src.common.constants import DEFAULT_CATEGORIES, DEFAULT_ROUND_TIME

class GameEngine:
    """
    Handle game logic.
    """
    def __init__(self, server):
        self.server = server
        self.state = GameState.LOBBY
        self.current_letter = None
        self.old_letters = set()
        self.current_categories = []
        self.round_time = DEFAULT_ROUND_TIME
        self._timer_task = None

    async def start_game(self, request_username, settings):
        """Handle game start request from admin."""

        if self.state != GameState.LOBBY:
            return False, "Game already in progress"

        if request_username != self.server.get_admin():
            return False, "Only the admin can start the game"

        if self.server.get_active_count() < 1:
            return False, "Not enough players"

        self.state = GameState.PLAYING

        self.current_letter = random.choice(string.ascii_uppercase)
        while self.current_letter in self.old_letters:
            self.current_letter = random.choice(string.ascii_uppercase)
        self.old_letters.add(self.current_letter)

        self.round_time = int(settings["round_time"])
        
        extra = settings.get("selected_categories", [])
        mode = settings.get("mode", "classic")
        
        if mode == "classic":
                self.current_categories = ["Name", "Things", "Cities"]
        elif mode == "classic_plus":
                self.current_categories = ["Name", "Things", "Cities"] + extra
        elif mode == "free":
                self.current_categories = extra 

        print(f"[GAME] Inizio Round: Lettera {self.current_letter}, Categorie {self.current_categories}")

        start_msg = Message(
            type=MessageType.EVT_GAME_START,
            sender="SERVER",
            payload={
                "letter": self.current_letter,
                "categories": self.current_categories,
                "duration": self.round_time
            }
        )
        await self.server.broadcast(start_msg)

        self._timer_task = asyncio.create_task(self._run_timer())
        return True, "Game started"

    async def _run_timer(self):
        """Handle round timer and end round when time is up."""
        remaining = self.round_time

        try:
            while remaining > 0 and self.state == GameState.PLAYING:
                timer_msg = Message(
                    type=MessageType.EVT_TIMER_UPDATE,
                    sender="SERVER",
                    payload={"time": remaining}
                )
                await self.server.broadcast(timer_msg)

                await asyncio.sleep(1)
                remaining -= 1

            await self._end_round()

        except asyncio.CancelledError:
            print("[GAME] Timer cancellato")

    async def _end_round(self):
        """End time: change PLAYING -> VOTING/SCORING"""
        print("[GAME] Tempo scaduto!.")
        self.state = GameState.VOTING

        end_msg = Message(
            type=MessageType.EVT_ROUND_END,
            sender="SERVER",
            payload={"reason": "TIME_UP"}
        )
        await self.server.broadcast(end_msg)

        #TODO logica di invio risultati e votazioni
