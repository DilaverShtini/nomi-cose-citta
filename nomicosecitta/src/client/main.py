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

from src.client.network_handler import NetworkHandler
from src.client.gui import GUIManager
from src.common.constants import DEFAULT_SERVER_PORT

class ClientController:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.network = None
        self.username = ""

        self.root = tk.Tk()
        self.gui = GUIManager(self.root)
        self.gui.on_connect = self.connect_to_server
        self.gui.on_send_message = self.send_message

        self.gui.on_start_game = self.request_game_start
        self.gui.on_submit_answers = self.submit_answers

        self.network_thread = threading.Thread(target=self._start_async_loop, daemon=True)
        self.network_thread.start()

    def _start_async_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def connect_to_server(self, ip, username):
        self.username = username
        self.network = NetworkHandler(host=ip, port=DEFAULT_SERVER_PORT)

        self.network.on_message = self.handle_incoming_message
        self.network.on_disconnect = self.handle_disconnection

        asyncio.run_coroutine_threadsafe(self._async_connect(), self.loop)

    async def _async_connect(self):
        success = await self.network.connect()
        if success:            
            join_msg = Message(
                type=MessageType.CMD_JOIN,
                sender=self.username,
                payload={"username": self.username}
            )
            await self.network.send(join_msg) 
        else:
            self.root.after(0, lambda: messagebox.showerror("Errore", "Impossibile connettersi al Server"))

    def request_game_start(self, settings):
        print(f"[CONTROLLER] Richiesta avvio gioco: {settings}")
        
        if self.network and self.network.is_connected():
            msg = Message(
                type=MessageType.CMD_START_GAME,
                sender=self.username,
                payload=settings
            )
            asyncio.run_coroutine_threadsafe(
                self.network.send(msg),
                self.loop
            )
        else:
            print("[ERROR] Non connesso, impossibile avviare.")

    def handle_incoming_message(self, msg_obj):        
        if msg_obj.type == MessageType.EVT_LOBBY_UPDATE:
            self.root.after(0, self.gui.show_lobby) 

            players = msg_obj.payload.get("players", [])
            admin = msg_obj.payload.get("admin")
            is_admin = (admin == self.username)
            self.root.after(0, lambda: self.gui.set_admin(is_admin))
            self.root.after(0, lambda: self.gui.update_player_list(players, admin_username=admin))
            self.root.after(0, lambda: self.gui.update_player_list(players))

        elif msg_obj.type == MessageType.EVT_ROUND_START:
            self.root.after(0, self.gui.show_game)
            
            letter = msg_obj.payload.get("letter", "?")
            categories = msg_obj.payload.get("categories", [])
            duration = msg_obj.payload.get("duration", 60)
            round_number = msg_obj.payload.get("round_number", 22)
            
            self.root.after(0, lambda: self.gui.update_game_letter(letter))
            self.root.after(0, lambda: self.gui.start_round(letter, categories, round_number, duration))

        elif msg_obj.type == MessageType.EVT_ROUND_END:
            reason = msg_obj.payload.get("reason", "")
            new_status = "Time's up! Round ended. Voting phase starting..."
            self.root.after(0, lambda: self.gui.update_game_status(new_status))
            self.root.after(0, lambda: self.gui.set_inputs_enabled(False))
            self.submit_answers()

        elif msg_obj.type == MessageType.EVT_ERROR:
            err = msg_obj.payload.get("error", "Errore generico")
            self.root.after(0, lambda: messagebox.showerror("Errore di Login", err))

            asyncio.run_coroutine_threadsafe(self.network.disconnect(), self.loop)

        elif msg_obj.type == MessageType.MSG_CHAT:
             chat_text = f"{msg_obj.sender}: {msg_obj.payload.get('text', '')}"
             self.root.after(0, lambda: self.gui.append_log(chat_text))

        else:
            text = f"[{msg_obj.sender}] {msg_obj.type}"
            self.root.after(0, lambda: self.gui.append_log(text))

    def submit_answers(self, answers=None):
        print("[CONTROLLER] Invio risposte al server...")
        if answers is None:
            answers = self.gui.get_answers() 
        
        if self.network and self.network.is_connected():
            submit_msg = Message(
                type=MessageType.CMD_SUBMIT,
                sender=self.username,
                payload={"words": answers}
            )
            asyncio.run_coroutine_threadsafe(
                self.network.send(submit_msg),
                self.loop
            )
        else:
            print("[ERROR] Disconnesso. Impossibile inviare le risposte.")

    def send_message(self, msg_text):
        if self.network and self.network.is_connected():
            chat_msg = Message(
                type=MessageType.MSG_CHAT,
                sender=self.username,
                payload={"text": msg_text}
            )
            
            asyncio.run_coroutine_threadsafe(
                self.network.send(chat_msg),
                self.loop
            )
            self.gui.append_log(f"TU: {msg_text}")

    def handle_disconnection(self, reason):
        self.root.after(0, lambda: messagebox.showwarning("Disconnesso", f"Persa connessione: {reason}"))
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
