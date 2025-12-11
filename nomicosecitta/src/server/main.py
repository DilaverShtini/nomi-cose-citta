import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(root_dir)

from src.server.game_server import GameServer
from src.common.constants import DEFAULT_SERVER_HOST, DEFAULT_SERVER_PORT

if __name__ == "__main__":
    # In Sprint 4, we'll add the "Primary vs. Backup" logic here.
    # For now (Sprint 1), we'll start the server directly.
    
    server = GameServer(DEFAULT_SERVER_HOST, DEFAULT_SERVER_PORT)
    server.start()