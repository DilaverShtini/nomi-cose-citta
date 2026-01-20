"""
Base class for all application screens.
Provides lifecycle hooks and consistent interface.
"""
from abc import ABC, abstractmethod
import tkinter as tk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.client.gui.gui_manager import GUIManager


class BaseScreen(ABC):
    """
    Abstract base class for all application screens.
    
    Subclasses must implement:
    - _setup_ui(): Build the screen's UI components
    """

    def __init__(self, parent: tk.Widget, manager: 'GUIManager'):
        """
        Initialize the screen.
        
        Args:
            parent: Parent widget (usually root window).
            manager: Reference to the GUIManager for navigation and callbacks.
        """
        self.parent = parent
        self.manager = manager
        self.frame = tk.Frame(parent)
        self._is_active = False
        
        self._setup_ui()

    @abstractmethod
    def _setup_ui(self):
        """
        Setup the screen UI. Must be implemented by subclasses.
        
        This method is called once during initialization.
        Use it to create and layout all widgets.
        """
        pass

    def show(self):
        """Show this screen and trigger on_enter hook."""
        self.frame.pack(fill="both", expand=True)
        self._is_active = True
        self.on_enter()

    def hide(self):
        """Hide this screen and trigger on_exit hook."""
        self.on_exit()
        self.frame.pack_forget()
        self._is_active = False

    def on_enter(self):
        """
        Called when screen becomes visible.
        
        Override this method to perform actions when entering the screen,
        such as focusing on an input field or starting animations.
        """
        pass

    def on_exit(self):
        """
        Called when screen is about to be hidden.
        
        Override this method to perform cleanup actions,
        such as stopping timers or saving state.
        """
        pass

    @property
    def is_active(self) -> bool:
        """Check if this screen is currently visible."""
        return self._is_active