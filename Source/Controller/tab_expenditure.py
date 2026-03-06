"""!
********************************************************************************
@file   tab_expenditure.py
@brief  Tab for managing expenditure.
********************************************************************************
"""

import logging
from typing import TYPE_CHECKING

from Source.version import __title__
from Source.Util.app_data import KEY_EXPENDITURE_COLUMN
from Source.Controller.dialog_receipt import EReceiptType
from Source.Controller.tab_receipt_base import TabReceiptBase
from Source.Model.expenditure import read_expenditure, EXPENDITURE_FILE_PATH, export_expenditure, delete_expenditure, clean_expenditure
from Source.Model.expenditure import check_paid_expenditure
if TYPE_CHECKING:
    from Source.Controller.main_window import MainWindow

log = logging.getLogger(__title__)


class TabExpenditure(TabReceiptBase):
    """!
    @brief Controller for the Expenditure tab.
    @param ui : main window
    @param tab_idx : Index of this tab in the tab widget
    """

    def __init__(self, ui: "MainWindow", tab_idx: int) -> None:
        check_paid_func = check_paid_expenditure
        super().__init__(ui, tab_idx,
                         title="Ausgaben",
                         file_path=EXPENDITURE_FILE_PATH,
                         column_setting_key=KEY_EXPENDITURE_COLUMN,
                         btn_1_name="Ausgabe erfassen",
                         receipt_type=EReceiptType.EXPENDITURE,
                         read_func=read_expenditure,
                         export_func=export_expenditure,
                         delete_func=delete_expenditure,
                         clean_func=clean_expenditure,
                         check_paid_func=check_paid_func,
                         date_right_align=False)
        # Alias for backward compatibility with external references
        self.ui_expenditure = self.table_filter

    def new_expenditure(self, import_file: str | None = None) -> None:
        """!
        @brief Creates a new expenditure entry and optionally imports a file.
        @param import_file : File path to import.
        """
        self._new_receipt(import_file)
