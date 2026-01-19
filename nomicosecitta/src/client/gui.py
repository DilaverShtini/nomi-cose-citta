import tkinter as tk
from tkinter import messagebox, scrolledtext
from src.common.constants import *

class ClientGUI:
    """
    Main GUI class for Nomi Cose Città client.

    Contains three main screens:
    1. Login: Username and server IP input.
    2. Lobby: Waiting room with game settings (mode, categories, time).
    3. Game: Main game screen with categories, inputs and timer.
    """

    def __init__(self, master, on_connect_callback, on_send_callback, on_start_game_callback=None):
        self.root = master
        self.root.title("Nomi Cose Città - Client")
        self.root.geometry("900x550")
        self.root.minsize(850, 500)
        
        self.on_connect = on_connect_callback
        self.on_send = on_send_callback
        self.on_start_game = on_start_game_callback

        # Variables
        self.username_var = tk.StringVar()
        self.ip_var = tk.StringVar(value="127.0.0.1")
        self.msg_var = tk.StringVar()

        # Game state variables
        self.current_letter = tk.StringVar(value="-")
        self.timer_var = tk.StringVar(value="--:--")
        self.categories = DEFAULT_CATEGORIES.copy()
        self.answer_vars = {}
        
        # Lobby settings variables
        self.is_admin = False
        self.game_mode_var = tk.StringVar(value=GAME_MODE_CLASSIC)
        self.num_extra_categories_var = tk.IntVar(value=2)
        self.round_time_var = tk.IntVar(value=DEFAULT_ROUND_TIME)
        self.extra_category_vars = {}

        # Frames
        self.login_frame = tk.Frame(self.root, padx=20, pady=20)
        self._setup_login()

        self.lobby_frame = tk.Frame(self.root, padx=10, pady=10)
        self._setup_lobby()

        self.game_frame = tk.Frame(self.root, padx=10, pady=10)
        self._setup_game()

        self.show_login()

    # ==================== LOGIN SCREEN ====================

    def _setup_login(self):
        tk.Label(self.login_frame, text="WELCOME", font=("Arial", 20, "bold")).pack(pady=20)
        
        tk.Label(self.login_frame, text="Username:", font=("Arial", 12)).pack(anchor="w")
        tk.Entry(self.login_frame, textvariable=self.username_var).pack(fill="x", pady=5)

        tk.Label(self.login_frame, text="Server IP:", font=("Arial", 12)).pack(anchor="w")
        tk.Entry(self.login_frame, textvariable=self.ip_var).pack(fill="x", pady=5)
        
        tk.Button(self.login_frame, text="ENTER THE LOBBY", bg="#4CAF50", fg="white", 
                  font=("Arial", 11, "bold"),
                  command=self._handle_connect_click).pack(fill="x", pady=30)
        
    def _handle_connect_click(self):
        user = self.username_var.get()
        ip = self.ip_var.get()
        if user and ip:
            self.on_connect(ip, user)
        else:
            messagebox.showerror("Error", "Missing data: please enter both username and server IP.")

    # ==================== LOBBY SCREEN ====================

    def _setup_lobby(self):
        header = tk.Frame(self.lobby_frame)
        header.pack(fill="x", pady=(0, 10))
        tk.Label(header, text="Waiting Room", font=("Arial", 16, "bold")).pack(side="left")
        
        self.admin_label = tk.Label(header, text="", font=("Arial", 10), fg="#FF9800")
        self.admin_label.pack(side="right")

        content = tk.Frame(self.lobby_frame)
        content.pack(fill="both", expand=True)

        # === LEFT PANEL: Player List ===
        left_panel = tk.Frame(content, width=140)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False)

        tk.Label(left_panel, text="Players:", font=("Arial", 10, "bold")).pack(anchor="w")
        self.players_list = tk.Listbox(left_panel, height=15, width=16, bg="#f0f0f0", 
                                        font=("Arial", 10))
        self.players_list.pack(fill="both", expand=True)

        # === CENTER PANEL: Game Settings ===
        center_panel = tk.Frame(content, relief="groove", bd=1)
        center_panel.pack(side="left", fill="both", expand=True, padx=5)

        settings_canvas = tk.Canvas(center_panel, highlightthickness=0)
        settings_scrollbar = tk.Scrollbar(center_panel, orient="vertical", 
                                          command=settings_canvas.yview)
        self.settings_frame = tk.Frame(settings_canvas)
        
        settings_canvas.configure(yscrollcommand=settings_scrollbar.set)
        settings_scrollbar.pack(side="right", fill="y")
        settings_canvas.pack(side="left", fill="both", expand=True)
        
        settings_window = settings_canvas.create_window((0, 0), window=self.settings_frame, 
                                                         anchor="nw")
        
        def on_settings_configure(event):
            settings_canvas.configure(scrollregion=settings_canvas.bbox("all"))
        
        def on_canvas_configure(event):
            settings_canvas.itemconfig(settings_window, width=event.width)
        
        self.settings_frame.bind("<Configure>", on_settings_configure)
        settings_canvas.bind("<Configure>", on_canvas_configure)

        self._bind_mousewheel(settings_canvas)

        self._setup_game_settings()

        # === RIGHT PANEL: Chat ===
        right_panel = tk.Frame(content, width=220)
        right_panel.pack(side="right", fill="both", padx=(10, 0))

        tk.Label(right_panel, text="Chat:", font=("Arial", 10, "bold")).pack(anchor="w")
        
        self.log_area = scrolledtext.ScrolledText(right_panel, state='disabled', 
                                                   height=12, width=25, font=("Arial", 9))
        self.log_area.pack(fill="both", expand=True, pady=5)

        input_frame = tk.Frame(right_panel)
        input_frame.pack(fill="x", pady=5)
        
        tk.Entry(input_frame, textvariable=self.msg_var, font=("Arial", 9)).pack(
            side="left", fill="x", expand=True)
        tk.Button(input_frame, text="Invia", command=self._handle_send_click, 
                  font=("Arial", 9)).pack(side="right", padx=5)

    def _setup_game_settings(self):
        """Setup the game settings panel in lobby."""
        
        tk.Label(self.settings_frame, text="Game Settings", 
                 font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        tk.Frame(self.settings_frame, height=1, bg="#ccc").pack(fill="x", padx=10, pady=5)

        mode_frame = tk.LabelFrame(self.settings_frame, text="Game Mode", 
                                   font=("Arial", 10, "bold"), padx=10, pady=5)
        mode_frame.pack(fill="x", padx=10, pady=5)

        modes = [
            (GAME_MODE_CLASSIC, "Classic", "Only Nomi + Cose + Città"),
            (GAME_MODE_CLASSIC_PLUS, "Classic Plus", "Nomi + Cose + Città + extra categories"),
            (GAME_MODE_FREE, "Free Choice", "Only selected categories")
        ]

        for mode_value, mode_name, mode_desc in modes:
            frame = tk.Frame(mode_frame)
            frame.pack(fill="x", pady=2)
            
            rb = tk.Radiobutton(frame, text=mode_name, variable=self.game_mode_var,
                               value=mode_value, font=("Arial", 10),
                               command=self._on_mode_change)
            rb.pack(side="left")
            
            tk.Label(frame, text=f"({mode_desc})", font=("Arial", 8), fg="#666").pack(side="left", padx=5)

        self.num_categories_frame = tk.LabelFrame(self.settings_frame, 
                                                  text="Number of extra categories to use", 
                                                  font=("Arial", 10, "bold"), padx=10, pady=5)

        tk.Label(self.num_categories_frame, 
                text="The top N voted categories will be used:",
                font=("Arial", 9), fg="#666").pack(anchor="w")

        num_frame = tk.Frame(self.num_categories_frame)
        num_frame.pack(fill="x", pady=5)

        for n in range(MIN_EXTRA_CATEGORIES, MAX_EXTRA_CATEGORIES + 1):
            rb = tk.Radiobutton(num_frame, text=str(n), variable=self.num_extra_categories_var,
                               value=n, font=("Arial", 10))
            rb.pack(side="left", padx=10)

        self.categories_frame = tk.LabelFrame(self.settings_frame, text="Extra Categories", 
                                              font=("Arial", 10, "bold"), padx=10, pady=5)

        self.categories_info = tk.Label(self.categories_frame, 
                                        text="Select the categories you prefer:",
                                        font=("Arial", 9), fg="#666")
        self.categories_info.pack(anchor="w", pady=(0, 5))

        checkbox_frame = tk.Frame(self.categories_frame)
        checkbox_frame.pack(fill="x")

        for i, category in enumerate(AVAILABLE_EXTRA_CATEGORIES):
            var = tk.BooleanVar(value=False)
            self.extra_category_vars[category] = var
            
            cb = tk.Checkbutton(checkbox_frame, text=category, variable=var,
                               font=("Arial", 9))
            row = i // 3
            col = i % 3
            cb.grid(row=row, column=col, sticky="w", padx=5, pady=1)

        self.time_frame = tk.LabelFrame(self.settings_frame, text="Round Time (seconds)", 
                                        font=("Arial", 10, "bold"), padx=10, pady=5)
        self.time_frame.pack(fill="x", padx=10, pady=5)

        self.time_admin_info = tk.Label(self.time_frame, 
                                        text="Only the admin can modify",
                                        font=("Arial", 9, "italic"), fg="#FF9800")
        self.time_admin_info.pack(anchor="w")

        time_control_frame = tk.Frame(self.time_frame)
        time_control_frame.pack(fill="x", pady=5)

        tk.Label(time_control_frame, text=f"{MIN_ROUND_TIME}", font=("Arial", 9)).pack(side="left")
        
        self.time_scale = tk.Scale(time_control_frame, from_=MIN_ROUND_TIME, to=MAX_ROUND_TIME,
                                   orient="horizontal", variable=self.round_time_var,
                                   length=200, font=("Arial", 9), resolution=5)
        self.time_scale.pack(side="left", fill="x", expand=True, padx=5)
        
        tk.Label(time_control_frame, text=f"{MAX_ROUND_TIME}", font=("Arial", 9)).pack(side="left")

        self.start_btn_frame = tk.Frame(self.settings_frame)
        self.start_btn_frame.pack(fill="x", padx=10, pady=15)

        self.start_game_btn = tk.Button(self.start_btn_frame, text="START GAME", 
                                        bg="#FF9800", fg="white", 
                                        font=("Arial", 12, "bold"),
                                        command=self._handle_start_game)
        self.start_game_btn.pack(fill="x", ipady=5)
        
        self.waiting_label = tk.Label(self.start_btn_frame, 
                                      text="Waiting for the admin to start the game...",
                                      font=("Arial", 10, "italic"), fg="#666")

        self._on_mode_change()
        self._update_admin_controls()

    def _on_mode_change(self):
        """Handle game mode radio button change."""
        mode = self.game_mode_var.get()
        
        if mode == GAME_MODE_CLASSIC:
            self.num_categories_frame.pack_forget()
            self.categories_frame.pack_forget()
        
        elif mode == GAME_MODE_CLASSIC_PLUS:
            self.num_categories_frame.pack(fill="x", padx=10, pady=5, before=self.time_frame)
            self.categories_frame.pack(fill="x", padx=10, pady=5, before=self.time_frame)
            self.categories_info.config(
                text="Select the preferred extra categories (in addition to Names+Things+Cities):",
                fg="#666")
        
        elif mode == GAME_MODE_FREE:
            self.num_categories_frame.pack(fill="x", padx=10, pady=5, before=self.time_frame)
            self.categories_frame.pack(fill="x", padx=10, pady=5, before=self.time_frame)
            self.categories_info.config(
                text="Select the categories you want to play with:",
                fg="#666")

    def _set_frame_state(self, frame, state):
        """Enable or disable all widgets in a frame."""
        for child in frame.winfo_children():
            try:
                if isinstance(child, (tk.Checkbutton, tk.Radiobutton, tk.Scale, tk.Entry)):
                    child.configure(state=state)
                elif isinstance(child, tk.Frame):
                    self._set_frame_state(child, state)
            except tk.TclError:
                pass

    def _update_admin_controls(self):
        """Update visibility of admin-only controls."""
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

    def set_admin(self, is_admin):
        """Set whether this client is the admin."""
        self.is_admin = is_admin
        self._update_admin_controls()

    def _handle_start_game(self):
        """Handle start game button click."""
        mode = self.game_mode_var.get()
        selected_extra = self.get_selected_extra_categories()
        num_extra = self.num_extra_categories_var.get()
        round_time = self.round_time_var.get()

        # Validation
        if mode in [GAME_MODE_CLASSIC_PLUS, GAME_MODE_FREE]:
            if len(selected_extra) == 0:
                messagebox.showwarning("Selection Required", 
                                      "You must select at least one extra category.")
                return
            
            if len(selected_extra) < num_extra:
                messagebox.showwarning("Insufficient Categories", 
                                      f"You have selected {len(selected_extra)} categories but at least {num_extra} are required.")
                return

        game_config = {
            "mode": mode,
            "selected_categories": selected_extra,
            "num_extra_categories": num_extra,
            "round_time": round_time
        }

        if self.on_start_game:
            self.on_start_game(game_config)
        else:
            print(f"[GUI] Start game requested: {game_config}")

    def _handle_send_click(self):
        msg = self.msg_var.get()
        if msg:
            self.on_send(msg)
            self.msg_var.set("")

    def get_selected_extra_categories(self):
        """Get list of selected extra categories."""
        return [cat for cat, var in self.extra_category_vars.items() if var.get()]

    def get_game_settings(self):
        """Get current game settings from lobby."""
        return {
            "mode": self.game_mode_var.get(),
            "selected_categories": self.get_selected_extra_categories(),
            "num_extra_categories": self.num_extra_categories_var.get(),
            "round_time": self.round_time_var.get()
        }

    # ==================== GAME SCREEN ====================

    def _setup_game(self):
        """Setup the game screen."""
        top_bar = tk.Frame(self.game_frame, bg="#2196F3", padx=15, pady=10)
        top_bar.pack(fill="x", pady=(0, 15))

        # Letter display
        letter_frame = tk.Frame(top_bar, bg="#2196F3")
        letter_frame.pack(side="left")

        tk.Label(letter_frame, text="LETTER:", font=("Arial", 12),
                 bg="#2196F3", fg="white").pack(side="left", padx=(0, 10))
        
        self.letter_label = tk.Label(letter_frame, textvariable=self.current_letter,
                                      font=("Arial", 36, "bold"), bg="#2196F3", fg="white",
                                      width=2)
        self.letter_label.pack(side="left")

        # Timer display
        timer_frame = tk.Frame(top_bar, bg="#2196F3")
        timer_frame.pack(side="right")

        tk.Label(timer_frame, text="TIME:", font=("Arial", 12),
                 bg="#2196F3", fg="white").pack(side="left", padx=(0, 10))
        
        self.timer_label = tk.Label(timer_frame, textvariable=self.timer_var,
                                     font=("Arial", 28, "bold"), bg="#2196F3", fg="yellow")
        self.timer_label.pack(side="left")

        # Categories container
        categories_container = tk.Frame(self.game_frame)
        categories_container.pack(fill="both", expand=True, pady=10)

        self.categories_canvas = tk.Canvas(categories_container, highlightthickness=0)
        scrollbar = tk.Scrollbar(categories_container, orient="vertical", 
                                 command=self.categories_canvas.yview)
        
        self.categories_inner_frame = tk.Frame(self.categories_canvas)

        self.categories_canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.categories_canvas.pack(side="left", fill="both", expand=True)

        self.canvas_window = self.categories_canvas.create_window(
            (0, 0), window=self.categories_inner_frame, anchor="nw"
        )

        self.categories_inner_frame.bind("<Configure>", self._on_frame_configure)
        self.categories_canvas.bind("<Configure>", self._on_canvas_configure)

        self._bind_mousewheel(self.categories_canvas)
        
        self._create_category_fields(DEFAULT_CATEGORIES)

        # Status bar
        status_bar = tk.Frame(self.game_frame, bg="#f5f5f5", padx=10, pady=8)
        status_bar.pack(fill="x", side="bottom")

        self.status_label = tk.Label(status_bar, text="Waiting for the round to start...",
                                     font=("Arial", 10, "italic"), bg="#f5f5f5", fg="#666")
        self.status_label.pack(side="left")

        self.round_label = tk.Label(status_bar, text="Round: -",
                                    font=("Arial", 10), bg="#f5f5f5", fg="#333")
        self.round_label.pack(side="right")

    def _on_frame_configure(self, event):
        """Update scroll region when frame changes."""
        self.categories_canvas.configure(scrollregion=self.categories_canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        """Update inner frame width when canvas resizes."""
        self.categories_canvas.itemconfig(self.canvas_window, width=event.width)

    def _create_category_fields(self, categories):
        """Create input fields for each category."""
        for widget in self.categories_inner_frame.winfo_children():
            widget.destroy()
        self.answer_vars.clear()

        self.categories = categories

        for i, category in enumerate(categories):
            row_frame = tk.Frame(self.categories_inner_frame, pady=8, padx=10)
            row_frame.pack(fill="x", pady=2)

            bg_color = "#ffffff" if i % 2 == 0 else "#f9f9f9"
            row_frame.configure(bg=bg_color)
            
            label = tk.Label(row_frame, text=f"{category}:", font=("Arial", 12, "bold"),
                             width=15, anchor="w", bg=bg_color)
            label.pack(side="left", padx=(0, 10))

            answer_var = tk.StringVar()
            self.answer_vars[category] = answer_var
            
            entry = tk.Entry(row_frame, textvariable=answer_var, font=("Arial", 12),
                            relief="solid", bd=1)
            entry.pack(side="left", fill="x", expand=True, ipady=5)

            entry.bind("<Return>", lambda e, idx=i: self._focus_next_entry(idx))

    # ==================== GAME GUI PUBLIC METHODS ====================

    def update_game_letter(self, letter):
        """Update the current letter display."""
        self.current_letter.set(letter.upper())

    def update_timer(self, seconds_remaining):
        """Update the timer display with the server-provided time."""
        if seconds_remaining < 0:
            seconds_remaining = 0

        minutes = seconds_remaining // 60
        seconds = seconds_remaining % 60
        self.timer_var.set(f"{minutes:02d}:{seconds:02d}")

        if seconds_remaining <= 10:
            self.timer_label.configure(fg="red")
        elif seconds_remaining <= 30:
            self.timer_label.configure(fg="orange")
        else:
            self.timer_label.configure(fg="yellow")

    def update_categories(self, categories):
        """Update the game with new categories."""
        self._create_category_fields(categories)

    def update_round_info(self, round_number):
        """Update the round number display."""
        self.round_label.configure(text=f"Round: {round_number}")

    def update_game_status(self, status_text):
        """Update the status bar text."""
        self.status_label.configure(text=status_text)

    def get_answers(self):
        """Get all current answers from the input fields."""
        return {category: var.get().strip() for category, var in self.answer_vars.items()}
    
    def clear_answers(self):
        """Clear all answer input fields."""
        for var in self.answer_vars.values():
            var.set("")

    def set_inputs_enabled(self, enabled):
        """Enable or disable all input fields."""
        state = "normal" if enabled else "disabled"
        for row in self.categories_inner_frame.winfo_children():
            for child in row.winfo_children():
                if isinstance(child, tk.Entry):
                    child.configure(state=state)

    def start_round(self, letter, categories, round_number):
        """Initialize and display a new round."""
        self.update_game_letter(letter)
        self.update_categories(categories)
        self.update_round_info(round_number)
        self.clear_answers()
        self.set_inputs_enabled(True)
        self.update_game_status("Inserisci le tue risposte!")
        self.timer_label.configure(fg="yellow") 

        if self.categories_inner_frame.winfo_children():
            first_row = self.categories_inner_frame.winfo_children()[0]
            for child in first_row.winfo_children():
                if isinstance(child, tk.Entry):
                    child.focus_set()
                    break
    
    def end_round(self):
        """Handle end of round - disable inputs and update status."""
        self.set_inputs_enabled(False)
        self.update_game_status("Tempo scaduto! In attesa dei risultati...")
        self.timer_var.set("00:00")
        self.timer_label.configure(fg="red")

    # ==================== SCREEN NAVIGATION ====================

    def show_login(self):
        """Show the login screen."""
        self.lobby_frame.pack_forget()
        self.game_frame.pack_forget()
        self.login_frame.pack(fill="both", expand=True)

    def show_lobby(self):
        """Show the lobby screen."""
        self.login_frame.pack_forget()
        self.game_frame.pack_forget()
        self.lobby_frame.pack(fill="both", expand=True)
    
    def show_game(self):
        """Show the game screen."""
        self.login_frame.pack_forget()
        self.lobby_frame.pack_forget()
        self.game_frame.pack(fill="both", expand=True)

    # ==================== LOBBY METHODS ====================

    def append_log(self, text):
        """Append text to the lobby chat log."""
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, text + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def update_player_list(self, players_list, admin_username=None):
        """
        Update the player list in the lobby.
        
        Args:
            players_list: List of player usernames
            admin_username: Username of the admin (will be marked with a star)
        """
        self.players_list.delete(0, tk.END)
        for player in players_list:
            if admin_username and player == admin_username:
                self.players_list.insert(tk.END, f"⭐ {player}")
            else:
                self.players_list.insert(tk.END, f"👤 {player}")

    # ==================== GAME METHODS ====================

    def _focus_next_entry(self, current_index):
        """Move focus to the next entry field."""
        entries = self.categories_inner_frame.winfo_children()
        next_index = current_index + 1
        if next_index < len(entries):
            next_row = entries[next_index]
            for child in next_row.winfo_children():
                if isinstance(child, tk.Entry):
                    child.focus_set()
                    break
    
    def _bind_mousewheel(self, canvas):
        """Bind mouse wheel scrolling to a canvas."""
        def _on_mousewheel(event):
            # Windows and MacOS
            if event.delta:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            # Linux (Button-4 is scroll up, Button-5 is scroll down)
            elif event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")
        
        def _bind_to_canvas(event):
            # Windows/MacOS
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            # Linux
            canvas.bind_all("<Button-4>", _on_mousewheel)
            canvas.bind_all("<Button-5>", _on_mousewheel)
        
        def _unbind_from_canvas(event):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")
        
        # Bind when mouse enters the canvas, unbind when it leaves
        canvas.bind("<Enter>", _bind_to_canvas)
        canvas.bind("<Leave>", _unbind_from_canvas)