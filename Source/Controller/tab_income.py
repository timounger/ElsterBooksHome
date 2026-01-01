"""!
********************************************************************************
@file   tab_income.py
@brief  Tab for managing income.
********************************************************************************
"""

import os
import logging
import subprocess
from typing import Any, TYPE_CHECKING, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFileDialog

from Source.version import __title__
from Source.Util.app_data import S_KEY_INCOME_COLUMN, ICON_INVOICE_LIGHT, ICON_INVOICE_DARK
from Source.Controller.table_filter import TableFilter, CellData, L_RECEIPT_ROW_DESCRIPTION, I_ATTACH_IDX, I_DESCRIPTION_IDX, \
    I_DATE_IDX, I_INVOICE_NUMBER_IDX
from Source.Controller.dialog_receipt import ReceiptDialog, EReceiptType
from Source.Controller.dialog_invoice import InvoiceDialog
from Source.Model.income import read_income, INCOME_FILE_PATH, export_income, delete_income, clean_income
from Source.Model.income import check_paid_income
from Source.Model.data_handler import INVOICE_FILE_TYPES, clear_dialog_data, EReceiptFields, get_status, \
    find_file, L_INVOICE_FILE_TYPES
from Source.Model.company import ECompanyFields, COMPANY_DEFAULT_FIELD
from Source.Model.fin_ts import Transaction
if TYPE_CHECKING:
    from Source.Controller.main_window import MainWindow

log = logging.getLogger(__title__)


class TabIncome:
    """!
    @brief Controller for the Income tab.
    @param ui : main window
    @param tab_idx : Index of this tab in the tab widget
    """

    def __init__(self, ui: "MainWindow", tab_idx: int) -> None:
        self.ui = ui
        s_title = "Einnahmen"
        ui.tabWidget.setTabText(tab_idx, s_title)
        self.ui_income = TableFilter(ui, ui.tabWidget, tab_idx, s_title, title_folder_link=INCOME_FILE_PATH,
                                     btn_1_name="Einnahme erfassen", btn_1_cb=self.new_income,
                                     btn_2_name="Rechnung erstellen", btn_2_icon=(ICON_INVOICE_LIGHT, ICON_INVOICE_DARK), btn_2_cb=self.create_invoice,
                                     table_double_click_fnc=self.on_item_double_clicked, l_table_header=L_RECEIPT_ROW_DESCRIPTION,
                                     sort_idx=I_DATE_IDX, pre_sort_idx=I_INVOICE_NUMBER_IDX, inverse_sort=False, row_fill_idx=I_DESCRIPTION_IDX,
                                     delete_fnc=delete_income, update_table_func=self.set_table_data,
                                     drag_fnc=self.new_income,
                                     column_setting_key=S_KEY_INCOME_COLUMN)
        self.l_data: list[dict[EReceiptFields, Any]] = []
        self.total_gross = 0
        self.total_net = 0
        self.l_value: list[float] = []
        self.l_invoice_date: list[str] = []
        self.l_payment_date: list[str] = []
        clear_dialog_data(self)

    def set_table_data(self, update: bool = False, rename: bool = False, update_dashboard: bool = True) -> None:
        """!
        @brief Reads income data and updates the table.
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
                self.l_invoice_date.append(income[EReceiptFields.INVOICE_DATE])
                self.l_payment_date.append(income[EReceiptFields.PAYMENT_DATE])
            else:
                l_entry.append(CellData(text="", right_align=True))
            l_entry.append(CellData(text=income[EReceiptFields.ID]))
            l_data.append(l_entry)
        self.ui_income.update_table(l_data)
        self.ui_income.table.setColumnHidden(len(L_RECEIPT_ROW_DESCRIPTION) - 1, True)
        if update_dashboard:
            self.ui.tab_dashboard.update_dashboard_data()

    def clean_data(self) -> None:
        """!
        @brief Removes invalid or orphaned income entries.
        """
        clean_income(self.ui.model.data_path)
        self.set_table_data()

    def check_for_paid(self, l_transaction: list[Transaction]) -> None:
        """!
        @brief Matches bank transactions to mark income as paid.
        @param l_transaction : transactions
        """
        check_paid_income(self.ui.model.data_path, l_transaction)
        self.set_table_data()

    def on_item_double_clicked(self, row: int, col: int, _value: str) -> None:
        """!
        @brief Callback for double-click events on table entries.
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
        @brief Opens the attached invoice file for the given UID.
        @param uid : uid
        """
        income_path = os.path.join(self.ui.model.data_path, INCOME_FILE_PATH)
        attachment_file = find_file(income_path, uid)
        if attachment_file:
            with subprocess.Popen(["start", "", attachment_file], shell=True):
                pass

    def create_invoice(self, uid: Optional[str] = None) -> None:
        """!
        @brief Opens an invoice creation dialog.
        @param uid : uid of contact
        """
        invoice_dialog: Any = None
        if invoice_dialog is None:
            invoice_dialog = InvoiceDialog(self.ui, uid)

    def new_income(self, import_file: Optional[str] = None) -> None:
        """!
        @brief Creates a new income entry and optionally imports a file.
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
