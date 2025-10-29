"""!
********************************************************************************
@file   data_handler.py
@brief  data handler
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
from typing import Optional, Any, TYPE_CHECKING
from pathlib import Path
from datetime import datetime
import subprocess
from subprocess import CompletedProcess
import re
import fitz  # PyMuPDF
os.environ["GIT_PYTHON_REFRESH"] = "quiet"
import git  # pylint: disable=wrong-import-position
import jsonschema.validators  # pylint: disable=wrong-import-position
import jsonschema.exceptions  # pylint: disable=wrong-import-position

from Source.version import __title__  # pylint: disable=wrong-import-position
from Source.Util.app_data import ICON_CIRCLE_GREEN, ICON_CIRCLE_RED, ICON_CIRCLE_ORANGE, ICON_CIRCLE_WHITE, \
    REL_PATH, TOOLS_FOLDER, run_subprocess, open_subprocess, CREATE_GIT_PATH  # pylint: disable=wrong-import-position
if TYPE_CHECKING:
    from Source.Controller.tab_income import TabIncome
    from Source.Controller.tab_expenditure import TabExpenditure
    from Source.Controller.tab_document import TabDocument
# autopep8: on

log = logging.getLogger(__title__)

B_USE_GIT_CMD = True  # TODO

###########################
##      Tools Paths      ##
###########################

# GIT
PORTABLE_GIT_EXE = os.path.abspath(f"{TOOLS_FOLDER}/PortableGit/bin/git.exe")
if not B_USE_GIT_CMD:
    if os.path.isfile(PORTABLE_GIT_EXE):
        os.environ["GIT_PYTHON_GIT_EXECUTABLE"] = PORTABLE_GIT_EXE

# Tortoise GIT
TORTOISE_GIT_EXE = os.path.abspath(f"{TOOLS_FOLDER}/TortoiseGit/bin/TortoiseGitProc.exe")

# LibreOffice
LIBRE_OFFICE_EXE = f"{TOOLS_FOLDER}/LibreOfficePortable/App/libreoffice/program/soffice.exe"


def get_libre_office_path() -> str:
    """!
    @brief Get libre office path.
    @return libre office path exe
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
IMAGE_FILE_TYPES = "Bilder (*.png *.jpg *.jpeg *.bmp *.gif)"
COMPANY_LOGO_TYPES = "Bilder (*.png)"
L_INVOICE_FILE_TYPES = [PDF_TYPE, XML_TYPE, PDF_TYPE.upper(), XML_TYPE.upper()]
DATE_FORMAT = "dd.MM.yyyy"
DATE_FORMAT_JSON = "%d.%m.%Y"
DATE_FORMAT_XML = "%Y-%m-%d"
DATE_FORMAT_XINVOICE = "yyyy-MM-dd"
DATE_TIME_FORMAT = "%Y/%m/%d %H:%M:%S"
NO_TAX_RATE = 0  # in percent

L_MONTH_NAMES_SHORT = ["Jan", "Feb", "März", "April", "Mai", "Juni", "Juli", "Aug", "Sep", "Okt", "Nov", "Dez"]
L_MONTH_NAMES = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]


class EReceiptGroup(str, enum.Enum):
    """!
    @brief Receipt group.
    """
    UST_VA = "Umsatzsteuer-Voranmeldung"
    UST = "Umsatzsteuererklärung"


D_RECEIPT_GROUP = {
    EReceiptGroup.UST_VA: "",
    EReceiptGroup.UST: ""
}


class EReceiptFields(str, enum.Enum):
    """!
    @brief Receipt fields.
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


D_RECEIPT_TEMPLATE = {
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
    @brief Mode of configuration change.
    """
    DESIGN = "Entwurf"
    NO_PRICE = "Null-Betrag"
    PAID = "Bezahlt"
    PARTLY_PAID = "Teilbezahlt"
    PENDING = "Ausstehend"
    DUE = "Fällig"


