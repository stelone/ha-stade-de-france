"""Shared base entity for Stade de France."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import StadeDeFranceCoordinator


class StadeDeFranceEntity(CoordinatorEntity[StadeDeFranceCoordinator]):
    """Base entity with shared device info."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: StadeDeFranceCoordinator) -> None:
        """Initialise the entity."""
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "stade_de_france")},
            name="Stade de France",
            manufacturer="Stade de France",
            entry_type=None,
            configuration_url="https://billets.stadefrance.com/list/events",
        )
