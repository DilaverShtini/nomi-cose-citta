"""
Timer display widget.
"""
import tkinter as tk
from src.client.gui import theme


class TimerDisplay:
    def __init__(self, parent: tk.Widget, bg_color: str = None):
        self._bg = bg_color or theme.BG_SURFACE
        self.frame = tk.Frame(parent, bg=self._bg)
        self._time_var = tk.StringVar(value="--:--")
        self._setup_ui()

    def _setup_ui(self):
        tk.Label(self.frame, text="Time remaining",
                 font=(theme.HAND_FONT, 8),
                 bg=self._bg, fg=theme.INK_LIGHT).pack(anchor="e")

        self._timer_label = tk.Label(
            self.frame,
            textvariable=self._time_var,
            font=theme.FONT_TIMER,
            bg=self._bg,
            fg=theme.BLUE_INK,
        )
        self._timer_label.pack()

    def update(self, seconds_remaining: int):
        if seconds_remaining < 0:
            seconds_remaining = 0
        m, s = divmod(seconds_remaining, 60)
        self._time_var.set(f"{m:02d}:{s:02d}")

        if seconds_remaining <= 10:
            self._timer_label.configure(fg=theme.RED_INK)
        elif seconds_remaining <= 30:
            self._timer_label.configure(fg=theme.ORANGE_INK)
        else:
            self._timer_label.configure(fg=theme.BLUE_INK)

    def reset(self):
        self._time_var.set("--:--")
        self._timer_label.configure(fg=theme.BLUE_INK)

    def set_expired(self):
        self._time_var.set("00:00")
        self._timer_label.configure(fg=theme.RED_INK)

    def pack(self, **kw): self.frame.pack(**kw)
    def grid(self, **kw): self.frame.grid(**kw)