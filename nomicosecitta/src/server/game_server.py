import asyncio

from src.common.constants import DEFAULT_SERVER_HOST, DEFAULT_SERVER_PORT
from src.server.client_handler import ClientHandler

class GameServer:
    """
    Main TCP server for Nomi, Cose, Città game.

    Manages client connections and provides broadcast functionality.
    """

    def __init__(self, host = DEFAULT_SERVER_HOST, port = DEFAULT_SERVER_PORT):
        self.host = host
        self.port = port
        self.server = None
        self.clients = [] # list of ClientHandler
        self.running = False

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
        """
        Called for each new client connection.
        
        Args:
            reader: AsyncIO StreamReader
            writer: AsyncIO StreamWriter
        """
        handler = ClientHandler(reader, writer, self)
        self.clients.append(handler)
        print(f"[ACTIVE CONNECTIONS] {len(self.clients)}")

        await handler.handle()

    def remove_client(self, handler):
        """ 
        Remove a client from the active list.
        
        Args:
            handler: ClientHandler instance to remove
        """
        if handler in self.clients:
            self.clients.remove(handler)
            print(f"[MANAGEMENT] Client removed. Remaining: {len(self.clients)}")

    async def broadcast(self, msg, exclude = None):
        """
        Send a message to all connected clients.
        
        Args:
            msg: String message to broadcast
            exclude: ClientHandler instance to exclude from broadcast
        """
        for client in self.clients:
            if client != exclude:
                client.send(msg)

    def get_client_by_username(self, username):
        """
        Find a client by username.
        
        Args:
            username: Username string to search for
        Returns:
            ClientHandler instance or None if not found
        """
        for client in self.clients:
            if client.username == username:
                return client
        return None
    
    def get_active_count(self):
        """
        Returns the number of active connected clients.
        """
        return len(self.clients)
        
    def get_active_usernames(self):
        """
        Returns set of currently connected usernames.
        """
        return {client.username for client in self.clients if client.username}
        
    def is_username_taken(self, username):
        """
        Check is a username is already in use.
        
        Args:
            username: Username string to check
        Returns:
            bool: True if taken, False otherwise
        """
        return username in self.get_active_usernames()
    
    def get_peer_map(self):
        """
        Returns dict mapping username -> p2p_address.
        """
        return {
            client.username: client.p2p_address
            for client in self.clients
            if client.username and client.p2p_address
        }

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