"""!
********************************************************************************
@file   vat_validation.py
@brief  VAT ID validation using regex and EU VIES web service.
********************************************************************************
"""

import logging
from typing import Any
import re
from zeep import Client

from PyQt6.QtCore import QThread, pyqtSignal

from Source.version import __title__

log = logging.getLogger(__title__)

# Rules for valid VAT IDs: https://de.wikipedia.org/wiki/Umsatzsteuer-Identifikationsnummer
VAT_PATTERNS = {
    'AT': r'^ATU[0-9]{8}$',  # Austria
    'BE': r'^BE[0-9]{9}$',  # Belgium
    'BG': r'^BG[0-9]{9,10}$',  # Bulgaria
    'CY': r'^CY(?!12)[013459][0-9]{7}[A-Z]$',  # Cyprus
    'CZ': r'^CZ[0-9]{8,10}$',  # Czech Republic
    'DE': r'^DE[0-9]{9}$',  # Germany
    'DK': r'^DK[0-9]{8}$',  # Denmark
    'EE': r'^EE[0-9]{9}$',  # Estonia
    'GR': r'^EL[0-9]{9}$',  # Greece
    'ES': r'^ES[A-Z0-9][0-9]{7}[A-Z0-9]$',  # Spain
    'FI': r'^FI[0-9]{8}$',  # Finland
    'FR': r'^FR[A-HJ-NP-Z0-9]{2}[0-9]{9}$',  # France
    'HU': r'^HU[0-9]{8}$',  # Hungary
    'IE': r'^IE(?:[0-9][A-Z]?[0-9]{5}[A-Z]|[0-9]{7}[A-W][A-I])$',  # Ireland
    'IT': r'^IT[0-9]{11}$',  # Italy
    'LT': r'^LT([0-9]{9}|[0-9]{12})$',  # Lithuania
    'LU': r'^LU[0-9]{8}$',  # Luxembourg
    'LV': r'^LV[0-9]{11}$',  # Latvia
    'MT': r'^MT[0-9]{8}$',  # Malta
    'NL': r'^NL[0-9]{9}B[0-9]{2}$',  # Netherlands
    'PL': r'^PL[0-9]{10}$',  # Poland
    'PT': r'^PT[0-9]{9}$',  # Portugal
    'RO': r'^RO[0-9]{2,10}$',  # Romania
    'SE': r'^SE[0-9]{12}$',  # Sweden
    'SI': r'^SI[0-9]{8}$',  # Slovenia
    'SK': r'^SK[0-9]{10}$',  # Slovakia
    'XI': r'^XI[0-9]{9,12}$',  # Northern Ireland
    # Non-EU countries
    'GB': r'^GB([0-9]{9,12}|GD[0-9]{3}|HA[0-9]{3})$',  # UK / Isle of Man
    'SM': r'^SM([0-9]{3}|[0-9]{5})$',  # San Marino
}


def check_vat_format(vat_id: str, pattern: str | None = None) -> bool:
    """!
    @brief Check if VAT ID format is valid for a given country.
    @param vat_id : VAT ID to validate.
    @param pattern : optional regex pattern, overrides default country patterns.
    @return True if valid, False otherwise.
    """
    if pattern:
        return re.match(pattern, vat_id) is not None
    for country_code, country_pattern in VAT_PATTERNS.items():
        if vat_id.startswith(country_code):
            return re.match(country_pattern, vat_id) is not None
    return False


class VatValidation(QThread):
    """!
    @brief Threaded VAT validation using EU VIES service.
    """
    finish_signal = pyqtSignal(dict)

    def __init__(self) -> None:
        super().__init__()
        self.vat_id: str = ""

    def validate_vat(self) -> dict[str, Any]:
        """!
        @brief Validate VAT ID with EU VIES web service.
        @return dict with keys valid/name/address on success, or error on failure.
        """
        vat_result: dict[str, Any] = {}
        wsdl = 'https://ec.europa.eu/taxation_customs/vies/checkVatService.wsdl'

        country_code = self.vat_id[:2]
        vat_number = self.vat_id[2:]

        try:
            # Suppress zeep warning about forcing soap:address to HTTPS
            logging.getLogger('zeep.wsdl.bindings.soap').setLevel(logging.ERROR)
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
            log.warning("VAT validation error for %s: %s", self.vat_id, e)

        return vat_result

    def run(self) -> None:
        """!
        @brief Run VAT validation and emit finish_signal with the result.
        """
        result = self.validate_vat()
        if not self.isInterruptionRequested():
            self.finish_signal.emit(result)
