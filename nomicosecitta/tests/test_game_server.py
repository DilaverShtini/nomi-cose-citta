import unittest
import sys
import os
from unittest.mock import MagicMock

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

from src.server.game_server import GameServer

class TestGameServer(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.server = GameServer()

        self.client1 = MagicMock()
        self.client1.username = "Veri"
        self.client1.p2p_address = "127.0.0.1:5001"

        self.client2 = MagicMock()
        self.client2.username = "Chiara"
        self.client2.p2p_address = "127.0.0.1:5002"

        self.server.clients.extend([self.client1, self.client2])

    def test_get_client_by_username(self):
        self.assertEqual(self.server.get_client_by_username("Veri"), self.client1)
        self.assertIsNone(self.server.get_client_by_username("Giovanni"))

    def test_get_active_count(self):
        self.assertEqual(self.server.get_active_count(), 2)

    def test_get_active_usernames(self):
        self.assertEqual(self.server.get_active_usernames(), {"Veri", "Chiara"})

    def test_is_username_taken(self):
        self.assertTrue(self.server.is_username_taken("Veri"))
        self.assertFalse(self.server.is_username_taken("Giovanni"))

    def test_get_peer_map(self):
        expected_map = {
            "Veri": "127.0.0.1:5001",
            "Chiara": "127.0.0.1:5002"
        }
        self.assertEqual(self.server.get_peer_map(), expected_map)

    def test_remove_client(self):
        self.server.remove_client(self.client1)
        self.assertEqual(self.server.get_active_count(), 1)
        self.assertNotIn(self.client1, self.server.clients)

    def test_admin_management(self):
        empty_server = GameServer()
        self.assertIsNone(empty_server.get_admin())

        empty_server.set_admin("Veri")
        self.assertEqual(empty_server.get_admin(), "Veri")

        empty_server.set_admin("Giovanni")
        self.assertEqual(empty_server.get_admin(), "Veri")
