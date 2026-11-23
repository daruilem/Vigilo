"""Small in-memory sliding-window rate limiter, one window per client IP.

Good enough for a single API process. Several processes would need a shared store
(for example Redis), which comes with the job queue.
"""

from __future__ import annotations

import time
from collections import deque
from collections.abc import Callable


class RateLimiter:
    def __init__(
        self,
        max_events: int,
        window_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.max_events = max_events
        self.window = window_seconds
        self._clock = clock
        self._events: dict[str, deque[float]] = {}

    def allow(self, key: str) -> bool:
        now = self._clock()
        events = self._events.setdefault(key, deque())
        while events and now - events[0] >= self.window:
            events.popleft()
        if len(events) >= self.max_events:
            return False
        events.append(now)
        return True

    def reset(self) -> None:
        self._events.clear()
