import asyncio
import os
import socket

from src.common.constants import (
    DEFAULT_SERVER_HOST, DEFAULT_SERVER_PORT,
    GAME_MODE_CLASSIC, DEFAULT_ROUND_TIME
)
from src.common.message import Message
from src.server.client_handler import ClientHandler
from src.server.session.game_session import GameSession
from src.server.state_manager import StateManager

class GameServer:
    """
    Main TCP server for Nomi, Cose, Città game.

    Manages client connections and provides broadcast functionality.
    """

    def __init__(self, host=DEFAULT_SERVER_HOST, port=DEFAULT_SERVER_PORT):
        self.host   = host
        self.port   = port
        self.server = None

        self.clients:        list[ClientHandler] = []
        self.running:        bool  = False
        self.is_shutting_down: bool = False
        self.admin_username: str | None = None

        self.session        = GameSession(self)
        self.lobby_settings = {
            "mode":                 GAME_MODE_CLASSIC,
            "num_extra_categories": 2,
            "round_time":           DEFAULT_ROUND_TIME,
        }
        self.state_manager     = StateManager()
        self._expected_players: set[str] = set()
        self.category_votes:    dict[str, list] = {}

    async def start(self):
        print(f"[SERVER] Starting on {self.host}:{self.port}…")
        self.load_initial_state()
        self.server  = await asyncio.start_server(
            self._handle_connection, self.host, self.port
        )
        self.running = True
        asyncio.create_task(self._udp_broadcaster())
        print("[SERVER] Listening…")

        try:
            async with self.server:
                await self.server.serve_forever()
        except BaseException:
            self.is_shutting_down = True
            raise

    async def stop(self):
        self.running         = False
        self.is_shutting_down = True

        for client in list(self.clients):
            await client.close_connection()
        self.clients.clear()

        if self.server:
            self.server.close()
            await self.server.wait_closed()

        print("[SERVER] Stopped.")

    async def _handle_connection(self, reader, writer):
        handler = ClientHandler(reader, writer, self)
        self.clients.append(handler)
        print(f"[SERVER] Active connections: {len(self.clients)}")
        await handler.handle()

    def remove_client(self, handler: ClientHandler):
        was_admin = (
            handler.username is not None
            and handler.username == self.admin_username
        )
        if handler in self.clients:
            self.clients.remove(handler)
            print(f"[SERVER] Client removed. Remaining: {len(self.clients)}")
            if handler.username and handler.username in self.category_votes:
                del self.category_votes[handler.username]
        if was_admin:
            self._elect_new_admin()

    def get_client_by_username(self, username: str) -> ClientHandler | None:
        return next((c for c in self.clients if c.username == username), None)

    def get_active_count(self) -> int:
        return len(self.clients)

    def get_active_usernames(self) -> set[str]:
        return {c.username for c in self.clients if c.username}

    def is_username_taken(self, username: str) -> bool:
        return username in self.get_active_usernames()

    def get_peer_map(self) -> dict[str, str]:
        return {
            c.username: c.p2p_address
            for c in self.clients
            if c.username and c.p2p_address
        }

    async def broadcast(self, msg: Message, exclude: ClientHandler | None = None):
        msg_bytes = msg.to_bytes()
        tasks = [
            asyncio.create_task(client.send(msg_bytes))
            for client in self.clients
            if client != exclude
        ]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def get_admin(self) -> str | None:
        return self.admin_username

    def set_admin(self, username: str):
        if self.admin_username is None or self.admin_username not in self.get_active_usernames():
            self.admin_username = username
            print(f"[SERVER] Admin assigned/reassigned to: {self.admin_username}")

    def _elect_new_admin(self):
        for client in self.clients:
            if client.username:
                self.admin_username = client.username
                print(f"[SERVER] New admin elected: {self.admin_username}")
                return
        self.admin_username = None
        print("[SERVER] No players remaining — admin slot vacant.")
        self.save_state()

    # Lobby / category votes
    
    def update_lobby_settings(self, settings: dict):
        for key in ("mode", "num_extra_categories", "round_time"):
            if key in settings:
                self.lobby_settings[key] = settings[key]
        self.save_state()

    def set_category_votes(self, username: str, categories: list):
        self.category_votes[username] = list(categories)
        self.save_state()

    def get_aggregated_categories(self, num_extra: int) -> list[str]:
        vote_count: dict[str, int] = {}
        for cats in self.category_votes.values():
            for cat in cats:
                vote_count[cat] = vote_count.get(cat, 0) + 1
        sorted_cats = sorted(vote_count, key=lambda c: (-vote_count[c], c))
        return sorted_cats[:num_extra]

    def reset_category_votes(self):
        self.category_votes.clear()
        self.save_state()

    def save_state(self):
        if getattr(self, 'is_shutting_down', False):
            return
        if hasattr(self, 'state_manager'):
            self.state_manager.save_state(self)

    def load_initial_state(self):
        if not os.path.exists(self.state_manager.filepath):
            print("[SERVER] No save file found — clean start.")
            return

        state_data = self.state_manager.load_state()
        if state_data is None:
            print("[CRITICAL] state.json is corrupt! "
                  "Delete shared_data/state.json manually to reset.")
            import sys; sys.exit(1)

        print("[SERVER] Save file found — starting recovery…")
        server_data = state_data.get("server", {})

        self.lobby_settings    = server_data.get("lobby_settings", self.lobby_settings)
        self.category_votes    = server_data.get("category_votes", {})
        self.admin_username    = server_data.get("admin")
        self._expected_players = set(server_data.get("players", []))
        self.session.restore_from_state(state_data.get("session", {}))

    async def _udp_broadcaster(self):
        """Sends periodic UDP broadcasts to announce the server's presence on the local network."""
        loop    = asyncio.get_running_loop()
        sock    = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setblocking(False)
        message = f"NOMI_COSE_CITTA:{self.port}".encode('utf-8')
        print(f"[DISCOVERY] UDP broadcaster active on port {self.port}")

        while self.running:
            try:
                await loop.sock_sendto(sock, message, ('255.255.255.255', 50000))
            except Exception:
                pass
            await asyncio.sleep(2)
