"""
Game screen for the Nomi Cose Città client.
Main gameplay with letter, timer, and category inputs.
"""
import tkinter as tk

from src.client.gui.screens.base_screen import BaseScreen
from src.client.gui.widgets import TimerDisplay
from src.client.gui.utils import bind_mousewheel
from src.common.constants import DEFAULT_CATEGORIES


class GameScreen(BaseScreen):
    """
    Main game screen.
    Displays current letter, timer, and category input fields.
    Manages round state and user answers.
    """

    def _setup_ui(self):
        """Setup the game screen UI."""
        self._letter_var = tk.StringVar(value="-")
        self._categories = DEFAULT_CATEGORIES.copy()
        self._answer_vars = {}
        
        self._setup_top_bar()
        self._setup_categories_area()
        self._setup_status_bar()

    def _setup_top_bar(self):
        """Setup top bar with letter and timer."""
        top_bar = tk.Frame(self.frame, bg="#2196F3", padx=15, pady=10)
        top_bar.pack(fill="x", pady=(0, 15))

        letter_frame = tk.Frame(top_bar, bg="#2196F3")
        letter_frame.pack(side="left")

        tk.Label(
            letter_frame,
            text="LETTER:",
            font=("Arial", 12),
            bg="#2196F3",
            fg="white"
        ).pack(side="left", padx=(0, 10))

        self._letter_label = tk.Label(
            letter_frame,
            textvariable=self._letter_var,
            font=("Arial", 36, "bold"),
            bg="#2196F3",
            fg="white",
            width=2
        )
        self._letter_label.pack(side="left")

        self._timer = TimerDisplay(top_bar, bg_color="#2196F3")
        self._timer.pack(side="right")

    def _setup_categories_area(self):
        """Setup scrollable category inputs."""
        container = tk.Frame(self.frame)
        container.pack(fill="both", expand=True, pady=10)

        self._canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=self._canvas.yview)

        self._categories_frame = tk.Frame(self._canvas)

        self._canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._canvas_window = self._canvas.create_window(
            (0, 0),
            window=self._categories_frame,
            anchor="nw"
        )

        self._categories_frame.bind("<Configure>", self._on_frame_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)

        bind_mousewheel(self._canvas)

        self._create_category_fields(DEFAULT_CATEGORIES)

    def _setup_status_bar(self):
        """Setup bottom status bar."""
        status_bar = tk.Frame(self.frame, bg="#f5f5f5", padx=10, pady=8)
        status_bar.pack(fill="x", side="bottom")

        self._status_label = tk.Label(
            status_bar,
            text="Waiting for round to start...",
            font=("Arial", 10, "italic"),
            bg="#f5f5f5",
            fg="#666"
        )
        self._status_label.pack(side="left")

        self._round_label = tk.Label(
            status_bar,
            text="Round: -",
            font=("Arial", 10),
            bg="#f5f5f5",
            fg="#333"
        )
        self._round_label.pack(side="right")

    def _on_frame_configure(self, event):
        """Update scroll region."""
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        """Update inner frame width."""
        self._canvas.itemconfig(self._canvas_window, width=event.width)

    def _create_category_fields(self, categories: list):
        """
        Create input fields for categories.
        
        Args:
            categories: List of category names.
        """
        for widget in self._categories_frame.winfo_children():
            widget.destroy()
        self._answer_vars.clear()

        self._categories = categories

        for i, category in enumerate(categories):
            row = tk.Frame(self._categories_frame, pady=8, padx=10)
            row.pack(fill="x", pady=2)

            bg = "#ffffff" if i % 2 == 0 else "#f9f9f9"
            row.configure(bg=bg)

            tk.Label(
                row,
                text=f"{category}:",
                font=("Arial", 12, "bold"),
                width=15,
                anchor="w",
                bg=bg
            ).pack(side="left", padx=(0, 10))

            var = tk.StringVar()
            self._answer_vars[category] = var

            entry = tk.Entry(
                row,
                textvariable=var,
                font=("Arial", 12),
                relief="solid",
                bd=1
            )
            entry.pack(side="left", fill="x", expand=True, ipady=5)

            entry.bind("<Return>", lambda e, idx=i: self._focus_next(idx))

    def _focus_next(self, current_index: int):
        """Move focus to next entry field."""
        rows = self._categories_frame.winfo_children()
        next_idx = current_index + 1
        
        if next_idx < len(rows):
            for child in rows[next_idx].winfo_children():
                if isinstance(child, tk.Entry):
                    child.focus_set()
                    break

    def _focus_first_entry(self):
        """Focus the first entry field."""
        rows = self._categories_frame.winfo_children()
        if rows:
            for child in rows[0].winfo_children():
                if isinstance(child, tk.Entry):
                    child.focus_set()
                    break

    # Public API

    def update_letter(self, letter: str):
        """Update the current letter display."""
        self._letter_var.set(letter.upper())

    def update_timer(self, seconds: int):
        """Update the timer display."""
        self._timer.update(seconds)

    def update_categories(self, categories: list):
        """Update categories and rebuild input fields."""
        self._create_category_fields(categories)

    def update_round_info(self, round_number: int):
        """Update round number display."""
        self._round_label.configure(text=f"Round: {round_number}")

    def update_status(self, text: str):
        """Update status bar text."""
        self._status_label.configure(text=text)

    def get_answers(self) -> dict:
        """
        Get all answers.
        
        Returns:
            Dict mapping category -> answer.
        """
        return {cat: var.get().strip() for cat, var in self._answer_vars.items()}

    def clear_answers(self):
        """Clear all answer fields."""
        for var in self._answer_vars.values():
            var.set("")

    def set_inputs_enabled(self, enabled: bool):
        """Enable or disable all input fields."""
        state = "normal" if enabled else "disabled"
        for row in self._categories_frame.winfo_children():
            for child in row.winfo_children():
                if isinstance(child, tk.Entry):
                    child.configure(state=state)

    def start_round(self, letter: str, categories: list, round_number: int):
        """
        Initialize and start a new round.
        
        Args:
            letter: The letter for this round.
            categories: List of category names.
            round_number: Current round number.
        """
        self.update_letter(letter)
        self.update_categories(categories)
        self.update_round_info(round_number)
        self.clear_answers()
        self.set_inputs_enabled(True)
        self.update_status("Enter your answers!")
        self._timer.reset()
        self._focus_first_entry()

    def end_round(self):
        """Handle end of round."""
        self.set_inputs_enabled(False)
        self.update_status("Time's up! Waiting for results...")
        self._timer.set_expired()