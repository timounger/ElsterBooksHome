"""!
********************************************************************************
@file   company.py
@brief  Handle company data
********************************************************************************
"""

import os
import enum
import logging
from typing import Optional, Any

from Source.version import __title__
from Source.Util.app_data import SCHEMATA_PATH
from Source.Model.data_handler import read_json_file, validate_data, read_json_files, \
    add_json, fill_data, set_general_json_data

log = logging.getLogger(__title__)

JSON_VERSION_COMPANY = "02.01.00"

COMPANY_FOLDER = "company"
COMPANY_TYPE = "company"
COMPANY_SCHEMA_FILE = "company_schema.json"
COMPANY_JSON_FILE = "company_data"

LOGO_BRIEF_PATH = f"{COMPANY_FOLDER}/logo.png"

COMPANY_ADDRESS_FIELD = "address"
COMPANY_CONTACT_FIELD = "contact"
COMPANY_PAYMENT_FIELD = "payment"
COMPANY_BOOKING_FIELD = "booking"
COMPANY_DEFAULT_FIELD = "default"


class ECompanyFields(str, enum.Enum):
    """!
    @brief Company fields.
    """
    JSON_TYPE = "json_type"
    JSON_VERSION = "json_version"
    ID = "id"
    # company
    NAME = "name"
    TRADE_NAME = "tradeName"
    TRADE_ID = "tradeId"
    VAT_ID = "vatId"
    TAX_ID = "taxId"
    LEGAL_INFO = "legalInfo"
    ELECTRONIC_ADDRESS = "electronicAddress"
    WEBSITE_TEXT = "websiteText"
    # address
    STREET_1 = "line1"
    STREET_2 = "line2"
    PLZ = "postCode"
    CITY = "city"
    COUNTRY = "countryCode"
    # contact
    FIRST_NAME = "firstName"
    LAST_NAME = "lastName"
    MAIL = "email"
    PHONE = "phone"
    # payment
    BANK_NAME = "bankName"
    BANK_IBAN = "iban"
    BANK_BIC = "bic"
    BANK_OWNER = "accountName"
    # booking
    SMALL_BUSINESS_REGULATION = "small_business_regulation"  # True: no UST; False: regular with UST
    PROFIT_CALCULATION_CAPITAL = "profit_calculation_capital"  # True: GUV; False: EUR
    AGREED_COST = "agreed_cost"  # True: vereinbarte Entgeld; False: Vereinnahme Entgeld
    TAX_RATES = "tax_rates"  # list with typical tax rates. first used as default
    # default
    QUARTERLY_SALES_TAX = "quarterly_sales_tax"  # True: quarterly UST; False: monthly UST
    PAYED = "payed"  # default payed status for receipt
    BAR_PAYED = "bar_payed"  # default bar payed status for receipt
    INCOME_GROUP = "income_group"  # default income group
    EXPENDITURE_GROUP = "expenditure_group"  # default expenditure group
    GROUPS = "groups"  # receipt groups
    PAYMENT_DAYS = "payment_days"  # payment days
    MAIL_SUBJECT = "mail_subject"  # mail subject
    MAIL_TEXT = "mail_text"  # mail text


DEFAULT_TAX_RATES = [19, 7, 0]
DEFAULT_MAIL_SUBJECT = "Rechnung <Betreff>"
DEFAULT_MAIL_TEXT = """Hallo <Name>,

<Text>

Mit freundlichen Grüßen

[%name%]
[%line1%]
[%postCode%] [%city%]
[%phone%]
"""

