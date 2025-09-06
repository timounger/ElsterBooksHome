"""!
********************************************************************************
@file   model.py
@brief  Application data storage model
********************************************************************************
"""

import os
import logging
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QFileDialog

from Source.version import __title__
from Source.Util.app_log import LogConfig
from Source.Util.app_data import read_last_dir, write_last_dir, write_output_path_settings, read_output_path_settings, \
    S_DEFAULT_LAST_PATH, REL_PATH, read_ai_type

from Source.Model.monitor import MonitorScale
from Source.Model.plz import get_plz_data
if TYPE_CHECKING:
    from Source.Controller.main_window import MainWindow
from Source.Worker.ollama_ai import OllamaAI
from Source.Worker.open_ai import OpenAI

log = logging.getLogger(__title__)

S_WRITE_TEST_FILE_NAME = "_write_test.txt"


def check_write_access(path: str) -> bool:
    """!
    @brief Check write access of path
    @param path : path to check
    @return write access status
    """
    try:  # test write access
        s_test_file = path + "/" + S_WRITE_TEST_FILE_NAME
        with open(s_test_file, mode="w", encoding="utf-8") as file:
            file.write("Write Access Test")
        os.remove(s_test_file)
    except BaseException:
        b_access = False
    else:
        b_access = True
    return b_access


class Model:
    """!
    @brief Holds the data of the application
    @param ui : main window object
    @param log_config : log configuration of the application
    """

    def __init__(self, ui: "MainWindow", log_config: LogConfig) -> None:
        self.ui = ui
        self.log_config = log_config
        self.s_output_path = read_output_path_settings()
        self.s_last_path = read_last_dir()
        self.c_monitor = MonitorScale(ui)
        self.d_plz_data = get_plz_data()
        self.c_ollama_ai = OllamaAI()
        self.c_open_ai = OpenAI()
        self.ai_type = read_ai_type()
        self.data_path = REL_PATH
        self.git_add = True

    def update_output_path(self, s_output_path: str) -> None:
        """!
        @brief Update output path TODO verwenden
        @param s_output_path : new output path to set
        """
        if s_output_path is None:
            s_path = QFileDialog.getExistingDirectory(parent=self.ui,
                                                      caption="Wähle ein Daten Verzeichnis",
                                                      directory=self.get_last_path())
        else:
            s_path = s_output_path

        if s_path is not None:
            if os.path.exists(s_path):
                b_access = check_write_access(s_path)
                if b_access:
                    write_output_path_settings(s_path)
                    self.s_output_path = s_path
                else:
                    self.ui.set_status(f"Kein Schreibzugriff auf das Ausgangsverzeichnis: {s_path}", True)
            else:
                self.ui.set_status(f"Ausgangsverzeichnis existiert nicht: {s_path}", True)

    def get_last_path(self) -> str:
        """!
        @brief Get last path to open dialog. Set and return default if path not exists.
        @return last path
        """
        if not os.path.exists(self.s_last_path):
            self.s_last_path = S_DEFAULT_LAST_PATH
        return self.s_last_path

    def set_last_path(self, path: str) -> None:
        """!
        @brief Set last path and save in persistent storage
        @param path : path to set as last path
        """
        self.s_last_path = path
        write_last_dir(path)
