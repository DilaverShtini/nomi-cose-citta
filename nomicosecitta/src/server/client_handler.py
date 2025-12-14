import asyncio
import sys
import os

from src.common.constants import BUFFER_SIZE, ENCODING
from src.common.message import Message, MessageType

class ClientHandler:
    """
    Handles TCP connection with a single client.
    
    Attributes:
        reader: AsyncIO StreamReader.
        writer: AsyncIO StreamWriter.
        addr: Tuple (ip, port) of the client.
        server: Reference to the GameServer.
        username: Player's username (set after JOIN).
        p2p_port: Client's P2P listening port (for peer discovery).
    """

    def __init__(self, reader, writer, server):
        self.reader = reader
        self.writer = writer
        self.server = server
        self.addr = writer.get_extra_info('peername')
        self.running = True

        # Player info (it will be popolated after CMD_JOIN)
        self.username = None
        self.p2p_port = None

    async def handle(self):
        """
        Main loop to handle client communication.
        """

        print(f"[NEW CONNECTION] {self.addr} connected.")
        try:
            while self.running:
                try: 
                    data = await self.reader.read(BUFFER_SIZE)
                    if not data:
                        break

                    msg_obj = Message.from_bytes(data)
                    if msg_obj.type == MessageType.CMD_JOIN:
                        await self._handle_join(msg_obj.payload)

                except ValueError as e:
                    print(f"[ERROR] Messaggio invalido da {self.addr}: {e}")
        except Exception as e:
            print(f"[ERROR] Handler {self.addr}: {e}")
        finally:
            await self.close_connection()

    async def _handle_join(self, payload):
        username = payload.get("username", "").strip()

        if not username or self.server.is_username_taken(username):
            err_msg = Message(MessageType.ERROR, "SERVER", {"error": "Nome non valido o in uso"})
            await self.send(err_msg.to_bytes())
            return

        self.username = username
        print(f"[JOIN] {self.addr} -> {username}")

        active_users = list(self.server.get_active_usernames())

        update_msg = Message(
            type=MessageType.EVT_LOBBY_UPDATE,
            sender="SERVER",
            payload={"players": active_users}
        )

        await self.server.broadcast(update_msg.to_bytes())

    async def send(self, data):
        if self.running:
            self.writer.write(data)
            await self.writer.drain()

    async def close_connection(self):
        """
        Closes resources and deregisteres from the server.
        """

        if not self.running:
            return
        
        self.running = False
        self.server.remove_client(self)
        try:
            self.writer.close()
            await self.writer.wait_closed()
        except:
            pass
        print(f"[DISCONNECTED] {self.addr} disconnected.")
