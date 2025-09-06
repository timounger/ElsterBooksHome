"""!
********************************************************************************
@file   ai_data.py
@brief  General AI data for Ollama and OpenAI
********************************************************************************
"""

import logging
from pydantic import BaseModel

from Source.version import __title__
from Source.Model.data_handler import is_date_format, L_MONTH_NAMES, get_pdf_text
from Source.Model.ocr_recognition import extract_text_with_ocr

log = logging.getLogger(__title__)

I_MAX_DOCUMENT_CHARS = 10000
I_MIN_OCR_TEXT = 20  # OCR integration in PDF requires this length, otherwise use Tesseract


class InvoiceData(BaseModel):
    """!
    @brief Invoice Data model class for AI
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
    @brief Create user message for Ollama request
    @param document_text : document text
    @return user message text
    """
    document_text = document_text[:I_MAX_DOCUMENT_CHARS]

    l_user_message = [
        "You are a helpful assistant. Tell me about document data.",
        "pattern code of invoice_date is: ^[0-9]{2}.[0-9]{2}.[0-9]{4}$",
        "do not answer with pattern code string. Only with a valid date in this format",
        "If not date detected return empty string",
        "For description create maximal 3 words as summary of invoice goods or service",
        "Invoice Text:",
        document_text
    ]

    user_message = "\n".join(l_user_message)
    return user_message


def validate_answer(invoice_data: InvoiceData) -> InvoiceData:
    """!
    @brief Validate invoice data answer and fix if possible
    @param invoice_data : invoice data
    @return invoice data
    """
    if not is_date_format(invoice_data.invoice_date):
        invoice_data.invoice_date = invoice_data.invoice_date.replace(" ", ".")
        for i_month, s_month in enumerate(L_MONTH_NAMES, start=1):
            invoice_data.invoice_date = invoice_data.invoice_date.replace(s_month, str(i_month).zfill(2))
        if not is_date_format(invoice_data.invoice_date):
            invoice_data.invoice_date = ""
    return invoice_data


def get_ai_document_text(file_path: str) -> str:
    """!
    @brief Get text from PDF for AI
    @param file_path : PDF file path
    @return document text
    """
    text = get_pdf_text(file_path)
    if len(text) < I_MIN_OCR_TEXT:
        text = extract_text_with_ocr(file_path)
        if len(text) < I_MIN_OCR_TEXT:
            text = ""
    return text
