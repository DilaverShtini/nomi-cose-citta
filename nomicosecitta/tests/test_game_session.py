import time
import unittest
from unittest.mock import AsyncMock, MagicMock
import sys
import os
import asyncio

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

from src.server.session.game_session import GameSession
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

    async def test_start_game_fail_not_enough_players(self):
        self.mock_server.get_active_count.return_value = 0
        settings = {"mode": "classic", "round_time": 60}
        
        success, msg = await self.session.start_game("AdminUser", settings)
        
        self.assertFalse(success)
        self.assertEqual(msg, "Not enough players")
        self.assertEqual(self.session.state, GameState.LOBBY)

    async def test_start_game_fail_already_in_progress(self):
        self.session.state = GameState.WAITING_INPUT
        settings = {"mode": "classic", "round_time": 60}
        
        success, msg = await self.session.start_game("AdminUser", settings)
        
        self.assertFalse(success)
        self.assertEqual(msg, "Game already in progress")

    async def test_receive_answers_rejected_outside_time_limit(self):
        self.session.state = GameState.VOTING
        
        await self.session.receive_answers("AdminUser", {"Nomi": "Mario"})
        self.assertEqual(len(self.session.received_answers), 0)

    def test_run_initial_validation(self):
        self.session.current_round = MagicMock()
        self.session.current_round.letter = "R"
        self.session.current_round.categories = ["Città"]
        
        self.session.received_answers = {
            "P1": {"Città": "Roma"},
            "P2": {"Città": "Milano"},
            "P3": {"Città": ""}
        }
        
        self.session._run_initial_validation()
        
        self.assertEqual(self.session.round_data["Città"]["P1"]["status"], "PENDING_VOTE")
        self.assertIn("P1", self.session.words_to_vote["Città"])
        self.assertEqual(self.session.round_data["Città"]["P2"]["status"], "INVALID")
        self.assertEqual(self.session.round_data["Città"]["P3"]["status"], "INVALID")
        self.assertNotIn("P2", self.session.words_to_vote["Città"])

    async def test_end_round(self):
        self.session.state = GameState.WAITING_INPUT
        self.session.current_round = MagicMock()
        self.session.current_round.letter = "A"
        self.session.current_round.categories = ["Nomi"]
        self.session.received_answers = {"P1": {"Nomi": "Anna"}}

        await self.session._end_round()

        pending = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        if pending:
            await asyncio.wait(pending)

        self.assertEqual(self.session.state, GameState.VOTING)

    async def test_handle_player_disconnection_triggers_voting(self):
        self.session.state = GameState.WAITING_INPUT
        self.mock_server.get_active_count.return_value = 2

        self.mock_server.is_shutting_down = False
        self.session.current_round = MagicMock()
        self.session.current_round.letter = "A"
        self.session.current_round.categories = ["Nomi"]

        
        self.session._timers.cancel_round_timer = MagicMock()

        self.session.received_answers = {
            "P1": {"Nomi": "Anna"},
            "P2": {"Nomi": "Alberto"}
        }

        await self.session.handle_player_disconnection("P3")

        self.assertEqual(self.session.state, GameState.VOTING)
        self.session._timers.cancel_round_timer.assert_called_once()

    async def test_sync_reconnecting_client(self):
        self.session.state = GameState.VOTING
        self.session.current_round = MagicMock()
        self.session.current_round.letter = "A"
        self.session.current_round.categories = ["Nomi"]
        self.session.current_round_number = 1
        self.session.round_time = 60
        self.session.round_start_time = time.time() - 20
        self.session.words_to_vote = {"Nomi": {"P1": "Anna"}}
        self.session.scores = {"P1": 10}

        mock_client = AsyncMock()
        mock_client.username = "P2"
        
        await self.session.sync_reconnecting_client(mock_client)

        self.assertEqual(mock_client.send.call_count, 2)