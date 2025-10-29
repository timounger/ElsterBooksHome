"""!
********************************************************************************
@file   dialog_contact.py
@brief  Create contact dialog
********************************************************************************
"""

import logging
from typing import Optional, TYPE_CHECKING, Any
import copy
import re

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import QDialog

from Source.version import __title__
from Source.Util.app_data import thread_dialog
from Source.Views.dialogs.dialog_contact_ui import Ui_DialogContact
from Source.Model.contacts import EContactFields, add_contact, remove_contact, CONTACT_CONTACT_FIELD, \
    CONTACT_ADDRESS_FIELD, D_CONTACT_TEMPLATE
from Source.Model.ZUGFeRD.drafthorse_data import D_COUNTRY_CODE
from Source.Model.ZUGFeRD.drafthorse_import import set_combo_box_items
from Source.Worker.vat_validation import VatValidation, check_vat_format, VAT_PATTERNS
if TYPE_CHECKING:
    from Source.Controller.main_window import MainWindow

log = logging.getLogger(__title__)

EMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"


class ContactDialog(QDialog, Ui_DialogContact):
    """!
    @brief Contact dialog.
    @param ui : main window
    @param data : contact data
    @param uid : UID of contact
    """

    def __init__(self, ui: "MainWindow", data: Optional[dict[EContactFields, str]] = None, uid: Optional[str] = None,  # pylint: disable=keyword-arg-before-vararg
                 *args: Any, **kwargs: Any) -> None:
        super().__init__(parent=ui, *args, **kwargs)  # type: ignore
        self.setupUi(self)
        self.setWindowFlags(Qt.WindowType.Window)  # set all window buttons (e.g max window size)
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        self.ui = ui
        self.data = data
        self.uid = uid
        self.b_lock_auto_city_data = False
        self.b_city_auto_change = False

        self.lbl_vat_status.setText("")
        self.vat_validator = VatValidation()
        self.vat_validator.finish_signal.connect(self.vat_result)
        self.le_vat.textChanged.connect(self.vat_id_changed)

        thread_dialog(self)

    def show_dialog(self) -> None:
        """!
        @brief Show dialog
        """
        log.debug("Starting Contact dialog")

        self.ui.model.c_monitor.set_dialog_style(self)

        if self.data is not None:
            self.b_lock_auto_city_data = True
            self.pte_name.setPlainText(self.data[EContactFields.NAME])
            self.le_trade_name.setText(self.data[EContactFields.TRADE_NAME])
            self.le_recognition.setText(self.data[EContactFields.CUSTOMER_NUMBER])
            self.le_register_number.setText(self.data[EContactFields.TRADE_ID])
            self.le_vat.setText(self.data[EContactFields.VAT_ID])
            self.le_electric_address.setText(self.data[EContactFields.ELECTRONIC_ADDRESS])
            self.le_street_1.setText(self.data[CONTACT_ADDRESS_FIELD][EContactFields.STREET_1])
            self.le_street_2.setText(self.data[CONTACT_ADDRESS_FIELD][EContactFields.STREET_2])
            self.le_plz.setText(self.data[CONTACT_ADDRESS_FIELD][EContactFields.PLZ])
            self.le_city.setText(self.data[CONTACT_ADDRESS_FIELD][EContactFields.CITY])
            self.le_first_name.setText(self.data[CONTACT_CONTACT_FIELD][EContactFields.FIRST_NAME])
            self.le_last_name.setText(self.data[CONTACT_CONTACT_FIELD][EContactFields.LAST_NAME])
            self.le_mail.setText(self.data[CONTACT_CONTACT_FIELD][EContactFields.MAIL])
            self.le_phone.setText(self.data[CONTACT_CONTACT_FIELD][EContactFields.PHONE])
            country = self.data[CONTACT_ADDRESS_FIELD][EContactFields.COUNTRY]
        else:
            self.btn_copy.hide()
            self.btn_delete.hide()
            country = "DE"
        set_combo_box_items(self.cb_country, country, D_COUNTRY_CODE)

        self.setWindowTitle("Kontakt")
        self.le_plz.textChanged.connect(self.plz_changed)
        self.le_city.textChanged.connect(self.city_changed)
        self.btn_save.clicked.connect(self.save_clicked)
        self.btn_copy.clicked.connect(self.copy_contact)
        self.btn_delete.clicked.connect(self.delete_clicked)
        self.btn_cancel.clicked.connect(self.close)

        self.show()
        self.exec()

    def closeEvent(self, event: Optional[QCloseEvent]) -> None:  # pylint: disable=invalid-name
        """!
        @brief Default close Event Method to handle application close
        @param event : arrived event
        """
        self.vat_validator.terminate()
        if event is not None:
            event.accept()

    def vat_id_changed(self, vat_id: str) -> None:
        """!
        @brief VAT ID changed
        @param vat_id : VAT id
        """
        self.vat_validator.terminate()
        if vat_id:
            if check_vat_format(vat_id):
                self.lbl_vat_status.setText("Überprüfung läuft...")
                self.lbl_vat_status.setStyleSheet("color: grey")
                self.vat_validator.vat_id = vat_id
                self.vat_validator.start()
            else:
                self.lbl_vat_status.setText("VAT Nummer ungültiges Format")
                self.lbl_vat_status.setStyleSheet("color: grey")
        else:
            self.lbl_vat_status.setText("")

    def vat_result(self, result: dict) -> None:
        """!
        @brief VAT result
        @param result : vat result
        """
        valid_status = result.get("valid", None)
        if valid_status is None:
            self.lbl_vat_status.setText("VAT Nummer nicht verifiziert")
            self.lbl_vat_status.setStyleSheet("color: grey")
        elif valid_status:
            self.lbl_vat_status.setText("VAT Nummer verifiziert")
            self.lbl_vat_status.setStyleSheet("color: green")
        else:
            self.lbl_vat_status.setText("VAT Nummer nicht bekannt")
            self.lbl_vat_status.setStyleSheet("color: red")

    def city_changed(self) -> None:
        """!
        @brief City changed
        """
        if self.b_city_auto_change:
            self.b_city_auto_change = False
            self.b_lock_auto_city_data = False
        else:
            self.b_lock_auto_city_data = bool(self.le_city.text().strip())

    def plz_changed(self) -> None:
        """!
        @brief PLZ changed
        """
        if (not self.b_lock_auto_city_data) and (self.ui.model.d_plz_data is not None):
            plz = self.le_plz.text().strip()
            if plz:
                new_city_name = self.ui.model.d_plz_data.get(plz, "")
                if new_city_name:
                    self.b_city_auto_change = True
                    self.le_city.setText(new_city_name)
                else:
                    self.le_city.clear()

    def delete_clicked(self) -> None:
        """!
        @brief Delete button clicked.
        """
        if self.uid is not None:
            remove_contact(self.ui.model.data_path, self.uid)
            self.ui.set_status("Kontakt gelöscht")
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
                add_contact(self.ui.model.data_path, self.ui.model.git_add, self.data, self.uid)
                if self.uid is None:
                    self.ui.set_status("Neuer Kontakt angelegt")
                else:
                    self.ui.set_status("Kontaktdaten gespeichert")
                self.close()
            else:
                log.warning("Save file clicked without data")

    def copy_contact(self) -> None:
        """!
        @brief Copy contact button clicked.
        """
        valid = self.set_data()
        if valid:
            if self.data is not None:
                self.data[EContactFields.NAME] += "_Kopie"
                add_contact(self.ui.model.data_path, self.ui.model.git_add, self.data, contact_id=None)
                self.ui.set_status("Kontakt Kopie angelegt")
                self.close()
            else:
                log.warning("Save file clicked without data")

    def set_data(self) -> bool:
        """!
        @brief If data valid set data.
        @return status if contact data are valid to save
        """
        organization = self.pte_name.toPlainText()
        vat_id = self.le_vat.text()
        street_1 = self.le_street_1.text()
        plz = self.le_plz.text()
        city = self.le_city.text()
        mail = self.le_mail.text()
        country_code = self.cb_country.currentData()
        # check for valid data
        self.pte_name.setStyleSheet("border: 1px solid palette(dark);")
        self.le_vat.setStyleSheet("border: 1px solid palette(dark);")
        self.le_street_1.setStyleSheet("border: 1px solid palette(dark);")
        self.le_plz.setStyleSheet("border: 1px solid palette(dark);")
        self.le_city.setStyleSheet("border: 1px solid palette(dark);")
        self.le_mail.setStyleSheet("border: 1px solid palette(dark);")
        valid = False
        if not organization:
            self.pte_name.setStyleSheet("border: 2px solid red;")
            self.ui.set_status("Kein Handelspartner vorhanden.", b_highlight=True)
        elif (len(vat_id) > 0) and (country_code in VAT_PATTERNS) and not check_vat_format(vat_id, pattern=VAT_PATTERNS[country_code]):
            self.le_vat.setStyleSheet("border: 2px solid red;")
            self.ui.set_status("Ungültige Umsatzsteuer-ID für das gewählte Land vorhanden.", b_highlight=True)
        elif not street_1:
            self.le_street_1.setStyleSheet("border: 2px solid red;")
            self.ui.set_status("Keine Straße vorhanden.", b_highlight=True)
        elif not plz:
            self.le_plz.setStyleSheet("border: 2px solid red;")
            self.ui.set_status("Keine PLZ vorhanden.", b_highlight=True)
        elif (country_code == "DE") and not plz.isdigit():  # in DE only digits allowed
            self.le_plz.setStyleSheet("border: 2px solid red;")
            self.ui.set_status("Ungültige PLZ vorhanden.", b_highlight=True)
        elif (country_code == "DE") and (len(plz) != 5):  # in DE PLZ only 5 digits
            self.le_plz.setStyleSheet("border: 2px solid red;")
            self.ui.set_status("Ungültige PLZ vorhanden.", b_highlight=True)
        elif not city:
            self.le_city.setStyleSheet("border: 2px solid red;")
            self.ui.set_status("Kein Ort vorhanden.", b_highlight=True)
        elif (len(mail) > 0) and ((re.match(EMAIL_REGEX, mail) is None) or ("\n" in mail)):
            self.le_mail.setStyleSheet("border: 2px solid red;")
            self.ui.set_status("Ungültiges E-Mail Format", b_highlight=True)
        else:
            valid = True
        if valid:
            self.data = copy.deepcopy(D_CONTACT_TEMPLATE)
            self.data[EContactFields.NAME] = organization
            self.data[EContactFields.TRADE_NAME] = self.le_trade_name.text()
            self.data[EContactFields.CUSTOMER_NUMBER] = self.le_recognition.text()
            self.data[EContactFields.TRADE_ID] = self.le_register_number.text()
            self.data[EContactFields.VAT_ID] = vat_id
            self.data[EContactFields.ELECTRONIC_ADDRESS] = self.le_electric_address.text()
            self.data[CONTACT_ADDRESS_FIELD][EContactFields.STREET_1] = street_1
            self.data[CONTACT_ADDRESS_FIELD][EContactFields.STREET_2] = self.le_street_2.text()
            self.data[CONTACT_ADDRESS_FIELD][EContactFields.PLZ] = plz
            self.data[CONTACT_ADDRESS_FIELD][EContactFields.CITY] = city
            self.data[CONTACT_ADDRESS_FIELD][EContactFields.COUNTRY] = country_code
            self.data[CONTACT_CONTACT_FIELD][EContactFields.FIRST_NAME] = self.le_first_name.text()
            self.data[CONTACT_CONTACT_FIELD][EContactFields.LAST_NAME] = self.le_last_name.text()
            self.data[CONTACT_CONTACT_FIELD][EContactFields.MAIL] = mail
            self.data[CONTACT_CONTACT_FIELD][EContactFields.PHONE] = self.le_phone.text()
        return valid
