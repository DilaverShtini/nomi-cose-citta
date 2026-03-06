"""
Game screen for the Nomi Cose Città client.
"""
import tkinter as tk
from tkinter import messagebox
from src.client.gui.screens.base_screen import BaseScreen
from src.client.gui.widgets import TimerDisplay
from src.client.gui.utils import bind_mousewheel
from src.client.gui import theme
from src.common.constants import DEFAULT_CATEGORIES
from src.client.gui.widgets import ChatPanel

_FONT_LETTER_SM  = (theme.HAND_FONT, 32, "bold")
_FONT_TIMER_SM   = (theme.HAND_FONT, 20, "bold")
_FONT_LB_NAME    = (theme.HAND_FONT,  9, "bold")
_FONT_LB_PTS     = (theme.HAND_FONT,  9)
_FONT_LB_DELTA   = (theme.HAND_FONT,  9, "bold")
_MAX_LB_PLAYERS  = 10


class GameScreen(BaseScreen):
    """Game screen — school notebook style, fully resizable."""

    def _setup_ui(self):
        self.frame.configure(bg=theme.BG_PAGE)
        self._letter_var = tk.StringVar(value="-")
        self._categories = DEFAULT_CATEGORIES.copy()
        self._answer_vars = {}

        self._setup_top_bar()
        self._setup_leaderboard_bar()

        self._middle_frame = tk.Frame(self.frame, bg=theme.BG_PAGE)
        self._middle_frame.pack(fill="both", expand=True)
        self._middle_frame.columnconfigure(0, weight=5)
        self._middle_frame.columnconfigure(1, weight=1)
        self._middle_frame.rowconfigure(0, weight=1)

        self._setup_categories_area()
        self._setup_chat_panel()
        self._setup_status_bar()

    # Top bar

    def _setup_top_bar(self):
        bar = tk.Frame(self.frame, bg=theme.BG_SURFACE,
                       padx=theme.PAD_MD, pady=2)
        bar.pack(fill="x")

        title_frame = tk.Frame(bar, bg=theme.BG_SURFACE)
        title_frame.pack(side="left")
        for text, color in [("Nomi", theme.TITLE_N), (",", theme.INK),
                             ("Cose", theme.TITLE_C1), (",", theme.INK),
                             ("Città", theme.TITLE_C2)]:
            tk.Label(title_frame, text=text, font=(theme.HAND_FONT, 11, "bold"),
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
                 bg=theme.BG_SURFACE, fg=theme.INK).pack(side="left", padx=(0, 8))
        self._letter_label = tk.Label(letter_row, textvariable=self._letter_var,
                                      font=_FONT_LETTER_SM,
                                      bg=theme.BG_SURFACE, fg=theme.RED_INK)
        self._letter_label.pack(side="left")

        self._timer = TimerDisplay(bar, bg_color=theme.BG_SURFACE)
        self._timer._timer_label.configure(font=_FONT_TIMER_SM)
        self._timer.pack(side="right")

        theme.separator(self.frame, color=theme.LINE_DARK).pack(fill="x")

    # Leaderboard

    _MEDALS = ["🥇", "🥈", "🥉"]

    def _setup_leaderboard_bar(self):
        outer = tk.Frame(self.frame, bg=theme.BG_SURFACE,
                         padx=theme.PAD_SM, pady=4)
        outer.pack(fill="x")

        tk.Label(outer, text="🏆",
                 font=(theme.HAND_FONT, 10, "bold"),
                 bg=theme.BG_SURFACE, fg=theme.BLUE_INK).pack(
                     side="left", padx=(0, theme.PAD_SM))

        self._lb_canvas = tk.Canvas(outer, bg=theme.BG_SURFACE,
                                    highlightthickness=0)
        self._lb_canvas.pack(side="left", fill="both", expand=True)

        self._lb_inner = tk.Frame(self._lb_canvas, bg=theme.BG_SURFACE)
        self._lb_canvas_win = self._lb_canvas.create_window(
            (0, 0), window=self._lb_inner, anchor="nw")

        def _sync_height(event):
            h = self._lb_inner.winfo_reqheight()
            self._lb_canvas.configure(height=max(h, 1),
                                      scrollregion=self._lb_canvas.bbox("all"))

        self._lb_inner.bind("<Configure>", _sync_height)

        self._lb_placeholder = tk.Label(
            self._lb_inner, text="No scores yet",
            font=(theme.HAND_FONT, 9, "italic"),
            bg=theme.BG_SURFACE, fg=theme.INK_LIGHT)
        self._lb_placeholder.pack(side="left", padx=theme.PAD_SM)

        theme.separator(self.frame, color=theme.LINE_COLOR).pack(fill="x")

    def update_scoreboard(self, scores: dict, round_scores: dict = None):
        for w in self._lb_inner.winfo_children():
            w.destroy()

        if not scores:
            tk.Label(self._lb_inner, text="No scores yet",
                     font=(theme.HAND_FONT, 9, "italic"),
                     bg=theme.BG_SURFACE, fg=theme.INK_LIGHT).pack(
                         side="left", padx=theme.PAD_SM)
            return

        sorted_players = sorted(scores.items(),
                                key=lambda kv: kv[1], reverse=True)
        sorted_players = sorted_players[:_MAX_LB_PLAYERS]

        for rank, (username, total) in enumerate(sorted_players):
            if rank > 0:
                tk.Frame(self._lb_inner, bg=theme.LINE_COLOR,
                         width=1).pack(side="left", fill="y",
                                       padx=theme.PAD_SM, pady=2)

            card = tk.Frame(self._lb_inner, bg=theme.BG_SURFACE)
            card.pack(side="left", padx=(4, 0))

            medal = self._MEDALS[rank] if rank < 3 else f"{rank + 1}."

            top = tk.Frame(card, bg=theme.BG_SURFACE)
            top.pack(anchor="w")
            tk.Label(top, text=medal, font=_FONT_LB_NAME,
                     bg=theme.BG_SURFACE, fg=theme.INK).pack(side="left")
            tk.Label(top, text=f" {username}", font=_FONT_LB_NAME,
                     bg=theme.BG_SURFACE, fg=theme.INK).pack(side="left")

            bot = tk.Frame(card, bg=theme.BG_SURFACE)
            bot.pack(anchor="w")
            tk.Label(bot, text=f"{total} pts", font=_FONT_LB_PTS,
                     bg=theme.BG_SURFACE, fg=theme.INK_LIGHT).pack(side="left")

            delta = (round_scores or {}).get(username)
            if delta is not None and delta > 0:
                tk.Label(bot, text=f"  +{delta}", font=_FONT_LB_DELTA,
                         bg=theme.BG_SURFACE, fg=theme.GREEN_INK).pack(side="left")

        self.update_status("Scores updated! Next round starting shortly...")
        self.frame.update_idletasks()

    # Categories area

    def _setup_categories_area(self):
        container = tk.Frame(self._middle_frame, bg=theme.BG_PAGE)
        container.grid(row=0, column=0, sticky="nsew")

        self._canvas = tk.Canvas(container, bg=theme.BG_PAGE,
                                 highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical",
                                 command=self._canvas.yview,
                                 bg=theme.BG_SURFACE,
                                 troughcolor=theme.BG_SURFACE,
                                 relief="flat", bd=0)

        h_scrollbar = tk.Scrollbar(container, orient="horizontal",
                                   command=self._canvas.xview,
                                   bg=theme.BG_SURFACE,
                                   troughcolor=theme.BG_SURFACE,
                                   relief="flat", bd=0)

        self._categories_frame = tk.Frame(self._canvas, bg=theme.BG_PAGE)

        self._canvas.configure(yscrollcommand=scrollbar.set, xscrollcommand=h_scrollbar.set)
        h_scrollbar.pack(side="bottom", fill="x")
        scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._canvas_window = self._canvas.create_window(
            (0, 0), window=self._categories_frame, anchor="nw")

        self._categories_frame.bind("<Configure>", self._on_frame_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        bind_mousewheel(self._canvas)

        self._create_category_fields(DEFAULT_CATEGORIES)

    def _on_frame_configure(self, event):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        req_width = self._categories_frame.winfo_reqwidth()
        canvas_width = self._canvas.winfo_width()
        self._canvas.itemconfig(self._canvas_window, width=max(canvas_width, req_width))

    def _on_canvas_configure(self, event):
        req_width = self._categories_frame.winfo_reqwidth()
        self._canvas.itemconfig(self._canvas_window, width=max(event.width, req_width))

    # Chat panel

    def _setup_chat_panel(self):
        right = tk.Frame(self._middle_frame, bg=theme.BG_PAGE)
        right.grid(row=0, column=1, sticky="nsew",
                   padx=(theme.PAD_SM, theme.PAD_MD),
                   pady=(0, theme.PAD_SM))

        self._chat = ChatPanel(right, on_send=self._handle_send_chat)
        self._chat.pack(fill="both", expand=True)

    def _handle_send_chat(self, message: str):
        if hasattr(self.manager, 'on_send_message') and self.manager.on_send_message:
            self.manager.on_send_message(message)

    def append_log(self, text: str):
        if hasattr(self, '_chat'):
            self._chat.append(text)

    # Status bar

    def _setup_status_bar(self):
        theme.separator(self.frame, color=theme.LINE_COLOR).pack(fill="x")
        bar = tk.Frame(self.frame, bg=theme.BG_SURFACE,
                       padx=theme.PAD_MD, pady=4)
        bar.pack(fill="x", side="bottom")

        self._status_label = tk.Label(bar,
                                      text="Waiting end of round...",
                                      font=(theme.HAND_FONT, 10, "italic"),
                                      bg=theme.BG_SURFACE, fg=theme.INK_LIGHT)
        self._status_label.pack(side="left")

    # Category

    def _create_category_fields(self, categories: list):
        for w in self._categories_frame.winfo_children():
            w.destroy()
        self._answer_vars.clear()
        self._categories = categories

        for i, cat in enumerate(categories):
            row = tk.Frame(self._categories_frame, bg=theme.BG_PAGE,
                           pady=0, padx=theme.PAD_LG)
            row.pack(fill="x")

            tk.Frame(self._categories_frame, bg=theme.LINE_COLOR,
                     height=1).pack(fill="x", padx=theme.PAD_LG)

            inner = tk.Frame(row, bg=theme.BG_PAGE)
            inner.pack(fill="x", pady=5)

            tk.Label(inner, text=f"{cat}:", font=theme.FONT_LABEL,
                     bg=theme.BG_PAGE, fg=theme.INK,
                     anchor="w").pack(side="left", padx=(0, theme.PAD_SM))

            var = tk.StringVar()
            self._answer_vars[cat] = var
            entry = tk.Entry(inner, textvariable=var)
            theme.style_entry(entry)
            entry.configure(highlightthickness=0, relief="flat", bd=0)
            entry.pack(side="left", fill="x", expand=True, ipady=4)
            entry.bind("<Return>", lambda e, idx=i: self._focus_next(idx))

    def _focus_next(self, idx):
        rows = [w for w in self._categories_frame.winfo_children()
                if isinstance(w, tk.Frame)]
        pairs = [(rows[i], rows[i + 1]) for i in range(0, len(rows) - 1, 2)]
        if idx + 1 < len(pairs):
            for child in pairs[idx + 1][0].winfo_children():
                if isinstance(child, tk.Frame):
                    for c in child.winfo_children():
                        if isinstance(c, tk.Entry):
                            c.focus_set()
                            return

    def _focus_first_entry(self):
        for w in self._categories_frame.winfo_children():
            if isinstance(w, tk.Frame):
                for child in w.winfo_children():
                    if isinstance(child, tk.Frame):
                        for c in child.winfo_children():
                            if isinstance(c, tk.Entry):
                                c.focus_set()
                                return

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

    # Round lifecycle

    def start_round(self, letter: str, categories: list,
                    round_number: int, duration: int):
        if hasattr(self, '_timer_job'):
            self.frame.after_cancel(self._timer_job)
            del self._timer_job

        self.update_letter(letter)
        self.update_categories(categories)
        self.update_round_info(round_number)
        self.clear_answers()
        self.set_inputs_enabled(True)
        self.update_status("Write your answers!")
        self._timer.reset()
        self._focus_first_entry()
        self._local_duration = duration
        if round_number == 1:
            self.update_scoreboard({})
            if hasattr(self, '_chat'):
                if hasattr(self._chat, 'clear'):
                    self._chat.clear()
                elif hasattr(self._chat, 'display'):
                    self._chat.display.configure(state="normal")
                    self._chat.display.delete("1.0", "end")
                    self._chat.display.configure(state="disabled")

        self.update_status("Write your answers!")
        self._timer.reset()
        self._focus_first_entry()
        self._local_duration = duration
        self._run_local_timer()

    def _run_local_timer(self):
        if (hasattr(self, '_local_duration')
                and self._local_duration >= 0
                and self.is_active):
            self.update_timer(self._local_duration)
            if self._local_duration > 0:
                self._local_duration -= 1
                self._timer_job = self.frame.after(1000, self._run_local_timer)
            else:
                self.end_round()
                if (hasattr(self.manager, 'on_submit_answers')
                        and self.manager.on_submit_answers):
                    self.manager.on_submit_answers(self.get_answers())

    def end_round(self):
        if hasattr(self, '_timer_job'):
            self.frame.after_cancel(self._timer_job)
        self.set_inputs_enabled(False)
        self.update_status("Time's up! Waiting for the results...")
        self._timer.set_expired()

    # Voting UI

    def build_voting_ui(self, words_to_vote: dict, my_username: str, duration: int = 0):
        self._my_username = my_username
        if hasattr(self, '_timer_job'):
            self.frame.after_cancel(self._timer_job)
            del self._timer_job
        
        for w in self._categories_frame.winfo_children():
            w.destroy()

        self.update_status(
            "Voting phase: vote and click Ready.")
        self._vote_buttons    = {}
        self._voted_items     = set()
        self._peer_votes_data = {}
        self._vote_counters   = {}

        for category, users_words in words_to_vote.items():
            tk.Label(self._categories_frame,
                     text=f"{category.upper()}",
                     font=theme.FONT_LABEL,
                     bg=theme.BG_PAGE, fg=theme.INK).pack(pady=(15, 5))

            for target_user, word in users_words.items():
                self._peer_votes_data[(category, target_user)] = {}

                row_frame = tk.Frame(self._categories_frame, bg=theme.BG_PAGE)
                row_frame.pack(fill="x", padx=theme.PAD_LG, pady=2)

                row_frame.columnconfigure(0, weight=1)

                display_name = "YOU" if target_user == my_username else target_user
                tk.Label(row_frame, text=f"{display_name}:  {word}",
                         font=theme.FONT_BODY,
                         bg=theme.BG_PAGE, fg=theme.INK,
                         anchor="w").grid(row=0, column=0,
                                          sticky="ew", padx=(0, theme.PAD_SM))

                if target_user != my_username:
                    btn_yes = tk.Button(row_frame, text="Valid", width=8)
                    theme.style_button(btn_yes, variant="ghost")
                    btn_yes.grid(row=0, column=1, padx=4)

                    btn_no = tk.Button(row_frame, text="Invalid", width=8)
                    theme.style_button(btn_no, variant="ghost")
                    btn_no.grid(row=0, column=2, padx=4)

                    btn_yes.configure(
                        command=lambda c=category, t=target_user,
                                       by=btn_yes, bn=btn_no:
                            self._cast_vote(t, c, True, by, bn))
                    btn_no.configure(
                        command=lambda c=category, t=target_user,
                                       by=btn_yes, bn=btn_no:
                            self._cast_vote(t, c, False, by, bn))
                    self._vote_buttons[(category, target_user)] = {
                        "yes": btn_yes, "no": btn_no}
                else:
                    tk.Label(row_frame, text="", bg=theme.BG_PAGE,
                             width=8).grid(row=0, column=1, padx=4)
                    tk.Label(row_frame, text="", bg=theme.BG_PAGE,
                             width=8).grid(row=0, column=2, padx=4)

                counters = tk.Frame(row_frame, bg=theme.BG_PAGE)
                counters.grid(row=0, column=3, padx=(8, 0))

                vbtn = tk.Button(counters, text="✅ 0", cursor="hand2",
                                 command=lambda c=category, t=target_user:
                                     self._show_vote_details(c, t))
                theme.style_button(vbtn, variant="ghost")
                vbtn.configure(font=(theme.HAND_FONT, 10, "bold"),
                               fg=theme.GREEN_INK)
                vbtn.pack(side="left", padx=2)

                ibtn = tk.Button(counters, text="❌ 0", cursor="hand2",
                                 command=lambda c=category, t=target_user:
                                     self._show_vote_details(c, t, is_invalid=True))
                theme.style_button(ibtn, variant="ghost")
                ibtn.configure(font=(theme.HAND_FONT, 10, "bold"),
                               fg=theme.RED_INK)
                ibtn.pack(side="left", padx=2)

                self._vote_counters[(category, target_user)] = {
                    "valid_btn": vbtn, "invalid_btn": ibtn}

        sf = tk.Frame(self._categories_frame, bg=theme.BG_PAGE)
        sf.pack(fill="x", pady=(30, 10))

        self._submit_votes_btn = tk.Button(
            sf, text="Ready",
            command=self._on_submit_votes_click,
            state="normal"
        )
        theme.style_button(self._submit_votes_btn, variant="primary")
        self._submit_votes_btn.pack()

        self._submit_hint = tk.Label(
            sf,
            text="Review the answers and click when ready.",
            font=(theme.HAND_FONT, 9, "italic"),
            bg=theme.BG_PAGE, fg=theme.INK_LIGHT)
        self._submit_hint.pack(pady=(4, 0))

        self.frame.update_idletasks()
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

        if duration > 0:
            self._timer.reset()
            self._voting_duration = duration
            self._run_voting_timer()

    def _run_voting_timer(self):
        if (hasattr(self, '_voting_duration') and self._voting_duration >= 0 and self.is_active):
            self.update_timer(self._voting_duration)
            if self._voting_duration > 0:
                self._voting_duration -= 1
                self._voting_timer_job = self.frame.after(1000, self._run_voting_timer)
            else:
                self._timer.set_expired()
                self.update_status("Time's up! Submitting votes...")
                
                if hasattr(self, '_submit_votes_btn') and self._submit_votes_btn['state'] != "disabled":
                    self._on_submit_votes_click()

    def _cast_vote(self, target_user: str, category: str, is_valid: bool,
                   btn_yes: tk.Button, btn_no: tk.Button):
        self._voted_items.add((category, target_user))

        theme.style_button(btn_yes, variant="success" if is_valid else "ghost")
        theme.style_button(btn_no, variant="ghost" if is_valid else "danger")

        if hasattr(self, '_my_username'):
            self.update_peer_vote(target_user, category,
                                  f"{self._my_username} (YOU)", is_valid)
        if hasattr(self.manager, 'on_vote_cast') and self.manager.on_vote_cast:
            self.manager.on_vote_cast(target_user, category, is_valid)

    def _on_submit_votes_click(self):
        for btns in self._vote_buttons.values():
            btns["yes"].configure(state="disabled")
            btns["no"].configure(state="disabled")
        theme.style_button(self._submit_votes_btn, variant="ghost")
        self._submit_votes_btn.configure(
            state="disabled", text="Ready for the next round!")
        if hasattr(self, '_voting_timer_job'):
            self.frame.after_cancel(self._voting_timer_job)
        if hasattr(self, '_submit_hint'):
            self._submit_hint.configure(text="")
        self.update_status("Waiting for other players to finish voting...")
        if hasattr(self.manager, 'on_submit_votes') and self.manager.on_submit_votes:
            self.manager.on_submit_votes()

    def update_peer_vote(self, target_user: str, category: str,
                         voter: str, is_valid: bool):
        key = (category, target_user)
        if key not in getattr(self, '_peer_votes_data', {}):
            return
        self._peer_votes_data[key][voter] = is_valid
        if key in getattr(self, '_vote_counters', {}):
            data  = self._vote_counters[key]
            votes = self._peer_votes_data[key]
            v = sum(1 for x in votes.values() if x is True)
            i = sum(1 for x in votes.values() if x is False)
            data["valid_btn"].configure(text=f"✅ {v}")
            data["invalid_btn"].configure(text=f"❌ {i}")

    def _show_vote_details(self, category: str, target_user: str,
                           is_invalid=False):
        votes = self._peer_votes_data.get((category, target_user), {})
        if not votes:
            messagebox.showinfo("Vote details",
                                "Nobody has voted for this word yet.")
            return
        validi   = [v for v, ok in votes.items() if ok]
        invalidi = [v for v, ok in votes.items() if not ok]
        msg = f"Votes for {target_user}'s answer in «{category}»\n\n"
        if is_invalid:
            msg += (f"INVALID ({len(invalidi)}): "
                    f"{', '.join(invalidi) if invalidi else 'None'}")
        else:
            msg += (f"VALID ({len(validi)}): "
                    f"{', '.join(validi) if validi else 'None'}")
        messagebox.showinfo("Vote details", msg)
