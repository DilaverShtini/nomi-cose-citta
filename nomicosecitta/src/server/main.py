import sys
import os
import argparse
import asyncio

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(root_dir)

from src.server.game_server import GameServer
from src.server.replication import ReplicationManager
from src.common.constants import DEFAULT_SERVER_HOST, DEFAULT_SERVER_PORT


def parse_args():
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(
        description="Nomi, Cose, Città - Game Server"
    )
    parser.add_argument(
        "--host",
        type = str,
        default = DEFAULT_SERVER_HOST,
        help = f"Server host (default: {DEFAULT_SERVER_HOST})"
    )
    parser.add_argument(
        "--port", "-p",
        type = int,
        default = DEFAULT_SERVER_PORT,
        help = f"Server port (default: {DEFAULT_SERVER_PORT})"
    )
    return parser.parse_args()

async def run_server(host, port):
    """
    Start the game server.
    
    Args:
        host: Server host address.
        port: Server port.
    """

    server = GameServer(host, port)
    try:
        await server.start()
    except BaseException as e:
        print(f"\n[SHUTDOWN/CRASH] Server stopped: {e}")
        server.is_shutting_down = True
    finally:
        server.is_shutting_down = True
        await server.stop()

async def run_with_replication(host, port):
    """
    Start server with Primary/Backup replication.
    """
    print(f"[INFO] Starting replication manager...")
    
    async def start_server():
        await run_server(host, port)
        
    replication = ReplicationManager(start_server)
    try:
        await replication.start()
    except asyncio.CancelledError:
        pass
    finally:
        await replication.stop()

def main():
    args = parse_args()

    print("=" * 50)
    print("  NOMI, COSE, CITTÀ - Game Server")
    print("=" * 50)
    print(f"  Host: {args.host}")
    print(f"  Port: {args.port}")
    print("=" * 50)

    asyncio.run(run_with_replication(args.host, args.port))

if __name__ == "__main__":
    main()