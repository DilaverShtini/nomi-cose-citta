"""
Lobby screen for the Nomi Cose Città client.
Waiting room with player list, game settings, and chat.
"""
import tkinter as tk
from tkinter import messagebox

from src.client.gui.screens.base_screen import BaseScreen
from src.client.gui.widgets import PlayerList, ChatPanel
from src.client.gui.utils import bind_mousewheel
from src.common.constants import (
    AVAILABLE_EXTRA_CATEGORIES,
    GAME_MODE_CLASSIC,
    GAME_MODE_CLASSIC_PLUS,
    GAME_MODE_FREE,
    MIN_EXTRA_CATEGORIES,
    MAX_EXTRA_CATEGORIES,
    MIN_ROUND_TIME,
    MAX_ROUND_TIME,
    DEFAULT_ROUND_TIME
)


class LobbyScreen(BaseScreen):
    """
    Lobby/waiting room screen.
    Displays player list, game settings, and chat panel.

    Admin controls are shown/hidden based on admin status.
    """

    def _setup_ui(self):
        """Setup the lobby screen UI."""
        self._is_admin = False
        
        self._game_mode_var = tk.StringVar(value=GAME_MODE_CLASSIC)
        self._num_extra_var = tk.IntVar(value=2)
        self._round_time_var = tk.IntVar(value=DEFAULT_ROUND_TIME)
        self._extra_category_vars = {}
        
        self._setup_header()
        self._setup_content()

    def _setup_header(self):
        """Setup the header with title and admin indicator."""
        header = tk.Frame(self.frame)
        header.pack(fill="x", pady=(0, 10), padx=10)

        tk.Label(
            header,
            text="Waiting Room",
            font=("Arial", 16, "bold")
        ).pack(side="left")

        self._admin_label = tk.Label(
            header,
            text="",
            font=("Arial", 10),
            fg="#FF9800"
        )
        self._admin_label.pack(side="right")

    def _setup_content(self):
        """Setup the main content area with three panels."""
        content = tk.Frame(self.frame)
        content.pack(fill="both", expand=True, padx=10)

        self._setup_players_panel(content)
        self._setup_settings_panel(content)
        self._setup_chat_panel(content)

    def _setup_players_panel(self, parent):
        """Setup left panel with player list widget."""
        left_panel = tk.Frame(parent, width=140)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False)

        self._player_list = PlayerList(left_panel)
        self._player_list.pack(fill="both", expand=True)

    def _setup_settings_panel(self, parent):
        """Setup center panel with game settings."""
        center_panel = tk.Frame(parent, relief="groove", bd=1)
        center_panel.pack(side="left", fill="both", expand=True, padx=5)

        canvas = tk.Canvas(center_panel, highlightthickness=0)
        scrollbar = tk.Scrollbar(center_panel, orient="vertical", command=canvas.yview)
        self._settings_frame = tk.Frame(canvas)

        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        settings_window = canvas.create_window((0, 0), window=self._settings_frame, anchor="nw")

        def on_configure():
            canvas.configure(scrollregion=canvas.bbox("all"))

        def on_canvas_resize(event):
            canvas.itemconfig(settings_window, width=event.width)

        self._settings_frame.bind("<Configure>", lambda e: on_configure())
        canvas.bind("<Configure>", on_canvas_resize)
        bind_mousewheel(canvas)

        self._build_settings_controls()

    def _setup_chat_panel(self, parent):
        """Setup right panel with chat widget."""
        right_panel = tk.Frame(parent, width=220)
        right_panel.pack(side="right", fill="both", padx=(10, 0))

        self._chat = ChatPanel(
            right_panel,
            on_send=self._handle_send_chat
        )
        self._chat.pack(fill="both", expand=True)

    def _build_settings_controls(self):
        """Build all settings controls."""
        tk.Label(
            self._settings_frame,
            text="Game Settings",
            font=("Arial", 12, "bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))

        tk.Frame(self._settings_frame, height=1, bg="#ccc").pack(fill="x", padx=10, pady=5)

        self._build_mode_selector()
        self._build_num_categories_selector()
        self._build_categories_selector()
        self._build_time_selector()
        self._build_start_button()

        self._on_mode_change()
        self._update_admin_controls()

    def _build_mode_selector(self):
        """Build game mode radio buttons."""
        mode_frame = tk.LabelFrame(
            self._settings_frame,
            text="Game Mode",
            font=("Arial", 10, "bold"),
            padx=10, pady=5
        )
        mode_frame.pack(fill="x", padx=10, pady=5)

        modes = [
            (GAME_MODE_CLASSIC, "Classic", "Only Nomi + Cose + Città"),
            (GAME_MODE_CLASSIC_PLUS, "Classic Plus", "Nomi + Cose + Città + extra"),
            (GAME_MODE_FREE, "Free Choice", "Only selected categories")
        ]

        for value, name, desc in modes:
            row = tk.Frame(mode_frame)
            row.pack(fill="x", pady=2)

            tk.Radiobutton(
                row,
                text=name,
                variable=self._game_mode_var,
                value=value,
                font=("Arial", 10),
                command=self._on_mode_change
            ).pack(side="left")

            tk.Label(
                row,
                text=f"({desc})",
                font=("Arial", 8),
                fg="#666"
            ).pack(side="left", padx=5)

    def _build_num_categories_selector(self):
        """Build number of categories selector."""
        self._num_frame = tk.LabelFrame(
            self._settings_frame,
            text="Number of extra categories",
            font=("Arial", 10, "bold"),
            padx=10, pady=5
        )

        tk.Label(
            self._num_frame,
            text="Top N voted categories will be used:",
            font=("Arial", 9),
            fg="#666"
        ).pack(anchor="w")

        num_row = tk.Frame(self._num_frame)
        num_row.pack(fill="x", pady=5)

        row1 = tk.Frame(num_row)
        row1.pack(fill="x")
        row2 = tk.Frame(num_row)
        row2.pack(fill="x")

        for n in range(MIN_EXTRA_CATEGORIES, MAX_EXTRA_CATEGORIES + 1):
            parent = row1 if n <= 5 else row2
            tk.Radiobutton(
                parent,
                text=str(n),
                variable=self._num_extra_var,
                value=n,
                font=("Arial", 10)
            ).pack(side="left", padx=8)

    def _build_categories_selector(self):
        """Build categories checkboxes."""
        self._categories_frame = tk.LabelFrame(
            self._settings_frame,
            text="Extra Categories",
            font=("Arial", 10, "bold"),
            padx=10, pady=5
        )

        self._categories_info = tk.Label(
            self._categories_frame,
            text="Select categories:",
            font=("Arial", 9),
            fg="#666"
        )
        self._categories_info.pack(anchor="w", pady=(0, 5))

        checkbox_grid = tk.Frame(self._categories_frame)
        checkbox_grid.pack(fill="x")

        for i, category in enumerate(AVAILABLE_EXTRA_CATEGORIES):
            var = tk.BooleanVar(value=False)
            self._extra_category_vars[category] = var

            cb = tk.Checkbutton(
                checkbox_grid,
                text=category,
                variable=var,
                font=("Arial", 9)
            )
            cb.grid(row=i // 3, column=i % 3, sticky="w", padx=5, pady=1)

    def _build_time_selector(self):
        """Build round time selector."""
        self._time_frame = tk.LabelFrame(
            self._settings_frame,
            text="Round Time (seconds)",
            font=("Arial", 10, "bold"),
            padx=10, pady=5
        )
        self._time_frame.pack(fill="x", padx=10, pady=5)

        self._time_info = tk.Label(
            self._time_frame,
            text="Only admin can modify",
            font=("Arial", 9, "italic"),
            fg="#FF9800"
        )
        self._time_info.pack(anchor="w")

        slider_row = tk.Frame(self._time_frame)
        slider_row.pack(fill="x", pady=5)

        tk.Label(slider_row, text=str(MIN_ROUND_TIME), font=("Arial", 9)).pack(side="left")

        self._time_scale = tk.Scale(
            slider_row,
            from_=MIN_ROUND_TIME,
            to=MAX_ROUND_TIME,
            orient="horizontal",
            variable=self._round_time_var,
            length=200,
            font=("Arial", 9),
            resolution=5
        )
        self._time_scale.pack(side="left", fill="x", expand=True, padx=5)

        tk.Label(slider_row, text=str(MAX_ROUND_TIME), font=("Arial", 9)).pack(side="left")

    def _build_start_button(self):
        """Build start game button."""
        self._start_frame = tk.Frame(self._settings_frame)
        self._start_frame.pack(fill="x", padx=10, pady=15)

        self._start_btn = tk.Button(
            self._start_frame,
            text="START GAME",
            bg="#FF9800",
            fg="white",
            font=("Arial", 12, "bold"),
            command=self._handle_start_game
        )
        self._start_btn.pack(fill="x", ipady=5)

        self._waiting_label = tk.Label(
            self._start_frame,
            text="Waiting for admin to start...",
            font=("Arial", 10, "italic"),
            fg="#666"
        )

    # Event handlers

    def _on_mode_change(self):
        """Handle game mode change."""
        mode = self._game_mode_var.get()

        if mode == GAME_MODE_CLASSIC:
            self._num_frame.pack_forget()
            self._categories_frame.pack_forget()
        else:
            self._num_frame.pack(fill="x", padx=10, pady=5, before=self._time_frame)
            self._categories_frame.pack(fill="x", padx=10, pady=5, before=self._time_frame)

            if mode == GAME_MODE_CLASSIC_PLUS:
                self._categories_info.config(text="Extra categories (added to Nomi+Cose+Città):")
            else:
                self._categories_info.config(text="Select categories to play with:")

    def _update_admin_controls(self):
        """Update controls based on admin status."""
        if self._is_admin:
            self._admin_label.config(text="⭐ You are the Admin")
            self._time_scale.config(state="normal")
            self._time_info.config(text="Set round time")
            self._start_btn.pack(fill="x", ipady=5)
            self._waiting_label.pack_forget()
        else:
            self._admin_label.config(text="")
            self._time_scale.config(state="disabled")
            self._time_info.config(text="Only admin can modify")
            self._start_btn.pack_forget()
            self._waiting_label.pack(pady=10)

    def _handle_send_chat(self, message: str):
        """Handle chat message send."""
        if self.manager.on_send_message:
            self.manager.on_send_message(message)

    def _handle_start_game(self):
        """Handle start game button click."""
        mode = self._game_mode_var.get()
        selected = self.get_selected_categories()

        if mode in [GAME_MODE_CLASSIC_PLUS, GAME_MODE_FREE]:
            if len(selected) == 0:
                messagebox.showwarning(
                    "Selection Required",
                    "You must select at least one category."
                )
                return

        config = {
            "mode": mode,
            "selected_categories": selected,
            "num_extra_categories": self._num_extra_var.get(),
            "round_time": self._round_time_var.get()
        }

        if self.manager.on_start_game:
            self.manager.on_start_game(config)

    # Public API

    def set_admin(self, is_admin: bool):
        """Set whether this client is the admin."""
        self._is_admin = is_admin
        self._update_admin_controls()

    def update_player_list(self, players: list, admin_username: str = None):
        """Update the player list."""
        self._player_list.update(players, admin_username)

    def append_log(self, text: str):
        """Append message to chat log."""
        self._chat.append(text)

    def get_selected_categories(self) -> list:
        """Get list of selected extra categories."""
        return [cat for cat, var in self._extra_category_vars.items() if var.get()]

    def get_settings(self) -> dict:
        """Get current game settings."""
        return {
            "mode": self._game_mode_var.get(),
            "selected_categories": self.get_selected_categories(),
            "num_extra_categories": self._num_extra_var.get(),
            "round_time": self._round_time_var.get()
        }

    @property
    def player_list(self):
        """Access player list widget for backward compatibility."""
        return self._player_list.listbox