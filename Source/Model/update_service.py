"""!
********************************************************************************
@file   update_service.py
@brief  check for newer tool version
********************************************************************************
"""

import logging
import requests

from Source.version import __title__, __version__, __owner__, __repo__

log = logging.getLogger(__title__)

I_TIMEOUT = 5
S_UPDATE_URL = f"https://github.com/{__owner__}/{__repo__}/releases/latest"
S_UPDATE_URL_API = f"https://api.github.com/repos/{__owner__}/{__repo__}/releases/latest"


def compare_versions(current_version: str, latest_version: str) -> bool:
    """!
    @brief Compare version for newer status
    @param current_version : current version
    @param latest_version : latest version
    @return status if newer version
    """
    newer_version = None
    l_current_version = current_version.split('.')
    l_latest_version = latest_version.split('.')
    try:
        _all_int = all(isinstance(int(x), int) for x in (l_current_version + l_latest_version))
    except ValueError:
        newer_version = False
        log.debug("Version not int; current: %s; latest: %s", current_version, latest_version)
    else:
        current_parts = list(map(int, l_current_version))
        latest_parts = list(map(int, l_latest_version))
        if current_parts == latest_parts:
            newer_version = False
            log.debug("Current and latest versions are same")
        else:
            for current, latest in zip(current_parts, latest_parts):
                if current > latest:
                    newer_version = False
                    break
                if latest > current:
                    newer_version = True
                    break
            if newer_version is None:
                newer_version = len(latest_parts) > len(current_parts)
    return newer_version


def get_newest_tool_version() -> str | None:
    """!
    @brief Get newest tool version
    @return latest version
    """
    latest_release = None
    try:
        response = requests.get(S_UPDATE_URL_API, timeout=I_TIMEOUT)
    except requests.Timeout:
        pass  # timeout
    except requests.RequestException:
        pass  # request exception
    else:
        if response.status_code == 200:
            latest_release = response.json().get("tag_name", "")
            latest_release = "".join(c for c in latest_release if c.isdigit() or c == ".")
    return latest_release


def get_tool_update_status() -> str | None:
    """!
    @brief Get tool update status
    @return tool status: None: no connection; False: not update required; else newest version
    """
    current_version = __version__
    latest_release = get_newest_tool_version()
    if latest_release is not None:
        b_newer_version = compare_versions(current_version, latest_release)
        update_to_version = latest_release if b_newer_version else False
    else:
        update_to_version = None
    return update_to_version
