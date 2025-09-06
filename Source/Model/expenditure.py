"""!
********************************************************************************
@file   expenditure.py
@brief  expenditure
********************************************************************************
"""

import os
import logging
from typing import Optional, Any

from Source.version import __title__
from Source.Util.app_data import SCHEMATA_PATH
from Source.Model.data_handler import read_json_files, remove_receipt, EReceiptFields, \
    read_json_file, validate_data, D_RECEIPT_TEMPLATE, add_receipt, get_file_names_in_folder

log = logging.getLogger(__title__)

EXPENDITURE_FOLDER = "expenditure"
EXPENDITURE_FILE_PATH = EXPENDITURE_FOLDER + "/files"
EXPENDITURE_TYPE = "expenditure"
EXPENDITURE_SCHEMA_FILE = "expenditure_schema.json"


def validate_expenditure(data: dict[EReceiptFields, Any]) -> list[str]:
    """!
    @brief Validate expenditure data.
    @param data : data to validate
    @return found error at validation
    """
    schemata_path = os.path.join(SCHEMATA_PATH, EXPENDITURE_SCHEMA_FILE)
    schemata = read_json_file(schemata_path)
    _is_valid, error = validate_data(data, schemata)
    return error


def read_expenditure(path: str) -> list[dict[EReceiptFields, Any]]:
    """!
    @brief Read all expenditures.
    @param path : read in this path
    @return list with existing expenditures JSON data
    """
    l_expenditure = read_json_files(os.path.join(path, EXPENDITURE_FOLDER), D_RECEIPT_TEMPLATE)
    return l_expenditure


def export_expenditure(path: str, add: bool, expenditure: dict[EReceiptFields, Any], expenditure_id: Optional[str] = None,
                       file_path: Optional[str] = None, rename: bool = False) -> None:
    """!
    @brief Export expenditure.
    @param path : export to this path
    @param add : GIT add status
    @param expenditure : expenditure data to export
    @param expenditure_id : expenditure ID
    @param file_path : receipt file
    @param rename : status if file name should renamed depend on actual data
    """
    add_receipt(expenditure, EXPENDITURE_TYPE, os.path.join(path, EXPENDITURE_FOLDER), os.path.join(path, EXPENDITURE_FILE_PATH), uid=expenditure_id,
                appendix_file=file_path, rename=rename, add=add)


def delete_expenditure(path: str, expenditure_id: str) -> None:
    """!
    @brief Delete expenditure.
    @param path : delete in this path
    @param expenditure_id : expenditure ID
    """
    remove_receipt(os.path.join(path, EXPENDITURE_FOLDER), os.path.join(path, EXPENDITURE_FILE_PATH), expenditure_id)


def get_expenditure_files(path: str) -> list[str]:
    """!
    @brief Get expenditure files.
    @param path : get expenditure in this path
    @return list with all expenditure files
    """
    return get_file_names_in_folder(os.path.join(path, EXPENDITURE_FILE_PATH))
