"""DataUpdateCoordinator for Stade de France events."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import DOMAIN, LOGGER, UPDATE_INTERVAL
from .scraper import ScrapeError, StadeEvent, fetch_events


class StadeDeFranceCoordinator(DataUpdateCoordinator[list[StadeEvent]]):
    """Coordinator that periodically scrapes upcoming events."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialise the coordinator."""
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self._session = async_get_clientsession(hass)

    async def _async_update_data(self) -> list[StadeEvent]:
        """Fetch events and drop those already in the past."""
        tz = dt_util.get_default_time_zone()
        try:
            events = await fetch_events(self._session, tz)
        except ScrapeError as err:
            raise UpdateFailed(str(err)) from err

        now = dt_util.now()
        upcoming = [event for event in events if event.start >= now]
        return upcoming
