"""Constants for the Stade de France integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Final

DOMAIN: Final = "stade_de_france"

LOGGER: Final = logging.getLogger(__package__)

# Official SecuTix ticketing event list (server-rendered HTML).
EVENTS_URL: Final = "https://billets.stadefrance.com/list/events?lang=fr"

# How often we re-scrape the event list.
UPDATE_INTERVAL: Final = timedelta(hours=12)

# Options keys.
CONF_NOTIFY_SERVICE: Final = "notify_service"
CONF_LEAD_DAYS: Final = "lead_days"
CONF_NOTIFY_TIME: Final = "notify_time"

# Defaults.
DEFAULT_LEAD_DAYS: Final = 2
MIN_LEAD_DAYS: Final = 0
MAX_LEAD_DAYS: Final = 7
DEFAULT_NOTIFY_TIME: Final = "09:00:00"

# Persistent storage of already-notified event uids.
STORAGE_VERSION: Final = 1
STORAGE_KEY: Final = f"{DOMAIN}_notified"

PLATFORMS: Final = ["calendar", "sensor", "binary_sensor"]
