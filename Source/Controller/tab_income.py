"""!
********************************************************************************
@file   tab_income.py
@brief  Tab for managing income.
********************************************************************************
"""

import logging
from typing import Any, TYPE_CHECKING

from Source.version import __title__
from Source.Util.app_data import KEY_INCOME_COLUMN, ICON_INVOICE_LIGHT, ICON_INVOICE_DARK
from Source.Controller.table_filter import INVOICE_NUMBER_IDX
from Source.Controller.dialog_receipt import EReceiptType
from Source.Controller.tab_receipt_base import TabReceiptBase
from Source.Controller.dialog_invoice import InvoiceDialog
from Source.Model.income import read_income, INCOME_FILE_PATH, export_income, delete_income, clean_income
from Source.Model.income import check_paid_income
if TYPE_CHECKING:
    from Source.Controller.main_window import MainWindow

log = logging.getLogger(__title__)


class TabIncome(TabReceiptBase):
    """!
    @brief Controller for the Income tab.
    @param ui : main window
    @param tab_idx : Index of this tab in the tab widget
    """

    def __init__(self, ui: "MainWindow", tab_idx: int) -> None:
        check_paid_func = check_paid_income
        super().__init__(ui, tab_idx,
                         title="Einnahmen",
                         file_path=INCOME_FILE_PATH,
                         column_setting_key=KEY_INCOME_COLUMN,
                         btn_1_name="Einnahme erfassen",
                         receipt_type=EReceiptType.INCOME,
                         read_func=read_income,
                         export_func=export_income,
                         delete_func=delete_income,
                         clean_func=clean_income,
                         check_paid_func=check_paid_func,
                         date_right_align=True,
                         table_filter_kwargs={
                             "btn_2_name": "Rechnung erstellen",
                             "btn_2_icon": (ICON_INVOICE_LIGHT, ICON_INVOICE_DARK),
                             "btn_2_cb": self.create_invoice,
                             "pre_sort_idx": INVOICE_NUMBER_IDX,
                         })
        # Alias for backward compatibility with external references
        self.ui_income = self.table_filter

    def create_invoice(self, uid: str | None = None) -> None:
        """!
        @brief Opens an invoice creation dialog.
        @param uid : Unique identifier of the contact.
        """
        invoice_dialog: Any = None
        if invoice_dialog is None:
            invoice_dialog = InvoiceDialog(self.ui, uid)

    def new_income(self, import_file: str | None = None) -> None:
        """!
        @brief Creates a new income entry and optionally imports a file.
        @param import_file : File path to import.
        """
        self._new_receipt(import_file)
