"""
Player list widget.
"""
import tkinter as tk
from typing import List, Optional
from src.client.gui import theme


class PlayerList:
    def __init__(self, parent: tk.Widget, title: str = "Players:"):
        self.frame = tk.Frame(parent, bg=theme.BG_PAGE)
        self._title = title
        self._setup_ui()

    def _setup_ui(self):
        tk.Label(self.frame, text=self._title,
                 font=theme.FONT_LABEL,
                 bg=theme.BG_PAGE, fg=theme.INK,
                 anchor="w").pack(fill="x", pady=(0, 6))

        self._listbox = tk.Listbox(self.frame, height=15, width=16)
        theme.style_listbox(self._listbox)
        self._listbox.pack(fill="both", expand=True)

    def update(self, players: List[str], admin_username: Optional[str] = None):
        self._listbox.delete(0, tk.END)
        for player in players:
            if admin_username and player == admin_username:
                self._listbox.insert(tk.END, f"⭐ {player}")
            else:
                self._listbox.insert(tk.END, f"{player}")

    def get_selected(self) -> Optional[str]:
        sel = self._listbox.curselection()
        if sel:
            return self._listbox.get(sel[0]).replace("⭐ ", "").strip()
        return None

    def clear(self):        self._listbox.delete(0, tk.END)
    def get_count(self):    return self._listbox.size()

    @property
    def listbox(self): return self._listbox

    def pack(self, **kw): self.frame.pack(**kw)
    def grid(self, **kw): self.frame.grid(**kw)