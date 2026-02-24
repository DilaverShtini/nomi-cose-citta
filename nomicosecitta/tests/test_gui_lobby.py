import unittest
import tkinter as tk
from unittest.mock import MagicMock, patch
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

from src.client.gui.screens.lobby import LobbyScreen
from src.common.constants import GAME_MODE_CLASSIC_PLUS

class TestLobbyScreen(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

        self.mock_manager = MagicMock()
        self.mock_manager.on_start_game = MagicMock()

        self.parent_frame = tk.Frame(self.root)
        self.screen = LobbyScreen(self.parent_frame, self.mock_manager)
        self.screen.show()

    def tearDown(self):
        self.root.update()
        self.root.destroy()

    def test_update_player_list(self):
        players = ["Veri", "Chiara", "Giovanni"]
        self.screen.update_player_list(players, "Veri")

        listbox_size = self.screen.player_list.size()
        self.assertEqual(listbox_size, 3)

    def test_admin_controls_visibility(self):
        self.screen.set_admin(False)
        self.root.update()
        self.assertFalse(self.screen._start_btn.winfo_ismapped())

        self.screen.set_admin(True)
        self.root.update()
        self.assertTrue(self.screen._start_btn.winfo_ismapped())

    @patch('src.client.gui.screens.lobby.messagebox.showwarning')
    def test_handle_start_game_emits_config(self, mock_warning):
        self.screen.set_admin(True)

        self.screen._game_mode_var.set(GAME_MODE_CLASSIC_PLUS)

        if "Animals" in self.screen._extra_category_vars:
            self.screen._extra_category_vars["Animals"].set(True)

        self.screen._handle_start_game()
        self.root.update()

        mock_warning.assert_not_called()
        self.mock_manager.on_start_game.assert_called_once()

        config = self.mock_manager.on_start_game.call_args[0][0]
        self.assertEqual(config["mode"], GAME_MODE_CLASSIC_PLUS)
        self.assertIn("Animals", config["selected_categories"])
