"""!
********************************************************************************
@file   income.py
@brief  income
********************************************************************************
"""

import os
import logging
from typing import Optional, Any

from Source.version import __title__
from Source.Util.app_data import SCHEMATA_PATH
from Source.Model.data_handler import add_receipt, read_json_files, remove_receipt, EReceiptFields, \
    read_json_file, validate_data, D_RECEIPT_TEMPLATE, get_file_names_in_folder

log = logging.getLogger(__title__)

INCOME_FOLDER = "income"
INCOME_FILE_PATH = INCOME_FOLDER + "/files"
INCOME_TYPE = "income"
INCOME_SCHEMA_FILE = "income_schema.json"


def validate_income(data: dict[EReceiptFields, Any]) -> list[str]:
    """!
    @brief Validate income data.
    @param data : data to validate
    @return found error at validation
    """
    schemata_path = os.path.join(SCHEMATA_PATH, INCOME_SCHEMA_FILE)
    schemata = read_json_file(schemata_path)
    _is_valid, error = validate_data(data, schemata)
    return error


def read_income(path: str) -> list[dict[EReceiptFields, Any]]:
    """!
    @brief Read all incomes.
    @param path : read in this path
    @return list with existing income JSON data
    """
    l_income = read_json_files(os.path.join(path, INCOME_FOLDER), D_RECEIPT_TEMPLATE)
    return l_income


def export_income(path: str, add: bool, income: dict[EReceiptFields, Any], income_id: Optional[str] = None,
                  file_path: Optional[str] = None, rename: bool = False) -> None:
    """!
    @brief Export income.
    @param path : export to this path
    @param add : GIT add status
    @param income : income data to export
    @param income_id : income ID
    @param file_path : receipt file
    @param rename : status if file name should renamed depend on actual data
    """
    add_receipt(income, INCOME_TYPE, os.path.join(path, INCOME_FOLDER), os.path.join(path, INCOME_FILE_PATH), uid=income_id,
                appendix_file=file_path, rename=rename, number_in_title=True, add=add)


def delete_income(path: str, income_id: str) -> None:
    """!
    @brief Delete income.
    @param path : delete in this path
    @param income_id : income ID
    """
    remove_receipt(os.path.join(path, INCOME_FOLDER), os.path.join(path, INCOME_FILE_PATH), income_id)


def get_income_files(path: str) -> list[str]:
    """!
    @brief Get income files.
    @param path : get expenditure in this path
    @return list with all income files
    """
    return get_file_names_in_folder(os.path.join(path, INCOME_FILE_PATH))
