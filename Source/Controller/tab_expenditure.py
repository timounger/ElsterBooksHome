"""!
********************************************************************************
@file   tab_expenditure.py
@brief  Expenditure Tab
********************************************************************************
"""

import os
import logging
import subprocess
from typing import Any, TYPE_CHECKING, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFileDialog

from Source.version import __title__
from Source.Util.app_data import S_KEY_EXPENDITURE_COLUMN
from Source.Controller.table_filter import TableFilter, CellData, L_RECEIPT_ROW_DESCRIPTION, I_ATTACH_IDX, I_DESCRIPTION_IDX, \
    I_DATE_IDX
from Source.Controller.dialog_receipt import ReceiptDialog, EReceiptType
from Source.Model.expenditure import read_expenditure, EXPENDITURE_FILE_PATH, export_expenditure, delete_expenditure
from Source.Model.data_handler import INVOICE_FILE_TYPES, clear_dialog_data, EReceiptFields, get_status, \
    find_file, L_INVOICE_FILE_TYPES
from Source.Model.company import ECompanyFields, COMPANY_DEFAULT_FIELD
if TYPE_CHECKING:
    from Source.Controller.main_window import MainWindow

log = logging.getLogger(__title__)


class TabExpenditure:
    """!
    @brief Expenditure dialog tab.
    @param ui : main window
    @param tab_idx : tab index
    """

    def __init__(self, ui: "MainWindow", tab_idx: int) -> None:
        self.ui = ui
        s_title = "Ausgaben"
        ui.tabWidget.setTabText(tab_idx, s_title)
        self.ui_expenditure = TableFilter(ui, ui.tabWidget, tab_idx, s_title, title_folder_link=EXPENDITURE_FILE_PATH,
                                          btn_1_name="Ausgabe erfassen", btn_1_cb=self.new_expenditure,
                                          table_double_click_fnc=self.on_item_double_clicked, l_table_header=L_RECEIPT_ROW_DESCRIPTION,
                                          sort_idx=I_DATE_IDX, inverse_sort=False, row_fill_idx=I_DESCRIPTION_IDX,
                                          delete_fnc=delete_expenditure, update_table_func=self.set_table_data,
                                          drag_fnc=self.new_expenditure,
                                          column_setting_key=S_KEY_EXPENDITURE_COLUMN)
        self.l_data: list[dict[EReceiptFields, Any]] = []
        self.total_gross = 0
        self.total_net = 0
        self.l_value: list[float] = []
        self.l_date: list[str] = []
        clear_dialog_data(self)

    def set_table_data(self, update: bool = False, rename: bool = False, update_dashboard: bool = True) -> None:
        """!
        @brief Read expenditure data and update table.
        @param update : update status of JSON file
        @param rename : rename status of file name
        @param update_dashboard : update dashboard
        """
        clear_dialog_data(self)
        self.l_data = read_expenditure(self.ui.model.data_path)
        l_data = []
        for expenditure in self.l_data:
            if update:
                export_expenditure(self.ui.model.data_path, self.ui.model.git_add, expenditure, expenditure[EReceiptFields.ID], rename=rename)
            status, icon = get_status(expenditure, self.ui.tab_settings.company_data[COMPANY_DEFAULT_FIELD][ECompanyFields.PAYMENT_DAYS])
            l_entry = []
            l_entry.append(CellData(text=status, icon=icon))
            l_entry.append(CellData(text=expenditure[EReceiptFields.PAYMENT_DATE], is_date=True))
            l_entry.append(CellData(text=expenditure[EReceiptFields.INVOICE_DATE], is_date=True))
            l_entry.append(CellData(text=expenditure[EReceiptFields.INVOICE_NUMBER]))
            l_entry.append(CellData(text=expenditure[EReceiptFields.DELIVER_DATE]))
            l_entry.append(CellData(text=expenditure[EReceiptFields.GROUP]))
            l_entry.append(CellData(icon=self.ui_expenditure.get_attach_icon(expenditure[EReceiptFields.ATTACHMENT])))
            l_entry.append(CellData(text=expenditure[EReceiptFields.TRADE_PARTNER]))
            l_entry.append(CellData(text=expenditure[EReceiptFields.DESCRIPTION]))
            l_entry.append(CellData(text=expenditure[EReceiptFields.COMMENT]))
            if isinstance(expenditure[EReceiptFields.AMOUNT_NET], (float, int)):
                l_entry.append(CellData(text=f"{expenditure[EReceiptFields.AMOUNT_NET]:.2f} EUR", right_align=True))
                self.total_net += expenditure[EReceiptFields.AMOUNT_NET]
            else:
                l_entry.append(CellData(text="", right_align=True))
            if isinstance(expenditure[EReceiptFields.AMOUNT_GROSS], (float, int)):
                l_entry.append(CellData(text=f"{expenditure[EReceiptFields.AMOUNT_GROSS]:.2f} EUR", right_align=True))
                self.total_gross += expenditure[EReceiptFields.AMOUNT_GROSS]
                self.l_value.append(expenditure[EReceiptFields.AMOUNT_GROSS])
                self.l_date.append(expenditure[EReceiptFields.INVOICE_DATE])
            else:
                l_entry.append(CellData(text="", right_align=True))
            l_entry.append(CellData(text=expenditure[EReceiptFields.ID]))
            l_data.append(l_entry)
        self.ui_expenditure.update_table(l_data)
        self.ui_expenditure.table.setColumnHidden(len(L_RECEIPT_ROW_DESCRIPTION) - 1, True)
        if update_dashboard:
            self.ui.tab_dashboard.update_dashboard_data()

    def on_item_double_clicked(self, row: int, col: int, _value: str) -> None:
        """!
        @brief Callback for double click on table entry.
        @param row : clicked row index
        @param col : clicked column index
        @param _value : value of clicked cell
        """
        model = self.ui_expenditure.table.model()
        uid_index = model.index(row, len(L_RECEIPT_ROW_DESCRIPTION) - 1)
        uid = model.data(uid_index, Qt.ItemDataRole.DisplayRole)

        if uid is not None:
            if col == I_ATTACH_IDX:
                self.open_invoice_file(uid)
            else:
                found_expenditure = next((expenditure for expenditure in self.l_data if expenditure[EReceiptFields.ID] == uid), None)
                if found_expenditure is not None:
                    ReceiptDialog(self.ui, found_expenditure, uid, receipt_type=EReceiptType.EXPENDITURE)
                    self.set_table_data()
                else:
                    self.ui.set_status("Expenditure UID not found", True)  # state not possible

    def open_invoice_file(self, uid: str) -> None:
        """!
        @brief Open invoice file.
        @param uid : uid
        """
        expenditure_path = os.path.join(self.ui.model.data_path, EXPENDITURE_FILE_PATH)
        attachment_file = find_file(expenditure_path, uid)
        if attachment_file:
            with subprocess.Popen(["start", "", attachment_file], shell=True):
                pass

    def new_expenditure(self, import_file: Optional[str] = None) -> None:
        """!
        @brief Create new expenditure.
        @param import_file : file to import
        """
        if import_file:
            if any(import_file.endswith(ext) for ext in L_INVOICE_FILE_TYPES):
                s_file_name_path = import_file
            else:
                s_file_name_path = None  # invalid file type
        else:
            s_file_name_path, _ = QFileDialog.getOpenFileName(parent=self.ui, caption="Ausgabe erfassen",
                                                              directory=self.ui.model.get_last_path(),
                                                              filter=INVOICE_FILE_TYPES)
        if s_file_name_path:
            self.ui.model.set_last_path(os.path.dirname(s_file_name_path))
            ReceiptDialog(self.ui, file_path=s_file_name_path, receipt_type=EReceiptType.EXPENDITURE)
            self.set_table_data()
