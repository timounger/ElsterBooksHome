"""!
********************************************************************************
@file   tab_document.py
@brief  Tab for managing and viewing documents.
********************************************************************************
"""

import os
import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFileDialog

from Source.version import __title__
from Source.Util.app_data import KEY_DOCUMENT_COLUMN
from Source.Controller.table_filter import TableFilter, CellData, ATTACH
from Source.Controller.dialog_document import DocumentDialog
from Source.Model.document import read_document, DOCUMENT_FILE_PATH, EDocumentFields, add_document, remove_document, clean_documents
from Source.Model.data_handler import PDF_FILE_TYPES, find_file, INVOICE_FILE_EXTENSIONS
if TYPE_CHECKING:
    from Source.Controller.main_window import MainWindow

log = logging.getLogger(__title__)

ROW_DESCRIPTION = ["Datum", ATTACH, "Beschreibung", "ID"]
ATTACH_IDX = ROW_DESCRIPTION.index(ATTACH)


class TabDocument:
    """!
    @brief Controller for the Documents tab.
    @param ui : main window
    @param tab_idx : Index of this tab in the tab widget
    """

    def __init__(self, ui: "MainWindow", tab_idx: int) -> None:
        self.ui = ui
        title = "Dokumente"
        ui.tabWidget.setTabText(tab_idx, title)
        self.ui_document = TableFilter(ui, ui.tabWidget, tab_idx, title, title_folder_link=DOCUMENT_FILE_PATH,
                                       btn_1_name="Dokument erfassen", btn_1_cb=self.new_document,
                                       table_double_click_fnc=self.on_item_double_clicked, table_header=ROW_DESCRIPTION,
                                       sort_idx=0, inverse_sort=False, row_fill_idx=len(ROW_DESCRIPTION) - 2,
                                       delete_fnc=remove_document, update_table_func=self.set_table_data,
                                       drag_fnc=self.new_document,
                                       column_setting_key=KEY_DOCUMENT_COLUMN)
        self.documents: list[dict[EDocumentFields, str]] = []

    def set_table_data(self, update: bool = False, rename: bool = False, update_dashboard: bool = True) -> None:
        """!
        @brief Reads document data and updates the table.
        @param update : update status of JSON file
        @param rename : rename status of file name
        @param update_dashboard : update dashboard
        """
        self.documents = read_document(self.ui.model.data_path)
        rows = []
        for document in self.documents:
            if update:
                add_document(self.ui.model.data_path, self.ui.model.git_add, document, document[EDocumentFields.ID], rename=rename)
            row = [
                CellData(text=document[EDocumentFields.DOCUMENT_DATE], right_align=True, is_date=True),
                CellData(icon=self.ui_document.get_attach_icon(document[EDocumentFields.ATTACHMENT])),
                CellData(text=document[EDocumentFields.DESCRIPTION]),
                CellData(text=document[EDocumentFields.ID]),
            ]
            rows.append(row)
        self.ui_document.update_table(rows)
        self.ui_document.table.setColumnHidden(len(ROW_DESCRIPTION) - 1, True)
        if update_dashboard:
            self.ui.tab_dashboard.update_dashboard_data()

    def clean_data(self) -> None:
        """!
        @brief Removes invalid or orphaned document entries.
        """
        clean_documents(self.ui.model.data_path)
        self.set_table_data()

    def on_item_double_clicked(self, row: int, col: int, _value: str) -> None:
        """!
        @brief Callback for double-click events on table entries.
        @param row : clicked row index
        @param col : clicked column index
        @param _value : value of clicked cell
        """
        model = self.ui_document.table.model()
        assert model is not None
        uid_index = model.index(row, len(ROW_DESCRIPTION) - 1)
        uid = model.data(uid_index, Qt.ItemDataRole.DisplayRole)

        if uid:
            if col == ATTACH_IDX:
                self.open_document_file(uid)
            else:
                found_doc = next((doc for doc in self.documents if doc[EDocumentFields.ID] == uid), None)
                if found_doc is not None:
                    DocumentDialog(self.ui, found_doc, uid)
                    self.set_table_data()
                else:
                    self.ui.set_status("Document UID not found", True)  # state not possible

    def open_document_file(self, uid: str) -> None:
        """!
        @brief Opens the attached document file for the given UID.
        @param uid : Unique document identifier.
        """
        document_path = os.path.join(self.ui.model.data_path, DOCUMENT_FILE_PATH)
        attachment_file = find_file(document_path, uid)
        if attachment_file:
            os.startfile(os.path.abspath(attachment_file))

    def new_document(self, import_file: str | None = None) -> None:
        """!
        @brief Creates a new document entry and optionally imports a file.
        @param import_file : file to import
        """
        if import_file:
            if any(import_file.endswith(ext) for ext in INVOICE_FILE_EXTENSIONS):
                file_path = import_file
            else:
                file_path = None  # invalid file type
        else:
            file_path, _ = QFileDialog.getOpenFileName(parent=self.ui, caption="Dokument erfassen",
                                                       directory=self.ui.model.get_last_path(),
                                                       filter=PDF_FILE_TYPES)
        if file_path:
            self.ui.model.set_last_path(os.path.dirname(file_path))
            DocumentDialog(self.ui, file_path=file_path)
            self.set_table_data()
