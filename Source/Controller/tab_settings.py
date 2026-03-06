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
from Source.Util.app_data import EAiType, ICON_CIRCLE_WHITE, ICON_CIRCLE_GREEN, ICON_CIRCLE_RED, ICON_CIRCLE_ORANGE
from Source.Model.data_handler import fill_data, get_git_repo
from Source.Model.company import LOGO_BRIEF_PATH, read_company, ECompanyFields, COMPANY_TEMPLATE, \
    COMPANY_ADDRESS_FIELD, COMPANY_CONTACT_FIELD, COMPANY_PAYMENT_FIELD
from Source.Views.tabs.tab_settings_ui import Ui_Settings
from Source.Controller.dialog_company import CompanyDialog
if TYPE_CHECKING:
    from Source.Controller.main_window import MainWindow

log = logging.getLogger(__title__)

HEIGHT_OFFSET = 15
HEIGHT_PER_LINE = 20


class TabSettings:
    """!
    @brief Controller for the Settings tab.
    @param ui : main window
    @param tab_idx : Index of this tab in the tab widget
    """

    def __init__(self, ui: "MainWindow", tab_idx: int) -> None:
        self.ui = ui
        title = "Einstellungen"
        tab = ui.tabWidget.widget(tab_idx)
        self.ui_settings = Ui_Settings()
        self.ui_settings.setupUi(tab)
        self.ui_settings.lbl_title.setText(title)
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
        ui.tabWidget.setTabText(tab_idx, title)

        company_data = read_company(self.ui.model.data_path)
        if company_data is None:
            CompanyDialog(self.ui)
            company_data = read_company(self.ui.model.data_path)
            if company_data is None:
                self.company_data = fill_data(COMPANY_TEMPLATE, {})
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

        # logo
        self.ui_settings.company_logo.setPixmap(QPixmap(os.path.join(self.ui.model.data_path, LOGO_BRIEF_PATH)))
        # company data
        lines = []
        if company[ECompanyFields.NAME]:
            lines.append(company[ECompanyFields.NAME])
        else:
            lines.append("Unternehmen")
        if company[ECompanyFields.TRADE_NAME]:
            lines.append(f"Handelsname: {company[ECompanyFields.TRADE_NAME]}")
        if company[ECompanyFields.TRADE_ID]:
            lines.append(f"Registernummer: {company[ECompanyFields.TRADE_ID]}")
        if company[ECompanyFields.VAT_ID]:
            lines.append(f"Umsatzsteuer-ID: {company[ECompanyFields.VAT_ID]}")
        if company[ECompanyFields.TAX_ID]:
            lines.append(f"Steuernummer: {company[ECompanyFields.TAX_ID]}")
        if company[ECompanyFields.LEGAL_INFO]:
            lines.append(f"Rechtliche Informationen: {company[ECompanyFields.LEGAL_INFO]}")
        if company[ECompanyFields.ELECTRONIC_ADDRESS]:
            lines.append(f"Elektronische Adresse: {company[ECompanyFields.ELECTRONIC_ADDRESS]}")
        if lines:
            self.ui_settings.pte_company.setPlainText("\n".join(lines))
            self.ui_settings.pte_company.setFixedHeight((HEIGHT_PER_LINE * len(lines)) + HEIGHT_OFFSET)
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
        lines = []
        if company_address[ECompanyFields.STREET_1]:
            lines.append(company_address[ECompanyFields.STREET_1])
        if company_address[ECompanyFields.STREET_2]:
            lines.append(company_address[ECompanyFields.STREET_2])
        if company_address[ECompanyFields.PLZ] or company_address[ECompanyFields.CITY]:
            parts = []
            if company_address[ECompanyFields.COUNTRY] and company_address[ECompanyFields.COUNTRY] != "DE":
                parts.append(f"{company_address[ECompanyFields.COUNTRY]} -")
            if company_address[ECompanyFields.PLZ]:
                parts.append(company_address[ECompanyFields.PLZ])
            if company_address[ECompanyFields.CITY]:
                parts.append(company_address[ECompanyFields.CITY])
            if parts:
                lines.append(" ".join(parts))
        if lines:
            self.ui_settings.pte_address.setPlainText("\n".join(lines))
            self.ui_settings.pte_address.setFixedHeight((HEIGHT_PER_LINE * len(lines)) + HEIGHT_OFFSET)
            self.ui_settings.pte_address.show()
            self.ui_settings.lbl_address.show()
        else:
            self.ui_settings.pte_address.hide()
            self.ui_settings.lbl_address.hide()
        # contact
        lines = []
        if company_contact[ECompanyFields.FIRST_NAME] or company_contact[ECompanyFields.LAST_NAME]:
            parts = []
            if company_contact[ECompanyFields.FIRST_NAME]:
                parts.append(company_contact[ECompanyFields.FIRST_NAME])
            if company_contact[ECompanyFields.LAST_NAME]:
                parts.append(company_contact[ECompanyFields.LAST_NAME])
            if parts:
                lines.append(" ".join(parts))
        if company_contact[ECompanyFields.MAIL]:
            lines.append(f"E-Mail: {company_contact[ECompanyFields.MAIL]}")
        if company_contact[ECompanyFields.PHONE]:
            lines.append(f"Telefon: {company_contact[ECompanyFields.PHONE]}")
        if lines:
            self.ui_settings.pte_contact.setPlainText("\n".join(lines))
            self.ui_settings.pte_contact.setFixedHeight((HEIGHT_PER_LINE * len(lines)) + HEIGHT_OFFSET)
            self.ui_settings.pte_contact.show()
            self.ui_settings.lbl_contact.show()
        else:
            self.ui_settings.pte_contact.hide()
            self.ui_settings.lbl_contact.hide()
        # payment
        lines = []
        if company_payment[ECompanyFields.BANK_NAME]:
            lines.append(company_payment[ECompanyFields.BANK_NAME])
        if company_payment[ECompanyFields.BANK_IBAN]:
            lines.append(f"IBAN: {company_payment[ECompanyFields.BANK_IBAN]}")
        if company_payment[ECompanyFields.BANK_BIC]:
            lines.append(f"BIC: {company_payment[ECompanyFields.BANK_BIC]}")
        if company_payment[ECompanyFields.BANK_OWNER]:
            lines.append(f"Kto. Inh.: {company_payment[ECompanyFields.BANK_OWNER]}")
        if lines:
            self.ui_settings.pte_payment.setPlainText("\n".join(lines))
            self.ui_settings.pte_payment.setFixedHeight((HEIGHT_PER_LINE * len(lines)) + HEIGHT_OFFSET)
            self.ui_settings.pte_payment.show()
            self.ui_settings.lbl_payment.show()
        else:
            self.ui_settings.pte_payment.hide()
            self.ui_settings.lbl_payment.hide()
        # git status
        if get_git_repo():
            git_status = "Aktiv"
            status_icon = ICON_CIRCLE_GREEN
        else:
            git_status = "Inaktiv"
            status_icon = ICON_CIRCLE_RED
        text = f"Git Versionierung: {git_status}"
        self.ui_settings.lbl_revision.setText(f"<img src='{status_icon}' width='14' height='14' style='vertical-align: middle; padding-right: 5px;'> {text}")
        # ai status
        ai_providers = {
            EAiType.OPEN_AI: self.ui.model.open_ai,
            EAiType.GEMINI: self.ui.model.gemini_ai,
            EAiType.MISTRAL: self.ui.model.mistral_ai,
            EAiType.OLLAMA: self.ui.model.ollama_ai,
        }
        ai_type = self.ui.model.ai_type
        ai_provider = ai_providers.get(ai_type)
        status_icon = ICON_CIRCLE_WHITE
        ai_status = ""
        ai_model = ""
        if ai_type == EAiType.DEACTIVATED:
            ai_type_text = "Deaktiviert"
        elif ai_provider:
            ai_type_text = ai_type.value
            ai_model = ai_provider.model
            if ai_provider.init_check:
                ai_status = "Aktiv" if ai_provider.ready else "Inaktiv"
                status_icon = ICON_CIRCLE_GREEN if ai_provider.ready else ICON_CIRCLE_RED
            else:
                ai_status = "Nicht initialisiert"
                status_icon = ICON_CIRCLE_ORANGE
        else:
            log.warning("Invalid AI type")
            ai_type_text = "Unbekannt"
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
