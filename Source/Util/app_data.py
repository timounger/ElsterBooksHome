"""!
********************************************************************************
@file   app_data.py
@brief  Data module (path related constants and functions)
********************************************************************************
"""

import sys
import os
import io
import logging
import enum
from typing import Any, TYPE_CHECKING
import socket
import platform
import subprocess
from subprocess import CompletedProcess
import traceback

if platform.system() == 'Windows':
    import win32crypt

from PyQt6.QtCore import QSettings, QByteArray  # pylint: disable=wrong-import-position
from PyQt6.QtGui import QActionGroup, QAction  # pylint: disable=wrong-import-position

from Source.version import __title__, __author__, running_as_exe, DISK_TYPE, DISK_MODEL, DISK_SERIAL_NUMBER  # pylint: disable=wrong-import-position
if TYPE_CHECKING:
    from Source.Controller.main_window import MainWindow

# Fix for PyInstaller + mt940 (stdout may be None)
if sys.stdout is None:
    sys.stdout = io.TextIOWrapper(io.BytesIO(), encoding='utf-8')
if sys.stderr is None:
    sys.stderr = io.TextIOWrapper(io.BytesIO(), encoding='utf-8')

log = logging.getLogger(__title__)

if running_as_exe():
    CREATE_GIT_PATH = "."
    REL_PATH = "Data"
    TOOLS_FOLDER = "Tools"
    EXPORT_PATH = "Export"
else:
    CREATE_GIT_PATH = "../"
    REL_PATH = "../Data"
    TOOLS_FOLDER = "../Resources/Tools"
    EXPORT_PATH = "../Export"


def resource_path(s_relative_path: str) -> str:
    """!
    @brief Returns the absolute path to a resource given by a relative path depending on the environment (EXE or Python)
    @param s_relative_path : the relative path to a file or directory
    @return absolute path to the resource
    """
    if hasattr(sys, "_MEIPASS"):  # check without function call for mypy
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        s_base_path = sys._MEIPASS  # pylint: disable=protected-access
    else:
        s_base_path = os.path.abspath("../")
    s_resource_path = os.path.join(s_base_path, s_relative_path)
    log.debug("Resource Path (relative %s): %s", s_relative_path, s_resource_path)
    return s_resource_path


def thread_dialog(obj: Any) -> None:
    """!
    @brief Handle dialog thread in exception to show errors in main thread.
    @param obj : object of thread class
    """
    try:
        obj.show_dialog()
    except Exception:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        s_err = "".join(traceback.format_exception(exc_type, exc_obj, exc_tb))  # complete stacktrace
        log.error(s_err)
        obj.ui.qt_exception_hook.exception_caught.emit(s_err)


def run_subprocess(command: list[str]) -> CompletedProcess[str]:
    """!
    @brief Run subprocess without open terminal
    @param command : subprocess command
    @return result
    """
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    result = subprocess.run(command, capture_output=True, text=True, check=True, startupinfo=startupinfo)
    return result


def open_subprocess(command: list[str]) -> None:
    """
    @brief Open subprocess without open terminal (and without freezing the main script)
    @param command : subprocess command
    """
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    subprocess.Popen(command, text=True, startupinfo=startupinfo)


def get_computer_name() -> str:
    """!
    @brief Get computer name.
    @return computer name
    """
    try:
        hostname = socket.gethostname()
    except BaseException:
        hostname = ""
    return hostname


def get_disk_info() -> str:
    """!
    @brief Get disk info using PowerShell
    @return disk info
    """
    ps_script = (
        "Get-WmiObject Win32_DiskDrive | "
        "Select-Object Model, InterfaceType, SerialNumber | "
        "Format-Table -AutoSize | Out-String"
    )
    result = run_subprocess(["powershell", "-Command", ps_script])
    return result.stdout.strip()


def validate_portable_edition() -> bool:
    """!
    @brief Check if valid portable device present
    @return portable status
    """
    result = get_disk_info()
    portable = False
    for line in result.split("\n"):
        line = line.strip()
        if line.startswith(DISK_MODEL) and line.endswith(DISK_SERIAL_NUMBER) and DISK_TYPE in line:
            portable = True
            break
    return portable


