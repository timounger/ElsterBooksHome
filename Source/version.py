"""!
********************************************************************************
@file   version.py
@brief  Version and general information
********************************************************************************
"""

import sys
from typing import Optional

# Version
VERSION_MAJOR = 0  # major changes/breaks at API (e.g incompatibility)
VERSION_MINOR = 3  # minor changes/does not break the API (e.g new feature)
VERSION_PATCH = 0  # Bug fixes
VERSION_BUILD = 0  # build number (if available)

__title__ = "ElsterBooks"
__description__ = "Buchhaltungssoftware"
__author__ = "Timo Unger"
__owner__ = "timounger"
__repo__ = "ElsterBooksHome"
__copyright__ = f"Copyright © 2023-2025 {__author__}"
__license__ = "GNU General Public License"
__home__ = f"https://{__owner__}.github.io/{__repo__}"
__issue__ = f"https://github.com/{__owner__}/{__repo__}/issues"

if VERSION_BUILD == 0:
    if VERSION_MAJOR != 0:
        PRERELEASE_BUILD = False
    else:
        PRERELEASE_BUILD = True
    __version__ = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}"
else:
    PRERELEASE_BUILD = True
    __version__ = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}.{VERSION_BUILD}"

DISK_TYPE = ""
DISK_MODEL = ""
DISK_SERIAL_NUMBER = ""


BUILD_NAME: str | None = None
BUILD_NAME = "Test User"
FEAT_AUTO_SERVICE = True


def running_as_exe() -> bool:
    """!
    @brief Check if we are currently running as an executable or directly in Python
    @return [True|False] running as an EXE
    """
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    return bool(hasattr(sys, "_MEIPASS"))


GIT_SHORT_SHA: Optional[str] = None

if running_as_exe():
    try:
        from Source.Util.git_version import GIT_SHORT_SHA  # type: ignore  # pylint: disable=unused-import
    except ImportError:
        GIT_SHORT_SHA = None
