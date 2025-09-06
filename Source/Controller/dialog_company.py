"""!
********************************************************************************
@file   dialog_company.py
@brief  Create company dialog
********************************************************************************
"""

import os
import logging
from typing import Optional, Any, TYPE_CHECKING
import shutil

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QCloseEvent
from PyQt6.QtWidgets import QDialog, QLineEdit, QFileDialog

from Source.version import __title__
from Source.Util.app_data import EAiType, write_ai_type, write_api_key, thread_dialog
from Source.Model.data_handler import COMPANY_LOGO_TYPES  # pylint: disable=wrong-import-position
from Source.Model.ZUGFeRD.drafthorse_data import D_COUNTRY_CODE  # pylint: disable=wrong-import-position
from Source.Views.dialogs.dialog_company_ui import Ui_DialogCompany  # pylint: disable=wrong-import-position
from Source.Model.company import ECompanyFields, add_company, LOGO_BRIEF_PATH, D_COMPANY_TEMPLATE, DEFAULT_TAX_RATES, \
    COMPANY_ADDRESS_FIELD, COMPANY_CONTACT_FIELD, COMPANY_PAYMENT_FIELD, COMPANY_BOOKING_FIELD, COMPANY_DEFAULT_FIELD  # pylint: disable=wrong-import-position
from Source.Model.ZUGFeRD.drafthorse_import import set_combo_box_items  # pylint: disable=wrong-import-position
from Source.Worker.vat_validation import VatValidation, check_vat_format  # pylint: disable=wrong-import-position
from Source.Worker.open_ai import DEFAULT_GPT_MODEL  # pylint: disable=wrong-import-position
from Source.Worker.ollama_ai import EOllamaModel  # pylint: disable=wrong-import-position
if TYPE_CHECKING:
    from Source.Controller.main_window import MainWindow

log = logging.getLogger(__title__)


def parse_number(s_string: str) -> float | int | None:
    """!
    @brief parse number to int or float
    @param s_string : string to check
    @return number
    """
    try:
        number = float(s_string)
        if number.is_integer():
            number = int(number)
        return number
    except ValueError:
        return None


