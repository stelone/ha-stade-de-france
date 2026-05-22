"""Tests for the SecuTix HTML scraper, using a frozen real-world fixture.

The scraper has no Home Assistant dependency, so we load it directly (without
triggering the package ``__init__``) to keep this test fast and standalone.
"""

from __future__ import annotations

import importlib.util
import sys
import types
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

PARIS = ZoneInfo("Europe/Paris")
_PKG_DIR = Path(__file__).parents[1] / "custom_components" / "stade_de_france"
FIXTURE = Path(__file__).parent / "fixtures" / "events.html"


def _load_scraper():
    """Load const + scraper modules without importing the HA-dependent package."""
    pkg = types.ModuleType("_sdf")
    pkg.__path__ = [str(_PKG_DIR)]
    sys.modules["_sdf"] = pkg
    for name in ("const", "scraper"):
        spec = importlib.util.spec_from_file_location(
            f"_sdf.{name}", _PKG_DIR / f"{name}.py"
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[f"_sdf.{name}"] = module
        spec.loader.exec_module(module)
    return sys.modules["_sdf.scraper"]


_scraper = _load_scraper()
parse_events = _scraper.parse_events


def _events():
    return parse_events(FIXTURE.read_text(encoding="utf-8"), PARIS)


def test_parses_all_events():
    assert len(_events()) == 2


def test_rugby_event_parsed():
    top14 = next(e for e in _events() if "TOP14" in e.name.upper())
    assert top14.event_type == "Rugby"
    assert top14.start == datetime(2026, 6, 27, 21, 5, tzinfo=PARIS)
    assert top14.uid == "10229562035639"
    assert top14.availability == "Épuisé"


def test_concert_event_parsed():
    aya = next(e for e in _events() if "AYA NAKAMURA" in e.name.upper())
    assert aya.event_type == "Concert"
    assert aya.start == datetime(2026, 5, 29, 18, 30, tzinfo=PARIS)
    assert aya.uid == "10229549968364"


def test_events_sorted_by_start():
    events = _events()
    assert events == sorted(events, key=lambda e: e.start)


def test_unparsable_html_returns_empty():
    assert parse_events("<html><body>no events here</body></html>", PARIS) == []
