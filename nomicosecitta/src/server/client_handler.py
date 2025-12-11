import socket
import threading
import sys
import os

from src.common.constants import BUFFER_SIZE, ENCODING

sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

class ClientHandler(threading.Thread):
    """
    Handles TCP connection with a single client in a separate thread.
    
    Attributes:
        conn: Socket connection with the client.
        addr: Tuple (ip, port) of the client.
        server: Reference to the GameServer.
        username: Player's username (set after JOIN).
        p2p_port: Client's P2P listening port (for peer discovery).
    """

    def __init__(self, conn, addr, server):
        super().__init__(daemon = True)
        self.conn = conn
        self.addr = addr
        self.server = server
        self.running = True

        # Player info (it will be popolated after CMD_JOIN)
        self.username = None
        self.p2p_port = None

    def run(self):
        """
        Main loop to handle client communication.
        """

        print(f"[NEW CONNECTION] {self.addr} connected.")
        try:
            while self.running:
                try: 
                    data = self.conn.recv(BUFFER_SIZE)
                    if not data:
                        break

                    msg = data.decode(ENCODING)
                    print(f"[{self.addr}] Received: {msg}")

                    # At the moment echo, in the future JSON commands will be parsed here
                    self.send(f"Server Echo: {msg}")

                except ConnectionResetError:
                    print(f"[ERROR] Connection reset by {self.addr}")
                    break
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"[ERROR] Error handling {self.addr}: {e}")
                    break
        finally:
            self.close_connection()

    def send(self, msg): 
        """
        Sends a string to the client (encoded in bytes).
        Args:
            msg: String message to send
        """

        try:
            self.conn.sendall(msg.encode('utf-8'))
        except Exception as e:
            print(f"[ERROR] Sending to {self.addr}: {e}")

    def close_connection(self):
        """
        Closes resources and deregisteres from the server.
        """

        if self.running:
            self.running = False
            try:
                self.conn.close()
            except:
                pass
            print(f"[DISCONNECTED] {self.addr} disconnected.")
            self.server.remove_client(self)