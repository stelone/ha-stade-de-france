"""Integrated notifications: alert N days before each event.

Restart-safe design:

* A daily time trigger (at the configured time) checks upcoming events.
* Each coordinator refresh also triggers a check.
* For every upcoming event within the ``lead_days`` window whose uid has not
  yet been notified, the configured ``notify`` service is called and the uid is
  recorded in a persistent store so we never notify twice (even across
  restarts). Past uids are purged to keep the store bounded.
"""

from __future__ import annotations

from datetime import datetime, time

from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    CONF_LEAD_DAYS,
    CONF_NOTIFY_SERVICE,
    CONF_NOTIFY_TIME,
    DEFAULT_LEAD_DAYS,
    DEFAULT_NOTIFY_TIME,
    LOGGER,
    STORAGE_KEY,
    STORAGE_VERSION,
)
from .coordinator import StadeDeFranceCoordinator
from .scraper import StadeEvent

_FRENCH_WEEKDAYS = [
    "lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche",
]
_FRENCH_MONTHS = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]


def _parse_time(value: str) -> time:
    """Parse a 'HH:MM' or 'HH:MM:SS' string into a time object."""
    parsed = dt_util.parse_time(value)
    return parsed or dt_util.parse_time(DEFAULT_NOTIFY_TIME)


def _format_date(start: datetime) -> str:
    """Human French date, e.g. 'samedi 27 juin 2026 à 21:05'."""
    weekday = _FRENCH_WEEKDAYS[start.weekday()]
    month = _FRENCH_MONTHS[start.month - 1]
    return f"{weekday} {start.day} {month} {start.year} à {start:%H:%M}"


def _lead_phrase(days: int) -> str:
    """Return 'aujourd'hui' / 'demain' / 'dans N jours'."""
    if days <= 0:
        return "aujourd'hui"
    if days == 1:
        return "demain"
    return f"dans {days} jours"


class EventNotifier:
    """Sends integrated notifications ahead of upcoming events."""

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: StadeDeFranceCoordinator,
        options: dict,
    ) -> None:
        """Initialise the notifier from config-entry options."""
        self.hass = hass
        self.coordinator = coordinator
        self._notify_service: str | None = options.get(CONF_NOTIFY_SERVICE)
        self._lead_days: int = int(options.get(CONF_LEAD_DAYS, DEFAULT_LEAD_DAYS))
        self._notify_time = _parse_time(
            options.get(CONF_NOTIFY_TIME, DEFAULT_NOTIFY_TIME)
        )
        self._store: Store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._notified: set[str] = set()
        self._unsub_time: CALLBACK_TYPE | None = None
        self._unsub_coordinator: CALLBACK_TYPE | None = None

    async def async_start(self) -> None:
        """Load persisted state and register triggers."""
        data = await self._store.async_load()
        if isinstance(data, dict):
            self._notified = set(data.get("notified", []))

        self._unsub_time = async_track_time_change(
            self.hass,
            self._handle_time,
            hour=self._notify_time.hour,
            minute=self._notify_time.minute,
            second=0,
        )
        # Also re-check whenever the event list refreshes.
        self._unsub_coordinator = self.coordinator.async_add_listener(
            self._handle_coordinator_update
        )
        # Run an initial check immediately (e.g. event already inside the window).
        await self._async_check()

    @callback
    def async_stop(self) -> None:
        """Unregister all triggers."""
        if self._unsub_time is not None:
            self._unsub_time()
            self._unsub_time = None
        if self._unsub_coordinator is not None:
            self._unsub_coordinator()
            self._unsub_coordinator = None

    @callback
    def _handle_time(self, _now: datetime) -> None:
        self.hass.async_create_task(self._async_check())

    @callback
    def _handle_coordinator_update(self) -> None:
        self.hass.async_create_task(self._async_check())

    async def _async_check(self) -> None:
        """Notify for events inside the lead window and prune past uids."""
        events: list[StadeEvent] = self.coordinator.data or []
        now = dt_util.now()
        today = now.date()

        valid_uids = {event.uid for event in events}
        changed = False

        for event in events:
            days_until = (event.start.date() - today).days
            if not 0 <= days_until <= self._lead_days:
                continue
            if event.uid in self._notified:
                continue
            self._send(event, days_until)
            self._notified.add(event.uid)
            changed = True

        # Prune uids that are no longer upcoming so the store stays bounded.
        stale = self._notified - valid_uids
        if stale:
            self._notified -= stale
            changed = True

        if changed:
            await self._store.async_save({"notified": list(self._notified)})

    @callback
    def _send(self, event: StadeEvent, days_until: int) -> None:
        """Call the configured notify service for an event."""
        if not self._notify_service:
            LOGGER.warning(
                "Stade de France: event '%s' is %s but no notify service is configured",
                event.name,
                _lead_phrase(days_until),
            )
            return

        # notify_service is stored as "notify.mobile_app_xxx" or "mobile_app_xxx".
        service = self._notify_service.split(".", 1)[-1]
        message = (
            f"🏟️ {event.name} au Stade de France {_lead_phrase(days_until)} "
            f"({_format_date(event.start)})."
        )
        self.hass.async_create_task(
            self.hass.services.async_call(
                "notify",
                service,
                {"title": "Stade de France", "message": message},
                blocking=False,
            )
        )
