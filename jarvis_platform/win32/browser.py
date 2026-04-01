"""
Windows browser and file explorer automation for JARVIS.
"""

import logging
import os
import subprocess
import webbrowser

log = logging.getLogger("jarvis.browser.win32")


async def open_browser(url: str, browser: str = "chrome") -> dict:
    """Open a URL in the user's browser."""
    try:
        if browser.lower() == "firefox":
            app_name = "Firefox"
            # Try to launch Firefox directly
            try:
                subprocess.Popen(["start", "firefox", url], shell=True)
            except Exception:
                webbrowser.open(url)
        else:
            app_name = "Chrome"
            # Try to launch Chrome directly
            try:
                subprocess.Popen(["start", "chrome", url], shell=True)
            except Exception:
                webbrowser.open(url)

        return {
            "success": True,
            "confirmation": f"Pulled that up in {app_name}, sir.",
        }
    except Exception as e:
        log.error(f"open_browser failed: {e}")
        return {
            "success": False,
            "confirmation": "Had trouble opening the browser, sir.",
        }


async def open_chrome(url: str) -> dict:
    """Backward-compatible Chrome opener."""
    return await open_browser(url, "chrome")


async def get_active_tab_info() -> dict:
    """Get the current browser tab's title and URL.

    On Windows, there's no easy equivalent to AppleScript's Chrome query.
    Returns empty dict — this is a best-effort feature.
    """
    return {}


async def open_file_explorer(path: str) -> None:
    """Open Windows Explorer at the given path."""
    try:
        os.startfile(path)
    except Exception as e:
        log.warning(f"open_file_explorer failed: {e}")
