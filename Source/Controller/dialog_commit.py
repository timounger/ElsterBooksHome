"""!
********************************************************************************
@file   dialog_commit.py
@brief  Dialog for creating a Git commit
********************************************************************************
"""

import os
import logging
from typing import TYPE_CHECKING, Any

from PyQt6.QtWidgets import QDialog
from PyQt6.QtCore import Qt

from Source.version import __title__
from Source.Util.app_data import thread_dialog
from Source.Model.data_handler import tortoise_git_check_for_mod, TORTOISE_GIT_EXE
from Source.Views.dialogs.dialog_commit_ui import Ui_CommitDialog
if TYPE_CHECKING:
    from Source.Controller.main_window import MainWindow

log = logging.getLogger(__title__)


class CommitDialog(QDialog, Ui_CommitDialog):
    """!
    @brief Dialog for reviewing changes and creating a Git commit.
    @param ui : main window
    @param changes : Git change summary text
    """

    def __init__(self, ui: "MainWindow", changes: str, *args: Any, **kwargs: Any) -> None:  # pylint: disable=keyword-arg-before-vararg
        super().__init__(parent=ui, *args, **kwargs)  # type: ignore
        self.setupUi(self)
        self.setWindowFlags(Qt.WindowType.Window)  # set all window buttons (e.g max window size)
        self.ui = ui
        self.changes = changes
        self.b_commit = False
        self.commit_message = ""
        thread_dialog(self)

    def show_dialog(self) -> None:
        """!
        @brief Initialize and display the commit dialog modally.
        """
        log.debug("Starting Commit dialog")

        self.ui.model.c_monitor.set_dialog_style(self)
        self.setWindowTitle("GIT Commit")

        self.pte_changes.setPlainText(self.changes)
        self.pte_changes.setReadOnly(True)
        self.pte_commit_text.setPlainText("Auto Commit")

        self.btn_yes.setStyleSheet("background-color: green; color: white;")
        self.btn_no.setStyleSheet("background-color: red; color: white;")
        self.btn_yes.clicked.connect(self.yes_clicked)
        self.btn_no.clicked.connect(self.close)
        if os.path.exists(TORTOISE_GIT_EXE):
            self.btn_diff.clicked.connect(self.diff_clicked)
        else:
            self.btn_diff.hide()

        self.show()
        self.exec()

    def yes_clicked(self) -> None:
        """!
        @brief Yes (commit) button clicked.
        """
        commit_message = self.pte_commit_text.toPlainText()
        if commit_message.strip():
            self.commit_message = commit_message
            self.b_commit = True
            self.close()
        else:
            self.pte_commit_text.setStyleSheet("border: 2px solid red;")
            self.ui.set_status("Keine Commit Message vorhanden.", b_highlight=True)

    def diff_clicked(self) -> None:
        """!
        @brief Diff button clicked.
        """
        tortoise_git_check_for_mod()
