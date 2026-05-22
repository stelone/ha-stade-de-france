"""Sensor platform for Stade de France."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from . import StadeConfigEntry
from .coordinator import StadeDeFranceCoordinator
from .entity import StadeDeFranceEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: StadeConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensors."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        [
            NextEventSensor(coordinator),
            DaysUntilNextSensor(coordinator),
            EventCountSensor(coordinator),
        ]
    )


class NextEventSensor(StadeDeFranceEntity, SensorEntity):
    """Name of the next upcoming event, with details as attributes."""

    _attr_translation_key = "next_event"
    _attr_icon = "mdi:stadium"

    def __init__(self, coordinator: StadeDeFranceCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = "stade_de_france_next_event"

    @property
    def native_value(self) -> str | None:
        events = self.coordinator.data or []
        return events[0].name if events else None

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        events = self.coordinator.data or []
        if not events:
            return None
        event = events[0]
        return {
            "start": event.start.isoformat(),
            "type": event.event_type,
            "availability": event.availability,
            "url": event.url,
        }


class DaysUntilNextSensor(StadeDeFranceEntity, SensorEntity):
    """Number of days until the next event."""

    _attr_translation_key = "days_until_next"
    _attr_icon = "mdi:calendar-clock"
    _attr_native_unit_of_measurement = UnitOfTime.DAYS
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: StadeDeFranceCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = "stade_de_france_days_until_next"

    @property
    def native_value(self) -> int | None:
        events = self.coordinator.data or []
        if not events:
            return None
        return max((events[0].start.date() - dt_util.now().date()).days, 0)


class EventCountSensor(StadeDeFranceEntity, SensorEntity):
    """Number of upcoming events."""

    _attr_translation_key = "event_count"
    _attr_icon = "mdi:calendar-multiple"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: StadeDeFranceCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = "stade_de_france_event_count"

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data or [])
