import asyncio
import random
import string
from src.common.constants import DEFAULT_ROUND_TIME

class RoundManager:
    """
    Handle round logic: letter generation, category selection, and timer management.
    """
    def __init__(self, settings, used_letters=set()):
        self.settings = settings
        self.letter = self._generate_letter(used_letters)
        self.categories = self._parse_categories(settings)
        self.duration = settings.get("round_time", DEFAULT_ROUND_TIME)
        self.is_active = True
        self._timer_task = None

    def _generate_letter(self, used_letters):
        available = list(set(string.ascii_uppercase) - used_letters)
        if not available:
            return random.choice(string.ascii_uppercase)
        return random.choice(available)

    def _parse_categories(self, settings):
        mode = settings.get("mode", "classic")
        extra = settings.get("selected_categories", [])
        if mode == "classic": return ["Name", "Things", "Cities"]
        elif mode == "classic_plus": return ["Name", "Things", "Cities"] + extra
        return extra

    async def start_timer(self, callback_on_end):
        """
        Wait for the round duration plus a grace period, then call the provided callback if still active.
        """
        grace_period = 2.0
        try:
            await asyncio.sleep(self.duration + grace_period)
            
            if self.is_active:
                self.is_active = False
                await callback_on_end()
                
        except asyncio.CancelledError:
            self.is_active = False
