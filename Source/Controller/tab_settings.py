"""!
********************************************************************************
@file   tab_settings.py
@brief  Settings Tab
********************************************************************************
"""

import os
import logging
from typing import TYPE_CHECKING

from PyQt6.QtGui import QPixmap, QFont

from Source.version import __title__
from Source.Util.app_data import REL_PATH, EAiType
from Source.Model.data_handler import fill_data, get_git_repo
from Source.Model.company import LOGO_BRIEF_PATH, read_company, ECompanyFields, D_COMPANY_TEMPLATE, \
    COMPANY_ADDRESS_FIELD, COMPANY_CONTACT_FIELD, COMPANY_PAYMENT_FIELD, COMPANY_BOOKING_FIELD, COMPANY_DEFAULT_FIELD
from Source.Model.export import EReportType
from Source.Views.tabs.tab_settings_ui import Ui_Settings
from Source.Controller.dialog_company import CompanyDialog
if TYPE_CHECKING:
    from Source.Controller.main_window import MainWindow

log = logging.getLogger(__title__)


class TabSettings:
    """!
    @brief Settings dialog tab.
    @param ui : main window
    @param tab_idx : tab index
    """

    def __init__(self, ui: "MainWindow", tab_idx: int) -> None:
        self.ui = ui
        s_title = "Einstellungen"
        tab = ui.tabWidget.widget(tab_idx)
        self.ui_settings = Ui_Settings()
        self.ui_settings.setupUi(tab)
        self.ui_settings.lbl_title.setText(s_title)
        self.ui_settings.company_data.setFont(QFont("Consolas", 14))
        ui.tabWidget.setTabText(tab_idx, s_title)

        company_data = read_company(self.ui.model.data_path)
        if company_data is None:
            CompanyDialog(self.ui)
            company_data = read_company(self.ui.model.data_path)
            if company_data is None:
                self.company_data = fill_data(D_COMPANY_TEMPLATE, {})
            else:
                self.company_data = company_data
        else:
            self.company_data = company_data
        self.ui_settings.company_data.setReadOnly(True)
        self.ui_settings.btn_change_company_data.clicked.connect(self.change_company_data)
        self.update_company_data()

    def update_company_data(self) -> None:
        """!
        @brief Update company data.
        """
        company = self.company_data
        company_address = company[COMPANY_ADDRESS_FIELD]
        company_contact = company[COMPANY_CONTACT_FIELD]
        company_payment = company[COMPANY_PAYMENT_FIELD]
        company_booking = company[COMPANY_BOOKING_FIELD]
        company_default = company[COMPANY_DEFAULT_FIELD]
        small_business_regulation = "Ja, keine Umsatzsteuer ausweisen" if company_booking[ECompanyFields.SMALL_BUSINESS_REGULATION] else "Nein, Umsatzsteuer ausweisen"
        ust_setting = "Vereinbartes Entgelt" if company_booking[ECompanyFields.AGREED_COST] else "Vereinnahmtes Entgelt"
        ust_time = "Vierteljährlich" if company_default[ECompanyFields.QUARTERLY_SALES_TAX] else "Monatlich"
        profit_calculation = EReportType.GUV.value if company_booking[ECompanyFields.PROFIT_CALCULATION_CAPITAL] else EReportType.EUR.value

        default_payed = "x" if company_default[ECompanyFields.PAYED] else " "
        default_bar = "x" if company_default[ECompanyFields.BAR_PAYED] else " "

        git_status = "Aktiv" if get_git_repo(os.path.abspath(REL_PATH)) else "Inaktiv"

        self.ui_settings.company_logo.setPixmap(QPixmap(os.path.join(self.ui.model.data_path, LOGO_BRIEF_PATH)))
        l_data = [company[ECompanyFields.NAME],
                  company_address[ECompanyFields.STREET_1],
                  f"{company_address[ECompanyFields.PLZ]} {company_address[ECompanyFields.CITY]}",
                  f"StNr.: {company[ECompanyFields.TAX_ID]}",
                  f"Ust-IdNr.: {company[ECompanyFields.VAT_ID]}",
                  "",
                  f"Mobil: {company_contact[ECompanyFields.PHONE]}",
                  f"E-Mail: {company_contact[ECompanyFields.MAIL]}",
                  "",
                  f"{company_payment[ECompanyFields.BANK_NAME]}",
                  f"IBAN: {company_payment[ECompanyFields.BANK_IBAN]}",
                  f"BIC: {company_payment[ECompanyFields.BANK_BIC]}",
                  f"Kto. Inh.: {company_payment[ECompanyFields.BANK_OWNER]}",
                  "",
                  f"Inanspruchnahme Kleinunternehmerregelung: {small_business_regulation}",
                  f"Umsatzsteuer-Abrechnung: {ust_setting}",
                  f"Umsatzsteuer-Voranmeldung Fälligkeit: {ust_time}",
                  f"Gewinnermittlung: {profit_calculation}",
                  "",
                  f"Standardwert Bezahlt: [{default_payed}]",
                  f"Standardwert Bar: [{default_bar}]",
                  f"Standardwert Gruppe Einnahmen: {company_default[ECompanyFields.INCOME_GROUP]}",
                  f"Standardwert Gruppe Ausgaben: {company_default[ECompanyFields.EXPENDITURE_GROUP]}",
                  f"Hinterlegte Gruppen: {company_default[ECompanyFields.GROUPS]}",
                  f"Zahlungsziel: {company_default[ECompanyFields.PAYMENT_DAYS]} Tage",
                  "",
                  f"Revisionierung: {git_status}"]  # GitStatus entfernen oder wo anders hin
        ai_status = "Unbekannt"
        ai_model = ""
        match self.ui.model.ai_type:
            case EAiType.OPEN_AI:
                if self.ui.model.c_open_ai.init_check:
                    ai_status = "Aktiv" if self.ui.model.c_open_ai.b_ready else "Inaktiv"
                    if self.ui.model.c_open_ai.b_ready:
                        ai_model = self.ui.model.c_open_ai.model
                else:
                    ai_status = "Nicht initialisiert"
            case EAiType.OLLAMA:
                if self.ui.model.c_ollama_ai.init_check:
                    ai_status = "Aktiv" if self.ui.model.c_ollama_ai.b_ready else "Inaktiv"
                    if self.ui.model.c_ollama_ai.b_ready:
                        ai_model = self.ui.model.c_ollama_ai.model
                else:
                    ai_status = "Nicht initialisiert"
            case EAiType.DEACTIVATED:
                ai_status = "Deaktiviert"
            case _:
                log.warning("Invalid AI type")
        ai_text = f"KI-Assistent: {ai_status}"
        if ai_model:
            ai_text += f" ({ai_model})"
        l_data.append(ai_text)
        self.ui_settings.company_data.setText("\n".join(l_data))

    def change_company_data(self) -> None:
        """!
        @brief Update company data.
        """
        CompanyDialog(self.ui, self.company_data, uid=self.company_data[ECompanyFields.ID])
        company_data = read_company(self.ui.model.data_path)
        if company_data is not None:
            self.company_data = company_data
        self.update_company_data()
        self.ui.tab_export.update_eur_btn()
