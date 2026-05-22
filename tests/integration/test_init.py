"""End-to-end setup test (network mocked)."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util

from custom_components.stade_de_france.const import CONF_LEAD_DAYS, DOMAIN
from custom_components.stade_de_france.scraper import StadeEvent

from pytest_homeassistant_custom_component.common import MockConfigEntry


def _sample_events() -> list[StadeEvent]:
    now = dt_util.now()
    return [
        StadeEvent(
            uid="1",
            name="Concert proche",
            start=now + timedelta(days=1),
            event_type="Concert",
            availability="Disponible",
            url="https://example.test/1",
        ),
        StadeEvent(
            uid="2",
            name="Match lointain",
            start=now + timedelta(days=20),
            event_type="Rugby",
            availability="Épuisé",
            url="https://example.test/2",
        ),
    ]


async def test_setup_creates_entities(hass: HomeAssistant) -> None:
    """Setting up the entry creates calendar, sensors and binary_sensor."""
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=DOMAIN, options={CONF_LEAD_DAYS: 2}
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.stade_de_france.coordinator.fetch_events",
        return_value=_sample_events(),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED

    registry = er.async_get(hass)

    def state_of(unique_id: str):
        entity_id = registry.async_get_entity_id(
            _domain_for(unique_id), DOMAIN, unique_id
        )
        assert entity_id is not None, f"no entity for unique_id {unique_id}"
        return hass.states.get(entity_id)

    assert state_of("stade_de_france_events") is not None  # calendar

    next_event = state_of("stade_de_france_next_event")
    assert next_event.state == "Concert proche"
    assert next_event.attributes["type"] == "Concert"

    assert state_of("stade_de_france_event_count").state == "2"

    # event in 1 day, lead window = 2 -> on
    assert state_of("stade_de_france_event_upcoming").state == "on"


def _domain_for(unique_id: str) -> str:
    if unique_id.endswith("_events"):
        return "calendar"
    if unique_id.endswith("_upcoming"):
        return "binary_sensor"
    return "sensor"


async def test_unload_entry(hass: HomeAssistant) -> None:
    """The entry unloads cleanly."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, options={})
    entry.add_to_hass(hass)

    with patch(
        "custom_components.stade_de_france.coordinator.fetch_events",
        return_value=_sample_events(),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.state is ConfigEntryState.NOT_LOADED