def open_explorer(explorer_path: str, b_open_input: bool = False) -> None:
    """!
    @brief Open explorer.
    @param explorer_path : path to open
    @param b_open_input : open explorer into folder
    """
    s_open_folder = explorer_path.replace("/", "\\")
    mode = "explorer " if b_open_input else r"explorer /select, "
    with subprocess.Popen(mode + s_open_folder):
        pass


def group_menu(parent: "MainWindow", l_actions: list[QAction], actual_value: Any, l_match_values: list[Any]) -> QActionGroup:
    """!
    @brief Set action group.
    @param parent : parent window controller
    @param l_actions: list with actions to add
    @param actual_value : actual setting value
    @param l_match_values : list with possible match values to check default setting
    @return action group object
    """
    action_group = QActionGroup(parent)
    for action in l_actions:
        action_group.addAction(action)
    for i, match_value in enumerate(l_match_values):
        if match_value == actual_value:
            l_actions[i].setChecked(True)
            break
    return action_group


# Files and Paths
# https://icons8.com/icons/fluency-systems-regular
# https://www.flaticon.com/free-icon/list-search_7560656
# General Icon and Images
ICON_APP_PATH = "Resources/app.ico"
ICON_APP_FAVICON_PATH = "Resources/favicon.ico"
ICON_APP = resource_path(ICON_APP_PATH)
IMG_SPLASH = resource_path("Resources/splash.gif")
LOGO_ZUGFERD = resource_path("Resources/InvoiceImage/zugferd.png")
LOGO_ZUGFERD_SVG = resource_path("Resources/InvoiceImage/zugferd.svg")
IMG_DROP_FILE = resource_path("Resources/Icon/drop_file.png")
# Menu Settings
ICON_THEME_LIGHT = resource_path("Resources/Icon/theme_light.png")
ICON_THEME_DARK = resource_path("Resources/Icon/theme_dark.png")
# Menu Help
ICON_HELP_LIGHT = resource_path("Resources/Icon/help_light.png")
ICON_HELP_DARK = resource_path("Resources/Icon/help_dark.png")
ICON_GITHUB_LIGHT = resource_path("Resources/Icon/github_light.png")
ICON_GITHUB_DARK = resource_path("Resources/Icon/github_dark.png")
HELP_PATH = resource_path("Resources/Help/")
# other (none menu)
ICON_CONTACT_LIGHT = resource_path("Resources/Icon/contact_light.png")
ICON_CONTACT_DARK = resource_path("Resources/Icon/contact_dark.png")

ICON_ATTACH_LIGHT = resource_path("Resources/Icon/file_attach_light.png")
ICON_ATTACH_DARK = resource_path("Resources/Icon/file_attach_dark.png")
ICON_PDF_LIGHT = resource_path("Resources/Icon/file_pdf_light.png")
ICON_PDF_DARK = resource_path("Resources/Icon/file_pdf_dark.png")
ICON_WORD_LIGHT = resource_path("Resources/Icon/file_word_light.png")
ICON_WORD_DARK = resource_path("Resources/Icon/file_word_dark.png")
ICON_EXCEL_LIGHT = resource_path("Resources/Icon/file_excel_light.png")
ICON_EXCEL_DARK = resource_path("Resources/Icon/file_excel_dark.png")
ICON_XML_LIGHT = resource_path("Resources/Icon/file_xml_light.png")
ICON_XML_DARK = resource_path("Resources/Icon/file_xml_dark.png")
ICON_ZUGFERD_LIGHT = resource_path("Resources/Icon/file_zugferd_light.png")
ICON_ZUGFERD_DARK = resource_path("Resources/Icon/file_zugferd_dark.png")

ICON_SEARCH_LIST_LIGHT = resource_path("Resources/Icon/search_list_light.png")
ICON_SEARCH_LIST_DARK = resource_path("Resources/Icon/search_list_dark.png")

