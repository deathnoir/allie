"""
Windows screen awareness for JARVIS.

Uses mss for screenshots and pywinauto for window enumeration.
"""

import asyncio
import base64
import io
import logging
from typing import Optional

log = logging.getLogger("jarvis.screen.win32")


async def get_active_windows() -> list[dict]:
    """Get list of visible windows with app name, title, and frontmost status.

    Uses pywinauto UIA backend to enumerate windows.
    Returns list of {"app": str, "title": str, "frontmost": bool}.
    """
    try:
        # Run in executor to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _get_active_windows_sync)
    except Exception as e:
        log.warning(f"get_active_windows error: {e}")
        return []


def _get_active_windows_sync() -> list[dict]:
    """Synchronous window enumeration using win32gui."""
    try:
        import win32gui
        import win32process
        import psutil
    except ImportError:
        log.warning("pywin32/psutil not installed — cannot enumerate windows")
        return []

    foreground_hwnd = win32gui.GetForegroundWindow()
    windows = []

    def enum_callback(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return
        title = win32gui.GetWindowText(hwnd)
        if not title:
            return

        # Get process name
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            proc = psutil.Process(pid)
            app_name = proc.name().replace(".exe", "")
        except Exception:
            app_name = "Unknown"

        windows.append({
            "app": app_name,
            "title": title,
            "frontmost": hwnd == foreground_hwnd,
        })

    win32gui.EnumWindows(enum_callback, None)
    return windows


async def get_running_apps() -> list[str]:
    """Get names of visible running applications."""
    windows = await get_active_windows()
    return list(set(w["app"] for w in windows))


async def take_screenshot(display_only: bool = True) -> Optional[str]:
    """Capture a screenshot and return base64-encoded PNG.

    Uses mss for fast, cross-platform screen capture.
    """
    try:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _take_screenshot_sync, display_only)
    except Exception as e:
        log.warning(f"Screenshot error: {e}")
        return None


def _take_screenshot_sync(display_only: bool = True) -> Optional[str]:
    """Synchronous screenshot capture using mss."""
    try:
        from mss import mss
        from PIL import Image
    except ImportError:
        log.warning("mss/Pillow not installed — cannot take screenshots")
        return None

    try:
        with mss() as sct:
            # monitors[0] is the virtual screen (all monitors combined)
            # monitors[1] is the primary monitor
            monitor = sct.monitors[1] if display_only else sct.monitors[0]
            img = sct.grab(monitor)

            # Convert to PNG via Pillow
            pil_img = Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX")
            buffer = io.BytesIO()
            pil_img.save(buffer, format="PNG")
            png_bytes = buffer.getvalue()

            log.info(f"Screenshot captured: {len(png_bytes)} bytes")
            return base64.b64encode(png_bytes).decode()

    except Exception as e:
        log.warning(f"Screenshot capture failed: {e}")
        return None