def convert_xlsx_to_pdf(xls_file: str) -> None:
    """!
    @brief Convert Excel to PDF
    @param xls_file : Excel file
    """
    libre_office_path = get_libre_office_path()
    if libre_office_path:
        out_dir, _file_name = os.path.split(xls_file)
        _result = run_subprocess([libre_office_path, "--headless", "--convert-to", "pdf:writer_pdf_Export:SelectPdfVersion=3", xls_file, "--outdir", out_dir])
    else:
        _result = None


def is_date_format(string: str) -> bool:
    """!
    @brief Check if string is JSON date format
    @param string : string to check
    @return status if string can convert to float
    """
    try:
        datetime.strptime(string, DATE_FORMAT_JSON)
        b_date = True
    except ValueError:
        b_date = False
    return b_date


def is_float(s_string: str) -> bool:
    """!
    @brief Check if string can convert to float.
    @param s_string : string to check
    @return status if string can convert to float
    """
    try:
        float(s_string)
        b_float = True
    except (TypeError, ValueError):
        b_float = False
    return b_float


def calc_vat_rate(gross: float, net: float) -> int | float:
    """!
    @brief Calculate vat rate to string and try to convert to integer string
    @param gross : gross value
    @param net : net value
    @return vat rate
    """
    if net != 0:
        vat_rate = round(((gross / net) - 1) * 100, 4)
        vat_rate_int = int(round(vat_rate, 0))
        gross_reference = net * (1 + (vat_rate_int / 100))
        diff = abs(gross - gross_reference)
        if diff < 0.02:  # allow one cent deviation (less than 2 cent for deviation)
            select_vat_rate = vat_rate_int
        else:
            select_vat_rate = vat_rate
    else:
        select_vat_rate = 0
    return select_vat_rate


def convert_amount(string: str) -> int | float:
    """!
    @brief Convert amount
    @param string : string to convert
    @return converted string
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


def fill_data(template: dict[Any, Any], data: dict[Any, Any]) -> dict[Any, Any]:
    """!
    @brief Fill data to template dictionary.
    @param template : default template dictionary
    @param data : actual data dictionary to fill in template dictionary
    @return filled data
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


def get_file_name(title_data: str | list[str], uid: Optional[str] = None) -> str:
    """!
    @brief Get file name from title.
           connect single title data, delete invalid file name characters and add short UID
    @param title_data : title
    @param uid : UID
    @return valid file name
    """
    s_title = ""
    if not isinstance(title_data, list):
        title_data = [title_data]
    for i, data in enumerate(title_data):
        if data != "":
            if i != 0:
                s_title += "_"
            s_title += data.replace("\n", " ").strip()  # write in single row
    s_title = re.sub(r'[^\w\s.-]', '', s_title)
    s_title = s_title[:200]  # max file title length
    if uid is not None:
        s_title += f"_{uid[:8]}"
    return s_title


