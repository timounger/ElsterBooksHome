"""!
********************************************************************************
@file   ocr_recognition.py
@brief  OCR text extraction from images and PDFs via Tesseract.
********************************************************************************
"""

import logging
from PIL import Image
from PIL.Image import Image as PILImage
import fitz  # PyMuPDF
import pytesseract
from pytesseract import image_to_string

from Source.Util.app_data import TOOLS_FOLDER

log = logging.getLogger(__name__)

# https://github.com/tesseract-ocr/tesseract
TESSERACT_EXE = f"{TOOLS_FOLDER}/Tesseract-OCR/tesseract.exe"

pytesseract.pytesseract.tesseract_cmd = TESSERACT_EXE


def convert_pdf_to_images(file_path: str, max_pages: int = 0) -> list[PILImage]:
    """!
    @brief Convert PDF pages to images.
    @param file_path : PDF file path to convert.
    @param max_pages : Maximum number of pages to convert. 0 for all pages.
    @return List of page images.
    """
    images = []

    with fitz.open(file_path) as pdf_document:
        for i, page in enumerate(pdf_document):
            if max_pages > 0 and i >= max_pages:
                break
            pix = page.get_pixmap(dpi=300)
            image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            images.append(image)

    return images


def extract_text_with_ocr(pdf_path: str, max_pages: int = 0) -> str:
    """!
    @brief Extract text from PDF using OCR.
    @param pdf_path : PDF file path to extract text from.
    @param max_pages : Maximum number of pages to process. 0 for all pages.
    @return Extracted text from OCR recognition.
    """
    images = convert_pdf_to_images(pdf_path, max_pages)
    page_texts = [image_to_string(image, lang="deu+eng").strip() for image in images]
    return "\n".join(page_texts)
