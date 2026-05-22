"""Binary sensor: an event is within the configured lead window."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from . import StadeConfigEntry
from .const import CONF_LEAD_DAYS, DEFAULT_LEAD_DAYS
from .coordinator import StadeDeFranceCoordinator
from .entity import StadeDeFranceEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: StadeConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary sensor."""
    lead_days = int(entry.options.get(CONF_LEAD_DAYS, DEFAULT_LEAD_DAYS))
    async_add_entities(
        [EventUpcomingBinarySensor(entry.runtime_data.coordinator, lead_days)]
    )


class EventUpcomingBinarySensor(StadeDeFranceEntity, BinarySensorEntity):
    """ON when an event falls within the configured lead window."""

    _attr_translation_key = "event_upcoming"
    _attr_icon = "mdi:bell-ring"

    def __init__(
        self, coordinator: StadeDeFranceCoordinator, lead_days: int
    ) -> None:
        super().__init__(coordinator)
        self._lead_days = lead_days
        self._attr_unique_id = "stade_de_france_event_upcoming"

    @property
    def is_on(self) -> bool:
        events = self.coordinator.data or []
        today = dt_util.now().date()
        return any(
            0 <= (event.start.date() - today).days <= self._lead_days
            for event in events
        )

    @property
    def extra_state_attributes(self) -> dict[str, int]:
        return {"lead_days": self._lead_days}