ICON_CIRCLE_WHITE = resource_path("Resources/Icon/circle_white.png")
ICON_CIRCLE_GREEN = resource_path("Resources/Icon/circle_green.png")
ICON_CIRCLE_ORANGE = resource_path("Resources/Icon/circle_orange.png")
ICON_CIRCLE_RED = resource_path("Resources/Icon/circle_red.png")

ICON_DELETE_LIGHT = resource_path("Resources/Icon/delete_file_light.png")
ICON_DELETE_DARK = resource_path("Resources/Icon/delete_file_dark.png")
ICON_INVOICE_LIGHT = resource_path("Resources/Icon/create_invoice_light.png")
ICON_INVOICE_DARK = resource_path("Resources/Icon/create_invoice_dark.png")
ICON_CONFIG_LIGHT = resource_path("Resources/Icon/config_light.png")
ICON_CONFIG_DARK = resource_path("Resources/Icon/config_dark.png")
ICON_OPEN_FOLDER_LIGHT = resource_path("Resources/Icon/open_folder_light.png")
ICON_OPEN_FOLDER_DARK = resource_path("Resources/Icon/open_folder_dark.png")

ICON_GIT_COMMIT = resource_path("Resources/Icon/git_commit.png")
ICON_GIT_PULL = resource_path("Resources/Icon/git_pull.png")
ICON_GIT_PUSH = resource_path("Resources/Icon/git_push.png")
ICON_CREATE_REPO = resource_path("Resources/Icon/create_repo.png")

ICON_ARROW_LEFT_LIGHT = resource_path("Resources/Icon/arrow_left_light.png")
ICON_ARROW_LEFT_DARK = resource_path("Resources/Icon/arrow_left_dark.png")
ICON_ARROW_RIGHT_LIGHT = resource_path("Resources/Icon/arrow_right_light.png")
ICON_ARROW_RIGHT_DARK = resource_path("Resources/Icon/arrow_right_dark.png")

ICON_WARNING = resource_path("Resources/Icon/warning.png")

# schemata
SCHEMATA_PATH = resource_path("Resources/schemata/")

# Git
GIT_IGNORE_FILE = resource_path("Resources/Git/template.gitignore")

# FinTS
FINTS_INSTITUTE_FILE = resource_path("Resources/FinTS/fints_institute NEU mit BIC Master.csv")

# Settings Registry
COMPANY_NAME = __author__  # **HIDDEN_LINE** COMPANY_NAME = "<COMPANY_NAME>"
APP_NAME = __title__  # **HIDDEN_LINE** APP_NAME = "<APP_NAME>"
settings_handle = QSettings(COMPANY_NAME, APP_NAME)


class ETab(int, enum.Enum):
    """!
    @brief Selected Tab in main window.
    """
    DASHBOARD = 0
    CONTACTS = 1
    INCOME = 2
    EXPENDITURE = 3
    DOCUMENT = 4
    EXPORT = 5
    SETTINGS = 6


class ETheme(str, enum.Enum):
    """!
    @brief Available application themes
    """
    LIGHT = "light"
    DARK = "dark"
    CLASSIC = "classic"
    SYSTEM = "system"


class EInvoiceOption(str, enum.Enum):
    """!
    @brief Invoice Option
    """
    EXCEL = "Excel erstellen"
    PDF = "PDF erstellen"
    XML = "X-Rechnung erstellen"
    ZUGFERD = "ZUGFeRD erstellen"


class EAiType(str, enum.Enum):
    """!
    @brief AI Type
    """
    DEACTIVATED = "Deactivated"
    OPEN_AI = "OpenAI"
    OLLAMA = "Ollama"


# sections
S_SECTION_SETTINGS = "SETTINGS"
S_SECTION_TABLE_COLUMN = "TABLE_COLUMN"
S_SECTION_AI = "AI"
S_SECTION_FINTS = "FINTS"

