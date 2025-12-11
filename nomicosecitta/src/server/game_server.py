import socket
import threading

from src.common.constants import DEFAULT_SERVER_HOST, DEFAULT_SERVER_PORT
from src.server.client_handler import ClientHandler

class GameServer:
    def __init__(self, host = DEFAULT_SERVER_HOST, port = DEFAULT_SERVER_PORT):
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = []
        self.lock = threading.Lock() # To manage concurrent access to the client list
        self.running = False

    # Start the TCP server
    def start(self):
        print(f"[STARTING] Server starting on {self.host}:{self.port}...")
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen()
            self.running = True
            print(f"[LISTENING] Server is listening...")

            while self.running:
                conn, addr = self.server_socket.accept()
                
                handler = ClientHandler(conn, addr, self)
                with self.lock:
                    self.clients.append(handler)
                handler.start()

                print(f"[ACTIVE CONNECTIONS] {len(self.clients)}")
        
        except KeyboardInterrupt:
            print("\n[SHUTDOWN] Server stopping by user request...")
        except Exception as e:
            print(f"[CRITICAL ERROR] Server loop failed: {e}")
        finally:
            self.stop()

    def remove_client(self, handler):
        with self.lock:
            if handler in self.clients:
                self.clients.remove(handler)
                print(f"[MANAGEMENT] Client removed. Remaining: {len(self.clients)}")

    def broadcast(self, msg, exclude = None):
        with self.lock:
            for client in self.clients:
                if client != exclude:
                    client.send(msg)

    # Closes the main socket and all clients.
    def stop(self):
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        with self.lock:
            for client in self.clients:
                client.close_connection()