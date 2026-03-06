import unittest
import tkinter as tk
from unittest.mock import MagicMock, patch
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

from src.client.gui.screens.login import LoginScreen

class TkinterGUITestCase(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
            self.root.withdraw() 
        except tk.TclError:
            self.skipTest("Tkinter not available.")
            return
        self.mock_manager = MagicMock()
        self.mock_manager.on_connect = MagicMock()

        self.parent_frame = tk.Frame(self.root)
        self.screen = LoginScreen(self.parent_frame, self.mock_manager)
        self.screen.show()

        self.login_button = None
        for widget in self.screen.frame.winfo_children():
            if isinstance(widget, tk.Frame):
                for sub in widget.winfo_children():
                    if isinstance(sub, tk.Button):
                        self.login_button = sub

    def tearDown(self):
        self.root.update()
        self.root.destroy()

    def enter_text(self, entry_widget, text):
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, text)
        self.root.update()

class TestLoginScreen(TkinterGUITestCase):

    def test_login_flow_success(self):
        self.enter_text(self.screen._username_entry, "Chiara")

        self.screen._handle_connect()
        self.root.update()

        self.mock_manager.on_connect.assert_called_once_with("127.0.0.1", "Chiara")

    @patch('src.client.gui.screens.login.messagebox.showerror')
    def test_login_flow_missing_data(self, mock_showerror):

        self.enter_text(self.screen._username_entry, "")

        self.screen._handle_connect()
        self.root.update()

        self.mock_manager.on_connect.assert_not_called()
        mock_showerror.assert_called_once()
