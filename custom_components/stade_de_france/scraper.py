"""Fetch and parse the Stade de France event list (SecuTix ticketing page).

There is no public API for Stade de France events, so we scrape the official
SecuTix ticketing page. Each event is a ``<section id="prod_<id>" class="product
product_EVENT … product_topic_<Type> …">`` block containing:

* ``a.title``        -> event name
* ``span.day``       -> date in French (e.g. "samedi 27 juin 2026")
* a "HH:MM" time string somewhere in the block
* ``product_topic_<Type>`` class -> event type (Concert, rugby, football…)

Parsing is defensive: a block we cannot understand is logged and skipped
rather than aborting the whole refresh.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, tzinfo

from bs4 import BeautifulSoup
from bs4.element import Tag

from .const import EVENTS_URL, LOGGER

# French month name -> month number. SecuTix renders lowercase month names.
_FRENCH_MONTHS: dict[str, int] = {
    "janvier": 1,
    "février": 2,
    "fevrier": 2,
    "mars": 3,
    "avril": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7,
    "août": 8,
    "aout": 8,
    "septembre": 9,
    "octobre": 10,
    "novembre": 11,
    "décembre": 12,
    "decembre": 12,
}

# "samedi 27 juin 2026" -> day, month name, year (weekday prefix is optional).
_DATE_RE = re.compile(
    r"(\d{1,2})\s+([A-Za-zéûôà]+)\s+(\d{4})",
    re.IGNORECASE,
)
_TIME_RE = re.compile(r"\b([01]?\d|2[0-3]):([0-5]\d)\b")
_TOPIC_RE = re.compile(r"product_topic_([A-Za-z0-9]+)")
_PRODUCT_ID_RE = re.compile(r"prod_(\d+)")

_USER_AGENT = (
    "Mozilla/5.0 (compatible; HomeAssistant-StadeDeFrance/0.1; "
    "+https://github.com/stelone/ha-stade-de-france)"
)


@dataclass(slots=True)
class StadeEvent:
    """A single event at the Stade de France."""

    uid: str
    name: str
    start: datetime
    event_type: str
    availability: str
    url: str


class ScrapeError(Exception):
    """Raised when the event page cannot be fetched or contains no events."""


def _normalise_topic(raw: str) -> str:
    """Turn a raw topic class fragment into a human label."""
    mapping = {
        "concert": "Concert",
        "rugby": "Rugby",
        "football": "Football",
        "foot": "Football",
    }
    return mapping.get(raw.lower(), raw.capitalize())


def _parse_datetime(date_text: str, time_text: str | None, tz: tzinfo) -> datetime | None:
    """Build a tz-aware datetime from a French date string and optional time."""
    match = _DATE_RE.search(date_text)
    if not match:
        return None
    day_s, month_name, year_s = match.groups()
    month = _FRENCH_MONTHS.get(month_name.lower())
    if month is None:
        return None

    hour, minute = 0, 0
    if time_text:
        time_match = _TIME_RE.search(time_text)
        if time_match:
            hour, minute = int(time_match.group(1)), int(time_match.group(2))

    try:
        return datetime(int(year_s), month, int(day_s), hour, minute, tzinfo=tz)
    except ValueError:
        return None


def _parse_block(block: Tag, tz: tzinfo) -> StadeEvent | None:
    """Parse a single event ``<section>`` into a StadeEvent, or None on failure."""
    # uid from the section id (prod_<id>).
    section_id = block.get("id", "") or ""
    id_match = _PRODUCT_ID_RE.search(section_id)
    uid = id_match.group(1) if id_match else None

    # event type from the product_topic_ class.
    classes = " ".join(block.get("class", []))
    topic_match = _TOPIC_RE.search(classes)
    event_type = _normalise_topic(topic_match.group(1)) if topic_match else "Événement"

    title_tag = block.select_one("a.title") or block.select_one(".title")
    name = title_tag.get_text(strip=True) if title_tag else None

    day_tag = block.select_one("span.day") or block.select_one(".unique")
    date_text = day_tag.get_text(" ", strip=True) if day_tag else ""

    block_text = block.get_text(" ", strip=True)
    start = _parse_datetime(date_text, block_text, tz)

    if not uid or not name or start is None:
        LOGGER.warning(
            "Skipping unparsable Stade de France event block (id=%r, name=%r, date=%r)",
            section_id,
            name,
            date_text,
        )
        return None

    # url: prefer the title link.
    url = EVENTS_URL
    if title_tag is not None and title_tag.has_attr("href"):
        href = title_tag["href"]
        if href.startswith("//"):
            url = f"https:{href}"
        elif href.startswith("http"):
            url = href
        elif href.startswith("/"):
            url = f"https://billets.stadefrance.com{href}"

    availability = _extract_availability(block_text)

    return StadeEvent(
        uid=uid,
        name=name,
        start=start,
        event_type=event_type,
        availability=availability,
        url=url,
    )


def _extract_availability(block_text: str) -> str:
    """Best-effort availability label from the block text."""
    lowered = block_text.lower()
    if "epuisé" in lowered or "épuisé" in lowered or "complet" in lowered:
        return "Épuisé"
    if "bientôt" in lowered or "bientot" in lowered:
        return "Bientôt"
    if "liste d'attente" in lowered or "waitinglist" in lowered:
        return "Liste d'attente"
    if "achat" in lowered or "disponible" in lowered or "acheter" in lowered:
        return "Disponible"
    return "Inconnu"


def parse_events(html: str, tz: tzinfo) -> list[StadeEvent]:
    """Parse the full events page HTML into a sorted list of StadeEvent."""
    soup = BeautifulSoup(html, "html.parser")
    blocks = soup.select("section.product_EVENT")
    events: list[StadeEvent] = []
    seen: set[str] = set()
    for block in blocks:
        event = _parse_block(block, tz)
        if event is None or event.uid in seen:
            continue
        seen.add(event.uid)
        events.append(event)
    events.sort(key=lambda e: e.start)
    return events


async def fetch_events(session, tz: tzinfo) -> list[StadeEvent]:
    """Fetch the event page and return parsed events.

    Raises ScrapeError on network failure or when the page yields no events.
    """
    import aiohttp

    try:
        async with session.get(
            EVENTS_URL,
            headers={"User-Agent": _USER_AGENT},
            timeout=aiohttp.ClientTimeout(total=30),
        ) as response:
            response.raise_for_status()
            html = await response.text()
    except Exception as err:  # noqa: BLE001 - surfaced as ScrapeError to coordinator
        raise ScrapeError(f"Could not fetch Stade de France events: {err}") from err

    events = parse_events(html, tz)
    if not events:
        raise ScrapeError("No events parsed from Stade de France page (layout changed?)")
    return events
