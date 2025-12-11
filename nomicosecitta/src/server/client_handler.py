import socket
import threading
import sys
import os

from src.common.constants import BUFFER_SIZE, ENCODING

sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

# Handles TCP connection with a single client in a separate thread.
class ClientHandler(threading.Thread):
    def __init__(self, conn, addr, server):
        super().__init__()
        self.conn = conn
        self.addr = addr
        self.server = server
        self.running = True

    def run(self):
        print(f"[NEW CONNECTION] {self.addr} connected.")
        try:
            while self.running:
                try: 
                    data = self.conn.recv(BUFFER_SIZE)
                    if not data:
                        break

                    print(f"[{self.addr}] Received: {data.decode(ENCODING)}")
                    self.send(f"Server Echo: {data.decode(ENCODING)}")

                except ConnectionResetError:
                    print(f"[ERROR] Connection reset by {self.addr}")
                    break
                except Exception as e:
                    print(f"[ERROR] Error handling {self.addr}: {e}")
                    break
        finally:
            self.close_connection()

    # Sends a string to the client (encoded in bytes).
    def send(self, msg): 
        try:
            self.conn.sendall(msg.encode('utf-8'))
        except Exception as e:
            print(f"[ERROR] Sending to {self.addr}: {e}")

    # Closes resources and deregisteres from the server.
    def close_connection(self):
        if self.running:
            self.running = False
            try:
                self.conn.close()
            except:
                pass
            print(f"[DISCONNECTED] {self.addr} disconnected.")
            self.server.remove_client(self)