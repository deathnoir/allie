"""
Windows (win32) platform implementation for JARVIS.

Re-exports all platform functions from Windows-specific modules.
"""

import os
from pathlib import Path
from urllib.parse import quote

# Terminal & browser actions
from .terminal import (
    open_terminal,
    open_claude_in_project,
    prompt_existing_terminal,
    focus_terminal_window,
    _mark_terminal_as_jarvis,
)
from .browser import (
    open_browser,
    open_chrome,
    open_file_explorer,
    get_active_tab_info,
)

# Screen awareness
from .screen import (
    get_active_windows,
    get_running_apps,
    take_screenshot,
)

# Calendar (Google Calendar API)
from .calendar import (
    get_todays_events,
    get_upcoming_events,
    get_next_event,
    get_calendar_names,
    refresh_calendar_cache,
)

# Mail (Gmail API — READ-ONLY)
from .mail import (
    get_unread_count,
    get_unread_messages,
    get_recent_messages,
    get_messages_from_account,
    search_mail,
    read_message,
    get_mail_accounts,
)

# Notes (local SQLite)
from .notes import (
    get_recent_notes,
    read_note,
    search_notes,
    create_note,
    get_note_folders,
)

# Cross-platform format helpers (pure Python, no platform calls at import)
from screen import describe_screen, format_windows_for_context
from calendar_access import format_events_for_context, format_schedule_summary
from mail_access import (
    format_unread_summary,
    format_messages_for_context,
    format_messages_for_voice,
)

# Re-export cross-platform utilities from actions
from actions import _generate_project_name, monitor_build

def _find_desktop_path() -> Path:
    """Find the actual Desktop path, handling OneDrive redirection."""
    for candidate in [
        Path.home() / "OneDrive" / "Desktop",
        Path.home() / "Desktop",
    ]:
        if candidate.exists():
            return candidate
    return Path.home() / "Desktop"

DESKTOP_PATH = _find_desktop_path()


async def execute_action(intent: dict, projects: list = None) -> dict:
    """Route a classified intent to the right action function (Windows version).

    Uses Windows-native terminal and browser implementations.
    """
    action = intent.get("action", "chat")
    target = intent.get("target", "")

    if action == "open_terminal":
        result = await open_terminal("claude --dangerously-skip-permissions")
        result["project_dir"] = None
        return result

    elif action == "browse":
        if target.startswith("http://") or target.startswith("https://"):
            url = target
        else:
            url = f"https://www.google.com/search?q={quote(target)}"

        target_lower = target.lower()
        browser = "firefox" if "firefox" in target_lower else "chrome"

        result = await open_browser(url, browser)
        result["project_dir"] = None
        return result

    elif action == "build":
        project_name = _generate_project_name(target)
        project_dir = str(DESKTOP_PATH / project_name)
        os.makedirs(project_dir, exist_ok=True)
        result = await open_claude_in_project(project_dir, target)
        result["project_dir"] = project_dir
        return result

    else:
        return {"success": False, "confirmation": "", "project_dir": None}
