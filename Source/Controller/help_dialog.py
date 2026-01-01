"""!
********************************************************************************
@file   help_dialog.py
@brief  Create help dialog
********************************************************************************
"""

import os
import logging
from typing import TYPE_CHECKING
import markdown

from PyQt6.QtWidgets import QDialog
from PyQt6.QtCore import Qt

from Source.version import __title__
from Source.Util.app_data import HELP_PATH
from Source.Views.dialogs.dialog_help_ui import Ui_HelpDialog
if TYPE_CHECKING:
    from Source.Controller.main_window import MainWindow

log = logging.getLogger(__title__)


def create_help_dialog(ui: "MainWindow") -> QDialog:
    """!
    @brief Create help dialog.
    @param ui : main window to create dialog with same style
    @return help dialog
    """
    dialog_help = QDialog(ui)
    dialog_help.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
    dialog_help.setWindowFlag(Qt.WindowType.WindowMinMaxButtonsHint, True)
    ui_help = Ui_HelpDialog()
    ui_help.setupUi(dialog_help)
    d_help_text_source_link = {}
    d_help_text_source_link[ui_help.helpTextGeneral] = "general.md"
    d_help_text_source_link[ui_help.helpTextInvoice] = "invoice.md"
    d_help_text_source_link[ui_help.helpTextBooking] = "booking.md"
    d_help_text_source_link[ui_help.helpTextExport] = "export.md"
    d_help_text_source_link[ui_help.helpTextSettings] = "settings.md"
    ui_help.tabWidget_helpMenu.setCurrentIndex(0)
    for q_text_browser, s_source_file in d_help_text_source_link.items():
        with open(os.path.join(HELP_PATH + s_source_file), mode="r", encoding="utf-8") as f:
            text = f.read()
            q_text_browser.setHtml(markdown.markdown(text))
    return dialog_help
