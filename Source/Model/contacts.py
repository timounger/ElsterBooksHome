"""!
********************************************************************************
@file   contacts.py
@brief  Manage contact data persistence and validation.
********************************************************************************
"""

import os
import logging
import enum
from typing import Any

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
    @brief Contact data field identifiers.
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


CONTACT_TEMPLATE = {
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
        EContactFields.COUNTRY: "DE",  # Land (BT-55)
    },
    CONTACT_CONTACT_FIELD: {
        EContactFields.FIRST_NAME: "",  # Name (BT-56) first
        EContactFields.LAST_NAME: "",  # Name (BT-56) last
        EContactFields.MAIL: "",  # E-Mail (BT-58)
        EContactFields.PHONE: "",  # Telefon (BT-57)
    }
}


def validate_contact(data: dict[EContactFields | str, Any]) -> list[str]:
    """!
    @brief Validate contact data against schema.
    @param data : contact data to validate.
    @return List of validation error messages.
    """
    schemata_path = os.path.join(SCHEMATA_PATH, CONTACT_SCHEMA_FILE)
    schemata = read_json_file(schemata_path)
    _, errors = validate_data(data, schemata)
    return errors


def read_contacts(path: str) -> list[dict[EContactFields | str, Any]]:
    """!
    @brief Read all contact records.
    @param path : data directory path.
    @return List of contact data dictionaries.
    """
    return read_json_files(os.path.join(path, CONTACT_FOLDER), CONTACT_TEMPLATE)


def add_contact(path: str, add: bool, contact: dict[EContactFields | str, Any],
                contact_id: str | None = None, rename: bool = False) -> None:
    """!
    @brief Add or update contact data.
    @param path : data directory path.
    @param add : whether to git-add the exported file.
    @param contact : contact data to export.
    @param contact_id : unique contact identifier.
    @param rename : whether to rename the file based on contact data.
    """
    uid = set_general_json_data(contact, CONTACT_TYPE, EContactFields.JSON_TYPE,
                                EContactFields.JSON_VERSION, JSON_VERSION_CONTACT,
                                EContactFields.ID, contact_id)
    instance = fill_data(CONTACT_TEMPLATE, contact)
    title = get_file_name(instance[EContactFields.NAME], uid)
    id_field = EContactFields.ID if (contact_id is not None) else None
    add_json(add, instance, title, uid, os.path.join(path, CONTACT_FOLDER), id_field=id_field, rename=rename)


def remove_contact(path: str, contact_id: str) -> None:
    """!
    @brief Remove contact data.
    @param path : data directory path.
    @param contact_id : unique contact identifier to delete.
    """
    delete_data(os.path.join(path, CONTACT_FOLDER), contact_id, id_field=EContactFields.ID)
