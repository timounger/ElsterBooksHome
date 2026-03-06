"""!
********************************************************************************
@file   income.py
@brief  Manage income records, export, and payment tracking.
********************************************************************************
"""

import os
import logging
from typing import Any
from datetime import datetime, timedelta
from fints.client import Transaction

from Source.version import __title__
from Source.Util.app_data import SCHEMATA_PATH
from Source.Model.data_handler import add_receipt, read_json_files, remove_receipt, EReceiptFields, \
    read_json_file, validate_data, RECEIPT_TEMPLATE, get_file_names_in_folder, clean_data, DATE_FORMAT_JSON

log = logging.getLogger(__title__)

INCOME_FOLDER = "income"
INCOME_FILE_PATH = os.path.join(INCOME_FOLDER, "files")
INCOME_TYPE = "income"
INCOME_SCHEMA_FILE = "income_schema.json"


def validate_income(data: dict[EReceiptFields, Any]) -> list[str]:
    """!
    @brief Validate income data against schema.
    @param data : income data to validate.
    @return List of validation error messages.
    """
    schemata_path = os.path.join(SCHEMATA_PATH, INCOME_SCHEMA_FILE)
    schemata = read_json_file(schemata_path)
    _, errors = validate_data(data, schemata)
    return errors


def read_income(path: str) -> list[dict[EReceiptFields, Any]]:
    """!
    @brief Read all income records.
    @param path : data directory path.
    @return List of income data dictionaries.
    """
    return read_json_files(os.path.join(path, INCOME_FOLDER), RECEIPT_TEMPLATE)


def export_income(path: str, add: bool, income: dict[EReceiptFields, Any], income_id: str | None = None,
                  file_path: str | None = None, rename: bool = False) -> None:
    """!
    @brief Export income record to file.
    @param path : data directory path.
    @param add : whether to git-add the exported file.
    @param income : income data to export.
    @param income_id : unique income identifier.
    @param file_path : receipt attachment file path.
    @param rename : whether to rename the file based on receipt data.
    """
    add_receipt(income, INCOME_TYPE, os.path.join(path, INCOME_FOLDER), os.path.join(path, INCOME_FILE_PATH), uid=income_id,
                appendix_file=file_path, rename=rename, number_in_title=True, add=add)


def clean_income(path: str) -> None:
    """!
    @brief Clean up orphaned income files and data.
    @param path : data directory path.
    """
    incomes = read_income(path)
    clean_data(path, incomes, INCOME_FOLDER, INCOME_FILE_PATH, EReceiptFields.ID, EReceiptFields.ATTACHMENT)


def delete_income(path: str, income_id: str) -> None:
    """!
    @brief Delete an income record and its attachment.
    @param path : data directory path.
    @param income_id : unique income identifier to delete.
    """
    remove_receipt(os.path.join(path, INCOME_FOLDER), os.path.join(path, INCOME_FILE_PATH), income_id)


def get_income_files(path: str) -> list[str]:
    """!
    @brief Get all income attachment file names.
    @param path : data directory path.
    @return List of income attachment file names.
    """
    return get_file_names_in_folder(os.path.join(path, INCOME_FILE_PATH))


def check_paid_income(path: str, transactions: list[Transaction], validate_only: bool = False) -> None:
    """!
    @brief Check and match income payments against bank transactions.
    @param path : data directory path.
    @param transactions : list of bank transactions to match against.
    @param validate_only : True to only validate existing matches, False to update payment dates.
    """
    today = datetime.now()
    incomes = read_income(path)
    for data in incomes:
        bar_paid = data[EReceiptFields.BAR]
        invoice_date = datetime.strptime(data[EReceiptFields.INVOICE_DATE], DATE_FORMAT_JSON)
        if data[EReceiptFields.PAYMENT_DATE]:
            payment_date = datetime.strptime(data[EReceiptFields.PAYMENT_DATE], DATE_FORMAT_JSON)
        else:
            payment_date = None
        amount_gross = data[EReceiptFields.AMOUNT_GROSS]
        invoice_number = data[EReceiptFields.INVOICE_NUMBER]
        if not bar_paid and (amount_gross != 0) and (validate_only or not payment_date):
            payment_date_high = None
            for transaction in transactions:
                if (transaction.date >= invoice_date) and (transaction.amount == amount_gross):
                    invoice_number_cut = ''.join(ch for ch in invoice_number if ch.isdigit())
                    purpose_cut = ''.join(ch for ch in transaction.purpose if ch.isdigit())
                    if invoice_number_cut in purpose_cut:
                        if (invoice_number in transaction.purpose.split()) and (not validate_only or (transaction.date == payment_date)):
                            payment_date_high = transaction.date
                            break
            if validate_only:
                if payment_date_high is None:
                    if (payment_date is None) or (payment_date > (today - timedelta(days=1.5 * 365))):
                        log.debug("Unpaid income: %s %s %s %s %s", invoice_number, payment_date, invoice_date, amount_gross, data[EReceiptFields.TRADE_PARTNER])
            else:
                if payment_date_high:
                    data[EReceiptFields.PAYMENT_DATE] = payment_date_high.strftime(DATE_FORMAT_JSON)
                    export_income(path, False, data, data[EReceiptFields.ID])