class CompanyDialog(QDialog, Ui_DialogCompany):
    """!
    @brief Company dialog tab.
    @param ui : main window
    @param company_data : company data
    @param uid : UID of company
    """

    def __init__(self, ui: "MainWindow", company_data: Optional[dict[Any, Any]] = None, uid: Optional[str] = None,  # pylint: disable=keyword-arg-before-vararg
                 *args: Any, **kwargs: Any) -> None:
        super().__init__(parent=ui, *args, **kwargs)  # type: ignore
        self.setupUi(self)
        self.setWindowFlags(Qt.WindowType.Window)  # set all window buttons (e.g max window size)
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        self.ui = ui
        self.company_data = company_data
        self.uid = uid
        self.b_lock_auto_city_data = False
        self.b_city_auto_change = False
        self.logo_path = None  # path to import

        self.lbl_vat_status.setText("")
        self.vat_validator = VatValidation()
        self.vat_validator.finish_signal.connect(self.vat_result)
        self.le_vat.textChanged.connect(self.vat_id_changed)

        thread_dialog(self)

    def show_dialog(self) -> None:
        """!
        @brief Show dialog.
        """
        log.debug("Starting Company dialog")

        self.ui.model.c_monitor.set_dialog_style(self)

        if self.company_data is None:
            self.company_data = D_COMPANY_TEMPLATE
        else:
            self.b_lock_auto_city_data = True

        company = self.company_data
        company_address = company[COMPANY_ADDRESS_FIELD]
        company_contact = company[COMPANY_CONTACT_FIELD]
        company_payment = company[COMPANY_PAYMENT_FIELD]
        company_booking = company[COMPANY_BOOKING_FIELD]
        company_default = company[COMPANY_DEFAULT_FIELD]
        # company
        self.pte_name.setPlainText(company[ECompanyFields.NAME])
        self.le_trade_name.setText(company[ECompanyFields.TRADE_NAME])
        self.le_register_number.setText(company[ECompanyFields.TRADE_ID])
        self.le_vat.setText(company[ECompanyFields.VAT_ID])
        self.le_tax_number.setText(company[ECompanyFields.TAX_ID])
        self.pte_law_information.setPlainText(company[ECompanyFields.LEGAL_INFO])
        self.le_electric_address.setText(company[ECompanyFields.ELECTRONIC_ADDRESS])
        self.le_website.setText(company[ECompanyFields.WEBSITE_TEXT])
        # address
        self.le_street_1.setText(company_address[ECompanyFields.STREET_1])
        self.le_street_2.setText(company_address[ECompanyFields.STREET_2])
        self.le_plz.setText(company_address[ECompanyFields.PLZ])
        self.le_city.setText(company_address[ECompanyFields.CITY])
        set_combo_box_items(self.cb_country, company_address[ECompanyFields.COUNTRY], D_COUNTRY_CODE)
        # contact
        self.le_first_name.setText(company_contact[ECompanyFields.FIRST_NAME])
        self.le_last_name.setText(company_contact[ECompanyFields.LAST_NAME])
        self.le_mail.setText(company_contact[ECompanyFields.MAIL])
        self.le_phone.setText(company_contact[ECompanyFields.PHONE])
        # payment
        self.le_bank_name.setText(company_payment[ECompanyFields.BANK_NAME])
        self.le_iban.setText(company_payment[ECompanyFields.BANK_IBAN])
        self.le_bic.setText(company_payment[ECompanyFields.BANK_BIC])
        self.le_bank_owner.setText(company_payment[ECompanyFields.BANK_OWNER])
        # booking
        if company_booking[ECompanyFields.SMALL_BUSINESS_REGULATION]:
            self.rb_ust_no.setChecked(True)
        else:
            self.rb_ust_default.setChecked(True)
        if company_booking[ECompanyFields.PROFIT_CALCULATION_CAPITAL]:
            self.rb_marge_guv.setChecked(True)
        else:
            self.rb_marge_eur.setChecked(True)
        if company_booking[ECompanyFields.AGREED_COST]:
            self.rb_tax_soll.setChecked(True)
        else:
            self.rb_tax_ist.setChecked(True)
        self.le_tax_rates.setText(" ".join(str(i) for i in company_booking[ECompanyFields.TAX_RATES]))
        # default
        if company_default[ECompanyFields.QUARTERLY_SALES_TAX]:
            self.rb_ustva_quaterly.setChecked(True)
        else:
            self.rb_ustva_monthly.setChecked(True)
        self.cb_payed.setChecked(company_default[ECompanyFields.PAYED])
        self.cb_bar_payed.setChecked(company_default[ECompanyFields.BAR_PAYED])
        self.le_default_group_income.setText(company_default[ECompanyFields.INCOME_GROUP])
        self.le_default_group_expenditure.setText(company_default[ECompanyFields.EXPENDITURE_GROUP])
        self.pte_group_list.setPlainText("\n".join(company_default[ECompanyFields.GROUPS]))
        self.sb_payment_days.setValue(company_default[ECompanyFields.PAYMENT_DAYS])
        self.le_mail_subtract.setText(company_default[ECompanyFields.MAIL_SUBJECT])
        self.pte_mail_template.setPlainText(company_default[ECompanyFields.MAIL_TEXT])
        # AI
        match self.ui.model.ai_type:
            case EAiType.DEACTIVATED:
                self.rb_ai_deactivated.setChecked(True)
            case EAiType.OPEN_AI:
                self.rb_ai_chatgpt.setChecked(True)
            case EAiType.OLLAMA:
                self.rb_ai_ollama.setChecked(True)
            case _:
                log.warning("Invalid AI type: %s", self.ui.model.ai_type)
        self.rb_ai_deactivated.toggled.connect(self.ai_changed)
        self.rb_ai_chatgpt.toggled.connect(self.ai_changed)
        self.rb_ai_ollama.toggled.connect(self.ai_changed)
        # API key
        self.le_ai_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.le_ai_api_key.setText(self.ui.model.c_open_ai.api_key)
        self.ai_changed()  # update ai widgets depend on model
        # External tools
        self.line_external_tools.hide()
        self.lbl_external_tools.hide()
        self.lbl_libre_office_description.hide()
        self.lbl_libre_office_path.hide()
        self.le_libre_office_path.hide()
        # logo
        self.btn_change_logo.clicked.connect(self.select_logo)
        logo_path = os.path.join(self.ui.model.data_path, LOGO_BRIEF_PATH)
        self.select_logo(logo_path)

        self.setWindowTitle("Persönliche Daten")
        self.le_plz.textChanged.connect(self.plz_changed)
        self.le_city.textChanged.connect(self.city_changed)
        self.btn_save.clicked.connect(self.save_clicked)
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

    def select_logo(self, fix_logo: Optional[str] = None) -> None:
        """!
        @brief Open file dialog to select logo and setup preview
        @param fix_logo : set fix logo file without dialog asking
        """
        if fix_logo:
            logo_path = fix_logo
        else:
            logo_path, _ = QFileDialog.getOpenFileName(parent=self.ui, caption="Logo auswählen",
                                                       directory=self.ui.model.get_last_path(),
                                                       filter=COMPANY_LOGO_TYPES)
        if logo_path:
            pixmap = QPixmap(logo_path)
            self.lbl_logo_preview.setText("")
            self.lbl_logo_preview.setPixmap(pixmap)
            if fix_logo is None:  # select only if changed by user
                self.logo_path = logo_path

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

    def ai_changed(self) -> None:
        """!
        @brief AI changed
        """
        show_model = False
        show_api_key = False
        if self.rb_ai_deactivated.isChecked():
            self.le_ai_model.setPlaceholderText("")
        elif self.rb_ai_chatgpt.isChecked():
            self.le_ai_model.setPlaceholderText(f"Default: {DEFAULT_GPT_MODEL}")
            self.le_ai_model.setText(self.ui.model.c_open_ai.model)
            show_model = True
            show_api_key = True
        elif self.rb_ai_ollama.isChecked():
            self.le_ai_model.setPlaceholderText(f"Default: {EOllamaModel.LLAMA3_1_8B.value}")
            self.le_ai_model.setText(self.ui.model.c_ollama_ai.model)
            show_model = True
        else:
            log.warning("Invalid AI checkbox selected")
        self.le_ai_model.setVisible(show_model)
        self.lbl_ai_model.setVisible(show_model)
        self.le_ai_api_key.setVisible(show_api_key)
        self.lbl_ai_api_key.setVisible(show_api_key)

    def save_clicked(self) -> None:
        """!
        @brief Save button clicked.
        """
        self.set_data()
        if self.company_data is not None:
            add_company(self.ui.model.data_path, self.ui.model.git_add, self.company_data, self.uid)
            self.ui.set_status("Persönliche Daten gespeichert")
            self.close()
        else:
            log.warning("Save company settings clicked without data")

    def set_data(self) -> None:
        """!
        @brief Set data
        """
        company = self.company_data
        company_address = company[COMPANY_ADDRESS_FIELD]
        company_contact = company[COMPANY_CONTACT_FIELD]
        company_payment = company[COMPANY_PAYMENT_FIELD]
        company_booking = company[COMPANY_BOOKING_FIELD]
        company_default = company[COMPANY_DEFAULT_FIELD]
        # company
        company[ECompanyFields.NAME] = self.pte_name.toPlainText()
        company[ECompanyFields.TRADE_NAME] = self.le_trade_name.text()
        company[ECompanyFields.TRADE_ID] = self.le_register_number.text()
        company[ECompanyFields.VAT_ID] = self.le_vat.text()
        company[ECompanyFields.TAX_ID] = self.le_tax_number.text()
        company[ECompanyFields.LEGAL_INFO] = self.pte_law_information.toPlainText()
        company[ECompanyFields.ELECTRONIC_ADDRESS] = self.le_electric_address.text()
        company[ECompanyFields.WEBSITE_TEXT] = self.le_website.text()
        # address
        company_address[ECompanyFields.STREET_1] = self.le_street_1.text()
        company_address[ECompanyFields.STREET_2] = self.le_street_2.text()
        company_address[ECompanyFields.PLZ] = self.le_plz.text()
        company_address[ECompanyFields.CITY] = self.le_city.text()
        company_address[ECompanyFields.COUNTRY] = self.cb_country.currentData()
        # contact
        company_contact[ECompanyFields.FIRST_NAME] = self.le_first_name.text()
        company_contact[ECompanyFields.LAST_NAME] = self.le_last_name.text()
        company_contact[ECompanyFields.MAIL] = self.le_mail.text()
        company_contact[ECompanyFields.PHONE] = self.le_phone.text()
        # payment
        company_payment[ECompanyFields.BANK_NAME] = self.le_bank_name.text()
        company_payment[ECompanyFields.BANK_IBAN] = self.le_iban.text()
        company_payment[ECompanyFields.BANK_BIC] = self.le_bic.text()
        company_payment[ECompanyFields.BANK_OWNER] = self.le_bank_owner.text()
        # booking
        company_booking[ECompanyFields.SMALL_BUSINESS_REGULATION] = self.rb_ust_no.isChecked()
        company_booking[ECompanyFields.PROFIT_CALCULATION_CAPITAL] = self.rb_marge_guv.isChecked()
        company_booking[ECompanyFields.AGREED_COST] = self.rb_tax_soll.isChecked()
        text = self.le_tax_rates.text()
        l_tax_rates = [num for part in text.split() if (num := parse_number(part)) is not None]
        if not l_tax_rates:
            l_tax_rates = DEFAULT_TAX_RATES
        company_booking[ECompanyFields.TAX_RATES] = l_tax_rates
        # default
        company_default[ECompanyFields.QUARTERLY_SALES_TAX] = self.rb_ustva_quaterly.isChecked()
        company_default[ECompanyFields.PAYED] = self.cb_payed.isChecked()
        company_default[ECompanyFields.BAR_PAYED] = self.cb_bar_payed.isChecked()
        company_default[ECompanyFields.INCOME_GROUP] = self.le_default_group_income.text()
        company_default[ECompanyFields.EXPENDITURE_GROUP] = self.le_default_group_expenditure.text()
        company_default[ECompanyFields.GROUPS] = self.pte_group_list.toPlainText().splitlines()
        company_default[ECompanyFields.PAYMENT_DAYS] = self.sb_payment_days.value()
        company_default[ECompanyFields.MAIL_SUBJECT] = self.le_mail_subtract.text()
        company_default[ECompanyFields.MAIL_TEXT] = self.pte_mail_template.toPlainText()
        # AI settings
        custom_model = self.le_ai_model.text()
        if self.rb_ai_deactivated.isChecked():
            ai_type = EAiType.DEACTIVATED
        elif self.rb_ai_chatgpt.isChecked():
            ai_type = EAiType.OPEN_AI
            self.ui.model.c_open_ai.set_model(custom_model)
        elif self.rb_ai_ollama.isChecked():
            ai_type = EAiType.OLLAMA
            self.ui.model.c_ollama_ai.set_model(custom_model)
        else:
            ai_type = EAiType.DEACTIVATED
            log.warning("Invalid AI type: %s", self.ui.model.ai_type)
        self.ui.model.ai_type = ai_type
        write_ai_type(ai_type)
        write_api_key(self.le_ai_api_key.text())
        # logo
        if self.logo_path:
            logo_path = os.path.join(self.ui.model.data_path, LOGO_BRIEF_PATH)
            shutil.copyfile(self.logo_path, logo_path)
