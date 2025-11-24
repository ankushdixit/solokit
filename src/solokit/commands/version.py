"""
Version command for Solokit CLI.

Displays version information including Solokit version, Python version, and platform.
"""

from __future__ import annotations

import platform
import sys

from solokit.__version__ import __version__
from solokit.core.output import get_output

output = get_output()


def show_version() -> int:
    """
    Display version information.

    Shows:
    - Solokit version
    - Python version
    - Platform/OS

    Returns:
        Exit code (0 for success)

    Examples:
        >>> show_version()
        solokit version 0.1.4
        Python 3.11.7 on Darwin
        0
    """
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    platform_name = platform.system()

    output.info(f"solokit version {__version__}")
    output.info(f"Python {python_version} on {platform_name}")

    return 0


def main() -> int:
    """Main entry point for version command."""
    return show_version()


if __name__ == "__main__":
    sys.exit(main())
