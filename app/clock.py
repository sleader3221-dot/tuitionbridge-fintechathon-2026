"""Injectable clock so tests can control time (quote expiry, daily caps, rate limits)."""
from datetime import date, datetime, timedelta, timezone


class Clock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)

    def today(self) -> date:
        return self.now().date()


class FixedClock(Clock):
    def __init__(self, at: datetime):
        self._at = at

    def now(self) -> datetime:
        return self._at

    def advance(self, seconds: int) -> None:
        self._at = self._at + timedelta(seconds=seconds)