# keys and default values
S_KEY_TAB = "last_tab"
I_DEFAULT_TAB = ETab.DASHBOARD.value
S_KEY_THEME = "darkmode"
E_DEFAULT_THEME = ETheme.SYSTEM
S_KEY_VERBOSITY = "verbosity"
I_LOG_LEVEL_DEFAULT = logging.WARNING
S_KEY_LAST_DIR_PATH = "last_dir"
S_DEFAULT_LAST_PATH = "./"
S_KEY_OUTPUT_PATH = "output_path"
S_DEFAULT_OUTPUT_PATH = "./"
S_KEY_UPDATE_VERSION = "update_version"
S_DEFAULT_UPDATE_VERSION = "0.0.0"
S_KEY_INVOICE_OPTION = "invoice_option"
E_DEFAULT_INVOICE_OPTION = EInvoiceOption.ZUGFERD

S_KEY_CONTACTS_COLUMN = "contacts"
S_KEY_DOCUMENT_COLUMN = "document"
S_KEY_INCOME_COLUMN = "income"
S_KEY_EXPENDITURE_COLUMN = "expenditure"
D_DEFAULT_COLUMN: dict[str, Any] = {}

S_KEY_AI_TYPE = "ai_type"
E_DEFAULT_AI_TYPE = EAiType.DEACTIVATED
S_KEY_OLLAMA_MODEL = "ollama_model"
S_DEFAULT_OLLAMA_MODEL = ""
S_KEY_GPT_MODEL = "gpt_model"
S_DEFAULT_GPT_MODEL = ""
S_KEY_API_KEY = "api_key"
S_DEFAULT_API_KEY = ""

S_KEY_BLZ = "blz"
S_DEFAULT_BLZ = ""
S_KEY_URL = "alias"
S_DEFAULT_URL = ""
S_KEY_USER_ID = "user_id"
S_DEFAULT_USER_ID = ""
S_KEY_PIN = "pin"
S_DEFAULT_PIN = ""
S_KEY_IBAN = "iban"
S_DEFAULT_IBAN = ""
S_KEY_TAN_MECHANISM = "tan_mechanism"
S_DEFAULT_TAN_MECHANISM = ""


S_KEY_GEOMETRY = "window_geometry"
S_KEY_STATE = "window_state"
I_DEFAULT_WIN_WIDTH = 720
I_DEFAULT_WIN_HEIGHT = 450


def clear_settings() -> None:
    """!
    @brief Clear registry settings to write defaults at next startup
    """
    log.warning("Set default configuration settings")
    handle = get_settings_handle()
    # do not delete group S_SECTION_SALES
    for group in [S_SECTION_SETTINGS, S_SECTION_TABLE_COLUMN, S_SECTION_AI]:
        handle.beginGroup(group)
        handle.remove("")  # delete group
        handle.endGroup()


def get_settings_handle() -> QSettings:
    """!
    @brief Returns the settings handle
    @return settings handle
    """
    return settings_handle


def get_registry_value(handle: QSettings, s_key: str, b_none_err: bool = True) -> Any:
    """!
    @brief Reads the registry value with given handle and key.
    @param handle : settings handle
    @param s_key : get value for this key
    @param b_none_err : [True] call error if None in setting [False] allowed None as setting
    @return value that is mapped to the given key or raises a KeyError if key not found in handle.
    """
    value = handle.value(s_key, defaultValue=None)
    if b_none_err and (value is None):
        raise KeyError(f"{s_key} not found in group {handle.group()}")
    return value


def write_last_tab(i_tab_idx: int) -> None:
    """!
    @brief Writes the last tab to persistent storage
    @param i_tab_idx : tab index
    """
    handle = get_settings_handle()
    handle.beginGroup(S_SECTION_SETTINGS)
    handle.setValue(S_KEY_TAB, i_tab_idx)
    handle.endGroup()


def read_last_tab() -> int:
    """!
    @brief Reads the last tab from persistent storage
    @return last tab
    """
    handle = get_settings_handle()
    try:
        handle.beginGroup(S_SECTION_SETTINGS)
        i_tab_idx = int(get_registry_value(handle, S_KEY_TAB))
        _tab = ETab(i_tab_idx)  # try if valid tab index
        handle.endGroup()
    except BaseException as e:
        log.debug("Last Tab not found, using default values (%s)", str(e))
        i_tab_idx = I_DEFAULT_TAB
        handle.endGroup()
    return i_tab_idx


