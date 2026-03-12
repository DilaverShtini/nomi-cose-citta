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
        self._heartbeat_task = None

    async def start(self):
        self._running = True
        os.makedirs(os.path.dirname(HEARTBEAT_FILE), exist_ok=True)
        await self._auto_assign_role()

    async def stop(self):
        """Stop the replication manager and the server if running."""
        self._running = False
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            
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
            try:
                mtime = os.path.getmtime(HEARTBEAT_FILE)
                return (time.time() - mtime) < HEARTBEAT_TIMEOUT
            except OSError:
                return False

    async def _become_primary(self):
        """Assume the Primary role and start the game server."""
        self.is_primary = True
        print("[REPLICATION] Assuming primary role. Starting game server...")
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        try:
            self._server_task = asyncio.create_task(self.server_factory())
            await self._server_task
        except OSError as e:
            if e.errno in (98, 10048): # Address already in use
                print("\n[REPLICATION] Port already in use! Another Backup won the race.")
                print("[REPLICATION] Reverting to Backup...")
                self.is_primary = False
                if self._heartbeat_task:
                    self._heartbeat_task.cancel()
                await self._run_as_backup()
            else:
                raise

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
        temp_file = HEARTBEAT_FILE + ".tmp"
        while self._running and self.is_primary:
            data = {
                "timestamp": time.time(),
                "pid": os.getpid()
            }
            try:
                with open(temp_file, "w") as f:
                    json.dump(data, f)
                os.replace(temp_file, HEARTBEAT_FILE)
            except IOError as e:
                print(f"[REPLICATION] Error writing heartbeat: {e}")
            await asyncio.sleep(HEARTBEAT_INTERVAL)