def get_file_name_content(file_path: str) -> tuple[str | None, str | None]:
    """!
    @brief Get file name content
    @param file_path : file path
    @return file date and content
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
    @brief Get pdf text
    @param pdf_path : pdf path
    @return text from pdf
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

def validate_data(data: dict[Any, Any], schema: dict[Any, Any]) -> tuple[bool, list[str]]:
    """!
    @brief Validate data.
    @param data : data to validate
    @param schema : schema as reference
    @return validation_result: [True|False] validate result; validation_errors list with error
    """
    validation_result = True
    validation_errors = []
    return validation_result, validation_errors


def get_file_names_in_folder(folder: str) -> list[str]:
    """!
    @brief Get files in folder.
    @param folder : folder
    @return list with all file names in folder
    """
    l_files = []
    if os.path.exists(folder):
        for file_name in os.listdir(folder):
            name, _file_type = os.path.splitext(file_name)
            l_files.append(name)
    return l_files


def read_json_file(file_path: str) -> Any:
    """!
    @brief Read JSON file content.
    @param file_path : file path
    @return JSON data from file content
    """
    try:
        with open(file_path, mode="r", encoding="utf-8") as file:
            d_data = json.load(file)
    except IOError as e:
        log.error("File not possible to read: %s", e)
        d_data = None
    return d_data


def read_json_files(path: str, d_template: Optional[dict[Any, Any]] = None) -> list[dict[Any, Any]]:
    """!
    @brief Read data.
    @param path : read in this path
    @param d_template : JSON template to fill data at read
    @return list with all files
    """
    if not os.path.exists(path):
        os.makedirs(path)
        log.debug("Data folder created: %s", path)
    l_data = []
    for filename in os.listdir(path):
        file_path = os.path.join(path, filename)
        if filename.endswith(JSON_TYPE):
            data = read_json_file(file_path)
            # Compatible Mode for breaking changes
            match data["json_type"]:
                case "contact":
                    if data["json_version"] == "01.00.00":  # until 22.06.2025 (changing break)
                        old_data = copy.deepcopy(data)
                        data = copy.deepcopy(old_data)
                        data["json_version"] = "02.00.00"
                        data["name"] = old_data["organization"]
                        data["address"] = {
                            "line1": old_data["street"] + " " + old_data["house_number"],
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
                        data = copy.deepcopy(old_data)
                        data["json_version"] = "02.00.00"
                        data["name"] = old_data["first_name"] + " " + old_data["last_name"] + " " + old_data["description"]
                        data["taxId"] = old_data["tax_number"]
                        data["websiteText"] = old_data.get("website", "")
                        data["address"] = {
                            "line1": old_data["street"] + " " + old_data["house_number"],
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
                if d_template is not None:
                    data = fill_data(d_template, data)
                l_data.append(data)
    return l_data


def write_json_file(file_path: str, data: dict[str, Any] | list[dict[str, Any]]) -> None:
    """!
    @brief Write JSON data to file.
    @param file_path : write to this file
    @param data : data to write
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


def delete_file(file_path: str) -> None:
    """!
    @brief Delete file.
    @param file_path : file to delete
    """
    try:
        os.remove(file_path)
    except IOError as e:
        log.error("Delete failed %s", e)


def find_file(path: str, uid: str, file_name: Optional[str] = None, file_type: Optional[str] = None) -> str | None:
    """!
    @brief Find file from title or UID.
    @param path : find file in this path
    @param uid : UID
    @param file_name : possible attachment file name
    @param file_type : file type [None] find every file type
    @return founded file
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
    @brief Find JSON file depend on UID in id field
    @param folder_path : find file in this folder
    @param uid : ID to find
    @param id_field : ID field in JSON data
    @return founded JSON file
    """
    file_path = None
    for filename in os.listdir(folder_path):
        if filename.endswith(JSON_TYPE):
            actual_file_path = os.path.join(folder_path, filename)
            json_data = read_json_file(actual_file_path)
            if json_data[id_field] == uid:
                file_path = actual_file_path
                break
    return file_path


def delete_data(folder: str, s_id: str, file_type: Optional[str] = None, id_field: Optional[str] = None) -> None:
    """!
    @brief Delete data.
    @param folder : delete a file in this folder
    @param s_id : ID to delete
    @param file_type : file type
    @param id_field : ID field name
    """
    if id_field is not None:
        file = find_json(folder, s_id, id_field=id_field)
    else:
        file = find_file(folder, s_id, file_type=file_type)
    if file is not None:
        git_delete(file)
    else:
        log.error("File with id %s not found in %s to delete", s_id, folder)


