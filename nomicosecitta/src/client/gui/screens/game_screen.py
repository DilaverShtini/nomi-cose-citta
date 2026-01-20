"""
Game screen component for the Nomi Cose Città client.
Contains the letter display, timer, and category input fields.
"""
import tkinter as tk

from src.common.constants import DEFAULT_CATEGORIES
from src.client.gui.utils import bind_mousewheel


class GameScreen:
    """
    Main game screen with letter, timer, and category inputs.
    """

    def __init__(self, parent):
        """
        Initialize the game screen.
        
        Args:
            parent: Parent widget (root window).
        """
        self.current_letter = tk.StringVar(value="-")
        self.timer_var = tk.StringVar(value="--:--")
        self.categories = DEFAULT_CATEGORIES.copy()
        self.answer_vars = {}  # {category: StringVar}
        
        # Create frame
        self.frame = tk.Frame(parent, padx=10, pady=10)
        self._setup_ui()

    def _setup_ui(self):
        """Setup the game screen UI."""
        self._setup_top_bar()
        self._setup_categories_area()
        self._setup_status_bar()

    def _setup_top_bar(self):
        """Setup the top bar with letter and timer."""
        top_bar = tk.Frame(self.frame, bg="#2196F3", padx=15, pady=10)
        top_bar.pack(fill="x", pady=(0, 15))

        # Letter display
        letter_frame = tk.Frame(top_bar, bg="#2196F3")
        letter_frame.pack(side="left")

        tk.Label(
            letter_frame, 
            text="LETTER:", 
            font=("Arial", 12),
            bg="#2196F3", 
            fg="white"
        ).pack(side="left", padx=(0, 10))
        
        self.letter_label = tk.Label(
            letter_frame, 
            textvariable=self.current_letter,
            font=("Arial", 36, "bold"), 
            bg="#2196F3", 
            fg="white",
            width=2
        )
        self.letter_label.pack(side="left")

        # Timer display
        timer_frame = tk.Frame(top_bar, bg="#2196F3")
        timer_frame.pack(side="right")

        tk.Label(
            timer_frame, 
            text="TIME:", 
            font=("Arial", 12),
            bg="#2196F3", 
            fg="white"
        ).pack(side="left", padx=(0, 10))
        
        self.timer_label = tk.Label(
            timer_frame, 
            textvariable=self.timer_var,
            font=("Arial", 28, "bold"), 
            bg="#2196F3", 
            fg="yellow"
        )
        self.timer_label.pack(side="left")

    def _setup_categories_area(self):
        """Setup the scrollable categories input area."""
        categories_container = tk.Frame(self.frame)
        categories_container.pack(fill="both", expand=True, pady=10)

        self.categories_canvas = tk.Canvas(categories_container, highlightthickness=0)
        scrollbar = tk.Scrollbar(
            categories_container, 
            orient="vertical", 
            command=self.categories_canvas.yview
        )
        
        self.categories_inner_frame = tk.Frame(self.categories_canvas)

        self.categories_canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.categories_canvas.pack(side="left", fill="both", expand=True)

        self.canvas_window = self.categories_canvas.create_window(
            (0, 0), 
            window=self.categories_inner_frame, 
            anchor="nw"
        )

        self.categories_inner_frame.bind("<Configure>", self._on_frame_configure)
        self.categories_canvas.bind("<Configure>", self._on_canvas_configure)

        bind_mousewheel(self.categories_canvas)
        
        self._create_category_fields(DEFAULT_CATEGORIES)

    def _setup_status_bar(self):
        """Setup the bottom status bar."""
        status_bar = tk.Frame(self.frame, bg="#f5f5f5", padx=10, pady=8)
        status_bar.pack(fill="x", side="bottom")

        self.status_label = tk.Label(
            status_bar, 
            text="Waiting for the round to start...",
            font=("Arial", 10, "italic"), 
            bg="#f5f5f5", 
            fg="#666"
        )
        self.status_label.pack(side="left")

        self.round_label = tk.Label(
            status_bar, 
            text="Round: -",
            font=("Arial", 10), 
            bg="#f5f5f5", 
            fg="#333"
        )
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
            categories: List of category names.
        """
        for widget in self.categories_inner_frame.winfo_children():
            widget.destroy()
        self.answer_vars.clear()

        self.categories = categories

        for i, category in enumerate(categories):
            row_frame = tk.Frame(self.categories_inner_frame, pady=8, padx=10)
            row_frame.pack(fill="x", pady=2)

            bg_color = "#ffffff" if i % 2 == 0 else "#f9f9f9"
            row_frame.configure(bg=bg_color)
            
            label = tk.Label(
                row_frame, 
                text=f"{category}:", 
                font=("Arial", 12, "bold"),
                width=15, 
                anchor="w", 
                bg=bg_color
            )
            label.pack(side="left", padx=(0, 10))

            answer_var = tk.StringVar()
            self.answer_vars[category] = answer_var
            
            entry = tk.Entry(
                row_frame, 
                textvariable=answer_var, 
                font=("Arial", 12),
                relief="solid", 
                bd=1
            )
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

    # Public methods
    def show(self):
        """Show this screen."""
        self.frame.pack(fill="both", expand=True)

    def hide(self):
        """Hide this screen."""
        self.frame.pack_forget()

    def update_letter(self, letter):
        """Update the current letter display."""
        self.current_letter.set(letter.upper())

    def update_timer(self, seconds_remaining):
        """
        Update the timer display.
        
        Args:
            seconds_remaining: Number of seconds remaining.
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
        """Update the game with new categories."""
        self._create_category_fields(categories)

    def update_round_info(self, round_number):
        """Update the round number display."""
        self.round_label.configure(text=f"Round: {round_number}")

    def update_status(self, status_text):
        """Update the status bar text."""
        self.status_label.configure(text=status_text)

    def get_answers(self):
        """
        Get all current answers from the input fields.
        
        Returns:
            dict: {category: answer} mapping.
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
            enabled: True to enable, False to disable.
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
            letter: The letter for this round.
            categories: List of category names.
            round_number: The current round number.
        """
        self.update_letter(letter)
        self.update_categories(categories)
        self.update_round_info(round_number)
        self.clear_answers()
        self.set_inputs_enabled(True)
        self.update_status("Enter your answers!")
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
        self.update_status("Tempo scaduto! In attesa dei risultati...")
        self.timer_var.set("00:00")
        self.timer_label.configure(fg="red")