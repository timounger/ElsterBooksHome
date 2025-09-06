"""!
********************************************************************************
@file   ust_import.py
@brief  Import Ust from PDF.
********************************************************************************
"""

import logging
from typing import Any
import fitz  # PyMuPDF

from Source.version import __title__
from Source.Model.data_handler import EReceiptFields, EReceiptGroup, fill_data, D_RECEIPT_TEMPLATE, convert_amount

log = logging.getLogger(__title__)


def check_ust(pdf_path: str) -> bool:
    """!
    @brief Check if document is pre tax
    @param pdf_path : PDF file path
    @return status if document is pre tax
    """
    b_is_pre_tax = False
    with fitz.open(pdf_path) as pdf_document:
        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]
            text = page.get_text()
            if EReceiptGroup.UST.value in text:
                b_is_pre_tax = True
                break
    return b_is_pre_tax


def import_ust(pdf_path: str, is_income: bool) -> dict[EReceiptFields, Any]:
    """!
    @brief Read items from PDF file
    @param pdf_path : PDF file path
    @param is_income : True: is income; False: is expenditure
    @return data
    """
    b_neg_amount = False
    event = EReceiptGroup.UST.value
    invoice_date = ""
    amount: float | int = 0
    b_pre_amount = False
    b_pre_year = False
    tax_office = "Unbekannt"
    with fitz.open(pdf_path) as pdf_document:
        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]
            text = page.get_text()
            lines = text.split('\n')
            for _i, line in enumerate(lines):
                # print(line)
                if "Erstellungsdatum" in line:
                    invoice_date = line.split()[1]
                elif "Finanzamt:" in line:
                    tax_office = line.split()[1]
                elif b_pre_amount:
                    s_amount = line.split()[0]
                    amount = convert_amount(s_amount)
                    if amount < 0:
                        b_neg_amount = True
                    amount = abs(amount)
                    b_pre_amount = False
                elif b_pre_year:
                    event += f" {line}"
                    b_pre_year = False
                elif line == "Minuszeichen voranstellen -":
                    b_pre_amount = True
                elif line == "Kalenderjahr":
                    b_pre_year = True

    receipt: dict[EReceiptFields, Any] = {}
    b_success = bool(is_income == b_neg_amount)
    if b_success:
        receipt[EReceiptFields.TRADE_PARTNER] = f"FK {tax_office}"
        receipt[EReceiptFields.DESCRIPTION] = event
        receipt[EReceiptFields.INVOICE_DATE] = invoice_date
        receipt[EReceiptFields.AMOUNT_GROSS] = amount
        receipt[EReceiptFields.AMOUNT_NET] = amount
        receipt[EReceiptFields.BAR] = False
        receipt[EReceiptFields.GROUP] = EReceiptGroup.UST
        receipt = fill_data(D_RECEIPT_TEMPLATE, receipt)
    return receipt
