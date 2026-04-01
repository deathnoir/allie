"""
Windows terminal automation for JARVIS.

Uses Windows Terminal (wt.exe) with PowerShell fallback.
Uses pywinauto for window management and keystroke injection.
"""

import asyncio
import logging
import shutil
import subprocess
from pathlib import Path

log = logging.getLogger("jarvis.terminal.win32")

# Check for Windows Terminal at import time
_HAS_WT = shutil.which("wt") is not None


async def _mark_terminal_as_jarvis(revert_after: float = 5.0):
    """Mark the active terminal as JARVIS-controlled via title.

    On Windows, we set the terminal title using escape sequences.
    No revert needed — title resets when the process ends.
    """
    # Title is set during open_terminal via the command itself
    pass


async def open_terminal(command: str = "") -> dict:
    """Open a terminal window and optionally run a command."""
    try:
        if _HAS_WT:
            # Windows Terminal: open a new tab with title
            args = ["wt", "new-tab", "--title", "JARVIS"]
            if command:
                args.extend(["powershell", "-NoExit", "-Command", command])
            else:
                args.extend(["powershell", "-NoExit"])
        else:
            # Fallback: plain PowerShell window
            if command:
                args = ["powershell", "-NoExit", "-Command", command]
            else:
                args = ["powershell", "-NoExit"]

        subprocess.Popen(
            args,
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
        return {
            "success": True,
            "confirmation": "Terminal is open, sir.",
        }
    except Exception as e:
        log.error(f"open_terminal failed: {e}")
        return {
            "success": False,
            "confirmation": "I had trouble opening a terminal, sir.",
        }


async def open_claude_in_project(project_dir: str, prompt: str) -> dict:
    """Open a terminal, cd to project dir, and run Claude Code."""
    # Write prompt to CLAUDE.md — claude reads this automatically
    claude_md = Path(project_dir) / "CLAUDE.md"
    claude_md.write_text(
        f"# Task\n\n{prompt}\n\nBuild this completely. If web app, make index.html work standalone.\n"
    )

    project_name = Path(project_dir).name
    command = f"cd '{project_dir}'; claude --dangerously-skip-permissions"

    try:
        if _HAS_WT:
            args = [
                "wt", "new-tab",
                "--title", f"JARVIS - {project_name}",
                "powershell", "-NoExit", "-Command", command,
            ]
        else:
            args = ["powershell", "-NoExit", "-Command", command]

        subprocess.Popen(
            args,
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
        return {
            "success": True,
            "confirmation": "Claude Code is running in the terminal, sir. You can watch the progress.",
        }
    except Exception as e:
        log.error(f"open_claude_in_project failed: {e}")
        return {
            "success": False,
            "confirmation": "Had trouble spawning Claude Code, sir.",
        }


async def prompt_existing_terminal(project_name: str, prompt: str) -> dict:
    """Find a terminal window matching project_name and type a prompt into it.

    Uses pywinauto to find the window by title and send keystrokes.
    """
    try:
        from pywinauto import Desktop

        desktop = Desktop(backend="uia")
        windows = desktop.windows(title_re=f".*{project_name}.*")

        if not windows:
            return {
                "success": False,
                "confirmation": f"Couldn't find a terminal for {project_name}, sir.",
            }

        win = windows[0]
        win.set_focus()
        await asyncio.sleep(0.5)

        # Send keystrokes — type_keys handles special characters
        win.type_keys(prompt, with_spaces=True, pause=0.02)
        await asyncio.sleep(0.1)
        win.type_keys("{ENTER}")

        return {
            "success": True,
            "confirmation": f"Sent that to {project_name}, sir.",
        }

    except ImportError:
        log.error("pywinauto not installed — cannot control terminal windows")
        return {
            "success": False,
            "confirmation": "Terminal control requires pywinauto, sir. Run pip install pywinauto.",
        }
    except Exception as e:
        log.error(f"prompt_existing_terminal failed: {e}")
        return {
            "success": False,
            "confirmation": f"Had trouble typing into {project_name}, sir.",
        }


async def focus_terminal_window(project_name: str) -> bool:
    """Bring a terminal window matching project_name to the front."""
    try:
        from pywinauto import Desktop

        desktop = Desktop(backend="uia")
        windows = desktop.windows(title_re=f".*{project_name}.*")

        if windows:
            windows[0].set_focus()
            return True
        return False

    except ImportError:
        log.warning("pywinauto not installed — cannot focus windows")
        return False
    except Exception as e:
        log.warning(f"focus_terminal_window failed: {e}")
        return False
