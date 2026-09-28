"""Simple in-process rate limiter for the football-data.org free tier (10 req/min)."""

from __future__ import annotations

import threading
import time
from collections import deque


class RateLimiter:
    """Blocks callers so no more than `max_calls` happen in any `period_seconds` window."""

    def __init__(self, max_calls: int, period_seconds: float) -> None:
        self._max_calls = max_calls
        self._period_seconds = period_seconds
        self._call_times: deque[float] = deque()
        self._lock = threading.Lock()

    def acquire(self) -> None:
        with self._lock:
            now = time.monotonic()
            while self._call_times and now - self._call_times[0] >= self._period_seconds:
                self._call_times.popleft()

            if len(self._call_times) >= self._max_calls:
                sleep_for = self._period_seconds - (now - self._call_times[0])
                if sleep_for > 0:
                    time.sleep(sleep_for)
                now = time.monotonic()
                while self._call_times and now - self._call_times[0] >= self._period_seconds:
                    self._call_times.popleft()

            self._call_times.append(time.monotonic())
