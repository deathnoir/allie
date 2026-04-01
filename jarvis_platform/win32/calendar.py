"""
Windows calendar access via Google Calendar API.

Async wrappers around GoogleCalendarClient that match the interface
expected by server.py (same signatures as calendar_access.py).
"""

import asyncio
import logging
import time as _time
from datetime import datetime, timedelta
from typing import Optional

log = logging.getLogger("jarvis.calendar.win32")

# Cache: refreshed in background, never blocks responses
_event_cache: list[dict] = []
_cache_time: float = 0


def _get_client():
    from ..google_services import get_calendar_client
    return get_calendar_client()


async def get_todays_events() -> list[dict]:
    """Get today's events from cache."""
    if not _event_cache and _cache_time == 0:
        await refresh_calendar_cache()
    return _event_cache


async def get_upcoming_events(hours: int = 4) -> list[dict]:
    """Get events in the next N hours."""
    events = await get_todays_events()
    now = datetime.now()
    cutoff = now + timedelta(hours=hours)
    return [
        e for e in events
        if not e["all_day"] and e.get("start_dt") and now <= e["start_dt"] <= cutoff
    ]


async def get_next_event() -> Optional[dict]:
    """Get the next upcoming event."""
    events = await get_upcoming_events(hours=24)
    return events[0] if events else None


async def get_calendar_names() -> list[str]:
    """Get list of all calendar names."""
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(None, _get_client().get_calendar_names)
    except Exception as e:
        log.warning(f"get_calendar_names failed: {e}")
        return []


async def refresh_calendar_cache() -> None:
    """Refresh the event cache from Google Calendar."""
    global _event_cache, _cache_time

    loop = asyncio.get_event_loop()
    start = _time.time()

    try:
        now = datetime.now()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        events = await loop.run_in_executor(
            None, _get_client().get_events_for_range, start_of_day, end_of_day
        )

        _event_cache = events
        _cache_time = _time.time()
        elapsed = _time.time() - start
        log.info(f"Calendar cache refreshed: {len(events)} events today ({elapsed:.1f}s)")

    except Exception as e:
        log.warning(f"Calendar cache refresh failed: {e}")
