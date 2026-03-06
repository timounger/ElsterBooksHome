"""!
********************************************************************************
@file   expenditure.py
@brief  Manage expenditure records, export, and payment tracking
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

EXPENDITURE_FOLDER = "expenditure"
EXPENDITURE_FILE_PATH = os.path.join(EXPENDITURE_FOLDER, "files")
EXPENDITURE_TYPE = "expenditure"
EXPENDITURE_SCHEMA_FILE = "expenditure_schema.json"


def validate_expenditure(data: dict[EReceiptFields, Any]) -> list[str]:
    """!
    @brief Validate expenditure data against schema.
    @param data : expenditure data to validate.
    @return List of validation error messages.
    """
    schemata_path = os.path.join(SCHEMATA_PATH, EXPENDITURE_SCHEMA_FILE)
    schemata = read_json_file(schemata_path)
    _, errors = validate_data(data, schemata)
    return errors


def read_expenditure(path: str) -> list[dict[EReceiptFields, Any]]:
    """!
    @brief Read all expenditure records.
    @param path : data directory path.
    @return List of expenditure data dictionaries.
    """
    return read_json_files(os.path.join(path, EXPENDITURE_FOLDER), RECEIPT_TEMPLATE)


def export_expenditure(path: str, add: bool, expenditure: dict[EReceiptFields, Any], expenditure_id: str | None = None,
                       file_path: str | None = None, rename: bool = False) -> None:
    """!
    @brief Export expenditure record to file.
    @param path : data directory path.
    @param add : whether to git-add the exported file.
    @param expenditure : expenditure data to export.
    @param expenditure_id : unique expenditure identifier.
    @param file_path : receipt attachment file path.
    @param rename : whether to rename the file based on receipt data.
    """
    add_receipt(expenditure, EXPENDITURE_TYPE, os.path.join(path, EXPENDITURE_FOLDER), os.path.join(path, EXPENDITURE_FILE_PATH), uid=expenditure_id,
                appendix_file=file_path, rename=rename, add=add)


def clean_expenditure(path: str) -> None:
    """!
    @brief Clean up orphaned expenditure files and data.
    @param path : data directory path.
    """
    expenditures = read_expenditure(path)
    clean_data(path, expenditures, EXPENDITURE_FOLDER, EXPENDITURE_FILE_PATH, EReceiptFields.ID, EReceiptFields.ATTACHMENT)


def delete_expenditure(path: str, expenditure_id: str) -> None:
    """!
    @brief Delete an expenditure record and its attachment.
    @param path : data directory path.
    @param expenditure_id : unique expenditure identifier to delete.
    """
    remove_receipt(os.path.join(path, EXPENDITURE_FOLDER), os.path.join(path, EXPENDITURE_FILE_PATH), expenditure_id)


def get_expenditure_files(path: str) -> list[str]:
    """!
    @brief Get all expenditure attachment file names.
    @param path : data directory path.
    @return List of expenditure attachment file names.
    """
    return get_file_names_in_folder(os.path.join(path, EXPENDITURE_FILE_PATH))


def check_paid_expenditure(path: str, transactions: list[Transaction], validate_only: bool = False) -> None:
    """!
    @brief Check and match expenditure payments against bank transactions.
    @param path : data directory path.
    @param transactions : list of bank transactions to match against.
    @param validate_only : True to only validate existing matches, False to update payment dates.
    """
    today = datetime.now()
    expenditures = read_expenditure(path)
    for data in expenditures:
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
            payment_date_low = None
            for transaction in transactions:
                if (transaction.date >= (invoice_date - timedelta(days=14))) and (transaction.amount == -amount_gross):
                    payment_date_low = transaction.date
                    invoice_number_cut = ''.join(ch for ch in invoice_number if ch.isdigit())
                    purpose_cut = ''.join(ch for ch in transaction.purpose if ch.isdigit())
                    if invoice_number_cut in purpose_cut:
                        if (invoice_number in transaction.purpose.split()) and (not validate_only or (transaction.date == payment_date)):
                            if (payment_date is not None) and (payment_date == transaction.date):
                                payment_date_high = transaction.date
                                break
            if validate_only:
                if payment_date_high is None:
                    if (payment_date is None) or (payment_date > (today - timedelta(days=1.5 * 365))):
                        log.debug("Unpaid expenditure: %s %s %s %s %s %s", invoice_number, payment_date, invoice_date,
                                  amount_gross, data[EReceiptFields.TRADE_PARTNER], data[EReceiptFields.DESCRIPTION])
                else:
                    log.debug("Found expenditure: %s %s %s %s %s %s", invoice_number, payment_date, invoice_date,
                              amount_gross, data[EReceiptFields.TRADE_PARTNER], data[EReceiptFields.DESCRIPTION])
            else:
                if payment_date_low:
                    data[EReceiptFields.PAYMENT_DATE] = payment_date_low.strftime(DATE_FORMAT_JSON)
                    export_expenditure(path, False, data, data[EReceiptFields.ID])
