"""!
********************************************************************************
@file   version.py
@brief  Version, build configuration, and feature flags.
********************************************************************************
"""

import sys

# Version
VERSION_MAJOR = 0  # Major changes, breaks API compatibility (e.g. incompatible changes)
VERSION_MINOR = 5  # Minor changes, API compatible (e.g. new feature)
VERSION_PATCH = 0  # Bug fixes
VERSION_BUILD = 0  # Build number (0 = release, >0 = pre-release)

# Project information
__title__ = "ElsterBooks"
__description__ = "Buchhaltungssoftware"
__author__ = "Timo Unger"
__owner__ = "timounger"
__repo__ = "ElsterBooksHome"
__copyright__ = f"Copyright © 2023-2026 {__author__}"
__license__ = "GNU General Public License"
__website__ = f"https://{__owner__}.github.io/{__repo__}"
__home__ = f"https://github.com/{__owner__}/{__repo__}"
__issue__ = f"{__home__}/issues"

# Build configuration
if VERSION_BUILD == 0:
    BUILD_PRERELEASE = False
    __version__ = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}"
else:
    BUILD_PRERELEASE = True
    __version__ = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}.{VERSION_BUILD}"

BUILD_NAME: str | None = None  # Name of current build depending on feature flags


def running_as_exe() -> bool:
    """!
    @brief Check if we are currently running as an executable or directly in Python.
    @return [True|False] running as an EXE
    """
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    return hasattr(sys, "_MEIPASS")


# Git version
GIT_SHORT_SHA: str | None = None  # Git commit SHA (available only in EXE build)

if running_as_exe():
    try:
        from Source.Util.git_version import GIT_SHORT_SHA  # type: ignore  # pylint: disable=unused-import
    except ImportError:
        GIT_SHORT_SHA = None
