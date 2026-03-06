import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(root_dir)

import asyncio
import threading
import tkinter as tk
from tkinter import messagebox
from src.common.message import Message, MessageType
from src.common.constants import DEFAULT_SERVER_PORT, GAME_MODE_CLASSIC

from src.client.network_handler import NetworkHandler
from src.client.reconnection_manager import ReconnectionManager
from src.client.gui import GUIManager

# Constants for lobby actions
_ACTION_SETTINGS   = "settings"
_ACTION_CATEGORIES = "categories"


class ClientController:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.network = None
        self.username = ""
        self.peer_map = {}
        self.my_votes = {}

        # Reconnection state
        self.reconnection_manager = ReconnectionManager()
        self.p2p_port: int = 0
        self._reconnecting: bool = False
        self._intentional_disconnect: bool = False

        # GUI
        self.root = tk.Tk()
        self.gui = GUIManager(self.root)

        self.gui.on_connect                = self.connect_to_server
        self.gui.on_send_message           = self.send_message
        self.gui.on_start_game             = self.request_game_start
        self.gui.on_submit_answers         = self.submit_answers
        self.gui.on_lobby_settings_changed = self.send_lobby_settings
        self.gui.on_vote_cast              = self.handle_user_vote
        self.gui.on_submit_votes           = self.submit_final_votes
        self.gui.on_category_vote_changed  = self.send_category_vote

        self.network_thread = threading.Thread(
            target=self._start_async_loop, daemon=True)
        self.network_thread.start()

    def _start_async_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    # Connection

    def connect_to_server(self, ip, username):
        self.username = username
        self._intentional_disconnect = False

        host, port = self.reconnection_manager.get_initial_server()
        self.network = self._build_handler(host, port)
        asyncio.run_coroutine_threadsafe(self._async_connect(), self.loop)

    def _build_handler(self, host: str, port: int) -> NetworkHandler:
        handler = NetworkHandler(host=host, port=port)
        handler.on_message = self.handle_incoming_message
        handler.on_disconnect = self.handle_disconnection
        return handler

    async def _async_connect(self):
        self.p2p_port = await self.network.start_p2p_listener()
        success  = await self.network.connect()

        if success:
            await self.network.send(Message(
                type=MessageType.CMD_JOIN,
                sender=self.username,
                payload={"username": self.username, "p2p_port": self.p2p_port},
            ))
        else:
            self.root.after(0, lambda: messagebox.showerror(
                "Error", "Unable to connect to the server.\n"
                f"Check config.json — servers: "
                f"{', '.join(self.reconnection_manager.server_list)}"))

    # Disconnection & reconnection

    def handle_disconnection(self, reason: str):
        if self._intentional_disconnect:
            print("[CONTROLLER] Clean disconnect — skipping reconnection.")
            return

        if self._reconnecting:
            print("[CONTROLLER] Reconnect already in progress — ignoring duplicate signal.")
            return

        print(f"[CONTROLLER] Unexpected disconnection: {reason}")
        self._reconnecting = True

        # Create the overlay on the main thread FIRST, then start the async loop
        # from inside it — this guarantees the window exists before any
        # reconnection callback tries to update or close it.
        self.root.after(0, lambda: self._show_reconnect_overlay(reason))

    # Reconnection overlay

    def _show_reconnect_overlay(self, reason: str):
        self._overlay = tk.Toplevel(self.root)
        self._overlay.title("Reconnecting…")
        self._overlay.resizable(False, False)
        self._overlay.grab_set()
        self._overlay.protocol("WM_DELETE_WINDOW", lambda: None)

        self._overlay.geometry("380x160")
        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width()  - 380) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 160) // 2
        self._overlay.geometry(f"380x160+{x}+{y}")

        tk.Label(self._overlay,
                 text="⚠  Connection lost",
                 font=("Segoe UI", 12, "bold")).pack(pady=(18, 4))
        tk.Label(self._overlay,
                 text=f"Reason: {reason}",
                 font=("Segoe UI", 9),
                 fg="#888").pack()

        self._overlay_status = tk.StringVar(value="Connecting…")
        tk.Label(self._overlay,
                 textvariable=self._overlay_status,
                 font=("Segoe UI", 10),
                 fg="#2b6cb0",
                 wraplength=340).pack(pady=(12, 0))

        self._overlay.update()

        asyncio.run_coroutine_threadsafe(self._async_reconnect(), self.loop)

    def _update_overlay(self, msg: str):
        try:
            self._overlay_status.set(msg)
            self._overlay.update_idletasks()
        except Exception:
            pass
        try:
            self.gui.append_log(f"[⟳] {msg}")
        except Exception:
            pass

    def _close_overlay(self):
        try:
            self._overlay.grab_release()
            self._overlay.destroy()
        except Exception:
            pass

    # Async reconnect loop

    async def _async_reconnect(self):
        def status_update(msg: str):
            self.root.after(0, lambda m=msg: self._update_overlay(m))

        new_handler = await self.reconnection_manager.reconnect(
            network_factory=self._build_handler,
            username=self.username,
            p2p_port=self.p2p_port,
            on_status=status_update,
        )

        self._reconnecting = False

        if new_handler is None:
            self.root.after(0, self._on_reconnection_failed)
            return

        self.network = new_handler
        host, port = self.reconnection_manager.get_current_server()
        print(f"[CONTROLLER] Active server is now {host}:{port}")

        success = await self.network.send(Message(
            type=MessageType.CMD_JOIN,
            sender=self.username,
            payload={"username": self.username, "p2p_port": self.p2p_port},
        ))

        if success:
            self.root.after(0, lambda h=host, p=port:
                            self._on_reconnection_success(h, p))
        else:
            self.root.after(0, self._on_reconnection_failed)

    # Reconnection outcome callbacks

    def _on_reconnection_success(self, host: str, port: int):
        self._close_overlay()
        info = f"Reconnected to {host}:{port}"
        self.gui.append_log(f"[✓] {info}")
        self.gui.update_game_status(info)
        print(f"[CONTROLLER] {info}")

    def _on_reconnection_failed(self):
        self._close_overlay()
        messagebox.showwarning(
            "Connection Lost",
            "Could not reconnect to any server.\n\n"
            f"Servers tried: {', '.join(self.reconnection_manager.server_list)}\n\n"
            "You will be returned to the login screen.")
        self.gui.show_login()
    
    # Lobby

    def send_lobby_settings(self, settings: dict):
        if self.network and self.network.is_connected():
            asyncio.run_coroutine_threadsafe(
                self.network.send(Message(
                    type=MessageType.CMD_LOBBY_ACTION,
                    sender=self.username,
                    payload={
                        "action_type":          _ACTION_SETTINGS,
                        "mode":                 settings["mode"],
                        "num_extra_categories": settings["num_extra_categories"],
                        "round_time":           settings["round_time"],
                    },
                )), self.loop)

    def send_category_vote(self, categories: list):
        if self.network and self.network.is_connected():
            asyncio.run_coroutine_threadsafe(
                self.network.send(Message(
                    type=MessageType.CMD_LOBBY_ACTION,
                    sender=self.username,
                    payload={"action_type": _ACTION_CATEGORIES, "categories": categories},
                )), self.loop)

    def request_game_start(self, settings: dict):
        print(f"[CONTROLLER] Request to start game: {settings}")
        if self.network and self.network.is_connected():
            asyncio.run_coroutine_threadsafe(
                self.network.send(Message(
                    type=MessageType.CMD_START_GAME,
                    sender=self.username,
                    payload={
                        "mode":                 settings["mode"],
                        "num_extra_categories": settings["num_extra_categories"],
                        "round_time":           settings["round_time"],
                    },
                )), self.loop)
        else:
            print("[ERROR] Not connected, unable to start game.")

    # Incoming messages

    def handle_incoming_message(self, msg_obj: Message):
        t = msg_obj.type

        if t == MessageType.EVT_LOBBY_UPDATE:
            if self.gui._current_screen.name in ("LOBBY", "LOGIN"):
                self.root.after(0, self.gui.show_lobby)

            players   = msg_obj.payload.get("players", [])
            admin     = msg_obj.payload.get("admin")
            settings  = msg_obj.payload.get("settings", {})
            is_admin  = (admin == self.username)

            self.root.after(0, lambda: self.gui.set_admin(is_admin))
            self.root.after(0, lambda: self.gui.update_player_list(players, admin_username=admin))
            if settings:
                mode       = settings.get("mode", GAME_MODE_CLASSIC)
                num_extra  = settings.get("num_extra_categories", 2)
                round_time = settings.get("round_time")
                self.root.after(0, lambda m=mode, n=num_extra, rt=round_time:
                                self.gui.update_lobby_settings(m, n, rt))

        elif t == MessageType.EVT_PEER_MAP:
            self.peer_map = msg_obj.payload.get("peermap", {})
            print(f"[CONTROLLER] Peer map updated: {self.peer_map}")

        elif t == MessageType.EVT_ROUND_START:
            self.root.after(0, self.gui.show_game)
            letter       = msg_obj.payload.get("letter", "?")
            categories   = msg_obj.payload.get("categories", [])
            duration     = msg_obj.payload.get("duration", 60)
            round_number = msg_obj.payload.get("round_number", 1)
            self.root.after(0, lambda: self.gui.start_round(
                letter, categories, round_number, duration))

        elif t == MessageType.EVT_ROUND_END:
            self.root.after(0, lambda: self.gui.update_game_status(
                "Time's up! Voting phase starting..."))
            self.root.after(0, lambda: self.gui.set_inputs_enabled(False))
            self.submit_answers()

        elif t == MessageType.EVT_VOTING_START:
            words_to_vote = msg_obj.payload.get("words_to_vote", {})
            self.my_votes = {cat: {} for cat in words_to_vote}
            duration = msg_obj.payload.get("duration", 180)
            print(f"[CONTROLLER] Voting phase — words: {words_to_vote}")
            self.root.after(0, lambda: self.gui.show_voting_phase(words_to_vote, self.username, duration))

        elif t == MessageType.EVT_SCORE_UPDATE:
            self._handle_score_update(msg_obj.payload)

        elif t == MessageType.EVT_GAME_OVER:
            self._handle_game_over(msg_obj.payload)

        elif t == MessageType.EVT_ERROR:
            err = msg_obj.payload.get("error", "Generic error")
            self.root.after(0, lambda: messagebox.showerror("Error", err))
            asyncio.run_coroutine_threadsafe(self.network.disconnect(), self.loop)

        elif t == MessageType.MSG_CHAT:
            chat_text = f"{msg_obj.sender}: {msg_obj.payload.get('text', '')}"
            self.root.after(0, lambda: self.gui.append_log(chat_text))

        elif t == MessageType.MSG_VOTE:
            target   = msg_obj.payload["target"]
            category = msg_obj.payload["category"]
            is_valid = msg_obj.payload["valid"]
            voter    = msg_obj.sender
            print(f"[P2P] Vote received from {voter}: {target} -> {category} is {is_valid}")
            self.root.after(0, lambda: self.gui.update_peer_vote(
                target_user=target,
                category=category,
                voter=voter,
                is_valid=is_valid,
            ))

        else:
            self.root.after(0, lambda: self.gui.append_log(
                f"[{msg_obj.sender}] {msg_obj.type}"))

    # Score update & game over

    def _handle_score_update(self, payload: dict):
        round_scores  = payload.get("round_scores", {})
        global_scores = payload.get("scores", {})
        round_number  = payload.get("round_number", "?")

        self.root.after(0, lambda: self.gui.update_scoreboard(
            global_scores, round_scores))

        winner_this_round = max(round_scores, key=round_scores.get) if round_scores else None
        if winner_this_round:
            top_pts = round_scores[winner_this_round]
            summary = (
                f"── Round {round_number} done · "
                f"best: {winner_this_round} +{top_pts} pts ──"
            )
        else:
            summary = f"── Round {round_number} done ──"

        self.root.after(0, lambda: self.gui.append_log(summary))
        self.root.after(0, lambda: self.gui.update_game_status(
            "Round ended — next round starting soon..."))

        print(f"[CONTROLLER] Score update — global: {global_scores}")

    def _handle_game_over(self, payload: dict):
        winner = payload.get("winner", "Unknown")
        scores = payload.get("scores", {})

        self.root.after(0, lambda: self.gui.update_scoreboard(scores))

        lines = ["GAME OVER", f"Winner: {winner}", ""]
        for user, pts in sorted(scores.items(), key=lambda kv: kv[1], reverse=True):
            lines.append(f"  {user}: {pts} pts")
        message = "\n".join(lines)

        self.root.after(0, lambda: messagebox.showinfo("Game Over", message))
        self.root.after(0, self.gui.show_lobby)

        print(f"[CONTROLLER] Game over — winner: {winner}, scores: {scores}")

    # Answers & votes submission

    def submit_answers(self, answers=None):
        print("[CONTROLLER] Sending answers to server...")
        if answers is None:
            answers = self.gui.get_answers()
        if self.network and self.network.is_connected():
            asyncio.run_coroutine_threadsafe(
                self.network.send(Message(
                    type=MessageType.CMD_SUBMIT,
                    sender=self.username,
                    payload={"words": answers},
                )), self.loop)
        else:
            print("[ERROR] Disconnected. Cannot submit answers.")

    def handle_user_vote(self, target_user: str, category: str, is_valid: bool):
        if category in self.my_votes:
            self.my_votes[category][target_user] = is_valid

        if self.network and self.network.is_connected():
            asyncio.run_coroutine_threadsafe(
                self.broadcast_vote(target_user, category, is_valid),
                self.loop)
        else:
            print("[ERROR] Disconnected. Cannot broadcast vote.")

    async def broadcast_vote(self, target_user: str, category: str, is_valid: bool):
        vote_msg = Message(
            type=MessageType.MSG_VOTE,
            sender=self.username,
            payload={"target": target_user, "category": category, "valid": is_valid},
        )
        for peer_name, peer_address in self.peer_map.items():
            if peer_name != self.username:
                await self.network.send_p2p(peer_address, vote_msg)

    def submit_final_votes(self):
        print(f"[CONTROLLER] Sending final votes to server: {self.my_votes}")
        if self.network and self.network.is_connected():
            asyncio.run_coroutine_threadsafe(
                self.network.send(Message(
                    type=MessageType.CMD_SUBMIT,
                    sender=self.username,
                    payload={"votes": self.my_votes},
                )), self.loop)
        else:
            print("[ERROR] Disconnected. Cannot submit votes.")

    # Chat

    def send_message(self, msg_text: str):
        if not msg_text.strip():
            return
        self.gui.append_log(f"YOU: {msg_text}")
        chat_msg = Message(
            type=MessageType.MSG_CHAT,
            sender=self.username,
            payload={"text": msg_text},
        )
        asyncio.run_coroutine_threadsafe(
            self.broadcast_chat_p2p(chat_msg), self.loop)

    async def broadcast_chat_p2p(self, chat_msg: Message):
        for peer_name, peer_address in self.peer_map.items():
            if peer_name != self.username:
                await self.network.send_p2p(peer_address, chat_msg)

    def run(self):
        try:
            self.root.mainloop()
        finally:
            if self.network:
                asyncio.run_coroutine_threadsafe(
                    self.network.disconnect(), self.loop)
            self.loop.call_soon_threadsafe(self.loop.stop)


if __name__ == "__main__":
    app = ClientController()
    app.run()