"""
Chat panel widget — stile quaderno.
"""
import tkinter as tk
from tkinter import scrolledtext
from typing import Callable, Optional
from src.client.gui import theme


class ChatPanel:
    def __init__(self, parent: tk.Widget,
                 on_send: Optional[Callable[[str], None]] = None,
                 title: str = "Chat:"):
        self.frame = tk.Frame(parent, bg=theme.BG_PAGE)
        self.on_send = on_send
        self._title = title
        self._msg_var = tk.StringVar()
        self._setup_ui()

    def _setup_ui(self):
        tk.Label(self.frame, text=self._title,
                 font=theme.FONT_LABEL,
                 bg=theme.BG_PAGE, fg=theme.INK,
                 anchor="w").pack(fill="x", pady=(0, 6))

        self._log_area = scrolledtext.ScrolledText(
            self.frame, state="disabled", height=12, width=10)
        theme.style_scrolled_text(self._log_area)
        self._log_area.configure(
            highlightthickness=1, highlightbackground=theme.LINE_COLOR)
        self._log_area.pack(fill="both", expand=True)

        input_row = tk.Frame(self.frame, bg=theme.LINE_COLOR, pady=1)
        input_row.pack(fill="x", pady=(6, 0))

        inner = tk.Frame(input_row, bg=theme.BG_PAGE)
        inner.pack(fill="x")

        send_btn = tk.Button(inner, text="Send", command=self._handle_send, width=6)
        theme.style_button(send_btn, "primary")
        send_btn.configure(pady=5, font=(theme.HAND_FONT, 10, "bold"))
        send_btn.pack(side="right", padx=2, pady=2)

        self._entry = tk.Entry(inner, textvariable=self._msg_var)
        theme.style_entry(self._entry)
        self._entry.configure(highlightthickness=0, bd=0)
        self._entry.pack(side="left", fill="x", expand=True, ipady=5, padx=(6, 2))
        self._entry.bind("<Return>", lambda e: self._handle_send())

    def _handle_send(self):
        msg = self._msg_var.get().strip()
        if msg and self.on_send:
            self.on_send(msg)
            self._msg_var.set("")

    def append(self, text: str):
        self._log_area.config(state="normal")
        self._log_area.insert(tk.END, text + "\n")
        self._log_area.see(tk.END)
        self._log_area.config(state="disabled")

    def clear(self):
        self._log_area.config(state="normal")
        self._log_area.delete(1.0, tk.END)
        self._log_area.config(state="disabled")

    def set_enabled(self, enabled: bool):
        self._entry.configure(state="normal" if enabled else "disabled")

    def focus_input(self): self._entry.focus_set()
    def pack(self, **kw):  self.frame.pack(**kw)
    def grid(self, **kw):  self.frame.grid(**kw)