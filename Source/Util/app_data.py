"""!
********************************************************************************
@file   app_data.py
@brief  Data module (path related constants and functions)
********************************************************************************
"""

# autopep8: off
import sys
import os
import io
import logging
import enum
from collections.abc import Callable
from typing import Any, TYPE_CHECKING
import socket
import platform
import subprocess
from subprocess import CompletedProcess
import traceback
import importlib.util
import inspect

from packaging.version import Version

IS_WINDOWS = platform.system() == 'Windows'

if IS_WINDOWS:
    import win32crypt  # pylint: disable=import-error
else:
    win32crypt = None

from PyQt6.QtCore import QSettings, QByteArray  # pylint: disable=wrong-import-position
from PyQt6.QtGui import QActionGroup, QAction  # pylint: disable=wrong-import-position

from Source.version import __title__, __author__, running_as_exe  # pylint: disable=wrong-import-position
if TYPE_CHECKING:
    from Source.Controller.main_window import MainWindow
# autopep8: on

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


def resource_path(relative_path: str) -> str:
    """!
    @brief Get the absolute path to a resource given by a relative path depending on the environment (EXE or Python).
    @param relative_path : the relative path to a file or directory.
    @return absolute path to the resource.
    """
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("../"))
    full_path = os.path.join(base_path, relative_path)
    log.debug("Resource Path (relative %s): %s", relative_path, full_path)
    return full_path


def thread_dialog(dialog: Any) -> None:
    """!
    @brief Execute dialog with exception handling to display errors via the main thread.
    @param dialog : thread dialog object with show_dialog() and ui attributes.
    """
    try:
        dialog.show_dialog()
    except Exception:
        exc_type, exc_value, exc_tb = sys.exc_info()
        err_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))  # complete stacktrace
        log.error(err_msg)
        dialog.ui.qt_exception_hook.exception_caught.emit(err_msg)


def run_subprocess(command: list[str]) -> CompletedProcess[str]:
    """!
    @brief Run subprocess without opening a terminal window.
    @param command : command line arguments list for subprocess.run.
    @return CompletedProcess with captured stdout and stderr.
    """
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    result = subprocess.run(command, capture_output=True, text=True, check=True, startupinfo=startupinfo)
    return result


def open_subprocess(command: list[str]) -> None:
    """!
    @brief Open a subprocess without opening a terminal window (non-blocking).
    @param command : command line arguments list for subprocess.Popen.
    """
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    with subprocess.Popen(command, text=True, startupinfo=startupinfo):
        pass


def get_computer_name() -> str:
    """!
    @brief Return the local machine's hostname, or empty string on failure.
    @return hostname of the local machine, or empty string on failure.
    """
    try:
        hostname = socket.gethostname()
    except Exception:
        hostname = ""
    return hostname


def open_explorer(explorer_path: str, open_folder: bool = False) -> None:
    """!
    @brief Open Windows Explorer at the given path.
    @param explorer_path : file or folder path to reveal in Windows Explorer.
    @param open_folder : True to open the folder directly, False to open explorer with the item selected.
    """
    win_path = explorer_path.replace("/", "\\")
    command = f"explorer {win_path}" if open_folder else f"explorer /select, {win_path}"
    with subprocess.Popen(command):
        pass


def group_menu(parent: "MainWindow", actions: list[QAction], current_value: Any, match_values: list[Any]) -> QActionGroup:
    """!
    @brief Create an exclusive action group and check the matching action.
    @param parent : parent window controller.
    @param actions : list of QAction objects to add.
    @param current_value : current setting value.
    @param match_values : list of possible values to match against the current setting.
    @return exclusive action group object.
    """
    action_group = QActionGroup(parent)
    for action in actions:
        action_group.addAction(action)
    for i, match_value in enumerate(match_values):
        if match_value == current_value:
            actions[i].setChecked(True)
            break
    return action_group


