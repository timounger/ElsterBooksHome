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
from Source.Model.data_handler import EReceiptFields, EReceiptGroup, fill_data, RECEIPT_TEMPLATE, convert_amount

log = logging.getLogger(__title__)


def check_ust(pdf_path: str) -> bool:
    """!
    @brief Check if document is UST (Umsatzsteuererklärung).
    @param pdf_path : PDF file path
    @return status if document is UST
    """
    with fitz.open(pdf_path) as pdf_document:
        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]
            text = page.get_text()
            if EReceiptGroup.UST.value in text:
                return True
    return False


def import_ust(pdf_path: str, is_income: bool) -> dict[EReceiptFields, Any]:
    """!
    @brief Extract UST (Umsatzsteuererklärung) data from PDF.
    @param pdf_path : PDF file path
    @param is_income : True: is income; False: is expenditure
    @return receipt data
    """
    neg_amount = False
    event = EReceiptGroup.UST.value
    invoice_date = ""
    amount: float | int = 0
    pre_amount = False
    pre_year = False
    tax_office = "Unbekannt"
    with fitz.open(pdf_path) as pdf_document:
        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]
            text = page.get_text()
            lines = text.split('\n')
            for line in lines:
                # print(line)
                if "Erstellungsdatum" in line:
                    parts = line.split()
                    if len(parts) > 1:
                        invoice_date = parts[1]
                elif "Finanzamt:" in line:
                    parts = line.split()
                    if len(parts) > 1:
                        tax_office = parts[1]
                elif pre_amount:
                    parts = line.split()
                    if not parts:
                        continue
                    amount_text = parts[0]
                    amount = convert_amount(amount_text)
                    if amount < 0:
                        neg_amount = True
                    amount = abs(amount)
                    pre_amount = False
                elif pre_year:
                    event += f" {line}"
                    pre_year = False
                elif line == "Minuszeichen voranstellen -":
                    pre_amount = True
                elif line == "Kalenderjahr":
                    pre_year = True

    receipt: dict[EReceiptFields, Any] = {}
    success = is_income == neg_amount
    if success:
        receipt[EReceiptFields.TRADE_PARTNER] = f"FK {tax_office}"
        receipt[EReceiptFields.DESCRIPTION] = event
        receipt[EReceiptFields.INVOICE_DATE] = invoice_date
        receipt[EReceiptFields.AMOUNT_GROSS] = amount
        receipt[EReceiptFields.AMOUNT_NET] = amount
        receipt[EReceiptFields.BAR] = False
        receipt[EReceiptFields.GROUP] = EReceiptGroup.UST
        receipt = fill_data(RECEIPT_TEMPLATE, receipt)
    return receipt
