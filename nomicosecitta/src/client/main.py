import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir    = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(root_dir)

import asyncio
import threading
import tkinter as tk
from tkinter import messagebox

from src.common.message import Message, MessageType
from src.common.constants import DEFAULT_SERVER_PORT, GAME_MODE_CLASSIC

from src.client.network_handler     import NetworkHandler
from src.client.reconnection_manager import ReconnectionManager
from src.client.message_handler     import MessageHandler
from src.client.gui                 import GUIManager

_ACTION_SETTINGS   = "settings"
_ACTION_CATEGORIES = "categories"


class ClientController:
    def __init__(self):
        self.loop     = asyncio.new_event_loop()
        self.network  = None
        self.username = ""
        self.peer_map: dict[str, str] = {}
        self.my_votes: dict[str, dict] = {}

        self.reconnection_manager = ReconnectionManager()
        self.p2p_port:   int  = 0
        self._reconnecting:          bool = False
        self._intentional_disconnect: bool = False

        # GUI
        self.root = tk.Tk()
        self.gui  = GUIManager(self.root)
        self._wire_gui_callbacks()

        # Message handler
        self._msg_handler = MessageHandler(self)

        self._network_thread = threading.Thread(
            target=self._start_async_loop, daemon=True
        )
        self._network_thread.start()

    def _wire_gui_callbacks(self):
        self.gui.on_connect                = self.connect_to_server
        self.gui.on_send_message           = self.send_message
        self.gui.on_start_game             = self.request_game_start
        self.gui.on_submit_answers         = self.submit_answers
        self.gui.on_lobby_settings_changed = self.send_lobby_settings
        self.gui.on_vote_cast              = self.handle_user_vote
        self.gui.on_submit_votes           = self.submit_final_votes
        self.gui.on_category_vote_changed  = self.send_category_vote

    def _start_async_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    # Connection

    def connect_to_server(self, ip: str, username: str):
        self.username = username
        self._intentional_disconnect = False
        self.root.config(cursor="watch")
        self.root.title("Nomi, Cose, Città — Searching for server…")

        discovered_ip, discovered_port = \
            self.reconnection_manager.discover_server_on_lan()
        if discovered_ip:
            self.reconnection_manager.set_discovered_server(discovered_ip, discovered_port)

        host, port = (
            (discovered_ip, discovered_port)
            if discovered_ip
            else self.reconnection_manager.get_initial_server()
        )
        future = asyncio.run_coroutine_threadsafe(
            self._async_connect(host, port), self.loop
        )
        future.add_done_callback(self._on_connect_done)

    def _on_connect_done(self, future):
        try:
            future.result()
        except Exception as e:
            import traceback
            print(f"[FATAL] {e}")
            traceback.print_exc()
        self.root.after(0, lambda: self.root.config(cursor=""))
        self.root.after(0, lambda: self.root.title("Nomi, Cose, Città"))

    async def _async_connect(self, host: str, port: int):
        def _status(msg: str):
            print(f"[LOGIN] {msg}")
            self.root.after(0, lambda: self.root.title(f"Searching: {msg}"))

        _status(f"Connecting to {host}:{port}…")
        self.network  = self._build_handler(host, port)
        self.p2p_port = await self.network.start_p2p_listener()
        success       = await self.network.connect()

        if not success:
            _status("Direct connection failed — trying fallback…")
            new_handler = await self.reconnection_manager.reconnect(
                network_factory=self._build_handler,
                username=self.username,
                p2p_port=0,
                on_status=_status,
            )
            if new_handler is None:
                self.root.after(0, lambda: messagebox.showerror(
                    "Error",
                    "Could not connect to any server.\n"
                    f"Tried: {', '.join(self.reconnection_manager.server_list)}",
                ))
                return
            self.network  = new_handler
            self.p2p_port = await self.network.start_p2p_listener()

        await self.network.send(Message(
            type=MessageType.CMD_JOIN,
            sender=self.username,
            payload={"username": self.username, "p2p_port": self.p2p_port},
        ))

    def _build_handler(self, host: str, port: int) -> NetworkHandler:
        handler              = NetworkHandler(host, port)
        handler.on_message   = self._msg_handler.handle
        handler.on_disconnect = self.handle_disconnection
        return handler

    # Disconnection & reconnection

    def handle_disconnection(self, reason: str):
        if self._intentional_disconnect:
            return
        if self._reconnecting:
            return
        print(f"[CONTROLLER] Unexpected disconnection: {reason}")
        self._reconnecting = True
        self.root.after(0, lambda: self._show_reconnect_overlay(reason))

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

        tk.Label(self._overlay, text="⚠  Connection lost",
                 font=("Segoe UI", 12, "bold")).pack(pady=(18, 4))
        tk.Label(self._overlay, text=f"Reason: {reason}",
                 font=("Segoe UI", 9), fg="#888").pack()
        self._overlay_status = tk.StringVar(value="Connecting…")
        tk.Label(self._overlay, textvariable=self._overlay_status,
                 font=("Segoe UI", 10), fg="#2b6cb0", wraplength=340).pack(pady=(12, 0))
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

    async def _async_reconnect(self):
        new_handler = await self.reconnection_manager.reconnect(
            network_factory=self._build_handler,
            username=self.username,
            p2p_port=self.p2p_port,
            on_status=lambda m: self.root.after(0, lambda msg=m: self._update_overlay(msg)),
        )
        self._reconnecting = False

        if new_handler is None:
            self.root.after(0, self._on_reconnection_failed)
            return

        self.network  = new_handler
        self.p2p_port = await self.network.start_p2p_listener()
        host, port    = self.reconnection_manager.get_current_server()

        success = await self.network.send(Message(
            type=MessageType.CMD_JOIN,
            sender=self.username,
            payload={"username": self.username, "p2p_port": self.p2p_port},
        ))

        if success:
            self.root.after(0, lambda h=host, p=port: self._on_reconnection_success(h, p))
        else:
            self.root.after(0, self._on_reconnection_failed)

    def _on_reconnection_success(self, host: str, port: int):
        self._close_overlay()
        info = f"Reconnected to {host}:{port}"
        self.gui.append_log(f"[✓] {info}")
        self.gui.update_game_status(info)

    def _on_reconnection_failed(self):
        self._close_overlay()
        messagebox.showwarning(
            "Connection Lost",
            "Could not reconnect to any server.\n\n"
            f"Servers tried: {', '.join(self.reconnection_manager.server_list)}\n\n"
            "Returning to the login screen.",
        )
        self.gui.show_login()
    
    # Lobby

    def send_lobby_settings(self, settings: dict):
        self._send_async(Message(
            type=MessageType.CMD_LOBBY_ACTION,
            sender=self.username,
            payload={
                "action_type":          _ACTION_SETTINGS,
                "mode":                 settings["mode"],
                "num_extra_categories": settings["num_extra_categories"],
                "round_time":           settings["round_time"],
            },
        ))

    def send_category_vote(self, categories: list):
        self._send_async(Message(
            type=MessageType.CMD_LOBBY_ACTION,
            sender=self.username,
            payload={"action_type": _ACTION_CATEGORIES, "categories": categories},
        ))

    def request_game_start(self, settings: dict):
        print(f"[CONTROLLER] Requesting game start: {settings}")
        self._send_async(Message(
            type=MessageType.CMD_START_GAME,
            sender=self.username,
            payload={
                "mode":                 settings["mode"],
                "num_extra_categories": settings["num_extra_categories"],
                "round_time":           settings["round_time"],
            },
        ))

    def submit_answers(self, answers: dict | None = None):
        if answers is None:
            answers = self.gui.get_answers()
        print("[CONTROLLER] Submitting answers…")
        self._send_async(Message(
            type=MessageType.CMD_SUBMIT,
            sender=self.username,
            payload={"words": answers},
        ))

    def handle_user_vote(self, target_user: str, category: str, is_valid: bool):
        if category in self.my_votes:
            self.my_votes[category][target_user] = is_valid
        asyncio.run_coroutine_threadsafe(
            self.broadcast_vote(target_user, category, is_valid), self.loop
        )

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
        print(f"[CONTROLLER] Submitting final votes: {self.my_votes}")
        self._send_async(Message(
            type=MessageType.CMD_SUBMIT,
            sender=self.username,
            payload={"votes": self.my_votes},
        ))

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
            self._broadcast_chat_p2p(chat_msg), self.loop
        )

    async def _broadcast_chat_p2p(self, chat_msg: Message):
        for peer_name, peer_address in self.peer_map.items():
            if peer_name != self.username:
                await self.network.send_p2p(peer_address, chat_msg)

    # Internals

    def _send_async(self, msg: Message):
        if self.network and self.network.is_connected():
            asyncio.run_coroutine_threadsafe(self.network.send(msg), self.loop)
        else:
            print(f"[ERROR] Not connected — cannot send {msg.type}.")

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)
        try:
            self.root.mainloop()
        finally:
            self._shutdown()

    def _on_window_close(self):
        self._intentional_disconnect = True
        self.root.quit()

    def _shutdown(self):
        print("[CLIENT] Shutting down…")
        if self.network:
            future = asyncio.run_coroutine_threadsafe(
                self.network.disconnect(), self.loop
            )
            try:
                future.result(timeout=1.5)
            except Exception:
                pass
        self.loop.call_soon_threadsafe(self.loop.stop)
        print("[CLIENT] Shutdown complete.")


if __name__ == "__main__":
    ClientController().run()