import unittest
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

from src.server.game_server import GameServer
from src.server.client_handler import ClientHandler
from src.common.message import MessageType

class TestLobbyLogic(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.server = GameServer()
        self.server.broadcast = AsyncMock()

        self.mock_writer = AsyncMock()

        self.mock_writer.get_extra_info = MagicMock(return_value=("192.168.1.100", 12345)) 

        self.mock_writer.close = MagicMock()

        self.mock_reader = AsyncMock()

        self.handler = ClientHandler(self.mock_reader, self.mock_writer, self.server)
        self.server.clients.append(self.handler)

    async def test_join_success_and_broadcast(self):
        payload = {"username": "Chiara", "p2p_port": 5000}

        await self.handler._handle_join(payload)

        self.assertEqual(self.handler.username, "Chiara")
        self.assertEqual(self.handler.p2p_address, "192.168.1.100:5000")
        self.assertEqual(self.server.get_admin(), "Chiara")

        self.server.broadcast.assert_called_once()
        broadcast_msg = self.server.broadcast.call_args[0][0]

        self.assertEqual(broadcast_msg.type, MessageType.EVT_LOBBY_UPDATE)
        self.assertIn("Chiara", broadcast_msg.payload["players"])
        self.assertEqual(broadcast_msg.payload["admin"], "Chiara")

    async def test_join_duplicate_name_error(self):
        existing_client = MagicMock()
        existing_client.username = "Chiara"
        self.server.clients.append(existing_client)

        payload = {"username": "Chiara", "p2p_port": 5001}

        with patch.object(self.handler, 'send', new_callable=AsyncMock) as mock_send:

            await self.handler._handle_join(payload)

            self.assertIsNone(self.handler.username)

            mock_send.assert_called_once()
            error_bytes = mock_send.call_args[0][0] 

            self.assertIn(b'evt_error', error_bytes)
            self.assertIn(b'Username already taken', error_bytes)

    async def test_handle_start_game_success(self):
        self.handler.username = "Chiara"

        self.server.session = MagicMock()
        self.server.session.start_game = AsyncMock(return_value=(True, "Game started"))

        await self.handler._handle_start_game({"mode": "classic"})

        self.server.session.start_game.assert_called_once_with("Chiara", {"mode": "classic"})

    async def test_handle_start_game_fail(self):
        self.handler.username = "Chiara"
        self.server.session = MagicMock()
        self.server.session.start_game = AsyncMock(return_value=(False, "Not enough players"))

        with patch.object(self.handler, 'send', new_callable=AsyncMock) as mock_send:
            await self.handler._handle_start_game({"mode": "classic"})

            mock_send.assert_called_once()
            error_bytes = mock_send.call_args[0][0]
            self.assertIn(b'evt_error', error_bytes)
            self.assertIn(b'Not enough players', error_bytes)

    async def test_close_connection_with_username(self):
        self.handler.username = "Chiara"

        await self.handler.close_connection()

        self.assertNotIn(self.handler, self.server.clients)
        self.mock_writer.close.assert_called_once()
        self.server.broadcast.assert_called_once()
        self.assertEqual(self.server.broadcast.call_args[0][0].type, MessageType.EVT_LOBBY_UPDATE)
