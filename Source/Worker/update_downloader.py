"""!
********************************************************************************
@file   update_downloader.py
@brief  Download update
********************************************************************************
"""

import logging
import requests

from PyQt6.QtCore import QThread, pyqtSignal

from Source.version import __title__, __owner__, __repo__
from Source.Util.app_data import open_subprocess
from Source.Model.data_handler import delete_file

log = logging.getLogger(__title__)

I_TIMEOUT = 5  # timeout for tool download
BASIS_VERSION_FILE = f"{__title__}.exe"
NEW_VERSION_FILE = f"_temp_new_{__title__}.exe"
OLD_VERSION_FILE = f"_temp_old_{__title__}.exe"
UPDATER_SCRIPT = "_temp_updater.bat"


def delete_temp_update_files() -> None:
    """!
    @brief Delete temporary update files
    """
    delete_file(NEW_VERSION_FILE)
    delete_file(OLD_VERSION_FILE)
    delete_file(UPDATER_SCRIPT)


def generate_and_start_updater_script() -> None:
    """!
    @brief Generate and start updater script
    """
    batch_commands = [
        'timeout /t 1',
        f'rename "{BASIS_VERSION_FILE}" "{OLD_VERSION_FILE}"',
        f'rename "{NEW_VERSION_FILE}" "{BASIS_VERSION_FILE}"'
    ]

    with open(UPDATER_SCRIPT, mode="w", encoding="utf-8") as file:
        file.write("\n".join(batch_commands))

    open_subprocess([UPDATER_SCRIPT])


class UpdateDownloader(QThread):
    """!
    @brief Update downloader
    """
    status_signal = pyqtSignal(str)
    finish_signal = pyqtSignal(bool)

    def __init__(self) -> None:  # pylint: disable=useless-parent-delegation
        super().__init__()
        self.latest_version = None

    def download_update(self) -> bool:
        """!
        @brief Download the latest update, save it locally, and optionally emit progress signals
        @return success_status : download success status
        """
        success_status = False
        url = f"https://github.com/{__owner__}/{__repo__}/releases/download/v{self.latest_version}/{__title__}.exe"
        # download update
        try:
            response = requests.get(url, stream=True, timeout=I_TIMEOUT)
            response.raise_for_status()

            # Gesamtlänge aus dem Header (falls vorhanden)
            total_length = response.headers.get('content-length')
            if total_length is not None:
                total_length = int(total_length)
            else:
                total_length = 0  # unbekannt

            downloaded = 0
            last_status_text = ""
            with open(NEW_VERSION_FILE, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_length > 0:
                        percent = downloaded / total_length * 100
                        mb_done = downloaded / (1024 * 1024)
                        mb_total = total_length / (1024 * 1024)
                        status_text = f"{mb_done:.1f} von {mb_total:.1f} MB ({percent:.1f}%)"
                    else:
                        mb_done = downloaded / (1024 * 1024)
                        status_text = f"{mb_done:.1f}  MB heruntergeladen"
                    if status_text != last_status_text:
                        self.status_signal.emit(status_text)
                        last_status_text = status_text
        except requests.exceptions.RequestException:
            self.status_signal.emit("Update fehlgeschlagen")
        else:
            success_status = True
        return success_status

    def run(self) -> None:
        """!
        @brief Execute the update download in a separate thread and emit finish signal when done
        """
        success_status = self.download_update()
        self.finish_signal.emit(success_status)
