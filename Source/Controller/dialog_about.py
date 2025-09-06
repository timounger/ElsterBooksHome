"""!
********************************************************************************
@file   dialog_about.py
@brief  Create about dialog
********************************************************************************
"""

import logging
from typing import TYPE_CHECKING

from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QDialog
from PyQt6.QtCore import Qt

from Source.version import __title__, __description__, __version__, __home__, __copyright__, __license__, GIT_SHORT_SHA, BUILD_NAME
from Source.Util.app_data import ICON_APP
from Source.Views.dialogs.dialog_about_ui import Ui_AboutDialog
if TYPE_CHECKING:
    from Source.Controller.main_window import MainWindow

log = logging.getLogger(__title__)


def show_about_dialog(ui: "MainWindow") -> None:
    """!
    @brief Show about dialog.
    @param ui : main window
    """
    log.debug("Starting About dialog")
    dialog_about = QDialog(ui)
    dialog_about.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
    dialog_about.setWindowFlag(Qt.WindowType.WindowMinMaxButtonsHint, False)

    ui_about = Ui_AboutDialog()
    ui_about.setupUi(dialog_about)

    ui.model.c_monitor.set_dialog_style(dialog_about)
    ui_about.lbl_productName.setText(__title__)
    ui_about.lbl_productDescription.setText(__description__)

    # Version info text
    version_info = f"Version: {__version__}"
    version_info += "  Prerelease Build"
    ui_about.lbl_version.setStyleSheet("color: red;")
    license_text = ""
    home_link = ""
    if GIT_SHORT_SHA is not None:
        version_info += f"\nGit SHA: {GIT_SHORT_SHA}"
    if BUILD_NAME:
        version_info += f'\nonly for "{BUILD_NAME}"'
    ui_about.lbl_version.setText(version_info)
    ui_about.lbl_copyright.setText(__copyright__)
    ui_about.lbl_license.setText(license_text)
    ui_about.lbl_home.setText(home_link)
    ui_about.imagePlaceholder.setPixmap(QPixmap(ICON_APP))
    dialog_about.setWindowTitle(f"Über {__title__}")
    dialog_about.setWindowIcon(QIcon(ICON_APP))
    dialog_about.show()
    dialog_about.exec()
