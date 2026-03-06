"""!
********************************************************************************
@file   data_handler.py
@brief  Core data handling, JSON file operations, and data validation utilities.
********************************************************************************
"""

# autopep8: off
import os
import json
import logging
import enum
import uuid
import shutil
import copy
from typing import Any, TYPE_CHECKING
from pathlib import Path
from datetime import datetime
import subprocess
from subprocess import CompletedProcess
import re
import fitz  # PyMuPDF

from Source.version import __title__
from Source.Util.app_data import ICON_CIRCLE_GREEN, ICON_CIRCLE_RED, ICON_CIRCLE_ORANGE, ICON_CIRCLE_WHITE, \
    REL_PATH, TOOLS_FOLDER, run_subprocess, open_subprocess, CREATE_GIT_PATH
if TYPE_CHECKING:
    from Source.Controller.tab_receipt_base import TabReceiptBase
# autopep8: on

log = logging.getLogger(__title__)

###########################
##      Tools Paths      ##
###########################

# GIT
PORTABLE_GIT_EXE = os.path.abspath(f"{TOOLS_FOLDER}/PortableGit/bin/git.exe")

# Tortoise GIT
TORTOISE_GIT_EXE = os.path.abspath(f"{TOOLS_FOLDER}/TortoiseGit/bin/TortoiseGitProc.exe")

# LibreOffice
LIBRE_OFFICE_EXE = f"{TOOLS_FOLDER}/LibreOfficePortable/App/libreoffice/program/soffice.exe"


def get_libre_office_path() -> str:
    """!
    @brief Get LibreOffice executable path.
    @return LibreOffice executable path or empty string if not found.
    """
    exe_path = LIBRE_OFFICE_EXE
    if not os.path.isfile(exe_path):
        exe_path = ""  # use invalid path if not exists or invalid
    return exe_path


###########################
##     Receipt data      ##
###########################

JSON_VERSION_RECEIPT = "01.00.00"

PDF_TYPE = ".pdf"
XML_TYPE = ".xml"
JSON_TYPE = ".json"
JSON_FILE_TYPES = "JSON file (*.json)"
PDF_FILE_TYPES = "PDF file (*.pdf)"
XML_FILE_TYPES = "XML file (*.xml)"
INVOICE_FILE_TYPES = "PDF und XML Files (*.pdf *.xml)"
INVOICE_TEMPLATE_FILE_TYPES = "PDF, XML, JSON Files (*.pdf *.xml *.json)"
IMAGE_FILE_TYPES = "Bilder (*.png *.jpg *.jpeg *.bmp *.gif)"
COMPANY_LOGO_TYPES = "Bilder (*.png)"
INVOICE_FILE_EXTENSIONS = [PDF_TYPE, XML_TYPE, PDF_TYPE.upper(), XML_TYPE.upper()]
DATE_FORMAT = "dd.MM.yyyy"
DATE_FORMAT_JSON = "%d.%m.%Y"
DATE_FORMAT_XML = "%Y-%m-%d"
DATE_FORMAT_XINVOICE = "yyyy-MM-dd"
DATE_TIME_FORMAT = "%Y/%m/%d %H:%M:%S"
NO_TAX_RATE = 0  # in percent

MONTH_NAMES_SHORT = ["Jan", "Feb", "März", "April", "Mai", "Juni", "Juli", "Aug", "Sep", "Okt", "Nov", "Dez"]
MONTH_NAMES = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]
MONTHS_IN_YEAR = len(MONTH_NAMES)


class EReceiptGroup(str, enum.Enum):
    """!
    @brief Receipt group identifiers.
    """
    UST_VA = "Umsatzsteuer-Voranmeldung"
    UST = "Umsatzsteuererklärung"


RECEIPT_GROUP = {
    EReceiptGroup.UST_VA: "",
    EReceiptGroup.UST: ""
}