def write_output_path_settings(s_output_path: str) -> None:
    """!
    @brief Writes the output path settings to persistent storage
    @param s_output_path : output path
    """
    handle = get_settings_handle()
    handle.beginGroup(S_SECTION_SETTINGS)
    handle.setValue(S_KEY_OUTPUT_PATH, s_output_path)
    handle.endGroup()


def read_output_path_settings() -> str:
    """!
    @brief Reads the output path settings from persistent storage
    @return output path
    """
    handle = get_settings_handle()
    try:
        handle.beginGroup(S_SECTION_SETTINGS)
        s_output_path = str(get_registry_value(handle, S_KEY_OUTPUT_PATH))
        handle.endGroup()
    except BaseException as e:
        log.debug("Output path settings not found, using default values (%s)", str(e))
        if not os.path.exists(S_DEFAULT_OUTPUT_PATH):
            os.mkdir(S_DEFAULT_OUTPUT_PATH)
        s_output_path = S_DEFAULT_OUTPUT_PATH
        handle.endGroup()
    return s_output_path


def write_theme_settings(e_theme: ETheme) -> None:
    """!
    @brief Writes the theme settings to persistent storage
    @param e_theme : current theme
    """
    handle = get_settings_handle()
    handle.beginGroup(S_SECTION_SETTINGS)
    handle.setValue(S_KEY_THEME, e_theme.value)
    handle.endGroup()


def read_theme_settings() -> ETheme:
    """!
    @brief Reads the theme settings from persistent storage
    @return Theme settings (enum ETheme)
    """
    handle = get_settings_handle()
    try:
        handle.beginGroup(S_SECTION_SETTINGS)
        s_theme = get_registry_value(handle, S_KEY_THEME)
        e_theme = ETheme(s_theme)
        handle.endGroup()
    except BaseException as e:
        log.debug("Theme settings not found, using default values (%s)", str(e))
        e_theme = E_DEFAULT_THEME
        handle.endGroup()
    return e_theme


def save_window_state(o_geometry: QByteArray, o_state: QByteArray) -> None:
    """!
    @brief Saves the window state to persistent storage.
    @param o_geometry : geometry (position, size) of the window as QByteArray
    @param o_state : state (dock widgets etc.) of the window as QByteArray
    """
    handle = get_settings_handle()
    handle.beginGroup(S_SECTION_SETTINGS)
    handle.setValue(S_KEY_GEOMETRY, o_geometry)
    handle.setValue(S_KEY_STATE, o_state)
    handle.endGroup()


def read_window_state() -> tuple[QByteArray, QByteArray]:
    """!
    @brief Reads the window geometry and state from persistent storage.
    @return window geometry and state as QByteArray
    """
    handle = get_settings_handle()
    try:
        handle.beginGroup(S_SECTION_SETTINGS)
        o_geometry = get_registry_value(handle, S_KEY_GEOMETRY)
        o_state = get_registry_value(handle, S_KEY_STATE)
        handle.endGroup()
    except BaseException as e:
        log.debug("WindowsSettings not found, using default values (%s)", str(e))
        o_geometry = o_state = None
        handle.endGroup()
    return o_geometry, o_state


def write_update_version(version: str) -> None:
    """!
    @brief Writes the last reminded tool version for update to persistent storage.
    @param version : last reminded version
    """
    handle = get_settings_handle()
    handle.beginGroup(S_SECTION_SETTINGS)
    handle.setValue(S_KEY_UPDATE_VERSION, version)
    handle.endGroup()


def read_update_version() -> str:
    """!
    @brief Reads the last reminded tool version from persistent storage
    @return last reminded version
    """
    handle = get_settings_handle()
    try:
        handle.beginGroup(S_SECTION_SETTINGS)
        version = str(get_registry_value(handle, S_KEY_UPDATE_VERSION))
        handle.endGroup()
    except BaseException as e:
        log.debug("Update version settings not found, using default values (%s)", str(e))
        version = S_DEFAULT_UPDATE_VERSION
        handle.endGroup()
    return version


