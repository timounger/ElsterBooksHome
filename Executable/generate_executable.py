"""!
********************************************************************************
@file   generate_executable.py
@brief  Generate single-file Windows executable using PyInstaller.
        Handles git version generation, version info file creation,
        build warnings and included package validation.
********************************************************************************
"""

# autopep8: off
import sys
import os
import logging
import subprocess
import shutil

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from Executable.generate_git_version import generate_git_version_file  # pylint: disable=wrong-import-position
from Executable.generate_version_file import generate_version_file  # pylint: disable=wrong-import-position
from Executable.check_included_packages import check_included_packages  # pylint: disable=wrong-import-position

from Source.version import __title__, __version__, __description__, __copyright__, BUILD_NUITKA  # pylint: disable=wrong-import-position
from Source.Util.colored_log import init_console_logging  # pylint: disable=wrong-import-position
# from Test.py_preprocessor import CONFIG_DEFINES  # pylint: disable=wrong-import-position
# autopep8: on

log = logging.getLogger("GenerateExecutable")
init_console_logging(logging.INFO)

WORKPATH = "build"
GIT_VERSION_PATH = "../Source/Util"
VERSION_FILE_NAME = "version_info.txt"
if BUILD_NUITKA:
    WARNING_FILE = "Nuitka_warnings.txt"
else:
    WARNING_FILE = "PyInstaller_warnings.txt"
OUTPUT_DIR = "bin"

EXCLUDE_MODULES = [
    "_distutils_hack",
    "cffi",
    "pkg_resources",
    "pyasn1",
    "pyasn1_modules",
    "pycparser",
    "pyparsing",
    "rsa",
    "setuptools",
    "yaml",
    "bs4",
    "charset_normalizer",
    "soupsieve",
    "defusedxml",
    "fontTools",
    "click",
    "markdown_it",
    "mdurl",
    "pygments",
    "rich",
    "mypy",
    "toml",
    "cairo",
    "freetype",
    "rlPyCairo",
    # can not imported by PyInstaller - exclude to avoid warnings
    "serial.tools.list_ports_osx",
    "darkdetect._mac_detect",
]

if BUILD_NUITKA:
    INCLUDE_DATA_DIRS = [
        "../Resources/FinTS/=Resources/FinTS/",
        "../Resources/Fonts/=Resources/Fonts/",
        "../Resources/Git/=Resources/Git/",
        "../Resources/Help/=Resources/Help/",
        "../Resources/Icon/=Resources/Icon/",
        "../Resources/InvoiceImage/=Resources/InvoiceImage/",
        "../Resources/schemata/=Resources/schemata/",
    ]

    INCLUDE_DATA_FILES = [
        "../LICENSE.md=LICENSE.md",
        "../Resources/splash.gif=Resources/splash.gif",
        "../Resources/app.ico=Resources/app.ico",
    ]
else:
    add_data = [
        "..\\LICENSE.md;.\\",
        "..\\Resources\\splash.gif;Resources\\",
        "..\\Resources\\app.ico;Resources\\",
        "..\\Resources\\FinTS\\;Resources\\FinTS\\",
        "..\\Resources\\Fonts\\;Resources\\Fonts\\",
        "..\\Resources\\Git\\;Resources\\Git\\",
        "..\\Resources\\Help\\;Resources\\Help\\",
        "..\\Resources\\Icon\\;Resources\\Icon\\",
        "..\\Resources\\InvoiceImage\\;Resources\\InvoiceImage\\",
        "..\\Resources\\schemata\\;Resources\\schemata\\",
        f"{sys.prefix}\\Lib\\site-packages\\drafthorse\\schema\\;drafthorse\\schema\\"  # add drafthorse resource file
    ]

if BUILD_NUITKA:
    def get_flag_list(flag_name: str, values: list[str]) -> list[str]:
        """!
        @brief Build repeated Nuitka CLI argument pairs.
        @param flag_name : Nuitka argument name (e.g. "include-package", "include-data-dir")
        @param values : values to pair with the argument name
        @return flat list of alternating argument flags and values
        """
        flag_list = []
        for value in values:
            flag_list.append(f"--{flag_name}={value}")
        return flag_list


    def find_drafthorse_schema_dir() -> str | None:
        """!
        @brief Find drafthorse schema directory in site-packages.
        @return path to drafthorse/schema directory or None
        """
        site_packages = os.path.join(sys.prefix, "Lib", "site-packages")
        schema_dir = os.path.join(site_packages, "drafthorse", "schema")
        if os.path.isdir(schema_dir):
            return schema_dir
        return None

else:
    TOLERATED_WARNINGS = [
        "No backend available",  # possible on CI
    ]

    """
    for _config_name, (config_status, _exclude_file, exclude_packages) in CONFIG_DEFINES.items():
        if not config_status and exclude_packages:
            EXCLUDE_MODULES.extend(exclude_packages)
    """

    HIDDEN_IMPORT = [
        "tzdata",
        "openpyxl",
        "reportlab",
    ]


    def get_type_list(type_name: str, type_values: list[str]) -> list[str]:
        """!
        @brief Build repeated PyInstaller CLI argument pairs (e.g. --exclude-module foo --exclude-module bar).
        @param type_name : PyInstaller argument name (e.g. "exclude-module", "add-data")
        @param type_values : values to pair with the argument name
        @return flat list of alternating argument flags and values
        """
        type_list = []
        for type_value in type_values:
            type_list.extend([f"--{type_name}", type_value])
        return type_list