class EReceiptFields(str, enum.Enum):
    """!
    @brief Receipt data field identifiers.
    """
    JSON_TYPE = "json_type"
    JSON_VERSION = "json_version"
    ID = "id"
    TRADE_PARTNER = "trade_partner"
    DESCRIPTION = "description"
    INVOICE_NUMBER = "invoice_number"
    INVOICE_DATE = "invoice_date"
    DELIVER_DATE = "deliver_date"
    AMOUNT_GROSS = "amount_gross"
    AMOUNT_NET = "amount_net"
    PAYMENT_DATE = "payment_date"
    BAR = "bar"
    GROUP = "group"
    COMMENT = "comment"
    ATTACHMENT = "attachment"


RECEIPT_TEMPLATE = {
    EReceiptFields.JSON_TYPE: "",
    EReceiptFields.JSON_VERSION: "",
    EReceiptFields.ID: "",
    EReceiptFields.TRADE_PARTNER: "",
    EReceiptFields.DESCRIPTION: "",
    EReceiptFields.INVOICE_NUMBER: "",
    EReceiptFields.INVOICE_DATE: "",
    EReceiptFields.DELIVER_DATE: "",
    EReceiptFields.AMOUNT_GROSS: "",
    EReceiptFields.AMOUNT_NET: "",
    EReceiptFields.PAYMENT_DATE: "",
    EReceiptFields.BAR: False,
    EReceiptFields.GROUP: "",
    EReceiptFields.COMMENT: "",
    EReceiptFields.ATTACHMENT: ""
}


class EStatus(str, enum.Enum):
    """!
    @brief Invoice payment status values.
    """
    DESIGN = "Entwurf"
    NO_PRICE = "Null-Betrag"
    PAID = "Bezahlt"
    PARTLY_PAID = "Teilbezahlt"
    PENDING = "Ausstehend"
    DUE = "Fällig"


def convert_xlsx_to_pdf(xls_file: str) -> None:
    """!
    @brief Convert Excel file to PDF using LibreOffice.
    @param xls_file : Excel file path to convert.
    """
    libre_office_path = get_libre_office_path()
    if libre_office_path:
        out_dir, _ = os.path.split(xls_file)
        run_subprocess([libre_office_path, "--headless", "--convert-to", "pdf:writer_pdf_Export:SelectPdfVersion=3", xls_file, "--outdir", out_dir])


def is_date_format(string: str) -> bool:
    """!
    @brief Check if string matches JSON date format.
    @param string : string to check.
    @return True if string is a valid JSON date format.
    """
    try:
        datetime.strptime(string, DATE_FORMAT_JSON)
        return True
    except ValueError:
        return False


def is_float(string: str) -> bool:
    """!
    @brief Check if string can be converted to float.
    @param string : string to check.
    @return True if string is a valid float representation.
    """
    try:
        float(string)
        return True
    except (TypeError, ValueError):
        return False


def calc_vat_rate(gross: float, net: float) -> int | float:
    """!
    @brief Calculate VAT rate and return as integer if possible.
    @param gross : gross amount.
    @param net : net amount.
    @return VAT rate as integer or float.
    """
    select_vat_rate: int | float = 0
    if net != 0:
        vat_rate = round(((gross / net) - 1) * 100, 4)
        vat_rate_int = int(round(vat_rate, 0))
        gross_reference = net * (1 + (vat_rate_int / 100))
        diff = abs(gross - gross_reference)
        if diff < 0.02:  # allow one cent deviation (less than 2 cent for deviation)
            select_vat_rate = vat_rate_int
        else:
            select_vat_rate = vat_rate
    return select_vat_rate


def convert_amount(string: str) -> int | float:
    """!
    @brief Convert amount string to numeric value.
    @param string : amount string to convert.
    @return Converted amount as integer or float.
    """
    string_value = string.replace(" €", "").replace(",", ".")
    last_point_index = string_value.rfind('.')
    if last_point_index != -1:
        string_value = string_value[:last_point_index].replace('.', '') + string_value[last_point_index:]
    float_value = float(string_value)
    amount: int | float = float_value
    if float_value % 1 == 0:
        amount = int(float_value)
    return amount


