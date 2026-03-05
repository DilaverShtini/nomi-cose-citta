import asyncio
import sys
import os

from src.common.constants import BUFFER_SIZE, ENCODING
from src.common.message import Message, MessageType

# action_type values for CMD_LOBBY_ACTION
ACTION_SETTINGS   = "settings"
ACTION_CATEGORIES = "categories"


class ClientHandler:
    """
    Handles TCP connection with a single client.
    """

    def __init__(self, reader, writer, server):
        self.reader = reader
        self.writer = writer
        self.server = server
        self.addr = writer.get_extra_info('peername')
        self.running = True
        self.username = None
        self.p2p_address = None

    async def handle(self):
        """Main loop to handle client communication."""
        print(f"[NEW CONNECTION] {self.addr} connected.")
        try:
            while self.running:
                try:
                    data = await self.reader.read(BUFFER_SIZE)
                    if not data:
                        print(f"[DEBUG] {self.addr} closed the connection.")
                        break

                    msg_obj = Message.from_bytes(data)

                    if msg_obj.type == MessageType.CMD_JOIN:
                        await self._handle_join(msg_obj.payload)
                    elif msg_obj.type == MessageType.CMD_START_GAME:
                        await self._handle_start_game(msg_obj.payload)
                    elif msg_obj.type == MessageType.CMD_SUBMIT:
                        await self._handle_submit(msg_obj.payload)
                    elif msg_obj.type == MessageType.CMD_LOBBY_ACTION:
                        await self._handle_lobby_action(msg_obj.payload)

                except ValueError as e:
                    print(f"[ERROR] Invalid message from {self.addr}: {e}")

        except Exception as e:
            print(f"[ERROR] Handler {self.addr}: {e}")
        finally:
            await self.close_connection()

    async def _handle_submit(self, payload: dict):
        if not self.username:
            return

        if "words" in payload:
            words = payload.get("words", {})
            await self.server.session.receive_answers(self.username, words)

        elif "votes" in payload:
            votes = payload.get("votes", {})
            print(f"[SUBMIT_VOTES] Received from {self.username}: {votes}")
            await self.server.session.receive_votes(self.username, votes)

        else:
            print(f"[WARN] CMD_SUBMIT from {self.username} with unknown payload keys: "
                  f"{list(payload.keys())}")

    async def _handle_join(self, payload: dict):
        username = payload.get("username", "").strip()

        if not username or self.server.is_username_taken(username):
            err_msg = Message(
                MessageType.EVT_ERROR, "SERVER",
                {"error": "Username already taken or invalid"}
            )
            await self.send(err_msg.to_bytes())
            return
        
        self.username = username
        self.server.set_admin(username)

        p2p_port = payload.get("p2p_port")
        if p2p_port:
            client_ip = self.addr[0]
            self.p2p_address = f"{client_ip}:{p2p_port}"

        print(f"[JOIN] {self.addr} -> {username} (p2p={self.p2p_address})")
        await self._broadcast_lobby_update()

        if self.server.session.state.name != "LOBBY":
            await self.server.session.sync_reconnecting_client(self)

    async def _handle_start_game(self, settings: dict):
        if not self.username:
            return

        print(f"[START GAME] Request from {self.username} with settings: {settings}")
        success, info = await self.server.session.start_game(self.username, settings)

        if not success:
            await self.send(Message(
                MessageType.EVT_ERROR, "SERVER", {"error": info}
            ).to_bytes())

    async def _handle_lobby_action(self, payload: dict):
        action_type = payload.get("action_type")

        if action_type == ACTION_SETTINGS:
            if self.username != self.server.get_admin():
                print(f"[WARN] {self.username} tried to change settings but is not admin.")
                return
            self.server.update_lobby_settings(payload)
            print(f"[SETTINGS] Admin {self.username}: {self.server.lobby_settings}")
            await self._broadcast_lobby_update()

        elif action_type == ACTION_CATEGORIES:
            if not self.username:
                return
            categories = payload.get("categories", [])
            self.server.set_category_votes(self.username, categories)
            print(f"[VOTE CATS] {self.username}: {categories}")

        else:
            print(f"[WARN] Unknown CMD_LOBBY_ACTION action_type={action_type!r}")

    async def _broadcast_lobby_update(self):
        await self.server.broadcast(Message(
            type=MessageType.EVT_LOBBY_UPDATE,
            sender="SERVER",
            payload={
                "players": list(self.server.get_active_usernames()),
                "admin": self.server.get_admin(),
                "settings": self.server.lobby_settings,
            }
        ))

    async def send(self, data: bytes):
        if self.running:
            try:
                if not data.endswith(b'\n'):
                    data = data + b'\n'
                self.writer.write(data)
                await self.writer.drain()
            except Exception as e:
                print(f"[ERROR] Error sending to {self.addr}: {e}")

    async def close_connection(self):
        if not self.running:
            return

        self.running = False
        had_username = self.username is not None
        self.server.remove_client(self)

        try:
            self.writer.close()
            await self.writer.wait_closed()
        except Exception:
            pass

        print(f"[DISCONNECTED] {self.addr} disconnected.")

        if had_username:
            await self._broadcast_lobby_update()
            await self.server.session.handle_player_disconnection(self.username)