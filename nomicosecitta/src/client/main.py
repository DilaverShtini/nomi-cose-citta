import sys
import os
import asyncio
import threading
import tkinter as tk
from tkinter import messagebox

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
            self.root.after(0, self.gui.show_lobby)
            
            # 2. (TASK LOBBY) Aggiungiamo noi stessi alla lista graficamente
            # NOTA: Quando il server sarà pronto, questo arriverà via rete.
            # Per ora lo facciamo "finto" per far vedere che la GUI funziona.
            mock_list = [self.username] 
            self.root.after(0, lambda: self.gui.update_player_list(mock_list))
            
            self.root.after(0, lambda: self.gui.append_log(f"[SYSTEM] Benvenuto nella Lobby, {self.username}!"))
        else:
            self.root.after(0, lambda: messagebox.showerror("Errore", "Server non trovato"))

    def send_message(self, msg):
        if self.network and self.network.is_connected():
            asyncio.run_coroutine_threadsafe(self.network.send(msg), self.loop)
            self.gui.append_log(f"TU: {msg}")

    def handle_incoming_message(self, msg):
        self.root.after(0, lambda: self.gui.append_log(f"SERVER: {msg}"))

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
