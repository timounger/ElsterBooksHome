"""!
********************************************************************************
@file   tab_document.py
@brief  Document Tab
********************************************************************************
"""

import os
import logging
import subprocess
from typing import TYPE_CHECKING, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFileDialog

from Source.version import __title__
from Source.Util.app_data import S_KEY_DOCUMENT_COLUMN
from Source.Controller.table_filter import TableFilter, CellData, ATTACH
from Source.Controller.dialog_document import DocumentDialog
from Source.Model.document import read_document, DOCUMENT_FILE_PATH, EDocumentFields, add_document, remove_document
from Source.Model.data_handler import PDF_FILE_TYPES, clear_dialog_data, find_file, L_INVOICE_FILE_TYPES
if TYPE_CHECKING:
    from Source.Controller.main_window import MainWindow

log = logging.getLogger(__title__)

L_ROW_DESCRIPTION = ["Datum", ATTACH, "Beschreibung", "ID"]
I_ATTACH_IDX = L_ROW_DESCRIPTION.index(ATTACH)


class TabDocument:
    """!
    @brief Document dialog tab.
    @param ui : main window
    @param tab_idx : tab index
    """

    def __init__(self, ui: "MainWindow", tab_idx: int) -> None:
        self.ui = ui
        s_title = "Dokumente"
        ui.tabWidget.setTabText(tab_idx, s_title)
        self.ui_document = TableFilter(ui, ui.tabWidget, tab_idx, s_title, title_folder_link=DOCUMENT_FILE_PATH,
                                       btn_1_name="Dokument erfassen", btn_1_cb=self.new_document,
                                       table_double_click_fnc=self.on_item_double_clicked, l_table_header=L_ROW_DESCRIPTION,
                                       sort_idx=0, inverse_sort=False, row_fill_idx=len(L_ROW_DESCRIPTION) - 2,
                                       delete_fnc=remove_document, update_table_func=self.set_table_data,
                                       drag_fnc=self.new_document,
                                       column_setting_key=S_KEY_DOCUMENT_COLUMN)
        self.l_data: list[dict[EDocumentFields, str]] = []
        clear_dialog_data(self)

    def set_table_data(self, update: bool = False, rename: bool = False, update_dashboard: bool = True) -> None:
        """!
        @brief Read document data and update table.
        @param update : update status of JSON file
        @param rename : rename status of file name
        @param update_dashboard : update dashboard
        """
        clear_dialog_data(self)
        self.l_data = read_document(self.ui.model.data_path)
        l_data = []
        for document in self.l_data:
            if update:
                add_document(self.ui.model.data_path, self.ui.model.git_add, document, document[EDocumentFields.ID], rename=rename)
            l_entry = []
            l_entry.append(CellData(text=document[EDocumentFields.DOCUMENT_DATE], right_align=True, is_date=True))
            l_entry.append(CellData(icon=self.ui_document.get_attach_icon(document[EDocumentFields.ATTACHMENT])))
            l_entry.append(CellData(text=document[EDocumentFields.DESCRIPTION]))
            l_entry.append(CellData(text=document[EDocumentFields.ID]))
            l_data.append(l_entry)
        self.ui_document.update_table(l_data)
        self.ui_document.table.setColumnHidden(len(L_ROW_DESCRIPTION) - 1, True)
        if update_dashboard:
            self.ui.tab_dashboard.update_dashboard_data()

    def on_item_double_clicked(self, row: int, col: int, _value: str) -> None:
        """!
        @brief Callback for double click on table entry.
        @param row : clicked row index
        @param col : clicked column index
        @param _value : value of clicked cell
        """
        model = self.ui_document.table.model()
        uid_index = model.index(row, len(L_ROW_DESCRIPTION) - 1)
        uid = model.data(uid_index, Qt.ItemDataRole.DisplayRole)

        if uid:
            if col == I_ATTACH_IDX:
                self.open_document_file(uid)
            else:
                found_doc = next((doc for doc in self.l_data if doc[EDocumentFields.ID] == uid), None)
                if found_doc is not None:
                    DocumentDialog(self.ui, found_doc, uid)
                    self.set_table_data()
                else:
                    self.ui.set_status("Document UID not found", True)  # state not possible

    def open_document_file(self, uid: str) -> None:
        """!
        @brief Open document file.
        @param uid : uid
        """
        document_path = os.path.join(self.ui.model.data_path, DOCUMENT_FILE_PATH)
        attachment_file = find_file(document_path, uid)
        if attachment_file:
            with subprocess.Popen(["start", "", attachment_file], shell=True):
                pass

    def new_document(self, import_file: Optional[str] = None) -> None:
        """!
        @brief Add new document.
        @param import_file : file to import
        """
        if import_file:
            if any(import_file.endswith(ext) for ext in L_INVOICE_FILE_TYPES):
                s_file_name_path = import_file
            else:
                s_file_name_path = None  # invalid file type
        else:
            s_file_name_path, _ = QFileDialog.getOpenFileName(parent=self.ui, caption="Dokument erfassen",
                                                              directory=self.ui.model.get_last_path(),
                                                              filter=PDF_FILE_TYPES)
        if s_file_name_path:
            self.ui.model.set_last_path(os.path.dirname(s_file_name_path))
            DocumentDialog(self.ui, file_path=s_file_name_path)
            self.set_table_data()
