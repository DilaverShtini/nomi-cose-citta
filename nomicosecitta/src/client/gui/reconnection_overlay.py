import tkinter as tk
from typing import Callable

class ReconnectionOverlay:
    def __init__(self, parent_root: tk.Tk, log_callback: Callable[[str], None]):
        self.root = parent_root
        self.log_callback = log_callback
        self._overlay = None
        self._overlay_status = None

    def show(self, reason: str):
        self._overlay = tk.Toplevel(self.root)
        self._overlay.title("Reconnecting…")
        self._overlay.resizable(False, False)
        self._overlay.protocol("WM_DELETE_WINDOW", lambda: None)
        self._overlay.geometry("380x160")
        
        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width()  - 380)
        y = self.root.winfo_y() + (self.root.winfo_height() - 160)
        self._overlay.geometry(f"380x160+{x}+{y}")

        tk.Label(self._overlay, text="⚠  Connection lost",
                 font=("Segoe UI", 12, "bold")).pack(pady=(18, 4))
        tk.Label(self._overlay, text=f"Reason: {reason}",
                 font=("Segoe UI", 9), fg="#888").pack()
        tk.Label(self._overlay, text="Chat with other players still works!",
                 font=("Segoe UI", 9, "italic"), fg="#2e9e5b").pack(pady=(2, 0))
                 
        self._overlay_status = tk.StringVar(value="Connecting…")
        tk.Label(self._overlay, textvariable=self._overlay_status,
                 font=("Segoe UI", 10), fg="#2b6cb0", wraplength=340).pack(pady=(8, 0))
        self._overlay.update()

    def update_status(self, msg: str):
        try:
            if self._overlay_status:
                self._overlay_status.set(msg)
            if self._overlay:
                self._overlay.update_idletasks()
        except Exception:
            pass
        print(f"[⟳] {msg}")

    def close(self):
        try:
            if self._overlay:
                self._overlay.destroy()
                self._overlay = None
        except Exception:
            pass