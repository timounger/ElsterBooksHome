"""!
********************************************************************************
@file   create_doxygen.py
@brief  Create doxygen documentation for project.
********************************************************************************
"""

# autopep8: off
import sys
import os
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from Source.version import APP_NAME, __version__, APP_DESCRIPTION, __author__, REPO_URL  # pylint: disable=wrong-import-position
from Source.Util.app_data import ICON_APP_FAVICON_PATH, ICON_APP_PATH  # pylint: disable=wrong-import-position
from Source.Util.colored_log import init_console_logging  # pylint: disable=wrong-import-position
from Documentation.DoxygenCreator.doxygen_creator import DoxygenCreator, get_cmd_args, MAIN_FOLDER, PYTHON_PATTERN  # pylint: disable=wrong-import-position
# autopep8: on

init_console_logging(logging.INFO)

if __name__ == "__main__":
    args = get_cmd_args()
    doxygen_creator = DoxygenCreator(REPO_URL)
    doxygen_creator.set_configuration("PROJECT_NAME", APP_NAME)
    doxygen_creator.set_configuration("PROJECT_NUMBER", __version__)
    doxygen_creator.set_configuration("PROJECT_BRIEF", APP_DESCRIPTION)
    doxygen_creator.set_configuration("PROJECT_LOGO", f"{MAIN_FOLDER}{ICON_APP_PATH}")
    doxygen_creator.set_configuration("PROJECT_ICON", f"{MAIN_FOLDER}{ICON_APP_FAVICON_PATH}")
    doxygen_creator.set_configuration("DOCSET_PUBLISHER_NAME", __author__)
    doxygen_creator.set_configuration("INPUT", MAIN_FOLDER)
    file_patterns = [PYTHON_PATTERN, "*.md"]
    exclude_patterns = [".venv", "Documentation", "Executable", "Tools", "Export", "docs", "tools", "Views", "CLAUDE.md"]
    doxygen_creator.set_configuration("EXCLUDE_PATTERNS", exclude_patterns)
    doxygen_creator.set_configuration("FILE_PATTERNS", file_patterns)

    sys.exit(doxygen_creator.run_doxygen(open_doxygen_output=args.open))
