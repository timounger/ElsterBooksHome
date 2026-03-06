"""!
********************************************************************************
@file   help_dialog.py
@brief  Create help dialog.
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
    @brief Create a modal help dialog displaying the application documentation as HTML.
    @param ui : main window instance used as parent and for theme styling.
    @return Configured help dialog instance.
    """
    dialog_help = QDialog(ui)
    dialog_help.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
    dialog_help.setWindowFlag(Qt.WindowType.WindowMinMaxButtonsHint, True)
    ui_help = Ui_HelpDialog()
    ui_help.setupUi(dialog_help)
    help_text_source_link = {}
    help_text_source_link[ui_help.helpTextGeneral] = "general.md"
    help_text_source_link[ui_help.helpTextInvoice] = "invoice.md"
    help_text_source_link[ui_help.helpTextBooking] = "booking.md"
    help_text_source_link[ui_help.helpTextExport] = "export.md"
    help_text_source_link[ui_help.helpTextSettings] = "settings.md"
    ui_help.tabWidget_helpMenu.setCurrentIndex(0)
    for q_text_browser, source_file in help_text_source_link.items():
        with open(os.path.join(HELP_PATH, source_file), mode="r", encoding="utf-8") as f:
            text = f.read()
            q_text_browser.setHtml(markdown.markdown(text))
    return dialog_help
