"""!
********************************************************************************
@file   model.py
@brief  Application data storage model.
********************************************************************************
"""

import os
import logging
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QFileDialog

from Source.version import __title__
from Source.Util.app_log import LogConfig
from Source.Util.app_data import read_last_dir, write_last_dir, write_output_path_settings, read_output_path_settings, \
    DEFAULT_LAST_PATH, REL_PATH, read_ai_type

from Source.Model.monitor import MonitorScale
from Source.Model.plz import load_plz_mapping
from Source.Worker.ollama_ai import OllamaAI
from Source.Worker.open_ai import OpenAI
from Source.Worker.gemini_ai import GeminiAI
from Source.Worker.mistral_ai import MistralAI
if TYPE_CHECKING:
    from Source.Controller.main_window import MainWindow

log = logging.getLogger(__title__)

WRITE_TEST_FILE_NAME = "_write_test.txt"


def check_write_access(path: str) -> bool:
    """!
    @brief Check write access of path. Requires an absolute path.
    @param path : path to check.
    @return True if path is writable, False otherwise.
    """
    test_file = os.path.join(path, WRITE_TEST_FILE_NAME)
    try:  # test write access
        with open(test_file, mode="w", encoding="utf-8") as file:
            file.write("Write Access Test")
        has_access = True
    except OSError:
        has_access = False
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)
    return has_access


class Model:
    """!
    @brief Application data model.
    @param ui : main window object.
    @param log_config : log configuration of the application.
    """

    def __init__(self, ui: "MainWindow", log_config: LogConfig) -> None:
        self.ui = ui
        self.log_config = log_config
        self.output_path = read_output_path_settings()
        self.last_path = read_last_dir()
        self.monitor = MonitorScale(ui)
        self.plz_map = load_plz_mapping()
        self.ollama_ai = OllamaAI()
        self.open_ai = OpenAI()
        self.gemini_ai = GeminiAI()
        self.mistral_ai = MistralAI()
        self.ai_type = read_ai_type()
        self.data_path = REL_PATH
        self.git_add = True

    def update_output_path(self, output_path: str) -> None:
        """!
        @brief Set the data output directory, prompting with a file dialog if no path is given. TODO Diese Funktion verwenden.
        @param output_path : new output path to set.
        """
        if output_path is None:
            path = QFileDialog.getExistingDirectory(parent=self.ui,
                                                    caption="Wähle ein Daten Verzeichnis",
                                                    directory=self.get_last_path())
        else:
            path = output_path

        if path is not None:
            if os.path.exists(path):
                has_access = check_write_access(path)
                if has_access:
                    write_output_path_settings(path)
                    self.output_path = path
                else:
                    self.ui.set_status(f"Kein Schreibzugriff auf das Ausgangsverzeichnis: {path}", True)
            else:
                self.ui.set_status(f"Ausgangsverzeichnis existiert nicht: {path}", True)

    def get_last_path(self) -> str:
        """!
        @brief Get last path to open dialog. Set and return default if path not exists.
        @return Last used directory path.
        """
        if not os.path.exists(self.last_path):
            self.last_path = DEFAULT_LAST_PATH
        return self.last_path

    def set_last_path(self, path: str) -> None:
        """!
        @brief Set last path and save in persistent storage.
        @param path : path to set as last path.
        """
        self.last_path = path
        write_last_dir(path)
