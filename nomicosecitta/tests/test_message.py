import unittest
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.insert(0, root_dir)

from src.common.message import Message, MessageType

class TestMessage(unittest.TestCase):

    def setUp(self):
        self.test_sender = "TestUser"
        self.test_payload = {"text": "Nomi - Cose - Citta"}
        self.message = Message(
            type=MessageType.MSG_CHAT,
            sender=self.test_sender,
            payload=self.test_payload
        )

    def tearDown(self):
        self.message = None

    def test_message_creation(self):
        self.assertEqual(self.message.sender, "TestUser")
        self.assertEqual(self.message.type, MessageType.MSG_CHAT)
        self.assertIn("text", self.message.payload)

    def test_message_to_json(self):
        json_str = self.message.to_json()
        self.assertIsInstance(json_str, str)
        self.assertIn("TestUser", json_str)
        self.assertIn("Nomi - Cose - Citta", json_str)
