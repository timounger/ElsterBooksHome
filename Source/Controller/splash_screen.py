"""!
********************************************************************************
@file   splash_screen.py
@brief  Create splash screen
********************************************************************************
"""

import logging

from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QDialog
from PyQt6.QtCore import Qt

from Source.version import __title__, __version__
from Source.version import BUILD_NAME
from Source.Util.app_data import IMG_SPLASH
from Source.Views.dialogs.dialog_splash_ui import Ui_SplashScreen

F_MIN_SPLASH_SCREEN_TIME = 2.0  # minimum splash screen time in "s"

log = logging.getLogger(__title__)


def create_splash_screen() -> QDialog:
    """!
    @brief Create splash screen
    @return splash screen dialog
    """
    splash = QDialog()
    splash.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
    splash.setWindowFlag(Qt.WindowType.WindowMinMaxButtonsHint, False)
    splash.setWindowFlag(Qt.WindowType.FramelessWindowHint)
    ui_splash = Ui_SplashScreen()
    ui_splash.setupUi(splash)
    ui_splash.lbl_icon_placeholder.setPixmap(QPixmap(IMG_SPLASH))
    ui_splash.lbl_productName.setText(__title__)
    ui_splash.lbl_version.setText(f"v{__version__}")

    # set color black anyway to be visible on Windows 11
    ui_splash.lbl_productName.setStyleSheet("color: black;")
    ui_splash.lbl_version.setStyleSheet("color: black;")

    ui_splash.lbl_prerelease.setStyleSheet("color: red;")
    ui_splash.lbl_prerelease.show()
    if BUILD_NAME:
        ui_splash.lbl_build_name.setText(f'only for "{BUILD_NAME}"')
        ui_splash.lbl_build_name.setStyleSheet("color: yellow;")
        ui_splash.lbl_build_name.show()
    else:
        ui_splash.lbl_build_name.hide()
    return splash
