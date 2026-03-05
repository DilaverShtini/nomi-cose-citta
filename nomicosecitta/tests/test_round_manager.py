import unittest
from unittest.mock import AsyncMock, patch
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

from src.server.round_manager import RoundManager
from src.common.constants import DEFAULT_ROUND_TIME

class TestRoundManager(unittest.IsolatedAsyncioTestCase):

    def test_generate_letter(self):
        used = set("ABCDEFGHILMNOPQRSTUVZ")
        rm = RoundManager({"mode": "classic"}, used_letters=used)

        self.assertNotIn(rm.letter, used)
        self.assertTrue(rm.letter.isalpha())
        self.assertTrue(rm.letter.isupper())

    def test_parse_categories_classic(self):
        rm = RoundManager({"mode": "classic"})
        self.assertEqual(rm.categories, ["Name", "Things", "Cities"])

    def test_parse_categories_classic_plus(self):
        rm = RoundManager({
            "mode": "classic_plus", 
            "selected_categories": ["Animals", "Colors"]
        })
        self.assertEqual(rm.categories, ["Name", "Things", "Cities", "Animals", "Colors"])

    @patch('src.server.round_manager.asyncio.sleep')
    async def test_start_timer_calls_callback(self, mock_sleep):
        rm = RoundManager({"round_time": 10})

        mock_callback = AsyncMock()

        await rm.start_timer(mock_callback)

        mock_sleep.assert_called_once_with(12.0)

        mock_callback.assert_called_once()
        self.assertFalse(rm.is_active)
