"""!
********************************************************************************
@file   vat_validation.py
@brief  Check VAT ID with VAT ID for free
********************************************************************************
"""

import logging
from typing import Any, Optional
import re
from zeep import Client

from PyQt6.QtCore import QThread, pyqtSignal

from Source.version import __title__

log = logging.getLogger(__title__)

# Rules for valid VAT see: https://de.wikipedia.org/wiki/Umsatzsteuer-Identifikationsnummer
VAT_PATTERNS = {
    'AT': r'^ATU[0-9]{8}$',  # Österreich
    'BE': r'^BE[0-9]{9}$',  # Belgien
    'BG': r'^BG[0-9]{9,10}$',  # Bulgarien
    'CY': r'^CY(?!12)[013459][0-9]{7}[A-Z]$',  # Zypern
    'CZ': r'^CZ[0-9]{8,10}$',  # Tschechien
    'DE': r'^DE[0-9]{9}$',  # Deutschland
    'DK': r'^DK[0-9]{8}$',  # Dänemark
    'EE': r'^EE[0-9]{9}$',  # Estland
    'GR': r'^EL[0-9]{9}$',  # Griechenland
    'ES': r'^ES[A-Z0-9][0-9]{7}[A-Z0-9]$',  # Spanien
    'FI': r'^FI[0-9]{8}$',  # Finnland
    'FR': r'^FR[A-HJ-NP-Z0-9]{2}[0-9]{9}$',  # Frankreich
    'HU': r'^HU[0-9]{8}$',  # Ungarn
    'IE': r'^IE(?:[0-9][A-Z]?[0-9]{5}[A-Z]|[0-9]{7}[A-W][A-I])$',  # Irland
    'IT': r'^IT[0-9]{11}$',  # Italien
    'LT': r'^LT([0-9]{9}|[0-9]{12})$',  # Litauen
    'LU': r'^LU[0-9]{8}$',  # Luxemburg
    'LV': r'^LV[0-9]{11}$',  # Lettland
    'MT': r'^MT[0-9]{8}$',  # Malta
    'NL': r'^NL[0-9]{9}B[0-9]{2}$',  # Niederlande
    'PL': r'^PL[0-9]{10}$',  # Polen
    'PT': r'^PT[0-9]{9}$',  # Portugal
    'RO': r'^RO[0-9]{2,10}$',  # Rumänien
    'SE': r'^SE[0-9]{12}$',  # Schweden
    'SI': r'^SI[0-9]{8}$',  # Slowenien
    'SK': r'^SK[0-9]{10}$',  # Slowakei
    'XI': r'^XI[0-9]{9,12}$',  # Nordirland
    # Nicht EU-Länder
    'GB': r'^GB([0-9]{9,12}|GD[0-9]{3}|HA[0-9]{3})$',  # Vereinigtes Königreich / Isle of Man
    'SM': r'^SM([0-9]{3}|[0-9]{5})$',  # San Marino
}


def check_vat_format(vat_id: str, pattern: Optional[str] = None) -> bool:
    """!
    @brief Check for valid VAT format depend on country
    @param vat_id : VAT id
    @param pattern : check fix pattern else use VAT_PATTERNS
    @return valid vat format
    """
    valid = False
    if pattern:
        if re.match(pattern, vat_id) is not None:
            valid = True
    else:
        for country_code, actual_pattern in VAT_PATTERNS.items():
            if vat_id.startswith(country_code):
                if re.match(actual_pattern, vat_id) is not None:
                    valid = True
                    break
    return valid


class VatValidation(QThread):
    """!
    @brief VAT validation
    """
    finish_signal = pyqtSignal(dict)

    def __init__(self) -> None:
        super().__init__()
        self.vat_id = ""

    def validate_vat(self) -> dict[str, Any] | None:
        """!
        @brief Validate VAT
        @return response status
        """
        vat_result = None
        wsdl = 'http://ec.europa.eu/taxation_customs/vies/checkVatService.wsdl'  # do not use https to prevent warning

        country_code = self.vat_id[:2]
        vat_number = self.vat_id[2:]

        try:
            client = Client(wsdl)
            result = client.service.checkVat(
                countryCode=country_code,
                vatNumber=vat_number
            )
            vat_result = {
                "valid": result.valid,
                "name": result.name,
                "address": result.address
            }
        except Exception as e:
            vat_result = {"error": str(e)}
        return vat_result

    def run(self) -> None:
        """!
        @brief Run VAT validation
        """
        result = self.validate_vat()
        self.finish_signal.emit(result)
