"""!
********************************************************************************
@file   tools_downloader.py
@brief  Download tools
********************************************************************************
"""

import os
import logging
import zipfile
import requests

from PyQt6.QtCore import QThread, pyqtSignal

from Source.version import __title__
from Source.Util.app_data import TOOLS_FOLDER
from Source.Model.data_handler import delete_file

log = logging.getLogger(__title__)

I_TIMEOUT = 5  # timeout for tool download
TOOLS_DOWNLOAD_LINK = "https://github.com/timounger/ElsterBooksTools/releases/download/latest/Tools.zip"


class ToolsDownloader(QThread):
    """!
    @brief Tools downloader
    """
    status_signal = pyqtSignal(str)
    finish_signal = pyqtSignal()

    def __init__(self) -> None:  # pylint: disable=useless-parent-delegation
        super().__init__()

    def download_tools(self) -> None:
        """!
        @brief Download tools
        """
        url = TOOLS_DOWNLOAD_LINK
        dest_dir = os.path.join(TOOLS_FOLDER, "../")
        zip_file = os.path.join(dest_dir, "Tools.zip")
        tools_dir = TOOLS_FOLDER
        if os.path.isdir(tools_dir):
            self.status_signal.emit(f"Ordner '{tools_dir}' existiert bereits.")
        else:
            # download tools
            self.status_signal.emit(f"Lade '{url}' herunter...")
            try:
                response = requests.get(url, stream=True, timeout=I_TIMEOUT)
                response.raise_for_status()
                with open(zip_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
            except requests.exceptions.RequestException as e:
                self.status_signal.emit(f"Fehler beim Herunterladen der Datei: {e}")
                return

            # unpack zip
            self.status_signal.emit(f"Entpacke '{zip_file}' nach '{dest_dir}'...")
            try:
                with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                    zip_ref.extractall(dest_dir)
            except zipfile.BadZipFile as e:
                self.status_signal.emit(f"Fehler beim Entpacken der ZIP-Datei: {e}")
                return

            # delete zip
            self.status_signal.emit(f"Lösche '{zip_file}'...")
            delete_success = delete_file(zip_file)
            if not delete_success:
                self.status_signal.emit(f"Fehler beim Löschen der ZIP-Datei: {e}")
            self.status_signal.emit("Erfolgreich heruntergeladen")

    def run(self) -> None:
        """!
        @brief Run tools download
        """
        self.download_tools()
        self.finish_signal.emit()
