"""!
********************************************************************************
@file   income.py
@brief  income
********************************************************************************
"""

import os
import logging
from typing import Optional, Any
from datetime import datetime, timedelta

from Source.version import __title__
from Source.Util.app_data import SCHEMATA_PATH
from Source.Model.data_handler import add_receipt, read_json_files, remove_receipt, EReceiptFields, \
    read_json_file, validate_data, D_RECEIPT_TEMPLATE, get_file_names_in_folder, clean_data, DATE_FORMAT_JSON
from Source.Model.fin_ts import Transaction

log = logging.getLogger(__title__)

INCOME_FOLDER = "income"
INCOME_FILE_PATH = os.path.join(INCOME_FOLDER, "files")
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
    @param rename : whether the file name should be renamed based on receipt data
    """
    add_receipt(income, INCOME_TYPE, os.path.join(path, INCOME_FOLDER), os.path.join(path, INCOME_FILE_PATH), uid=income_id,
                appendix_file=file_path, rename=rename, number_in_title=True, add=add)


def clean_income(path: str) -> None:
    """!
    @brief Clean incomes.
    @param path : data path
    """
    l_data = read_income(path)
    clean_data(path, l_data, INCOME_FOLDER, INCOME_FILE_PATH, EReceiptFields.ID, EReceiptFields.ATTACHMENT)


def check_paid_income(path: str, l_transaction: list[Transaction], b_validate_only: bool = False) -> None:
    """!
    @brief Check income for paid.
    @param path : data path
    @param l_transaction : transactions
    @param b_validate_only : True to only validate, False to update payment date in file
    """
    today = datetime.now()
    l_data = read_income(path)
    for data in l_data:
        bar_paid = data[EReceiptFields.BAR]
        invoice_date = datetime.strptime(data[EReceiptFields.INVOICE_DATE], DATE_FORMAT_JSON)
        if data[EReceiptFields.PAYMENT_DATE]:
            payment_date = datetime.strptime(data[EReceiptFields.PAYMENT_DATE], DATE_FORMAT_JSON)
        else:
            payment_date = None
        amount_gross = data[EReceiptFields.AMOUNT_GROSS]
        invoice_number = data[EReceiptFields.INVOICE_NUMBER]
        if not bar_paid and (amount_gross != 0) and (b_validate_only or not bar_paid) and (b_validate_only or not payment_date):
            payment_date_high = None
            _payment_date_medium = None
            _payment_date_low = None
            for transaction in l_transaction:
                if (transaction.date >= invoice_date) and (transaction.amount == amount_gross):
                    _payment_date_low = transaction.date
                    invoice_number_cut = ''.join(ch for ch in invoice_number if ch.isdigit())
                    purpose_cut = ''.join(ch for ch in transaction.purpose if ch.isdigit())
                    if invoice_number_cut in purpose_cut:
                        _payment_date_medium = transaction.date
                        if (invoice_number in transaction.purpose.split()) and (not b_validate_only or (transaction.date == payment_date)):
                            payment_date_high = transaction.date
                            break
            if b_validate_only:
                if payment_date_high is None:
                    if (payment_date is None) or (payment_date > (today - timedelta(days=1.5 * 365))):
                        print(invoice_number, payment_date, invoice_date, amount_gross, data[EReceiptFields.TRADE_PARTNER])
            else:
                if payment_date_high:
                    data[EReceiptFields.PAYMENT_DATE] = payment_date_high.strftime(DATE_FORMAT_JSON)
                    export_income(path, False, data, data[EReceiptFields.ID])


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
    @param path : get income in this path
    @return list with all income files
    """
    return get_file_names_in_folder(os.path.join(path, INCOME_FILE_PATH))