if __name__ == "__main__":
    result_report = []
    source_file = "../Source/app.py"

    if BUILD_NUITKA:
        command = [r"..\.venv\Scripts\python", "-m", "nuitka"]
        command.append("--standalone")
        command.append("--onefile")  # Disabled for debugging
        command.append("--remove-output")
        command.append("--assume-yes-for-downloads")
        # https://github.com/Nuitka/Nuitka/blob/develop/Standard-Plugins-Documentation.rst
        command.append("--enable-plugin=pyqt6")

        # Windows specific
        command.append("--windows-console-mode=disable")  # disable or attach
        command.append(f"--windows-icon-from-ico=..\\Resources\\app.ico")
        command.append(f"--windows-file-version={__version__}")
        command.append(f"--windows-product-version={__version__}")
        command.append(f"--windows-company-name={__copyright__.replace('©', '(c)')}")
        command.append(f"--windows-product-name={__title__}")
        command.append(f"--windows-file-description={__title__} - {__description__}")

        # Output
        command.append(f"--output-dir={OUTPUT_DIR}")
        command.append(f"--output-filename={__title__}.exe")

        # Include data
        command.extend(get_flag_list("include-data-dir", INCLUDE_DATA_DIRS))
        command.extend(get_flag_list("include-data-files", INCLUDE_DATA_FILES))

        # Drafthorse schema files
        drafthorse_schema = find_drafthorse_schema_dir()
        if drafthorse_schema:
            command.append(f"--include-data-dir={drafthorse_schema}=drafthorse/schema/")

        # Excluded modules
        command.extend(get_flag_list("nofollow-import-to", EXCLUDE_MODULES))

        # Source file
        command.append(source_file)

        generate_git_version_file(GIT_VERSION_PATH)

        log.info("Running Nuitka build command...")
        log.info(" ".join(command))

        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.abspath("..")
        result = subprocess.run(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, check=False, env=env)
        if result.returncode != 0:
            result_report.append("Build executable failed!")
            if result.stderr:
                result_report.append(result.stderr)
            if result.stdout:
                result_report.append(result.stdout)
        else:
            # Check for warnings in output
            output = (result.stderr or "") + (result.stdout or "")
            warnings = [line for line in output.split("\n") if "WARNING" in line]
            if warnings:
                log.warning("Build warnings:\n%s", "\n".join(warnings))

        if result.stderr:
            log.info(result.stderr)
        if result.stdout:
            log.info(result.stdout)
    else:
        command = [r"..\.venv\Scripts\python", "-m", "PyInstaller", "--clean"]
        command.extend(["--paths", "..\\"])
        command.extend(get_type_list("add-data", add_data))
        command.extend(["--icon", "..\\Resources\\app.ico"])
        command.extend(["--version-file", f"{WORKPATH}\\{VERSION_FILE_NAME}"])
        command.extend(get_type_list("hidden-import", HIDDEN_IMPORT))
        command.extend(get_type_list("exclude-module", EXCLUDE_MODULES))
        command.extend(["--name", __title__])
        command.extend(["--onefile", "--noconsole", "--noupx"])
        command.extend(["--distpath", OUTPUT_DIR])
        command.extend(["--workpath", WORKPATH])
        command.extend([source_file])

        generate_git_version_file(GIT_VERSION_PATH)
        generate_version_file(VERSION_FILE_NAME, WORKPATH)

        result = subprocess.run(command, stderr=subprocess.PIPE, text=True, check=False)
        if result.returncode != 0:
            result_report.append("Build executable failed!")
            result_report.append(result.stderr)
        else:
            possible_build_warnings = [line for line in result.stderr.split("\n") if "WARNING" in line]
            build_warnings = [w for w in possible_build_warnings if not any(t in w for t in TOLERATED_WARNINGS)]
            if build_warnings:
                result_report.extend(build_warnings)
            else:
                not_allowed_packages = check_included_packages()
                if not_allowed_packages:
                    result_report.extend(not_allowed_packages)
        log.info(result.stderr)

    with open(WARNING_FILE, mode="w", encoding="utf-8") as file:
        report = "\n".join(result_report)
        if report:
            log.warning(report)
        file.write(report)
    if result_report:
        log.error("FAILED build of executable")
        ret_value = 1
    else:
        if not BUILD_NUITKA:
            spec_file = f"{__title__}.spec"
            if os.path.exists(spec_file):
                os.remove(spec_file)
            if os.path.exists(WORKPATH):
                shutil.rmtree(WORKPATH)
        log.info("SUCCESS build of executable")
        ret_value = 0
    sys.exit(ret_value)
