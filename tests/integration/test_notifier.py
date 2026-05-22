"""Tests for the integrated notifier (lead window + dedup)."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from custom_components.stade_de_france.const import (
    CONF_LEAD_DAYS,
    CONF_NOTIFY_SERVICE,
    CONF_NOTIFY_TIME,
)
from custom_components.stade_de_france.notifier import EventNotifier
from custom_components.stade_de_france.scraper import StadeEvent

from pytest_homeassistant_custom_component.common import async_mock_service


class _StubCoordinator:
    """Minimal stand-in for the DataUpdateCoordinator."""

    def __init__(self, events):
        self.data = events

    def async_add_listener(self, _update_callback, _context=None):
        return lambda: None


def _event(uid: str, days_from_now: int) -> StadeEvent:
    start = dt_util.now() + timedelta(days=days_from_now)
    return StadeEvent(
        uid=uid,
        name=f"Event {uid}",
        start=start,
        event_type="Concert",
        availability="Disponible",
        url="https://example.test",
    )


def _options() -> dict:
    return {
        CONF_NOTIFY_SERVICE: "notify.mobile_app_test",
        CONF_LEAD_DAYS: 2,
        CONF_NOTIFY_TIME: "09:00:00",
    }


async def test_notifies_within_window_only(hass: HomeAssistant) -> None:
    """Only events within lead_days are notified."""
    calls = async_mock_service(hass, "notify", "mobile_app_test")
    events = [
        _event("inside", 1),   # within 2 days -> notify
        _event("today", 0),    # today -> notify
        _event("outside", 5),  # beyond 2 days -> no notify
    ]
    notifier = EventNotifier(hass, _StubCoordinator(events), _options())

    await notifier._async_check()
    await hass.async_block_till_done()

    notified_names = {call.data["message"] for call in calls}
    assert len(calls) == 2
    assert any("Event inside" in m for m in notified_names)
    assert any("Event today" in m for m in notified_names)
    assert not any("Event outside" in m for m in notified_names)


async def test_no_duplicate_notifications(hass: HomeAssistant) -> None:
    """An event is notified at most once across repeated checks."""
    calls = async_mock_service(hass, "notify", "mobile_app_test")
    events = [_event("once", 1)]
    notifier = EventNotifier(hass, _StubCoordinator(events), _options())

    await notifier._async_check()
    await notifier._async_check()
    await hass.async_block_till_done()

    assert len(calls) == 1


async def test_no_service_configured_does_not_raise(hass: HomeAssistant) -> None:
    """With no notify service set, checking is a no-op (warning only)."""
    options = _options() | {CONF_NOTIFY_SERVICE: None}
    notifier = EventNotifier(hass, _StubCoordinator([_event("x", 1)]), options)
    await notifier._async_check()
    await hass.async_block_till_done()
