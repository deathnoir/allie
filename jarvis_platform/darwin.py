"""
macOS (darwin) platform implementation for JARVIS.

Thin wrapper that re-exports existing macOS-specific modules.
No code is moved — this just imports from the original files.
"""

# Terminal & browser actions
from actions import (
    open_terminal,
    open_browser,
    open_chrome,
    open_claude_in_project,
    prompt_existing_terminal,
    get_chrome_tab_info,
    monitor_build,
    execute_action,
    _generate_project_name,
    _mark_terminal_as_jarvis,
)

# Screen awareness
from screen import (
    get_active_windows,
    get_running_apps,
    take_screenshot,
    describe_screen,
    format_windows_for_context,
)

# Calendar
from calendar_access import (
    get_todays_events,
    get_upcoming_events,
    get_next_event,
    get_calendar_names,
    refresh_cache as refresh_calendar_cache,
    format_events_for_context,
    format_schedule_summary,
)

# Mail (READ-ONLY)
from mail_access import (
    get_unread_count,
    get_unread_messages,
    get_recent_messages,
    get_messages_from_account,
    search_mail,
    read_message,
    get_accounts as get_mail_accounts,
    format_unread_summary,
    format_messages_for_context,
    format_messages_for_voice,
)

# Notes (read + create)
from notes_access import (
    get_recent_notes,
    read_note,
    search_notes_apple as search_notes,
    create_apple_note as create_note,
    get_note_folders,
)


async def focus_terminal_window(project_name: str) -> bool:
    """Bring a Terminal window matching project_name to front (macOS)."""
    import asyncio
    escaped = project_name.replace('"', '\\"')
    script = (
        'tell application "Terminal"\n'
        f'    set targetWindow to first window whose name contains "{escaped}"\n'
        '    set index of targetWindow to 1\n'
        '    activate\n'
        'end tell'
    )
    try:
        proc = await asyncio.create_subprocess_exec(
            "osascript", "-e", script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
        return proc.returncode == 0
    except Exception:
        return False


async def open_file_explorer(path: str) -> None:
    """Open Finder at the given path (macOS)."""
    import asyncio
    escaped = path.replace('"', '\\"')
    script = f'tell application "Finder" to open POSIX file "{escaped}"'
    try:
        proc = await asyncio.create_subprocess_exec(
            "osascript", "-e", script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
    except Exception:
        pass


# Re-export get_chrome_tab_info as get_active_tab_info for the unified interface
get_active_tab_info = get_chrome_tab_info
