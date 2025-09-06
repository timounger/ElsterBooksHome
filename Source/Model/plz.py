"""!
********************************************************************************
@file   plz.py
@brief  Get city name from PLZ
        other GitHub project: https://github.com/mdornseif/pyGeoDb
********************************************************************************
"""

import os
import logging
from typing import Any
import requests

from Source.version import __title__
from Source.Util.app_data import TOOLS_FOLDER
from Source.Model.data_handler import write_json_file, read_json_file, JSON_TYPE

log = logging.getLogger(__title__)

B_DOWNLOAD_PLZ = False

PLZ_DATABASE = "https://dev.ratopi.de/opengeodb/DE.tab.json"
PLZ_DIR = TOOLS_FOLDER
PLZ_FILE = os.path.join(PLZ_DIR, f"plz{JSON_TYPE}")
I_TIMEOUT = 2  # timeout to get PLZ data


def download_plz_data() -> Any:
    """!
    @brief Download PLZ data
    @return PLZ data
    """
    try:
        response = requests.get(PLZ_DATABASE, timeout=I_TIMEOUT)
        response.raise_for_status()
        plz_data = response.json()
    except requests.exceptions.RequestException as e:
        log.error("Error occurred: %s", e)
        plz_data = None
    return plz_data


def get_plz_data() -> dict[str, str]:
    """!
    @brief Get PLZ city data. Download if data file not present
    @return PLZ data
    """
    d_plz = {}
    if B_DOWNLOAD_PLZ:
        if os.path.isfile(PLZ_FILE):
            plz_data = download_plz_data()
            if plz_data is not None:
                write_json_file(PLZ_FILE, plz_data)
    if os.path.isfile(PLZ_FILE):
        l_plz_data = read_json_file(PLZ_FILE)
        if l_plz_data is not None:
            for entry in l_plz_data:
                s_plz = entry["plz"]
                name = entry["name"]
                if s_plz and name:
                    l_plz = s_plz.split(",")
                    for plz in l_plz:
                        d_plz[plz] = name
    return d_plz
