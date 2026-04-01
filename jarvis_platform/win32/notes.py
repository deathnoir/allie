"""
Windows notes access — uses local SQLite via memory.py.

On Windows there's no Apple Notes equivalent that's easily accessible,
so notes are stored locally in the same SQLite database as JARVIS memory.
The voice experience is identical: "Take a note" / "What are my notes?"
"""

import logging
from datetime import datetime
from typing import Optional

log = logging.getLogger("jarvis.notes.win32")


async def get_recent_notes(count: int = 10) -> list[dict]:
    """Get most recent notes from local storage."""
    from memory import search_notes

    try:
        notes = search_notes("")  # Empty query returns recent notes
        return [
            {
                "title": n.get("topic", n.get("title", "Untitled")),
                "date": n.get("created_at", ""),
                "folder": "Local",
            }
            for n in notes[:count]
        ]
    except Exception as e:
        log.warning(f"get_recent_notes failed: {e}")
        return []


async def read_note(title_match: str) -> Optional[dict]:
    """Read a note by title (partial match)."""
    from memory import search_notes

    try:
        results = search_notes(title_match)
        if results:
            note = results[0]
            return {
                "title": note.get("topic", note.get("title", "Untitled")),
                "body": note.get("content", note.get("body", "")),
            }
        return None
    except Exception as e:
        log.warning(f"read_note failed: {e}")
        return None


async def search_notes(query: str, count: int = 5) -> list[dict]:
    """Search notes by keyword."""
    from memory import search_notes as memory_search

    try:
        results = memory_search(query)
        return [
            {
                "title": n.get("topic", n.get("title", "Untitled")),
                "date": n.get("created_at", ""),
            }
            for n in results[:count]
        ]
    except Exception as e:
        log.warning(f"search_notes failed: {e}")
        return []


async def create_note(title: str, body: str, folder: str = "Notes") -> bool:
    """Create a new note in local storage."""
    from memory import create_note as memory_create

    try:
        memory_create(topic=title, content=body)
        log.info(f"Created local note: {title}")
        return True
    except Exception as e:
        log.warning(f"create_note failed: {e}")
        return False


async def get_note_folders() -> list[str]:
    """Get list of note folders. Local storage has a single folder."""
    return ["Local"]
