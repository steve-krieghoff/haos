"""Persistent storage for feeding events."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.storage import Store
import homeassistant.util.dt as dt_util

from .const import DOMAIN, HISTORY_RETENTION_DAYS, SIGNAL_UPDATE

STORAGE_VERSION = 1


@dataclass
class FeedingEvent:
    """A single logged feeding."""

    timestamp: datetime
    amount_g: float
    food_type: str | None = None
    note: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "amount_g": self.amount_g,
            "food_type": self.food_type,
            "note": self.note,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "FeedingEvent":
        return FeedingEvent(
            timestamp=dt_util.parse_datetime(data["timestamp"]) or dt_util.utcnow(),
            amount_g=data["amount_g"],
            food_type=data.get("food_type"),
            note=data.get("note"),
        )


@dataclass
class FeedingStore:
    """Loads, saves and queries feeding events for one cat (config entry)."""

    hass: HomeAssistant
    entry_id: str
    _store: Store = field(init=False)
    events: list[FeedingEvent] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        self._store = Store(self.hass, STORAGE_VERSION, f"{DOMAIN}_{self.entry_id}")

    async def async_load(self) -> None:
        data = await self._store.async_load()
        if data and "events" in data:
            self.events = [FeedingEvent.from_dict(e) for e in data["events"]]

    async def _async_save(self) -> None:
        await self._store.async_save(
            {"events": [e.as_dict() for e in self.events]}
        )

    async def async_log_feeding(
        self, amount_g: float, food_type: str | None = None, note: str | None = None
    ) -> FeedingEvent:
        event = FeedingEvent(
            timestamp=dt_util.now(), amount_g=amount_g, food_type=food_type, note=note
        )
        self.events.append(event)
        self._prune()
        await self._async_save()
        self._notify()
        return event

    def _prune(self) -> None:
        cutoff = dt_util.now() - timedelta(days=HISTORY_RETENTION_DAYS)
        self.events = [e for e in self.events if e.timestamp >= cutoff]

    @callback
    def notify_update(self) -> None:
        """Fire an update without logging a new event (e.g. midnight rollover)."""
        self._notify()

    def _notify(self) -> None:
        async_dispatcher_send(self.hass, SIGNAL_UPDATE.format(entry_id=self.entry_id))

    def events_since(self, since: datetime) -> list[FeedingEvent]:
        return [e for e in self.events if e.timestamp >= since]

    @property
    def today_events(self) -> list[FeedingEvent]:
        return self.events_since(dt_util.start_of_local_day())

    @property
    def today_total_g(self) -> float:
        return round(sum(e.amount_g for e in self.today_events), 1)

    @property
    def today_count(self) -> int:
        return len(self.today_events)

    @property
    def last_event(self) -> FeedingEvent | None:
        # Events are always appended in logging order, so the last list
        # entry is the most recently logged one - this also stays correct
        # when two events happen to share the same timestamp, unlike
        # picking the max() by timestamp.
        if not self.events:
            return None
        return self.events[-1]

    def average_daily_total_g(self, days: int = 7) -> float:
        since = dt_util.start_of_local_day() - timedelta(days=days - 1)
        recent = self.events_since(since)
        if not recent:
            return 0.0
        totals: dict[Any, float] = {}
        for e in recent:
            day = dt_util.as_local(e.timestamp).date()
            totals[day] = totals.get(day, 0.0) + e.amount_g
        return round(sum(totals.values()) / days, 1)
