"""!
********************************************************************************
@file   tab_settings.py
@brief  Manage company information, booking settings and AI status
********************************************************************************
"""

import os
import logging
from typing import TYPE_CHECKING

from PyQt6.QtGui import QPixmap, QFont

from Source.version import __title__
from Source.Util.app_data import REL_PATH, EAiType, ICON_CIRCLE_WHITE, ICON_CIRCLE_GREEN, ICON_CIRCLE_RED, ICON_CIRCLE_ORANGE
from Source.Model.data_handler import fill_data, get_git_repo
from Source.Model.company import LOGO_BRIEF_PATH, read_company, ECompanyFields, D_COMPANY_TEMPLATE, \
    COMPANY_ADDRESS_FIELD, COMPANY_CONTACT_FIELD, COMPANY_PAYMENT_FIELD
from Source.Views.tabs.tab_settings_ui import Ui_Settings
from Source.Controller.dialog_company import CompanyDialog
if TYPE_CHECKING:
    from Source.Controller.main_window import MainWindow

log = logging.getLogger(__title__)


class TabSettings:
    """!
    @brief Controller for the Settings tab
    @param ui : main window
    @param tab_idx : Index of this tab in the tab widget
    """

    def __init__(self, ui: "MainWindow", tab_idx: int) -> None:
        self.ui = ui
        s_title = "Einstellungen"
        tab = ui.tabWidget.widget(tab_idx)
        self.ui_settings = Ui_Settings()
        self.ui_settings.setupUi(tab)
        self.ui_settings.lbl_title.setText(s_title)
        self.ui_settings.pte_company.setFont(QFont("Consolas", 12))
        self.ui_settings.lbl_website.setFont(QFont("Consolas", 12))
        self.ui_settings.pte_address.setFont(QFont("Consolas", 12))
        self.ui_settings.pte_contact.setFont(QFont("Consolas", 12))
        self.ui_settings.pte_payment.setFont(QFont("Consolas", 12))
        self.ui_settings.lbl_revision.setFont(QFont("Consolas", 12))
        self.ui_settings.lbl_ai.setFont(QFont("Consolas", 12))
        self.ui_settings.pte_company.setReadOnly(True)
        self.ui_settings.pte_address.setReadOnly(True)
        self.ui_settings.pte_contact.setReadOnly(True)
        self.ui_settings.pte_payment.setReadOnly(True)
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
        self.ui_settings.btn_change_company_data.clicked.connect(self.change_company_data)
        self.update_company_data()

    def update_company_data(self) -> None:
        """!
        @brief Updates all company-related UI elements, including company info, address,
               contact, payment, Git status, and AI assistant status.
        """
        company = self.company_data
        company_address = company[COMPANY_ADDRESS_FIELD]
        company_contact = company[COMPANY_CONTACT_FIELD]
        company_payment = company[COMPANY_PAYMENT_FIELD]

        HEIGHT_OFFSET = 15
        HEIGHT_PER_LINE = 20
        # logo
        self.ui_settings.company_logo.setPixmap(QPixmap(os.path.join(self.ui.model.data_path, LOGO_BRIEF_PATH)))
        # company data
        l_data = []
        if company[ECompanyFields.NAME]:
            l_data.append(company[ECompanyFields.NAME])
        else:
            l_data.append("Unternehmen")
        if company[ECompanyFields.TRADE_NAME]:
            l_data.append(f"Handelsname: {company[ECompanyFields.TRADE_NAME]}")
        if company[ECompanyFields.TRADE_ID]:
            l_data.append(f"Registernummer: {company[ECompanyFields.TRADE_ID]}")
        if company[ECompanyFields.VAT_ID]:
            l_data.append(f"Umsatzsteuer-ID: {company[ECompanyFields.VAT_ID]}")
        if company[ECompanyFields.TAX_ID]:
            l_data.append(f"Steuernummer: {company[ECompanyFields.TAX_ID]}")
        if company[ECompanyFields.LEGAL_INFO]:
            l_data.append(f"Rechtliche Informationen: {company[ECompanyFields.LEGAL_INFO]}")
        if company[ECompanyFields.ELECTRONIC_ADDRESS]:
            l_data.append(f"Elektronische Adresse: {company[ECompanyFields.ELECTRONIC_ADDRESS]}")
        if l_data:
            self.ui_settings.pte_company.setPlainText("\n".join(l_data))
            self.ui_settings.pte_company.setFixedHeight((HEIGHT_PER_LINE * len(l_data)) + HEIGHT_OFFSET)
            self.ui_settings.pte_company.show()
        else:
            self.ui_settings.pte_company.hide()
        # website
        if company[ECompanyFields.WEBSITE_TEXT]:
            website_link = f"Webseite: <a href=\"{company[ECompanyFields.WEBSITE_TEXT]}\">{company[ECompanyFields.WEBSITE_TEXT]}</a>"
            self.ui_settings.lbl_website.setText(website_link)
            self.ui_settings.lbl_website.setOpenExternalLinks(True)
            self.ui_settings.lbl_website.show()
        else:
            self.ui_settings.lbl_website.hide()
        # address
        l_data = []
        if company_address[ECompanyFields.STREET_1]:
            l_data.append(company_address[ECompanyFields.STREET_1])
        if company_address[ECompanyFields.STREET_2]:
            l_data.append(company_address[ECompanyFields.STREET_2])
        if company_address[ECompanyFields.PLZ] or company_address[ECompanyFields.CITY]:
            l_line_data = []
            if company_address[ECompanyFields.COUNTRY] and company_address[ECompanyFields.COUNTRY] != "DE":
                l_line_data.append(f"{company_address[ECompanyFields.COUNTRY]} -")
            if company_address[ECompanyFields.PLZ]:
                l_line_data.append(company_address[ECompanyFields.PLZ])
            if company_address[ECompanyFields.CITY]:
                l_line_data.append(company_address[ECompanyFields.CITY])
            if l_line_data:
                l_data.append(" ".join(l_line_data))
        if l_data:
            self.ui_settings.pte_address.setPlainText("\n".join(l_data))
            self.ui_settings.pte_address.setFixedHeight((HEIGHT_PER_LINE * len(l_data)) + HEIGHT_OFFSET)
            self.ui_settings.pte_address.show()
            self.ui_settings.lbl_address.show()
        else:
            self.ui_settings.pte_address.hide()
            self.ui_settings.lbl_address.hide()
        # contact
        l_data = []
        if company_contact[ECompanyFields.FIRST_NAME] or company_contact[ECompanyFields.LAST_NAME]:
            l_line_data = []
            if company_contact[ECompanyFields.FIRST_NAME]:
                l_line_data.append(company_contact[ECompanyFields.FIRST_NAME])
            if company_contact[ECompanyFields.LAST_NAME]:
                l_line_data.append(company_contact[ECompanyFields.LAST_NAME])
            if l_line_data:
                l_data.append(" ".join(l_line_data))
        if company_contact[ECompanyFields.MAIL]:
            l_data.append(f"E-Mail: {company_contact[ECompanyFields.MAIL]}")
        if company_contact[ECompanyFields.PHONE]:
            l_data.append(f"Telefon: {company_contact[ECompanyFields.PHONE]}")
        if l_data:
            self.ui_settings.pte_contact.setPlainText("\n".join(l_data))
            self.ui_settings.pte_contact.setFixedHeight((HEIGHT_PER_LINE * len(l_data)) + HEIGHT_OFFSET)
            self.ui_settings.pte_contact.show()
            self.ui_settings.lbl_contact.show()
        else:
            self.ui_settings.pte_contact.hide()
            self.ui_settings.lbl_contact.hide()
        # payment
        l_data = []
        if company_payment[ECompanyFields.BANK_NAME]:
            l_data.append(company_payment[ECompanyFields.BANK_NAME])
        if company_payment[ECompanyFields.BANK_IBAN]:
            l_data.append(f"IBAN: {company_payment[ECompanyFields.BANK_IBAN]}")
        if company_payment[ECompanyFields.BANK_BIC]:
            l_data.append(f"BIC: {company_payment[ECompanyFields.BANK_BIC]}")
        if company_payment[ECompanyFields.BANK_OWNER]:
            l_data.append(f"Kto. Inh.: {company_payment[ECompanyFields.BANK_OWNER]}")
        if l_data:
            self.ui_settings.pte_payment.setPlainText("\n".join(l_data))
            self.ui_settings.pte_payment.setFixedHeight((HEIGHT_PER_LINE * len(l_data)) + HEIGHT_OFFSET)
            self.ui_settings.pte_payment.show()
            self.ui_settings.lbl_payment.show()
        else:
            self.ui_settings.pte_payment.hide()
            self.ui_settings.lbl_payment.hide()
        # git status
        if get_git_repo(os.path.abspath(REL_PATH)):
            git_status = "Aktiv"
            status_icon = ICON_CIRCLE_GREEN
        else:
            git_status = "Inaktiv"
            status_icon = ICON_CIRCLE_RED
        text = f"Git Versionierung: {git_status}"
        self.ui_settings.lbl_revision.setText(f"<img src='{status_icon}' width='14' height='14' style='vertical-align: middle; padding-right: 5px;'> {text}")
        # ai status
        status_icon = ICON_CIRCLE_WHITE
        ai_status = "Unbekannt"
        ai_model = ""
        match self.ui.model.ai_type:
            case EAiType.OPEN_AI:
                ai_type_text = EAiType.OPEN_AI.value
                ai_model = self.ui.model.c_open_ai.model
                if self.ui.model.c_open_ai.init_check:
                    ai_status = "Aktiv" if self.ui.model.c_open_ai.b_ready else "Inaktiv"
                    status_icon = ICON_CIRCLE_GREEN if self.ui.model.c_open_ai.b_ready else ICON_CIRCLE_RED
                else:
                    ai_status = "Nicht initialisiert"
                    status_icon = ICON_CIRCLE_ORANGE
            case EAiType.MISTRAL:
                ai_type_text = EAiType.MISTRAL.value
                ai_model = self.ui.model.c_mistral_ai.model
                if self.ui.model.c_mistral_ai.init_check:
                    ai_status = "Aktiv" if self.ui.model.c_mistral_ai.b_ready else "Inaktiv"
                    status_icon = ICON_CIRCLE_GREEN if self.ui.model.c_mistral_ai.b_ready else ICON_CIRCLE_RED
                else:
                    ai_status = "Nicht initialisiert"
                    status_icon = ICON_CIRCLE_ORANGE
            case EAiType.OLLAMA:
                ai_type_text = EAiType.OLLAMA.value
                ai_model = self.ui.model.c_ollama_ai.model
                if self.ui.model.c_ollama_ai.init_check:
                    ai_status = "Aktiv" if self.ui.model.c_ollama_ai.b_ready else "Inaktiv"
                    status_icon = ICON_CIRCLE_GREEN if self.ui.model.c_ollama_ai.b_ready else ICON_CIRCLE_RED
                else:
                    ai_status = "Nicht initialisiert"
                    status_icon = ICON_CIRCLE_ORANGE
            case EAiType.DEACTIVATED:
                ai_type_text = "Deaktiviert"
                ai_status = ""
                status_icon = ICON_CIRCLE_WHITE
            case _:
                log.warning("Invalid AI type")
        text = f"KI-Assistent: {ai_type_text}"
        if ai_model:
            text += f" ({ai_model})"
        if ai_status:
            text += f" - {ai_status}"
        self.ui_settings.lbl_ai.setText(f"<img src='{status_icon}' width='14' height='14' style='vertical-align: middle; padding-right: 5px;'> {text}")

    def change_company_data(self) -> None:
        """!
        @brief Opens a dialog to edit company information, saves changes, and refreshes the UI and dependent buttons.
        """
        CompanyDialog(self.ui, self.company_data, uid=self.company_data[ECompanyFields.ID])
        company_data = read_company(self.ui.model.data_path)
        if company_data is not None:
            self.company_data = company_data
        self.update_company_data()
        self.ui.tab_export.update_eur_btn()
