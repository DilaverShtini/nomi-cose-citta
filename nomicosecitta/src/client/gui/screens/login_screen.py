"""
Login screen component for the Nomi Cose Città client.
"""
import tkinter as tk
from tkinter import messagebox

class LoginScreen:
    """
    Login screen with username and server IP input fields.
    """

    def __init__(self, parent, on_connect_callback):
        """
        Initialize the login screen.
        
        Args:
            parent: Parent widget (root window).
            on_connect_callback: Function called when user clicks connect.
                                 Signature: on_connect(ip: str, username: str)
        """
        self.on_connect = on_connect_callback
        
        self.username_var = tk.StringVar()
        self.ip_var = tk.StringVar(value="127.0.0.1")
        
        # Create frame
        self.frame = tk.Frame(parent, padx=20, pady=20)
        self._setup_ui()

    def _setup_ui(self):
        """Setup the login screen UI."""
        tk.Label(
            self.frame, 
            text="WELCOME", 
            font=("Arial", 20, "bold")
        ).pack(pady=20)
        
        tk.Label(
            self.frame, 
            text="Username:", 
            font=("Arial", 12)
        ).pack(anchor="w")
        
        tk.Entry(
            self.frame, 
            textvariable=self.username_var
        ).pack(fill="x", pady=5)

        tk.Label(
            self.frame, 
            text="Server IP:", 
            font=("Arial", 12)
        ).pack(anchor="w")
        
        tk.Entry(
            self.frame, 
            textvariable=self.ip_var
        ).pack(fill="x", pady=5)
        
        tk.Button(
            self.frame, 
            text="ENTER THE LOBBY", 
            bg="#4CAF50", 
            fg="white", 
            font=("Arial", 11, "bold"),
            command=self._handle_connect
        ).pack(fill="x", pady=30)

    def _handle_connect(self):
        """Handle the connect button click."""
        username = self.username_var.get().strip()
        ip = self.ip_var.get().strip()
        
        if username and ip:
            self.on_connect(ip, username)
        else:
            messagebox.showerror(
                "Error", 
                "Missing data: please enter both username and server IP."
            )

    def show(self):
        """Show this screen."""
        self.frame.pack(fill="both", expand=True)

    def hide(self):
        """Hide this screen."""
        self.frame.pack_forget()

    def get_username(self):
        """Get the current username value."""
        return self.username_var.get().strip()

    