def try_load_plugin(name: str, path: str) -> Any:
    """!
    @brief Try to load a Python plugin module from a file path.
    @param name : plugin module name.
    @param path : file path to the plugin module.
    @return loaded module or None if file not found.
    """
    if os.path.isfile(path):
        spec = importlib.util.spec_from_file_location(name, path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        else:
            module = None
    else:
        module = None
    return module


def function_accepts_params(func: Callable[..., object], *args: object) -> bool:
    """!
    @brief Check if a function signature accepts the given arguments.
    @param func : callable to check.
    @param args : arguments to validate against function signature.
    @return True if function accepts the arguments, False otherwise.
    """
    sig = inspect.signature(func)
    try:
        sig.bind(*args)
        return True
    except TypeError:
        return False


# Files and Paths
# https://icons8.com/icons/fluency-systems-regular
# https://www.flaticon.com/free-icon/list-search_7560656
# https://compresspng.com/
# https://ezgif.com/optimize
# https://compress-image.net/compress-image-online/compress-ico
# https://www.zamzar.com/compress-bmp/
# https://invert.imageonline.co/de/
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
ICON_ARROW_UP_LIGHT = resource_path("Resources/Icon/arrow_up_light.png")
ICON_ARROW_UP_DARK = resource_path("Resources/Icon/arrow_up_dark.png")
ICON_ARROW_DOWN_LIGHT = resource_path("Resources/Icon/arrow_down_light.png")
ICON_ARROW_DOWN_DARK = resource_path("Resources/Icon/arrow_down_dark.png")

ICON_UPDATE_LIGHT = resource_path("Resources/Icon/update_light.svg")
ICON_UPDATE_DARK = resource_path("Resources/Icon/update_dark.svg")
ICON_TICK_GREEN = resource_path("Resources/Icon/tick_green.png")
ICON_CROSS_RED = resource_path("Resources/Icon/cross_red.png")
ICON_LICENSE_LIGHT = resource_path("Resources/Icon/license_light.png")
ICON_LICENSE_DARK = resource_path("Resources/Icon/license_dark.png")

ICON_WARNING = resource_path("Resources/Icon/warning.png")

ICON_OLLAMA_LIGHT = resource_path("Resources/Icon/ollama_light.png")
ICON_OLLAMA_DARK = resource_path("Resources/Icon/ollama_dark.png")
ICON_OPEN_AI_LIGHT = resource_path("Resources/Icon/openai_light.png")
ICON_OPEN_AI_DARK = resource_path("Resources/Icon/openai_dark.png")
ICON_GEMINI = resource_path("Resources/Icon/gemini.png")
ICON_MISTRAL = resource_path("Resources/Icon/mistral.png")

# License
LICENSE_FILE = resource_path("LICENSE.md")

# schemata
SCHEMATA_PATH = resource_path("Resources/schemata/")

# Git
GIT_IGNORE_FILE = resource_path("Resources/Git/template.gitignore")

# Fonts
# https://github.com/liberationfonts/liberation-fonts/files/7261482/liberation-fonts-ttf-2.1.5.tar.gz
FONT_LIBERATION_MONO_BOLD = resource_path("Resources/Fonts/LiberationMono-Bold.ttf")
FONT_LIBERATION_MONO_BOLD_ITALIC = resource_path("Resources/Fonts/LiberationMono-BoldItalic.ttf")
FONT_LIBERATION_MONO_ITALIC = resource_path("Resources/Fonts/LiberationMono-Italic.ttf")
FONT_LIBERATION_MONO_REGULAR = resource_path("Resources/Fonts/LiberationMono-Regular.ttf")
FONT_LIBERATION_SANS_BOLD = resource_path("Resources/Fonts/LiberationSans-Bold.ttf")
FONT_LIBERATION_SANS_BOLD_ITALIC = resource_path("Resources/Fonts/LiberationSans-BoldItalic.ttf")
FONT_LIBERATION_SANS_ITALIC = resource_path("Resources/Fonts/LiberationSans-Italic.ttf")
FONT_LIBERATION_SANS_REGULAR = resource_path("Resources/Fonts/LiberationSans-Regular.ttf")
FONT_LIBERATION_SERIF_BOLD = resource_path("Resources/Fonts/LiberationSerif-Bold.ttf")
FONT_LIBERATION_SERIF_BOLD_ITALIC = resource_path("Resources/Fonts/LiberationSerif-BoldItalic.ttf")
FONT_LIBERATION_SERIF_ITALIC = resource_path("Resources/Fonts/LiberationSerif-Italic.ttf")
FONT_LIBERATION_SERIF_REGULAR = resource_path("Resources/Fonts/LiberationSerif-Regular.ttf")

# FinTS
# https://python-fints.readthedocs.io/en/latest/quickstart.html#register-for-a-product-id
FINTS_INSTITUTE_FILE = resource_path("Resources/FinTS/fints_institute NEU mit BIC Master.csv")

# Settings Registry
ORGANIZATION_NAME = __author__
APPLICATION_NAME = __title__
SETTINGS_HANDLE = QSettings(ORGANIZATION_NAME, APPLICATION_NAME)


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


class DocView(enum.IntEnum):
    """!
    @brief Index of document view.
    """
    PDF = 0
    XML = 1


class ETheme(str, enum.Enum):
    """!
    @brief Available application themes.
    """
    LIGHT = "light"
    DARK = "dark"
    CLASSIC = "classic"
    SYSTEM = "system"


class EInvoiceOption(str, enum.Enum):
    """!
    @brief Available invoice output format options.
    """
    EXCEL = "Excel erstellen"
    PDF = "PDF erstellen"
    XML = "X-Rechnung erstellen"
    ZUGFERD = "ZUGFeRD erstellen"


class EAiType(str, enum.Enum):
    """!
    @brief Available AI provider types.
    """
    DEACTIVATED = "Deactivated"
    OPEN_AI = "OpenAI"
    GEMINI = "Gemini"
    MISTRAL = "Mistral"
    OLLAMA = "Ollama"


# sections
SECTION_SETTINGS = "SETTINGS"
SECTION_TABLE_COLUMN = "TABLE_COLUMN"
SECTION_AI = "AI"
SECTION_FINTS = "FINTS"

# keys and default values
KEY_TAB = "last_tab"
DEFAULT_TAB = ETab.DASHBOARD.value
KEY_DOC_VIEW = "last_doc_view"
DEFAULT_DOC_VIEW = DocView.PDF
KEY_THEME = "darkmode"
DEFAULT_THEME = ETheme.SYSTEM
KEY_VERBOSITY = "verbosity"
DEFAULT_LOG_LEVEL = logging.WARNING
KEY_LAST_DIR_PATH = "last_dir"
DEFAULT_LAST_PATH = "./"
KEY_OUTPUT_PATH = "output_path"
DEFAULT_OUTPUT_PATH = "./"
KEY_UPDATE_VERSION = "update_version"
DEFAULT_UPDATE_VERSION = "0.0.0"
KEY_INVOICE_OPTION = "invoice_option"
DEFAULT_INVOICE_OPTION = EInvoiceOption.ZUGFERD
KEY_QR_CODE = "qr_code"
DEFAULT_QR_CODE = False

KEY_CONTACTS_COLUMN = "contacts"
KEY_DOCUMENT_COLUMN = "document"
KEY_INCOME_COLUMN = "income"
KEY_EXPENDITURE_COLUMN = "expenditure"
DEFAULT_COLUMN: dict[str, Any] = {}

KEY_AI_TYPE = "ai_type"
DEFAULT_AI_TYPE = EAiType.DEACTIVATED
KEY_OLLAMA_MODEL = "ollama_model"
DEFAULT_OLLAMA_MODEL = ""
KEY_GPT_MODEL = "gpt_model"
DEFAULT_GPT_MODEL = ""
KEY_GEMINI_MODEL = "gemini_model"
DEFAULT_GEMINI_MODEL = ""
KEY_MISTRAL_MODEL = "mistral_model"
DEFAULT_MISTRAL_MODEL = ""
KEY_GPT_API_KEY = "api_key"
DEFAULT_GPT_API_KEY = ""
KEY_GEMINI_API_KEY = "gemini_api_key"
DEFAULT_GEMINI_API_KEY = ""
KEY_MISTRAL_API_KEY = "mistral_api_key"
DEFAULT_MISTRAL_API_KEY = ""

KEY_BLZ = "blz"
DEFAULT_BLZ = ""
KEY_URL = "alias"
DEFAULT_URL = ""
KEY_USER_ID = "user_id"
DEFAULT_USER_ID = ""
KEY_PIN = "pin"
DEFAULT_PIN = ""
KEY_IBAN = "iban"
DEFAULT_IBAN = ""
KEY_TAN_MECHANISM = "tan_mechanism"
DEFAULT_TAN_MECHANISM = ""


KEY_GEOMETRY = "window_geometry"
KEY_STATE = "window_state"
DEFAULT_WIN_WIDTH = 720
DEFAULT_WIN_HEIGHT = 450


def get_settings_handle() -> QSettings:
    """!
    @brief Get the settings handle.
    @return global QSettings instance for reading and writing persistent configuration.
    """
    return SETTINGS_HANDLE


def get_registry_value(handle: QSettings, key: str, none_err: bool = True) -> Any:
    """!
    @brief Reads the registry value with given handle and key.
    @param handle : QSettings/SETTINGS instance positioned within a group.
    @param key : registry key to look up.
    @param none_err : [True] raise error if setting is None; [False] allow None as valid setting.
    @return value that is mapped to the given key or raises a KeyError if key not found in handle.
    """
    value = handle.value(key, defaultValue=None)
    if none_err and value is None:
        raise KeyError(f"{key} not found in group {handle.group()}")
    return value


def _encrypt_string(value: str) -> str | bytes:
    """!
    @brief Encrypt a string using Windows DPAPI, or return it unchanged on other platforms.
    @param value : plaintext string to encrypt.
    @return encrypted bytes on Windows, or the original string on other platforms.
    """
    if IS_WINDOWS and len(value) > 0:
        result: bytes = win32crypt.CryptProtectData(bytes(value, "utf-8"))  # pylint: disable=possibly-used-before-assignment
        return result
    return value


def _decrypt_string(encrypted_value: str | bytes) -> str:
    """!
    @brief Decrypt a DPAPI-encrypted value, or return it unchanged on other platforms.
    @param encrypted_value : encrypted bytes on Windows, or plaintext string on other platforms.
    @return decrypted plaintext string.
    """
    if IS_WINDOWS and len(encrypted_value) > 0:
        _, decrypted_bytes = win32crypt.CryptUnprotectData(encrypted_value)
        result: str = decrypted_bytes.decode("utf-8")
        return result
    return encrypted_value if isinstance(encrypted_value, str) else ""


def clear_settings() -> None:
    """!
    @brief Clear registry settings to write defaults at next startup.
    """
    log.warning("Set default configuration settings")
    handle = get_settings_handle()
    # do not delete group SECTION_SALES
    for group in [SECTION_SETTINGS, SECTION_TABLE_COLUMN, SECTION_AI]:
        handle.beginGroup(group)
        handle.remove("")  # delete group
        handle.endGroup()


def write_last_tab(tab_idx: int) -> None:
    """!
    @brief Writes the last tab to persistent storage.
    @param tab_idx : tab index.
    """
    handle = get_settings_handle()
    handle.beginGroup(SECTION_SETTINGS)
    handle.setValue(KEY_TAB, tab_idx)
    handle.endGroup()


def read_last_tab() -> int:
    """!
    @brief Reads the last tab from persistent storage.
    @return last selected tab index.
    """
    handle = get_settings_handle()
    try:
        handle.beginGroup(SECTION_SETTINGS)
        tab_idx = int(get_registry_value(handle, KEY_TAB))
        ETab(tab_idx)  # try if valid tab index
    except Exception as e:
        log.debug("Last Tab not found, using default values (%s)", str(e))
        tab_idx = DEFAULT_TAB
    finally:
        handle.endGroup()
    return tab_idx


def write_last_doc_view(view: DocView) -> None:
    """!
    @brief Writes the last document view to persistent storage.
    @param view : document view.
    """
    handle = get_settings_handle()
    handle.beginGroup(SECTION_SETTINGS)
    handle.setValue(KEY_DOC_VIEW, view.value)
    handle.endGroup()


def read_last_doc_view() -> DocView:
    """!
    @brief Reads the last document view from persistent storage.
    @return last document view.
    """
    handle = get_settings_handle()
    try:
        handle.beginGroup(SECTION_SETTINGS)
        view_index = int(get_registry_value(handle, KEY_DOC_VIEW))
        view = DocView(view_index)
    except Exception as e:
        log.debug("Last View not found, using default values (%s)", str(e))
        view = DEFAULT_DOC_VIEW
    finally:
        handle.endGroup()
    return view


def write_output_path_settings(output_path: str) -> None:
    """!
    @brief Writes the output path settings to persistent storage.
    @param output_path : file output directory path.
    """
    handle = get_settings_handle()
    handle.beginGroup(SECTION_SETTINGS)
    handle.setValue(KEY_OUTPUT_PATH, output_path)
    handle.endGroup()


def read_output_path_settings() -> str:
    """!
    @brief Reads the output path settings from persistent storage.
    @return file output directory path.
    """
    handle = get_settings_handle()
    try:
        handle.beginGroup(SECTION_SETTINGS)
        output_path = str(get_registry_value(handle, KEY_OUTPUT_PATH))
    except Exception as e:
        log.debug("Output path settings not found, using default values (%s)", str(e))
        if not os.path.exists(DEFAULT_OUTPUT_PATH):
            os.mkdir(DEFAULT_OUTPUT_PATH)
        output_path = DEFAULT_OUTPUT_PATH
    finally:
        handle.endGroup()
    return output_path


def write_theme_settings(theme: ETheme) -> None:
    """!
    @brief Writes the theme settings to persistent storage.
    @param theme : current theme.
    """
    handle = get_settings_handle()
    handle.beginGroup(SECTION_SETTINGS)
    handle.setValue(KEY_THEME, theme.value)
    handle.endGroup()


def read_theme_settings() -> ETheme:
    """!
    @brief Reads the theme settings from persistent storage.
    @return Theme settings (enum ETheme).
    """
    handle = get_settings_handle()
    try:
        handle.beginGroup(SECTION_SETTINGS)
        theme_value = get_registry_value(handle, KEY_THEME)
        theme = ETheme(theme_value)
    except Exception as e:
        log.debug("Theme settings not found, using default values (%s)", str(e))
        theme = DEFAULT_THEME
    finally:
        handle.endGroup()
    return theme


def write_window_state(geometry: QByteArray, state: QByteArray) -> None:
    """!
    @brief Writes the window geometry and state to persistent storage.
    @param geometry : geometry (position, size) of the window as QByteArray.
    @param state : state (dock widgets etc.) of the window as QByteArray.
    """
    handle = get_settings_handle()
    handle.beginGroup(SECTION_SETTINGS)
    handle.setValue(KEY_GEOMETRY, geometry)
    handle.setValue(KEY_STATE, state)
    handle.endGroup()


def read_window_state() -> tuple[QByteArray | None, QByteArray | None]:
    """!
    @brief Reads the window geometry and state from persistent storage.
    @return window geometry and state as QByteArray.
    """
    handle = get_settings_handle()
    try:
        handle.beginGroup(SECTION_SETTINGS)
        geometry = get_registry_value(handle, KEY_GEOMETRY)
        state = get_registry_value(handle, KEY_STATE)
    except Exception as e:
        log.debug("WindowsSettings not found, using default values (%s)", str(e))
        geometry = state = None
    finally:
        handle.endGroup()
    return geometry, state


def write_update_version(version: str) -> None:
    """!
    @brief Writes the last reminded tool version for update to persistent storage.
    @param version : last reminded version.
    """
    handle = get_settings_handle()
    handle.beginGroup(SECTION_SETTINGS)
    handle.setValue(KEY_UPDATE_VERSION, version)
    handle.endGroup()


def read_update_version() -> str:
    """!
    @brief Reads the last reminded tool version from persistent storage.
    @return last reminded version.
    """
    handle = get_settings_handle()
    try:
        handle.beginGroup(SECTION_SETTINGS)
        version = str(get_registry_value(handle, KEY_UPDATE_VERSION))
        Version(version)  # try if valid version
    except Exception as e:
        log.debug("Update version settings not found, using default values (%s)", str(e))
        version = DEFAULT_UPDATE_VERSION
    finally:
        handle.endGroup()
    return version


def write_last_dir(dir_path: str) -> None:
    """!
    @brief Writes the last directory to persistent storage.
    @param dir_path : directory path.
    """
    handle = get_settings_handle()
    handle.beginGroup(SECTION_SETTINGS)
    handle.setValue(KEY_LAST_DIR_PATH, dir_path)
    handle.endGroup()


def read_last_dir() -> str:
    """!
    @brief Reads the last directory from persistent storage.
    @return directory path.
    """
    handle = get_settings_handle()
    try:
        handle.beginGroup(SECTION_SETTINGS)
        dir_path = str(get_registry_value(handle, KEY_LAST_DIR_PATH))
    except Exception as e:
        log.debug("Last directory settings not found, using default values (%s)", str(e))
        dir_path = DEFAULT_LAST_PATH
    finally:
        handle.endGroup()
    return dir_path


def write_invoice_option(invoice_option: EInvoiceOption) -> None:
    """!
    @brief Writes the invoice option to persistent storage.
    @param invoice_option : current invoice option.
    """
    handle = get_settings_handle()
    handle.beginGroup(SECTION_SETTINGS)
    handle.setValue(KEY_INVOICE_OPTION, invoice_option.value)
    handle.endGroup()


def read_invoice_option() -> EInvoiceOption:
    """!
    @brief Reads the invoice option from persistent storage.
    @return current invoice option.
    """
    handle = get_settings_handle()
    try:
        handle.beginGroup(SECTION_SETTINGS)
        invoice_option = EInvoiceOption(get_registry_value(handle, KEY_INVOICE_OPTION))
    except Exception as e:
        log.debug("Invoice option not found, using default values (%s)", str(e))
        invoice_option = DEFAULT_INVOICE_OPTION
    finally:
        handle.endGroup()
    return invoice_option


def write_qr_code_settings(qr_code: bool) -> None:
    """!
    @brief Writes the QR code settings to persistent storage.
    @param qr_code : QR code status.
    """
    handle = get_settings_handle()
    handle.beginGroup(SECTION_SETTINGS)
    handle.setValue(KEY_QR_CODE, qr_code)
    handle.endGroup()


def read_qr_code_settings() -> bool:
    """!
    @brief Reads the QR code settings from persistent storage.
    @return True if QR code is enabled.
    """
    handle = get_settings_handle()
    try:
        handle.beginGroup(SECTION_SETTINGS)
        qr_code = bool(get_registry_value(handle, KEY_QR_CODE) == "true")
    except Exception as e:
        log.debug("QR Code not found, using default values (%s)", str(e))
        qr_code = DEFAULT_QR_CODE
    finally:
        handle.endGroup()
    return qr_code


def write_table_column(key: str, config: dict[str, bool]) -> None:
    """!
    @brief Writes the column configuration to persistent storage.
    @param key : table key name.
    @param config : column configuration.
    """
    handle = get_settings_handle()
    handle.beginGroup(SECTION_TABLE_COLUMN)
    handle.setValue(key, config)
    handle.endGroup()


def read_table_column(key: str) -> dict[str, bool]:
    """!
    @brief Reads the column configuration from persistent storage.
    @param key : table key name.
    @return column configuration.
    """
    handle = get_settings_handle()
    try:
        handle.beginGroup(SECTION_TABLE_COLUMN)
        config = get_registry_value(handle, key)
    except Exception as e:
        log.debug("Column settings not found, using default values (%s)", str(e))
        config = DEFAULT_COLUMN
    finally:
        handle.endGroup()
    return config if isinstance(config, dict) else {}


def write_ai_type(ai_type: EAiType) -> None:
    """!
    @brief Writes the AI type settings to persistent storage.
    @param ai_type : current AI type.
    """
    handle = get_settings_handle()
    handle.beginGroup(SECTION_AI)
    handle.setValue(KEY_AI_TYPE, ai_type.value)
    handle.endGroup()


def read_ai_type() -> EAiType:
    """!
    @brief Reads the AI type settings from persistent storage.
    @return AI type settings (enum EAiType).
    """
    handle = get_settings_handle()
    try:
        handle.beginGroup(SECTION_AI)
        ai_type_value = get_registry_value(handle, KEY_AI_TYPE)
        ai_type = EAiType(ai_type_value)
    except Exception as e:
        log.debug("AI type settings not found, using default values (%s)", str(e))
        ai_type = DEFAULT_AI_TYPE
    finally:
        handle.endGroup()
    return ai_type


def write_gpt_model(model: str) -> None:
    """!
    @brief Writes the GPT model settings to persistent storage.
    @param model : model name.
    """
    handle = get_settings_handle()
    handle.beginGroup(SECTION_AI)
    handle.setValue(KEY_GPT_MODEL, model)
    handle.endGroup()


def read_gpt_model() -> str:
    """!
    @brief Reads the GPT model settings from persistent storage.
    @return GPT model name.
    """
    handle = get_settings_handle()
    try:
        handle.beginGroup(SECTION_AI)
        model = str(get_registry_value(handle, KEY_GPT_MODEL))
    except Exception as e:
        log.debug("GPT model settings not found, using default values (%s)", str(e))
        model = DEFAULT_GPT_MODEL
    finally:
        handle.endGroup()
    return model


def write_gemini_model(model: str) -> None:
    """!
    @brief Writes the Gemini model settings to persistent storage.
    @param model : model name.
    """
    handle = get_settings_handle()
    handle.beginGroup(SECTION_AI)
    handle.setValue(KEY_GEMINI_MODEL, model)
    handle.endGroup()


def read_gemini_model() -> str:
    """!
    @brief Reads the Gemini model settings from persistent storage.
    @return Gemini model name.
    """
    handle = get_settings_handle()
    try:
        handle.beginGroup(SECTION_AI)
        model = str(get_registry_value(handle, KEY_GEMINI_MODEL))
    except Exception as e:
        log.debug("Gemini model settings not found, using default values (%s)", str(e))
        model = DEFAULT_GEMINI_MODEL
    finally:
        handle.endGroup()
    return model


def write_mistral_model(model: str) -> None:
    """!
    @brief Writes the Mistral model settings to persistent storage.
    @param model : model name.
    """
    handle = get_settings_handle()
    handle.beginGroup(SECTION_AI)
    handle.setValue(KEY_MISTRAL_MODEL, model)
    handle.endGroup()


def read_mistral_model() -> str:
    """!
    @brief Reads the Mistral model settings from persistent storage.
    @return Mistral model name.
    """
    handle = get_settings_handle()
    try:
        handle.beginGroup(SECTION_AI)
        model = str(get_registry_value(handle, KEY_MISTRAL_MODEL))
    except Exception as e:
        log.debug("Mistral model settings not found, using default values (%s)", str(e))
        model = DEFAULT_MISTRAL_MODEL
    finally:
        handle.endGroup()
    return model


def write_ollama_model(model: str) -> None:
    """!
    @brief Writes the Ollama model settings to persistent storage.
    @param model : model name.
    """
    handle = get_settings_handle()
    handle.beginGroup(SECTION_AI)
    handle.setValue(KEY_OLLAMA_MODEL, model)
    handle.endGroup()


def read_ollama_model() -> str:
    """!
    @brief Reads the Ollama model settings from persistent storage.
    @return Ollama model name.
    """
    handle = get_settings_handle()
    try:
        handle.beginGroup(SECTION_AI)
        model = str(get_registry_value(handle, KEY_OLLAMA_MODEL))
    except Exception as e:
        log.debug("Ollama model settings not found, using default values (%s)", str(e))
        model = DEFAULT_OLLAMA_MODEL
    finally:
        handle.endGroup()
    return model


def write_gpt_api_key(api_key: str) -> None:
    """!
    @brief Writes GPT API key to persistent storage.
    @param api_key : current API key.
    """
    handle = get_settings_handle()
    handle.beginGroup(SECTION_AI)
    handle.setValue(KEY_GPT_API_KEY, _encrypt_string(api_key))
    handle.endGroup()


def read_gpt_api_key() -> str:
    """!
    @brief Reads the GPT API key from persistent storage.
    @return API key.
    """
    handle = get_settings_handle()
    try:
        handle.beginGroup(SECTION_AI)
        api_key = _decrypt_string(get_registry_value(handle, KEY_GPT_API_KEY))
    except Exception as e:
        log.debug("API key not found, using default values (%s)", str(e))
        api_key = DEFAULT_GPT_API_KEY
    finally:
        handle.endGroup()
    return api_key


def write_gemini_api_key(api_key: str) -> None:
    """!
    @brief Writes Gemini API key to persistent storage.
    @param api_key : current API key.
    """
    handle = get_settings_handle()
    handle.beginGroup(SECTION_AI)
    handle.setValue(KEY_GEMINI_API_KEY, _encrypt_string(api_key))
    handle.endGroup()


def read_gemini_api_key() -> str:
    """!
    @brief Reads the Gemini API key from persistent storage.
    @return API key.
    """
    handle = get_settings_handle()
    try:
        handle.beginGroup(SECTION_AI)
        api_key = _decrypt_string(get_registry_value(handle, KEY_GEMINI_API_KEY))
    except Exception as e:
        log.debug("API key not found, using default values (%s)", str(e))
        api_key = DEFAULT_GEMINI_API_KEY
    finally:
        handle.endGroup()
    return api_key


def write_mistral_api_key(api_key: str) -> None:
    """!
    @brief Writes Mistral API key to persistent storage.
    @param api_key : current API key.
    """
    handle = get_settings_handle()
    handle.beginGroup(SECTION_AI)
    handle.setValue(KEY_MISTRAL_API_KEY, _encrypt_string(api_key))
    handle.endGroup()


def read_mistral_api_key() -> str:
    """!
    @brief Reads the Mistral API key from persistent storage.
    @return API key.
    """
    handle = get_settings_handle()
    try:
        handle.beginGroup(SECTION_AI)
        api_key = _decrypt_string(get_registry_value(handle, KEY_MISTRAL_API_KEY))
    except Exception as e:
        log.debug("API key not found, using default values (%s)", str(e))
        api_key = DEFAULT_MISTRAL_API_KEY
    finally:
        handle.endGroup()
    return api_key


def write_fints_blz(blz: str) -> None:
    """!
    @brief Writes the FinTS BLZ to persistent storage.
    @param blz : bank code (Bankleitzahl).
    """
    handle = get_settings_handle()
    handle.beginGroup(SECTION_FINTS)
    handle.setValue(KEY_BLZ, blz)
    handle.endGroup()


def read_fints_blz() -> str:
    """!
    @brief Reads the FinTS BLZ from persistent storage.
    @return bank code (Bankleitzahl).
    """
    handle = get_settings_handle()
    try:
        handle.beginGroup(SECTION_FINTS)
        blz = str(get_registry_value(handle, KEY_BLZ))
    except Exception as e:
        log.debug("FinTS BLZ not found, using default values (%s)", str(e))
        blz = DEFAULT_BLZ
    finally:
        handle.endGroup()
    return blz


def write_fints_url(url: str) -> None:
    """!
    @brief Writes the FinTS URL to persistent storage.
    @param url : FinTS server URL.
    """
    handle = get_settings_handle()
    handle.beginGroup(SECTION_FINTS)
    handle.setValue(KEY_URL, url)
    handle.endGroup()


def read_fints_url() -> str:
    """!
    @brief Reads the FinTS URL from persistent storage.
    @return FinTS server URL.
    """
    handle = get_settings_handle()
    try:
        handle.beginGroup(SECTION_FINTS)
        url = str(get_registry_value(handle, KEY_URL))
    except Exception as e:
        log.debug("FinTS URL not found, using default values (%s)", str(e))
        url = DEFAULT_URL
    finally:
        handle.endGroup()
    return url


def write_fints_auth_data(user_id: str, pin: str) -> None:
    """!
    @brief Writes FinTS authentication data to persistent storage.
    @param user_id : FinTS user ID.
    @param pin : FinTS PIN.
    """
    handle = get_settings_handle()
    handle.beginGroup(SECTION_FINTS)
    handle.setValue(KEY_USER_ID, _encrypt_string(user_id))
    handle.setValue(KEY_PIN, _encrypt_string(pin))
    handle.endGroup()


def read_fints_auth_data() -> tuple[str, str]:
    """!
    @brief Reads the FinTS authentication data from persistent storage.
    @return user ID and PIN.
    """
    handle = get_settings_handle()
    try:
        handle.beginGroup(SECTION_FINTS)
        user_id = _decrypt_string(get_registry_value(handle, KEY_USER_ID))
        pin = _decrypt_string(get_registry_value(handle, KEY_PIN))
    except Exception as e:
        log.debug("FinTS Auth data not found, using default values (%s)", str(e))
        user_id = DEFAULT_USER_ID
        pin = DEFAULT_PIN
    finally:
        handle.endGroup()
    return user_id, pin


def write_fints_iban(iban: str) -> None:
    """!
    @brief Writes the FinTS IBAN to persistent storage.
    @param iban : bank account IBAN.
    """
    handle = get_settings_handle()
    handle.beginGroup(SECTION_FINTS)
    handle.setValue(KEY_IBAN, iban)
    handle.endGroup()


def read_fints_iban() -> str:
    """!
    @brief Reads the FinTS IBAN from persistent storage.
    @return bank account IBAN.
    """
    handle = get_settings_handle()
    try:
        handle.beginGroup(SECTION_FINTS)
        iban = str(get_registry_value(handle, KEY_IBAN))
    except Exception as e:
        log.debug("FinTS IBAN not found, using default values (%s)", str(e))
        iban = DEFAULT_IBAN
    finally:
        handle.endGroup()
    return iban


def write_fints_tan_mechanism(tan_mechanism: str) -> None:
    """!
    @brief Writes the FinTS TAN mechanism to persistent storage.
    @param tan_mechanism : TAN mechanism.
    """
    handle = get_settings_handle()
    handle.beginGroup(SECTION_FINTS)
    handle.setValue(KEY_TAN_MECHANISM, tan_mechanism)
    handle.endGroup()


def read_fints_tan_mechanism() -> str:
    """!
    @brief Reads the FinTS TAN mechanism from persistent storage.
    @return TAN mechanism.
    """
    handle = get_settings_handle()
    try:
        handle.beginGroup(SECTION_FINTS)
        tan_mechanism = str(get_registry_value(handle, KEY_TAN_MECHANISM))
    except Exception as e:
        log.debug("FinTS TAN mechanism not found, using default values (%s)", str(e))
        tan_mechanism = DEFAULT_TAN_MECHANISM
    finally:
        handle.endGroup()
    return tan_mechanism
