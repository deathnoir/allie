"""
Platform abstraction base classes for JARVIS.

Defines the interface contract that macOS (darwin) and Windows (win32)
implementations must satisfy.
"""

from abc import ABC, abstractmethod
from typing import Optional


class TerminalProvider(ABC):
    @abstractmethod
    async def open_terminal(self, command: str = "") -> dict:
        """Open a terminal window, optionally running a command.
        Returns {"success": bool, "confirmation": str}.
        """

    @abstractmethod
    async def open_claude_in_project(self, project_dir: str, prompt: str) -> dict:
        """Open a terminal, cd to project dir, and run Claude Code.
        Returns {"success": bool, "confirmation": str}.
        """

    @abstractmethod
    async def prompt_existing_terminal(self, project_name: str, prompt: str) -> dict:
        """Find a terminal window matching project_name and type a prompt into it.
        Returns {"success": bool, "confirmation": str}.
        """

    @abstractmethod
    async def focus_terminal_window(self, project_name: str) -> bool:
        """Bring a terminal window matching project_name to the front."""


class BrowserProvider(ABC):
    @abstractmethod
    async def open_browser(self, url: str, browser: str = "chrome") -> dict:
        """Open a URL in the user's browser.
        Returns {"success": bool, "confirmation": str}.
        """

    @abstractmethod
    async def get_active_tab_info(self) -> dict:
        """Get the current browser tab's title and URL.
        Returns {"title": str, "url": str} or {}.
        """

    @abstractmethod
    async def open_file_explorer(self, path: str) -> None:
        """Open the system file explorer at the given path."""


class ScreenProvider(ABC):
    @abstractmethod
    async def get_active_windows(self) -> list[dict]:
        """Get visible windows: [{"app": str, "title": str, "frontmost": bool}]."""

    @abstractmethod
    async def get_running_apps(self) -> list[str]:
        """Get names of visible running applications."""

    @abstractmethod
    async def take_screenshot(self, display_only: bool = True) -> Optional[str]:
        """Capture a screenshot, return base64-encoded PNG or None."""


class CalendarProvider(ABC):
    @abstractmethod
    async def get_todays_events(self) -> list[dict]:
        """Get today's calendar events."""

    @abstractmethod
    async def get_upcoming_events(self, hours: int = 4) -> list[dict]:
        """Get events in the next N hours."""

    @abstractmethod
    async def get_next_event(self) -> Optional[dict]:
        """Get the single next upcoming event."""

    @abstractmethod
    async def get_calendar_names(self) -> list[str]:
        """Get list of all calendar names."""

    @abstractmethod
    async def refresh_cache(self) -> None:
        """Refresh the event cache."""


class MailProvider(ABC):
    @abstractmethod
    async def get_unread_count(self) -> dict:
        """Get unread counts: {"total": int, "accounts": {name: count}}."""

    @abstractmethod
    async def get_unread_messages(self, count: int = 10) -> list[dict]:
        """Get unread messages: [{"sender", "subject", "date", "read", "preview"}]."""

    @abstractmethod
    async def get_recent_messages(self, count: int = 10) -> list[dict]:
        """Get recent messages from inbox."""

    @abstractmethod
    async def search_mail(self, query: str, count: int = 10) -> list[dict]:
        """Search mail by subject/sender keyword."""

    @abstractmethod
    async def read_message(self, subject_match: str) -> Optional[dict]:
        """Read full content of a message matching subject."""

    @abstractmethod
    async def get_accounts(self) -> list[str]:
        """Get list of configured mail account names."""


class NotesProvider(ABC):
    @abstractmethod
    async def get_recent_notes(self, count: int = 10) -> list[dict]:
        """Get recent notes: [{"title", "date", "folder"}]."""

    @abstractmethod
    async def read_note(self, title_match: str) -> Optional[dict]:
        """Read a note by title: {"title", "body"} or None."""

    @abstractmethod
    async def search_notes(self, query: str, count: int = 5) -> list[dict]:
        """Search notes by title keyword."""

    @abstractmethod
    async def create_note(self, title: str, body: str, folder: str = "Notes") -> bool:
        """Create a new note. Returns True on success."""

    @abstractmethod
    async def get_note_folders(self) -> list[str]:
        """Get list of note folder names."""
