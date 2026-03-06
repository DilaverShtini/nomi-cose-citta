import json
import os
import time
from src.common.constants import SHARED_DATA_PATH

class StateManager:
    """
    Handle the saving and loading of the game state to/from a JSON file.
    """
    def __init__(self, filename="state.json"):
        self.filepath = os.path.join(SHARED_DATA_PATH, filename)
        os.makedirs(SHARED_DATA_PATH, exist_ok=True)

    def save_state(self, server):
        """
        Extracts the relevant state from the GameServer and saves it to a JSON file.
        """
        session = server.session
        now = time.time()
        round_time_passed = now - session.round_start_time if session.round_start_time > 0 else 0
        voting_start = getattr(session, 'voting_start_time', 0)
        voting_time_passed = now - voting_start if (voting_start > 0 and session.state and session.state.name == "VOTING") else 0

        state_data = {
            "server": {
                "admin": server.get_admin(),
                "players": list(server._expected_players) if session.state.name != "LOBBY" else list(server.get_active_usernames()),
                "lobby_settings": server.lobby_settings,
                "category_votes": server.category_votes,
            },
            "session": {
                "state":  session.state.name if session.state else "LOBBY",
                "round_number": session.current_round_number,
                "scores": session.scores,
                "old_letters": list(session.old_letters),
                "current_settings": session.current_settings,
                "round_time": session.round_time,
                "round_time_passed": round_time_passed,
                "current_voting_duration": getattr(session, 'current_voting_duration', 60),
                "voting_time_passed": voting_time_passed,
                "current_round": {
                    "letter": session.current_round.letter if session.current_round else None,
                    "categories": session.current_round.categories if session.current_round else [],
                } if session.current_round else None,
                "received_answers": session.received_answers,
                "received_votes": session.received_votes,
                "round_data": session.round_data,
                "words_to_vote": session.words_to_vote
            }
        }

        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=4, ensure_ascii=False)
            print(f"[STATE MANAGER] Stato salvato con successo in {self.filepath}")
        except Exception as e:
            print(f"[STATE MANAGER] Errore durante il salvataggio: {e}")

    def load_state(self):
        """
        Read the state from the JSON file and return it as a dictionary.
        """
        if not os.path.exists(self.filepath):
            return None
            
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[STATE MANAGER] Errore durante la lettura: {e}")
            return None
