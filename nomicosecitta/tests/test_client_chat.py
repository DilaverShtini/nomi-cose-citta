import unittest
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

from src.client.main import ClientController
from src.client.message_handler import MessageHandler
from src.common.message import Message, MessageType

class TestClientChat(unittest.IsolatedAsyncioTestCase):

    @patch('src.client.main.threading.Thread')
    @patch('src.client.main.GUIManager')
    @patch('src.client.main.tk.Tk')
    async def asyncSetUp(self, mock_tk, mock_gui, mock_thread):
        self.controller = ClientController()
        self.controller.username = "Veri"
        
        self.controller.network = MagicMock()
        self.controller.network.send_p2p = AsyncMock()

        self.controller.peer_map = {
            "Veri": "127.0.0.1:5000",
            "Chiara": "127.0.0.1:5001",
            "Giovanni": "127.0.0.1:5002"
        }

    async def asyncTearDown(self):
        if hasattr(self, 'controller') and self.controller.loop:
            self.controller.loop.close()

    async def test_broadcast_chat_sends_to_peers_only(self):
        test_message = Message(
            type=MessageType.MSG_CHAT, 
            sender="Veri", 
            payload={"text": "Hello everyone"}
        )
        
        await self.controller._broadcast_chat_p2p(test_message)
        
        self.assertEqual(self.controller.network.send_p2p.call_count, 2)
        
        calls = self.controller.network.send_p2p.call_args_list
        addresses_called = [call[0][0] for call in calls]
        messages_sent = [call[0][1] for call in calls]
        
        self.assertIn("127.0.0.1:5001", addresses_called)
        self.assertIn("127.0.0.1:5002", addresses_called)
        self.assertNotIn("127.0.0.1:5000", addresses_called)

        msg_obj = messages_sent[0]
        self.assertEqual(msg_obj.type, MessageType.MSG_CHAT)
        self.assertEqual(msg_obj.sender, "Veri")
        self.assertEqual(msg_obj.payload["text"], "Hello everyone")

    @patch('src.client.main.asyncio.run_coroutine_threadsafe')
    def test_send_message_updates_gui_and_broadcasts(self, mock_run_coroutine):
        self.controller.network.is_connected.return_value = True

        with patch.object(self.controller, '_broadcast_chat_p2p') as mock_broadcast:

            self.controller.send_message("Messaggio di test")

            self.controller.gui.append_log.assert_called_once_with("YOU: Messaggio di test")
            
            mock_broadcast.assert_called_once()

            sent_msg = mock_broadcast.call_args[0][0]
            
            self.assertEqual(sent_msg.type, MessageType.MSG_CHAT)
            self.assertEqual(sent_msg.payload["text"], "Messaggio di test")

            mock_run_coroutine.assert_called_once()

            coroutine_generata = mock_run_coroutine.call_args[0][0]
            if hasattr(coroutine_generata, 'close'):
                coroutine_generata.close()

    def test_handle_incoming_chat_message(self):
        incoming_msg = Message(
            type=MessageType.MSG_CHAT,
            sender="Veri",
            payload={"text": "Hello from Veri"}
        )

        def fake_after(delay, func, *args):
            func()

        self.controller.root.after = MagicMock(side_effect=fake_after)

        msg_handler = MessageHandler(self.controller)
        msg_handler.handle(incoming_msg)

        self.controller.gui.append_log.assert_called_once_with("Veri: Hello from Veri")

    def test_handle_peer_map_update(self):
        fake_peer_map = {
            "Chiara": "192.168.1.5:5000", 
            "Giovanni": "192.168.1.6:5000"
        }

        incoming_msg = Message(
            type=MessageType.EVT_PEER_MAP,
            sender="SERVER",
            payload={"peermap": fake_peer_map}
        )

        msg_handler = MessageHandler(self.controller)
        msg_handler.handle(incoming_msg)

        self.assertEqual(self.controller.peer_map, fake_peer_map)