def convert_to_de_amount(amount: int | float) -> str:
    """!
    @brief Convert amount to German formatted string.
    @param amount : amount to convert.
    @return German formatted amount string.
    """
    formatted = f"{amount:,.2f}"  # equals: 1,234,567.89
    amount_string = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return amount_string


def convert_to_rate(rate: int | float) -> str:
    """!
    @brief Convert rate to display string with percent sign.
    @param rate : rate value.
    @return Formatted rate string.
    """
    if isinstance(rate, float) and rate.is_integer():
        rate = int(rate)
    return f"{rate} %"


def convert_to_de_date(date_string: str) -> str:
    """!
    @brief Convert XML date to German date format.
    @param date_string : date in format YYYY-MM-DD.
    @return Converted date in format DD.MM.YYYY.
    """
    date_datetime = datetime.strptime(str(date_string), DATE_FORMAT_XML)
    converted_date = date_datetime.strftime(DATE_FORMAT_JSON)
    return converted_date


def fill_data(template: dict[Any, Any], data: dict[Any, Any]) -> dict[Any, Any]:
    """!
    @brief Fill data into template dictionary.
    @param template : default template dictionary.
    @param data : data dictionary to merge into template.
    @return Filled data dictionary.
    """
    filled_data = {}
    for key, default_value in template.items():
        if isinstance(default_value, dict):
            if isinstance(data.get(key), dict):
                filled_data[key] = fill_data(default_value, data[key])
            else:
                filled_data[key] = fill_data(default_value, {})
        else:
            filled_data[key] = data.get(key, default_value)
    return filled_data


def get_file_name(title_data: str | list[str], uid: str | None = None) -> str:
    """!
    @brief Build a valid file name from title data with optional UID suffix.
    @param title_data : title string or list of title parts.
    @param uid : UUID to append as short suffix.
    @return Sanitized file name string.
    """
    if not isinstance(title_data, list):
        title_data = [title_data]
    parts = [data.replace("\n", " ").strip() for data in title_data if data != ""]
    title = "_".join(parts)
    title = re.sub(r'[^\w\s.-]', '', title)
    title = title[:200]  # max file title length
    if uid is not None:
        title = f"{title}_{uid[:8]}"
    return title


def get_file_name_content(file_path: str) -> tuple[str | None, str | None]:
    """!
    @brief Extract date and description from file name.
    @param file_path : file path.
    @return Tuple of file date and file name without date prefix.
    """
    file_date = None
    file_content = None
    file_name = os.path.basename(file_path)
    if re.match(r"^\d{4}_\d{2}_\d{2}_", file_name):
        file_date = datetime.strptime(file_name[:10], "%Y_%m_%d").strftime("%d.%m.%Y")
    file_name_without_ending = os.path.splitext(file_name)[0]
    if file_date is None:
        file_content = file_name_without_ending
    else:
        file_content = file_name_without_ending[11:]  # remove prefix yyyy_mm_dd_
    return file_date, file_content


def get_pdf_text(pdf_path: str) -> str:
    """!
    @brief Extract text content from PDF file.
    @param pdf_path : PDF file path.
    @return Extracted text from all pages.
    """
    text = ""
    with fitz.open(pdf_path) as pdf_document:
        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]
            text += page.get_text() + "\n"
    return text


###########################
##     Data functions    ##
###########################

def validate_data(_data: dict[Any, Any], _schema: dict[Any, Any]) -> tuple[bool, list[str]]:
    """!
    @brief Validate data against JSON schema.
    @param _data : data to validate.
    @param _schema : JSON schema as reference.
    @return Tuple of validation result and list of validation errors.
    """
    validation_result = True
    validation_errors = []
    return validation_result, validation_errors


