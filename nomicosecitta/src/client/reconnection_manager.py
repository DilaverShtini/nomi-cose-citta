import asyncio
import json
import os
from typing import Callable, Optional, Tuple

class ReconnectionManager:
    """
    Manages automatica reconnection with circular server retry.
    """

    _DEFAULT_SERVERS = ["127.0.0.1:5000"]
    _DEFAULT_MAX_RETRIES = 3
    _DEFAULT_RETRY_DELAY = 2.0

    def __init__(self, config_path: Optional[str] = None):
        resolved = config_path or self._find_config()
        raw_cfg = self._load_json(resolved)

        raw_servers = raw_cfg.get("servers", self._DEFAULT_SERVERS)
        recon_cfg = raw_cfg.get("reconnection", {})

        self.servers: list[Tuple[str, int]] = [
            self._parse_address(addr) for addr in raw_servers
        ]
        self.max_retries: int = recon_cfg.get(
            "max_retries_per_server", self._DEFAULT_MAX_RETRIES)
        self.retry_delay: float = recon_cfg.get(
            "retry_delay_seconds", self._DEFAULT_RETRY_DELAY)
        
        self._index: int = 0
        self._active: bool = False

        print(f"[ReconnectionManager] Servers: {self.server_list}")
        print(f"[ReconnectionManager] Retries/server: {self.max_retries}, "
              f"delay: {self.retry_delay}s")
        
    def _find_config(self) -> str:
        here = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            os.path.join(here, "..", "..", "config.json"),
            os.path.join(here, "..", "config.json"),
            os.path.join(here, "config.json"),
            "config.json",
        ]
        for path in candidates:
            norm = os.path.normpath(path)
            if os.path.isfile(norm):
                return norm
            
        return os.path.normpath(os.path.join(here, "..", "..", "config.json"))
    
    def _load_json(self, path: str) -> dict:
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
            print(f"[ReconnectionManager] Config loaded from '{path}'")
            return data
        except FileNotFoundError:
            print(f"[ReconnectionManager] config.json not found at '{path}'. "
                  "Using built-in defaults.")
            return {}
        except json.JSONDecodeError as exc:
            print(f"[ReconnectionManager] config.json parse error: {exc}. "
                  "Using built-in defaults.")
            return {}
        
    @staticmethod
    def _parse_address(addr: str) -> Tuple[str, int]:
        parts = str(addr).strip().split(":")
        host = parts[0] or "127.0.0.1"
        port = int(parts[1]) if len(parts) > 1 else 5000
        return (host, port)
    
    def get_initial_server(self) -> Tuple[str, int]:
        return self.servers[0]
    
    def get_current_server(self) -> Tuple[str, int]:
        return self.servers[self._index]
    
    def advance(self) -> Tuple[str, int]:
        """Rotate to the next erver (circular) and return it."""
        self._index = (self._index + 1) % len(self.servers)
        return self.servers[self._index]
    
    def reset_rotation(self) -> None:
        self._index = 0

    async def reconnect(
            self,
            network_factory: Callable,
            username: str,
            p2p_port: int,
            on_status: Optional[Callable[[str], None]] = None,
    ) -> Optional[object]:
        """
        Attempt reconnection in circular order until success or exhaustion.

        Creates  a fresh NetworkHandler for each attempt so that the failed socket state never leaks into the connection.
        """
        if self._active:
            print("[ReconnectionManager] Reconnect already in progress — ignoring.")
            return None
        
        self._active = True
        total_attempts = len(self.servers) * self.max_retries

        def _notify(msg: str):
            print(f"[ReconnectionManager] {msg}")
            if on_status:
                on_status(msg)

        try:
            for attempt in range(1, total_attempts + 1):
                host, port = self.servers[self._index]
                _notify(
                    f"Reconnecting [{attempt}/{total_attempts}] → {host}:{port} …"
                )

                handler = network_factory(host, port)
                connected = await handler.connect()

                if connected:
                    _notify(f"Reconnected successfully to {host}:{port}")
                    return handler
                
                _notify(f"✗ {host}:{port} unreachable.")
                self.advance()

                if attempt < total_attempts:
                    await asyncio.sleep(self.retry_delay)

            _notify("All reconnection attempts exhausted.")
            return None
        
        finally:
            self._active = False

    @property
    def is_active(self) -> bool: 
        return self._active
    
    @property
    def server_list(self) -> list[str]:
        return [f"{h}:{p}" for h, p in self.servers]