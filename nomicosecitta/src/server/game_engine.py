import asyncio
from src.common.message import Message, MessageType, GameState
from src.server.round_manager import RoundManager

class GameEngine:
    """
    Handle game logic.
    """
    def __init__(self, server):
        self.server = server
        self.state = GameState.LOBBY
        self.old_letters = set()
        self.current_round = None

    async def start_game(self, request_username, settings):
        """Handle game start request from admin."""

        if self.state != GameState.LOBBY:
            return False, "Game already in progress"

        if request_username != self.server.get_admin():
            return False, "Only the admin can start the game"

        if self.server.get_active_count() < 1:
            return False, "Not enough players"

        self.state = GameState.WAITING_INPUT

        self.current_round = RoundManager(settings, self.old_letters)
        self.old_letters.add(self.current_round.letter)

        self.round_time = int(settings["round_time"])

        print(f"[GAME] Inizio Round: Lettera {self.current_round.letter}, Categorie {self.current_round.categories}")

        start_msg = Message(
            type=MessageType.EVT_GAME_START,
            sender="SERVER",
            payload={
                "letter": self.current_round.letter,
                "categories": self.current_round.categories,
                "duration": self.round_time
            }
        )
        await self.server.broadcast(start_msg)

        self._timer_task = asyncio.create_task(
            self.current_round.start_timer(
                callback_on_tick=self._broadcast_timer, 
                callback_on_end=self._end_round
            )
        )

        return True, "Game started"

    async def _broadcast_timer(self, seconds):
        msg = Message(
            type=MessageType.EVT_TIMER_UPDATE,
            sender="SERVER",
            payload={"time": seconds}
        )
        await self.server.broadcast(msg)

    async def _end_round(self):
        """End time: change WAITING_INPUT -> VOTING/SCORING"""
        print("[GAME] Tempo scaduto!.")
        self.state = GameState.VOTING

        end_msg = Message(
            type=MessageType.EVT_ROUND_END,
            sender="SERVER",
            payload={"reason": "TIME_UP"}
        )
        await self.server.broadcast(end_msg)

        #TODO logica di invio risultati e votazioni
