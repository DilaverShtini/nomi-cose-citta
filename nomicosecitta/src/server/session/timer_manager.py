import asyncio
from typing import Callable, Coroutine, Optional


class TimerManager:
    """
    Owns the two asyncio Tasks used during a game session.
    """

    def __init__(self) -> None:
        self._round_task:  Optional[asyncio.Task] = None
        self._voting_task: Optional[asyncio.Task] = None

    #  Round timer

    def start_round_timer(self, coro: Coroutine) -> None:
        self.cancel_round_timer()
        self._round_task = asyncio.create_task(coro)

    def cancel_round_timer(self) -> None:
        if self._round_task and not self._round_task.done():
            self._round_task.cancel()
        self._round_task = None

    def is_round_timer_active(self) -> bool:
        return self._round_task is not None and not self._round_task.done()

    #  Voting timer

    def start_voting_timer(self, duration: int, on_timeout: Callable) -> None:
        self.cancel_voting_timer()
        self._voting_task = asyncio.create_task(
            self._run_voting_timeout(duration, on_timeout)
        )

    def cancel_voting_timer(self) -> None:
        if self._voting_task and not self._voting_task.done():
            self._voting_task.cancel()
        self._voting_task = None

    def is_voting_timer_active(self) -> bool:
        return self._voting_task is not None and not self._voting_task.done()

    #  Helpers

    def cancel_all(self) -> None:
        self.cancel_round_timer()
        self.cancel_voting_timer()

    #  Restore after crash or restart

    def restore(
        self,
        state_name:       str,
        round_remaining:  float,
        voting_remaining: float,
        round_callback:   Callable,
        voting_callback:  Callable,
    ) -> None:
        if state_name == "WAITING_INPUT":
            print(f"[TIMERS] Reset round timer: {round_remaining:.1f}s remaining.")

            async def _resume_round(t: float) -> None:
                await asyncio.sleep(t)
                await round_callback()

            self._round_task = asyncio.create_task(_resume_round(round_remaining))

        elif state_name == "VOTING":
            print(f"[TIMERS] Reset votes timer: {voting_remaining:.1f}s remaining.")

            async def _resume_voting(t: float) -> None:
                await asyncio.sleep(t)
                await voting_callback()

            self._voting_task = asyncio.create_task(_resume_voting(voting_remaining))

    @staticmethod
    async def _run_voting_timeout(duration: int, on_timeout: Callable) -> None:
        try:
            await asyncio.sleep(duration)
            await on_timeout()
        except asyncio.CancelledError:
            pass