import unittest
import os
import tempfile
import sys
from unittest.mock import MagicMock

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

from src.server.state_manager import StateManager
from src.common.message import GameState

class TestStateManager(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.manager = StateManager(filename="test_state.json")
        self.manager.filepath = os.path.join(self.temp_dir.name, "test_state.json")

        self.mock_server = MagicMock()
        self.mock_server.get_admin.return_value = "AdminUser"
        self.mock_server._expected_players = {"AdminUser", "Player2"}
        self.mock_server.lobby_settings = {"mode": "classic"}
        self.mock_server.category_votes = {}

        self.mock_session = MagicMock()
        self.mock_session.state = GameState.VOTING
        self.mock_session.round_start_time = 0
        self.mock_session.current_round_number = 3
        self.mock_session.scores = {"AdminUser": 10, "Player2": 5}
        self.mock_session.old_letters = {"A", "B"}
        self.mock_session.current_settings = {}
        self.mock_session.round_time = 60
        self.mock_session.received_answers = {}
        self.mock_session.received_votes = {}
        self.mock_session.round_data = {}
        self.mock_session.words_to_vote = {}
        self.mock_session.current_round = MagicMock()
        self.mock_session.current_round.letter = "C"
        self.mock_session.current_round.categories = ["Name"]
        self.mock_session.voting_start_time = 0
        self.mock_session.current_voting_duration = 30

        self.mock_server.session = self.mock_session

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_save_and_load_state(self):
        self.manager.save_state(self.mock_server)
        self.assertTrue(os.path.exists(self.manager.filepath))

        loaded_data = self.manager.load_state()

        self.assertIsNotNone(loaded_data)
        self.assertEqual(loaded_data["server"]["admin"], "AdminUser")
        self.assertEqual(loaded_data["session"]["state"], "VOTING")
        self.assertEqual(loaded_data["session"]["round_number"], 3)
        self.assertEqual(loaded_data["session"]["scores"]["Player2"], 5)
        self.assertIn("A", loaded_data["session"]["old_letters"])
        self.assertEqual(loaded_data["session"]["current_round"]["letter"], "C")

    def test_load_state_file_not_found(self):
        non_existent_manager = StateManager(filename="missing.json")
        non_existent_manager.filepath = os.path.join(self.temp_dir.name, "missing.json")
        self.assertIsNone(non_existent_manager.load_state())
