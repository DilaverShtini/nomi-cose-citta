from typing import Callable
from src.common.message import Message, MessageType

class P2PBroadcaster:
    def __init__(self, get_network: Callable, get_peer_map: Callable, get_username: Callable):
        self.get_network = get_network
        self.get_peer_map = get_peer_map
        self.get_username = get_username

    async def broadcast_vote(self, target_user: str, category: str, is_valid: bool):
        network = self.get_network()
        if not network:
            return
            
        username = self.get_username()
        vote_msg = Message(
            type=MessageType.MSG_VOTE,
            sender=username,
            payload={"target": target_user, "category": category, "valid": is_valid},
        )
        
        for peer_name, peer_address in self.get_peer_map().items():
            if peer_name != username:
                await network.send_p2p(peer_address, vote_msg)

    async def broadcast_chat(self, msg_text: str):
        network = self.get_network()
        if not network:
            return
            
        username = self.get_username()
        chat_msg = Message(
            type=MessageType.MSG_CHAT,
            sender=username,
            payload={"text": msg_text},
        )
        
        for peer_name, peer_address in self.get_peer_map().items():
            if peer_name != username:
                await network.send_p2p(peer_address, chat_msg)