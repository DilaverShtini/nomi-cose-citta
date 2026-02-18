"""
Game screen for the Nomi Cose Città client.
"""
import tkinter as tk
from src.client.gui.screens.base_screen import BaseScreen
from src.client.gui.widgets import TimerDisplay
from src.client.gui.utils import bind_mousewheel
from src.client.gui import theme
from src.common.constants import DEFAULT_CATEGORIES


class GameScreen(BaseScreen):
    """Game screen — stile quaderno scolastico."""

    def _setup_ui(self):
        self.frame.configure(bg=theme.BG_PAGE)
        self._letter_var = tk.StringVar(value="-")
        self._categories = DEFAULT_CATEGORIES.copy()
        self._answer_vars = {}

        self._setup_top_bar()
        self._setup_categories_area()
        self._setup_status_bar()

    # Top bar

    def _setup_top_bar(self):
        bar = tk.Frame(self.frame, bg=theme.BG_SURFACE,
                       padx=theme.PAD_LG, pady=theme.PAD_SM,
                       relief="flat")
        bar.pack(fill="x")

        title_frame = tk.Frame(bar, bg=theme.BG_SURFACE)
        title_frame.pack(side="left")

        for text, color in [("Nomi", theme.TITLE_N), (",", theme.INK),
                             ("Cose", theme.TITLE_C1), (",", theme.INK),
                             ("Città", theme.TITLE_C2)]:
            tk.Label(title_frame, text=text, font=(theme.HAND_FONT, 13, "bold"),
                     bg=theme.BG_SURFACE, fg=color).pack(side="left")

        center = tk.Frame(bar, bg=theme.BG_SURFACE)
        center.pack(side="left", expand=True)

        self._round_label = tk.Label(center, text="Round  —",
                                     font=theme.FONT_SMALL,
                                     bg=theme.BG_SURFACE, fg=theme.INK_LIGHT)
        self._round_label.pack()

        letter_row = tk.Frame(center, bg=theme.BG_SURFACE)
        letter_row.pack()

        tk.Label(letter_row, text="Letter:",
                 font=theme.FONT_BODY,
                 bg=theme.BG_SURFACE, fg=theme.INK).pack(side="left", padx=(0, 10))

        self._letter_label = tk.Label(letter_row, textvariable=self._letter_var,
                                      font=theme.FONT_LETTER,
                                      bg=theme.BG_SURFACE, fg=theme.RED_INK)
        self._letter_label.pack(side="left")

        self._timer = TimerDisplay(bar, bg_color=theme.BG_SURFACE)
        self._timer.pack(side="right")

        theme.separator(self.frame, color=theme.LINE_DARK).pack(fill="x")

    # Categories area

    def _setup_categories_area(self):
        container = tk.Frame(self.frame, bg=theme.BG_PAGE)
        container.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(container, bg=theme.BG_PAGE, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=self._canvas.yview,
                                 bg=theme.BG_SURFACE, troughcolor=theme.BG_SURFACE,
                                 relief="flat", bd=0)

        self._categories_frame = tk.Frame(self._canvas, bg=theme.BG_PAGE)

        self._canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._canvas_window = self._canvas.create_window(
            (0, 0), window=self._categories_frame, anchor="nw")

        self._categories_frame.bind("<Configure>", self._on_frame_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        bind_mousewheel(self._canvas)

        self._create_category_fields(DEFAULT_CATEGORIES)

    def _setup_status_bar(self):
        theme.separator(self.frame, color=theme.LINE_COLOR).pack(fill="x")
        bar = tk.Frame(self.frame, bg=theme.BG_SURFACE,
                       padx=theme.PAD_MD, pady=6)
        bar.pack(fill="x", side="bottom")

        self._status_label = tk.Label(bar,
                                      text="Waiting end of round...",
                                      font=(theme.HAND_FONT, 10, "italic"),
                                      bg=theme.BG_SURFACE, fg=theme.INK_LIGHT)
        self._status_label.pack(side="left")

    def _on_frame_configure(self, event):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self._canvas.itemconfig(self._canvas_window, width=event.width)

    # Category rows

    def _create_category_fields(self, categories: list):
        for w in self._categories_frame.winfo_children():
            w.destroy()
        self._answer_vars.clear()
        self._categories = categories

        for i, cat in enumerate(categories):
            row = tk.Frame(self._categories_frame, bg=theme.BG_PAGE,
                           pady=0, padx=theme.PAD_LG)
            row.pack(fill="x")

            line = tk.Frame(self._categories_frame, bg=theme.LINE_COLOR, height=1)
            line.pack(fill="x", padx=theme.PAD_LG)

            inner = tk.Frame(row, bg=theme.BG_PAGE)
            inner.pack(fill="x", pady=6)

            tk.Label(inner, text=f"{cat}:", font=theme.FONT_LABEL,
                     bg=theme.BG_PAGE, fg=theme.INK, width=14, anchor="w").pack(side="left")

            var = tk.StringVar()
            self._answer_vars[cat] = var

            entry = tk.Entry(inner, textvariable=var)
            theme.style_entry(entry)
            entry.configure(highlightthickness=0,
                            relief="flat", bd=0)
            entry.pack(side="left", fill="x", expand=True, ipady=5)
            entry.bind("<Return>", lambda e, idx=i: self._focus_next(idx))

    def _focus_next(self, idx):
        rows = [w for w in self._categories_frame.winfo_children()
                if isinstance(w, tk.Frame)]
        pairs = [(rows[i], rows[i+1]) for i in range(0, len(rows)-1, 2)]
        if idx + 1 < len(pairs):
            for child in pairs[idx + 1][0].winfo_children():
                inner = child if isinstance(child, tk.Frame) else None
                if inner:
                    for c in inner.winfo_children():
                        if isinstance(c, tk.Entry):
                            c.focus_set(); return

    def _focus_first_entry(self):
        for w in self._categories_frame.winfo_children():
            if isinstance(w, tk.Frame):
                for child in w.winfo_children():
                    if isinstance(child, tk.Frame):
                        for c in child.winfo_children():
                            if isinstance(c, tk.Entry):
                                c.focus_set(); return

    # Public API

    def update_letter(self, letter: str):
        self._letter_var.set(letter.upper())

    def update_timer(self, seconds: int):
        self._timer.update(seconds)

    def update_categories(self, categories: list):
        self._create_category_fields(categories)

    def update_round_info(self, round_number: int):
        self._round_label.configure(text=f"Round  {round_number}")

    def update_status(self, text: str):
        self._status_label.configure(text=text)

    def get_answers(self) -> dict:
        return {cat: var.get().strip() for cat, var in self._answer_vars.items()}

    def clear_answers(self):
        for var in self._answer_vars.values():
            var.set("")

    def set_inputs_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        for row in self._categories_frame.winfo_children():
            for child in row.winfo_children():
                if isinstance(child, tk.Frame):
                    for c in child.winfo_children():
                        if isinstance(c, tk.Entry):
                            c.configure(state=state)

    def start_round(self, letter: str, categories: list, round_number: int):
        self.update_letter(letter)
        self.update_categories(categories)
        self.update_round_info(round_number)
        self.clear_answers()
        self.set_inputs_enabled(True)
        self.update_status("Write your answers!")
        self._timer.reset()
        self._focus_first_entry()

    def end_round(self):
        self.set_inputs_enabled(False)
        self.update_status("Time's up! Waiting for the results...")
        self._timer.set_expired()