def get_file_names_in_folder(folder: str) -> list[str]:
    """!
    @brief Get file names without extension in folder.
    @param folder : folder path.
    @return List of file names without extension.
    """
    files = []
    if os.path.exists(folder):
        for file_name in os.listdir(folder):
            name, _ = os.path.splitext(file_name)
            files.append(name)
    return files


def read_json_file(file_path: str) -> Any:
    """!
    @brief Read JSON file content.
    @param file_path : JSON file path.
    @return Parsed JSON data or None on error.
    """
    try:
        with open(file_path, mode="r", encoding="utf-8") as file:
            data = json.load(file)
    except IOError as e:
        log.error("File not possible to read: %s", e)
        data = None
    return data


def read_json_files(path: str, template: dict[Any, Any] | None = None) -> list[dict[Any, Any]]:
    """!
    @brief Read all JSON files from directory.
    @param path : directory path to read from.
    @param template : JSON template to fill data at read.
    @return List of JSON data dictionaries.
    """
    if not os.path.exists(path):
        os.makedirs(path)
        log.debug("Data folder created: %s", path)
    records = []
    for filename in os.listdir(path):
        file_path = os.path.join(path, filename)
        if filename.endswith(JSON_TYPE):
            data = read_json_file(file_path)
            if data is None:
                log.warning("Could not read JSON file: %s", file_path)
                continue
            # Compatible Mode for breaking changes
            match data["json_type"]:
                case "contact":
                    if data["json_version"] == "01.00.00":  # until 22.06.2025 (changing break)
                        old_data = copy.deepcopy(data)
                        data["json_version"] = "02.00.00"
                        data["name"] = old_data["organization"]
                        data["address"] = {
                            "line1": f"{old_data['street']} {old_data['house_number']}",
                            "postCode": old_data["plz"],
                            "city": old_data["city"],
                        }
                        data["contact"] = {
                            "firstName": old_data["first_name"],
                            "lastName": old_data["last_name"],
                            "email": old_data["mail"],
                        }
                case "company":
                    if data["json_version"] == "01.00.00":  # until 28.06.2025 (changing break)
                        old_data = copy.deepcopy(data)
                        data["json_version"] = "02.00.00"
                        data["name"] = f"{old_data['first_name']} {old_data['last_name']} {old_data['description']}"
                        data["taxId"] = old_data["tax_number"]
                        data["websiteText"] = old_data.get("website", "")
                        data["address"] = {
                            "line1": f"{old_data['street']} {old_data['house_number']}",
                            "postCode": old_data["plz"],
                            "city": old_data["city"],
                        }
                        data["contact"] = {
                            "firstName": old_data["first_name"],
                            "lastName": old_data["last_name"],
                            "email": old_data["mail"],
                            "phone": old_data["phone"],
                        }
                        data["payment"] = {
                            "bankName": old_data["bank_name"],
                            "iban": old_data["bank_iban"],
                            "bic": old_data["bank_bic"],
                            "accountName": old_data["bank_owner"],
                        }
                        data["booking"] = {
                            "small_business_regulation": old_data["settings"].get("small_business_regulation", False),
                            "profit_calculation_capital": old_data["settings"].get("profit_calculation_capital", False),
                            "agreed_cost": old_data["settings"].get("agreed_cost", True),
                        }
                        data["default"] = {
                            "quarterly_sales_tax": old_data["settings"].get("quarterly_sales_tax", True),
                            "payed": old_data["settings"].get("payed", False),
                            "bar_payed": old_data["settings"].get("bar_payed", False),
                            "income_group": old_data["settings"].get("income_group", ""),
                            "expenditure_group": old_data["settings"].get("expenditure_group", ""),
                            "groups": old_data["settings"].get("groups", []),
                        }
            if data is not None:
                if template is not None:
                    data = fill_data(template, data)
                records.append(data)
    return records