def add_json(add: bool, data: dict[str, Any], title: str, uid: str, json_export_path: str, id_field: Optional[str] = None, rename: bool = False) -> None:
    """!
    @brief Add or actualize JSON file
    @param add : GIT add status
    @param data : data to add or actualize
    @param title : title name
    @param uid : UUID to create short id for suffix name or find file
    @param json_export_path: add JSON to this file path
    @param id_field : field of ID [None] JSON is new
    @param rename : status if existing file should renamed (JSON and appendix)
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
            if old_data[id_field] != uid:
                raise ValueError("Invalid UID to update")
            write_json_file(found_file_path, data)
            if rename:
                if found_file_path != file_path:
                    git_rename(found_file_path, file_path)


def add_appendix(title: str, uid: str, appendix_export_path: str, add: bool, appendix_file: Optional[str] = None) -> None:
    """!
    @brief Add or rename appendix file to accounting.
    @param title : title of file to add for new naming
    @param uid : UUID to find existing file
    @param appendix_export_path : add appendix to this file path
    @param add : GIT add status
    @param appendix_file : appendix file to add [None] for renaming
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
                          version_number: str, id_field: str, uid: Optional[str] = None) -> str:
    """!
    @brief Set general JSON data
    @param json_data : receipt data
    @param json_type : type parameter to write in JSON file
    @param type_field : type field name
    @param version_field : version field name
    @param version_number : version number
    @param id_field : ID field name
    @param uid : UUID of receipt [None] receipt is new to add
    @return UID
    """
    if uid is None:
        s_id = str(uuid.uuid4())
    else:
        s_id = uid
    json_data[type_field] = json_type
    json_data[version_field] = version_number
    json_data[id_field] = s_id
    return s_id


def get_date_title(date: str) -> str:
    """!
    @brief Get date title name
    @param date : date string dd.mm.yyyy
    @return date title yyyy_mm_dd
    """
    title = date[6:10] + "_" + date[3:5] + "_" + date[0:2]
    return title


def add_receipt(d_receipt_data: dict[EReceiptFields, Any], receipt_type: str, json_export_path: str, appendix_export_path: str, add: bool,
                uid: Optional[str] = None, appendix_file: Optional[str] = None, rename: bool = False, number_in_title: bool = False) -> None:
    """!
    @brief Add or actualize receipt (data and appendix) to accounting.
    @param d_receipt_data : receipt data
    @param receipt_type : type parameter to write in JSON file
    @param json_export_path : add JSON to this file path
    @param appendix_export_path : add appendix to this file path
    @param add : GIT add status
    @param uid : UUID of receipt [None] receipt is new to add
    @param appendix_file : appendix file to add with JSON data
    @param rename : status if existing file should renamed (JSON and appendix)
    @param number_in_title : status if invoice number is in file title
    """
    s_id = set_general_json_data(d_receipt_data, receipt_type, EReceiptFields.JSON_TYPE,
                                 EReceiptFields.JSON_VERSION, JSON_VERSION_RECEIPT,
                                 EReceiptFields.ID, uid)
    date = d_receipt_data[EReceiptFields.INVOICE_DATE]
    l_title_data = [get_date_title(date)]
    if number_in_title:
        l_title_data += [d_receipt_data[EReceiptFields.INVOICE_NUMBER]]
    l_title_data += [d_receipt_data[EReceiptFields.TRADE_PARTNER], d_receipt_data[EReceiptFields.DESCRIPTION]]
    title = get_file_name(l_title_data, s_id)
    if (appendix_file is not None) or rename:
        if appendix_file is None:
            if d_receipt_data[EReceiptFields.ATTACHMENT]:
                _, file_extension = os.path.splitext(d_receipt_data[EReceiptFields.ATTACHMENT])
                file_extension = file_extension.lower()
            else:
                file_extension = PDF_TYPE  # only for compatible with old version without existing attachment
        else:
            _, file_extension = os.path.splitext(appendix_file)
            file_extension = file_extension.lower()
        d_receipt_data[EReceiptFields.ATTACHMENT] = f"{title}{file_extension}"
    id_field = EReceiptFields.ID if (uid is not None) else None
    instance = fill_data(D_RECEIPT_TEMPLATE, d_receipt_data)
    add_json(add, instance, title, s_id, json_export_path, id_field=id_field, rename=rename)
    if (appendix_file is not None) or rename:
        add_appendix(title, s_id, appendix_export_path, add, appendix_file=appendix_file)


