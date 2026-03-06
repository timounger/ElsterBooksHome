"""!
********************************************************************************
@file   tools_downloader.py
@brief  Background worker for downloading ElsterBooksTools from GitHub.
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

DOWNLOAD_TIMEOUT = 5  # timeout for tool download
TOOLS_DOWNLOAD_LINK = "https://github.com/timounger/ElsterBooksTools/releases/download/latest/Tools.zip"


class ToolsDownloader(QThread):
    """!
    @brief Background QThread worker that downloads and extracts ElsterBooksTools from GitHub.
    """
    status_signal = pyqtSignal(str)
    finish_signal = pyqtSignal()

    def __init__(self) -> None:  # pylint: disable=useless-parent-delegation
        super().__init__()

    def download_tools(self) -> None:
        """!
        @brief Download the tools ZIP from GitHub, extract it to the tools folder, and delete the ZIP file afterwards.
        """
        dest_dir = os.path.join(TOOLS_FOLDER, "../")
        zip_file = os.path.join(dest_dir, "Tools.zip")
        if os.path.isdir(TOOLS_FOLDER):
            self.status_signal.emit(f"Ordner '{TOOLS_FOLDER}' existiert bereits.")
        else:
            # download tools
            self.status_signal.emit(f"Lade '{TOOLS_DOWNLOAD_LINK}' herunter...")
            try:
                response = requests.get(TOOLS_DOWNLOAD_LINK, stream=True, timeout=DOWNLOAD_TIMEOUT)
                response.raise_for_status()
                with open(zip_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
            except requests.exceptions.RequestException as e:
                self.status_signal.emit(f"Fehler beim Herunterladen der Datei: {e}")
                return

            # unpack zip (with path traversal protection)
            self.status_signal.emit(f"Entpacke '{zip_file}' nach '{dest_dir}'...")
            try:
                abs_dest = os.path.abspath(dest_dir)
                with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                    for member in zip_ref.namelist():
                        member_path = os.path.abspath(os.path.join(abs_dest, member))
                        if not member_path.startswith(abs_dest + os.sep):
                            self.status_signal.emit(f"ZIP enthält unsicheren Pfad: {member}")
                            return
                    zip_ref.extractall(dest_dir)
            except zipfile.BadZipFile as e:
                self.status_signal.emit(f"Fehler beim Entpacken der ZIP-Datei: {e}")
                return

            # delete zip
            self.status_signal.emit(f"Lösche '{zip_file}'...")
            delete_success = delete_file(zip_file)
            if not delete_success:
                self.status_signal.emit(f"Fehler beim Löschen der ZIP-Datei: {zip_file}")
            self.status_signal.emit("Erfolgreich heruntergeladen")

    def run(self) -> None:
        """!
        @brief Execute the tools download in a separate thread and emit finish_signal when done.
        """
        self.download_tools()
        self.finish_signal.emit()
