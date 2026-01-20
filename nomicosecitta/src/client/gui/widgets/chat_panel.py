"""
Reusable chat panel widget.
Used in Lobby and Voting screens.
"""
import tkinter as tk
from tkinter import scrolledtext
from typing import Callable, Optional


class ChatPanel:
    """
    Chat panel with message log and input field.
    """

    def __init__(self, parent: tk.Widget, on_send: Optional[Callable[[str], None]] = None,
                 title: str = "Chat:"):
        """
        Initialize the chat panel.
        
        Args:
            parent: Parent widget.
            on_send: Callback when user sends a message. Signature: (message: str) -> None
            title: Label text above the chat.
        """
        self.frame = tk.Frame(parent)
        self.on_send = on_send
        self._title = title
        self._msg_var = tk.StringVar()
        
        self._setup_ui()

    def _setup_ui(self):
        """Setup the chat panel UI."""
        tk.Label(
            self.frame,
            text=self._title,
            font=("Arial", 10, "bold")
        ).pack(anchor="w")

        self._log_area = scrolledtext.ScrolledText(
            self.frame,
            state='disabled',
            height=12,
            width=25,
            font=("Arial", 9)
        )
        self._log_area.pack(fill="both", expand=True, pady=5)

        input_frame = tk.Frame(self.frame)
        input_frame.pack(fill="x", pady=5)

        self._entry = tk.Entry(
            input_frame,
            textvariable=self._msg_var,
            font=("Arial", 9)
        )
        self._entry.pack(side="left", fill="x", expand=True)
        self._entry.bind("<Return>", lambda e: self._handle_send())

        tk.Button(
            input_frame,
            text="Invia",
            command=self._handle_send,
            font=("Arial", 9)
        ).pack(side="right", padx=5)

    def _handle_send(self):
        """Handle send button click or Enter key."""
        msg = self._msg_var.get().strip()
        if msg and self.on_send:
            self.on_send(msg)
            self._msg_var.set("")

    def append(self, text: str):
        """
        Add a message to the chat log.
        
        Args:
            text: Message text to append.
        """
        self._log_area.config(state='normal')
        self._log_area.insert(tk.END, text + "\n")
        self._log_area.see(tk.END)
        self._log_area.config(state='disabled')

    def clear(self):
        """Clear all messages from the chat log."""
        self._log_area.config(state='normal')
        self._log_area.delete(1.0, tk.END)
        self._log_area.config(state='disabled')

    def set_enabled(self, enabled: bool):
        """
        Enable or disable the input field.
        
        Args:
            enabled: True to enable input, False to disable.
        """
        state = "normal" if enabled else "disabled"
        self._entry.configure(state=state)

    def focus_input(self):
        """Set focus to the input field."""
        self._entry.focus_set()

    def pack(self, **kwargs):
        """Pack the chat panel frame."""
        self.frame.pack(**kwargs)

    def grid(self, **kwargs):
        """Grid the chat panel frame."""
        self.frame.grid(**kwargs)