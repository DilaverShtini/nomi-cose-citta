#!/usr/bin/env python3
"""
Test script for the refactored GUI architecture.

Tests:
- Screen navigation with BaseScreen lifecycle hooks
- Widget reusability (Timer, PlayerList, Chat)
- GUIManager coordination
- Game flow simulation
"""

import sys
import os
import tkinter as tk
import threading
import time
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.client.gui import GUIManager, Screen
from src.common.constants import (
    DEFAULT_CATEGORIES,
    GAME_MODE_CLASSIC,
    GAME_MODE_CLASSIC_PLUS,
    GAME_MODE_FREE
)


class TestGUI:
    """Test harness for the GUI."""

    def __init__(self):
        self.root = tk.Tk()
        self.timer_running = False
        self.timer_seconds = 60

        # Create GUI manager
        self.gui = GUIManager(self.root)

        # Set callbacks
        self.gui.on_connect = self._on_connect
        self.gui.on_send_message = self._on_send_message
        self.gui.on_start_game = self._on_start_game

        # Create control panel
        self._create_control_panel()

    def _on_connect(self, ip: str, username: str):
        """Handle connection request."""
        print(f"[TEST] Connect: {username}@{ip}")

    def _on_send_message(self, message: str):
        """Handle chat message."""
        print(f"[TEST] Chat: {message}")
        self.gui.append_log(f"Tu: {message}")

    def _on_start_game(self, config: dict):
        """Handle start game request."""
        print(f"\n{'='*50}")
        print("[TEST] === STARTING GAME ===")
        print(f"Mode: {config['mode']}")
        print(f"Categories: {config['selected_categories']}")
        print(f"Num extra: {config['num_extra_categories']}")
        print(f"Round time: {config['round_time']}s")
        print('='*50)

        # Determine categories
        mode = config['mode']
        selected = config['selected_categories']
        num_extra = config['num_extra_categories']

        if mode == GAME_MODE_CLASSIC:
            categories = DEFAULT_CATEGORIES.copy()
        elif mode == GAME_MODE_CLASSIC_PLUS:
            categories = DEFAULT_CATEGORIES.copy()
            categories.extend(selected[:num_extra])
        else:  # FREE
            categories = selected[:num_extra] if selected else DEFAULT_CATEGORIES.copy()

        print(f"[TEST] Final categories: {categories}")

        # Start round
        letter = random.choice("ABCDEFGHILMNOPRSTV")
        self.timer_seconds = config['round_time']

        self.gui.show_game()
        self.gui.start_round(letter, categories, 1)
        self.gui.update_timer(self.timer_seconds)
        self._start_timer()

    def _create_control_panel(self):
        """Create the test control panel."""
        control = tk.Toplevel(self.root)
        control.title("Test Controls")
        control.geometry("350x550")

        tk.Label(
            control,
            text="🎮 GUI Test Controls",
            font=("Arial", 14, "bold")
        ).pack(pady=10)

        # Navigation section
        nav_frame = tk.LabelFrame(control, text="Navigation", padx=10, pady=5)
        nav_frame.pack(fill="x", padx=10, pady=5)

        tk.Button(nav_frame, text="Login", 
                  command=lambda: self.gui.navigate_to(Screen.LOGIN)).pack(side="left", padx=2)
        tk.Button(nav_frame, text="Lobby",
                  command=lambda: self.gui.navigate_to(Screen.LOBBY)).pack(side="left", padx=2)
        tk.Button(nav_frame, text="Game",
                  command=lambda: self.gui.navigate_to(Screen.GAME)).pack(side="left", padx=2)

        # Connection simulation
        conn_frame = tk.LabelFrame(control, text="Connection Simulation", padx=10, pady=5)
        conn_frame.pack(fill="x", padx=10, pady=5)

        tk.Button(
            conn_frame,
            text="Connect as ADMIN",
            bg="#FF9800",
            fg="white",
            command=lambda: self._simulate_connect(is_admin=True)
        ).pack(fill="x", pady=2)

        tk.Button(
            conn_frame,
            text="Connect as PLAYER",
            bg="#4CAF50",
            fg="white",
            command=lambda: self._simulate_connect(is_admin=False)
        ).pack(fill="x", pady=2)

        tk.Button(
            conn_frame,
            text="Add Fake Player",
            command=self._add_fake_player
        ).pack(fill="x", pady=2)

        # Quick test section
        test_frame = tk.LabelFrame(control, text="Quick Tests", padx=10, pady=5)
        test_frame.pack(fill="x", padx=10, pady=5)

        tk.Button(
            test_frame,
            text="▶ Test Classic Mode",
            command=lambda: self._quick_start(GAME_MODE_CLASSIC)
        ).pack(fill="x", pady=1)

        tk.Button(
            test_frame,
            text="▶ Test Classic Plus",
            command=lambda: self._quick_start(GAME_MODE_CLASSIC_PLUS)
        ).pack(fill="x", pady=1)

        tk.Button(
            test_frame,
            text="▶ Test Free Choice",
            command=lambda: self._quick_start(GAME_MODE_FREE)
        ).pack(fill="x", pady=1)

        # Timer controls
        timer_frame = tk.LabelFrame(control, text="Timer", padx=10, pady=5)
        timer_frame.pack(fill="x", padx=10, pady=5)

        btn_row = tk.Frame(timer_frame)
        btn_row.pack(fill="x")

        tk.Button(btn_row, text="▶ Start", command=self._start_timer).pack(side="left", padx=2)
        tk.Button(btn_row, text="⏸ Stop", command=self._stop_timer).pack(side="left", padx=2)
        tk.Button(btn_row, text="⏹ End Round", command=self.gui.end_round).pack(side="left", padx=2)

        # Debug section
        debug_frame = tk.LabelFrame(control, text="Debug", padx=10, pady=5)
        debug_frame.pack(fill="x", padx=10, pady=5)

        tk.Button(
            debug_frame,
            text="📋 Show Answers",
            command=self._show_answers
        ).pack(fill="x", pady=1)

        tk.Button(
            debug_frame,
            text="⚙ Show Settings",
            command=self._show_settings
        ).pack(fill="x", pady=1)

        tk.Button(
            debug_frame,
            text="📍 Current Screen",
            command=self._show_current_screen
        ).pack(fill="x", pady=1)

    def _simulate_connect(self, is_admin: bool):
        """Simulate a connection."""
        self.gui.set_admin(is_admin)
        self.gui.show_lobby()

        if is_admin:
            self.gui.update_player_list(["You (Admin)"], admin_username="You (Admin)")
            self.gui.append_log("[SYSTEM] You are the admin!")
            print("[TEST] Connected as ADMIN")
        else:
            self.gui.update_player_list(["Admin", "You"], admin_username="Admin")
            self.gui.append_log("[SYSTEM] Connected! Waiting for admin...")
            print("[TEST] Connected as PLAYER")

    def _add_fake_player(self):
        """Add a fake player to the list."""
        names = ["Mario", "Luigi", "Peach", "Toad", "Yoshi", "Bowser"]
        fake_name = random.choice(names) + str(random.randint(1, 99))

        # Get current players
        listbox = self.gui.players_list
        current = list(listbox.get(0, tk.END))

        # Find admin
        admin = None
        for p in current:
            if p.startswith("⭐"):
                admin = p.replace("⭐ ", "")
                break

        # Add new player
        players = [p.replace("⭐ ", "").replace("👤 ", "") for p in current]
        players.append(fake_name)

        self.gui.update_player_list(players, admin_username=admin)
        self.gui.append_log(f"[SYSTEM] {fake_name} joined")
        print(f"[TEST] Added: {fake_name}")

    def _quick_start(self, mode: str):
        """Quick start a game in given mode."""
        configs = {
            GAME_MODE_CLASSIC: {
                "mode": GAME_MODE_CLASSIC,
                "selected_categories": [],
                "num_extra_categories": 0,
                "round_time": 60
            },
            GAME_MODE_CLASSIC_PLUS: {
                "mode": GAME_MODE_CLASSIC_PLUS,
                "selected_categories": ["Animals", "Flowers", "Sports"],
                "num_extra_categories": 2,
                "round_time": 90
            },
            GAME_MODE_FREE: {
                "mode": GAME_MODE_FREE,
                "selected_categories": ["Animals", "Movies", "Sports", "Singers"],
                "num_extra_categories": 4,
                "round_time": 120
            }
        }
        self._on_start_game(configs[mode])

    def _start_timer(self):
        """Start the countdown timer."""
        if self.timer_running:
            return
        self.timer_running = True
        threading.Thread(target=self._timer_loop, daemon=True).start()

    def _stop_timer(self):
        """Stop the countdown timer."""
        self.timer_running = False

    def _timer_loop(self):
        """Timer countdown loop."""
        while self.timer_running and self.timer_seconds > 0:
            self.timer_seconds -= 1
            self.root.after(0, lambda s=self.timer_seconds: self.gui.update_timer(s))
            time.sleep(1)

        if self.timer_seconds <= 0:
            self.timer_running = False
            self.root.after(0, self.gui.end_round)

    def _show_answers(self):
        """Print current answers."""
        answers = self.gui.get_answers()
        print("\n=== ANSWERS ===")
        for cat, ans in answers.items():
            print(f"  {cat}: {ans or '(empty)'}")

    def _show_settings(self):
        """Print lobby settings."""
        settings = self.gui.get_game_settings()
        print("\n=== SETTINGS ===")
        print(f"  Mode: {settings['mode']}")
        print(f"  Categories: {settings['selected_categories']}")
        print(f"  Num extra: {settings['num_extra_categories']}")
        print(f"  Round time: {settings['round_time']}s")

    def _show_current_screen(self):
        """Print current screen."""
        print(f"\n[DEBUG] Current screen: {self.gui.current_screen}")

    def run(self):
        """Run the test GUI."""
        print("=" * 60)
        print("  GUI ARCHITECTURE TEST")
        print("  Nomi Cose Città - Release 2")
        print("=" * 60)
        print("\nArchitecture:")
        print("  - BaseScreen with lifecycle hooks (on_enter, on_exit)")
        print("  - GUIManager with Screen enum navigation")
        print("  - Reusable widgets (Timer, PlayerList, Chat)")
        print("\nUse the control panel to test different features.")
        print()

        self.root.mainloop()


if __name__ == "__main__":
    TestGUI().run()