"""!
********************************************************************************
@file   document.py
@brief  document
********************************************************************************
"""

import os
import logging
import enum
from typing import Optional, Any

from Source.version import __title__
from Source.Util.app_data import SCHEMATA_PATH
from Source.Model.data_handler import read_json_files, get_file_names_in_folder, validate_data, read_json_file, \
    set_general_json_data, fill_data, get_file_name, add_json, add_appendix, get_date_title, delete_data, PDF_TYPE

log = logging.getLogger(__title__)

JSON_VERSION_DOCUMENT = "01.00.00"

DOCUMENT_FOLDER = "document"
DOCUMENT_FILE_PATH = DOCUMENT_FOLDER + "/files"
DOCUMENT_TYPE = "document"
DOCUMENT_SCHEMA_FILE = "document_schema.json"


class EDocumentFields(str, enum.Enum):
    """!
    @brief Document fields.
    """
    JSON_TYPE = "json_type"
    JSON_VERSION = "json_version"
    ID = "id"
    DESCRIPTION = "description"
    DOCUMENT_DATE = "document_date"
    ATTACHMENT = "attachment"


D_DOCUMENT_TEMPLATE = {
    EDocumentFields.JSON_TYPE: "",
    EDocumentFields.JSON_VERSION: "",
    EDocumentFields.ID: "",
    EDocumentFields.DESCRIPTION: "",
    EDocumentFields.DOCUMENT_DATE: "",
    EDocumentFields.ATTACHMENT: ""
}


def validate_document(data: dict[EDocumentFields, Any]) -> list[str]:
    """!
    @brief Validate document data.
    @param data : data to validate
    @return found error at validation
    """
    schemata_path = os.path.join(SCHEMATA_PATH, DOCUMENT_SCHEMA_FILE)
    schemata = read_json_file(schemata_path)
    _is_valid, error = validate_data(data, schemata)
    return error


def read_document(path: str) -> list[dict[EDocumentFields, str]]:
    """!
    @brief Read all documents
    @param path : read in this path
    @return list with existing documents JSON data
    """
    l_document = read_json_files(os.path.join(path, DOCUMENT_FOLDER), D_DOCUMENT_TEMPLATE)
    return l_document


def add_document(path: str, add: bool, d_document_data: dict[EDocumentFields, str], document_id: Optional[str] = None,
                 appendix_file: Optional[str] = None, rename: bool = False) -> None:
    """!
    @brief Add or actualize document (data and appendix).
    @param path : export to this path
    @param add : GIT add status
    @param d_document_data : document data to export
    @param document_id : document ID
    @param appendix_file : document file
    @param rename : status if file name should renamed depend on actual data
    """
    s_id = set_general_json_data(d_document_data, DOCUMENT_TYPE, EDocumentFields.JSON_TYPE,
                                 EDocumentFields.JSON_VERSION, JSON_VERSION_DOCUMENT,
                                 EDocumentFields.ID, document_id)
    date = d_document_data[EDocumentFields.DOCUMENT_DATE]
    title = get_file_name([get_date_title(date), d_document_data[EDocumentFields.DESCRIPTION]], s_id)
    if (appendix_file is not None) or rename:
        if appendix_file is None:
            if d_document_data[EDocumentFields.ATTACHMENT]:
                _, file_extension = os.path.splitext(d_document_data[EDocumentFields.ATTACHMENT])
                file_extension = file_extension.lower()
            else:
                file_extension = PDF_TYPE  # only for compatible with old version without existing attachment
        else:
            _, file_extension = os.path.splitext(appendix_file)
            file_extension = file_extension.lower()
        d_document_data[EDocumentFields.ATTACHMENT] = f"{title}{file_extension}"
    id_field = EDocumentFields.ID if (document_id is not None) else None
    instance = fill_data(D_DOCUMENT_TEMPLATE, d_document_data)
    add_json(add, instance, title, s_id, os.path.join(path, DOCUMENT_FOLDER), id_field=id_field, rename=rename)
    if (appendix_file is not None) or rename:
        add_appendix(title, s_id, os.path.join(path, DOCUMENT_FILE_PATH), add, appendix_file=appendix_file)


def remove_document(path: str, document_id: str) -> None:
    """!
    @brief Remove document (data and appendix).
    @param path : delete in this path
    @param document_id : document ID
    """
    delete_data(os.path.join(path, DOCUMENT_FOLDER), document_id, id_field=EDocumentFields.ID)
    delete_data(os.path.join(path, DOCUMENT_FILE_PATH), document_id)


def get_document_files(path: str) -> list[str]:
    """!
    @brief Get document files.
    @param path : get document in this path
    @return list with all document files
    """
    return get_file_names_in_folder(os.path.join(path, DOCUMENT_FILE_PATH))
