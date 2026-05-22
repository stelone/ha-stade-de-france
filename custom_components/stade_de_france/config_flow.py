"""Config and options flow for Stade de France."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_LEAD_DAYS,
    CONF_NOTIFY_SERVICE,
    CONF_NOTIFY_TIME,
    DEFAULT_LEAD_DAYS,
    DEFAULT_NOTIFY_TIME,
    DOMAIN,
    MAX_LEAD_DAYS,
    MIN_LEAD_DAYS,
)


class StadeDeFranceConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial setup. A single instance only."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Create the single config entry."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(
                title="Stade de France",
                data={},
                options={
                    CONF_LEAD_DAYS: DEFAULT_LEAD_DAYS,
                    CONF_NOTIFY_TIME: DEFAULT_NOTIFY_TIME,
                },
            )

        return self.async_show_form(step_id="user")

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the options flow."""
        return StadeDeFranceOptionsFlow()


class StadeDeFranceOptionsFlow(OptionsFlow):
    """Configure notify service, lead time and notification hour."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        options = self.config_entry.options
        notify_services = sorted(
            self.hass.services.async_services().get("notify", {}).keys()
        )
        notify_options = [f"notify.{name}" for name in notify_services]

        notify_default = options.get(CONF_NOTIFY_SERVICE)

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_NOTIFY_SERVICE,
                    description={"suggested_value": notify_default},
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=notify_options,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                        custom_value=True,
                    )
                ),
                vol.Required(
                    CONF_LEAD_DAYS,
                    default=options.get(CONF_LEAD_DAYS, DEFAULT_LEAD_DAYS),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=MIN_LEAD_DAYS,
                        max=MAX_LEAD_DAYS,
                        step=1,
                        mode=selector.NumberSelectorMode.SLIDER,
                    )
                ),
                vol.Required(
                    CONF_NOTIFY_TIME,
                    default=options.get(CONF_NOTIFY_TIME, DEFAULT_NOTIFY_TIME),
                ): selector.TimeSelector(),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
