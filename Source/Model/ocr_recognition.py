"""!
********************************************************************************
@file   ocr_recognition.py
@brief  OCR recognition
********************************************************************************
"""

import logging
from PIL import Image
from PIL.Image import Image as PILImage
import fitz  # PyMuPDF
from pytesseract import image_to_string
import pytesseract

from Source.version import __title__
from Source.Util.app_data import TOOLS_FOLDER

log = logging.getLogger(__title__)

# https://github.com/tesseract-ocr/tesseract
TESSERACT_EXE = f"{TOOLS_FOLDER}/Tesseract-OCR/tesseract.exe"

pytesseract.pytesseract.tesseract_cmd = TESSERACT_EXE


def convert_pdf_to_images(file: str) -> list[PILImage]:
    """!
    @brief Convert PDF to images
    @param file : file to convert
    @return images for OCR recognition
    """
    pdf_document = fitz.open(file)
    images = []

    for page in pdf_document:
        pix = page.get_pixmap(dpi=300)
        image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        images.append(image)

    return images


def extract_text_with_ocr(pdf_path: str) -> str:
    """!
    @brief Extract text from file
    @param pdf_path : file to extract text
    @return text from ocr recognition
    """
    images = convert_pdf_to_images(pdf_path)
    full_text = ""

    for image in images:
        page_text = image_to_string(image, lang="deu+eng")
        full_text += page_text.strip() + "\n"

    return full_text.strip()
