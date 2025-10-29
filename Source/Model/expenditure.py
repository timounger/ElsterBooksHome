"""!
********************************************************************************
@file   expenditure.py
@brief  expenditure
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


def clean_expenditure(path: str) -> None:
    """!
    @brief Clean expenditures.
    @param path : data path
    """
    l_data = read_expenditure(path)
    clean_data(path, l_data, EXPENDITURE_FOLDER, EXPENDITURE_FILE_PATH, EReceiptFields.ID, EReceiptFields.ATTACHMENT)


def check_payed_expenditure(path: str, l_transaction: list[Transaction], b_validate_only: bool = False) -> None:
    """!
    @brief Check expenditure for payed.
    @param path : data path
    @param l_transaction : transactions
    @param b_validate_only : True = validate only; False = write found transaction date to file
    """
    today = datetime.now()
    l_data = read_expenditure(path)
    for data in l_data:
        bar_payed = data[EReceiptFields.BAR]
        invoice_date = datetime.strptime(data[EReceiptFields.INVOICE_DATE], DATE_FORMAT_JSON)
        if data[EReceiptFields.PAYMENT_DATE]:
            payed_date = datetime.strptime(data[EReceiptFields.PAYMENT_DATE], DATE_FORMAT_JSON)
        else:
            payed_date = None
        amount_gross = data[EReceiptFields.AMOUNT_GROSS]
        invoice_number = data[EReceiptFields.INVOICE_NUMBER]
        if not bar_payed and (amount_gross != 0) and (b_validate_only or not bar_payed) and (b_validate_only or not payed_date):
            payed_date_high = None
            payed_date_medium = None
            payed_date_low = None
            for transaction in l_transaction:
                if (transaction.date >= (invoice_date - timedelta(days=14))) and (transaction.amount == -amount_gross):
                    payed_date_low = transaction.date
                    invoice_number_cut = ''.join(ch for ch in invoice_number if ch.isdigit())
                    purpose_cut = ''.join(ch for ch in transaction.purpose if ch.isdigit())
                    if invoice_number_cut in purpose_cut:
                        payed_date_medium = transaction.date
                        if (invoice_number in transaction.purpose.split()) and (not b_validate_only or (transaction.date == payed_date)):
                            if (payed_date is not None) and (payed_date == transaction.date):
                                payed_date_high = transaction.date
                                break
            if b_validate_only:
                if payed_date_high is None:
                    if (payed_date is None) or (payed_date > (today - timedelta(days=1.5 * 365))):
                        print(invoice_number, payed_date, invoice_date, amount_gross, data[EReceiptFields.TRADE_PARTNER], data[EReceiptFields.DESCRIPTION])
                else:
                    print("FOUND", invoice_number, payed_date, invoice_date, amount_gross, data[EReceiptFields.TRADE_PARTNER], data[EReceiptFields.DESCRIPTION])
            else:
                if not b_validate_only:
                    if payed_date_low:
                        data[EReceiptFields.PAYMENT_DATE] = payed_date_high.strftime(DATE_FORMAT_JSON)
                        export_expenditure(path, False, data, data[EReceiptFields.ID])


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
