import tkinter as tk
from tkinter import messagebox, scrolledtext
from src.common.constants import DEFAULT_CATEGORIES

class ClientGUI:
    """
    Main GUI class for Nomi Cose Città client.

    Contains three main screens:
    1. Login: Username and server IP input.
    2. Lobby: Waiting room with connected palyer list.
    3. Game: Main game screen with categories, inputs and timer.
    """

    def __init__(self, master, on_connect_callback, on_send_callback):
        self.root = master
        self.root.title("Nomi Cose Città - Client")
        self.root.geometry("600x450")
        
        self.on_connect = on_connect_callback
        self.on_send = on_send_callback

        # Variables
        self.username_var = tk.StringVar()
        self.ip_var = tk.StringVar(value="127.0.0.1")
        self.msg_var = tk.StringVar()

        # Game state variables
        self.current_letter = tk.StringVar(value="-")
        self.timer_var = tk.StringVar(value="--:--")
        self.categories = DEFAULT_CATEGORIES.copy()
        self.answer_vars = {} # Dictionary to store answer StringVars

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
        tk.Label(self.login_frame, text="BENVENUTO", font=("Arial", 20, "bold")).pack(pady=20)
        
        tk.Label(self.login_frame, text="Username:", font=("Arial", 12)).pack(anchor="w")
        tk.Entry(self.login_frame, textvariable=self.username_var).pack(fill="x", pady=5)

        tk.Label(self.login_frame, text="Server IP:", font=("Arial", 12)).pack(anchor="w")
        tk.Entry(self.login_frame, textvariable=self.ip_var).pack(fill="x", pady=5)
        
        tk.Button(self.login_frame, text="ENTRA IN LOBBY", bg="#4CAF50", fg="white", font=("Arial", 11, "bold"),
                  command=self._handle_connect_click).pack(fill="x", pady=30)
        
    def _handle_connect_click(self):
        user = self.username_var.get()
        ip = self.ip_var.get()
        if user and ip:
            self.on_connect(ip, user)
        else:
            messagebox.showerror("Errore", "Dati mancanti")

    # ==================== LOBBY SCREEN ====================

    def _setup_lobby(self):
        header = tk.Frame(self.lobby_frame)
        header.pack(fill="x", pady=(0, 10))
        tk.Label(header, text="Sala d'Attesa", font=("Arial", 16, "bold")).pack(side="left")

        content = tk.Frame(self.lobby_frame)
        content.pack(fill="both", expand=True)

        left_panel = tk.Frame(content, width=150)
        left_panel.pack(side="left", fill="y", padx=(0, 10))

        tk.Label(left_panel, text="Giocatori Connessi:", font=("Arial", 10, "bold")).pack(anchor="w")

        self.players_list = tk.Listbox(left_panel, height=15, width=20, bg="#f0f0f0")
        self.players_list.pack(fill="both", expand=True)

        right_panel = tk.Frame(content)
        right_panel.pack(side="right", fill="both", expand=True)

        tk.Label(right_panel, text="Chat di Lobby:", font=("Arial", 10, "bold")).pack(anchor="w")
        
        self.log_area = scrolledtext.ScrolledText(right_panel, state='disabled', height=15)
        self.log_area.pack(fill="both", expand=True, pady=5)

        input_frame = tk.Frame(right_panel)
        input_frame.pack(fill="x", pady=5)
        
        tk.Entry(input_frame, textvariable=self.msg_var).pack(side="left", fill="x", expand=True)
        tk.Button(input_frame, text="Invia", command=self._handle_send_click).pack(side="right", padx=5)

    def _handle_send_click(self):
        msg = self.msg_var.get()
        if msg:
            self.on_send(msg)
            self.msg_var.set("")

    # ==================== GAME SCREEN ====================

    def _setup_game(self):
        """
        Setup the game screen with:
        - Current letter display
        - Server-side timer display
        - Category input fields
        - Round info
        """

        top_bar = tk.Frame(self.game_frame, bg="#2196F3", padx=15, pady=10)
        top_bar.pack(fill="x", pady=(0, 15))

        # Letter display
        letter_frame = tk.Frame(top_bar, bg="#2196F3")
        letter_frame.pack(side="left")

        tk.Label(letter_frame, text="LETTERA:", font=("Arial", 12),
                bg="#2196F3", fg="white").pack(side="left", padx=(0, 10))
        
        self.letter_label = tk.Label(letter_frame, textvariable=self.current_letter,
                                    font=("Arial", 36, "bold"), bg="#2196F3", fg="white",
                                    width=2)
        self.letter_label.pack(side="left")

        # Timer display
        timer_frame = tk.Frame(top_bar, bg="#2196F3")
        timer_frame.pack(side="right")

        tk.Label(timer_frame, text="TEMPO:", font=("Arial", 12),
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

        self._create_category_fields(DEFAULT_CATEGORIES)

        # Status bar
        status_bar = tk.Frame(self.game_frame, bg="#f5f5f5", padx=10, pady=8)
        status_bar.pack(fill="x", side="bottom")

        self.status_label = tk.Label(status_bar, text="In attesa dell'inizio del round...",
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
        """
        Create input fields for each category.
        
        Args:
            categories: List of category names
        """
        for widget in self.categories_inner_frame.winfo_children():
            widget.destroy()
        self.answer_vars.clear()

        self.categories = categories

        for i, category in enumerate(categories):
            row_frame = tk.Frame(self. categories_inner_frame, pady=8, padx=10)
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

    # ==================== GAME GUI PUBLIC METHODS ====================

    def update_game_letter(self, letter):
        """
        Update the current letter display.
        
        Args:
            letter: The letter for the current round
        """
        self.current_letter.set(letter.upper())

    def update_timer(self, seconds_remaining):
        """
        Update the timer display with the server-provided time.

        Args:
            seconds_remaining: Number of seconds left in the round
        """
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
        """
        Update the game with new categories. 
        
        Args:
            categories: List of category names
        """
        self._create_category_fields(categories)

    def update_game_status(self, status_text):
        """
        Update the status bar text.
        
        Args:
            status_text: Status message to display
        """
        self.status_label.configure(text=status_text)

    def update_round_info(self, round_number):
        """
        Update the round number display.
        
        Args:
            round_number: Current round number
        """
        self.round_label.configure(text=f"Round: {round_number}")

    def get_answers(self):
        """
        Get all current answers from the input fields.
        
        Returns:
            dict: Dictionary mapping category names to answers
        """
        return {category: var.get().strip() for category, var in self.answer_vars.items()}
    
    def clear_answers(self):
        """Clear all answer input fields."""
        for var in self.answer_vars.values():
            var.set("")

    def set_inputs_enabled(self, enabled):
        """
        Enable or disable all input fields.
        
        Args:
            enabled: True to enable inputs, False to disable
        """
        state = "normal" if enabled else "disabled"
        for row in self.categories_inner_frame.winfo_children():
            for child in row.winfo_children():
                if isinstance(child, tk.Entry):
                    child.configure(state=state)

    def start_round(self, letter, categories, round_number):
        """
        Initialize and display a new round.
        
        Args:
            letter: The letter for this round
            categories: List of categories for this round
            round_number: Current round number
        """

        self.update_game_letter(letter)
        self.update_categories(categories)
        self.update_round_info(round_number)
        self.clear_answers()
        self.set_inputs_enabled(True)
        self.update_game_status("Enter your answers!")
        self.timer_label.configure(fg="yellow") 

        if self.categories_inner_frame.winfo_children():
            first_row = self.categories_inner_frame.winfo_children()[0]
            for child in first_row.winfo_children():
                if isinstance(child, tk.Entry):
                    child.focus_set()
                    break
    
    def end_round(self):
        """
        Handle end of round - disable inputs and update status.
        """
        self.set_inputs_enabled(False)
        self.update_game_status("Time's up! Waiting for the results...")
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

    def update_player_list(self, players_list):
        """Update the player list in the lobby."""
        self.players_list.delete(0, tk.END)
        for player in players_list:
            self.players_list.insert(tk.END, f"👤 {player}")
