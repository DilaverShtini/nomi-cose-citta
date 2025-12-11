import socket
import threading

from src.common.constants import BUFFER_SIZE, ENCODING, DEFAULT_SERVER_HOST, DEFAULT_SERVER_PORT

class NetworkHandler:
    """
    Handles TCP conncetion with the game server.

    Manages connecton, sending messages, and receiving message
    in a background thread.

    Attributes:
        host: Server host address.
        port: Server port.
        socket: TCP socket connection.
        running: Flag to control the receive loop.
        on_message: Callback function called when a message is received.
        on_disconnect: Callback function called on disconnection.
    """

    def __init__(self, host = DEFAULT_SERVER_HOST, port = DEFAULT_SERVER_PORT):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        self.receive_thread = None

        # Callbacks
        self.on_message = None # called wehn a message is received: on_message(data: str)
        self.on_disconnect = None # called on disconnection: on_disconnect(reason: str)

    def connect(self):
        """
        Connect to the game server.
        
        Returns:
            bool: True if connection successful, False otherwise.
        """
        if self.running:
            print("[NetworkHandler] Already connected.")
            return True
        
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.running = True

            self.receive_thread = threading.Thread(target = self._receive_loop, daemon = True)
            self.receive_thread.start()

            print(f"[NetworkHandler] Connected to server at {self.host}:{self.port}.")
            return True
        
        except ConnectionRefusedError:
            print(f"[NetworkHandler] Connection refused by {self.host}:{self.port}")
            return False
        except Exception as e:
            print(f"[NetworkHandler] Connection error: {e}")
            return False

    def disconnect(self):
        """
        Disconnect from the game server.
        """
        if not self.running:
            return
        
        self.running = False

        if self.socket:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
            except:
                pass
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        print("[NetworkHandler] Disconnected from server.")

    def send(self, message):
        """
        Send a message to the server.
        
        Args:
            message: String message to send.
            
        Returns:
            bool: True if sent successfully, False otherwise.
        """
        if not self.running or not self.socket:
            print("[NetworkHandler] Not connected.")
            return False
        
        try:
            self.socket.sendall(message.encode(ENCODING))
            return True
        except Exception as e:
            print(f"[NetworkHandler] Send error: {e}")
            self._handle_disconnect("Send error")
            return False
        
    def _receive_loop(self):
        """
        Background thread loop to receive messages from the server.
        """
        while self.running:
            try:
                data = self.socket.recv(BUFFER_SIZE)
                if not data:
                    self._handle_disconnect("Server closed connection")
                    break
                
                message = data.decode(ENCODING)
                if self.on_message:
                    self.on_message(message)
                else:
                    print(f"[NetworkHandler] Received: {message}")
            
            except ConnectionResetError:
                self._handle_disconnect("Connection reset by server")
                break
            except OSError:
                if self.running:
                    self._handle_disconnect("Connection lost")
                break
            except Exception as e:
                if self.running:
                    print(f"[NetworkHandler] Receive error: {e}")
                    self._handle_disconnect(str(e))
                break

    def _handle_disconnect(self, reason):
        """
        Handle disconnection from the server.
        
        Args:
            reason: Reason for disconnection.
        """
        was_running = self.running
        self.running = False

        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None

        if was_running and self.on_disconnect:
            self.on_disconnect(reason)

    def is_connected(self):
        """
        Check if currently connected to the server.
        
        Returns:
            bool: True if connected, False otherwise.
        """
        return self.running and self.socket is not None
    
    @property
    def server_address(self):
        """
        Returns server address as string.
        
        Returns:
            str: Server address in "host:port" format.
        """
        return f"{self.host}:{self.port}"