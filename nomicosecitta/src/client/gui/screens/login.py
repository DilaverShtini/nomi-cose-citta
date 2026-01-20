"""
Login screen for the Nomi Cose Città client.
"""
import tkinter as tk
from tkinter import messagebox

from src.client.gui.screens.base_screen import BaseScreen


class LoginScreen(BaseScreen):
    """
    Login screen with username and server IP input fields.
    
    Provides entry point for users to connect to a game server.
    """

    def _setup_ui(self):
        """Setup the login screen UI."""
        container = tk.Frame(self.frame, padx=20, pady=20)
        container.pack(expand=True)

        tk.Label(
            container,
            text="WELCOME",
            font=("Arial", 20, "bold")
        ).pack(pady=20)

        tk.Label(
            container,
            text="Username:",
            font=("Arial", 12)
        ).pack(anchor="w")

        self._username_var = tk.StringVar()
        self._username_entry = tk.Entry(
            container,
            textvariable=self._username_var,
            font=("Arial", 11)
        )
        self._username_entry.pack(fill="x", pady=5)

        tk.Label(
            container,
            text="Server IP:",
            font=("Arial", 12)
        ).pack(anchor="w")

        self._ip_var = tk.StringVar(value="127.0.0.1")
        self._ip_entry = tk.Entry(
            container,
            textvariable=self._ip_var,
            font=("Arial", 11)
        )
        self._ip_entry.pack(fill="x", pady=5)

        tk.Button(
            container,
            text="ENTER THE LOBBY",
            bg="#4CAF50",
            fg="white",
            font=("Arial", 11, "bold"),
            command=self._handle_connect
        ).pack(fill="x", pady=30)

        self._username_entry.bind("<Return>", lambda e: self._ip_entry.focus_set())
        self._ip_entry.bind("<Return>", lambda e: self._handle_connect())

    def on_enter(self):
        """Focus username field when screen appears."""
        self._username_entry.focus_set()

    def _handle_connect(self):
        """Handle the connect button click."""
        username = self._username_var.get().strip()
        ip = self._ip_var.get().strip()

        if username and ip:
            if self.manager.on_connect:
                self.manager.on_connect(ip, username)
        else:
            messagebox.showerror(
                "Error",
                "Missing data: please enter both username and server IP."
            )

    # Public API

    def get_username(self) -> str:
        """Get the current username value."""
        return self._username_var.get().strip()

    def get_ip(self) -> str:
        """Get the current IP value."""
        return self._ip_var.get().strip()

    def clear(self):
        """Clear all input fields."""
        self._username_var.set("")
        self._ip_var.set("127.0.0.1")