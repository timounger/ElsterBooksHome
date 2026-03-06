"""!
********************************************************************************
@file   tab_receipt_base.py
@brief  Base class for income and expenditure tabs.
********************************************************************************
"""

import os
import logging
from typing import Any, Callable, TYPE_CHECKING
from fints.client import Transaction

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFileDialog

from Source.version import __title__
from Source.Controller.table_filter import TableFilter, CellData, RECEIPT_ROW_DESCRIPTION, ATTACH_IDX, DESCRIPTION_IDX, \
    DATE_IDX
from Source.Controller.dialog_receipt import ReceiptDialog, EReceiptType
from Source.Model.data_handler import INVOICE_FILE_TYPES, clear_dialog_data, EReceiptFields, get_status, \
    find_file, INVOICE_FILE_EXTENSIONS
from Source.Model.company import ECompanyFields, COMPANY_DEFAULT_FIELD
if TYPE_CHECKING:
    from Source.Controller.main_window import MainWindow

log = logging.getLogger(__title__)


class TabReceiptBase:
    """!
    @brief Base controller for receipt tabs (income/expenditure).
    @param ui : main window
    @param tab_idx : Index of this tab in the tab widget
    """

    def __init__(self, ui: "MainWindow", tab_idx: int, *,
                 title: str, file_path: str, column_setting_key: str,
                 btn_1_name: str, receipt_type: EReceiptType,
                 read_func: Callable[..., Any], export_func: Callable[..., Any],
                 delete_func: Callable[..., Any], clean_func: Callable[..., Any],
                 check_paid_func: Callable[..., Any] | None = None,
                 date_right_align: bool = False,
                 table_filter_kwargs: dict[str, Any] | None = None) -> None:
        self.ui = ui
        self._file_path = file_path
        self._receipt_type = receipt_type
        self._read_func = read_func
        self._export_func = export_func
        self._clean_func = clean_func
        self._check_paid_func = check_paid_func
        self._date_right_align = date_right_align
        ui.tabWidget.setTabText(tab_idx, title)
        extra_kwargs = table_filter_kwargs or {}
        self.table_filter = TableFilter(ui, ui.tabWidget, tab_idx, title, title_folder_link=file_path,
                                        btn_1_name=btn_1_name, btn_1_cb=self._new_receipt,
                                        table_double_click_fnc=self.on_item_double_clicked,
                                        table_header=RECEIPT_ROW_DESCRIPTION,
                                        sort_idx=DATE_IDX, inverse_sort=False, row_fill_idx=DESCRIPTION_IDX,
                                        delete_fnc=delete_func, update_table_func=self.set_table_data,
                                        drag_fnc=self._new_receipt,
                                        column_setting_key=column_setting_key,
                                        **extra_kwargs)
        self.receipts: list[dict[EReceiptFields, Any]] = []
        self.total_gross = 0
        self.total_net = 0
        self.values: list[float] = []
        self.invoice_dates: list[str] = []
        self.payment_dates: list[str] = []
        clear_dialog_data(self)

    def set_table_data(self, update: bool = False, rename: bool = False, update_dashboard: bool = True) -> None:
        """!
        @brief Reads receipt data and updates the table.
        @param update : Whether to re-export JSON files.
        @param rename : Whether to rename attachment files.
        @param update_dashboard : Whether to update the dashboard.
        """
        clear_dialog_data(self)
        self.receipts = self._read_func(self.ui.model.data_path)
        rows = []
        for receipt in self.receipts:
            if update:
                self._export_func(self.ui.model.data_path, self.ui.model.git_add, receipt, receipt[EReceiptFields.ID], rename=rename)
            status, icon = get_status(receipt, self.ui.tab_settings.company_data[COMPANY_DEFAULT_FIELD][ECompanyFields.PAYMENT_DAYS])
            if isinstance(receipt[EReceiptFields.AMOUNT_NET], (float, int)):
                net_cell = CellData(text=f"{receipt[EReceiptFields.AMOUNT_NET]:.2f} EUR", right_align=True)
                self.total_net += receipt[EReceiptFields.AMOUNT_NET]
            else:
                net_cell = CellData(text="", right_align=True)
            if isinstance(receipt[EReceiptFields.AMOUNT_GROSS], (float, int)):
                gross_cell = CellData(text=f"{receipt[EReceiptFields.AMOUNT_GROSS]:.2f} EUR", right_align=True)
                self.total_gross += receipt[EReceiptFields.AMOUNT_GROSS]
                self.values.append(receipt[EReceiptFields.AMOUNT_GROSS])
                self.invoice_dates.append(receipt[EReceiptFields.INVOICE_DATE])
                self.payment_dates.append(receipt[EReceiptFields.PAYMENT_DATE])
            else:
                gross_cell = CellData(text="", right_align=True)
            row = [
                CellData(text=status, icon=icon),
                CellData(text=receipt[EReceiptFields.PAYMENT_DATE], right_align=self._date_right_align, is_date=True),
                CellData(text=receipt[EReceiptFields.INVOICE_DATE], right_align=self._date_right_align, is_date=True),
                CellData(text=receipt[EReceiptFields.INVOICE_NUMBER]),
                CellData(text=receipt[EReceiptFields.DELIVER_DATE]),
                CellData(text=receipt[EReceiptFields.GROUP]),
                CellData(icon=self.table_filter.get_attach_icon(receipt[EReceiptFields.ATTACHMENT])),
                CellData(text=receipt[EReceiptFields.TRADE_PARTNER]),
                CellData(text=receipt[EReceiptFields.DESCRIPTION]),
                CellData(text=receipt[EReceiptFields.COMMENT]),
                net_cell,
                gross_cell,
                CellData(text=receipt[EReceiptFields.ID]),
            ]
            rows.append(row)
        self.table_filter.update_table(rows)
        self.table_filter.table.setColumnHidden(len(RECEIPT_ROW_DESCRIPTION) - 1, True)
        if update_dashboard:
            self.ui.tab_dashboard.update_dashboard_data()

    def clean_data(self) -> None:
        """!
        @brief Removes invalid or orphaned entries.
        """
        self._clean_func(self.ui.model.data_path)
        self.set_table_data()

    def check_for_paid(self, transactions: list[Transaction]) -> None:
        """!
        @brief Matches bank transactions to mark receipts as paid.
        @param transactions : List of bank transactions to match.
        """
        if self._check_paid_func:
            self._check_paid_func(self.ui.model.data_path, transactions)
            self.set_table_data()

    def on_item_double_clicked(self, row: int, col: int, _value: str) -> None:
        """!
        @brief Callback for double-click events on table entries.
        @param row : clicked row index
        @param col : clicked column index
        @param _value : Value of the clicked cell.
        """
        model = self.table_filter.table.model()
        assert model is not None
        uid_index = model.index(row, len(RECEIPT_ROW_DESCRIPTION) - 1)
        uid = model.data(uid_index, Qt.ItemDataRole.DisplayRole)

        if uid is not None:
            if col == ATTACH_IDX:
                self.open_invoice_file(uid)
            else:
                found_receipt = next((r for r in self.receipts if r[EReceiptFields.ID] == uid), None)
                if found_receipt is not None:
                    ReceiptDialog(self.ui, found_receipt, uid, receipt_type=self._receipt_type)
                    self.set_table_data()
                else:
                    self.ui.set_status(f"{self._receipt_type.name} UID not found", True)

    def open_invoice_file(self, uid: str) -> None:
        """!
        @brief Opens the attached invoice file for the given UID.
        @param uid : Unique receipt identifier.
        """
        receipt_path = os.path.join(self.ui.model.data_path, self._file_path)
        attachment_file = find_file(receipt_path, uid)
        if attachment_file:
            os.startfile(os.path.abspath(attachment_file))

    def _new_receipt(self, import_file: str | None = None) -> None:
        """!
        @brief Creates a new receipt entry and optionally imports a file.
        @param import_file : File path to import.
        """
        if import_file:
            if any(import_file.endswith(ext) for ext in INVOICE_FILE_EXTENSIONS):
                file_path = import_file
            else:
                file_path = None  # invalid file type
        else:
            caption = "Einnahme erfassen" if self._receipt_type == EReceiptType.INCOME else "Ausgabe erfassen"
            file_path, _ = QFileDialog.getOpenFileName(parent=self.ui, caption=caption,
                                                       directory=self.ui.model.get_last_path(),
                                                       filter=INVOICE_FILE_TYPES)
        if file_path:
            self.ui.model.set_last_path(os.path.dirname(file_path))
            ReceiptDialog(self.ui, file_path=file_path, receipt_type=self._receipt_type)
            self.set_table_data()
