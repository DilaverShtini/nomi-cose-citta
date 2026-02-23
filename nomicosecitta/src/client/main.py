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
from src.client.gui import GUIManager

_ACTION_SETTINGS   = "settings"
_ACTION_CATEGORIES = "categories"


class ClientController:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.network = None
        self.username = ""
        self.peer_map = {}

        self.root = tk.Tk()
        self.gui = GUIManager(self.root)

        self.gui.on_connect                = self.connect_to_server
        self.gui.on_send_message           = self.send_message
        self.gui.on_start_game             = self.request_game_start
        self.gui.on_submit_answers         = self.submit_answers
        self.gui.on_lobby_settings_changed = self.send_lobby_settings
        self.gui.on_vote_cast = self.handle_user_vote

        self.gui.on_category_vote_changed  = self.send_category_vote

        self.network_thread = threading.Thread(
            target=self._start_async_loop, daemon=True)
        self.network_thread.start()

    def _start_async_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def connect_to_server(self, ip, username):
        self.username = username
        self.network = NetworkHandler(host=ip, port=DEFAULT_SERVER_PORT)
        self.network.on_message    = self.handle_incoming_message
        self.network.on_disconnect = self.handle_disconnection
        asyncio.run_coroutine_threadsafe(self._async_connect(), self.loop)

    async def _async_connect(self):
        p2p_port = await self.network.start_p2p_listener()
        success = await self.network.connect()
        if success:
            join_msg = Message(
                type=MessageType.CMD_JOIN,
                sender=self.username,
                payload={
                    "username": self.username,
                    "p2p_port": p2p_port
                }
            )
            await self.network.send(join_msg)
        else:
            self.root.after(0, lambda: messagebox.showerror(
                "Error", "Unable to connect to the server"))

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
                )),
                self.loop,
            )

    def send_category_vote(self, categories: list):
        if self.network and self.network.is_connected():
            asyncio.run_coroutine_threadsafe(
                self.network.send(Message(
                    type=MessageType.CMD_LOBBY_ACTION,
                    sender=self.username,
                    payload={
                        "action_type": _ACTION_CATEGORIES,
                        "categories":  categories,
                    },
                )),
                self.loop,
            )

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
                )),
                self.loop,
            )
        else:
            print("[ERROR] Not connected, unable to start game.")

    def handle_incoming_message(self, msg_obj: Message):
        t = msg_obj.type

        if t == MessageType.EVT_LOBBY_UPDATE:
            self.root.after(0, self.gui.show_lobby)

            players  = msg_obj.payload.get("players", [])
            admin    = msg_obj.payload.get("admin")
            settings = msg_obj.payload.get("settings", {})
            is_admin = (admin == self.username)

            self.root.after(0, lambda: self.gui.set_admin(is_admin))
            self.root.after(0, lambda: self.gui.update_player_list(players, admin_username=admin))

            if settings:
                mode      = settings.get("mode", GAME_MODE_CLASSIC)
                num_extra = settings.get("num_extra_categories", 2)
                self.root.after(
                    0, lambda m=mode, n=num_extra: self.gui.update_lobby_settings(m, n))
        
        elif msg_obj.type == MessageType.EVT_PEER_MAP:
            self.peer_map = msg_obj.payload.get("peermap", {})
            print(f"[CONTROLLER] Updated peer map: {self.peer_map}")

        elif t == MessageType.EVT_ROUND_START:
            self.root.after(0, self.gui.show_game)
            letter       = msg_obj.payload.get("letter", "?")
            categories   = msg_obj.payload.get("categories", [])
            duration     = msg_obj.payload.get("duration", 60)
            round_number = msg_obj.payload.get("round_number", 1)
            self.root.after(
                0, lambda: self.gui.start_round(letter, categories, round_number, duration))

        elif t == MessageType.EVT_ROUND_END:
            self.root.after(0, lambda: self.gui.update_game_status(
                "Time's up! Round ended. Voting phase starting..."))
            self.root.after(0, lambda: self.gui.set_inputs_enabled(False))
            self.submit_answers()

        elif msg_obj.type == MessageType.EVT_VOTING_START:
            words_to_vote = msg_obj.payload.get("words_to_vote", {})
            print(f"[CONTROLLER] Starting voting phase for: {words_to_vote}")
            self.root.after(0, lambda: self.gui.show_voting_phase(words_to_vote, self.username))

        elif t == MessageType.EVT_ERROR:
            err = msg_obj.payload.get("error", "Generic error")
            self.root.after(0, lambda: messagebox.showerror("Login error", err))
            asyncio.run_coroutine_threadsafe(self.network.disconnect(), self.loop)

        elif t == MessageType.MSG_CHAT:
            chat_text = f"{msg_obj.sender}: {msg_obj.payload.get('text', '')}"
            self.root.after(0, lambda: self.gui.append_log(chat_text))

        elif msg_obj.type == MessageType.MSG_VOTE:
            target = msg_obj.payload["target"]
            category = msg_obj.payload["category"]
            is_valid = msg_obj.payload["valid"]
            voter = msg_obj.sender
            print(f"[P2P] Vote received from {voter}: {target} -> {category} is {is_valid}")
            #TODO: Manage vote received.

        else:
            self.root.after(0, lambda: self.gui.append_log(
                f"[{msg_obj.sender}] {msg_obj.type}"))

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
                )),
                self.loop,
            )
        else:
            print("[ERROR] Disconnected. Impossible to submit answers.")

    def send_message(self, msg_text: str):
        if self.network and self.network.is_connected():
            asyncio.run_coroutine_threadsafe(
                self.network.send(Message(
                    type=MessageType.MSG_CHAT,
                    sender=self.username,
                    payload={"text": msg_text},
                )),
                self.loop,
            )
            self.gui.append_log(f"TU: {msg_text}")

    async def broadcast_vote(self, target_user, category, is_valid):
        """Send a vote to all peers via P2P."""
        vote_msg = Message(
            type=MessageType.MSG_VOTE,
            sender=self.username,
            payload={
                "target": target_user,
                "category": category,
                "valid": is_valid
            }
        )
        for peer_name, peer_address in self.peer_map.items():
            if peer_name != self.username:
                await self.network.send_p2p(peer_address, vote_msg)
    
    def handle_user_vote(self, target_user, category, is_valid):
        """Called when the user casts a vote in the GUI. Broadcasts the vote to peers."""
        if self.network and self.network.is_connected():
            asyncio.run_coroutine_threadsafe(
                self.broadcast_vote(target_user, category, is_valid),
                self.loop
            )

    def handle_disconnection(self, reason):
        self.root.after(0, lambda: messagebox.showwarning("Disconnected", f"Lost connection: {reason}"))
    def handle_disconnection(self, reason: str):
        self.root.after(0, lambda: messagebox.showwarning(
            "Disconnected", f"Connection lost: {reason}"))
        self.root.after(0, self.gui.show_login)

    def run(self):
        try:
            self.root.mainloop()
        finally:
            if self.network:
                asyncio.run_coroutine_threadsafe(self.network.disconnect(), self.loop)
            self.loop.call_soon_threadsafe(self.loop.stop)

if __name__ == "__main__":
    app = ClientController()
    app.run()