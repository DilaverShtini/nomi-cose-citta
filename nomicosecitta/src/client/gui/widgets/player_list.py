"""
Reusable player list widget.
Used in Lobby, Game, and Voting screens.
"""
import tkinter as tk
from typing import List, Optional


class PlayerList:
    """
    Displays a list of players with admin indicator.
    """

    def __init__(self, parent: tk.Widget, title: str = "Players:"):
        """
        Initialize the player list.
        
        Args:
            parent: Parent widget.
            title: Label text above the list.
        """
        self.frame = tk.Frame(parent)
        self._title = title
        
        self._setup_ui()

    def _setup_ui(self):
        """Setup the player list UI."""
        tk.Label(
            self.frame,
            text=self._title,
            font=("Arial", 10, "bold")
        ).pack(anchor="w")

        self._listbox = tk.Listbox(
            self.frame,
            height=15,
            width=16,
            bg="#f0f0f0",
            font=("Arial", 10),
            selectmode=tk.SINGLE
        )
        self._listbox.pack(fill="both", expand=True)

    def update(self, players: List[str], admin_username: Optional[str] = None):
        """
        Update the player list.
        
        Args:
            players: List of player usernames.
            admin_username: Username of the admin (marked with star).
        """
        self._listbox.delete(0, tk.END)
        
        for player in players:
            if admin_username and player == admin_username:
                self._listbox.insert(tk.END, f"⭐ {player}")
            else:
                self._listbox.insert(tk.END, f"👤 {player}")

    def get_selected(self) -> Optional[str]:
        """
        Get the currently selected player.
        
        Returns:
            Username of selected player (without icon) or None.
        """
        selection = self._listbox.curselection()
        if selection:
            text = self._listbox.get(selection[0])
            return text.replace("⭐ ", "").replace("👤 ", "")
        return None

    def clear(self):
        """Clear the player list."""
        self._listbox.delete(0, tk.END)

    def get_count(self) -> int:
        """Get the number of players in the list."""
        return self._listbox.size()

    @property
    def listbox(self) -> tk.Listbox:
        """Direct access to listbox for advanced operations."""
        return self._listbox

    def pack(self, **kwargs):
        """Pack the player list frame."""
        self.frame.pack(**kwargs)

    def grid(self, **kwargs):
        """Grid the player list frame."""
        self.frame.grid(**kwargs)