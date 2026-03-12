import asyncio
from tkinter import messagebox
from typing import TYPE_CHECKING

from src.common.message import Message, MessageType
from src.common.constants import GAME_MODE_CLASSIC

if TYPE_CHECKING:
    from src.client.main import ClientController


class MessageHandler:
    """
    Dispatches incoming messages to the correct handler method.
    Holds no mutable state of its own — all state lives in the controller.
    """

    def __init__(self, controller: "ClientController"):
        self._ctrl = controller
        self._dispatch = {
            MessageType.EVT_LOBBY_UPDATE:  self._on_lobby_update,
            MessageType.EVT_PEER_MAP:      self._on_peer_map,
            MessageType.EVT_ROUND_START:   self._on_round_start,
            MessageType.EVT_ROUND_END:     self._on_round_end,
            MessageType.EVT_VOTING_START:  self._on_voting_start,
            MessageType.EVT_SCORE_UPDATE:  self._on_score_update,
            MessageType.EVT_GAME_OVER:     self._on_game_over,
            MessageType.EVT_ERROR:         self._on_error,
            MessageType.MSG_CHAT:          self._on_chat,
            MessageType.MSG_VOTE:          self._on_vote,
        }

    def handle(self, msg: Message) -> None:
        """Dispatch a message to its handler. Unknown types are logged."""
        handler = self._dispatch.get(msg.type)
        if handler:
            handler(msg)
        else:
            self._after(lambda: self._ctrl.gui.append_log(
                f"[{msg.sender}] {msg.type}"))

    # Server to client

    def _on_lobby_update(self, msg: Message) -> None:
        c = self._ctrl
        if c.gui._current_screen.name in ("LOBBY", "LOGIN"):
            self._after(c.gui.show_lobby)

        players  = msg.payload.get("players", [])
        admin    = msg.payload.get("admin")
        settings = msg.payload.get("settings", {})
        is_admin = (admin == c.username)

        self._after(lambda: c.gui.set_admin(is_admin))
        self._after(lambda: c.gui.update_player_list(players, admin_username=admin))

        if settings:
            mode      = settings.get("mode", GAME_MODE_CLASSIC)
            num_extra = settings.get("num_extra_categories", 2)
            rt        = settings.get("round_time")
            self._after(lambda m=mode, n=num_extra, r=rt:
                        c.gui.update_lobby_settings(m, n, r))

    def _on_peer_map(self, msg: Message) -> None:
        self._ctrl.peer_map = msg.payload.get("peermap", {})
        print(f"[MSG_HANDLER] Peer map: {self._ctrl.peer_map}")

    def _on_round_start(self, msg: Message) -> None:
        c = self._ctrl
        self._after(c.gui.show_game)
        letter       = msg.payload.get("letter", "?")
        categories   = msg.payload.get("categories", [])
        duration     = msg.payload.get("duration", 60)
        round_number = msg.payload.get("round_number", 1)
        is_recovery  = msg.payload.get("is_recovery", False)
        self._after(lambda: c.gui.start_round(letter, categories, round_number, duration, is_recovery))

    def _on_round_end(self, msg: Message) -> None:
        c = self._ctrl
        self._after(lambda: c.gui.update_game_status("Time's up! Voting phase starting…"))
        self._after(lambda: c.gui.set_inputs_enabled(False))
        c.submit_answers()

    def _on_voting_start(self, msg: Message) -> None:
        c               = self._ctrl
        words_to_vote   = msg.payload.get("words_to_vote", {})
        c.my_votes      = {cat: {} for cat in words_to_vote}
        duration        = msg.payload.get("duration", 180)
        is_recovery     = msg.payload.get("is_recovery", False)
        print(f"[MSG_HANDLER] Voting phase")
        self._after(lambda: c.gui.show_voting_phase(words_to_vote, c.username, duration, is_recovery))

    def _on_score_update(self, msg: Message) -> None:
        c             = self._ctrl
        round_scores  = msg.payload.get("round_scores", {})
        global_scores = msg.payload.get("scores", {})
        round_number  = msg.payload.get("round_number", "?")
        is_recovery   = msg.payload.get("is_recovery", False)

        if is_recovery:
            return

        self._after(lambda: c.gui.update_scoreboard(global_scores, round_scores))

        winner = max(round_scores, key=round_scores.get) if round_scores else None
        summary = (
            f"── Round {round_number} done · best: {winner} +{round_scores[winner]} pts ──"
            if winner else f"── Round {round_number} done ──"
        )
        self._after(lambda: c.gui.append_log(summary))
        self._after(lambda: c.gui.update_game_status(
            "Round ended — next round starting soon…"))

    def _on_game_over(self, msg: Message) -> None:
        c      = self._ctrl
        winner = msg.payload.get("winner", "Unknown")
        scores = msg.payload.get("scores", {})

        self._after(lambda: c.gui.update_scoreboard(scores))

        lines   = ["GAME OVER", f"Winner: {winner}", ""]
        lines  += [f"  {u}: {p} pts"
                   for u, p in sorted(scores.items(), key=lambda kv: kv[1], reverse=True)]
        message = "\n".join(lines)

        self._after(lambda: messagebox.showinfo("Game Over", message))
        self._after(c.gui.show_lobby)
        print(f"[MSG_HANDLER] Game over — winner: {winner}")

    def _on_error(self, msg: Message) -> None:
        err = msg.payload.get("error", "Generic error")
        self._after(lambda: messagebox.showerror("Error", err))
        asyncio.run_coroutine_threadsafe(
            self._ctrl.network.disconnect(), self._ctrl.loop
        )

    # Peer to client

    def _on_chat(self, msg: Message) -> None:
        text = f"{msg.sender}: {msg.payload.get('text', '')}"
        self._after(lambda: self._ctrl.gui.append_log(text))

    def _on_vote(self, msg: Message) -> None:
        c        = self._ctrl
        target   = msg.payload["target"]
        category = msg.payload["category"]
        is_valid = msg.payload["valid"]
        voter    = msg.sender
        print(f"[P2P] Vote from {voter}: {target} → {category} = {is_valid}")
        self._after(lambda: c.gui.update_peer_vote(
            target_user=target, category=category, voter=voter, is_valid=is_valid))

    # Utility

    def _after(self, fn) -> None:
        """Schedule a callable on the Tkinter main thread."""
        self._ctrl.root.after(0, fn)