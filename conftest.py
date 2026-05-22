"""Root pytest configuration.

The scraper test runs with no Home Assistant dependency. The integration tests
under ``tests/integration`` need ``pytest-homeassistant-custom-component``; when
it isn't installed they are excluded from collection so the scraper test still
runs on its own.
"""

from __future__ import annotations

import importlib.util

_HAS_HA = (
    importlib.util.find_spec("pytest_homeassistant_custom_component") is not None
)

collect_ignore_glob: list[str] = [] if _HAS_HA else ["tests/integration/*"]

if _HAS_HA:
    pytest_plugins = "pytest_homeassistant_custom_component"