def write_last_dir(dir_path: str) -> None:
    """!
    @brief Writes the last directory to persistent storage
    @param dir_path : directory path
    """
    handle = get_settings_handle()
    handle.beginGroup(S_SECTION_SETTINGS)
    handle.setValue(S_KEY_LAST_DIR_PATH, dir_path)
    handle.endGroup()


def read_last_dir() -> str:
    """!
    @brief Reads the last directory from persistent storage
    @return directory path
    """
    handle = get_settings_handle()
    try:
        handle.beginGroup(S_SECTION_SETTINGS)
        dir_path = str(get_registry_value(handle, S_KEY_LAST_DIR_PATH))
        handle.endGroup()
    except BaseException as e:
        log.debug("Last directory settings not found, using default values (%s)", str(e))
        dir_path = S_DEFAULT_LAST_PATH
        handle.endGroup()
    return dir_path


def write_invoice_option(e_invoice_option: EInvoiceOption) -> None:
    """!
    @brief Writes the invoice option to persistent storage
    @param e_invoice_option : current invoice option
    """
    handle = get_settings_handle()
    handle.beginGroup(S_SECTION_SETTINGS)
    handle.setValue(S_KEY_INVOICE_OPTION, e_invoice_option.value)
    handle.endGroup()


def read_invoice_option() -> EInvoiceOption:
    """!
    @brief Reads the invoice option from persistent storage
    @return invoice option
    """
    handle = get_settings_handle()
    try:
        handle.beginGroup(S_SECTION_SETTINGS)
        invoice_option = EInvoiceOption(get_registry_value(handle, S_KEY_INVOICE_OPTION))
        handle.endGroup()
    except BaseException as e:
        log.debug("Invoice option not found, using default values (%s)", str(e))
        invoice_option = E_DEFAULT_INVOICE_OPTION
        handle.endGroup()
    return invoice_option


def write_table_column(key: str, d_config: dict[str, bool]) -> None:
    """!
    @brief Writes the column configuration to persistent storage
    @param key : table key name
    @param d_config : column configuration
    """
    handle = get_settings_handle()
    handle.beginGroup(S_SECTION_TABLE_COLUMN)
    handle.setValue(key, d_config)
    handle.endGroup()


def read_table_column(key: str) -> dict[str, bool]:
    """!
    @brief Reads the articles settings from persistent storage
    @param key : table key name
    @return column configuration
    """
    handle = get_settings_handle()
    try:
        handle.beginGroup(S_SECTION_TABLE_COLUMN)
        d_config = get_registry_value(handle, key)
        handle.endGroup()
    except BaseException as e:
        log.debug("Column settings not found, using default values (%s)", str(e))
        d_config = D_DEFAULT_COLUMN
        handle.endGroup()
    return d_config if isinstance(d_config, dict) else {}


def write_ai_type(ai_type: EAiType) -> None:
    """!
    @brief Writes the AI type settings to persistent storage
    @param ai_type : current AI type
    """
    handle = get_settings_handle()
    handle.beginGroup(S_SECTION_AI)
    handle.setValue(S_KEY_AI_TYPE, ai_type.value)
    handle.endGroup()


def read_ai_type() -> EAiType:
    """!
    @brief Reads the AI type settings from persistent storage
    @return AI type settings (enum EAiType)
    """
    handle = get_settings_handle()
    try:
        handle.beginGroup(S_SECTION_AI)
        s_ai_type = get_registry_value(handle, S_KEY_AI_TYPE)
        ai_type = EAiType(s_ai_type)
        handle.endGroup()
    except BaseException as e:
        log.debug("AI type settings not found, using default values (%s)", str(e))
        ai_type = E_DEFAULT_AI_TYPE
        handle.endGroup()
    return ai_type


def write_gpt_model(model: str) -> None:
    """!
    @brief Writes the GPT model settings to persistent storage
    @param model : model
    """
    handle = get_settings_handle()
    handle.beginGroup(S_SECTION_AI)
    handle.setValue(S_KEY_GPT_MODEL, model)
    handle.endGroup()


