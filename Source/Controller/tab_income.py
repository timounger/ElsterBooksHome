"""!
********************************************************************************
@file   tab_income.py
@brief  Invoice Tab
********************************************************************************
"""

import os
import logging
import subprocess
from typing import Any, TYPE_CHECKING, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFileDialog

from Source.version import __title__
from Source.Util.app_data import S_KEY_INCOME_COLUMN
from Source.Controller.table_filter import TableFilter, CellData, L_RECEIPT_ROW_DESCRIPTION, I_ATTACH_IDX, I_DESCRIPTION_IDX, \
    I_DATE_IDX, I_INVOICE_NUMBER_IDX
from Source.Controller.dialog_receipt import ReceiptDialog, EReceiptType
from Source.Controller.dialog_invoice import InvoiceDialog
from Source.Model.income import read_income, INCOME_FILE_PATH, export_income, delete_income
from Source.Model.data_handler import INVOICE_FILE_TYPES, clear_dialog_data, EReceiptFields, get_status, \
    find_file, L_INVOICE_FILE_TYPES
from Source.Model.company import ECompanyFields, COMPANY_DEFAULT_FIELD
if TYPE_CHECKING:
    from Source.Controller.main_window import MainWindow

log = logging.getLogger(__title__)


class TabIncome:
    """!
    @brief Income dialog tab.
    @param ui : main window
    @param tab_idx : tab index
    """

    def __init__(self, ui: "MainWindow", tab_idx: int) -> None:
        self.ui = ui
        s_title = "Einnahmen"
        ui.tabWidget.setTabText(tab_idx, s_title)
        self.ui_income = TableFilter(ui, ui.tabWidget, tab_idx, s_title, title_folder_link=INCOME_FILE_PATH,
                                     btn_1_name="Einnahme erfassen", btn_1_cb=self.new_income,
                                     btn_2_name="Rechnung erstellen", btn_2_cb=self.create_invoice,
                                     table_double_click_fnc=self.on_item_double_clicked, l_table_header=L_RECEIPT_ROW_DESCRIPTION,
                                     sort_idx=I_DATE_IDX, pre_sort_idx=I_INVOICE_NUMBER_IDX, inverse_sort=False, row_fill_idx=I_DESCRIPTION_IDX,
                                     delete_fnc=delete_income, update_table_func=self.set_table_data,
                                     drag_fnc=self.new_income,
                                     column_setting_key=S_KEY_INCOME_COLUMN)
        self.l_data: list[dict[EReceiptFields, Any]] = []
        self.total_gross = 0
        self.total_net = 0
        self.l_value: list[float] = []
        self.l_date: list[str] = []
        clear_dialog_data(self)

    def set_table_data(self, update: bool = False, rename: bool = False, update_dashboard: bool = True) -> None:
        """!
        @brief Read income data and update table.
        @param update : update status of JSON file
        @param rename : rename status of file name
        @param update_dashboard : update dashboard
        """
        clear_dialog_data(self)
        self.l_data = read_income(self.ui.model.data_path)
        l_data = []
        for income in self.l_data:
            if update:
                export_income(self.ui.model.data_path, self.ui.model.git_add, income, income[EReceiptFields.ID], rename=rename)
            status, icon = get_status(income, self.ui.tab_settings.company_data[COMPANY_DEFAULT_FIELD][ECompanyFields.PAYMENT_DAYS])
            l_entry = []
            l_entry.append(CellData(text=status, icon=icon))
            l_entry.append(CellData(text=income[EReceiptFields.PAYMENT_DATE], right_align=True, is_date=True))
            l_entry.append(CellData(text=income[EReceiptFields.INVOICE_DATE], right_align=True, is_date=True))
            l_entry.append(CellData(text=income[EReceiptFields.INVOICE_NUMBER]))
            l_entry.append(CellData(text=income[EReceiptFields.DELIVER_DATE]))
            l_entry.append(CellData(text=income[EReceiptFields.GROUP]))
            l_entry.append(CellData(icon=self.ui_income.get_attach_icon(income[EReceiptFields.ATTACHMENT])))
            l_entry.append(CellData(text=income[EReceiptFields.TRADE_PARTNER]))
            l_entry.append(CellData(text=income[EReceiptFields.DESCRIPTION]))
            l_entry.append(CellData(text=income[EReceiptFields.COMMENT]))
            if isinstance(income[EReceiptFields.AMOUNT_NET], (float, int)):
                l_entry.append(CellData(text=f"{income[EReceiptFields.AMOUNT_NET]:.2f} EUR", right_align=True))
                self.total_net += income[EReceiptFields.AMOUNT_NET]
            else:
                l_entry.append(CellData(text="", right_align=True))
            if isinstance(income[EReceiptFields.AMOUNT_GROSS], (float, int)):
                l_entry.append(CellData(text=f"{income[EReceiptFields.AMOUNT_GROSS]:.2f} EUR", right_align=True))
                self.total_gross += income[EReceiptFields.AMOUNT_GROSS]
                self.l_value.append(income[EReceiptFields.AMOUNT_GROSS])
                self.l_date.append(income[EReceiptFields.INVOICE_DATE])
            else:
                l_entry.append(CellData(text="", right_align=True))
            l_entry.append(CellData(text=income[EReceiptFields.ID]))
            l_data.append(l_entry)
        self.ui_income.update_table(l_data)
        self.ui_income.table.setColumnHidden(len(L_RECEIPT_ROW_DESCRIPTION) - 1, True)
        if update_dashboard:
            self.ui.tab_dashboard.update_dashboard_data()

    def on_item_double_clicked(self, row: int, col: int, _value: str) -> None:
        """!
        @brief Callback for double click on table entry.
        @param row : clicked row index
        @param col : clicked column index
        @param _value : value of clicked cell
        """
        model = self.ui_income.table.model()
        uid_index = model.index(row, len(L_RECEIPT_ROW_DESCRIPTION) - 1)
        uid = model.data(uid_index, Qt.ItemDataRole.DisplayRole)

        if uid is not None:
            if col == I_ATTACH_IDX:
                self.open_invoice_file(uid)
            else:
                found_income = next((income for income in self.l_data if income[EReceiptFields.ID] == uid), None)
                if found_income is not None:
                    ReceiptDialog(self.ui, found_income, uid, receipt_type=EReceiptType.INCOME)
                    self.set_table_data()
                else:
                    self.ui.set_status("Income UID not found", True)  # state not possible

    def open_invoice_file(self, uid: str) -> None:
        """!
        @brief Open invoice file.
        @param uid : uid
        """
        income_path = os.path.join(self.ui.model.data_path, INCOME_FILE_PATH)
        attachment_file = find_file(income_path, uid)
        if attachment_file:
            with subprocess.Popen(["start", "", attachment_file], shell=True):
                pass

    def create_invoice(self) -> None:
        """!
        @brief Create invoice.
        """
        invoice_dialog: Any = None
        if invoice_dialog is None:
            invoice_dialog = InvoiceDialog(self.ui)

    def new_income(self, import_file: Optional[str] = None) -> None:
        """!
        @brief Create new income.
        @param import_file : file to import
        """
        if import_file:
            if any(import_file.endswith(ext) for ext in L_INVOICE_FILE_TYPES):
                s_file_name_path = import_file
            else:
                s_file_name_path = None  # invalid file type
        else:
            s_file_name_path, _ = QFileDialog.getOpenFileName(parent=self.ui, caption="Einnahme erfassen",
                                                              directory=self.ui.model.get_last_path(),
                                                              filter=INVOICE_FILE_TYPES)
        if s_file_name_path:
            self.ui.model.set_last_path(os.path.dirname(s_file_name_path))
            ReceiptDialog(self.ui, file_path=s_file_name_path, receipt_type=EReceiptType.INCOME)
            self.set_table_data()
