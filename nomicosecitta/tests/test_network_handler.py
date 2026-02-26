import unittest
from unittest.mock import patch, AsyncMock, MagicMock
import asyncio
import json

import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

from src.client.network_handler import NetworkHandler
from src.common.message import Message, MessageType
from src.common.constants import ENCODING

class TestNetworkHandler(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.handler = NetworkHandler(host="127.0.0.1", port=5000)
        self.mock_on_message = MagicMock()
        self.mock_on_disconnect = MagicMock()
        self.handler.on_message = self.mock_on_message
        self.handler.on_disconnect = self.mock_on_disconnect

    def test_initialization(self):
        self.assertEqual(self.handler.server_address, "127.0.0.1:5000")
        self.assertFalse(self.handler.is_connected())

    @patch('asyncio.open_connection')
    async def test_connect_success(self, mock_open_connection):
        """Testa la connessione riuscita al server."""
        mock_reader, mock_writer = AsyncMock(), AsyncMock()
        mock_open_connection.return_value = (mock_reader, mock_writer)

        result = await self.handler.connect()

        self.assertTrue(result)
        self.assertTrue(self.handler.running)
        self.assertTrue(self.handler.is_connected())
        self.assertIsNotNone(self.handler.receive_task)
        
        await self.handler.disconnect()

    @patch('asyncio.open_connection')
    async def test_connect_refused(self, mock_open_connection):
        mock_open_connection.side_effect = ConnectionRefusedError()

        result = await self.handler.connect()

        self.assertFalse(result)
        self.assertFalse(self.handler.running)

    async def test_send_not_connected(self):
        msg = Message(type=MessageType.MSG_CHAT, sender="P1", payload={})
        result = await self.handler.send(msg)
        self.assertFalse(result)

    @patch('asyncio.open_connection')
    async def test_send_success(self, mock_open_connection):
        mock_reader, mock_writer = AsyncMock(), AsyncMock()
        mock_open_connection.return_value = (mock_reader, mock_writer)
        await self.handler.connect()

        msg = Message(type=MessageType.MSG_CHAT, sender="P1", payload={"text": "Ciao"})
        result = await self.handler.send(msg)

        self.assertTrue(result)
        mock_writer.write.assert_called_once()
        mock_writer.drain.assert_awaited_once()

        await self.handler.disconnect()

    @patch('asyncio.open_connection')
    async def test_receive_loop_valid_message(self, mock_open_connection):
        mock_reader, mock_writer = AsyncMock(), AsyncMock()
        mock_open_connection.return_value = (mock_reader, mock_writer)
        
        msg = Message(type=MessageType.MSG_CHAT, sender="P1", payload={})
        json_bytes = (msg.to_json() + "\n").encode(ENCODING)
        mock_reader.readline.side_effect = [json_bytes, b""] 

        await self.handler.connect()
        await self.handler.receive_task

        self.mock_on_message.assert_called_once()
        received_msg = self.mock_on_message.call_args[0][0]
        self.assertEqual(received_msg.type, MessageType.MSG_CHAT)
        
        self.mock_on_disconnect.assert_called_once_with("Server closed connection")
        self.assertFalse(self.handler.running)

    @patch('asyncio.start_server')
    async def test_start_p2p_listener(self, mock_start_server):
        mock_server = AsyncMock()
        mock_socket = MagicMock()
        mock_socket.getsockname.return_value = ('0.0.0.0', 12345)
        mock_server.sockets = [mock_socket]
        mock_start_server.return_value = mock_server

        port = await self.handler.start_p2p_listener()

        self.assertEqual(port, 12345)
        mock_start_server.assert_called_once()

    @patch('asyncio.open_connection')
    async def test_send_p2p_success(self, mock_open_connection):
        mock_reader, mock_writer = AsyncMock(), AsyncMock()
        mock_open_connection.return_value = (mock_reader, mock_writer)

        msg = Message(type=MessageType.MSG_VOTE, sender="P1", payload={})
        result = await self.handler.send_p2p("192.168.1.5:9000", msg)

        self.assertTrue(result)
        mock_open_connection.assert_called_once_with("192.168.1.5", 9000)
        mock_writer.write.assert_called_once()
        mock_writer.drain.assert_awaited_once()
        mock_writer.close.assert_called_once()
        mock_writer.wait_closed.assert_awaited_once()

    async def test_handle_p2p_connection(self):
        mock_reader, mock_writer = AsyncMock(), AsyncMock()
        mock_writer.get_extra_info.return_value = "192.168.1.10:8000"
        
        msg = Message(type=MessageType.MSG_VOTE, sender="P2", payload={})
        mock_reader.readline.return_value = (msg.to_json() + "\n").encode(ENCODING)

        await self.handler._handle_p2p_connection(mock_reader, mock_writer)

        self.mock_on_message.assert_called_once()
        mock_writer.close.assert_called_once()