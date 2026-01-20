import asyncio

from src.common.constants import BUFFER_SIZE, ENCODING, DEFAULT_SERVER_HOST, DEFAULT_SERVER_PORT
from src.common.message import Message

class NetworkHandler:
    """
    Handles TCP conncetion with the game server.

    Manages connecton, sending messages, and receiving message
    in a background task.

    Attributes:
        host: Server host address.
        port: Server port.
        reader: AsyncIO StreamReader.
        writer: AsyncIO StreamWriter.
        running: Flag to control the receive loop.
        on_message: Callback function called when a message is received.
        on_disconnect: Callback function called on disconnection.
    """

    def __init__(self, host=DEFAULT_SERVER_HOST, port=DEFAULT_SERVER_PORT):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None
        self.running = False
        self.receive_task = None

        # Callbacks
        self.on_message = None  # called when a message is received: on_message(data: str)
        self.on_disconnect = None  # called on disconnection: on_disconnect(reason: str)

    async def connect(self):
        """
        Connect to the game server.
        
        Returns:
            bool: True if connection is successful, False otherwise.
        """

        if self.running:
            print("[NetworkHandler] Already connected.")
            return True
        
        try:
            self.reader, self.writer = await asyncio.open_connection(
                self.host, 
                self.port
            )
            self.running = True

            self.receive_task = asyncio.create_task(self._receive_loop())

            print(f"[NetworkHandler] Connected to server at {self.host}:{self.port}")
            return True
        
        except ConnectionRefusedError:
            print(f"[NetworkHandler] Connection refused by {self.host}:{self.port}")
            return False
        except Exception as e:
            print(f"[NetworkHandler] Connection error: {e}")
            return False
        
    async def disconnect(self):
        """
        Disconnect from the game server.
        """
        if not self.running:
            return
        
        self.running = False

        if self.receive_task:
            self.receive_task.cancel()
            try:
                await self.receive_task
            except asyncio.CancelledError:
                pass

        if self.writer:
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except:
                pass
            self.writer = None
            self.reader = None
        
        print("[NetworkHandler] Disconnected from server.")

    async def send(self, message : Message):
        """
        Send a message to the server.
        
        Args:
            message: a Message to send.
            
        Returns:
            bool: True if sent successfully, False otherwise.
        """
        if not self.running or not self.writer:
            print("[NetworkHandler] Not connected.")
            return False
        
        try:
            json_str = message.to_json()
            data = (json_str + "\n").encode(ENCODING)
            self.writer.write(data)
            await self.writer.drain()
            return True
        except Exception as e:
            print(f"[NetworkHandler] Send error: {e}")
            await self._handle_disconnect("Send error")
            return False
        
    async def _receive_loop(self):
        """
        Background task to receive messages from the server.
        """
        while self.running:
            try:
                data = await self.reader.readline()
                if not data:
                    await self._handle_disconnect("Server closed connection")
                    break
                json_msg = data.decode(ENCODING).strip()
                if not json_msg:
                    continue
                try:
                    message = Message.from_json(json_msg)
                    if self.on_message:
                        self.on_message(message)
                    else:
                        print(f"[NetworkHandler] Received: {message.type}")

                except ValueError as e:
                    print(f"[NetworkHandler] JSON error: {e}")
            
            except ConnectionResetError:
                await self._handle_disconnect("Connection reset by server")
                break
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self.running:
                    print(f"[NetworkHandler] Receive error: {e}")
                    await self._handle_disconnect(str(e))
                break

    async def _handle_disconnect(self, reason):
        """
        Handle disconnection from the server.
        
        Args:
            reason: Reason for disconnection.
        """
        was_running = self.running
        self.running = False

        if self.writer:
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except:
                pass
            self.writer = None
            self.reader = None

        if was_running and self.on_disconnect:
            self.on_disconnect(reason)

    def is_connected(self):
        """
        Check if currently connected to the server.
        
        Returns:
            bool: True if connected, False otherwise.
        """
        return self.running and self.writer is not None
    
    @property
    def server_address(self):
        """
        Returns server address as string.
        
        Returns:
            str: Server address in "host:port" format.
        """
        return f"{self.host}:{self.port}"