"""!
********************************************************************************
@file   dialog_banking.py
@brief  Create banking dialog
********************************************************************************
"""

import logging
from typing import Optional, TYPE_CHECKING, Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import QDialog, QLineEdit

from Source.version import __title__
from Source.Util.app_data import thread_dialog, write_fints_blz, read_fints_blz, write_fints_url, read_fints_url, \
    write_fints_auth_data, read_fints_auth_data, write_fints_iban, read_fints_iban, write_fints_tan_mechanism, read_fints_tan_mechanism
from Source.Views.dialogs.dialog_banking_ui import Ui_DialogBanking
from Source.Model.fin_ts import FinTs, FinTSInstitute, delete_transaction_files
if TYPE_CHECKING:
    from Source.Controller.main_window import MainWindow

log = logging.getLogger(__title__)

UNKNOWN_INSTITUTE_NAME = "Unbekannt"


def build_institute_name(fints_institute: FinTSInstitute) -> str:
    """!
    @brief Build institute name
    @param fints_institute : institute
    @return institute name
    """
    return f"{fints_institute.institute} (BLZ: {fints_institute.blz})"


class BankingDialog(QDialog, Ui_DialogBanking):
    """!
    @brief Banking dialog.
    @param ui : main window
    """

    def __init__(self, ui: "MainWindow", *args: Any, **kwargs: Any) -> None:
        super().__init__(parent=ui, *args, **kwargs)  # type: ignore
        self.setupUi(self)
        self.setWindowFlags(Qt.WindowType.Window)  # set all window buttons (e.g max window size)
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        self.ui = ui

        self.fin_ts = FinTs(self.ui, self.pte_text)

        thread_dialog(self)

    def show_dialog(self) -> None:
        """!
        @brief Show dialog
        """
        log.debug("Starting Banking dialog")

        self.ui.model.c_monitor.set_dialog_style(self)

        # read last data
        blz = read_fints_blz()
        url = read_fints_url()
        user_id, pin = read_fints_auth_data()
        iban = read_fints_iban()
        tan_mechanism = read_fints_tan_mechanism()
        self.fin_ts.bank_code = blz
        self.fin_ts.fints_url = url
        self.fin_ts.user_id = user_id
        self.fin_ts.pin = pin
        self.fin_ts.iban = iban
        self.fin_ts.tan_mechanism = tan_mechanism

        # bank data
        l_fints_institutes_sorted = sorted(self.fin_ts.l_fints_institutes, key=lambda x: x.institute)
        l_used_institutes = []
        self.cb_institutes.addItem(UNKNOWN_INSTITUTE_NAME, None)
        for fints_institute in l_fints_institutes_sorted:
            institute_text = build_institute_name(fints_institute)
            if institute_text not in l_used_institutes:
                self.cb_institutes.addItem(institute_text, fints_institute)
                l_used_institutes.append(institute_text)
        self.cb_institutes.activated.connect(self.institute_activated)
        self.le_blz.setText(self.fin_ts.bank_code)
        self.le_url.setText(self.fin_ts.fints_url)
        self.le_alias.setText(self.fin_ts.user_id)
        self.le_pin.setEchoMode(QLineEdit.EchoMode.Password)
        self.le_pin.setText(self.fin_ts.pin)
        self.le_blz.textChanged.connect(self.bank_data_changed)
        self.le_url.textChanged.connect(self.bank_data_changed)
        self.bank_data_changed()  # update initial tab name

        # account data
        self.pte_text.setPlainText("")

        # buttons
        self.btn_get_transactions.setEnabled(False)
        self.btn_clear.clicked.connect(self.clear_btn_clicked)
        self.btn_connect.clicked.connect(self.connect_btn_clicked)
        self.btn_get_transactions.clicked.connect(self.get_transactions_btn_clicked)
        self.btn_payed_check.clicked.connect(self.confirm_btn_validate_payments)

        self.setWindowTitle("Bankverbindung")

        self.show()
        self.exec()

    def closeEvent(self, event: Optional[QCloseEvent]) -> None:  # pylint: disable=invalid-name
        """!
        @brief Default close Event Method to handle application close
        @param event : arrived event
        """
        if event is not None:
            event.accept()

    def institute_activated(self, _index: int) -> None:
        """!
        @brief Institute was selected. Update institute data.
        @param _index : index of selected institute entry
        """
        institute = self.cb_institutes.currentData()
        if institute is not None:
            blz = institute.blz
            url = institute.url
        else:
            blz = ""
            url = ""
        self.le_blz.setText(blz)
        self.le_url.setText(url)

    def bank_data_changed(self) -> None:
        """!
        @brief Bank data changed
        """
        blz = self.le_blz.text()
        url = self.le_url.text()

        b_found = False
        if blz:
            for fints_institute in self.fin_ts.l_fints_institutes:
                if fints_institute.blz == blz:
                    if url:
                        if fints_institute.url == url:
                            self.cb_institutes.setCurrentText(build_institute_name(fints_institute))
                            b_found = True
                            break
                    else:
                        self.le_url.setText(fints_institute.url)
                        self.cb_institutes.setCurrentText(build_institute_name(fints_institute))
                        b_found = True
                        break
        if not b_found:
            self.cb_institutes.setCurrentText(UNKNOWN_INSTITUTE_NAME)

    def clear_btn_clicked(self):
        """!
        @brief Clear button clicked.
        """
        blz = ""
        url = ""
        alias = ""
        pin = ""
        self.le_blz.setText(blz)
        self.le_url.setText(url)
        self.le_alias.setText(alias)
        self.le_pin.setText(pin)
        write_fints_blz(blz)
        write_fints_url(url)
        write_fints_auth_data(alias, pin)
        delete_transaction_files()

    def connect_btn_clicked(self):
        """!
        @brief Connect button clicked.
        """
        blz = self.le_blz.text()
        url = self.le_url.text()
        alias = self.le_alias.text()
        pin = self.le_pin.text()

        self.le_blz.setStyleSheet("border: 1px solid palette(dark);")
        self.le_url.setStyleSheet("border: 1px solid palette(dark);")
        self.le_alias.setStyleSheet("border: 1px solid palette(dark);")
        self.le_pin.setStyleSheet("border: 1px solid palette(dark);")
        if not blz:
            self.le_blz.setStyleSheet("border: 2px solid red;")
            self.ui.set_status("Keine BLZ vorhanden.", b_highlight=True)
        elif not url:
            self.le_url.setStyleSheet("border: 2px solid red;")
            self.ui.set_status("Keine URL vorhanden.", b_highlight=True)
        elif not alias:
            self.le_alias.setStyleSheet("border: 2px solid red;")
            self.ui.set_status("Kein Alias vorhanden.", b_highlight=True)
        elif not pin:
            self.le_pin.setStyleSheet("border: 2px solid red;")
            self.ui.set_status("Keine PIN vorhanden.", b_highlight=True)
        else:
            write_fints_blz(blz)
            write_fints_url(url)
            write_fints_auth_data(alias, pin)
            self.fin_ts.bank_code = blz
            self.fin_ts.fints_url = url
            self.fin_ts.user_id = alias
            self.fin_ts.pin = pin
            success, success_text = self.fin_ts.connect_client()
            self.pte_text.setPlainText(success_text)
            if success:
                # accounts
                d_accounts = self.fin_ts.get_accounts()
                self.cb_accounts.clear()
                for i, (account_name, iban) in enumerate(d_accounts.items()):
                    self.cb_accounts.addItem(account_name, iban)
                    self.btn_get_transactions.setEnabled(True)
                    if iban == self.fin_ts.iban:
                        self.cb_accounts.setCurrentIndex(i)
                # tan mechanism
                d_tan_mechanism = self.fin_ts.get_tan_mechanism()
                self.cb_tan_mechanisms.clear()
                for i, (mechanism_key, mechanism_name) in enumerate(d_tan_mechanism.items()):
                    self.cb_tan_mechanisms.addItem(mechanism_name, mechanism_key)
                    if mechanism_key == self.fin_ts.tan_mechanism:
                        self.cb_tan_mechanisms.setCurrentIndex(i)

    def get_transactions_btn_clicked(self):
        """!
        @brief Get transactions button clicked.
        """
        iban = self.cb_accounts.currentData()
        tan_mechanism = self.cb_tan_mechanisms.currentData()

        write_fints_iban(iban)
        write_fints_tan_mechanism(tan_mechanism)
        self.fin_ts.iban = iban
        self.fin_ts.tan_mechanism = tan_mechanism

        _success, success_text = self.fin_ts.get_and_create_transaction()

        self.pte_text.setPlainText(success_text)

    def confirm_btn_validate_payments(self):
        """!
        @brief Validate payments button clicked.
        """
        l_transaction = self.fin_ts.get_transactions()
        self.ui.tab_income.check_for_payed(l_transaction)
        self.ui.tab_expenditure.check_for_payed(l_transaction)
        self.ui.set_status("Zahlungen wurden überprüft und zugeordnet")
