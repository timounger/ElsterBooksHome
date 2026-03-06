"""!
********************************************************************************
@file   tab_contacts.py
@brief Tab for managing contacts.
********************************************************************************
"""

import logging
from typing import Any, TYPE_CHECKING
import re

from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QDesktopServices

from Source.version import __title__
from Source.Util.app_data import ICON_CONTACT_LIGHT, ICON_CONTACT_DARK, KEY_CONTACTS_COLUMN
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
ROW_DESCRIPTION = ["Handelspartner", "Kontaktperson", "Straße", "PLZ", "Ort", EMAIL, "ID"]
EMAIL_IDX = ROW_DESCRIPTION.index(EMAIL)


class TabContacts:
    """!
    @brief Controller for the Contacts tab.
    @param ui : main window
    @param tab_idx : Index of the tab in the tab widget.
    """

    def __init__(self, ui: "MainWindow", tab_idx: int) -> None:
        self.ui = ui
        title = "Kontakte"
        ui.tabWidget.setTabText(tab_idx, title)
        self.ui_table = TableFilter(ui, ui.tabWidget, tab_idx, title,
                                    btn_1_name="Kontakt anlegen", btn_1_cb=self.new_contact,
                                    table_double_click_fnc=self.on_item_double_clicked, table_header=ROW_DESCRIPTION,
                                    sort_idx=0, inverse_sort=True, row_fill_idx=len(ROW_DESCRIPTION) - 3,
                                    delete_fnc=remove_contact, update_table_func=self.set_table_data,
                                    column_setting_key=KEY_CONTACTS_COLUMN,
                                    create_invoice=True)
        self.contacts: list[dict[EContactFields | str, Any]] = []
        self.ui_table.lbl_drag.setText("")  # contacts can not drop file

    def set_table_data(self, update: bool = False, rename: bool = False, update_dashboard: bool = True) -> None:
        """!
        @brief Populates the contacts table with data.
        @param update : update status of JSON file
        @param rename : rename status of file name
        @param update_dashboard : update dashboard
        """
        self.contacts = read_contacts(self.ui.model.data_path)
        icon = ICON_CONTACT_LIGHT if self.ui.model.monitor.is_light_theme() else ICON_CONTACT_DARK
        rows = []
        for contact in self.contacts:
            contact_contact = contact[CONTACT_CONTACT_FIELD]
            contact_address = contact[CONTACT_ADDRESS_FIELD]
            if update:
                add_contact(self.ui.model.data_path, self.ui.model.git_add, contact, contact[EContactFields.ID], rename=rename)
            person = " ".join(filter(None, [contact_contact[EContactFields.FIRST_NAME], contact_contact[EContactFields.LAST_NAME]]))
            row = [
                CellData(text=contact[EContactFields.NAME], icon=icon),
                CellData(text=person),
                CellData(text=contact_address[EContactFields.STREET_1]),
                CellData(text=contact_address[EContactFields.PLZ], right_align=True),
                CellData(text=contact_address[EContactFields.CITY]),
                CellData(text=contact_contact[EContactFields.MAIL]),
                CellData(text=contact[EContactFields.ID]),
            ]
            rows.append(row)
        self.ui_table.update_table(rows)
        self.ui_table.table.setColumnHidden(len(ROW_DESCRIPTION) - 1, True)
        if update_dashboard:
            self.ui.tab_dashboard.update_dashboard_data()

    def get_template(self, template: str) -> str:
        """!
        @brief Replace placeholder fields in the mail template with company data.
        @param template : Mail template text with placeholders.
        @return Mail text with resolved placeholders.
        """

        company = self.ui.tab_settings.company_data
        company_address = company[COMPANY_ADDRESS_FIELD]
        company_contact = company[COMPANY_CONTACT_FIELD]
        company_payment = company[COMPANY_PAYMENT_FIELD]

        text_blocks = {
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
        for text_block, text_value in text_blocks.items():
            template = template.replace(f"[%{text_block}%]", text_value)  # format: [%TEXT_BLOCK%]
        return template

    def on_item_double_clicked(self, row: int, col: int, value: str) -> None:
        """!
        @brief Handles double-click events on a table entry.
        @param row : clicked row index
        @param col : clicked column index
        @param value : value of clicked cell
        """
        if col == EMAIL_IDX:
            if re.match(EMAIL_REGEX, value) is not None:
                subject = self.get_template(self.ui.tab_settings.company_data[COMPANY_DEFAULT_FIELD][ECompanyFields.MAIL_SUBJECT])
                body = self.get_template(self.ui.tab_settings.company_data[COMPANY_DEFAULT_FIELD][ECompanyFields.MAIL_TEXT])
                company = self.ui.tab_settings.company_data
                company_contact = company[COMPANY_CONTACT_FIELD]
                sender_mail = company_contact[ECompanyFields.MAIL]
                url = QUrl(f"mailto:{value}?from={sender_mail}&subject={subject}&body={body}")
                QDesktopServices.openUrl(url)
        else:
            model = self.ui_table.table.model()
            assert model is not None
            uid_index = model.index(row, len(ROW_DESCRIPTION) - 1)
            uid = model.data(uid_index, Qt.ItemDataRole.DisplayRole)

            if uid:
                found_contact = next((contact for contact in self.contacts if contact[EContactFields.ID] == uid), None)

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
