"""Calendar platform exposing all upcoming Stade de France events."""

from __future__ import annotations

from datetime import datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import StadeConfigEntry
from .coordinator import StadeDeFranceCoordinator
from .entity import StadeDeFranceEntity
from .scraper import StadeEvent

# Events have a start time but no published end time; assume a typical duration.
_DEFAULT_DURATION = timedelta(hours=3)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: StadeConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the calendar entity."""
    async_add_entities([StadeDeFranceCalendar(entry.runtime_data.coordinator)])


def _to_calendar_event(event: StadeEvent) -> CalendarEvent:
    """Convert a StadeEvent into a Home Assistant CalendarEvent."""
    return CalendarEvent(
        start=event.start,
        end=event.start + _DEFAULT_DURATION,
        summary=event.name,
        location="Stade de France, Saint-Denis",
        description=f"{event.event_type} — {event.availability}\n{event.url}",
        uid=event.uid,
    )


class StadeDeFranceCalendar(StadeDeFranceEntity, CalendarEntity):
    """A calendar of all upcoming events."""

    _attr_translation_key = "events"

    def __init__(self, coordinator: StadeDeFranceCoordinator) -> None:
        """Initialise the calendar."""
        super().__init__(coordinator)
        self._attr_unique_id = "stade_de_france_events"

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming event."""
        events = self.coordinator.data or []
        if not events:
            return None
        return _to_calendar_event(events[0])

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        """Return events within the requested window."""
        events = self.coordinator.data or []
        return [
            _to_calendar_event(event)
            for event in events
            if start_date <= event.start <= end_date
        ]
