"""!
********************************************************************************
@file   tab_contacts.py
@brief  Tab for managing contacts.
********************************************************************************
"""

import logging
from typing import TYPE_CHECKING
import re

from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QDesktopServices

from Source.version import __title__
from Source.Util.app_data import ICON_CONTACT_LIGHT, ICON_CONTACT_DARK, S_KEY_CONTACTS_COLUMN
from Source.Controller.table_filter import TableFilter, CellData
from Source.Controller.dialog_contact import ContactDialog, EMAIL_REGEX
from Source.Model.contacts import read_contacts, EContactFields, add_contact, remove_contact, \
    CONTACT_CONTACT_FIELD, CONTACT_ADDRESS_FIELD
from Source.Model.company import ECompanyFields, COMPANY_ADDRESS_FIELD, COMPANY_CONTACT_FIELD, \
    COMPANY_DEFAULT_FIELD, COMPANY_PAYMENT_FIELD
if TYPE_CHECKING:
    from Source.Controller.main_window import MainWindow

log = logging.getLogger(__title__)

EMAIL = "E-Mail"
L_ROW_DESCRIPTION = ["Handelspartner", "Kontaktperson", "Straße", "PLZ", "Ort", EMAIL, "ID"]
I_EMAIL_IDX = L_ROW_DESCRIPTION.index(EMAIL)