def remove_receipt(json_folder: str, appendix_folder: str, uid: str) -> None:
    """!
    @brief Remove receipt (data and appendix) from accounting.
    @param json_folder : remove JSON in this file path
    @param appendix_folder : remove appendix in this file path
    @param uid : UUID of receipt
    """
    delete_data(json_folder, uid, id_field=EReceiptFields.ID)
    delete_data(appendix_folder, uid)


def clean_data(path: str, l_data: list, json_folder_name: str, appendix_folder_name: str,
               id_field: str, attachment_field: str) -> None:
    """!
    @brief Clean data.
    @param path : data path
    @param l_data : data
    @param json_folder_name : JSON folder name
    @param appendix_folder_name : appendix folder name
    @param id_field : field name of ID
    @param attachment_field : field name of attachment
    """
    attachment_file_names = []
    income_path = os.path.join(path, json_folder_name)
    attachment_path = os.path.join(path, appendix_folder_name)
    for income in l_data:
        uid = income[id_field]
        attachment_file = find_file(attachment_path, uid, file_name=income[attachment_field])
        if attachment_file:
            attachment_file_names.append(os.path.basename(attachment_file))
        else:
            file = find_json(income_path, uid, id_field=id_field)
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

if B_USE_GIT_CMD:
    def git_cmd(param: list[str]) -> CompletedProcess[str]:
        """!
        @brief Execute GIT command on cmd
        @param param : file to add
        @return GIT command result
        """
        result = run_subprocess([PORTABLE_GIT_EXE] + param)
        return result


def get_git_repo(file_path: str) -> bool:
    """!
    @brief Get git Repo with configuration.
    @param file_path : file to add
    @return status if git repo exist
    """
    if os.path.isfile(PORTABLE_GIT_EXE):
        if B_USE_GIT_CMD:
            try:
                _result = git_cmd(["--version"])
            except BaseException:
                b_git_repo = False
            else:
                b_git_repo = True
        else:
            try:
                test_repo = git.Repo(os.path.abspath(REL_PATH), search_parent_directories=True)
                test_repo.git.execute(["git", "--version"])
            except git.exc.GitError:
                b_git_repo = False
            else:
                b_git_repo = True
    else:
        b_git_repo = False

    if b_git_repo:
        if not B_USE_GIT_CMD:
            s_folder = os.path.dirname(file_path)
            repo = git.Repo(s_folder, search_parent_directories=True)
            with repo.config_writer() as config:
                config.set_value("user", "name", os.getlogin())
                # config.set_value("user", "email", "deine.email@example.com")
        else:
            repo = True
    else:
        repo = False
    return repo


def git_rename(old_file_path: str, new_file_path: str) -> None:
    """!
    @brief Rename file on GIT.
    @param old_file_path : old file name
    @param new_file_path : new file name
    """
    if old_file_path == new_file_path:
        log.warning("File name same to rename (%s)", old_file_path)
    else:
        old_file_path = os.path.abspath(old_file_path)
        new_file_path = os.path.abspath(new_file_path)
        repo = get_git_repo(old_file_path)
        if repo:
            if B_USE_GIT_CMD:
                _result = git_cmd(["-C", os.path.abspath(REL_PATH), "mv", old_file_path, new_file_path])
            else:
                try:
                    repo.index.move([old_file_path, new_file_path])
                except git.GitCommandError as err:
                    log.error("Git Rename failed (%s): %s", new_file_path, err)
        else:
            p_old_file_path = Path(old_file_path)
            p_new_file_path = Path(new_file_path)
            p_old_file_path.rename(p_new_file_path)


def git_add(file_path: str) -> None:
    """!
    @brief Add file to GIT.
    @param file_path : file to add
    """
    file_path = os.path.abspath(file_path)
    repo = get_git_repo(file_path)
    if repo:
        if B_USE_GIT_CMD:
            _result = git_cmd(["-C", os.path.abspath(REL_PATH), "add", file_path])
        else:
            try:
                repo.index.add(file_path)
            except git.GitCommandError as err:
                log.error("Git Add failed (%s): %s", file_path, err)


