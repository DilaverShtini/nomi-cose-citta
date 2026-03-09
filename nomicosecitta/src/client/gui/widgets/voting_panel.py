import tkinter as tk
from tkinter import messagebox
from typing import Callable, Optional

from src.client.gui import theme


class VotingPanel:
    """
    Self-contained widget for the voting phase.
    """

    def __init__(
        self,
        parent_frame: tk.Frame,
        canvas: tk.Canvas,
        timer_display,
        on_vote_cast:    Optional[Callable[[str, str, bool], None]] = None,
        on_submit_votes: Optional[Callable[[], None]]               = None,
        on_status_change: Optional[Callable[[str], None]]           = None,
    ):
        self._frame           = parent_frame
        self._canvas          = canvas
        self._timer           = timer_display
        self.on_vote_cast     = on_vote_cast
        self.on_submit_votes  = on_submit_votes
        self.on_status_change = on_status_change

        self._vote_buttons:    dict = {}
        self._voted_items:     set  = set()
        self._peer_votes_data: dict = {}
        self._vote_counters:   dict = {}
        self._my_username:     str  = ""
        self._voting_timer_job      = None

    def build(self, words_to_vote: dict, my_username: str, duration: int = 0):
        """Clear the parent frame and build the full voting UI."""
        self._my_username = my_username
        self.reset()

        self._vote_buttons.clear()
        self._voted_items.clear()
        self._peer_votes_data.clear()
        self._vote_counters.clear()

        for w in self._frame.winfo_children():
            w.destroy()

        for category, users_words in words_to_vote.items():
            tk.Label(self._frame, text=category.upper(),
                     font=theme.FONT_LABEL,
                     bg=theme.BG_PAGE, fg=theme.INK).pack(pady=(15, 5))
            for target_user, word in users_words.items():
                self._peer_votes_data[(category, target_user)] = {}
                self._build_answer_row(category, target_user, word)

        self._build_submit_row()

        self._frame.update_idletasks()
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

        if duration > 0:
            self._timer.reset()
            self._voting_duration = duration
            self._run_timer()

    def update_peer_vote(self, target_user: str, category: str,
                         voter: str, is_valid: bool):
        """Reflect a vote cast by any peer (including self) in the counter UI."""
        key = (category, target_user)
        if key not in self._peer_votes_data:
            return
        self._peer_votes_data[key][voter] = is_valid
        if key in self._vote_counters:
            votes = self._peer_votes_data[key]
            v     = sum(1 for x in votes.values() if x is True)
            i     = sum(1 for x in votes.values() if x is False)
            self._vote_counters[key]["valid_btn"].configure(text=f"✅ {v}")
            self._vote_counters[key]["invalid_btn"].configure(text=f"❌ {i}")

    def reset(self):
        """Cancel any active voting timer (call before starting a new round)."""
        if self._voting_timer_job is not None:
            self._frame.after_cancel(self._voting_timer_job)
            self._voting_timer_job = None

    # UI builders

    def _build_answer_row(self, category: str, target_user: str, word: str):
        row = tk.Frame(self._frame, bg=theme.BG_PAGE)
        row.pack(fill="x", padx=theme.PAD_LG, pady=2)
        row.columnconfigure(0, weight=1)

        display = "YOU" if target_user == self._my_username else target_user
        tk.Label(row, text=f"{display}:  {word}",
                 font=theme.FONT_BODY, bg=theme.BG_PAGE, fg=theme.INK,
                 anchor="w").grid(row=0, column=0, sticky="ew",
                                  padx=(0, theme.PAD_SM))

        if target_user != self._my_username:
            btn_yes = tk.Button(row, text="Valid",   width=8)
            btn_no  = tk.Button(row, text="Invalid", width=8)
            theme.style_button(btn_yes, variant="ghost")
            theme.style_button(btn_no,  variant="ghost")
            btn_yes.grid(row=0, column=1, padx=4)
            btn_no.grid( row=0, column=2, padx=4)
            btn_yes.configure(
                command=lambda c=category, t=target_user, y=btn_yes, n=btn_no:
                    self._cast_vote(t, c, True, y, n))
            btn_no.configure(
                command=lambda c=category, t=target_user, y=btn_yes, n=btn_no:
                    self._cast_vote(t, c, False, y, n))
            self._vote_buttons[(category, target_user)] = {
                "yes": btn_yes, "no": btn_no}
        else:
            tk.Label(row, bg=theme.BG_PAGE, width=8).grid(row=0, column=1, padx=4)
            tk.Label(row, bg=theme.BG_PAGE, width=8).grid(row=0, column=2, padx=4)

        counters = tk.Frame(row, bg=theme.BG_PAGE)
        counters.grid(row=0, column=3, padx=(8, 0))

        vbtn = tk.Button(counters, text="✅ 0", cursor="hand2",
                         command=lambda c=category, t=target_user:
                             self._show_vote_details(c, t))
        theme.style_button(vbtn, variant="ghost")
        vbtn.configure(font=(theme.HAND_FONT, 10, "bold"), fg=theme.GREEN_INK)
        vbtn.pack(side="left", padx=2)

        ibtn = tk.Button(counters, text="❌ 0", cursor="hand2",
                         command=lambda c=category, t=target_user:
                             self._show_vote_details(c, t, is_invalid=True))
        theme.style_button(ibtn, variant="ghost")
        ibtn.configure(font=(theme.HAND_FONT, 10, "bold"), fg=theme.RED_INK)
        ibtn.pack(side="left", padx=2)

        self._vote_counters[(category, target_user)] = {
            "valid_btn": vbtn, "invalid_btn": ibtn}

    def _build_submit_row(self):
        sf           = tk.Frame(self._frame, bg=theme.BG_PAGE)
        sf.pack(fill="x", pady=(30, 10))
        needs_voting = len(self._vote_buttons) > 0

        self._submit_btn = tk.Button(
            sf, text="Ready",
            command=self._on_submit_click,
            state="disabled" if needs_voting else "normal",
        )
        theme.style_button(self._submit_btn,
                           variant="ghost" if needs_voting else "primary")
        self._submit_btn.pack()

        hint = ("Vote all answers to unlock the button."
                if needs_voting else "No answers to vote.")
        self._hint_label = tk.Label(sf, text=hint,
                                    font=(theme.HAND_FONT, 9, "italic"),
                                    bg=theme.BG_PAGE, fg=theme.INK_LIGHT)
        self._hint_label.pack(pady=(4, 0))

    # Interaction handlers

    def _cast_vote(self, target: str, category: str, is_valid: bool,
                   btn_yes: tk.Button, btn_no: tk.Button):
        self._voted_items.add((category, target))
        theme.style_button(btn_yes, variant="success" if is_valid else "ghost")
        theme.style_button(btn_no,  variant="ghost"   if is_valid else "danger")

        if len(self._voted_items) >= len(self._vote_buttons):
            self._submit_btn.configure(state="normal")
            theme.style_button(self._submit_btn, variant="primary")
            self._hint_label.configure(text="All answers voted.", fg=theme.GREEN_INK)

        self.update_peer_vote(target, category, f"{self._my_username} (YOU)", is_valid)

        if self.on_vote_cast:
            self.on_vote_cast(target, category, is_valid)

    def _on_submit_click(self):
        for btns in self._vote_buttons.values():
            btns["yes"].configure(state="disabled")
            btns["no"].configure(state="disabled")
        theme.style_button(self._submit_btn, variant="ghost")
        self._submit_btn.configure(state="disabled", text="Ready for the next round!")
        self.reset()
        self._hint_label.configure(text="")

        if self.on_status_change:
            self.on_status_change("Waiting for other players to finish voting…")
        if self.on_submit_votes:
            self.on_submit_votes()

    def _show_vote_details(self, category: str, target_user: str,
                           is_invalid: bool = False):
        votes = self._peer_votes_data.get((category, target_user), {})
        if not votes:
            messagebox.showinfo("Vote details", "Nobody has voted for this word yet.")
            return
        valid   = [v for v, ok in votes.items() if ok]
        invalid = [v for v, ok in votes.items() if not ok]
        msg     = f"Votes for {target_user}'s answer in «{category}»\n\n"
        if is_invalid:
            msg += f"INVALID ({len(invalid)}): {', '.join(invalid) or 'None'}"
        else:
            msg += f"VALID ({len(valid)}): {', '.join(valid) or 'None'}"
        messagebox.showinfo("Vote details", msg)

    # Timer

    def _run_timer(self):
        if not hasattr(self, '_voting_duration') or self._voting_duration < 0:
            return
        self._timer.update(self._voting_duration)
        if self._voting_duration > 0:
            self._voting_duration -= 1
            self._voting_timer_job = self._frame.after(1000, self._run_timer)
        else:
            self._timer.set_expired()
            if self.on_status_change:
                self.on_status_change("Time's up! Submitting votes…")
            self._submit_btn.configure(state="normal")
            self._on_submit_click()