class TabContacts:
    """!
    @brief Controller for the Contacts tab.
    @param ui : main window
    @param tab_idx : Index of the tab in the tab widget.
    """

    def __init__(self, ui: "MainWindow", tab_idx: int) -> None:
        self.ui = ui
        s_title = "Kontakte"
        ui.tabWidget.setTabText(tab_idx, s_title)
        self.ui_table = TableFilter(ui, ui.tabWidget, tab_idx, s_title,
                                    btn_1_name="Kontakt anlegen", btn_1_cb=self.new_contact,
                                    table_double_click_fnc=self.on_item_double_clicked, l_table_header=L_ROW_DESCRIPTION,
                                    sort_idx=0, inverse_sort=True, row_fill_idx=len(L_ROW_DESCRIPTION) - 3,
                                    delete_fnc=remove_contact, update_table_func=self.set_table_data,
                                    column_setting_key=S_KEY_CONTACTS_COLUMN,
                                    b_create_invoice=True)
        self.l_data: list[dict[EContactFields | str, str]] = []
        self.ui_table.lbl_drag.setText("")  # contacts can not drop file

    def set_table_data(self, update: bool = False, rename: bool = False, update_dashboard: bool = True) -> None:
        """!
        @brief Populates the contacts table with data.
        @param update : update status of JSON file
        @param rename : rename status of file name
        @param update_dashboard : update dashboard
        """
        self.l_data = read_contacts(self.ui.model.data_path)
        icon = ICON_CONTACT_LIGHT if self.ui.model.c_monitor.is_light_theme() else ICON_CONTACT_DARK
        l_data = []
        for contact in self.l_data:
            contact_contact = contact[CONTACT_CONTACT_FIELD]
            contact_address = contact[CONTACT_ADDRESS_FIELD]
            if update:
                add_contact(self.ui.model.data_path, self.ui.model.git_add, contact, contact[EContactFields.ID], rename=rename)
            l_entry = []
            l_entry.append(CellData(text=contact[EContactFields.NAME], icon=icon))
            person = " ".join(filter(None, [contact_contact[EContactFields.FIRST_NAME], contact_contact[EContactFields.LAST_NAME]]))
            l_entry.append(CellData(text=person))
            l_entry.append(CellData(text=contact_address[EContactFields.STREET_1]))
            l_entry.append(CellData(text=contact_address[EContactFields.PLZ], right_align=True))
            l_entry.append(CellData(text=contact_address[EContactFields.CITY]))
            l_entry.append(CellData(text=contact_contact[EContactFields.MAIL]))
            l_entry.append(CellData(text=contact[EContactFields.ID]))
            l_data.append(l_entry)
        self.ui_table.update_table(l_data)
        self.ui_table.table.setColumnHidden(len(L_ROW_DESCRIPTION) - 1, True)
        if update_dashboard:
            self.ui.tab_dashboard.update_dashboard_data()

    def get_mail_template(self, text: str) -> str:
        """!
        @brief Replaces placeholder fields in the mail template with company data.
        @param text : text
        @return mail text
        """
        mail_template = text

        company = self.ui.tab_settings.company_data
        company_address = company[COMPANY_ADDRESS_FIELD]
        company_contact = company[COMPANY_CONTACT_FIELD]
        company_payment = company[COMPANY_PAYMENT_FIELD]

        d_text_blocks = {
            "name": company[ECompanyFields.NAME],
            "tradeName": company[ECompanyFields.TRADE_NAME],
            "tradeId": company[ECompanyFields.TRADE_ID],
            "vatId": company[ECompanyFields.VAT_ID],
            "taxId": company[ECompanyFields.TAX_ID],
            "legalInfo": company[ECompanyFields.LEGAL_INFO],
            "electronicAddress": company[ECompanyFields.ELECTRONIC_ADDRESS],
            "websiteText": company[ECompanyFields.WEBSITE_TEXT],
            "line1": company_address[ECompanyFields.STREET_1],
            "line2": company_address[ECompanyFields.STREET_2],
            "postCode": company_address[ECompanyFields.PLZ],
            "city": company_address[ECompanyFields.CITY],
            "countryCode": company_address[ECompanyFields.COUNTRY],
            "firstName": company_contact[ECompanyFields.FIRST_NAME],
            "lastName": company_contact[ECompanyFields.LAST_NAME],
            "email": company_contact[ECompanyFields.MAIL],
            "phone": company_contact[ECompanyFields.PHONE],
            "bankName": company_payment[ECompanyFields.BANK_NAME],
            "iban": company_payment[ECompanyFields.BANK_IBAN],
            "bic": company_payment[ECompanyFields.BANK_BIC],
            "accountName": company_payment[ECompanyFields.BANK_OWNER]
        }
        for text_block, text_value in d_text_blocks.items():
            mail_template = mail_template.replace(f"[%{text_block}%]", text_value)  # format: [%TEXT_BLOCK%]
        return mail_template

    def on_item_double_clicked(self, row: int, col: int, value: str) -> None:
        """!
        @brief Handles double-click events on a table entry.
        @param row : clicked row index
        @param col : clicked column index
        @param value : value of clicked cell
        """
        if col == I_EMAIL_IDX:
            if re.match(EMAIL_REGEX, value) is not None:
                subject = self.get_mail_template(self.ui.tab_settings.company_data[COMPANY_DEFAULT_FIELD][ECompanyFields.MAIL_SUBJECT])
                body = self.get_mail_template(self.ui.tab_settings.company_data[COMPANY_DEFAULT_FIELD][ECompanyFields.MAIL_TEXT])
                company = self.ui.tab_settings.company_data
                company_contact = company[COMPANY_CONTACT_FIELD]
                sender_mail = company_contact[ECompanyFields.MAIL]
                url = QUrl(f"mailto:{value}?from={sender_mail}&subject={subject}&body={body}")
                QDesktopServices.openUrl(url)
        else:
            model = self.ui_table.table.model()
            uid_index = model.index(row, len(L_ROW_DESCRIPTION) - 1)
            uid = model.data(uid_index, Qt.ItemDataRole.DisplayRole)

            if uid:
                found_contact = next((contact for contact in self.l_data if contact[EContactFields.ID] == uid), None)

                if found_contact is not None:
                    ContactDialog(self.ui, found_contact, uid)
                    self.set_table_data()
                else:
                    self.ui.set_status("Contact UID not found", True)  # state not possible

    def new_contact(self) -> None:
        """!
        @brief Opens the dialog to create a new contact.
        """
        ContactDialog(self.ui)
        self.set_table_data()
