"""
Main GUI class for the Nomi CoseCitta client.
Orchestrates the different screens.
"""
from src.client.gui.screens.login_screen import LoginScreen
from src.client.gui.screens.lobby_screen import LobbyScreen
from src.client.gui.screens.game_screen import GameScreen

class ClientGUI:
    """
    Main GUI class that manages navigation between screens.
    
    Provides a unified interface for the client controller to interact
    with all GUI components. This class maintains backward compatibility
    with the original monolithic gui.py API.
    """
     
    def __init__(self, master, on_connect_callback, on_send_callback, on_start_game_callback=None):
        """
        Initialize the client GUI.
        
        Args:
            master: The root Tk window.
            on_connect_callback: Called when user connects. Signature: (ip, username)
            on_send_callback: Called when user sends chat message. Signature: (message)
            on_start_game_callback: Called when admin starts game. Signature: (config)
        """
        self.root = master
        self.root.title("Nomi Cose Città - Client")
        self.root.geometry("900x550")
        self.root.minsize(850, 500)

        # Create screens
        self.login_screen = LoginScreen(self.root, on_connect_callback)
        self.lobby_screen = LobbyScreen(self.root, on_send_callback, on_start_game_callback)
        self.game_screen = GameScreen(self.root)

        # Show initial screen
        self.show_login()

    # Screen navigation methods
    def show_login(self):
        """Show the login screen."""
        self.lobby_screen.hide()
        self.game_screen.hide()
        self.login_screen.show()

    def show_lobby(self):
        """Show the lobby screen."""
        self.login_screen.hide()
        self.game_screen.hide()
        self.lobby_screen.show()
    
    def show_game(self):
        """Show the game screen."""
        self.login_screen.hide()
        self.lobby_screen.hide()
        self.game_screen.show()

    # Lobby delegation methods
    def set_admin(self, is_admin):
        """Set whether this client is the admin."""
        self.lobby_screen.set_admin(is_admin)

    def update_player_list(self, players_list, admin_username=None):
        """Update the player list in the lobby."""
        self.lobby_screen.update_player_list(players_list, admin_username)

    def append_log(self, text):
        """Append text to the lobby chat log."""
        self.lobby_screen.append_log(text)

    def get_selected_extra_categories(self):
        """Get list of selected extra categories."""
        return self.lobby_screen.get_selected_extra_categories()

    def get_game_settings(self):
        """Get current game settings from lobby."""
        return self.lobby_screen.get_game_settings()
    
    # Game delegation methods
    def update_game_letter(self, letter):
        """Update the current letter display."""
        self.game_screen.update_letter(letter)

    def update_timer(self, seconds_remaining):
        """Update the timer display."""
        self.game_screen.update_timer(seconds_remaining)

    def update_categories(self, categories):
        """Update the game with new categories."""
        self.game_screen.update_categories(categories)

    def update_round_info(self, round_number):
        """Update the round number display."""
        self.game_screen.update_round_info(round_number)

    def update_game_status(self, status_text):
        """Update the game status bar text."""
        self.game_screen.update_status(status_text)

    def get_answers(self):
        """Get all current answers from the game input fields."""
        return self.game_screen.get_answers()
    
    def clear_answers(self):
        """Clear all game answer input fields."""
        self.game_screen.clear_answers()

    def set_inputs_enabled(self, enabled):
        """Enable or disable game input fields."""
        self.game_screen.set_inputs_enabled(enabled)

    def start_round(self, letter, categories, round_number):
        """Initialize and display a new round."""
        self.game_screen.start_round(letter, categories, round_number)
    
    def end_round(self):
        """Handle end of round."""
        self.game_screen.end_round()