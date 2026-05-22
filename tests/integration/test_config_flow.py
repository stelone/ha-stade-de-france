"""Config and options flow tests."""

from __future__ import annotations

from unittest.mock import patch

from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.stade_de_france.const import (
    CONF_LEAD_DAYS,
    CONF_NOTIFY_SERVICE,
    CONF_NOTIFY_TIME,
    DEFAULT_LEAD_DAYS,
    DOMAIN,
)

from pytest_homeassistant_custom_component.common import MockConfigEntry


async def test_user_flow_creates_entry(hass: HomeAssistant) -> None:
    """The user step creates a single entry with default options."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Stade de France"
    assert result["options"][CONF_LEAD_DAYS] == DEFAULT_LEAD_DAYS


async def test_single_instance_only(hass: HomeAssistant) -> None:
    """A second setup attempt is aborted."""
    MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN).add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_options_flow(hass: HomeAssistant) -> None:
    """Options can be set and are stored."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, options={})
    entry.add_to_hass(hass)

    with patch(
        "custom_components.stade_de_france.async_setup_entry", return_value=True
    ):
        result = await hass.config_entries.options.async_init(entry.entry_id)
        assert result["type"] is FlowResultType.FORM

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_NOTIFY_SERVICE: "notify.mobile_app_test",
                CONF_LEAD_DAYS: 1,
                CONF_NOTIFY_TIME: "08:30:00",
            },
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_NOTIFY_SERVICE] == "notify.mobile_app_test"
        assert result["data"][CONF_LEAD_DAYS] == 1