D_COMPANY_TEMPLATE = {
    ECompanyFields.JSON_TYPE: "",
    ECompanyFields.JSON_VERSION: "",
    ECompanyFields.ID: "",
    ECompanyFields.NAME: "",  # Unternehmen (BT-27)
    ECompanyFields.TRADE_NAME: "",  # Handelsname (BT-28)
    ECompanyFields.TRADE_ID: "",  # Registernummer (BT-30)
    ECompanyFields.VAT_ID: "",  # Umsatzsteuer-ID (BT-31)
    ECompanyFields.TAX_ID: "",  # Steuernummer (BT-32)
    ECompanyFields.LEGAL_INFO: "",  # Rechtliche Informationen (BT-33)
    ECompanyFields.ELECTRONIC_ADDRESS: "",  # Elektronische Adresse (BT-34)
    ECompanyFields.WEBSITE_TEXT: "",  # Webseite Text
    COMPANY_ADDRESS_FIELD: {
        ECompanyFields.STREET_1: "",  # Straße 1 (BT-35)
        ECompanyFields.STREET_2: "",  # Straße 2 (BT-36)
        ECompanyFields.PLZ: "",  # PLZ (BT-38)
        ECompanyFields.CITY: "",  # Ort (BT-37)
        ECompanyFields.COUNTRY: "DE"  # Land (BT-40) D_COUNTRY_CODE
    },
    COMPANY_CONTACT_FIELD: {
        ECompanyFields.FIRST_NAME: "",  # Name (BT-41) first
        ECompanyFields.LAST_NAME: "",  # Name (BT-41) last
        ECompanyFields.MAIL: "",  # E-Mail (BT-43)
        ECompanyFields.PHONE: ""  # Telefon (BT-42)
    },
    COMPANY_PAYMENT_FIELD: {
        ECompanyFields.BANK_NAME: "",  # Name der Bank
        ECompanyFields.BANK_IBAN: "",  # IBAN (BT-84)
        ECompanyFields.BANK_BIC: "",  # BIC (BT-86)
        ECompanyFields.BANK_OWNER: ""  # Kontoinhaber (BT-85)
    },
    COMPANY_BOOKING_FIELD: {
        ECompanyFields.SMALL_BUSINESS_REGULATION: False,  # True: no UST; False: regular with UST
        ECompanyFields.PROFIT_CALCULATION_CAPITAL: False,  # True: GUV; False: EUR
        ECompanyFields.AGREED_COST: True,  # True: vereinbarte Entgeld; False: Vereinnahme Entgeld
        ECompanyFields.TAX_RATES: DEFAULT_TAX_RATES  # list with typical tax rates. first used as default
    },
    COMPANY_DEFAULT_FIELD: {
        ECompanyFields.QUARTERLY_SALES_TAX: True,  # True: quarterly UST; False: monthly UST
        ECompanyFields.PAYED: False,  # default payed status for receipt
        ECompanyFields.BAR_PAYED: False,  # default bar payed status for receipt
        ECompanyFields.INCOME_GROUP: "",  # default income group
        ECompanyFields.EXPENDITURE_GROUP: "",  # default expenditure group
        ECompanyFields.GROUPS: [],  # receipt groups
        ECompanyFields.PAYMENT_DAYS: 14,  # payment days
        ECompanyFields.MAIL_SUBJECT: DEFAULT_MAIL_SUBJECT,  # mail subject
        ECompanyFields.MAIL_TEXT: DEFAULT_MAIL_TEXT  # mail text
    }
}


def validate_company(data: dict[str, Any]) -> list[str]:
    """!
    @brief Validate company data.
    @param data : data to validate
    @return found error at validation
    """
    schemata_path = os.path.join(SCHEMATA_PATH, COMPANY_SCHEMA_FILE)
    schemata = read_json_file(schemata_path)
    _is_valid, error = validate_data(data, schemata)
    return error


def read_company(path: str) -> dict[Any, Any] | None:
    """!
    @brief Read company.
    @param path : read in this path
    @return company data
    """
    l_company = read_json_files(os.path.join(path, COMPANY_FOLDER), D_COMPANY_TEMPLATE)
    company = l_company[0] if (len(l_company) > 0) else None  # only one company data possible
    return company


def add_company(path: str, add: bool, company: dict[Any, Any], company_id: Optional[str] = None, rename: bool = False) -> None:
    """!
    @brief Add or actualize company data.
    @param path : export to this path
    @param add : GIT add status
    @param company : contact data to export
    @param company_id : contact ID
    @param rename : status if file name should renamed depend on actual data
    """
    s_id = set_general_json_data(company, COMPANY_TYPE, ECompanyFields.JSON_TYPE,
                                 ECompanyFields.JSON_VERSION, JSON_VERSION_COMPANY,
                                 ECompanyFields.ID, company_id)
    instance = fill_data(D_COMPANY_TEMPLATE, company)
    id_field = ECompanyFields.ID if (company_id is not None) else None
    add_json(add, instance, COMPANY_JSON_FILE, s_id, os.path.join(path, COMPANY_FOLDER), id_field=id_field, rename=rename)
