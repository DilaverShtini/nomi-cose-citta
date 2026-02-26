import asyncio

from src.common.constants import DEFAULT_SERVER_HOST, DEFAULT_SERVER_PORT, GAME_MODE_CLASSIC, DEFAULT_ROUND_TIME
from src.common.message import Message
from src.server.client_handler import ClientHandler
from src.server.game_session import GameSession

class GameServer:
    """
    Main TCP server for Nomi, Cose, Città game.

    Manages client connections and provides broadcast functionality.
    """

    def __init__(self, host = DEFAULT_SERVER_HOST, port = DEFAULT_SERVER_PORT):
        self.host = host
        self.port = port
        self.server = None
        self.clients = []
        self.running = False
        self.admin_username = None
        self.session = GameSession(self)
        self.lobby_settings = {
            "mode": GAME_MODE_CLASSIC,
            "num_extra_categories": 2,
            "round_time": DEFAULT_ROUND_TIME,
        }
        self.category_votes: dict[str, list] = {}

    def update_lobby_settings(self, settings: dict):
        for key in ("mode", "num_extra_categories", "round_time"):
            if key in settings:
                self.lobby_settings[key] = settings[key]

    def set_category_votes(self, username: str, categories: list):
        self.category_votes[username] = list(categories)

    def get_aggregated_categories(self, num_extra: int) -> list:
        vote_count: dict[str, int] = {}
        for cats in self.category_votes.values():
            for cat in cats:
                vote_count[cat] = vote_count.get(cat, 0) + 1

        sorted_cats = sorted(
            vote_count.keys(),
            key=lambda c: (-vote_count[c], c)
        )
        return sorted_cats[:num_extra]
    
    def reset_category_votes(self):
        self.category_votes.clear()

    async def start(self):
        """ 
        Start the TCP server and accept client connections.
        """

        print(f"[STARTING] Server starting on {self.host}:{self.port}...")

        self.server = await asyncio.start_server(
            self._handle_connection,
            self.host,
            self.port
        )
        self.running = True

        print(f"[LISTENING] Server is listening...")

        async with self.server:
            await self.server.serve_forever()

    async def _handle_connection(self, reader, writer):
        handler = ClientHandler(reader, writer, self)
        self.clients.append(handler)
        print(f"[ACTIVE CONNECTIONS] {len(self.clients)}")
        await handler.handle()

    def remove_client(self, handler):
        """ 
        Remove a client from the active list.
        """
        was_admin = (handler.username is not None and
                     handler.username == self.admin_username)

        if handler in self.clients:
            self.clients.remove(handler)
            print(f"[MANAGEMENT] Client removed. Remaining: {len(self.clients)}")
            if handler.username and handler.username in self.category_votes:
                del self.category_votes[handler.username]

        if was_admin:
            self._elect_new_admin()

    def get_admin(self):
        return self.admin_username

    def set_admin(self, username):
        if self.admin_username is None:
            self.admin_username = username

    def _elect_new_admin(self):
        """
        Elect a new admin using FIFO policy
        """
        for client in self.clients:
            if client.username:
                self.admin_username = client.username
                print(f"[ADMIN] New admin elected: {self.admin_username}")
                return
        self.admin_username = None
        print("[ADMIN] No players remaining, admin slot is vacant.")

    def get_client_by_username(self, username):
        for client in self.clients:
            if client.username == username:
                return client
        return None

    def get_active_count(self):
        return len(self.clients)

    def get_active_usernames(self):
        return {client.username for client in self.clients if client.username}

    def is_username_taken(self, username):
        return username in self.get_active_usernames()

    def get_peer_map(self):
        return {
            client.username: client.p2p_address
            for client in self.clients
            if client.username and client.p2p_address
        }

    async def broadcast(self, msg: Message, exclude = None):
        """
        Send a message to all connected clients.
        """
        msg_bytes = msg.to_bytes()
        tasks = []
        for client in self.clients:
            if client != exclude:
                tasks.append(asyncio.create_task(client.send(msg_bytes)))
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def stop(self):
        """
        Closes the main socket and all client connections.
        """
        self.running = False

        for client in list(self.clients):
            await client.close_connection()
        self.clients.clear()

        if self.server:
            self.server.close()
            await self.server.wait_closed()

        print("[SHUTDOWN] Server has been stopped.")