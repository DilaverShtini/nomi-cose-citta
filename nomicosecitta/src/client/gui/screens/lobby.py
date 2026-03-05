"""
Lobby screen for the Nomi Cose Città client.
Waiting room with player list, game settings, and chat.
"""
import tkinter as tk
from tkinter import messagebox
from src.client.gui.screens.base_screen import BaseScreen
from src.client.gui.widgets import PlayerList
from src.client.gui.utils import bind_mousewheel
from src.client.gui import theme
from src.common.constants import (
    AVAILABLE_EXTRA_CATEGORIES, GAME_MODE_CLASSIC, GAME_MODE_CLASSIC_PLUS,
    GAME_MODE_FREE, MIN_EXTRA_CATEGORIES, MAX_EXTRA_CATEGORIES,
    MIN_ROUND_TIME, MAX_ROUND_TIME, DEFAULT_ROUND_TIME,
)


class LobbyScreen(BaseScreen):
    """Lobby screen"""

    def _setup_ui(self):
        self.frame.configure(bg=theme.BG_PAGE)
        self._is_admin = False
        self._game_mode_var = tk.StringVar(value=GAME_MODE_CLASSIC)
        self._num_extra_var = tk.IntVar(value=2)
        self._round_time_var = tk.IntVar(value=DEFAULT_ROUND_TIME)
        self._extra_category_vars: dict[str, tk.BooleanVar] = {}
        self._max_categories: int = self._num_extra_var.get()

        self._mode_radios: list[tk.Radiobutton] = []
        self._num_radios: list[tk.Radiobutton] = []
        self._cat_count_label: tk.Label | None = None

        self._setup_header()
        self._setup_content()

    # Header

    def _setup_header(self):
        header = tk.Frame(self.frame, bg=theme.BG_SURFACE,
                          padx=theme.PAD_MD, pady=8)
        header.pack(fill="x")

        title_frame = tk.Frame(header, bg=theme.BG_SURFACE)
        title_frame.pack(side="left")
        for text, color in [("Nomi", theme.TITLE_N), (",", theme.INK),
                             ("Cose", theme.TITLE_C1), (",", theme.INK),
                             ("Città", theme.TITLE_C2)]:
            tk.Label(title_frame, text=text, font=(theme.HAND_FONT, 15, "bold"),
                     bg=theme.BG_SURFACE, fg=color).pack(side="left")

        tk.Label(header, text="— Waiting room",
                 font=theme.FONT_BODY,
                 bg=theme.BG_SURFACE, fg=theme.INK_LIGHT).pack(side="left", padx=8)

        self._admin_badge = tk.Label(header, text="",
                                     font=(theme.HAND_FONT, 9, "bold"),
                                     bg=theme.ORANGE_INK, fg="#ffffff",
                                     padx=8, pady=3)

        theme.separator(self.frame, color=theme.LINE_DARK).pack(fill="x")

    # Content

    def _setup_content(self):
        content = tk.Frame(self.frame, bg=theme.BG_PAGE)
        content.pack(fill="both", expand=True, padx=theme.PAD_MD, pady=theme.PAD_MD)
        self._setup_players_panel(content)
        self._setup_settings_panel(content)

    def _setup_players_panel(self, parent):
        left = tk.Frame(parent, bg=theme.BG_PAGE, width=150)
        left.pack(side="left", fill="y", padx=(0, theme.PAD_SM))
        left.pack_propagate(False)
        self._player_list = PlayerList(left)
        self._player_list.pack(fill="both", expand=True)

    def _setup_settings_panel(self, parent):
        center_wrap = tk.Frame(parent, bg=theme.LINE_DARK, padx=1, pady=1)
        center_wrap.pack(side="left", fill="both", expand=True, padx=theme.PAD_SM)

        center = tk.Frame(center_wrap, bg=theme.BG_PAGE)
        center.pack(fill="both", expand=True)

        canvas = tk.Canvas(center, bg=theme.BG_PAGE, highlightthickness=0)
        scrollbar = tk.Scrollbar(center, orient="vertical", command=canvas.yview,
                                 bg=theme.BG_SURFACE, troughcolor=theme.BG_SURFACE,
                                 relief="flat", bd=0)
        self._settings_frame = tk.Frame(canvas, bg=theme.BG_PAGE)

        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        win = canvas.create_window((0, 0), window=self._settings_frame, anchor="nw")
        self._settings_frame.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win, width=e.width))
        bind_mousewheel(canvas)

        self._build_settings_controls()

    # Settings

    def _build_settings_controls(self):
        sf = self._settings_frame

        tk.Label(sf, text="Game settings",
                 font=theme.FONT_HEADING,
                 bg=theme.BG_PAGE, fg=theme.INK,
                 anchor="w").pack(fill="x", padx=theme.PAD_MD, pady=(theme.PAD_MD, 4))

        theme.separator(sf, color=theme.LINE_COLOR).pack(
            fill="x", padx=theme.PAD_MD, pady=(0, theme.PAD_SM))

        self._build_mode_selector()
        self._build_num_categories_selector()
        self._build_categories_selector()
        self._build_time_selector()
        self._build_start_button()

        self._on_mode_change()
        self._update_admin_controls()

    def _section_title(self, text):
        tk.Label(self._settings_frame, text=text,
                 font=(theme.HAND_FONT, 10, "bold"),
                 bg=theme.BG_PAGE, fg=theme.BLUE_INK,
                 anchor="w").pack(fill="x", padx=theme.PAD_MD, pady=(theme.PAD_MD, 6))

    def _build_mode_selector(self):
        self._section_title("Game mode")
        self._mode_info_label = tk.Label(
            self._settings_frame,
            text="Only the admin can change the game mode.",
            font=(theme.HAND_FONT, 9, "italic"),
            bg=theme.BG_PAGE, fg=theme.ORANGE_INK,
        )

        modes = [
            (GAME_MODE_CLASSIC,      "Classic",      "Only Nomi + Cose + Città"),
            (GAME_MODE_CLASSIC_PLUS, "Classic Plus", "Nomi + Cose + Città + extra"),
            (GAME_MODE_FREE,         "Free Choice",  "Only selected categories"),
        ]
        self._mode_radios = []
        for value, name, desc in modes:
            row = tk.Frame(self._settings_frame, bg=theme.BG_PAGE, padx=theme.PAD_MD)
            row.pack(fill="x", pady=2)
            rb = tk.Radiobutton(
                row, text=name,
                variable=self._game_mode_var, value=value,
                font=theme.FONT_BODY,
                bg=theme.BG_PAGE, fg=theme.INK,
                selectcolor=theme.YELLOW_HL,
                activebackground=theme.BG_PAGE,
                activeforeground=theme.BLUE_INK,
                command=self._on_mode_change_by_admin,
                disabledforeground=theme.INK_LIGHT,
            )
            rb.pack(side="left")
            self._mode_radios.append(rb)
            tk.Label(row, text=f"({desc})", font=theme.FONT_SMALL,
                     bg=theme.BG_PAGE, fg=theme.INK_LIGHT).pack(side="left", padx=6)

    def _build_num_categories_selector(self):
        self._num_frame = tk.Frame(self._settings_frame, bg=theme.BG_PAGE)
        self._section_title_dyn = tk.Label(
            self._num_frame, text="Number of extra categories:",
            font=(theme.HAND_FONT, 10, "bold"),
            bg=theme.BG_PAGE, fg=theme.BLUE_INK, anchor="w")
        self._section_title_dyn.pack(fill="x", padx=theme.PAD_MD, pady=(theme.PAD_MD, 6))

        self._num_info_label = tk.Label(
            self._num_frame,
            text="Only the admin can change this.",
            font=(theme.HAND_FONT, 9, "italic"),
            bg=theme.BG_PAGE, fg=theme.ORANGE_INK,
        )

        self._num_radios_wrap = tk.Frame(self._num_frame, bg=theme.BG_PAGE)
        self._num_radios_wrap.pack(fill="x", padx=theme.PAD_MD)
        wrap = self._num_radios_wrap

        h_canvas = tk.Canvas(wrap, bg=theme.BG_PAGE, height=34, highlightthickness=0)
        h_scroll = tk.Scrollbar(wrap, orient="horizontal", command=h_canvas.xview,
                                bg=theme.BG_SURFACE, troughcolor=theme.LINE_COLOR,
                                relief="flat", bd=0)
        h_canvas.configure(xscrollcommand=h_scroll.set)
        h_scroll.pack(side="bottom", fill="x")
        h_canvas.pack(side="top", fill="x")

        inner = tk.Frame(h_canvas, bg=theme.BG_PAGE)
        win_id = h_canvas.create_window((0, 0), window=inner, anchor="nw")

        self._num_radios = []
        for n in range(MIN_EXTRA_CATEGORIES, MAX_EXTRA_CATEGORIES + 1):
            rb = tk.Radiobutton(
                inner, text=str(n),
                variable=self._num_extra_var, value=n,
                font=theme.FONT_BODY,
                bg=theme.BG_PAGE, fg=theme.INK,
                selectcolor=theme.YELLOW_HL,
                activebackground=theme.BG_PAGE,
                activeforeground=theme.BLUE_INK,
                command=self._on_num_extra_change_by_admin,
                disabledforeground=theme.INK_LIGHT,
            )
            rb.pack(side="left", padx=6)
            self._num_radios.append(rb)

        def _update_scroll(e=None):
            h_canvas.configure(scrollregion=h_canvas.bbox("all"))
        inner.bind("<Configure>", _update_scroll)

    def _build_categories_selector(self):
        self._categories_frame = tk.Frame(self._settings_frame, bg=theme.BG_PAGE)

        header_row = tk.Frame(self._categories_frame, bg=theme.BG_PAGE)
        header_row.pack(fill="x", padx=theme.PAD_MD, pady=(theme.PAD_MD, 0))

        self._categories_info = tk.Label(
            header_row, text="Extra categories:",
            font=(theme.HAND_FONT, 10, "bold"),
            bg=theme.BG_PAGE, fg=theme.BLUE_INK, anchor="w")
        self._categories_info.pack(side="left")

        self._cat_count_label = tk.Label(
            header_row, text="",
            font=(theme.HAND_FONT, 10, "bold"),
            bg=theme.BG_PAGE, fg=theme.GREEN_INK, anchor="e")
        self._cat_count_label.pack(side="right", padx=(8, 0))

        self._cat_hint_label = tk.Label(
            self._categories_frame,
            text="Select at least 1 and at most N categories to vote.",
            font=(theme.HAND_FONT, 9, "italic"),
            bg=theme.BG_PAGE, fg=theme.ORANGE_INK,
        )
        self._cat_hint_label.pack(fill="x", padx=theme.PAD_MD, pady=(2, 6))

        self._categories_grid_wrap = tk.Frame(self._categories_frame, bg=theme.BG_PAGE)
        self._categories_grid_wrap.pack(fill="x", padx=theme.PAD_MD)
        wrap = self._categories_grid_wrap

        h_canvas = tk.Canvas(wrap, bg=theme.BG_PAGE, height=280, highlightthickness=0)
        h_scroll = tk.Scrollbar(wrap, orient="horizontal", command=h_canvas.xview,
                                bg=theme.BG_SURFACE, troughcolor=theme.LINE_COLOR,
                                relief="flat", bd=0)
        h_canvas.configure(xscrollcommand=h_scroll.set)
        h_scroll.pack(side="bottom", fill="x")
        h_canvas.pack(side="top", fill="x")

        grid = tk.Frame(h_canvas, bg=theme.BG_PAGE)
        win_id = h_canvas.create_window((0, 0), window=grid, anchor="nw")

        COLS = 3
        for i, cat in enumerate(AVAILABLE_EXTRA_CATEGORIES):
            var = tk.BooleanVar(value=False)
            self._extra_category_vars[cat] = var
            tk.Checkbutton(
                grid, text=cat, variable=var,
                font=theme.FONT_SMALL,
                bg=theme.BG_PAGE, fg=theme.INK,
                selectcolor=theme.YELLOW_HL,
                activebackground=theme.BG_PAGE,
                activeforeground=theme.GREEN_INK,
                command=lambda c=cat: self._on_category_changed(c),
            ).grid(row=i // COLS, column=i % COLS, sticky="w", padx=6, pady=2)

        def _update_scroll(e=None):
            h_canvas.configure(scrollregion=h_canvas.bbox("all"))
        grid.bind("<Configure>", _update_scroll)

        self._update_category_count_label()

    def _build_time_selector(self):
        self._time_frame = tk.Frame(self._settings_frame, bg=theme.BG_PAGE)
        self._time_frame.pack(fill="x", padx=theme.PAD_MD, pady=(theme.PAD_MD, 0))

        tk.Label(self._time_frame, text="Round duration",
                 font=(theme.HAND_FONT, 10, "bold"),
                 bg=theme.BG_PAGE, fg=theme.BLUE_INK, anchor="w").pack(fill="x", pady=(0, 6))

        self._time_info = tk.Label(self._time_frame,
                                   text="Only the admin can modify this setting",
                                   font=(theme.HAND_FONT, 9, "italic"),
                                   bg=theme.BG_PAGE, fg=theme.ORANGE_INK)
        self._time_info.pack(anchor="w", pady=(0, 4))

        row = tk.Frame(self._time_frame, bg=theme.BG_PAGE)
        row.pack(fill="x")

        tk.Label(row, text=f"{MIN_ROUND_TIME}s", font=theme.FONT_SMALL,
                 bg=theme.BG_PAGE, fg=theme.INK_LIGHT).pack(side="left")

        self._time_scale = tk.Scale(
            row, from_=MIN_ROUND_TIME, to=MAX_ROUND_TIME,
            orient="horizontal", variable=self._round_time_var,
            length=200, resolution=5,
            font=theme.FONT_SMALL,
            bg=theme.BG_PAGE, fg=theme.INK,
            troughcolor=theme.LINE_COLOR,
            highlightthickness=0,
            activebackground=theme.BLUE_INK,
            sliderrelief="flat",
            command=self._on_round_time_change_by_admin,
        )
        self._time_scale.pack(side="left", fill="x", expand=True, padx=6)

        tk.Label(row, text=f"{MAX_ROUND_TIME}s", font=theme.FONT_SMALL,
                 bg=theme.BG_PAGE, fg=theme.INK_LIGHT).pack(side="left")

    def _build_start_button(self):
        self._start_frame = tk.Frame(self._settings_frame, bg=theme.BG_PAGE)
        self._start_frame.pack(fill="x", padx=theme.PAD_MD, pady=theme.PAD_LG)

        self._start_btn = tk.Button(self._start_frame, text="START GAME",
                                    command=self._handle_start_game)
        theme.style_button(self._start_btn, "success")
        self._start_btn.configure(font=(theme.HAND_FONT, 13, "bold"))

        self._waiting_label = tk.Label(
            self._start_frame,
            text="Waiting for the admin to start the game...",
            font=(theme.HAND_FONT, 10, "italic"),
            bg=theme.BG_PAGE, fg=theme.INK_LIGHT,
        )

    # Handlers

    def _on_mode_change(self):
        """Update the visibility of the panels based on the current mode."""
        mode = self._game_mode_var.get()
        if mode == GAME_MODE_CLASSIC:
            self._num_frame.pack_forget()
            self._categories_frame.pack_forget()
        else:
            self._num_frame.pack(fill="x", before=self._time_frame)
            self._categories_frame.pack(fill="x", before=self._time_frame)
            self._categories_info.config(text=(
                "Extra categories (added to Nomi+Cose+Città):"
                if mode == GAME_MODE_CLASSIC_PLUS
                else "Select the categories to play with:"))

    def _on_mode_change_by_admin(self):
        self._on_mode_change()
        self._notify_settings_changed()

    def _on_num_extra_change_by_admin(self):
        new_max = self._num_extra_var.get()
        self._apply_max_categories(new_max)
        self._notify_settings_changed()

    def _on_round_time_change_by_admin(self, value=None):
        self._notify_settings_changed()

    def _notify_settings_changed(self):
        if self._is_admin and self.manager.on_lobby_settings_changed:
            self.manager.on_lobby_settings_changed(self.get_settings())

    def _on_category_changed(self, category: str):
        var = self._extra_category_vars[category]
        if var.get():
            count = len(self.get_selected_categories())
            if count > self._max_categories:
                var.set(False)
                messagebox.showwarning(
                    "Selection limit",
                    f"You can select at most {self._max_categories} "
                    f"categor{'y' if self._max_categories == 1 else 'ies'}."
                )
                return

        self._update_category_count_label()
        if self.manager.on_category_vote_changed:
            self.manager.on_category_vote_changed(self.get_selected_categories())

    def _handle_start_game(self):
        mode = self._game_mode_var.get()
        selected = self.get_selected_categories()

        if mode in [GAME_MODE_CLASSIC_PLUS, GAME_MODE_FREE]:
            if len(selected) < 1:
                messagebox.showwarning(
                    "Selection required",
                    "Please select at least 1 category before starting.",
                )
                return

        if self.manager.on_category_vote_changed:
            self.manager.on_category_vote_changed(selected)

        config = {
            "mode": mode,
            "num_extra_categories": self._num_extra_var.get(),
            "round_time": self._round_time_var.get(),
        }
        if self.manager.on_start_game:
            self.manager.on_start_game(config)

    # Helpers

    def _apply_max_categories(self, new_max: int):
        """Aggiorna _max_categories; deseleziona in eccesso se necessario."""
        self._max_categories = new_max
        selected = self.get_selected_categories()
        if len(selected) > new_max:
            for cat in selected[new_max:]:
                self._extra_category_vars[cat].set(False)
        self._update_category_count_label()

    def _update_category_count_label(self):
        if self._cat_count_label is None:
            return
        mode = self._game_mode_var.get()
        if mode == GAME_MODE_CLASSIC:
            self._cat_count_label.configure(text="")
            return
        count = len(self.get_selected_categories())
        max_n = self._max_categories
        color = theme.GREEN_INK if count >= 1 else theme.RED_INK
        self._cat_count_label.configure(
            text=f"Selected: {count}/{max_n}",
            fg=color,
        )

    def _update_admin_controls(self):
        """Aggiorna lo stato enable/disable dei controlli in base al ruolo."""
        if self._is_admin:
            self._admin_badge.configure(text="⭐ YOU ARE THE ADMIN")
            self._admin_badge.pack(side="right", padx=4)
            self._mode_info_label.pack_forget()
            for rb in self._mode_radios:
                rb.configure(state="normal")
            self._num_info_label.pack_forget()
            for rb in self._num_radios:
                rb.configure(state="normal")
            self._cat_hint_label.pack_forget()
            self._time_scale.configure(state="normal")
            self._time_info.configure(text="Set the round duration")
            self._start_btn.pack(fill="x", ipady=6)
            self._waiting_label.pack_forget()
        else:
            self._admin_badge.pack_forget()
            for rb in self._mode_radios:
                rb.configure(state="disabled")
            self._mode_info_label.pack(fill="x", padx=theme.PAD_MD, pady=(0, 4))
            for rb in self._num_radios:
                rb.configure(state="disabled")
            self._num_info_label.pack(
                fill="x", padx=theme.PAD_MD, pady=(0, 4),
                before=self._num_radios_wrap,
            )
            self._cat_hint_label.pack(
                fill="x", padx=theme.PAD_MD, pady=(2, 6),
                before=self._categories_grid_wrap,
            )
            self._time_scale.configure(state="disabled")
            self._time_info.configure(text="Only the admin can modify this setting")
            # Bottone start
            self._start_btn.pack_forget()
            self._waiting_label.pack(pady=10)

    # Public API

    def set_admin(self, is_admin: bool):
        self._is_admin = is_admin
        self._update_admin_controls()

    def update_player_list(self, players: list, admin_username: str = None):
        self._player_list.update(players, admin_username)

    def get_selected_categories(self) -> list:
        return [cat for cat, var in self._extra_category_vars.items() if var.get()]

    def get_settings(self) -> dict:
        return {
            "mode": self._game_mode_var.get(),
            "selected_categories": self.get_selected_categories(),
            "num_extra_categories": self._num_extra_var.get(),
            "round_time": self._round_time_var.get(),
        }

    def update_lobby_settings(self, mode: str, num_extra_categories: int, round_time: int = None):
        self._game_mode_var.set(mode)
        self._num_extra_var.set(num_extra_categories)
        self._apply_max_categories(num_extra_categories)
        if round_time is not None:
            self._round_time_var.set(round_time)
        self._on_mode_change()
        self._update_category_count_label()

    @property
    def player_list(self):
        return self._player_list.listbox