def read_gpt_model() -> str:
    """!
    @brief Reads the GPT model settings from persistent storage
    @return AI type settings
    """
    handle = get_settings_handle()
    try:
        handle.beginGroup(S_SECTION_AI)
        model = str(get_registry_value(handle, S_KEY_GPT_MODEL))
        handle.endGroup()
    except BaseException as e:
        log.debug("GPT model settings not found, using default values (%s)", str(e))
        model = S_DEFAULT_GPT_MODEL
        handle.endGroup()
    return model


def write_ollama_model(model: str) -> None:
    """!
    @brief Writes the ollama model settings to persistent storage
    @param model : model
    """
    handle = get_settings_handle()
    handle.beginGroup(S_SECTION_AI)
    handle.setValue(S_KEY_OLLAMA_MODEL, model)
    handle.endGroup()


def read_ollama_model() -> str:
    """!
    @brief Reads the Ollama model settings from persistent storage
    @return AI type settings
    """
    handle = get_settings_handle()
    try:
        handle.beginGroup(S_SECTION_AI)
        model = str(get_registry_value(handle, S_KEY_OLLAMA_MODEL))
        handle.endGroup()
    except BaseException as e:
        log.debug("Ollama model settings not found, using default values (%s)", str(e))
        model = S_DEFAULT_OLLAMA_MODEL
        handle.endGroup()
    return model


def write_api_key(api_key: str) -> None:
    """!
    @brief Writes API key to persistent storage
    @param api_key : current API key
    """
    if platform.system() == 'Windows':
        api_key_crypt = win32crypt.CryptProtectData(bytes(api_key, "utf-8")) if len(api_key) > 0 else ""
    else:
        api_key_crypt = api_key
    handle = get_settings_handle()
    handle.beginGroup(S_SECTION_AI)
    handle.setValue(S_KEY_API_KEY, api_key_crypt)
    handle.endGroup()


def read_api_key() -> str:
    """!
    @brief Reads the API key from persistent storage
    @return API key
    """
    handle = get_settings_handle()
    api_key: str
    try:
        handle.beginGroup(S_SECTION_AI)
        api_key_crypt = get_registry_value(handle, S_KEY_API_KEY)
        if platform.system() == 'Windows':
            _, bytes_api_key = win32crypt.CryptUnprotectData(api_key_crypt) if (len(api_key_crypt) > 0) else (None, bytes(api_key_crypt, "utf-8"))
            api_key = bytes_api_key.decode("utf-8")
        else:
            api_key = api_key_crypt
        handle.endGroup()
    except BaseException as e:
        log.debug("API key not found, using default values (%s)", str(e))
        api_key = S_DEFAULT_API_KEY
        handle.endGroup()
    return api_key


def write_fints_blz(s_blz: str) -> None:
    """!
    @brief Writes the FinTS BLZ to persistent storage
    @param s_blz : BLZ name
    """
    handle = get_settings_handle()
    handle.beginGroup(S_SECTION_FINTS)
    handle.setValue(S_KEY_BLZ, s_blz)
    handle.endGroup()


def read_fints_blz() -> str:
    """!
    @brief Reads the FinTS BLZ from persistent storage
    @return BLZ name
    """
    handle = get_settings_handle()
    try:
        handle.beginGroup(S_SECTION_FINTS)
        s_blz = str(get_registry_value(handle, S_KEY_BLZ))
        handle.endGroup()
    except BaseException as e:
        log.debug("FinTS BLZ not found, using default values (%s)", str(e))
        s_blz = S_DEFAULT_BLZ
        handle.endGroup()
    return s_blz


def write_fints_url(s_url: str) -> None:
    """!
    @brief Writes the FinTS URL to persistent storage
    @param s_url : URL
    """
    handle = get_settings_handle()
    handle.beginGroup(S_SECTION_FINTS)
    handle.setValue(S_KEY_URL, s_url)
    handle.endGroup()


def read_fints_url() -> str:
    """!
    @brief Reads the FinTS URL from persistent storage
    @return URL
    """
    handle = get_settings_handle()
    try:
        handle.beginGroup(S_SECTION_FINTS)
        s_url = str(get_registry_value(handle, S_KEY_URL))
        handle.endGroup()
    except BaseException as e:
        log.debug("FinTS URL not found, using default values (%s)", str(e))
        s_url = S_DEFAULT_URL
        handle.endGroup()
    return s_url