def write_json_file(file_path: str, data: dict[str, Any] | list[dict[str, Any]]) -> None:
    """!
    @brief Write JSON data to file.
    @param file_path : JSON file path to write to.
    @param data : data to serialize as JSON.
    """
    if not file_path.endswith(JSON_TYPE):
        raise TypeError("File is no JSON type")
    try:
        directory_path = os.path.dirname(file_path)
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
        with open(file_path, mode="w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
    except IOError as e:
        log.error("File not possible to write: %s", e)


def delete_file(file_path: str) -> bool:
    """!
    @brief Delete file from filesystem.
    @param file_path : file path to delete.
    @return True if file was deleted or does not exist.
    """
    if not os.path.exists(file_path):
        return True
    try:
        os.remove(file_path)
    except OSError as e:
        log.error("Delete failed %s", e)
        return False
    return True


def find_file(path: str, uid: str, file_name: str | None = None, file_type: str | None = None) -> str | None:
    """!
    @brief Find file by UID suffix in file name.
    @param path : directory to search in.
    @param uid : unique identifier to match.
    @param file_name : expected attachment file name.
    @param file_type : file type filter, None for any type.
    @return Found file path or None.
    """
    found_file = None
    if os.path.exists(path):
        if file_name is not None:
            file_path = os.path.join(path, file_name)
            name, _file_type = os.path.splitext(file_name)
            if os.path.isfile(file_path) and name.endswith(uid[:8]):
                if (file_type is None) or file_name.endswith(file_type):
                    found_file = file_path
        if found_file is None:
            for actual_file in os.listdir(path):
                if (file_type is None) or actual_file.endswith(file_type):
                    name, _file_type = os.path.splitext(actual_file)
                    if name.endswith(uid[:8]):
                        found_file = os.path.join(path, actual_file)
                        break
    return found_file


def find_json(folder_path: str, uid: str, id_field: str) -> str | None:
    """!
    @brief Find JSON file by UID in ID field.
    @param folder_path : directory to search in.
    @param uid : unique identifier to match.
    @param id_field : ID field name in JSON data.
    @return Found JSON file path or None.
    """
    file_path = None
    for filename in os.listdir(folder_path):
        if filename.endswith(JSON_TYPE):
            actual_file_path = os.path.join(folder_path, filename)
            json_data = read_json_file(actual_file_path)
            if json_data is not None and json_data[id_field] == uid:
                file_path = actual_file_path
                break
    return file_path


def delete_data(folder: str, uid: str, file_type: str | None = None, id_field: str | None = None) -> None:
    """!
    @brief Delete data file by identifier.
    @param folder : folder to delete file from.
    @param uid : unique identifier of the file to delete.
    @param file_type : file type filter.
    @param id_field : ID field name in JSON data.
    """
    if id_field is not None:
        file = find_json(folder, uid, id_field=id_field)
    else:
        file = find_file(folder, uid, file_type=file_type)
    if file is not None:
        git_delete(file)
    else:
        log.error("File with id %s not found in %s to delete", uid, folder)


def add_json(add: bool, data: dict[str, Any], title: str, uid: str, json_export_path: str, id_field: str | None = None, rename: bool = False) -> None:
    """!
    @brief Add or update JSON file.
    @param add : whether to git-add the file.
    @param data : data to write.
    @param title : file title name.
    @param uid : UUID for short ID suffix or file lookup.
    @param json_export_path : JSON export directory path.
    @param id_field : ID field name, None if JSON is new.
    @param rename : whether to rename existing file.
    """
    file_path = os.path.join(json_export_path, f"{title}{JSON_TYPE}")
    if (id_field is None) and not rename:
        write_json_file(file_path, data)
        if add:
            git_add(file_path)
    else:
        if id_field is None:
            log.warning("No field to add JSON")
            return
        found_file_path = find_json(json_export_path, uid, id_field)
        if found_file_path is not None:
            old_data = read_json_file(found_file_path)
            if old_data is None or old_data[id_field] != uid:
                raise ValueError("Invalid UID to update")
            write_json_file(found_file_path, data)
            if rename:
                if found_file_path != file_path:
                    git_rename(found_file_path, file_path)


def add_appendix(title: str, uid: str, appendix_export_path: str, add: bool, appendix_file: str | None = None) -> None:
    """!
    @brief Add or rename attachment file.
    @param title : file title for naming.
    @param uid : UUID to find existing file.
    @param appendix_export_path : attachment export directory path.
    @param add : whether to git-add the file.
    @param appendix_file : attachment file to add, None for rename only.
    """
    if appendix_file is not None:
        _, file_extension = os.path.splitext(appendix_file)
        file_extension = file_extension.lower()
        if not os.path.exists(appendix_export_path):
            os.makedirs(appendix_export_path)
        destination_file = os.path.join(appendix_export_path, f"{title}{file_extension}")
        shutil.copy2(appendix_file, destination_file)
        if add:
            git_add(destination_file)
    else:
        old_file_path = find_file(appendix_export_path, uid)
        if old_file_path is not None:
            _, file_extension = os.path.splitext(old_file_path)
            new_file_path = os.path.join(appendix_export_path, f"{title}{file_extension}")
            if old_file_path != new_file_path:
                git_rename(old_file_path, new_file_path)
        else:
            log.error("File with this ID not found %s", uid)


def set_general_json_data(json_data: dict[Any, Any], json_type: str, type_field: str, version_field: str,
                          version_number: str, id_field: str, uid: str | None = None) -> str:
    """!
    @brief Set general JSON metadata fields (type, version, ID).
    @param json_data : data dictionary to update.
    @param json_type : type value to write.
    @param type_field : type field name.
    @param version_field : version field name.
    @param version_number : version number value.
    @param id_field : ID field name.
    @param uid : existing UUID, None to generate new one.
    @return UUID string.
    """
    generated_uid = str(uuid.uuid4()) if uid is None else uid
    json_data[type_field] = json_type
    json_data[version_field] = version_number
    json_data[id_field] = generated_uid
    return generated_uid


def get_date_title(date: str) -> str:
    """!
    @brief Convert date string to file title format.
    @param date : date string in dd.mm.yyyy format.
    @return Date string in yyyy_mm_dd format.
    """
    return f"{date[6:10]}_{date[3:5]}_{date[0:2]}"


def add_receipt(receipt_data: dict[EReceiptFields, Any], receipt_type: str, json_export_path: str, appendix_export_path: str, add: bool,
                uid: str | None = None, appendix_file: str | None = None, rename: bool = False, number_in_title: bool = False) -> None:
    """!
    @brief Add or update receipt data and attachment.
    @param receipt_data : receipt data to export.
    @param receipt_type : type parameter to write in JSON file.
    @param json_export_path : JSON export directory path.
    @param appendix_export_path : attachment export directory path.
    @param add : whether to git-add the exported files.
    @param uid : UUID of receipt, None if new.
    @param appendix_file : attachment file path to add.
    @param rename : whether to rename existing files.
    @param number_in_title : whether to include invoice number in file title.
    """
    receipt_uid = set_general_json_data(receipt_data, receipt_type, EReceiptFields.JSON_TYPE,
                                        EReceiptFields.JSON_VERSION, JSON_VERSION_RECEIPT,
                                        EReceiptFields.ID, uid)
    date = receipt_data[EReceiptFields.INVOICE_DATE]
    title_parts = [get_date_title(date)]
    if number_in_title:
        title_parts += [receipt_data[EReceiptFields.INVOICE_NUMBER]]
    title_parts += [receipt_data[EReceiptFields.TRADE_PARTNER], receipt_data[EReceiptFields.DESCRIPTION]]
    title = get_file_name(title_parts, receipt_uid)
    if (appendix_file is not None) or rename:
        if appendix_file is None:
            if receipt_data[EReceiptFields.ATTACHMENT]:
                _, file_extension = os.path.splitext(receipt_data[EReceiptFields.ATTACHMENT])
            else:
                file_extension = PDF_TYPE  # compatibility with old version without existing attachment
        else:
            _, file_extension = os.path.splitext(appendix_file)
        file_extension = file_extension.lower()
        receipt_data[EReceiptFields.ATTACHMENT] = f"{title}{file_extension}"
    id_field = EReceiptFields.ID if (uid is not None) else None
    instance = fill_data(RECEIPT_TEMPLATE, receipt_data)
    add_json(add, instance, title, receipt_uid, json_export_path, id_field=id_field, rename=rename)
    if (appendix_file is not None) or rename:
        add_appendix(title, receipt_uid, appendix_export_path, add, appendix_file=appendix_file)


def remove_receipt(json_folder: str, appendix_folder: str, uid: str) -> None:
    """!
    @brief Remove receipt data and attachment.
    @param json_folder : JSON directory path.
    @param appendix_folder : attachment directory path.
    @param uid : UUID of receipt to remove.
    """
    delete_data(json_folder, uid, id_field=EReceiptFields.ID)
    delete_data(appendix_folder, uid)


def clean_data(path: str, records: list[dict[Any, Any]], json_folder_name: str, appendix_folder_name: str,
               id_field: str, attachment_field: str) -> None:
    """!
    @brief Clean up orphaned data files and attachments.
    @param path : data directory path.
    @param records : list of data records.
    @param json_folder_name : JSON folder name.
    @param appendix_folder_name : attachment folder name.
    @param id_field : field name of ID.
    @param attachment_field : field name of attachment.
    """
    attachment_file_names = []
    json_path = os.path.join(path, json_folder_name)
    attachment_path = os.path.join(path, appendix_folder_name)
    for record in records:
        uid = record[id_field]
        attachment_file = find_file(attachment_path, uid, file_name=record[attachment_field])
        if attachment_file:
            attachment_file_names.append(os.path.basename(attachment_file))
        else:
            file = find_json(json_path, uid, id_field=id_field)
            if file:
                git_delete(file)  # delete meta data without attachment
    # delete attachment without meta data
    if os.path.exists(attachment_path):
        for actual_file in os.listdir(attachment_path):
            if actual_file not in attachment_file_names:
                actual_file_path = os.path.join(attachment_path, actual_file)
                git_delete(actual_file_path)


###########################
##      GIT Actions      ##
###########################

def git_cmd(param: list[str]) -> CompletedProcess[str]:
    """!
    @brief Execute Git command via portable Git executable.
    @param param : Git command parameters.
    @return Git command result.
    """
    result = run_subprocess([PORTABLE_GIT_EXE] + param)
    return result


def get_git_repo() -> bool:
    """!
    @brief Get Git repository with configuration.
    @return True if using Git CMD, or False if no repository.
    """
    if os.path.isfile(PORTABLE_GIT_EXE):
        try:
            _result = git_cmd(["--version"])
        except Exception:
            has_repo = False
        else:
            has_repo = True
    else:
        has_repo = False

    return has_repo


def git_rename(old_file_path: str, new_file_path: str) -> None:
    """!
    @brief Rename file via Git.
    @param old_file_path : current file path.
    @param new_file_path : new file path.
    """
    if old_file_path == new_file_path:
        log.warning("File name same to rename (%s)", old_file_path)
    else:
        old_file_path = os.path.abspath(old_file_path)
        new_file_path = os.path.abspath(new_file_path)
        repo = get_git_repo()
        if repo:
            _result = git_cmd(["-C", os.path.abspath(REL_PATH), "mv", old_file_path, new_file_path])
        else:
            p_old_file_path = Path(old_file_path)
            p_new_file_path = Path(new_file_path)
            p_old_file_path.rename(p_new_file_path)


def git_add(file_path: str) -> None:
    """!
    @brief Add file to Git index.
    @param file_path : file path to add.
    """
    file_path = os.path.abspath(file_path)
    repo = get_git_repo()
    if repo:
        _result = git_cmd(["-C", os.path.abspath(REL_PATH), "add", file_path])


def git_delete(file_path: str) -> None:
    """!
    @brief Delete file and remove from Git index.
    @param file_path : file path to delete.
    """
    file_path = os.path.abspath(file_path)
    delete_file(file_path)
    repo = get_git_repo()
    if repo:
        _result = git_cmd(["-C", os.path.abspath(REL_PATH), "rm", file_path])


def check_git_changes() -> tuple[bool, str]:
    """!
    @brief Check for uncommitted Git changes.
    @return Tuple of has_changes flag and changes summary string.
    """
    has_changes = False
    changes = ""
    repo = get_git_repo()
    if repo:
        result = git_cmd(["-C", os.path.abspath(REL_PATH), "status", "--porcelain"])
        changes = result.stdout
        has_changes = bool(changes.strip())
    return has_changes, changes


def commit_all_changes(commit_message: str) -> None:
    """!
    @brief Commit all changes to Git.
    @param commit_message : commit message text.
    """
    repo = get_git_repo()
    if repo:
        _result = git_cmd(["-C", os.path.abspath(REL_PATH), "add", "--all"])  # "-u" for only untracked  --all for all
        _result = git_cmd(["-C", os.path.abspath(REL_PATH), "commit", "-m", commit_message])


def create_repo() -> bool:
    """!
    @brief Create Git repository if not exists.
    @return True if repository was created.
    """
    repo = get_git_repo()
    if not repo:  # create only if not exists
        _result = git_cmd(["-C", CREATE_GIT_PATH, "init"])
        success = True
    else:
        success = False
    return success


def check_repo_exists() -> bool:
    """!
    @brief Check if Git repository exists.
    @return True if repository exists and is valid.
    """
    repo = get_git_repo()
    if repo:
        try:
            _result = git_cmd(["-C", os.path.abspath(REL_PATH), "rev-parse", "--is-inside-work-tree"])
            success = True
        except subprocess.CalledProcessError:
            success = False
    else:
        success = False
    return success


###########################
## Tortoise GIT Actions  ##
###########################

def tortoise_git_check_for_mod() -> None:
    """!
    @brief Open TortoiseGit check for modifications dialog.
    """
    repo_path = os.path.abspath(REL_PATH)
    command = [TORTOISE_GIT_EXE, "/command:repostatus", f"/path:{repo_path}", "/notempfile"]
    open_subprocess(command)


###########################
##    Dialog functions   ##
###########################

def get_status(invoice: dict[EReceiptFields, Any], payment_days: int) -> tuple[str, str]:
    """!
    @brief Get invoice payment status and icon.
    @param invoice : invoice data dictionary.
    @param payment_days : number of days until due.
    @return Tuple of status value and icon path.
    """
    if not invoice[EReceiptFields.INVOICE_DATE]:
        icon = ICON_CIRCLE_WHITE
        status = EStatus.DESIGN
    elif invoice[EReceiptFields.PAYMENT_DATE]:
        icon = ICON_CIRCLE_GREEN
        status = EStatus.PAID
    elif invoice[EReceiptFields.AMOUNT_GROSS] == 0:
        icon = ICON_CIRCLE_GREEN
        status = EStatus.NO_PRICE
    else:
        invoice_date = datetime.strptime(invoice[EReceiptFields.INVOICE_DATE], DATE_FORMAT_JSON)
        current_datetime = datetime.now()
        diff_datetime = current_datetime - invoice_date
        if diff_datetime.days > payment_days:
            icon = ICON_CIRCLE_RED
            status = EStatus.DUE
        else:
            icon = ICON_CIRCLE_ORANGE
            status = EStatus.PENDING
    return status.value, icon


def clear_dialog_data(dialog: "TabReceiptBase") -> None:
    """!
    @brief Clear data of receipt tab for income or expenditure.
    @param dialog : tab instance to clear.
    """
    dialog.receipts = []
    dialog.total_gross = 0
    dialog.total_net = 0
    dialog.values = []
    dialog.invoice_dates = []
    dialog.payment_dates = []
