import asyncio
import sys
import os

from src.common.constants import BUFFER_SIZE, ENCODING

sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

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

                    msg = data.decode(ENCODING)
                    print(f"[{self.addr}] Received: {msg}")

                    # At the moment echo, in the future JSON commands will be parsed here
                    await self.send(f"Server Echo: {msg}")

                except ConnectionResetError:
                    print(f"[ERROR] Connection reset by {self.addr}")
                    break
                except Exception as e:
                    print(f"[ERROR] Error handling {self.addr}: {e}")
                    break
        finally:
            await self.close_connection()

    async def send(self, msg): 
        """
        Sends a string to the client (encoded in bytes).
        
        Args:
            msg: String message to send
        """

        if not self.running:
            return
        try:
            self.writer.write(msg.encode(ENCODING))
            await self.writer.drain()
        except Exception as e:
            print(f"[ERROR] Sending to {self.addr}: {e}")

    async def close_connection(self):
        """
        Closes resources and deregisteres from the server.
        """

        if not self.running:
            return
        
        self.running = False
        try:
            self.writer.close()
            await self.writer.wait_closed()
        except:
            pass
        print(f"[DISCONNECTED] {self.addr} disconnected.")
        self.server.remove_client(self)