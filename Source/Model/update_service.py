"""!
********************************************************************************
@file   update_service.py
@brief  check for newer tool version
********************************************************************************
"""

import logging
import requests
from packaging.version import Version, InvalidVersion

from Source.version import __title__, __version__, __owner__, __repo__

log = logging.getLogger(__title__)

I_TIMEOUT = 5
S_UPDATE_URL_API = f"https://api.github.com/repos/{__owner__}/{__repo__}/releases/latest"


def compare_versions(current_version: str, latest_version: str) -> bool:
    """!
    @brief Compare version for newer status. See https://peps.python.org/pep-0440/
    @param current_version : current version
    @param latest_version : latest version
    @return status if newer version
    """
    newer_version = False
    try:
        current = Version(current_version)
        latest = Version(latest_version)
    except InvalidVersion:
        log.warning("Version not valid; current: %s; latest: %s", current_version, latest_version)
        newer_version = False
    else:
        newer_version = bool(latest > current)
    return newer_version


def get_newest_tool_version() -> str | None:
    """!
    @brief Get newest tool version
    @return latest version or None for no connection or invalid version string
    """
    latest_release = None
    try:
        response = requests.get(S_UPDATE_URL_API, timeout=I_TIMEOUT)
    except requests.Timeout:
        pass  # timeout
    except requests.RequestException:
        pass  # request exception
    except Exception:
        pass  # unknown exception
    else:
        if response.status_code == 200:
            tag_name = response.json().get("tag_name", "")
            try:
                Version(tag_name)  # validate
            except InvalidVersion:
                latest_release = None
            else:
                latest_release = tag_name
    return latest_release


def get_tool_update_status() -> str | None:
    """!
    @brief Get tool update status
    @return tool status: None: no connection; False: not update required; else newest version
    """
    latest_release = get_newest_tool_version()
    if latest_release is not None:
        b_newer_version = compare_versions(__version__, latest_release)
        update_to_version = latest_release if b_newer_version else False
    else:
        update_to_version = None
    return update_to_version
