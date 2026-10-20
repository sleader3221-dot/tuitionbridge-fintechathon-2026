import threading
from collections import defaultdict, deque

from ..clock import Clock


class RateLimited(Exception):
    pass


class RateLimiter:
    def __init__(self, limit_per_minute: int, clock: Clock):
        self.limit = limit_per_minute
        self.clock = clock
        self._hits: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str) -> None:
        now = self.clock.now().timestamp()
        with self._lock:
            dq = self._hits[key]
            while dq and now - dq[0] >= 60:
                dq.popleft()
            if len(dq) >= self.limit:
                raise RateLimited(f"Rate limit of {self.limit} requests per minute exceeded")
            dq.append(now)
