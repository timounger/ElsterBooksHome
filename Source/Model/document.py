"""!
********************************************************************************
@file   document.py
@brief  Manage document data persistence and validation.
********************************************************************************
"""

import os
import logging
import enum
from typing import Any

from Source.version import __title__
from Source.Util.app_data import SCHEMATA_PATH
from Source.Model.data_handler import read_json_files, get_file_names_in_folder, validate_data, read_json_file, \
    set_general_json_data, fill_data, get_file_name, add_json, add_appendix, get_date_title, delete_data, PDF_TYPE, \
    clean_data

log = logging.getLogger(__title__)

JSON_VERSION_DOCUMENT = "01.00.00"

DOCUMENT_FOLDER = "document"
DOCUMENT_FILE_PATH = os.path.join(DOCUMENT_FOLDER, "files")
DOCUMENT_TYPE = "document"
DOCUMENT_SCHEMA_FILE = "document_schema.json"


class EDocumentFields(str, enum.Enum):
    """!
    @brief Document data field identifiers.
    """
    JSON_TYPE = "json_type"
    JSON_VERSION = "json_version"
    ID = "id"
    DESCRIPTION = "description"
    DOCUMENT_DATE = "document_date"
    ATTACHMENT = "attachment"


DOCUMENT_TEMPLATE = {
    EDocumentFields.JSON_TYPE: "",
    EDocumentFields.JSON_VERSION: "",
    EDocumentFields.ID: "",
    EDocumentFields.DESCRIPTION: "",
    EDocumentFields.DOCUMENT_DATE: "",
    EDocumentFields.ATTACHMENT: ""
}


def validate_document(data: dict[EDocumentFields, Any]) -> list[str]:
    """!
    @brief Validate document data against schema.
    @param data : document data to validate.
    @return List of validation error messages.
    """
    schemata_path = os.path.join(SCHEMATA_PATH, DOCUMENT_SCHEMA_FILE)
    schemata = read_json_file(schemata_path)
    _, errors = validate_data(data, schemata)
    return errors


def read_document(path: str) -> list[dict[EDocumentFields, str]]:
    """!
    @brief Read all document records.
    @param path : data directory path.
    @return List of document data dictionaries.
    """
    return read_json_files(os.path.join(path, DOCUMENT_FOLDER), DOCUMENT_TEMPLATE)


def add_document(path: str, add: bool, document_data: dict[EDocumentFields, str], document_id: str | None = None,
                 appendix_file: str | None = None, rename: bool = False) -> None:
    """!
    @brief Add or update document data and attachment.
    @param path : data directory path.
    @param add : whether to git-add the exported file.
    @param document_data : document data to export.
    @param document_id : unique document identifier.
    @param appendix_file : document attachment file path.
    @param rename : whether to rename the file based on document data.
    """
    uid = set_general_json_data(document_data, DOCUMENT_TYPE, EDocumentFields.JSON_TYPE,
                                EDocumentFields.JSON_VERSION, JSON_VERSION_DOCUMENT,
                                EDocumentFields.ID, document_id)
    date = document_data[EDocumentFields.DOCUMENT_DATE]
    title = get_file_name([get_date_title(date), document_data[EDocumentFields.DESCRIPTION]], uid)
    if (appendix_file is not None) or rename:
        if appendix_file is None:
            if document_data[EDocumentFields.ATTACHMENT]:
                _, file_extension = os.path.splitext(document_data[EDocumentFields.ATTACHMENT])
            else:
                file_extension = PDF_TYPE  # compatibility with old version without existing attachment
        else:
            _, file_extension = os.path.splitext(appendix_file)
        file_extension = file_extension.lower()
        document_data[EDocumentFields.ATTACHMENT] = f"{title}{file_extension}"
    id_field = EDocumentFields.ID if (document_id is not None) else None
    instance = fill_data(DOCUMENT_TEMPLATE, document_data)
    add_json(add, instance, title, uid, os.path.join(path, DOCUMENT_FOLDER), id_field=id_field, rename=rename)
    if (appendix_file is not None) or rename:
        add_appendix(title, uid, os.path.join(path, DOCUMENT_FILE_PATH), add, appendix_file=appendix_file)


def clean_documents(path: str) -> None:
    """!
    @brief Clean up orphaned document files and data.
    @param path : data directory path.
    """
    documents = read_document(path)
    clean_data(path, documents, DOCUMENT_FOLDER, DOCUMENT_FILE_PATH, EDocumentFields.ID, EDocumentFields.ATTACHMENT)


def remove_document(path: str, document_id: str) -> None:
    """!
    @brief Remove document data and attachment.
    @param path : data directory path.
    @param document_id : unique document identifier to delete.
    """
    delete_data(os.path.join(path, DOCUMENT_FOLDER), document_id, id_field=EDocumentFields.ID)
    delete_data(os.path.join(path, DOCUMENT_FILE_PATH), document_id)


def get_document_files(path: str) -> list[str]:
    """!
    @brief Get all document attachment file names.
    @param path : data directory path.
    @return List of document attachment file names.
    """
    return get_file_names_in_folder(os.path.join(path, DOCUMENT_FILE_PATH))
