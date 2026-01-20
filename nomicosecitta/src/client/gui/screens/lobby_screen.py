"""
Lobby screen component for the Nomi Cose Città client.
Contains player list, game settings, and chat.
"""
import tkinter as tk
from tkinter import messagebox, scrolledtext

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
from src.client.gui.utils import bind_mousewheel


class LobbyScreen:
    """
    Lobby/waiting room screen with player list, game settings, and chat.
    """

    def __init__(self, parent, on_send_callback, on_start_game_callback=None):
        """
        Initialize the lobby screen.
        
        Args:
            parent: Parent widget (root window).
            on_send_callback: Function called when sending chat messages.
                              Signature: on_send(message: str)
            on_start_game_callback: Function called when admin starts game.
                                    Signature: on_start_game(config: dict)
        """
        self.on_send = on_send_callback
        self.on_start_game = on_start_game_callback
        
        self.is_admin = False
        
        self.game_mode_var = tk.StringVar(value=GAME_MODE_CLASSIC)
        self.num_extra_categories_var = tk.IntVar(value=2)
        self.round_time_var = tk.IntVar(value=DEFAULT_ROUND_TIME)
        self.extra_category_vars = {} # category_name -> BooleanVar
        self.msg_var = tk.StringVar()
        
        # Create frame
        self.frame = tk.Frame(parent, padx=10, pady=10)
        self._setup_ui()

    def _setup_ui(self):
        """Setup the lobby screen UI."""
        # Header
        header = tk.Frame(self.frame)
        header.pack(fill="x", pady=(0, 10))
        
        tk.Label(
            header, 
            text="Waiting Room", 
            font=("Arial", 16, "bold")
        ).pack(side="left")
        
        self.admin_label = tk.Label(
            header, 
            text="", 
            font=("Arial", 10), 
            fg="#FF9800"
        )
        self.admin_label.pack(side="right")

        # Main content area
        content = tk.Frame(self.frame)
        content.pack(fill="both", expand=True)

        self._setup_players_panel(content)
        self._setup_settings_panel(content)
        self._setup_chat_panel(content)

    def _setup_players_panel(self, parent):
        """Setup the left panel with player list."""
        left_panel = tk.Frame(parent, width=140)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False)

        tk.Label(
            left_panel, 
            text="Players:", 
            font=("Arial", 10, "bold")
        ).pack(anchor="w")
        
        self.players_list = tk.Listbox(
            left_panel, 
            height=15, 
            width=16, 
            bg="#f0f0f0", 
            font=("Arial", 10)
        )
        self.players_list.pack(fill="both", expand=True)

    def _setup_settings_panel(self, parent):
        """Setup the center panel with game settings."""
        center_panel = tk.Frame(parent, relief="groove", bd=1)
        center_panel.pack(side="left", fill="both", expand=True, padx=5)

        # Scrollable settings area
        settings_canvas = tk.Canvas(center_panel, highlightthickness=0)
        settings_scrollbar = tk.Scrollbar(
            center_panel, 
            orient="vertical", 
            command=settings_canvas.yview
        )
        self.settings_frame = tk.Frame(settings_canvas)
        
        settings_canvas.configure(yscrollcommand=settings_scrollbar.set)
        settings_scrollbar.pack(side="right", fill="y")
        settings_canvas.pack(side="left", fill="both", expand=True)
        
        settings_window = settings_canvas.create_window(
            (0, 0), 
            window=self.settings_frame, 
            anchor="nw"
        )
        
        def on_settings_configure(event):
            settings_canvas.configure(scrollregion=settings_canvas.bbox("all"))
        
        def on_canvas_configure(event):
            settings_canvas.itemconfig(settings_window, width=event.width)
        
        self.settings_frame.bind("<Configure>", on_settings_configure)
        settings_canvas.bind("<Configure>", on_canvas_configure)
        
        bind_mousewheel(settings_canvas)

        self._setup_game_settings()

    def _setup_chat_panel(self, parent):
        """Setup the right panel with chat."""
        right_panel = tk.Frame(parent, width=220)
        right_panel.pack(side="right", fill="both", padx=(10, 0))

        tk.Label(
            right_panel, 
            text="Chat:", 
            font=("Arial", 10, "bold")
        ).pack(anchor="w")
        
        self.log_area = scrolledtext.ScrolledText(
            right_panel, 
            state='disabled', 
            height=12, 
            width=25, 
            font=("Arial", 9)
        )
        self.log_area.pack(fill="both", expand=True, pady=5)

        input_frame = tk.Frame(right_panel)
        input_frame.pack(fill="x", pady=5)
        
        tk.Entry(
            input_frame, 
            textvariable=self.msg_var, 
            font=("Arial", 9)
        ).pack(side="left", fill="x", expand=True)
        
        tk.Button(
            input_frame, 
            text="Invia", 
            command=self._handle_send,
            font=("Arial", 9)
        ).pack(side="right", padx=5)

    def _setup_game_settings(self):
        """Setup the game settings controls."""
        # Title
        tk.Label(
            self.settings_frame, 
            text="Game Settings", 
            font=("Arial", 12, "bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        tk.Frame(
            self.settings_frame, 
            height=1, 
            bg="#ccc"
        ).pack(fill="x", padx=10, pady=5)

        self._setup_mode_selector()
        self._setup_num_categories_selector()
        self._setup_categories_selector()
        self._setup_time_selector()
        self._setup_start_button()
        
        self._on_mode_change()
        self._update_admin_controls()

    def _setup_mode_selector(self):
        """Setup game mode radio buttons."""
        mode_frame = tk.LabelFrame(
            self.settings_frame, 
            text="Game Mode", 
            font=("Arial", 10, "bold"), 
            padx=10, 
            pady=5
        )
        mode_frame.pack(fill="x", padx=10, pady=5)

        modes = [
            (GAME_MODE_CLASSIC, "Classic", "Only Nomi + Cose + Città"),
            (GAME_MODE_CLASSIC_PLUS, "Classic Plus", "Nomi + Cose + Città + extra categories"),
            (GAME_MODE_FREE, "Free Choice", "Only selected categories")
        ]

        for mode_value, mode_name, mode_desc in modes:
            frame = tk.Frame(mode_frame)
            frame.pack(fill="x", pady=2)
            
            rb = tk.Radiobutton(
                frame, 
                text=mode_name, 
                variable=self.game_mode_var,
                value=mode_value, 
                font=("Arial", 10),
                command=self._on_mode_change
            )
            rb.pack(side="left")
            
            tk.Label(
                frame, 
                text=f"({mode_desc})", 
                font=("Arial", 8), 
                fg="#666"
            ).pack(side="left", padx=5)

    def _setup_num_categories_selector(self):
        """Setup number of extra categories selector."""
        self.num_categories_frame = tk.LabelFrame(
            self.settings_frame, 
            text="Number of extra categories to use", 
            font=("Arial", 10, "bold"), 
            padx=10, 
            pady=5
        )

        tk.Label(
            self.num_categories_frame, 
            text="The top N voted categories will be used:",
            font=("Arial", 9), 
            fg="#666"
        ).pack(anchor="w")

        num_frame = tk.Frame(self.num_categories_frame)
        num_frame.pack(fill="x", pady=5)

        for n in range(MIN_EXTRA_CATEGORIES, MAX_EXTRA_CATEGORIES + 1):
            rb = tk.Radiobutton(
                num_frame, 
                text=str(n), 
                variable=self.num_extra_categories_var,
                value=n, 
                font=("Arial", 10)
            )
            rb.pack(side="left", padx=10)

    def _setup_categories_selector(self):
        """Setup extra categories checkboxes."""
        self.categories_frame = tk.LabelFrame(
            self.settings_frame, 
            text="Extra Categories", 
            font=("Arial", 10, "bold"), 
            padx=10, 
            pady=5
        )

        self.categories_info = tk.Label(
            self.categories_frame, 
            text="Select the categories you prefer:",
            font=("Arial", 9), 
            fg="#666"
        )
        self.categories_info.pack(anchor="w", pady=(0, 5))

        checkbox_frame = tk.Frame(self.categories_frame)
        checkbox_frame.pack(fill="x")

        for i, category in enumerate(AVAILABLE_EXTRA_CATEGORIES):
            var = tk.BooleanVar(value=False)
            self.extra_category_vars[category] = var
            
            cb = tk.Checkbutton(
                checkbox_frame, 
                text=category, 
                variable=var,
                font=("Arial", 9)
            )
            row = i // 3
            col = i % 3
            cb.grid(row=row, column=col, sticky="w", padx=5, pady=1)

    def _setup_time_selector(self):
        """Setup round time selector."""
        self.time_frame = tk.LabelFrame(
            self.settings_frame, 
            text="Round Time (seconds)", 
            font=("Arial", 10, "bold"), 
            padx=10, 
            pady=5
        )
        self.time_frame.pack(fill="x", padx=10, pady=5)

        self.time_admin_info = tk.Label(
            self.time_frame, 
            text="Only the admin can modify",
            font=("Arial", 9, "italic"), 
            fg="#FF9800"
        )
        self.time_admin_info.pack(anchor="w")

        time_control_frame = tk.Frame(self.time_frame)
        time_control_frame.pack(fill="x", pady=5)

        tk.Label(
            time_control_frame, 
            text=f"{MIN_ROUND_TIME}", 
            font=("Arial", 9)
        ).pack(side="left")
        
        self.time_scale = tk.Scale(
            time_control_frame, 
            from_=MIN_ROUND_TIME, 
            to=MAX_ROUND_TIME,
            orient="horizontal", 
            variable=self.round_time_var,
            length=200, 
            font=("Arial", 9), 
            resolution=5
        )
        self.time_scale.pack(side="left", fill="x", expand=True, padx=5)
        
        tk.Label(
            time_control_frame, 
            text=f"{MAX_ROUND_TIME}", 
            font=("Arial", 9)
        ).pack(side="left")

    def _setup_start_button(self):
        """Setup start game button."""
        self.start_btn_frame = tk.Frame(self.settings_frame)
        self.start_btn_frame.pack(fill="x", padx=10, pady=15)

        self.start_game_btn = tk.Button(
            self.start_btn_frame, 
            text="START GAME", 
            bg="#FF9800", 
            fg="white", 
            font=("Arial", 12, "bold"),
            command=self._handle_start_game
        )
        self.start_game_btn.pack(fill="x", ipady=5)
        
        self.waiting_label = tk.Label(
            self.start_btn_frame, 
            text="Waiting for the admin to start the game...",
            font=("Arial", 10, "italic"), 
            fg="#666"
        )

    def _on_mode_change(self):
        """Handle game mode change."""
        mode = self.game_mode_var.get()
        
        if mode == GAME_MODE_CLASSIC:
            self.num_categories_frame.pack_forget()
            self.categories_frame.pack_forget()
        
        elif mode == GAME_MODE_CLASSIC_PLUS:
            self.num_categories_frame.pack(fill="x", padx=10, pady=5, before=self.time_frame)
            self.categories_frame.pack(fill="x", padx=10, pady=5, before=self.time_frame)
            self.categories_info.config(
                text="Select the preferred extra categories (in addition to Names+Things+Cities):",
                fg="#666"
            )
        
        elif mode == GAME_MODE_FREE:
            self.num_categories_frame.pack(fill="x", padx=10, pady=5, before=self.time_frame)
            self.categories_frame.pack(fill="x", padx=10, pady=5, before=self.time_frame)
            self.categories_info.config(
                text="Select the categories you want to play with:",
                fg="#666"
            )

    def _update_admin_controls(self):
        """Update controls based on admin status."""
        if self.is_admin:
            self.admin_label.config(text="⭐ You are the game Admin")
            self.time_scale.config(state="normal")
            self.time_admin_info.config(text="Set the round time")
            self.start_game_btn.pack(fill="x", ipady=5)
            self.waiting_label.pack_forget()
        else:
            self.admin_label.config(text="")
            self.time_scale.config(state="disabled")
            self.time_admin_info.config(text="Only the admin can modify the time")
            self.start_game_btn.pack_forget()
            self.waiting_label.pack(pady=10)

    def _handle_send(self):
        """Handle send chat message."""
        msg = self.msg_var.get().strip()
        if msg:
            self.on_send(msg)
            self.msg_var.set("")

    def _handle_start_game(self):
        """Handle start game button click."""
        mode = self.game_mode_var.get()
        selected_extra = self.get_selected_extra_categories()
        num_extra = self.num_extra_categories_var.get()
        round_time = self.round_time_var.get()

        if mode in [GAME_MODE_CLASSIC_PLUS, GAME_MODE_FREE]:
            if len(selected_extra) == 0:
                messagebox.showwarning(
                    "Selection Required", 
                    "You must select at least one extra category."
                )
                return

        game_config = {
            "mode": mode,
            "selected_categories": selected_extra,
            "num_extra_categories": num_extra,
            "round_time": round_time
        }

        if self.on_start_game:
            self.on_start_game(game_config)

    # Public methods
    def show(self):
        """Show this screen."""
        self.frame.pack(fill="both", expand=True)

    def hide(self):
        """Hide this screen."""
        self.frame.pack_forget()

    def set_admin(self, is_admin):
        """Set whether this client is the admin."""
        self.is_admin = is_admin
        self._update_admin_controls()

    def update_player_list(self, players_list, admin_username=None):
        """
        Update the player list.
        
        Args:
            players_list: List of player usernames.
            admin_username: Username of the admin (marked with star).
        """
        self.players_list.delete(0, tk.END)
        for player in players_list:
            if admin_username and player == admin_username:
                self.players_list.insert(tk.END, f"⭐ {player}")
            else:
                self.players_list.insert(tk.END, f"👤 {player}")

    def append_log(self, text):
        """Append text to the chat log."""
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, text + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def get_selected_extra_categories(self):
        """Get list of selected extra categories."""
        return [cat for cat, var in self.extra_category_vars.items() if var.get()]

    def get_game_settings(self):
        """Get current game settings."""
        return {
            "mode": self.game_mode_var.get(),
            "selected_categories": self.get_selected_extra_categories(),
            "num_extra_categories": self.num_extra_categories_var.get(),
            "round_time": self.round_time_var.get()
        }