import asyncio
import json
import time
import os

from src.common.constants import HEARTBEAT_FILE, HEARTBEAT_INTERVAL, HEARTBEAT_TIMEOUT

class ReplicationManager:
    def __init__(self, server_factory):
        self.server_factory = server_factory
        self.is_primary = False
        self._running = False
        self._server_task = None

    async def start(self):
        self._running = True
        os.makedirs(os.path.dirname(HEARTBEAT_FILE), exist_ok=True)
        await self._auto_assign_role()

    async def stop(self):
        """Stop the replication manager and the server if running."""
        self._running = False
        if self._server_task and not self._server_task.done():
            self._server_task.cancel()
            try:
                await self._server_task
            except asyncio.CancelledError:
                pass
        print("[REPLICATION] Manager stopped.")

    async def _auto_assign_role(self):
        """Decide whether to start as Primary or Backup based on heartbeat presence."""
        if self._is_primary_alive():
            print("[REPLICATION] Active Primary detected. Starting as Backup...")
            await self._run_as_backup()
        else:
            print("[REPLICATION] No active Primary detected. Starting as Primary...")
            await self._become_primary()

    def _is_primary_alive(self):
        """Read the heartbeat file to check if the Primary is alive."""
        if not os.path.exists(HEARTBEAT_FILE):
            return False
            
        try:
            with open(HEARTBEAT_FILE, "r") as f:
                data = json.load(f)
                last_beat = data.get("timestamp", 0)
                return (time.time() - last_beat) < HEARTBEAT_TIMEOUT
        except (json.JSONDecodeError, IOError):
            return False

    async def _become_primary(self):
        """Assume the Primary role and start the game server."""
        self.is_primary = True
        print("[REPLICATION] Assuming primary role. Starting game server...")
        asyncio.create_task(self._heartbeat_loop())
        self._server_task = asyncio.create_task(self.server_factory())
        await self._server_task

    async def _run_as_backup(self):
        """Assume the Backup role and monitor the Primary's heartbeat."""
        self.is_primary = False
        print("[REPLICATION] Running as backup. Monitoring primary heartbeat...")
        
        while self._running:
            if not self._is_primary_alive():
                print("\n[REPLICATION] Primary heartbeat lost. Promoting to Primary...")
                await self._become_primary()
                break
            await asyncio.sleep(HEARTBEAT_INTERVAL)

    async def _heartbeat_loop(self):
        """Update the heartbeat file at regular intervals to signal that the Primary is alive."""
        while self._running and self.is_primary:
            data = {
                "timestamp": time.time(),
                "pid": os.getpid()
            }
            try:
                with open(HEARTBEAT_FILE, "w") as f:
                    json.dump(data, f)
            except IOError as e:
                print(f"[REPLICATION] Error writing heartbeat: {e}")
            await asyncio.sleep(HEARTBEAT_INTERVAL)