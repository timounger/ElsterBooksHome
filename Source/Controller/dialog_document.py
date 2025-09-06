"""!
********************************************************************************
@file   dialog_document.py
@brief  Document dialog
********************************************************************************
"""

import logging
from typing import Optional, Any, TYPE_CHECKING
import copy

from PyQt6.QtWidgets import QDialog
from PyQt6.QtCore import QDate

from Source.version import __title__
from Source.Util.app_data import thread_dialog
from Source.Views.dialogs.dialog_document_ui import Ui_DialogDocument
from Source.Model.document import remove_document, add_document, EDocumentFields, D_DOCUMENT_TEMPLATE
from Source.Model.data_handler import DATE_FORMAT, get_file_name_content
if TYPE_CHECKING:
    from Source.Controller.main_window import MainWindow

log = logging.getLogger(__title__)


class DocumentDialog(QDialog, Ui_DialogDocument):
    """!
    @brief Document dialog.
    @param ui : main window
    @param data : document data
    @param uid : UID of contact
    @param file_path : document file
    """

    def __init__(self, ui: "MainWindow", data: Optional[dict[EDocumentFields, Any]] = None, uid: Optional[str] = None,  # pylint: disable=keyword-arg-before-vararg
                 file_path: Optional[str] = None, *args: Any, **kwargs: Any) -> None:
        super().__init__(parent=ui, *args, **kwargs)  # type: ignore
        self.setupUi(self)
        self.ui = ui
        self.data = data
        self.uid = uid
        self.file_path = file_path
        self.document_data = None
        thread_dialog(self)

    def show_dialog(self) -> None:
        """!
        @brief Show dialog
        """
        log.debug("Starting Document dialog")

        self.ui.model.c_monitor.set_dialog_style(self)
        current_date = QDate.currentDate()

        if self.data is not None:
            # document data
            date = QDate.fromString(self.data[EDocumentFields.DOCUMENT_DATE], DATE_FORMAT)
            self.de_document_date.setDate(date)
            # description
            self.pte_description.setPlainText(self.data[EDocumentFields.DESCRIPTION])
        else:
            self.btn_delete.hide()
            # set actual date date
            actual_date = current_date
            self.de_document_date.setDate(actual_date)
            file_date, file_content = get_file_name_content(self.file_path)
            if file_date is not None:
                invoice_date = QDate.fromString(file_date, DATE_FORMAT)
                self.de_document_date.setDate(invoice_date)
            if file_content is not None:
                self.pte_description.setPlainText(file_content)
        self.setWindowTitle("Dokument")
        self.btn_save.clicked.connect(self.save_clicked)
        self.btn_delete.clicked.connect(self.delete_clicked)
        self.btn_cancel.clicked.connect(self.close)
        self.show()
        self.exec()

    def delete_clicked(self) -> None:
        """!
        @brief Delete button clicked.
        """
        if self.uid is not None:
            remove_document(self.ui.model.data_path, self.uid)
            self.ui.set_status("Dokument gelöscht")
            self.close()
        else:
            log.warning("Delete file clicked without UID")

    def save_clicked(self) -> None:
        """!
        @brief Save button clicked.
        """
        valid = self.set_data()
        if valid:
            if self.data is not None:
                add_document(self.ui.model.data_path, self.ui.model.git_add, self.data, self.uid, self.file_path)
                if self.uid is None:
                    self.ui.set_status("Dokument hinzugefügt")
                else:
                    self.ui.set_status("Dokument gespeichert")
                self.close()
            else:
                log.warning("Save file clicked without data")

    def set_data(self) -> bool:
        """!
        @brief Set document data.
        @return status if contact data are valid to save
        """
        description = self.pte_description.toPlainText()
        attachment = self.data.get(EDocumentFields.ATTACHMENT) if (self.data is not None) else None
        if description:
            self.data = copy.deepcopy(D_DOCUMENT_TEMPLATE)
            self.data[EDocumentFields.DESCRIPTION] = description
            self.data[EDocumentFields.DOCUMENT_DATE] = self.de_document_date.date().toString(DATE_FORMAT)
            self.data[EDocumentFields.ATTACHMENT] = attachment
            valid = True
        else:
            self.pte_description.setStyleSheet("border: 2px solid red;")
            self.ui.set_status("Keine Beschreibung vorhanden.", b_highlight=True)
            valid = False
        return valid
