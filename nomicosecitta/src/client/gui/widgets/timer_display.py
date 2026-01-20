"""
Reusable timer display widget.
Used in Game and Voting screens.
"""
import tkinter as tk


class TimerDisplay:
    """
    Displays a countdown timer with color-coded urgency.
    """

    def __init__(self, parent: tk.Widget, bg_color: str = "#2196F3"):
        """
        Initialize the timer display.
        
        Args:
            parent: Parent widget.
            bg_color: Background color for the timer frame.
        """
        self.frame = tk.Frame(parent, bg=bg_color)
        self._time_var = tk.StringVar(value="--:--")
        self._bg_color = bg_color
        
        self._setup_ui()

    def _setup_ui(self):
        """Setup the timer UI."""
        tk.Label(
            self.frame,
            text="TIME:",
            font=("Arial", 12),
            bg=self._bg_color,
            fg="white"
        ).pack(side="left", padx=(0, 10))

        self._timer_label = tk.Label(
            self.frame,
            textvariable=self._time_var,
            font=("Arial", 28, "bold"),
            bg=self._bg_color,
            fg="yellow"
        )
        self._timer_label.pack(side="left")

    def update(self, seconds_remaining: int):
        """
        Update the timer display.
        
        Args:
            seconds_remaining: Number of seconds remaining.
        """
        if seconds_remaining < 0:
            seconds_remaining = 0

        minutes = seconds_remaining // 60
        seconds = seconds_remaining % 60
        self._time_var.set(f"{minutes:02d}:{seconds:02d}")

        if seconds_remaining <= 10:
            self._timer_label.configure(fg="red")
        elif seconds_remaining <= 30:
            self._timer_label.configure(fg="orange")
        else:
            self._timer_label.configure(fg="yellow")

    def reset(self):
        """Reset timer to initial state."""
        self._time_var.set("--:--")
        self._timer_label.configure(fg="yellow")

    def set_expired(self):
        """Set timer to expired state (00:00 in red)."""
        self._time_var.set("00:00")
        self._timer_label.configure(fg="red")

    def pack(self, **kwargs):
        """Pack the timer frame."""
        self.frame.pack(**kwargs)

    def grid(self, **kwargs):
        """Grid the timer frame."""
        self.frame.grid(**kwargs)