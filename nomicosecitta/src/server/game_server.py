import socket
import threading

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
        self.server_socket = None
        self.clients = [] # list of ClientHandler
        self.lock = threading.Lock() # thread-safe access to clients list
        self.running = False

    def start(self):
        """ 
        Start the TCP server and accept client connections.
        """

        print(f"[STARTING] Server starting on {self.host}:{self.port}...")

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            print(f"[LISTENING] Server is listening...")

            while self.running:
                try:
                    self.server_socket.settimeout(1.0) # Allow periodic checks of self.running
                    conn, addr = self.server_socket.accept()
                    
                    handler = ClientHandler(conn, addr, self)
                    with self.lock:
                        self.clients.append(handler)
                    handler.start()

                    print(f"[ACTIVE CONNECTIONS] {len(self.clients)}")
                    
                except socket.timeout:
                    continue
                except OSError as e:
                    if self.running:
                        print(f"[ERROR] Accept failed: {e}")
                    break
        
        except KeyboardInterrupt:
            print("\n[SHUTDOWN] Server stopping by user request...")
        except Exception as e:
            print(f"[CRITICAL ERROR] Server loop failed: {e}")
        finally:
            self.stop()

    def remove_client(self, handler):
        """ 
        Remove a client from the active list.
        
        Args:
            handler: ClientHandler instance to remove
        """
        with self.lock:
            if handler in self.clients:
                self.clients.remove(handler)
                print(f"[MANAGEMENT] Client removed. Remaining: {len(self.clients)}")

    def broadcast(self, msg, exclude = None):
        """
        Send a message to all connected clients.
        
        Args:
            msg: String message to broadcast
            exclude: ClientHandler instance to exclude from broadcast
        """
        with self.lock:
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
        with self.lock:
            for client in self.clients:
                if client.username == username:
                    return client
        return None
    
    def get_active_count(self):
        """
        Returns the number of active connected clients.
        """
        with self.lock:
            return len(self.clients)
        
    def get_active_usernames(self):
        """
        Returns set of currently connected usernames.
        """
        with self.lock:
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
        with self.lock:
            return {
                client.username: client.p2p_address
                for client in self.clients
                if client.username and client.p2p_address
            }

    def stop(self):
        """
        Closes the main socket and all client connections.
        """

        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        with self.lock:
            for client in list(self.clients):
                client.close_connection()
            self.clients.clear()

        print("[SHUTDOWN] Server has been stopped.")