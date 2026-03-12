"""
GUI Manager - Central coordinator for screen navigation and callbacks.

This is the main entry point for the GUI subsystem.
The controller interacts only with this class.
"""
import tkinter as tk
from enum import Enum, auto
from typing import Callable, Optional, Dict

from src.client.gui.screens import LoginScreen, LobbyScreen, GameScreen
from src.client.gui.screens.base_screen import BaseScreen
from src.client.gui import theme


class Screen(Enum):
    LOGIN = auto()
    LOBBY = auto()
    GAME = auto()


class GUIManager:
    """
    Central manager for the GUI subsystem.
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        self._configure_window()

        self.on_connect: Optional[Callable[[str, str], None]] = None
        self.on_send_message: Optional[Callable[[str], None]] = None
        self.on_start_game: Optional[Callable[[dict], None]] = None
        self.on_submit_answers: Optional[Callable[[dict], None]] = None
        self.on_vote_cast: Optional[Callable[[str, str, bool], None]] = None

        self.on_lobby_settings_changed: Optional[Callable[[dict], None]] = None
        self.on_category_vote_changed: Optional[Callable[[list], None]] = None

        self._screens: Dict[Screen, BaseScreen] = {}
        self._current_screen: Optional[Screen] = None

        self._init_screens()
        self.navigate_to(Screen.LOGIN)

    def _configure_window(self):
        self.root.title("Nomi Cose Città")
        self.root.geometry("900x550")
        self.root.minsize(850, 500)
        self.root.configure(bg=theme.BG_PAGE)

    def _init_screens(self):
        self._screens[Screen.LOGIN] = LoginScreen(self.root, self)
        self._screens[Screen.LOBBY] = LobbyScreen(self.root, self)
        self._screens[Screen.GAME] = GameScreen(self.root, self)

    # Navigation methods

    def navigate_to(self, screen: Screen):
        if self._current_screen is not None:
            self._screens[self._current_screen].hide()
        self._current_screen = screen
        self._screens[screen].show()

    def get_screen(self, screen: Screen) -> BaseScreen:
        return self._screens[screen]

    @property
    def current_screen(self) -> Optional[Screen]:
        return self._current_screen

    def show_login(self):
        self.navigate_to(Screen.LOGIN)

    def show_lobby(self):
        self.navigate_to(Screen.LOBBY)

    def show_game(self):
        self.navigate_to(Screen.GAME)

    def show_voting_phase(self, words_to_vote: dict, my_username: str, duration: int):
        self.navigate_to(Screen.GAME)
        self.game.build_voting_ui(words_to_vote, my_username, duration)

    # Screen properties

    @property
    def login(self) -> LoginScreen:
        return self._screens[Screen.LOGIN]

    @property
    def lobby(self) -> LobbyScreen:
        return self._screens[Screen.LOBBY]

    @property
    def game(self) -> GameScreen:
        return self._screens[Screen.GAME]

    # Lobby delegations

    def set_admin(self, is_admin: bool):
        self.lobby.set_admin(is_admin)

    def update_player_list(self, players: list, admin_username: str = None):
        self.lobby.update_player_list(players, admin_username)

    def append_log(self, text: str):
        self.game.append_log(text)

    def get_selected_extra_categories(self) -> list:
        return self.lobby.get_selected_categories()

    def get_game_settings(self) -> dict:
        return self.lobby.get_settings()

    def update_lobby_settings(self, mode: str, num_extra_categories: int, round_time: int = None):
        self.lobby.update_lobby_settings(mode, num_extra_categories, round_time)

    # Game delegations

    def update_game_letter(self, letter: str):
        self.game.update_letter(letter)

    def update_timer(self, seconds: int):
        self.game.update_timer(seconds)

    def update_categories(self, categories: list):
        self.game.update_categories(categories)

    def update_round_info(self, round_number: int):
        self.game.update_round_info(round_number)

    def update_game_status(self, status: str):
        self.game.update_status(status)

    def get_answers(self) -> dict:
        return self.game.get_answers()

    def clear_answers(self):
        self.game.clear_answers()

    def set_inputs_enabled(self, enabled: bool):
        self.game.set_inputs_enabled(enabled)

    def start_round(self, letter: str, categories: list, round_number: int, duration: int):
        self.game.start_round(letter, categories, round_number, duration)

    def update_peer_vote(self, target_user: str, category: str, voter: str, is_valid: bool):
        if self._current_screen == Screen.GAME:
            self.game.update_peer_vote(target_user, category, voter, is_valid)

    def end_round(self):
        self.game.end_round()

    def update_scoreboard(self, scores: dict, round_scores: dict = None):
        self.game.update_scoreboard(scores, round_scores)

    def pause_timers(self):
        if self._current_screen == Screen.GAME:
            self.game.pause_timers()

    @property
    def players_list(self):
        return self.lobby.player_list