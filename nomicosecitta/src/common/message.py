import json
import time
from enum import StrEnum, auto
from dataclasses import dataclass, field, asdict
from typing import Any, Optional

class MessageType(StrEnum):
    # client -> server
    CMD_JOIN = auto()
    CMD_SUBMIT= auto()

    # server -> client
    EVT_LOBBY_UPDATE = auto()
    EVT_PEER_MAP = auto()
    EVT_ROUND_START = auto()
    EVT_VOTING_START = auto()
    EVT_ROUND_END = auto()
    EVT_GAME_OVER = auto()
    ERROR = auto()

    # client <-> client
    P2P_CHAT = auto()
    P2P_VOTE = auto()

@dataclass
class Message:
    """
    Represents a packet exchanged in the network.
    """
    type: MessageType
    sender: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_json(self) -> str:
        """Serializes the object to a JSON string."""
        data = asdict(self)
        return json.dumps(data)

    def to_bytes(self) -> bytes:
        """Utility for sending directly via socket."""
        return self.to_json().encode('utf-8')

    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """Creates a Message object from a JSON string."""
        try:
            data = json.loads(json_str)
            msg_type = MessageType(data['type'])
            
            return cls(
                type=msg_type,
                sender=data['sender'],
                payload=data.get('payload', {}),
                timestamp=data.get('timestamp', time.time())
            )
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            raise ValueError(f"Invalid message format: {e}")

    @classmethod
    def from_bytes(cls, byte_data: bytes) -> 'Message':
        """Decodes bytes received from the socket."""
        return cls.from_json(byte_data.decode('utf-8'))