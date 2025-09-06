"""!
********************************************************************************
@file   contacts.py
@brief  contacts
********************************************************************************
"""

import os
import logging
import enum
from typing import Optional, Any

from Source.version import __title__
from Source.Util.app_data import SCHEMATA_PATH
from Source.Model.data_handler import read_json_file, validate_data, read_json_files, \
    add_json, delete_data, fill_data, get_file_name, set_general_json_data

CONTACT_FOLDER = "contacts"
CONTACT_TYPE = "contact"
CONTACT_SCHEMA_FILE = "contact_schema.json"

log = logging.getLogger(__title__)

JSON_VERSION_CONTACT = "02.00.00"
# JSON_VERSION_CONTACT_V1 = "01.00.00" # until 22.06.2025 (changing break)

CONTACT_ADDRESS_FIELD = "address"
CONTACT_CONTACT_FIELD = "contact"


class EContactFields(str, enum.Enum):
    """!
    @brief Contact fields.
    """
    # general
    JSON_TYPE = "json_type"
    JSON_VERSION = "json_version"
    ID = "id"
    # company
    NAME = "name"
    TRADE_NAME = "tradeName"
    CUSTOMER_NUMBER = "customerNumber"
    TRADE_ID = "tradeId"
    VAT_ID = "vatId"
    ELECTRONIC_ADDRESS = "electronicAddress"
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


D_CONTACT_TEMPLATE = {
    EContactFields.JSON_TYPE: "",
    EContactFields.JSON_VERSION: "",
    EContactFields.ID: "",
    EContactFields.NAME: "",  # Unternehmen (BT-44)
    EContactFields.TRADE_NAME: "",  # Handelsname (BT-45)
    EContactFields.CUSTOMER_NUMBER: "",  # Käuferkennung (BT-46)
    EContactFields.TRADE_ID: "",  # Registernummer (BT-47)
    EContactFields.VAT_ID: "",  # Umsatzsteuer-ID (BT-48)
    EContactFields.ELECTRONIC_ADDRESS: "",  # Elektronische Adresse (BT-49)
    CONTACT_ADDRESS_FIELD: {
        EContactFields.STREET_1: "",  # Straße 1 (BT-50)
        EContactFields.STREET_2: "",  # Straße 2 (BT-51)
        EContactFields.PLZ: "",  # PLZ (BT-53)
        EContactFields.CITY: "",  # Ort (BT-52)
        EContactFields.COUNTRY: "DE",  # Land (BT-55) D_COUNTRY_CODE
    },
    CONTACT_CONTACT_FIELD: {
        EContactFields.FIRST_NAME: "",  # Name (BT-56) first
        EContactFields.LAST_NAME: "",  # Name (BT-56) last
        EContactFields.MAIL: "",  # E-Mail (BT-58)
        EContactFields.PHONE: "",  # Telefon (BT-57)
    }
}


def validate_contact(data: dict[EContactFields, Any]) -> list[str]:
    """!
    @brief Validate contact data.
    @param data : data to validate
    @return found error at validation
    """
    schemata_path = os.path.join(SCHEMATA_PATH, CONTACT_SCHEMA_FILE)
    schemata = read_json_file(schemata_path)
    _is_valid, error = validate_data(data, schemata)
    return error


def read_contacts(path: str) -> list[dict[EContactFields, str]]:
    """!
    @brief Read contacts.
    @param path : read in this path
    @return list with existing contacts JSON data
    """
    l_contacts = read_json_files(os.path.join(path, CONTACT_FOLDER), D_CONTACT_TEMPLATE)
    return l_contacts


def add_contact(path: str, add: bool, contact: dict[EContactFields, str],
                contact_id: Optional[str] = None, rename: bool = False) -> None:
    """!
    @brief Add or actualize contact.
    @param path : export to this path
    @param add : GIT add status
    @param contact : contact data to export
    @param contact_id : contact ID
    @param rename : status if file name should renamed depend on actual data
    """
    s_id = set_general_json_data(contact, CONTACT_TYPE, EContactFields.JSON_TYPE,
                                 EContactFields.JSON_VERSION, JSON_VERSION_CONTACT,
                                 EContactFields.ID, contact_id)
    instance = fill_data(D_CONTACT_TEMPLATE, contact)
    title = get_file_name(instance[EContactFields.NAME], s_id)
    id_field = EContactFields.ID if (contact_id is not None) else None
    add_json(add, instance, title, s_id, os.path.join(path, CONTACT_FOLDER), id_field=id_field, rename=rename)


def remove_contact(path: str, contact_id: str) -> None:
    """!
    @brief Remove contact.
    @param path : delete in this path
    @param contact_id : contact ID
    """
    delete_data(os.path.join(path, CONTACT_FOLDER), contact_id, id_field=EContactFields.ID)
