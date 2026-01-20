import sys
import os
import argparse
import asyncio

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(root_dir)

from src.server.game_server import GameServer
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
    parser.add_argument(
        "--role",
        type = str,
        choices = ["auto", "primary", "backup"],
        default = "auto",
        help = "Server role: auto (default), primary, or backup"
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
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Server stopping by user request...")
    finally:
        await server.stop()


async def run_with_replication(host, port, role):
    """
    Start server with Primary/Backup replication.

    Args:
        host: Server host address.
        port: Server port.
        role: 'auto', 'primary', or 'backup'

    To be implemented in Sprint 4:
    - 'auto': Use heartbeat lock to determine role
    - 'primary': Force primary role
    - 'backup': Force backup role (monitor and wait)
    """
    # TODO Sprint 4: Import and use replication module
    # from src.server.replication import ReplicationManager
    # replication = ReplicationManager(role)
    # replication.start(lambda: run_server(host, port))
    
    # For now, just run as standalone server
    print(f"[INFO] Role '{role}' requested - replication not yet implemented")
    print(f"[INFO] Running as standalone server...")
    await run_server(host, port)

def main():
    args = parse_args()

    print("=" * 50)
    print("  NOMI, COSE, CITTÀ - Game Server")
    print("=" * 50)
    print(f"  Host: {args.host}")
    print(f"  Port: {args.port}")
    print(f"  Role: {args.role}")
    print("=" * 50)
    
    if args.role == "auto":
        # Default: run without replication for now
        asyncio.run(run_server(args.host, args.port))
    else:
        # Primary/Backup mode requested
        asyncio.run(run_with_replication(args.host, args.port, args.role))

if __name__ == "__main__":
    main()