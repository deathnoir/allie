"""
JARVIS Platform Abstraction — unified interface for macOS and Windows.

Detects the current platform and re-exports the appropriate implementation.
All consumers import from here:

    from jarvis_platform import open_terminal, get_todays_events, ...
"""

import sys

if sys.platform == "darwin":
    from .darwin import *  # noqa: F401,F403
    from .darwin import _generate_project_name, _mark_terminal_as_jarvis  # noqa: F401
elif sys.platform == "win32":
    from .win32 import *  # noqa: F401,F403
    from .win32 import _generate_project_name, _mark_terminal_as_jarvis  # noqa: F401
else:
    raise RuntimeError(
        f"Unsupported platform: {sys.platform}. "
        "JARVIS currently supports macOS (darwin) and Windows (win32)."
    )
