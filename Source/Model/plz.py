"""!
********************************************************************************
@file   plz.py
@brief  Get city name from PLZ.
        other GitHub project: https://github.com/mdornseif/pyGeoDb
********************************************************************************
"""

import os
import logging

from Source.version import __title__
from Source.Util.app_data import TOOLS_FOLDER
from Source.Model.data_handler import read_json_file, JSON_TYPE

log = logging.getLogger(__title__)


PLZ_FILE = os.path.join(TOOLS_FOLDER, f"plz{JSON_TYPE}")


def load_plz_mapping() -> dict[str, str]:
    """!
    @brief Load PLZ-to-city mapping from local JSON file.
    @return Dictionary mapping postal codes to city names.
    """
    plz_map = {}
    if os.path.isfile(PLZ_FILE):
        plz_data = read_json_file(PLZ_FILE)
        if plz_data is not None:
            for entry in plz_data:
                plz_codes_str = entry["plz"]
                name = entry["name"]
                if plz_codes_str and name:
                    plz_codes = plz_codes_str.split(",")
                    for plz in plz_codes:
                        plz_map[plz] = name
    return plz_map
