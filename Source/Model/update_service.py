"""!
********************************************************************************
@file   update_service.py
@brief  Check for newer tool version.
********************************************************************************
"""

import json
import logging
import requests
from packaging.version import Version, InvalidVersion

from Source.version import __title__, __version__, __owner__, __repo__

log = logging.getLogger(__title__)

REQUEST_TIMEOUT = 5
UPDATE_API_URL = f"https://api.github.com/repos/{__owner__}/{__repo__}/releases/latest"


def is_newer_version(current_version: str, latest_version: str) -> bool:
    """!
    @brief Check if the latest version is newer than the current version. See https://peps.python.org/pep-0440/
    @param current_version : current version string.
    @param latest_version : latest version string.
    @return True if latest version is newer, False otherwise.
    """
    try:
        return Version(latest_version) > Version(current_version)
    except InvalidVersion:
        log.warning("Version not valid; current: %s; latest: %s", current_version, latest_version)
        return False


def get_latest_tool_version() -> str | None:
    """!
    @brief Get the newest tool version from the GitHub API.
    @return Latest version string or None on failure.
    """
    latest_release = None
    try:
        response = requests.get(UPDATE_API_URL, timeout=REQUEST_TIMEOUT)
    except requests.Timeout:
        log.debug("Update check timed out")
    except requests.RequestException as e:
        log.debug("Update check request failed: %s", e)
    except Exception as e:
        log.debug("Update check failed: %s", e)
    else:
        if response.status_code == 200:
            try:
                tag_name = response.json().get("tag_name", "")
                Version(tag_name)  # validate
            except (json.JSONDecodeError, InvalidVersion):
                pass
            else:
                latest_release = tag_name
    return latest_release


def get_tool_update_status() -> str | None:
    """!
    @brief Get tool update status.
    @return Latest version string if update available, empty string if up-to-date, None on failure.
    """
    latest_release = get_latest_tool_version()
    if latest_release is None:
        return None
    if is_newer_version(__version__, latest_release):
        return latest_release
    return ""
