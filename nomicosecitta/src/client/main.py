import sys
import os
import asyncio
import threading
import tkinter as tk
from tkinter import messagebox
from src.common.message import Message, MessageType

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.append(root_dir)

from src.client.network_handler import NetworkHandler
from src.client.gui import ClientGUI
from src.common.constants import DEFAULT_SERVER_PORT

class ClientController:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.network = None
        self.username = ""

        self.root = tk.Tk()
        self.gui = ClientGUI(self.root, self.connect_to_server, self.send_message)

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
            await self.network.send(join_msg.to_json()) 
        else:
            self.root.after(0, lambda: messagebox.showerror("Errore", "Impossibile connettersi al Server"))

    def handle_incoming_message(self, msg_obj):        
        if msg_obj.type == MessageType.EVT_LOBBY_UPDATE:
            self.root.after(0, self.gui.show_lobby) 

            players = msg_obj.payload.get("players", [])
            self.root.after(0, lambda: self.gui.update_player_list(players))

        elif msg_obj.type == MessageType.ERROR:
            err = msg_obj.payload.get("error", "Errore generico")
            self.root.after(0, lambda: messagebox.showerror("Errore di Login", err))

            asyncio.run_coroutine_threadsafe(self.network.disconnect(), self.loop)

        elif msg_obj.type == MessageType.P2P_CHAT:
             chat_text = f"{msg_obj.sender}: {msg_obj.payload.get('text', '')}"
             self.root.after(0, lambda: self.gui.append_log(chat_text))

        else:
            text = f"[{msg_obj.sender}] {msg_obj.type}"
            self.root.after(0, lambda: self.gui.append_log(text))

    def send_message(self, msg_text):
        if self.network and self.network.is_connected():
            chat_msg = Message(
                type=MessageType.P2P_CHAT,
                sender=self.username,
                payload={"text": msg_text}
            )
            
            asyncio.run_coroutine_threadsafe(
                self.network.send(chat_msg.to_json()),
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
