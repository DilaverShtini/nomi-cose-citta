"""
Login screen for the Nomi Cose Città client.
"""
import tkinter as tk
from tkinter import messagebox
from src.client.gui.screens.base_screen import BaseScreen
from src.client.gui import theme
from src.common.constants import DEFAULT_SERVER_HOST


class LoginScreen(BaseScreen):
    """ Login screen """

    def _setup_ui(self):
        self.frame.configure(bg=theme.BG_PAGE)
        self._draw_notebook_lines()
        self._build_card()

    def _draw_notebook_lines(self):
        canvas = tk.Canvas(self.frame, bg=theme.BG_PAGE, highlightthickness=0)
        canvas.place(relwidth=1, relheight=1)

        def draw(event=None):
            canvas.delete("lines")
            w, h = canvas.winfo_width(), canvas.winfo_height()
            for y in range(30, h, 28):
                canvas.create_line(0, y, w, y, fill=theme.LINE_COLOR, width=1, tags="lines")
            canvas.create_line(60, 0, 60, h, fill=theme.MARGIN_RED, width=2, tags="lines")

        canvas.bind("<Configure>", lambda e: draw())

    def _build_card(self):
        card = tk.Frame(self.frame, bg=theme.BG_PAGE,
                        padx=theme.PAD_XL, pady=theme.PAD_XL,
                        relief="flat", bd=0)
        card.place(relx=0.5, rely=0.5, anchor="center")

        title_frame = tk.Frame(card, bg=theme.BG_PAGE)
        title_frame.pack(pady=(0, 6))

        for text, color in [("Nomi", theme.TITLE_N), (",", theme.INK),
                             ("Cose", theme.TITLE_C1), (",", theme.INK),
                             ("Città", theme.TITLE_C2)]:
            tk.Label(title_frame, text=text, font=theme.FONT_TITLE,
                     bg=theme.BG_PAGE, fg=color).pack(side="left")

        tk.Label(card, text="Enter in the lobby and have fun playing with your friends!",
                 font=theme.FONT_SMALL, bg=theme.BG_PAGE,
                 fg=theme.INK_LIGHT).pack(pady=(0, 20))

        theme.separator(card, color=theme.LINE_COLOR).pack(fill="x", pady=(0, 16))

        tk.Label(card, text="Username:", font=theme.FONT_LABEL,
                 bg=theme.BG_PAGE, fg=theme.INK, anchor="w").pack(fill="x", pady=(0, 4))
        self._username_var = tk.StringVar()
        self._username_entry = tk.Entry(card, textvariable=self._username_var, width=28)
        theme.style_entry(self._username_entry)
        self._username_entry.pack(fill="x", ipady=6)

        btn = tk.Button(card, text="Connect",
                        command=self._handle_connect)
        theme.style_button(btn, "primary")
        btn.pack(fill="x", pady=(22, 0), ipady=4)

        self._username_entry.bind("<Return>", lambda e: self._handle_connect())

    def on_enter(self):
        self._username_entry.focus_set()

    def _handle_connect(self):
        username = self._username_var.get().strip()
        if username:
            if self.manager.on_connect:
                self.manager.on_connect(DEFAULT_SERVER_HOST, username)
        else:
            messagebox.showerror("Error",
                "Missing data: please enter your username.")

    def get_username(self): return self._username_var.get().strip()
    def get_ip(self):       return DEFAULT_SERVER_HOST
    def clear(self):        self._username_var.set("")