def git_delete(file_path: str) -> None:
    """!
    @brief Delete file from GIT.
    @param file_path : file to delete
    """
    file_path = os.path.abspath(file_path)
    delete_file(file_path)
    repo = get_git_repo(file_path)
    if repo:
        if B_USE_GIT_CMD:
            _result = git_cmd(["-C", os.path.abspath(REL_PATH), "rm", file_path])
        else:
            try:
                repo.index.remove([file_path])
            except git.GitCommandError as err:
                log.error("Git Remove failed (%s): %s", file_path, err)


def check_git_changes() -> tuple[bool, str]:
    """!
    @brief Check for Git Changes.
    @return changes status
    """
    b_changes = False
    s_changes = ""
    repo = get_git_repo(os.path.abspath(REL_PATH))
    if repo:
        if B_USE_GIT_CMD:
            result = git_cmd(["-C", os.path.abspath(REL_PATH), "status", "--porcelain"])
            s_changes = result.stdout
            b_changes = bool(s_changes.strip())
        else:
            s_changes = ""  # TODO
            try:
                if repo.is_dirty(untracked_files=False):
                    log.debug("Changes found to commit")
                    for item in repo.index.diff(None):
                        log.debug("Changed: %s", item.a_path)
                    for item in repo.untracked_files:
                        log.debug("Untracked: %s", item)
                    b_changes = True
                else:
                    log.debug("No changes to commit")
            except git.exc.InvalidGitRepositoryError:
                log.debug("Path is no Git Path")
    return b_changes, s_changes


def commit_all_changes(commit_message: str) -> None:
    """!
    @brief Commit all changes
    @param commit_message : commit message
    """
    repo = get_git_repo(os.path.abspath(REL_PATH))
    if repo:
        if B_USE_GIT_CMD:
            _result = git_cmd(["-C", os.path.abspath(REL_PATH), "add", "--all"])  # "-u" for only untracked  --all for all
            _result = git_cmd(["-C", os.path.abspath(REL_PATH), "commit", "-m", commit_message])
        else:
            try:
                repo.git.add(A=True)
                repo.index.commit(commit_message)
                log.debug("All changes commit")
            except git.exc.InvalidGitRepositoryError:
                log.debug("Path is no Git Path")


def create_repo() -> bool:
    """!
    @brief Create repo
    @return success status
    """
    repo = get_git_repo(os.path.abspath(REL_PATH))
    if repo:  # create only if not exists
        _result = git_cmd(["-C", CREATE_GIT_PATH, "init"])
        success = True
    else:
        success = False
    return success


def check_repo_exists() -> bool:
    """!
    @brief Create repo
    @return success status
    """
    repo = get_git_repo(os.path.abspath(REL_PATH))
    if repo:  # create only if not exists
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
    @brief Execute GIT command on cmd. Command for TortoiseGit: Check for Modifications
    """
    repo_path = os.path.abspath(REL_PATH)
    command = [TORTOISE_GIT_EXE, "/command:repostatus", f"/path:{repo_path}", "/notempfile"]
    open_subprocess(command)


###########################
##    Dialog functions   ##
###########################

def get_status(invoice: dict[EReceiptFields, Any], payment_days: int) -> tuple[str, str]:
    """!
    @brief Get invoice status.
    @param invoice : invoice data
    @param payment_days : payment days
    @return status value and icon as tuple
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


def clear_dialog_data(dialog: "TabDocument | TabExpenditure | TabIncome") -> None:
    """!
    @brief Clear data of dialog for income and expenditure.
    @param dialog : dialog
    """
    dialog.l_data = []
    dialog.total_gross = 0
    dialog.total_net = 0
    dialog.l_value = []
    dialog.l_date = []