def write_fints_auth_data(user_id: str, pin: str) -> None:
    """!
    @brief Writes FinTS authentication data to persistent storage
    @param user_id : user id
    @param pin : pin
    """
    if platform.system() == 'Windows':
        user_id_crypt = win32crypt.CryptProtectData(bytes(user_id, "utf-8")) if len(user_id) > 0 else ""
        pin_crypt = win32crypt.CryptProtectData(bytes(pin, "utf-8")) if len(pin) > 0 else ""
    else:
        user_id_crypt = user_id
        pin_crypt = pin
    handle = get_settings_handle()
    handle.beginGroup(S_SECTION_FINTS)
    handle.setValue(S_KEY_USER_ID, user_id_crypt)
    handle.setValue(S_KEY_PIN, pin_crypt)
    handle.endGroup()


def read_fints_auth_data() -> tuple[str, str]:
    """!
    @brief Reads the FinTS authentication data from persistent storage
    @return user ID and pin
    """
    handle = get_settings_handle()
    user_id: str
    pin: str
    try:
        handle.beginGroup(S_SECTION_FINTS)
        user_id_crypt = get_registry_value(handle, S_KEY_USER_ID)
        pin_crypt = get_registry_value(handle, S_KEY_PIN)
        if platform.system() == 'Windows':
            _, bytes_user_id = win32crypt.CryptUnprotectData(user_id_crypt) if (len(user_id_crypt) > 0) else (None, bytes(user_id_crypt, "utf-8"))
            user_id = bytes_user_id.decode("utf-8")
            _, bytes_pin = win32crypt.CryptUnprotectData(pin_crypt) if (len(pin_crypt) > 0) else (None, bytes(pin_crypt, "utf-8"))
            pin = bytes_pin.decode("utf-8")
        else:
            user_id = user_id_crypt
            pin = pin_crypt
        handle.endGroup()
    except BaseException as e:
        log.debug("FinTS Auth data not found, using default values (%s)", str(e))
        user_id = S_DEFAULT_USER_ID
        pin = S_DEFAULT_PIN
        handle.endGroup()
    return user_id, pin


def write_fints_iban(s_iban: str) -> None:
    """!
    @brief Writes the FinTS IBAN to persistent storage
    @param s_iban : IBAN
    """
    handle = get_settings_handle()
    handle.beginGroup(S_SECTION_FINTS)
    handle.setValue(S_KEY_IBAN, s_iban)
    handle.endGroup()


def read_fints_iban() -> str:
    """!
    @brief Reads the FinTS IBAN from persistent storage
    @return IBAN
    """
    handle = get_settings_handle()
    try:
        handle.beginGroup(S_SECTION_FINTS)
        s_iban = str(get_registry_value(handle, S_KEY_IBAN))
        handle.endGroup()
    except BaseException as e:
        log.debug("FinTS IBAN not found, using default values (%s)", str(e))
        s_iban = S_DEFAULT_IBAN
        handle.endGroup()
    return s_iban


def write_fints_tan_mechanism(s_tan_mechanism: str) -> None:
    """!
    @brief Writes the FinTS tan mechanism to persistent storage
    @param s_tan_mechanism : tan mechanism
    """
    handle = get_settings_handle()
    handle.beginGroup(S_SECTION_FINTS)
    handle.setValue(S_KEY_TAN_MECHANISM, s_tan_mechanism)
    handle.endGroup()


def read_fints_tan_mechanism() -> str:
    """!
    @brief Reads the FinTS tan mechanism from persistent storage
    @return tan mechanism
    """
    handle = get_settings_handle()
    try:
        handle.beginGroup(S_SECTION_FINTS)
        s_tan_mechanism = str(get_registry_value(handle, S_KEY_TAN_MECHANISM))
        handle.endGroup()
    except BaseException as e:
        log.debug("FinTS tan mechanism not found, using default values (%s)", str(e))
        s_tan_mechanism = S_DEFAULT_TAN_MECHANISM
        handle.endGroup()
    return s_tan_mechanism
