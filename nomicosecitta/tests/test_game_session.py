import unittest
from unittest.mock import AsyncMock, MagicMock
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

from src.server.game_session import GameSession
from src.common.message import GameState

class TestGameSession(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.mock_server = MagicMock()

        self.mock_server.get_admin.return_value = "AdminUser"
        self.mock_server.get_active_count.return_value = 3
        self.mock_server.get_peer_map.return_value = {"AdminUser": "ip1", "P2": "ip2", "P3": "ip3"}
        self.mock_server.broadcast = AsyncMock()

        self.session = GameSession(self.mock_server)

    async def test_start_game_success(self):
        settings = {"mode": "classic", "round_time": 60}

        success, msg = await self.session.start_game("AdminUser", settings)

        self.assertTrue(success)
        self.assertEqual(msg, "Game started")

        self.assertEqual(self.session.state, GameState.WAITING_INPUT)

        self.assertIsNotNone(self.session.current_round)

        self.assertEqual(self.mock_server.broadcast.call_count, 2)

    async def test_start_game_fail_not_admin(self):
        settings = {"mode": "classic", "round_time": 60}
        success, msg = await self.session.start_game("NormalUser", settings)

        self.assertFalse(success)
        self.assertEqual(msg, "Only the admin can start the game")
        self.assertEqual(self.session.state, GameState.LOBBY)

    async def test_receive_answers_all_players_triggers_voting(self):
        self.session.state = GameState.WAITING_INPUT

        self.session.current_round = MagicMock()
        self.session.current_round.letter = "A"
        self.session.current_round.categories = ["Name"]
        self.session._timer_task = MagicMock()

        await self.session.receive_answers("AdminUser", {"Name": "Chiara"})
        await self.session.receive_answers("P2", {"Name": "Giovanni"})

        self.assertEqual(self.session.state, GameState.WAITING_INPUT)

        await self.session.receive_answers("P3", {"Name": "Veri"})

        self.assertEqual(self.session.state, GameState.VOTING)

        self.mock_server.broadcast.assert_called_once()
        broadcast_msg = self.mock_server.broadcast.call_args[0][0]
        self.assertEqual(broadcast_msg.type.name, "EVT_VOTING_START")
