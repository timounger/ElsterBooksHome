"""!
********************************************************************************
@file   ai_data.py
@brief  Data models and prompts for AI-powered invoice data extraction.
********************************************************************************
"""

import logging
from pydantic import BaseModel

from Source.version import __title__
from Source.Model.data_handler import is_date_format, MONTH_NAMES, get_pdf_text
from Source.Model.ocr_recognition import extract_text_with_ocr

log = logging.getLogger(__title__)

MAX_DOCUMENT_CHARS = 10000
MIN_OCR_TEXT = 20  # OCR integration in PDF requires this length, otherwise use Tesseract


class InvoiceData(BaseModel):
    """!
    @brief Invoice data model class for AI extraction.
    """
    invoice_date: str
    invoice_number: str
    gross_amount: float
    net_amount: float
    seller_name: str
    buyer_name: str
    description: str


EMPTY_INVOICE_DATA = InvoiceData(
    invoice_date="",
    invoice_number="",
    gross_amount=0.0,
    net_amount=0.0,
    seller_name="",
    buyer_name="",
    description=""
)


def create_user_message(document_text: str) -> str:
    """!
    @brief Create the AI prompt message with extraction rules for invoice data.
    @param document_text : invoice document text to extract data from.
    @return formatted user message text for AI prompt.
    """
    document_text = document_text[:MAX_DOCUMENT_CHARS]

    parts = [
        "You are a helpful assistant that extracts structured data from invoices.",
        "pattern code of invoice_date is: ^[0-9]{2}.[0-9]{2}.[0-9]{4}$",
        "Do not respond with a pattern code string. Only enter a valid date in this format.",
        "If the date is not detected, return an empty string.",
        "For the description, create a summary of the invoice goods or services in German using a maximum of three words.",
        "Rules for gross_amount and net_amount:",
        "- Extract the exact gross_amount (Brutto) and net_amount (Netto) as stated on the invoice.",
        "- Do NOT calculate or estimate tax. Only use values explicitly written on the invoice.",
        "- If the invoice shows 0% VAT, reverse charge, or tax-exempt amounts, then gross_amount equals net_amount.",
        "- If no separate net amount is stated, set net_amount equal to gross_amount.",
        "Invoice Text:",
        document_text
    ]

    return "\n".join(parts)


def validate_answer(invoice_data: InvoiceData) -> InvoiceData:
    """!
    @brief Validate and normalize AI-extracted invoice data, correcting date formats if possible.
    @param invoice_data : AI-extracted invoice data to validate.
    @return validated and normalized invoice data.
    """
    invoice_data.invoice_date = invoice_data.invoice_date.strip()
    if not is_date_format(invoice_data.invoice_date):
        invoice_data.invoice_date = invoice_data.invoice_date.replace(" ", ".")
        for month, name in enumerate(MONTH_NAMES, start=1):
            invoice_data.invoice_date = invoice_data.invoice_date.replace(name, str(month).zfill(2))
        if not is_date_format(invoice_data.invoice_date):
            invoice_data.invoice_date = ""
    return invoice_data


def get_ai_document_text(file_path: str) -> str:
    """!
    @brief Extract text from PDF for AI processing.
    @param file_path : path to the PDF file.
    @return extracted document text.
    """
    text = get_pdf_text(file_path)
    if len(text) < MIN_OCR_TEXT:
        text = extract_text_with_ocr(file_path)
        if len(text) < MIN_OCR_TEXT:
            text = ""
    return text
