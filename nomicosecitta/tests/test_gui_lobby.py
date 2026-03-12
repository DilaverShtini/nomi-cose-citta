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
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except tk.TclError:
            self.skipTest("Tkinter engine not available.")
            return

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
