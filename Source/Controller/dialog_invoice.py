"""!
********************************************************************************
@file   dialog_invoice.py
@brief  Create invoice dialog
********************************************************************************
"""

import os
import logging
from typing import Any, Optional, TYPE_CHECKING
from datetime import datetime

from PyQt6 import QtWidgets
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QIcon, QPixmap, QAction
from PyQt6.QtWidgets import QWidget, QDialog, QFileDialog, QVBoxLayout, QPushButton, QHBoxLayout, QMessageBox

from Source.version import __title__
from Source.Util.app_data import EInvoiceOption, ETheme, ICON_EXCEL_LIGHT, ICON_EXCEL_DARK, \
    ICON_PDF_LIGHT, ICON_PDF_DARK, ICON_XML_LIGHT, ICON_XML_DARK, ICON_ZUGFERD_LIGHT, ICON_ZUGFERD_DARK, thread_dialog, \
    write_invoice_option, read_invoice_option, write_qr_code_settings, read_qr_code_settings, try_load_plugin, function_accepts_params
from Source.Views.dialogs.dialog_invoice_general_ui import Ui_DialogInvoice
from Source.Views.widgets.invoice_data_ui import Ui_InvoiceData
from Source.Views.widgets.invoice_item_data_ui import Ui_InvoiceItemData
from Source.Views.widgets.invoice_discounts_data_ui import Ui_InvoiceDiscountsData
from Source.Views.widgets.invoice_surcharges_data_ui import Ui_InvoiceSurchargesData
from Source.Views.widgets.invoice_tax_data_ui import Ui_InvoiceTaxData
from Source.Model.company import ECompanyFields, LOGO_BRIEF_PATH, COMPANY_BOOKING_FIELD, \
    COMPANY_ADDRESS_FIELD, COMPANY_CONTACT_FIELD, COMPANY_PAYMENT_FIELD, COMPANY_DEFAULT_FIELD
from Source.Model.contacts import EContactFields, CONTACT_CONTACT_FIELD, CONTACT_ADDRESS_FIELD
from Source.Model.general_invoice import create_general_invoice
from Source.Model.invoice_number import InvoiceNumber
from Source.Model.data_handler import get_libre_office_path, IMAGE_FILE_TYPES, NO_TAX_RATE, INVOICE_TEMPLATE_FILE_TYPES, \
    DATE_FORMAT_XINVOICE, JSON_FILE_TYPES, read_json_file, write_json_file, DATE_FORMAT_XML, \
    PDF_TYPE, XML_TYPE, JSON_TYPE
from Source.Model.ZUGFeRD.drafthorse_data import D_INVOICE_TYPE, D_CURRENCY, D_COUNTRY_CODE, D_PAYMENT_METHOD, \
    D_VAT_CODE, D_UNIT, D_ALLOWANCE_REASON_CODE, D_CHARGE_REASON_CODE, D_EXEMPTION_REASON_CODE
from Source.Model.ZUGFeRD.drafthorse_invoice import write_customer_to_json, write_company_to_json, fill_invoice_data
from Source.Model.ZUGFeRD.drafthorse_import import set_spin_box_read_only, set_combo_box_items, set_line_edit_read_only, \
    set_combo_box_value, check_zugferd, extract_xml_from_pdf, check_xinvoice, extract_xml_from_xinvoice
from Source.Model.ZUGFeRD.drafthorse_convert import convert_facturx_to_json, normalize_decimal
if TYPE_CHECKING:
    from Source.Controller.main_window import MainWindow

log = logging.getLogger(__title__)

I_MAX_POSITIONS = 100


def add_icon(action: QAction, icon: str) -> None:
    """!
    @brief Add icon to action
    @param action : action
    @param icon : icon
    """
    image = QIcon()
    image.addPixmap(QPixmap(icon), QIcon.Mode.Normal, QIcon.State.Off)
    action.setIcon(image)


def config_invoice_type_btn(dialog: Any) -> None:
    """!
    @brief Configuration invoice type button.
    @param dialog : dialog
    """
    generate_pdf = os.path.isfile(get_libre_office_path())

    create_options = QtWidgets.QMenu(dialog)
    dialog.btn_create.setMenu(create_options)

    dialog.action_create_excel = create_options.addAction(EInvoiceOption.EXCEL)
    add_icon(dialog.action_create_excel, ICON_EXCEL_LIGHT if dialog.ui.model.c_monitor.is_light_theme() else ICON_EXCEL_DARK)

    if generate_pdf:
        dialog.action_create_pdf = create_options.addAction(EInvoiceOption.PDF)
        add_icon(dialog.action_create_pdf, ICON_PDF_LIGHT if dialog.ui.model.c_monitor.is_light_theme() else ICON_PDF_DARK)

    dialog.action_create_xml = create_options.addAction(EInvoiceOption.XML)
    add_icon(dialog.action_create_xml, ICON_XML_LIGHT if dialog.ui.model.c_monitor.is_light_theme() else ICON_XML_DARK)

    if generate_pdf:
        dialog.action_create_zugferd = create_options.addAction(EInvoiceOption.ZUGFERD)
        add_icon(dialog.action_create_zugferd, ICON_ZUGFERD_LIGHT if dialog.ui.model.c_monitor.is_light_theme() else ICON_ZUGFERD_DARK)

    # set last invoice type option
    e_last_invoice_option = read_invoice_option()
    if generate_pdf:
        match e_last_invoice_option:  # set invoice option from last session
            case EInvoiceOption.EXCEL:
                dialog.btn_create.setDefaultAction(dialog.action_create_excel)
            case EInvoiceOption.PDF:
                dialog.btn_create.setDefaultAction(dialog.action_create_pdf)
            case EInvoiceOption.XML:
                dialog.btn_create.setDefaultAction(dialog.action_create_xml)
            case EInvoiceOption.ZUGFERD:
                dialog.btn_create.setDefaultAction(dialog.action_create_zugferd)
            case _:
                log.error("Invalid invoice option: %s", e_last_invoice_option)
    else:
        match e_last_invoice_option:  # set invoice option from last session
            case EInvoiceOption.EXCEL:
                dialog.btn_create.setDefaultAction(dialog.action_create_excel)
            case EInvoiceOption.XML:
                dialog.btn_create.setDefaultAction(dialog.action_create_xml)
            case _:
                dialog.btn_create.setDefaultAction(dialog.action_create_excel)  # default is PDF generation not possible

    # set border of button
    match dialog.ui.model.c_monitor.e_actual_theme:
        case ETheme.LIGHT:
            dialog.btn_create.setStyleSheet(
                dialog.btn_create.styleSheet() +
                "QToolButton{border-width: 1px; border-style: solid; border-color: #DADCE0;} QToolButton::menu-button{border-width: 1px; border-style: solid; border-color: #DADCE0;}")
        case ETheme.DARK:
            dialog.btn_create.setStyleSheet(
                dialog.btn_create.styleSheet() +
                "QToolButton{border-width: 1px; border-style: solid; border-color: #3F4042;} QToolButton::menu-button{border-width: 1px; border-style: solid; border-color: #3F4042;}")
        case _:
            dialog.btn_create.setStyleSheet("border: 1px solid palette(dark);")

    if dialog.action_create_excel is not None:
        dialog.action_create_excel.triggered.connect(lambda: dialog.create_invoice(EInvoiceOption.EXCEL))
    if dialog.action_create_xml is not None:
        dialog.action_create_xml.triggered.connect(lambda: dialog.create_invoice(EInvoiceOption.XML))
    if generate_pdf:
        if dialog.action_create_pdf is not None:
            dialog.action_create_pdf.triggered.connect(lambda: dialog.create_invoice(EInvoiceOption.PDF))
        if dialog.action_create_zugferd is not None:
            dialog.action_create_zugferd.triggered.connect(lambda: dialog.create_invoice(EInvoiceOption.ZUGFERD))


class InvoiceDialog(QDialog, Ui_DialogInvoice):
    """!
    @brief Invoice dialog.
    @param ui : main window
    @param uid : UID of selected contact
    """

    def __init__(self, ui: "MainWindow", uid: Optional[str] = None, *args: Any, **kwargs: Any) -> None:
        super().__init__(parent=ui, *args, **kwargs)  # type: ignore
        self.setupUi(self)
        self.setMinimumWidth(960)
        self.setMinimumHeight(500)
        self.setWindowFlags(Qt.WindowType.Window)  # set all window buttons (e.g max window size)
        self.setWindowTitle("Rechnung erstellen")
        self.ui = ui
        self.due_days_changed = False  # True=due days changed; False=due date changed
        self.c_invoice_number = InvoiceNumber(ui)

        # select customer data
        self.customer = None
        self.default_uid = uid
        self.extended_mode = False
        self.ui_invoice_data = None
        self.lock_auto_price_edit = False
        self.lock_due_date_edit = False
        if self.ui.tab_settings.company_data[COMPANY_BOOKING_FIELD][ECompanyFields.SMALL_BUSINESS_REGULATION]:
            self.default_tax_rate = NO_TAX_RATE
        else:
            self.default_tax_rate = self.ui.tab_settings.company_data[COMPANY_BOOKING_FIELD][ECompanyFields.TAX_RATES][0]
        self.default_payment_days = self.ui.tab_settings.company_data[COMPANY_DEFAULT_FIELD][ECompanyFields.PAYMENT_DAYS]
        # items
        self.item_gross_changed = [False] * I_MAX_POSITIONS  # True=gross changed; False=net changed
        self.item_layout = None
        self.btn_add_item = QPushButton("Position hinzufügen")
        self.btn_remove_item = QPushButton("Position entfernen")
        self.item_button_layout = QHBoxLayout()
        self.item_button_layout.addWidget(self.btn_add_item)
        self.item_button_layout.addWidget(self.btn_remove_item)
        # discounts
        self.discount_percent_changed = [False] * I_MAX_POSITIONS  # True=percent changed; False=net changed
        self.discounts_layout = None
        self.btn_add_discount = QPushButton("Nachlass zufügen")
        self.btn_remove_discount = QPushButton("Nachlass entfernen")
        self.discounts_button_layout = QHBoxLayout()
        self.discounts_button_layout.addWidget(self.btn_add_discount)
        self.discounts_button_layout.addWidget(self.btn_remove_discount)
        # surcharges
        self.surcharges_percent_changed = [False] * I_MAX_POSITIONS  # True=percent changed; False=net changed
        self.surcharges_layout = None
        self.btn_add_surcharge = QPushButton("Zuschlag zufügen")
        self.btn_remove_surcharge = QPushButton("Zuschlag entfernen")
        self.surcharges_button_layout = QHBoxLayout()
        self.surcharges_button_layout.addWidget(self.btn_add_surcharge)
        self.surcharges_button_layout.addWidget(self.btn_remove_surcharge)
        # tax
        self.tax_layout = None
        thread_dialog(self)

    def show_dialog(self) -> None:
        """!
        @brief Show dialog
        """
        self.ui.model.c_monitor.set_dialog_style(self)

        config_invoice_type_btn(self)

        # empty Widget as Container
        container_widget = QtWidgets.QWidget()
        # build Ui in Container
        self.ui_invoice_data = Ui_InvoiceData()
        self.ui_invoice_data.setupUi(container_widget)
        # Set Container als Content of ScrollArea
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(container_widget)
        # to add BT label in UI designer
        #  <span style="font-size:7pt; color: grey;">(BT-x)</span>

        # add item widget
        self.ui_invoice_data.item_widgets = []  # item widget list
        if self.ui_invoice_data.groupBox_6_position.layout() is None:  # ensure that layout exists
            self.item_layout = QVBoxLayout(self.ui_invoice_data.groupBox_6_position)
            self.ui_invoice_data.groupBox_6_position.setLayout(self.item_layout)
        else:
            self.item_layout = self.ui_invoice_data.groupBox_6_position.layout()
        # Add item button
        self.item_layout.addLayout(self.item_button_layout)
        self.btn_add_item.clicked.connect(self.add_item)
        self.btn_remove_item.clicked.connect(self.remove_item)
        self.btn_remove_item.setEnabled(False)

        # add discount widget
        self.ui_invoice_data.discounts_widgets = []  # discounts widget list
        if self.ui_invoice_data.groupBox_7_discounts.layout() is None:  # ensure that layout exists
            self.discounts_layout = QVBoxLayout(self.ui_invoice_data.groupBox_7_discounts)
            self.ui_invoice_data.groupBox_7_discounts.setLayout(self.discounts_layout)
        else:
            self.discounts_layout = self.ui_invoice_data.groupBox_7_discounts.layout()
        # Add discount button
        self.discounts_layout.addLayout(self.discounts_button_layout)
        self.btn_add_discount.clicked.connect(self.add_discount)
        self.btn_remove_discount.clicked.connect(self.remove_discount)
        self.btn_remove_discount.setEnabled(False)

        # add surcharges widget
        self.ui_invoice_data.surcharges_widgets = []  # surcharges widget list
        if self.ui_invoice_data.groupBox_8_surcharges.layout() is None:  # ensure that layout exists
            self.surcharges_layout = QVBoxLayout(self.ui_invoice_data.groupBox_8_surcharges)
            self.ui_invoice_data.groupBox_8_surcharges.setLayout(self.surcharges_layout)
        else:
            self.surcharges_layout = self.ui_invoice_data.groupBox_8_surcharges.layout()
        # Add surcharges button
        self.surcharges_layout.addLayout(self.surcharges_button_layout)
        self.btn_add_surcharge.clicked.connect(self.add_surcharge)
        self.btn_remove_surcharge.clicked.connect(self.remove_surcharge)
        self.btn_remove_surcharge.setEnabled(False)

        # add tax widget
        self.ui_invoice_data.tax_widgets = []  # tax widget list
        if self.ui_invoice_data.groupBox_9_tax.layout() is None:  # ensure that layout exists
            self.tax_layout = QVBoxLayout(self.ui_invoice_data.groupBox_9_tax)
            self.ui_invoice_data.groupBox_9_tax.setLayout(self.tax_layout)
        else:
            self.tax_layout = self.ui_invoice_data.groupBox_9_tax.layout()

        # create first item widget
        self.add_item()

        # delivery time
        self.ui_invoice_data.cb_accounting_date.stateChanged.connect(self.accounting_date_checkbox_changed)
        self.accounting_date_checkbox_changed(False)
        self.ui_invoice_data.de_accounting_date_from.dateChanged.connect(self.accounting_date_from_changed)
        self.ui_invoice_data.de_accounting_date_to.dateChanged.connect(self.accounting_date_to_changed)

        self.ui_invoice_data.dsb_payed_amount.valueChanged.connect(self.update_total_data)
        self.ui_invoice_data.dsb_rounded_amount.valueChanged.connect(self.update_total_data)

        self.cb_extended.clicked.connect(self.expand_mode_changed)
        self.set_default_data()
        self.expand_mode_changed()
        self.update_total_data()

        # customer
        index_to_set = None
        for i, contact in enumerate(self.ui.tab_contacts.l_data):
            self.cb_contact_template.addItem(contact[EContactFields.NAME].replace("\n", " "), contact)  # show in single row
            if self.default_uid:
                if contact[EContactFields.ID] == self.default_uid:
                    index_to_set = i
        self.cb_contact_template.activated.connect(self.contact_template_activated)
        if index_to_set is not None:
            self.cb_contact_template.setCurrentIndex(index_to_set)
            self.contact_template_activated(index_to_set)
        else:
            self.cb_contact_template.setCurrentIndex(-1)

        self.cb_qr_code.setChecked(read_qr_code_settings())

        self.btn_import.clicked.connect(self.import_btn_clicked)
        self.btn_export.clicked.connect(self.export_btn_clicked)

        self.show()
        self.exec()

    def close_dialog(self) -> None:
        """!
        @brief Close dialog.
        """
        self.close()

    def set_default_data(self) -> None:
        """!
        @brief Set default data
        """
        dialog = self.ui_invoice_data
        actual_date = QDate.currentDate()

        # Rechnungstitel
        dialog.le_invoice_title.setText("Rechnung")
        # Rechnungsnummer (BT-1)
        dialog.le_invoice_number.setText("")  # updated by set invoice date later
        # Rechnungsdatum (BT-2)
        dialog.de_invoice_date.setDate(actual_date)
        dialog.de_invoice_date.dateChanged.connect(self.on_invoice_data_changed)
        self.on_invoice_data_changed(actual_date)
        # Code für den Rechnungstyp (BT-3)
        set_combo_box_items(dialog.cb_invoice_type, "380", D_INVOICE_TYPE)
        # Code für die Rechnungswährung (BT-5)
        set_combo_box_items(dialog.cb_currency, "EUR", D_CURRENCY)
        # Fälligkeitsdatum der Zahlung (BT-9)
        dialog.de_due_date.setDate(actual_date.addDays(self.default_payment_days))
        dialog.sb_due_days.setValue(self.default_payment_days)
        dialog.de_due_date.dateChanged.connect(lambda: self.due_date_changed(False))
        dialog.sb_due_days.valueChanged.connect(lambda: self.due_date_changed(True))
        # Tatsächliches Lieferdatum (BT-72)
        dialog.de_deliver_date.setDate(actual_date)
        # Anfangsdatum des Rechnungszeitraums (BT-73)
        dialog.de_accounting_date_from.setDate(actual_date)
        # Enddatum des Rechnungszeitraums (BT-74)
        dialog.de_accounting_date_to.setDate(actual_date)
        # Käuferreferenz (BT-10)
        dialog.le_buyer_reference.setText("")
        # Projektnummer (BT-11)
        dialog.le_project_number.setText("")
        # Vertragsnummer (BT-12)
        dialog.le_contract_number.setText("")
        # Bestellnummer (BT-13)
        dialog.le_order_number.setText("")
        # Auftragsnummer (BT-14)
        dialog.le_assignment_number.setText("")
        # Wareneingangsmeldung (BT-15)
        dialog.le_receiving_referenced_document.setText("")
        dialog.de_receiving_advice_referenced_document.setDate(actual_date)
        # Versandanzeige (BT-16)
        dialog.le_despatch_advice_referenced_document.setText("")
        dialog.de_despatch_advice_referenced_document.setDate(actual_date)
        # Ausschreibung/Los (BT-17)
        dialog.le_additional_referenced_document.setText("")
        # Objektreferenz (BT-18)
        dialog.le_object_reference.setText("")
        # Buchungskonto des Käufers (BT-19)
        dialog.le_booking_account_buyer.setText("")
        # Rechnungsreferenz (BT-25, BT-26)
        dialog.le_booking_account_buyer.setText("")  # ID (BT-25)
        dialog.de_invoice_reference.setDate(actual_date)  # Datum (BT-26)
        # Freitext zur Rechnung (BT-22)
        dialog.pte_note.setPlainText("")
        # Einleitungstext
        dialog.pte_introduction_text.setPlainText("")

        company = self.ui.tab_settings.company_data
        company_address = company[COMPANY_ADDRESS_FIELD]
        company_contact = company[COMPANY_CONTACT_FIELD]
        company_payment = company[COMPANY_PAYMENT_FIELD]
        # Name des Verkäufers (BT-27)
        dialog.le_seller_company.setText(company[ECompanyFields.NAME])
        # Handelsname (BT-28)
        dialog.le_seller_name.setText(company[ECompanyFields.TRADE_NAME])
        # Verkäuferkennung (BT-29)
        dialog.le_seller_recognition.setText("")  # no in company data
        # Registernummer (BT-30)
        dialog.le_seller_register_number.setText(company[ECompanyFields.TRADE_ID])
        # Umsatzsteuer-Identifikationsnummer des Verkäufers (BT-31)
        dialog.le_seller_vat.setText(company[ECompanyFields.VAT_ID])
        # Steuernummer des Verkäufers (BT-32)
        dialog.le_seller_tax_number.setText(company[ECompanyFields.TAX_ID])
        # WEEE-Nummer
        dialog.le_seller_weee_number.setText("")  # no in company data
        # Rechtliche Informationen (BT-33)
        dialog.pte_seller_law_info.setPlainText(company[ECompanyFields.LEGAL_INFO])
        # seller electric address (BT-34)
        dialog.le_seller_electric_address.setText(company[ECompanyFields.ELECTRONIC_ADDRESS])
        # Webseite
        dialog.le_seller_website.setText(company[ECompanyFields.WEBSITE_TEXT])
        # Zeile 1 der Verkäuferanschrift (BT-35)
        dialog.le_seller_street_1.setText(company_address[ECompanyFields.STREET_1])
        # Zeile 2 der Verkäuferanschrift (BT-36)
        dialog.le_seller_street_2.setText(company_address[ECompanyFields.STREET_2])
        # Postleitzahl der Verkäuferanschrift (BT-38)
        dialog.le_seller_plz.setText(company_address[ECompanyFields.PLZ])
        # Stadt der Verkäuferanschrift (BT-37)
        dialog.le_seller_city.setText(company_address[ECompanyFields.CITY])
        # Ländercode der Verkäuferanschrift (BT-40)
        set_combo_box_items(dialog.cb_seller_country, company_address[ECompanyFields.COUNTRY], D_COUNTRY_CODE)
        # Kontaktstelle des Verkäufers (BT-41)
        contact_name = f"{company_contact[ECompanyFields.FIRST_NAME]} {company_contact[ECompanyFields.LAST_NAME]}"
        dialog.le_seller_contact_name.setText(contact_name)
        # E-Mail-Adresse der Kontaktstelle des Verkäufers (BT-43)
        dialog.le_seller_contact_mail.setText(company_contact[ECompanyFields.MAIL])
        # Telefonnummer der Kontaktstelle des Verkäufers (BT-42)
        dialog.le_seller_contact_phone.setText(company_contact[ECompanyFields.PHONE])
        # seller fax
        dialog.le_seller_contact_fax.setText("")  # no in company data
        # seller logo
        dialog.btn_seller_logo_select.clicked.connect(self.select_logo)
        logo_path = os.path.join(self.ui.model.data_path, LOGO_BRIEF_PATH)
        self.select_logo(logo_path)

        # Name des Käufers (BT-44)
        dialog.le_buyer_company.setText("")
        # Handelsname (BT-45)
        dialog.le_buyer_name.setText("")
        # Käuferkennung (BT-46)
        dialog.le_buyer_recognition.setText("")
        # Registernummer (BT-47)
        dialog.le_buyer_register_number.setText("")
        # Umsatzsteuer-Identifikationsnummer des Käufers (BT-48)
        dialog.le_buyer_vat.setText("")
        # Elektronische Adresse (BT-49)
        dialog.le_buyer_electric_address.setText("")
        # Zeile 1 der Käuferanschrift (BT-50)
        dialog.le_buyer_street_1.setText("")
        # Zeile 2 der Käuferanschrift (BT-51)
        dialog.le_buyer_street_2.setText("")
        # Postleitzahl der Käuferanschrift (BT-53)
        dialog.le_buyer_plz.setText("")
        # Stadt der Käuferanschrift (BT-52)
        dialog.le_buyer_city.setText("")
        # Ländercode der Käuferanschrift (BT-55)
        set_combo_box_items(dialog.cb_buyer_country, "DE", D_COUNTRY_CODE)
        # Kontaktstelle des Käufers (BT-56)
        dialog.le_buyer_contact_name.setText("")
        # E-Mail-Adresse der Kontaktstelle des Käufers (BT-58)
        dialog.le_buyer_contact_mail.setText("")
        # Telefonnummer der Kontaktstelle des Käufers (BT-57)
        dialog.le_buyer_contact_phone.setText("")

        # Code für die Zahlungsart D_PAYMENT_METHOD (BT-81)
        set_combo_box_items(dialog.cb_payment_method, "58", D_PAYMENT_METHOD)
        # Name des Zahlungskontos (BT-85)
        dialog.le_account_holder.setText(company_payment[ECompanyFields.BANK_OWNER])
        # Kennung des Zahlungskontos (BT-84)
        dialog.le_iban.setText(company_payment[ECompanyFields.BANK_IBAN])
        # Kennung des Zahlungsdienstleisters (BT-86)
        dialog.le_bic.setText(company_payment[ECompanyFields.BANK_BIC])
        # bank name
        dialog.le_bank_name.setText(company_payment[ECompanyFields.BANK_NAME])
        # Verwendungszweck (BT-83)
        dialog.le_payment_purpose.setText("")
        # Zahlungsbedingungen (BT-20)
        dialog.pte_payment_terms.setPlainText("")

        # Name des Waren- oder Dienstleistungsempfängers (BT-70)
        dialog.le_deliver_name.setText("")
        # Kennung des Lieferorts (BT-71)
        dialog.le_deliver_place_ident.setText("")
        # Zeile 1 der Lieferanschrift (BT-75)
        dialog.le_deliver_street_1.setText("")
        # Zeile 2 der Lieferanschrift (BT-76)
        dialog.le_deliver_street_2.setText("")
        # Zeile 3 der Lieferanschrift (BT-165)
        dialog.le_deliver_addition.setText("")
        # Postleitzahl der Lieferanschrift (BT-78)
        dialog.le_deliver_plz.setText("")
        # Stadt der Lieferanschrift (BT-77)
        dialog.le_deliver_city.setText("")
        # Ländercode der Lieferanschrift (BT-80)
        set_combo_box_items(dialog.cb_deliver_country, "DE", D_COUNTRY_CODE)
        # Stadt der Lieferanschrift (BT-79)
        dialog.le_deliver_region.setText("")

        # Summe der Nettobeträge aller Rechnungspositionen (BT-106)
        set_spin_box_read_only(dialog.dsb_sum_positions, 0.0)
        # Summe der Zuschläge auf Dokumentenebene (BT-108)
        set_spin_box_read_only(dialog.dsb_sum_surcharges, 0.0)
        # Summe der Abschläge auf Dokumentenebene (BT-107)
        set_spin_box_read_only(dialog.dsb_sum_discounts, 0.0)
        # Rechnungsgesamtbetrag ohne Umsatzsteuer (BT-109)
        set_spin_box_read_only(dialog.dsb_sum_net, 0.0)
        # Summe Umsatzsteuer (BT-110)
        set_spin_box_read_only(dialog.dsb_sum_vat, 0.0)
        # Rechnungsgesamtbetrag einschließlich Umsatzsteuer (BT-112)
        set_spin_box_read_only(dialog.dsb_sum_gross, 0.0)
        # Vorauszahlungsbetrag (BT-113)
        dialog.dsb_payed_amount.setValue(0.0)
        # Rundungsbetrag (BT-114)
        dialog.dsb_rounded_amount.setValue(0.0)
        # Fälliger Zahlungsbetrag (BT-115)
        set_spin_box_read_only(dialog.dsb_amount_due, 0.0)

    def update_total_data(self) -> None:
        """!
        @brief Update total data
        """
        invoice_data = self.read_ui_data_to_json()
        fill_invoice_data(invoice_data)

        data_totals = invoice_data["totals"]

        discount_dialog: Ui_InvoiceDiscountsData  # declare for typing
        for discount_dialog in self.ui_invoice_data.discounts_widgets:
            discount_dialog.dsb_basis_amount.setValue(data_totals["itemsNetAmount"])
        surcharge_dialog: Ui_InvoiceSurchargesData  # declare for typing
        for surcharge_dialog in self.ui_invoice_data.surcharges_widgets:
            surcharge_dialog.dsb_basis_amount.setValue(data_totals["itemsNetAmount"])

        self.update_tax_widget(invoice_data)

        dialog = self.ui_invoice_data
        # Summe der Nettobeträge aller Rechnungspositionen (BT-106)
        dialog.dsb_sum_positions.setValue(data_totals["itemsNetAmount"])
        # Summe der Zuschläge auf Dokumentenebene (BT-108)
        dialog.dsb_sum_surcharges.setValue(data_totals["chargesNetAmount"])
        # Summe der Abschläge auf Dokumentenebene (BT-107)
        dialog.dsb_sum_discounts.setValue(data_totals["allowancesNetAmount"])
        # Rechnungsgesamtbetrag ohne Umsatzsteuer (BT-109)
        dialog.dsb_sum_net.setValue(data_totals["netAmount"])
        # Summe Umsatzsteuer (BT-110)
        dialog.dsb_sum_vat.setValue(data_totals["vatAmount"])
        # Rechnungsgesamtbetrag einschließlich Umsatzsteuer (BT-112)
        dialog.dsb_sum_gross.setValue(data_totals["grossAmount"])
        # Fälliger Zahlungsbetrag (BT-115)
        dialog.dsb_amount_due.setValue(data_totals["dueAmount"])

    def item_billing_period_checkbox_changed(self, state: bool, item_index: int) -> None:
        """!
        @brief Item billing period checkbox changed
        @param state : enable state
        @param item_index : item index
        """
        item_dialog: Ui_InvoiceItemData = self.ui_invoice_data.item_widgets[item_index]
        item_dialog.de_item_billing_period_start.setEnabled(state)
        item_dialog.de_item_billing_period_end.setEnabled(state)
        item_dialog.lbl_item_billing_period_start.setEnabled(state)
        item_dialog.lbl_item_billing_period_end.setEnabled(state)

    def accounting_date_checkbox_changed(self, state: int | bool) -> None:
        """!
        @brief Accounting date checkbox changed
        @param state : checkbox status
        """
        enable = bool(state)
        self.ui_invoice_data.de_accounting_date_from.setEnabled(enable)
        self.ui_invoice_data.lbl_accounting_to.setEnabled(enable)
        self.ui_invoice_data.de_accounting_date_to.setEnabled(enable)

    def accounting_date_from_changed(self, from_date: QDate) -> None:
        """!
        @brief Accounting date "from" changed
        @param from_date : from date
        """
        to_date = self.ui_invoice_data.de_accounting_date_to.date()
        if to_date < from_date:
            self.ui_invoice_data.de_accounting_date_to.setDate(from_date)

    def accounting_date_to_changed(self, to_date: QDate) -> None:
        """!
        @brief Accounting date "to" changed
        @param to_date : to date
        """
        from_date = self.ui_invoice_data.de_accounting_date_from.date()
        if to_date < from_date:
            self.ui_invoice_data.de_accounting_date_from.setDate(to_date)

    def add_item(self) -> None:
        """!
        @brief Add item
        """
        item_index = len(self.ui_invoice_data.item_widgets)
        if item_index <= I_MAX_POSITIONS:
            item_dialog = Ui_InvoiceItemData()  # new item instance
            widget = QWidget()  # new container widget
            item_dialog.setupUi(widget)
            self.item_layout.insertWidget(self.item_layout.count() - 1, widget)  # insert widget in layout before buttons
            item_dialog.groupBox.setTitle(f"Position {item_index + 1}")
            self.ui_invoice_data.item_widgets.append(item_dialog)  # store item ui for later use
            self.set_default_item_data(item_dialog)
            self.update_item_expand_status(item_dialog, self.cb_extended.isChecked())
            if item_index > 0:
                self.btn_remove_item.setEnabled(True)
            # date checkbox callback
            item_dialog.cb_item_billing_period.stateChanged.connect(lambda state, idx=item_index: self.item_billing_period_checkbox_changed(state, idx))
            # price callback
            item_dialog.dsb_item_net_unit_price.valueChanged.connect(lambda: self.item_price_changed(item_index, False))
            item_dialog.dsb_item_gross_unit_price.valueChanged.connect(lambda: self.item_price_changed(item_index, True))
            item_dialog.dsb_item_vat_rate.valueChanged.connect(lambda: self.item_price_changed(item_index, None))
            item_dialog.cb_item_vat_code.currentTextChanged.connect(self.update_total_data)  # update for taxes
            item_dialog.dsb_item_quantity.valueChanged.connect(lambda: self.item_price_changed(item_index, None))
            item_dialog.dsb_item_basis_quantity.valueChanged.connect(lambda: self.item_price_changed(item_index, None))
            item_dialog.line_charge.hide()  # TODO Nachlässe/Zulagen für Items umsetzen
            self.update_total_data()
        else:
            self.ui.set_status("Maximale Positionen erreicht.", b_highlight=True)

    def remove_item(self) -> None:
        """!
        @brief Remove item
        """
        item_index = len(self.ui_invoice_data.item_widgets)
        if item_index <= 2:
            self.btn_remove_item.setEnabled(False)
        if item_index > 1:
            last_item = self.ui_invoice_data.item_widgets.pop()
            widget = last_item.groupBox.parentWidget()
            self.item_layout.removeWidget(widget)
            widget.setParent(None)
            self.update_total_data()

    def set_default_item_data(self, item_dialog: Ui_InvoiceItemData) -> None:
        """!
        @brief Set default item data
        @param item_dialog : item dialog
        """
        actual_date = QDate.currentDate()
        # Name (BT-153)
        item_dialog.le_item_name.setText("")
        # Umsatzsteuersatz für den in Rechnung gestellten Artikel (BT-152)
        item_dialog.dsb_item_vat_rate.setValue(self.default_tax_rate)
        # Code der Umsatzsteuerkategorie des in Rechnung gestellten Artikels (BT-151)
        set_combo_box_items(item_dialog.cb_item_vat_code, "S", D_VAT_CODE)
        # Artikel-Nr. (BT-155)
        item_dialog.le_item_id.setText("")
        # Startdatum (BT-134)
        item_dialog.de_item_billing_period_start.setDate(actual_date)
        item_dialog.de_item_billing_period_start.setEnabled(False)
        item_dialog.lbl_item_billing_period_start.setEnabled(False)
        # Enddatum (BT-135)
        item_dialog.de_item_billing_period_end.setDate(actual_date)
        item_dialog.de_item_billing_period_end.setEnabled(False)
        item_dialog.lbl_item_billing_period_end.setEnabled(False)
        # Referenz zur Bestellposition (BT-132)
        item_dialog.le_item_order_position.setText("")
        # Objektkennung auf Ebene der Rechnungsposition (BT-128)
        item_dialog.le_object_reference.setText("")
        # Artikelbeschreibung (BT-154)
        item_dialog.pte_item_description.setPlainText("")
        # Menge (BT-129)
        item_dialog.dsb_item_quantity.setValue(1)
        # Einheit (BT-130) D_UNIT
        set_combo_box_items(item_dialog.cb_item_quantity_unit, "H87", D_UNIT)
        # Einzelpreis (Netto) (BT-146)
        item_dialog.dsb_item_net_unit_price.setValue(0.0)
        # Einzelpreis (Brutto)
        item_dialog.dsb_item_gross_unit_price.setValue(0.0)
        # Basismenge zum Artikelpreis (BT-149)
        item_dialog.dsb_item_basis_quantity.setValue(1)
        # Steuerbetrag
        set_spin_box_read_only(item_dialog.dsb_item_vat_amount, 0.0)
        # Gesamtpreis (Netto) (BT-131)
        set_spin_box_read_only(item_dialog.dsb_item_net_amount, 0.0)
        # Gesamtpreis (Brutto)
        set_spin_box_read_only(item_dialog.dsb_item_gross_price, 0.0)

    def item_price_changed(self, item_index: int, gross_changed: None | bool) -> None:
        """!
        @brief Item price changed
        @param item_index : item index
        @param gross_changed : changed object True=gross False=net None=other (use last changed)
        """
        if not self.lock_auto_price_edit:
            self.lock_auto_price_edit = True
            item_dialog: Ui_InvoiceItemData = self.ui_invoice_data.item_widgets[item_index]
            b_extended = self.cb_extended.isChecked()

            if gross_changed is not None:
                self.item_gross_changed[item_index] = gross_changed

            net_price = item_dialog.dsb_item_net_unit_price.value()
            gross_price = item_dialog.dsb_item_gross_unit_price.value()
            vat_rate = item_dialog.dsb_item_vat_rate.value()
            item_quantity = item_dialog.dsb_item_quantity.value()
            item_basis_quantity = item_dialog.dsb_item_basis_quantity.value() if b_extended else 1

            if self.item_gross_changed[item_index]:
                new_net_price = gross_price / (1 + (vat_rate / 100))
                net_amount = item_quantity * new_net_price
                gross_amount = item_quantity * gross_price
                item_dialog.dsb_item_net_unit_price.setValue(new_net_price)
            else:
                new_gross_price = net_price * (1 + (vat_rate / 100))
                net_amount = item_quantity * net_price
                gross_amount = item_quantity * new_gross_price
                item_dialog.dsb_item_gross_unit_price.setValue(new_gross_price)
            net_amount /= item_basis_quantity
            gross_amount /= item_basis_quantity
            tax_amount = gross_amount - net_amount
            item_dialog.dsb_item_vat_amount.setValue(tax_amount)
            item_dialog.dsb_item_net_amount.setValue(net_amount)
            item_dialog.dsb_item_gross_price.setValue(gross_amount)
            self.lock_auto_price_edit = False

        self.update_total_data()

    def add_discount(self) -> None:
        """!
        @brief Add discount
        """
        discount_index = len(self.ui_invoice_data.discounts_widgets)
        if discount_index == 0:
            current_size = self.size()
            current_width = current_size.width()
            current_height = current_size.height()
            min_width = 1150
            if current_width < min_width:
                self.resize(min_width, current_height)
        if discount_index <= I_MAX_POSITIONS:
            discount_dialog = Ui_InvoiceDiscountsData()  # new discount instance
            widget = QWidget()  # new container widget
            discount_dialog.setupUi(widget)
            self.discounts_layout.insertWidget(self.discounts_layout.count() - 1, widget)  # insert widget in layout before buttons
            self.ui_invoice_data.discounts_widgets.append(discount_dialog)  # store discount ui for later use
            self.set_default_dis_sur_data(discount_dialog, D_ALLOWANCE_REASON_CODE)
            self.btn_remove_discount.setEnabled(True)
            # price callback
            discount_dialog.dsb_basis_amount.valueChanged.connect(lambda: self.discount_price_changed(discount_index, None))
            discount_dialog.dsb_percent.valueChanged.connect(lambda: self.discount_price_changed(discount_index, True))
            discount_dialog.dsb_net_amount.valueChanged.connect(lambda: self.discount_price_changed(discount_index, False))
            discount_dialog.dsb_vat_rate.valueChanged.connect(lambda: self.discount_price_changed(discount_index, None))
            self.update_total_data()
        else:
            self.ui.set_status("Maximale Nachlässe erreicht.", b_highlight=True)

    def remove_discount(self) -> None:
        """!
        @brief Remove discount
        """
        discount_index = len(self.ui_invoice_data.discounts_widgets)
        if discount_index <= 1:
            self.btn_remove_discount.setEnabled(False)
        if discount_index > 0:
            last_discount = self.ui_invoice_data.discounts_widgets.pop()
            widget = last_discount.frame.parentWidget()
            self.discounts_layout.removeWidget(widget)
            widget.setParent(None)
            self.update_total_data()

    def add_surcharge(self) -> None:
        """!
        @brief Add surcharge
        """
        surcharge_index = len(self.ui_invoice_data.surcharges_widgets)
        if surcharge_index == 0:
            current_size = self.size()
            current_width = current_size.width()
            current_height = current_size.height()
            min_width = 1150
            if current_width < min_width:
                self.resize(min_width, current_height)
        if surcharge_index <= I_MAX_POSITIONS:
            surcharge_dialog = Ui_InvoiceSurchargesData()  # new surcharge instance
            widget = QWidget()  # new container widget
            surcharge_dialog.setupUi(widget)
            self.surcharges_layout.insertWidget(self.surcharges_layout.count() - 1, widget)  # insert widget in layout before buttons
            self.ui_invoice_data.surcharges_widgets.append(surcharge_dialog)  # store surcharge ui for later use
            self.set_default_dis_sur_data(surcharge_dialog, D_CHARGE_REASON_CODE)
            self.btn_remove_surcharge.setEnabled(True)
            # price callback
            surcharge_dialog.dsb_basis_amount.valueChanged.connect(lambda: self.surcharge_price_changed(surcharge_index, None))
            surcharge_dialog.dsb_percent.valueChanged.connect(lambda: self.surcharge_price_changed(surcharge_index, True))
            surcharge_dialog.dsb_net_amount.valueChanged.connect(lambda: self.surcharge_price_changed(surcharge_index, False))
            surcharge_dialog.dsb_vat_rate.valueChanged.connect(lambda: self.surcharge_price_changed(surcharge_index, None))
            self.update_total_data()
        else:
            self.ui.set_status("Maximale Zuschläge erreicht.", b_highlight=True)

    def remove_surcharge(self) -> None:
        """!
        @brief Remove surcharge
        """
        surcharge_index = len(self.ui_invoice_data.surcharges_widgets)
        if surcharge_index <= 1:
            self.btn_remove_discount.setEnabled(False)
        if surcharge_index > 0:
            last_surcharge = self.ui_invoice_data.surcharges_widgets.pop()
            widget = last_surcharge.frame.parentWidget()
            self.surcharges_layout.removeWidget(widget)
            widget.setParent(None)
            self.update_total_data()

    def set_default_dis_sur_data(self, dialog: Ui_InvoiceDiscountsData | Ui_InvoiceSurchargesData, reason_codes: dict[str, str]) -> None:
        """!
        @brief Set default discounts or surcharges data
        @param dialog : dialog
        @param reason_codes : reason codes
        """
        # Grundbetrag (BT-93) (BT-100)
        set_spin_box_read_only(dialog.dsb_basis_amount, 0.0)
        # Prozent (BT-94) (BT-101)
        dialog.dsb_percent.setValue(0)
        # Betrag (Netto) (BT-92) (BT-99)
        dialog.dsb_net_amount.setValue(0.0)
        # Steuersatz (BT-96) (BT-103)
        dialog.dsb_vat_rate.setValue(self.default_tax_rate)
        # Steuerkategorie (BT-95) (BT-102)
        set_combo_box_items(dialog.cb_vat_code, "S", D_VAT_CODE)
        # Betrag Brutto
        set_spin_box_read_only(dialog.dsb_gross_amount, 0.0)
        # Steuerbetrag (Netto)
        set_spin_box_read_only(dialog.dsb_vat_amount, 0.0)
        hide_too_long = False  # hide too long line status
        if hide_too_long:
            # hide for too long line
            dialog.lbl_vat_amount.hide()
            dialog.dsb_vat_amount.hide()
            dialog.lbl_vat_amount_symbol.hide()
        # Grund (BT-97) (BT-104)
        dialog.le_reason.setText("")
        # Code des Grundes (BT-98) (BT-105)
        set_combo_box_items(dialog.cb_reason_code, "", reason_codes)

    def discount_price_changed(self, discount_index: int, percent_changed: bool) -> None:
        """!
        @brief Discount price changed
        @param discount_index : discount index
        @param percent_changed : True: percent changed; False: ne changed; None=other (use last changed)
        """
        if not self.lock_auto_price_edit:
            self.lock_auto_price_edit = True
            discount_dialog: Ui_InvoiceDiscountsData = self.ui_invoice_data.discounts_widgets[discount_index]

            if percent_changed is not None:
                self.discount_percent_changed[discount_index] = percent_changed

            basis_amount = discount_dialog.dsb_basis_amount.value()
            percent = discount_dialog.dsb_percent.value()
            net_amount = discount_dialog.dsb_net_amount.value()
            vat_rate = discount_dialog.dsb_vat_rate.value()

            if self.discount_percent_changed[discount_index]:
                net_amount = basis_amount * (percent / 100)
                discount_dialog.dsb_net_amount.setValue(net_amount)
            else:
                percent = (net_amount / basis_amount) * 100
                discount_dialog.dsb_percent.setValue(percent)
            gross_amount = net_amount * (1 + (vat_rate / 100))
            tax_amount = gross_amount - net_amount
            discount_dialog.dsb_gross_amount.setValue(gross_amount)
            discount_dialog.dsb_vat_amount.setValue(tax_amount)
            self.lock_auto_price_edit = False

        self.update_total_data()

    def surcharge_price_changed(self, surcharge_index: int, percent_changed: bool) -> None:
        """!
        @brief Surcharge price changed
        @param surcharge_index : discount index
        @param percent_changed : True: percent changed; False: ne changed; None=other (use last changed)
        """
        if not self.lock_auto_price_edit:
            self.lock_auto_price_edit = True
            surcharge_dialog: Ui_InvoiceSurchargesData = self.ui_invoice_data.surcharges_widgets[surcharge_index]

            if percent_changed is not None:
                self.surcharges_percent_changed[surcharge_index] = percent_changed

            basis_amount = surcharge_dialog.dsb_basis_amount.value()
            percent = surcharge_dialog.dsb_percent.value()
            net_amount = surcharge_dialog.dsb_net_amount.value()
            vat_rate = surcharge_dialog.dsb_vat_rate.value()

            if self.surcharges_percent_changed[surcharge_index]:
                net_amount = basis_amount * (percent / 100)
                surcharge_dialog.dsb_net_amount.setValue(net_amount)
            else:
                percent = (net_amount / basis_amount) * 100
                surcharge_dialog.dsb_percent.setValue(percent)
            gross_amount = net_amount * (1 + (vat_rate / 100))
            tax_amount = gross_amount - net_amount
            surcharge_dialog.dsb_gross_amount.setValue(gross_amount)
            surcharge_dialog.dsb_vat_amount.setValue(tax_amount)
            self.lock_auto_price_edit = False

        self.update_total_data()

    def update_item_expand_status(self, item_dialog: Ui_InvoiceItemData, b_visible: bool) -> None:
        """!
        @brief Update widgets for item expand status
        @param item_dialog : item dialog
        @param b_visible : visible status
        """
        # Steuerkategorie (BT-151)
        item_dialog.lbl_item_vat_code.setVisible(b_visible)
        item_dialog.cb_item_vat_code.setVisible(b_visible)
        # Artikel-Nr. (BT-155)
        item_dialog.lbl_item_id.setVisible(b_visible)
        item_dialog.le_item_id.setVisible(b_visible)
        # Startdatum (BT-134)
        item_dialog.lbl_item_billing_period_start.setVisible(b_visible)
        item_dialog.de_item_billing_period_start.setVisible(b_visible)
        # Enddatum (BT-135)
        item_dialog.lbl_item_billing_period_end.setVisible(b_visible)
        item_dialog.de_item_billing_period_end.setVisible(b_visible)
        # Set Date checkbox
        item_dialog.cb_item_billing_period.setVisible(b_visible)
        # Referenz zur Bestellposition (BT-132)
        item_dialog.lbl_item_order_position.setVisible(b_visible)
        item_dialog.le_item_order_position.setVisible(b_visible)
        # Objektkennung auf Ebene der Rechnungsposition (BT-128)
        item_dialog.lbl_object_reference.setVisible(b_visible)
        item_dialog.le_object_reference.setVisible(b_visible)
        # Basismenge zum Artikelpreis (BT-149)
        item_dialog.lbl_item_basis_quantity.setVisible(b_visible)
        item_dialog.dsb_item_basis_quantity.setVisible(b_visible)
        # Steuerbetrag
        item_dialog.lbl_item_vat_amount.setVisible(b_visible)
        item_dialog.dsb_item_vat_amount.setVisible(b_visible)
        item_dialog.lbl_item_vat_amount_symbol.setVisible(b_visible)
        # Gesamtpreis (Netto) (BT-131)
        item_dialog.lbl_item_net_amount.setVisible(b_visible)
        item_dialog.dsb_item_net_amount.setVisible(b_visible)
        item_dialog.lbl_item_net_amount_symbol.setVisible(b_visible)
        # Gesamtpreis (Brutto)
        item_dialog.lbl_item_gross_price.setVisible(b_visible)
        item_dialog.dsb_item_gross_price.setVisible(b_visible)
        item_dialog.lbl_item_gross_price_symbol.setVisible(b_visible)

    def set_default_tax_data(self, tax_dialog: Ui_InvoiceTaxData) -> None:
        """!
        @brief Set default tax data. Set only editable data
        @param tax_dialog : tax dialog
        """
        # Befreiungsgrund (BT-120)
        tax_dialog.le_exemption_reason.setText("")
        # Code für Befreiungsgrund (BT-121)
        set_combo_box_items(tax_dialog.cb_exemption_reason_code, "", D_EXEMPTION_REASON_CODE)

    def set_tax_data(self, tax_dialog: Ui_InvoiceTaxData, tax_data: dict[str, Any]) -> None:
        """!
        @brief Set default tax data. Set only editable data
        @param tax_dialog : tax dialog
        @param tax_data : tax data
        """
        # Steuerkategorie (BT-118)
        set_line_edit_read_only(tax_dialog.le_tax_category, tax_data["code"], D_VAT_CODE)
        # Steuersatz (BT-119)
        set_spin_box_read_only(tax_dialog.dsb_tax_rate, tax_data["rate"])
        # Gesamt (Netto) (BT-116)
        set_spin_box_read_only(tax_dialog.dsb_tax_net, tax_data["netAmount"])
        # Steuerbetrag (BT-117)
        set_spin_box_read_only(tax_dialog.dsb_tax_amount, tax_data["vatAmount"])
        # Gesamt (Brutto)
        set_spin_box_read_only(tax_dialog.dsb_tax_gross, tax_data["netAmount"] + tax_data["vatAmount"])
        b_visible = bool(tax_data["rate"] == 0)
        # Befreiungsgrund (BT-120)
        tax_dialog.lbl_exemption_reason.setVisible(b_visible)
        tax_dialog.le_exemption_reason.setVisible(b_visible)
        tax_dialog.le_exemption_reason.setText(tax_data["exemptionReason"])
        # Code für Befreiungsgrund (BT-121)
        tax_dialog.lbl_exemption_reason_code.setVisible(b_visible)
        tax_dialog.cb_exemption_reason_code.setVisible(b_visible)
        set_combo_box_value(tax_dialog.cb_exemption_reason_code, tax_data["exemptionReasonCode"], D_EXEMPTION_REASON_CODE)

    def update_tax_widget(self, invoice_data: dict[str, Any]) -> None:
        """!
        @brief Update tax widget
        @param invoice_data : invoice data
        """
        taxes_data = invoice_data.get("taxes", {})
        existing_widgets = len(self.ui_invoice_data.tax_widgets)
        required_widgets = len(taxes_data.items())

        for tax_index, (_tax_name, tax_data) in enumerate(taxes_data.items()):
            if len(self.ui_invoice_data.tax_widgets) <= tax_index:
                tax_dialog = Ui_InvoiceTaxData()  # new item instance
                widget = QWidget()  # new container widget
                tax_dialog.setupUi(widget)
                self.tax_layout.insertWidget(self.tax_layout.count(), widget)
                self.ui_invoice_data.tax_widgets.append(tax_dialog)  # store item ui for later use
                self.set_default_tax_data(tax_dialog)
            else:
                tax_dialog = self.ui_invoice_data.tax_widgets[tax_index]

            self.set_tax_data(tax_dialog, tax_data)

        widgets_to_delete = existing_widgets - required_widgets
        if widgets_to_delete > 0:
            for _i in range(widgets_to_delete):
                last_tax = self.ui_invoice_data.tax_widgets.pop()
                widget = last_tax.frame.parentWidget()
                self.tax_layout.removeWidget(widget)
                widget.setParent(None)

    def expand_mode_changed(self) -> None:
        """!
        @brief Update widgets for new expand status
        """
        b_visible = self.cb_extended.isChecked()

        dialog = self.ui_invoice_data
        # Rechnungstitel
        dialog.lbl_invoice_title.setVisible(b_visible)
        dialog.le_invoice_title.setVisible(b_visible)
        # Code für den Rechnungstyp (BT-3)
        dialog.lbl_invoice_type.setVisible(b_visible)
        dialog.cb_invoice_type.setVisible(b_visible)
        # Code für die Rechnungswährung (BT-5)
        dialog.lbl_currency.setVisible(b_visible)
        dialog.cb_currency.setVisible(b_visible)
        # Fälligkeitsdatum der Zahlung (BT-9)
        dialog.lbl_due_date.setVisible(b_visible)
        dialog.de_due_date.setVisible(b_visible)
        dialog.sb_due_days.setVisible(b_visible)
        dialog.lbl_due_days.setVisible(b_visible)
        # Käuferreferenz (BT-10)
        dialog.lbl_buyer_reference.setVisible(b_visible)
        dialog.le_buyer_reference.setVisible(b_visible)
        # Projektnummer (BT-11)
        dialog.lbl_project_number.setVisible(b_visible)
        dialog.le_project_number.setVisible(b_visible)
        # Vertragsnummer (BT-12)
        dialog.lbl_contract_number.setVisible(b_visible)
        dialog.le_contract_number.setVisible(b_visible)
        # Bestellnummer (BT-13)
        dialog.lbl_order_number.setVisible(b_visible)
        dialog.le_order_number.setVisible(b_visible)
        # Auftragsnummer (BT-14)
        dialog.lbl_assignment_number.setVisible(b_visible)
        dialog.le_assignment_number.setVisible(b_visible)
        # Wareneingangsmeldung (BT-15)
        dialog.lbl_receiving_advice_referenced_document.setVisible(b_visible)
        dialog.le_receiving_referenced_document.setVisible(b_visible)
        dialog.lbl_receiving_document_date.setVisible(b_visible)
        dialog.de_receiving_advice_referenced_document.setVisible(b_visible)
        # Versandanzeige (BT-16)
        dialog.lbl_despatch_advice_referenced_document.setVisible(b_visible)
        dialog.le_despatch_advice_referenced_document.setVisible(b_visible)
        dialog.lbl_despatch_advice_referenced_document_date.setVisible(b_visible)
        dialog.de_despatch_advice_referenced_document.setVisible(b_visible)
        # Ausschreibung/Los (BT-17)
        dialog.lbl_additional_referenced_document.setVisible(b_visible)
        dialog.le_additional_referenced_document.setVisible(b_visible)
        # Objektreferenz (BT-18)
        dialog.lbl_object_reference.setVisible(b_visible)
        dialog.le_object_reference.setVisible(b_visible)
        # Buchungskonto des Käufers (BT-19)
        dialog.lbl_booking_account_buyer.setVisible(b_visible)
        dialog.le_booking_account_buyer.setVisible(b_visible)
        # Rechnungsreferenz (BT-25, BT-26)
        dialog.lbl_invoice_reference.setVisible(b_visible)
        dialog.le_invoice_reference.setVisible(b_visible)
        dialog.lbl_invoice_reference_date.setVisible(b_visible)
        dialog.de_invoice_reference.setVisible(b_visible)
        # Einleitungstext
        dialog.lbl_introduction_text.setVisible(b_visible)
        dialog.pte_introduction_text.setVisible(b_visible)

        # Verkäufer
        dialog.groupBox_2_seller.setVisible(b_visible)

        # Käufer
        dialog.groupBox_3_buyer.setVisible(b_visible)

        # Zahlungsdetails
        dialog.groupBox_4_payment.setVisible(b_visible)

        # Lieferdetails
        dialog.groupBox_5_delivery.setVisible(b_visible)

        item_dialog: Ui_InvoiceItemData  # declare for typing
        for item_dialog in dialog.item_widgets:
            self.update_item_expand_status(item_dialog, b_visible)

        # Nachlässe
        dialog.groupBox_7_discounts.setVisible(False)  # TODO wenn Berechnung korrekt verwenden

        # Zuschläge
        dialog.groupBox_8_surcharges.setVisible(False)  # TODO wenn Berechnung korrekt verwenden

        # Steuern
        dialog.groupBox_9_tax.setVisible(b_visible)

        # Summe der Nettobeträge aller Rechnungspositionen (BT-106)
        dialog.lbl_sum_positions.setVisible(b_visible)
        dialog.dsb_sum_positions.setVisible(b_visible)
        dialog.lbl_sum_positions_symbol.setVisible(b_visible)
        # Summe der Zuschläge auf Dokumentenebene (BT-108)
        dialog.lbl_sum_surcharges.setVisible(b_visible)
        dialog.dsb_sum_surcharges.setVisible(b_visible)
        dialog.lbl_sum_surcharges_symbol.setVisible(b_visible)
        # Summe der Abschläge auf Dokumentenebene (BT-107)
        dialog.lbl_sum_discounts.setVisible(b_visible)
        dialog.dsb_sum_discounts.setVisible(b_visible)
        dialog.lbl_sum_discounts_symbol.setVisible(b_visible)
        # Vorauszahlungsbetrag (BT-113)
        dialog.lbl_payed_amount.setVisible(b_visible)
        dialog.dsb_payed_amount.setVisible(b_visible)
        dialog.lbl_payed_amount_symbol.setVisible(b_visible)
        # Rundungsbetrag (BT-114)
        dialog.lbl_rounded_amount.setVisible(b_visible)
        dialog.dsb_rounded_amount.setVisible(b_visible)
        dialog.lbl_rounded_amount_symbol.setVisible(b_visible)
        # Fälliger Zahlungsbetrag (BT-115)
        dialog.lbl_amount_due.setVisible(b_visible)
        dialog.dsb_amount_due.setVisible(b_visible)
        dialog.lbl_amount_due_symbol.setVisible(b_visible)

        self.update_total_data()  # required if basis quantity not 1

    def select_logo(self, fix_logo: Optional[str] = None) -> None:
        """!
        @brief Open file dialog to select logo and setup preview and path
        @param fix_logo : set fix logo file without dialog asking
        """
        if fix_logo is not None:
            logo_path = fix_logo
        else:
            logo_path, _ = QFileDialog.getOpenFileName(parent=self.ui, caption="Logo auswählen",
                                                       directory=self.ui.model.get_last_path(),
                                                       filter=IMAGE_FILE_TYPES)
        if logo_path:
            self.ui_invoice_data.lbl_seller_logo_path.setText(logo_path)
            pixmap = QPixmap(logo_path)
            self.ui_invoice_data.lbl_seller_logo_preview.setText("")
            self.ui_invoice_data.lbl_seller_logo_preview.setPixmap(pixmap)

    def contact_template_activated(self, _index: int) -> None:
        """!
        @brief Contact template was selected. Update Address field.
        @param _index : index of selected template entry
        """
        contact = self.cb_contact_template.currentData()
        self.customer = contact
        self.ui_invoice_data.le_buyer_company.setText(contact[EContactFields.NAME])  # Name des Käufers (BT-44) TODO textumbruch ermöglichen
        self.ui_invoice_data.le_buyer_name.setText(contact[EContactFields.TRADE_NAME])  # Handelsname (BT-45)
        self.ui_invoice_data.le_buyer_recognition.setText(contact[EContactFields.CUSTOMER_NUMBER])  # Käuferkennung (BT-46)
        self.ui_invoice_data.le_buyer_register_number.setText(contact[EContactFields.TRADE_ID])  # Registernummer (BT-47)
        self.ui_invoice_data.le_buyer_vat.setText(contact[EContactFields.VAT_ID])  # Umsatzsteuer-Identifikationsnummer des Käufers (BT-48)
        self.ui_invoice_data.le_buyer_electric_address.setText(contact[EContactFields.ELECTRONIC_ADDRESS])  # Elektronische Adresse (BT-49)
        contact_address = contact[CONTACT_ADDRESS_FIELD]  # address
        self.ui_invoice_data.le_buyer_street_1.setText(contact_address[EContactFields.STREET_1])  # Zeile 1 der Käuferanschrift (BT-50)
        self.ui_invoice_data.le_buyer_street_2.setText(contact_address[EContactFields.STREET_2])  # Zeile 2 der Käuferanschrift (BT-51)
        self.ui_invoice_data.le_buyer_plz.setText(contact_address[EContactFields.PLZ])  # Postleitzahl der Käuferanschrift (BT-53)
        self.ui_invoice_data.le_buyer_city.setText(contact_address[EContactFields.CITY])  # Stadt der Käuferanschrift (BT-52)
        self.ui_invoice_data.cb_buyer_country.setCurrentText(contact_address[EContactFields.COUNTRY])  # Ländercode der Käuferanschrift (BT-55)
        contact_contact = contact[CONTACT_CONTACT_FIELD]  # contact
        person = " ".join(filter(None, [contact_contact[EContactFields.FIRST_NAME], contact_contact[EContactFields.LAST_NAME]]))
        self.ui_invoice_data.le_buyer_contact_name.setText(person)  # Kontaktstelle des Käufers (BT-56)
        self.ui_invoice_data.le_buyer_contact_mail.setText(contact_contact[EContactFields.MAIL])  # E-Mail-Adresse der Kontaktstelle des Käufers (BT-58)
        self.ui_invoice_data.le_buyer_contact_phone.setText(contact_contact[EContactFields.PHONE])  # Telefonnummer der Kontaktstelle des Käufers (BT-57)

    def import_btn_clicked(self) -> None:
        """!
        @brief Import button clicked
        """
        s_file_name_path, _ = QFileDialog.getOpenFileName(parent=self.ui, caption="Öffnen",
                                                          directory=self.ui.model.get_last_path(),
                                                          filter=INVOICE_TEMPLATE_FILE_TYPES)
        if s_file_name_path:
            self.ui.model.set_last_path(os.path.dirname(s_file_name_path))
            _, file_extension = os.path.splitext(s_file_name_path)
            if file_extension in [JSON_TYPE, JSON_TYPE.upper()]:
                data = read_json_file(s_file_name_path)
                self.write_json_data_to_ui(data)
                self.ui.set_status("Rechnungsdaten importiert.")
            elif file_extension in [PDF_TYPE, PDF_TYPE.upper()]:
                if check_zugferd(s_file_name_path):
                    file_content = extract_xml_from_pdf(s_file_name_path)
                    data = convert_facturx_to_json(file_content)
                    self.write_json_data_to_ui(data)
                else:
                    self.ui.set_status("NUR ZUGFeRD PDF Dateien können importiert werden.", b_highlight=True)
            elif file_extension in [XML_TYPE, XML_TYPE.upper()]:
                if check_xinvoice(s_file_name_path):
                    file_content = extract_xml_from_xinvoice(s_file_name_path)
                    data = convert_facturx_to_json(file_content)
                    self.write_json_data_to_ui(data)
                else:
                    self.ui.set_status("Diese XML ist keine E-Rechnung.", b_highlight=True)
            else:
                self.ui.set_status("Dateityp nicht num Import geeignet.", b_highlight=True)

    def export_btn_clicked(self) -> None:
        """!
        @brief Export button clicked
        """
        default_filename = f"{__title__}-Rechnung{JSON_TYPE}"
        default_path = os.path.join(self.ui.model.get_last_path(), default_filename)
        s_file_name_path, _ = QFileDialog.getSaveFileName(parent=self.ui, caption="Speichern unter",
                                                          directory=default_path,
                                                          filter=JSON_FILE_TYPES)
        if s_file_name_path:
            self.ui.model.set_last_path(os.path.dirname(s_file_name_path))
            data = self.read_ui_data_to_json()
            fill_invoice_data(data)
            write_json_file(s_file_name_path, data)

    def on_invoice_data_changed(self, date: QDate) -> None:
        """!
        @brief Invoice Date changed. Update invoice number.
        @param date : date
        """
        self.due_date_changed(None)  # update due date
        # invoice number
        invoice_number = self.c_invoice_number.create_invoice_number(date)
        self.ui_invoice_data.le_invoice_number.setText(invoice_number)
        # invoice date
        currentDate = QDate.currentDate()
        if date != currentDate:
            self.ui_invoice_data.de_invoice_date.setStyleSheet("QDateEdit { background-color: red; }")
        else:
            self.ui_invoice_data.de_invoice_date.setStyleSheet("border: 1px solid palette(dark);")

    def due_date_changed(self, due_days_changed: None | bool) -> None:
        """!
        @brief Due date changed
        @param due_days_changed : changed object True=days False=date None=other (use last changed)
        """
        if not self.lock_due_date_edit:
            self.lock_due_date_edit = True
            dialog = self.ui_invoice_data

            if due_days_changed is not None:
                self.due_days_changed = due_days_changed

            due_date = dialog.de_due_date.date()
            due_days = dialog.sb_due_days.value()
            invoice_date = dialog.de_invoice_date.date()

            if self.due_days_changed:
                new_due_date = invoice_date.addDays(due_days)
                dialog.de_due_date.setDate(new_due_date)
            else:
                new_due_days = invoice_date.daysTo(due_date)
                dialog.sb_due_days.setValue(new_due_days)
            self.lock_due_date_edit = False

    def check_item_name(self) -> bool:
        """!
        @brief Check item name
        @return valid status
        """
        valid_item = True
        for item_dialog in self.ui_invoice_data.item_widgets:
            if not item_dialog.le_item_name.text():
                item_dialog.le_item_name.setStyleSheet("border: 2px solid red;")
                valid_item = False
                break
        return valid_item

    def create_invoice(self, e_invoice_option: EInvoiceOption) -> None:
        """!
        @brief Create invoice.
        @param e_invoice_option : invoice option
        """
        b_extended = self.cb_extended.isChecked()
        dialog = self.ui_invoice_data

        self.cb_contact_template.setStyleSheet("border: 1px solid palette(dark);")
        dialog.le_invoice_number.setStyleSheet("border: 1px solid palette(dark);")
        for item_dialog in dialog.item_widgets:
            item_dialog.le_item_name.setStyleSheet("border: 1px solid palette(dark);")
        dialog.le_seller_company.setStyleSheet("border: 1px solid palette(dark);")

        if not b_extended and self.customer is None:  # TODO bei Extended weitere Pflichtfelder prüfen
            self.cb_contact_template.setStyleSheet("border: 2px solid red;")
            self.ui.set_status("Kein Kunde ausgewählt.", b_highlight=True)
        elif not dialog.le_invoice_number.text():
            dialog.le_invoice_number.setStyleSheet("border: 2px solid red;")
            self.ui.set_status("Keine Rechnungsnummer vorhanden.", b_highlight=True)
        elif not self.check_item_name():
            # border for first missing item name was set in function
            self.ui.set_status("Kein Artikelname vorhanden.", b_highlight=True)
        elif b_extended and not dialog.le_seller_company.text():
            dialog.le_seller_company.setStyleSheet("border: 2px solid red;")
            self.ui.set_status("Kein Name des Rechnungsstellers", b_highlight=True)
        else:
            invoice_data = self.read_ui_data_to_json()
            write_invoice_option(e_invoice_option)
            create_qr_code = self.cb_qr_code.isChecked()
            write_qr_code_settings(create_qr_code)
            custom_invoice = False
            if not custom_invoice:
                plugin = try_load_plugin("custom_invoice", "plugins/custom_invoice.py")
                if plugin and hasattr(plugin, "create_custom_invoice"):
                    func = plugin.create_custom_invoice
                    if function_accepts_params(func, invoice_data, e_invoice_option, create_qr_code):
                        func(invoice_data, e_invoice_option, create_qr_code)
                        custom_invoice = True
                    else:
                        QMessageBox.warning(self, "Plugin Hinweis", "Dein verwendetes Plugin wird nicht mehr unterstützt.\nEine Rechnung im Standardformat wird erstellt!")
            if not custom_invoice:
                create_general_invoice(invoice_data, e_invoice_option, create_qr_code)
            self.close()

    def read_ui_data_to_json(self) -> dict[str, Any]:
        """!
        @brief Visualize xml invoice in dialog.
        @return invoice json file in PDF24 Format (D_DEFAULT_INVOICE_DATA)
        """
        b_extended = self.cb_extended.isChecked()

        dialog = self.ui_invoice_data
        data = {}
        data["title"] = dialog.le_invoice_title.text() if b_extended else ""  # Rechnungstitel
        data["number"] = dialog.le_invoice_number.text()  # Rechnungsnummer (BT-1)
        q_invoice_date = dialog.de_invoice_date.date()
        data["issueDate"] = q_invoice_date.toString(DATE_FORMAT_XINVOICE)  # Rechnungsdatum (BT-2)
        data["typeCode"] = dialog.cb_invoice_type.currentData() if b_extended else "380"  # Code für den Rechnungstyp (BT-3)
        data["currencyCode"] = dialog.cb_currency.currentData() if b_extended else "EUR"  # Code für die Rechnungswährung (BT-5)
        if b_extended:
            data["dueDate"] = dialog.de_due_date.date().toString(DATE_FORMAT_XINVOICE)  # Fälligkeitsdatum der Zahlung (BT-9)
        else:
            q_due_date = q_invoice_date.addDays(self.default_payment_days)
            data["dueDate"] = q_due_date.toString(DATE_FORMAT_XINVOICE)
        data["deliveryDate"] = dialog.de_deliver_date.date().toString(DATE_FORMAT_XINVOICE)  # Tatsächliches Lieferdatum (BT-72)
        data["billingPeriodStartDate"] = dialog.de_accounting_date_from.date().toString(DATE_FORMAT_XINVOICE) if dialog.cb_accounting_date.isChecked() else ""  # Anfangsdatum des Rechnungszeitraums (BT-73)
        data["billingPeriodEndDate"] = dialog.de_accounting_date_to.date().toString(DATE_FORMAT_XINVOICE) if dialog.cb_accounting_date.isChecked() else ""  # Enddatum des Rechnungszeitraums (BT-74)
        data["buyerReference"] = dialog.le_buyer_reference.text() if b_extended else ""  # Käuferreferenz (BT-10)
        data["projectReference"] = dialog.le_project_number.text() if b_extended else ""  # Projektnummer (BT-11)
        data["contractReference"] = dialog.le_contract_number.text() if b_extended else ""  # Vertragsnummer (BT-12)
        data["purchaseOrderReference"] = dialog.le_order_number.text() if b_extended else ""  # Bestellnummer (BT-13)
        data["salesOrderReference"] = dialog.le_assignment_number.text() if b_extended else ""  # Auftragsnummer (BT-14)
        if b_extended:
            # Wareneingangsmeldung (BT-15)
            data_receiving_advice_reference = data.setdefault("receivingAdviceReference", {})
            data_receiving_advice_reference["id"] = dialog.le_receiving_referenced_document.text()
            data_receiving_advice_reference["issueDate"] = dialog.de_receiving_advice_referenced_document.date().toString(DATE_FORMAT_XINVOICE)
            # Versandanzeige (BT-16)
            data_despatch_advice_reference = data.setdefault("despatchAdviceReference", {})
            data_despatch_advice_reference["id"] = dialog.le_despatch_advice_referenced_document.text()
            data_despatch_advice_reference["issueDate"] = dialog.de_despatch_advice_referenced_document.date().toString(DATE_FORMAT_XINVOICE)
            # Ausschreibung/Los (BT-17)
            data_tender_references = data.setdefault("tenderReferences", [])
            reference = {}
            reference["id"] = dialog.le_additional_referenced_document.text()
            reference["typeCode"] = "50"
            data_tender_references.append(reference)
            # Objektreferenz (BT-18)
            data_object_references = data.setdefault("objectReferences", [])
            reference = {}
            reference["id"] = dialog.le_object_reference.text()
            reference["typeCode"] = "130"
            data_object_references.append(reference)
            # Buchungskonto des Käufers (BT-19)
            data_buyer_accounting_accounts = data.setdefault("buyerAccountingAccounts", [])
            data_account = {}
            data_account["id"] = dialog.le_booking_account_buyer.text()
            data_buyer_accounting_accounts.append(data_account)
            # Rechnungsreferenz (BT-25, BT-26)
            data_invoice_references = data.setdefault("invoiceReferences", [])
            data_invoice = {}
            data_invoice["id"] = dialog.le_invoice_reference.text()  # ID (BT-25)
            data_invoice["issueDate"] = dialog.de_invoice_reference.date().toString(DATE_FORMAT_XINVOICE)  # Datum (BT-26)
            data_invoice_references.append(data_invoice)
        # Freitext zur Rechnung (BT-22)
        data["note"] = dialog.pte_note.toPlainText()
        # Einleitungstext
        data["introText"] = dialog.pte_introduction_text.toPlainText() if b_extended else ""

        if b_extended:
            data_seller = data.setdefault("seller", {})
            data_seller["name"] = dialog.le_seller_company.text()  # Name des Verkäufers (BT-27)
            data_seller["tradeName"] = dialog.le_seller_name.text()  # Handelsname (BT-28)
            data_seller["id"] = dialog.le_seller_recognition.text()  # Verkäuferkennung (BT-29)
            data_seller["tradeId"] = dialog.le_seller_register_number.text()  # Registernummer (BT-30)
            data_seller["vatId"] = dialog.le_seller_vat.text()  # Umsatzsteuer-Identifikationsnummer des Verkäufers (BT-31)
            data_seller["taxId"] = dialog.le_seller_tax_number.text()  # Steuernummer des Verkäufers (BT-32)
            data_seller["weeeId"] = dialog.le_seller_weee_number.text()  # WEEE-Nummer
            data_seller["legalInfo"] = dialog.pte_seller_law_info.toPlainText()  # Rechtliche Informationen (BT-33)
            data_seller["electronicAddress"] = dialog.le_seller_electric_address.text()  # seller electric address (BT-34)
            data_seller["websiteText"] = dialog.le_seller_website.text()  # Webseite
            data_seller_address = data_seller.setdefault("address", {})
            data_seller_address["line1"] = dialog.le_seller_street_1.text()  # Zeile 1 der Verkäuferanschrift (BT-35)
            data_seller_address["line2"] = dialog.le_seller_street_2.text()  # Zeile 2 der Verkäuferanschrift (BT-36)
            data_seller_address["postCode"] = dialog.le_seller_plz.text()  # Postleitzahl der Verkäuferanschrift (BT-38)
            data_seller_address["city"] = dialog.le_seller_city.text()  # Stadt der Verkäuferanschrift (BT-37)
            data_seller_address["countryCode"] = dialog.cb_seller_country.currentData()  # Ländercode der Verkäuferanschrift (BT-40)
            data_seller_contact = data_seller.setdefault("contact", {})
            data_seller_contact["name"] = dialog.le_seller_contact_name.text()  # Kontaktstelle des Verkäufers (BT-41)
            data_seller_contact["email"] = dialog.le_seller_contact_mail.text()  # E-Mail-Adresse der Kontaktstelle des Verkäufers (BT-43)
            data_seller_contact["phone"] = dialog.le_seller_contact_phone.text()  # Telefonnummer der Kontaktstelle des Verkäufers (BT-42)
            data_seller_contact["fax"] = dialog.le_seller_contact_fax.hide()  # Fax
            data_seller["logoData"] = dialog.lbl_seller_logo_path.text()  # Logo Pfad
        else:
            logo_path = os.path.join(self.ui.model.data_path, LOGO_BRIEF_PATH)
            write_company_to_json(data, self.ui.tab_settings.company_data, logo_path=logo_path)

        if b_extended:
            data_buyer = data.setdefault("buyer", {})
            data_buyer["name"] = dialog.le_buyer_company.text()  # Name des Käufers (BT-44)
            data_buyer["tradeName"] = dialog.le_buyer_name.text()  # Handelsname (BT-45)
            data_buyer["id"] = dialog.le_buyer_recognition.text()  # Käuferkennung (BT-46)
            data_buyer["tradeId"] = dialog.le_buyer_register_number.text()  # Registernummer (BT-47)
            data_buyer["vatId"] = dialog.le_buyer_vat.text()  # Umsatzsteuer-Identifikationsnummer des Käufers (BT-48)
            data_buyer["electronicAddress"] = dialog.le_buyer_electric_address.text()  # Elektronische Adresse (BT-49)
            data_buyer_address = data_buyer.setdefault("address", {})
            data_buyer_address["line1"] = dialog.le_buyer_street_1.text()  # Zeile 1 der Käuferanschrift (BT-50)
            data_buyer_address["line2"] = dialog.le_buyer_street_2.text()  # Zeile 2 der Käuferanschrift (BT-51)
            data_buyer_address["postCode"] = dialog.le_buyer_plz.text()  # Postleitzahl der Käuferanschrift (BT-53)
            data_buyer_address["city"] = dialog.le_buyer_city.text()  # Stadt der Käuferanschrift (BT-52)
            data_buyer_address["countryCode"] = dialog.cb_buyer_country.currentData()  # Ländercode der Käuferanschrift (BT-55)
            data_buyer_contact = data_buyer.setdefault("contact", {})
            data_buyer_contact["name"] = dialog.le_buyer_contact_name.text()  # Kontaktstelle des Käufers (BT-56)
            data_buyer_contact["email"] = dialog.le_buyer_contact_mail.text()  # E-Mail-Adresse der Kontaktstelle des Käufers (BT-58)
            data_buyer_contact["phone"] = dialog.le_buyer_contact_phone.text()  # Telefonnummer der Kontaktstelle des Käufers (BT-57)
        else:
            write_customer_to_json(data, self.customer)

        data_payment = data.setdefault("payment", {})
        if b_extended:
            data_payment_methods = data_payment.setdefault("methods", [])
            data_payment_method = {}
            data_payment_method["typeCode"] = dialog.cb_payment_method.currentData()  # Code für die Zahlungsart D_PAYMENT_METHOD (BT-81)
            data_payment_method["accountName"] = dialog.le_account_holder.text()  # Name des Zahlungskontos (BT-85)
            data_payment_method["iban"] = dialog.le_iban.text()  # Kennung des Zahlungskontos (BT-84)
            data_payment_method["bic"] = dialog.le_bic.text()  # Kennung des Zahlungsdienstleisters (BT-86)
            data_payment_method["bankName"] = dialog.le_bank_name.text()  # Name der Bank
            data_payment_methods.append(data_payment_method)
        data_payment["reference"] = dialog.le_payment_purpose.text()  # Verwendungszweck (BT-83)
        data_payment["terms"] = dialog.pte_payment_terms.toPlainText()  # Zahlungsbedingungen (BT-20)

        if b_extended:
            data_delivery = data.setdefault("delivery", {})
            data_delivery["recipientName"] = dialog.le_deliver_name.text()  # Name des Waren- oder Dienstleistungsempfängers (BT-70)
            data_delivery["locationId"] = dialog.le_deliver_place_ident.text()  # Kennung des Lieferorts (BT-71)
            data_delivery_address = data_delivery.setdefault("address", {})
            data_delivery_address["line1"] = dialog.le_deliver_street_1.text()  # Zeile 1 der Lieferanschrift (BT-75)
            data_delivery_address["line2"] = dialog.le_deliver_street_2.text()  # Zeile 2 der Lieferanschrift (BT-76)
            data_delivery_address["line3"] = dialog.le_deliver_addition.text()  # Zeile 3 der Lieferanschrift (BT-165)
            data_delivery_address["postCode"] = dialog.le_deliver_plz.text()  # Postleitzahl der Lieferanschrift (BT-78)
            deliver_city = dialog.le_deliver_city.text()
            data_delivery_address["city"] = deliver_city  # Stadt der Lieferanschrift (BT-77)
            if deliver_city:  # set only country if city present
                data_delivery_address["countryCode"] = dialog.cb_deliver_country.currentData()  # Ländercode der Lieferanschrift (BT-80)
            else:
                data_delivery_address["countryCode"] = ""
            data_delivery_address["region"] = dialog.le_deliver_region.text()  # Stadt der Lieferanschrift (BT-79)

        # position
        data_items = data.setdefault("items", [])
        data_taxes = data.setdefault("taxes", {})
        for _item_pos, item_dialog in enumerate(dialog.item_widgets):
            data_item = {}
            data_item["name"] = item_dialog.le_item_name.text()  # Name (BT-153)
            vat_rate = item_dialog.dsb_item_vat_rate.value()  # Umsatzsteuersatz für den in Rechnung gestellten Artikel (BT-152)
            data_item["vatRate"] = vat_rate
            vat_code = item_dialog.cb_item_vat_code.currentData() if b_extended else "S"  # Code der Umsatzsteuerkategorie des in Rechnung gestellten Artikels (BT-151)
            data_item["vatCode"] = vat_code
            data_item["id"] = item_dialog.le_item_id.text() if b_extended else ""  # Artikel-Nr. (BT-155)
            b_use_date = b_extended and item_dialog.cb_item_billing_period.isChecked()
            data_item["billingPeriodStart"] = item_dialog.de_item_billing_period_start.date().toString(DATE_FORMAT_XINVOICE) if b_use_date else ""  # Startdatum (BT-134)
            data_item["billingPeriodEnd"] = item_dialog.de_item_billing_period_end.date().toString(DATE_FORMAT_XINVOICE) if b_use_date else ""  # Enddatum (BT-135)
            data_item["orderPosition"] = item_dialog.le_item_order_position.text() if b_extended else ""  # Referenz zur Bestellposition (BT-132)
            object_references = item_dialog.le_object_reference.text() if b_extended else ""  # Objektkennung auf Ebene der Rechnungsposition (BT-128)
            if object_references:
                data_object_references = data_item.setdefault("objectReferences", [])
                reference = {}
                reference["id"] = object_references
                reference["typeCode"] = "130"
                data_object_references.append(reference)
            data_item["description"] = item_dialog.pte_item_description.toPlainText()  # Artikelbeschreibung (BT-154)
            data_item["quantity"] = item_dialog.dsb_item_quantity.value()  # Menge (BT-129)
            data_item["quantityUnit"] = item_dialog.cb_item_quantity_unit.currentData()  # Einheit (BT-130) D_UNIT
            data_item["netUnitPrice"] = item_dialog.dsb_item_net_unit_price.value()  # Einzelpreis (Netto) (BT-146)
            data_item["basisQuantity"] = item_dialog.dsb_item_basis_quantity.value() if b_extended else 1  # Basismenge zum Artikelpreis (BT-149)
            data_items.append(data_item)
            if b_extended:
                # Steuern
                vat_rate_normalized = normalize_decimal(vat_rate)
                vat_key = f"{vat_code}-{vat_rate_normalized}"
                if vat_key not in data_taxes:
                    tax_widget = dialog.tax_widgets[len(data_taxes) - 1]
                    vat_value = {
                        "exemptionReason": tax_widget.le_exemption_reason.text(),  # Befreiungsgrund (BT-120)
                        "exemptionReasonCode": tax_widget.cb_exemption_reason_code.currentData()  # Code für Befreiungsgrund (BT-121)
                    }
                    data_taxes[vat_key] = vat_value

        if b_extended:
            # Nachlässe
            data_allowances = data.setdefault("allowances", [])
            for allowance_dialog in dialog.discounts_widgets:
                data_allowance = {}
                data_allowance["basisAmount"] = allowance_dialog.dsb_basis_amount.value()  # Grundbetrag (BT-93)
                data_allowance["netAmount"] = allowance_dialog.dsb_net_amount.value()  # Betrag (Netto) (BT-92)
                data_allowance["percent"] = allowance_dialog.dsb_percent.value()  # Prozent (BT-94)
                data_allowance["reason"] = allowance_dialog.le_reason.text()  # Grund (BT-97)
                data_allowance["reasonCode"] = allowance_dialog.cb_reason_code.currentData()  # Code des Grundes (BT-98)
                data_allowance["vatCode"] = allowance_dialog.cb_vat_code.currentData()  # Steuerkategorie (BT-95)
                data_allowance["vatRate"] = allowance_dialog.dsb_vat_rate.value()  # Steuersatz (BT-96)
                data_allowances.append(data_allowance)
            # Zuschläge
            data_charges = data.setdefault("charges", [])
            for charge_dialog in dialog.surcharges_widgets:
                data_charge = {}
                data_charge["basisAmount"] = charge_dialog.dsb_basis_amount.value()  # Grundbetrag (BT-100)
                data_charge["netAmount"] = charge_dialog.dsb_net_amount.value()  # Betrag (Netto) (BT-99)
                data_charge["percent"] = charge_dialog.dsb_percent.value()  # Prozent (BT-101)
                data_charge["reason"] = charge_dialog.le_reason.text()  # Grund (BT-104)
                data_charge["reasonCode"] = charge_dialog.cb_reason_code.currentData()  # Code des Grundes (BT-105)
                data_charge["vatCode"] = charge_dialog.cb_vat_code.currentData()  # Steuerkategorie (BT-102)
                data_charge["vatRate"] = charge_dialog.dsb_vat_rate.value()  # Steuersatz (BT-103)
                data_charges.append(data_charge)

        # Gesamtsummen (nur die Eingaben der Rest wird errechnet)
        data_totals = data.setdefault("totals", {})
        data_totals["paidAmount"] = dialog.dsb_payed_amount.value() if b_extended else 0  # Vorauszahlungsbetrag (BT-113)
        data_totals["roundingAmount"] = dialog.dsb_rounded_amount.value() if b_extended else 0  # Rundungsbetrag (BT-114)

        return data

    def write_json_data_to_ui(self, data: dict[str, Any], import_all: bool = False):
        """!
        @brief Write JSON data to UI
        @param data : JSON data
        @param import_all : import all
        """
        dialog = self.ui_invoice_data
        dialog.le_invoice_title.setText(data.get("title"))  # Rechnungstitel
        if import_all:
            dialog.le_invoice_number.setText(data.get("number"))  # Rechnungsnummer (BT-1)
            # Rechnungsdatum (BT-2)
            invoice_date = data.get("issueDate")
            if invoice_date:
                invoice_date_datetime = datetime.strptime(str(invoice_date), DATE_FORMAT_XML)
                qdate = QDate(invoice_date_datetime.year, invoice_date_datetime.month, invoice_date_datetime.day)
                dialog.de_invoice_date.setDate(qdate)
        # Code für den Rechnungstyp (BT-3)
        set_combo_box_value(dialog.cb_invoice_type, data.get("typeCode"), D_INVOICE_TYPE)
        # Code für die Rechnungswährung (BT-5)
        set_combo_box_value(dialog.cb_currency, data.get("currencyCode"), D_CURRENCY)
        if import_all:
            # Fälligkeitsdatum der Zahlung (BT-9)
            due_date = data.get("dueDate")
            if due_date:
                due_date_datetime = datetime.strptime(str(due_date), DATE_FORMAT_XML)
                qdate = QDate(due_date_datetime.year, due_date_datetime.month, due_date_datetime.day)
                dialog.de_due_date.setDate(qdate)
            # Tatsächliches Lieferdatum (BT-72)
            deliver_date = data.get("deliveryDate")
            if deliver_date:
                deliver_date_datetime = datetime.strptime(str(deliver_date), DATE_FORMAT_XML)
                qdate = QDate(deliver_date_datetime.year, deliver_date_datetime.month, deliver_date_datetime.day)
                dialog.de_deliver_date.setDate(qdate)
            # Anfangsdatum des Rechnungszeitraums (BT-73)
            accounting_period_start = data.get("billingPeriodStartDate")
            if accounting_period_start:
                accounting_period_start_datetime = datetime.strptime(str(accounting_period_start), DATE_FORMAT_XML)
                qdate = QDate(accounting_period_start_datetime.year, accounting_period_start_datetime.month, accounting_period_start_datetime.day)
                dialog.de_accounting_date_from.setDate(qdate)
            # Enddatum des Rechnungszeitraums (BT-74)
            accounting_period_end = data.get("billingPeriodEndDate")
            if accounting_period_end:
                accounting_period_end_datetime = datetime.strptime(str(accounting_period_end), DATE_FORMAT_XML)
                qdate = QDate(accounting_period_end_datetime.year, accounting_period_end_datetime.month, accounting_period_end_datetime.day)
                dialog.de_accounting_date_to.setDate(qdate)
            self.ui_invoice_data.cb_accounting_date.setChecked(bool(accounting_period_start or accounting_period_end))
            dialog.le_buyer_reference.setText(data.get("buyerReference", ""))  # Käuferreferenz (BT-10)
            dialog.le_project_number.setText(data.get("projectReference", ""))  # Projektnummer (BT-11)
            dialog.le_contract_number.setText(data.get("contractReference", ""))  # Vertragsnummer (BT-12)
            dialog.le_order_number.setText(data.get("purchaseOrderReference", ""))  # Bestellnummer (BT-13)
            dialog.le_assignment_number.setText(data.get("salesOrderReference", ""))  # Auftragsnummer (BT-14)
        # Wareneingangsmeldung (BT-15)
        receiving_advice_reference = data.get("receivingAdviceReference")
        if receiving_advice_reference:
            dialog.le_receiving_referenced_document.setText(receiving_advice_reference.get("id", ""))
            receiving_advice_reference_date = receiving_advice_reference.get("issueDate")
            if receiving_advice_reference_date:
                receiving_advice_reference_date_datetime = datetime.strptime(str(receiving_advice_reference_date), DATE_FORMAT_XML)
                qdate = QDate(receiving_advice_reference_date_datetime.year, receiving_advice_reference_date_datetime.month, receiving_advice_reference_date_datetime.day)
                dialog.de_receiving_advice_referenced_document.setDate(qdate)
        else:
            dialog.le_receiving_referenced_document.setText("")
        # Versandanzeige (BT-16)
        despatch_advice_reference = data.get("despatchAdviceReference")
        if despatch_advice_reference:
            dialog.le_despatch_advice_referenced_document.setText(despatch_advice_reference.get("id", ""))
            despatch_advice_reference_date = despatch_advice_reference.get("issueDate")
            if despatch_advice_reference_date:
                despatch_advice_reference_date_datetime = datetime.strptime(str(despatch_advice_reference_date), DATE_FORMAT_XML)
                qdate = QDate(despatch_advice_reference_date_datetime.year, despatch_advice_reference_date_datetime.month, despatch_advice_reference_date_datetime.day)
                dialog.de_despatch_advice_referenced_document.setDate(qdate)
        else:
            dialog.le_despatch_advice_referenced_document.setText("")
        # Ausschreibung/Los (BT-17)
        tender_references = data.get("tenderReferences", [])
        if len(tender_references) > 0:
            dialog.le_additional_referenced_document.setText(tender_references[0].get("id", ""))
        else:
            dialog.le_additional_referenced_document.setText("")
        # Objektreferenz (BT-18)
        object_references = data.get("objectReferences", [])
        if len(object_references) > 0:
            dialog.le_object_reference.setText(object_references[0].get("id", ""))
        else:
            dialog.le_object_reference.setText("")
        # Buchungskonto des Käufers (BT-19)
        buyer_accounting_accounts = data.get("buyerAccountingAccounts", [])
        if len(buyer_accounting_accounts) > 0:
            dialog.le_booking_account_buyer.setText(buyer_accounting_accounts[0].get("id", ""))
        else:
            dialog.le_booking_account_buyer.setText("")
        # Rechnungsreferenz (BT-25, BT-26)
        invoice_references = data.get("invoiceReferences", [])
        if len(invoice_references) > 0:
            dialog.le_invoice_reference.setText(invoice_references[0].get("id", ""))
            invoice_references_date = invoice_references[0].get("issueDate")
            if invoice_references_date:
                invoice_references_date_datetime = datetime.strptime(str(invoice_references_date), DATE_FORMAT_XML)
                qdate = QDate(invoice_references_date_datetime.year, invoice_references_date_datetime.month, invoice_references_date_datetime.day)
                dialog.de_invoice_reference.setDate(qdate)
        else:
            dialog.le_invoice_reference.setText("")
        dialog.pte_note.setPlainText(data.get("note", ""))  # Bemerkung (BT-22)
        dialog.pte_introduction_text.setPlainText(data.get("introText", ""))  # Einleitungstext

        data_seller = data.setdefault("seller", {})
        dialog.le_seller_company.setText(data_seller.get("name", ""))  # Name des Verkäufers (BT-27)
        dialog.le_seller_name.setText(data_seller.get("tradeName", ""))  # Handelsname (BT-28)
        dialog.le_seller_recognition.setText(data_seller.get("id", ""))  # Verkäuferkennung (BT-29)
        dialog.le_seller_register_number.setText(data_seller.get("tradeId", ""))  # Registernummer (BT-30)
        dialog.le_seller_vat.setText(data_seller.get("vatId", ""))  # Umsatzsteuer-Identifikationsnummer des Verkäufers (BT-31)
        dialog.le_seller_tax_number.setText(data_seller.get("taxId", ""))  # Steuernummer des Verkäufers (BT-32)
        dialog.le_seller_weee_number.setText(data_seller.get("weeeId", ""))  # WEEE-Nummer
        dialog.pte_seller_law_info.setPlainText(data_seller.get("legalInfo", ""))  # Rechtliche Informationen (BT-33)
        dialog.le_seller_electric_address.setText(data_seller.get("electronicAddress", ""))  # seller electric address (BT-34)
        dialog.le_seller_website.setText(data_seller.get("websiteText", ""))  # Webseite
        data_seller_address = data_seller.setdefault("address", {})
        dialog.le_seller_street_1.setText(data_seller_address.get("line1", ""))  # Zeile 1 der Verkäuferanschrift (BT-35)
        dialog.le_seller_street_2.setText(data_seller_address.get("line2", ""))  # Zeile 2 der Verkäuferanschrift (BT-36)
        dialog.le_seller_plz.setText(data_seller_address.get("postCode", ""))  # Postleitzahl der Verkäuferanschrift (BT-38)
        dialog.le_seller_city.setText(data_seller_address.get("city", ""))  # Stadt der Verkäuferanschrift (BT-37)
        # Ländercode der Verkäuferanschrift (BT-40)
        set_combo_box_value(dialog.cb_seller_country, data_seller_address.get("countryCode"), D_COUNTRY_CODE)
        data_seller_contact = data_seller.setdefault("contact", {})
        dialog.le_seller_contact_name.setText(data_seller_contact.get("name", ""))  # Kontaktstelle des Verkäufers (BT-41)
        dialog.le_seller_contact_mail.setText(data_seller_contact.get("email", ""))  # E-Mail-Adresse der Kontaktstelle des Verkäufers (BT-43)
        dialog.le_seller_contact_phone.setText(data_seller_contact.get("phone", ""))  # Telefonnummer der Kontaktstelle des Verkäufers (BT-42)
        dialog.le_seller_contact_fax.setText(data_seller_contact.get("fax", ""))  # seller fax
        self.select_logo(data_seller.get("logoData", ""))  # seller logo

        data_buyer = data.setdefault("buyer", {})
        dialog.le_buyer_company.setText(data_buyer.get("name", ""))  # Name des Käufers (BT-44)
        dialog.le_buyer_name.setText(data_buyer.get("tradeName", ""))  # Handelsname (BT-45)
        dialog.le_buyer_recognition.setText(data_buyer.get("id", ""))  # Käuferkennung (BT-46)
        dialog.le_buyer_register_number.setText(data_buyer.get("tradeId", ""))  # Registernummer (BT-47)
        dialog.le_buyer_vat.setText(data_buyer.get("vatId", ""))  # Umsatzsteuer-Identifikationsnummer des Käufers (BT-48)
        dialog.le_buyer_electric_address.setText(data_buyer.get("electronicAddress", ""))  # Elektronische Adresse (BT-49)
        data_buyer_address = data_buyer.setdefault("address", {})
        dialog.le_buyer_street_1.setText(data_buyer_address.get("line1", ""))  # Zeile 1 der Käuferanschrift (BT-50)
        dialog.le_buyer_street_2.setText(data_buyer_address.get("line2", ""))  # Zeile 2 der Käuferanschrift (BT-51)
        dialog.le_buyer_plz.setText(data_buyer_address.get("postCode", ""))  # Postleitzahl der Käuferanschrift (BT-53)
        dialog.le_buyer_city.setText(data_buyer_address.get("city", ""))  # Stadt der Käuferanschrift (BT-52)
        # Ländercode der Käuferanschrift (BT-55)
        set_combo_box_value(dialog.cb_buyer_country, data_buyer_address.get("countryCode"), D_COUNTRY_CODE)
        data_buyer_contact = data_buyer.setdefault("contact", {})
        dialog.le_buyer_contact_name.setText(data_buyer_contact.get("name", ""))  # Kontaktstelle des Käufers (BT-56)
        dialog.le_buyer_contact_mail.setText(data_buyer_contact.get("email", ""))  # E-Mail-Adresse der Kontaktstelle des Käufers (BT-58)
        dialog.le_buyer_contact_phone.setText(data_buyer_contact.get("phone", ""))  # Telefonnummer der Kontaktstelle des Käufers (BT-57)

        data_payment = data.setdefault("payment", {})
        data_payment_methods = data_payment.setdefault("methods", [])
        data_payment_method = data_payment_methods[0] if (len(data_payment_methods) > 0) else {}
        # Code für die Zahlungsart D_PAYMENT_METHOD (BT-81)
        set_combo_box_value(dialog.cb_payment_method, data_payment_method.get("typeCode"), D_PAYMENT_METHOD)
        dialog.le_account_holder.setText(data_payment_method.get("accountName", ""))  # Name des Zahlungskontos (BT-85)
        dialog.le_iban.setText(data_payment_method.get("iban", ""))  # Kennung des Zahlungskontos (BT-84)
        dialog.le_bic.setText(data_payment_method.get("bic", ""))  # Kennung des Zahlungsdienstleisters (BT-86)
        dialog.le_bank_name.setText(data_payment_method.get("bankName", ""))  # bank name
        dialog.le_payment_purpose.setText(data_payment.get("reference", ""))  # Verwendungszweck (BT-83)
        dialog.pte_payment_terms.setPlainText(data_payment.get("terms", ""))  # Zahlungsbedingungen (BT-20)

        data_delivery = data.setdefault("delivery", {})
        dialog.le_deliver_name.setText(data_delivery.get("recipientName", ""))  # Name des Waren- oder Dienstleistungsempfängers (BT-70)
        dialog.le_deliver_place_ident.setText(data_delivery.get("locationId", ""))  # Kennung des Lieferorts (BT-71)
        data_delivery_address = data_delivery.setdefault("address", {})
        dialog.le_deliver_street_1.setText(data_delivery_address.get("line1", ""))  # Zeile 1 der Lieferanschrift (BT-75)
        dialog.le_deliver_street_2.setText(data_delivery_address.get("line2", ""))  # Zeile 2 der Lieferanschrift (BT-76)
        dialog.le_deliver_addition.setText(data_delivery_address.get("line3", ""))  # Zeile 3 der Lieferanschrift (BT-165)
        dialog.le_deliver_plz.setText(data_delivery_address.get("postCode", ""))  # Postleitzahl der Lieferanschrift (BT-78)
        dialog.le_deliver_city.setText(data_delivery_address.get("city", ""))  # Stadt der Lieferanschrift (BT-77)
        # Ländercode der Lieferanschrift (BT-80)
        set_combo_box_value(dialog.cb_deliver_country, data_delivery_address.get("countryCode"), D_COUNTRY_CODE)
        dialog.le_deliver_region.setText(data_delivery_address.get("region", ""))  # Stadt der Lieferanschrift (BT-79)
        # remove additional existing items
        existing_items = len(self.ui_invoice_data.item_widgets)
        if existing_items > 1:
            for _i in range(existing_items - 1):
                self.remove_item()

        for item_idx, data_item in enumerate(data.setdefault("items", [])):  # TODO wenn schon vorhanden alte Löschen auch bei Zuschläge und Nachlass
            if item_idx > 0:  # add additional item widget before
                self.add_item()
            item_dialog: Ui_InvoiceItemData = dialog.item_widgets[item_idx]
            item_dialog.le_item_name.setText(data_item.get("name", ""))  # Name (BT-153)
            item_dialog.dsb_item_vat_rate.setValue(data_item.get("vatRate", self.default_tax_rate))  # Umsatzsteuersatz für den in Rechnung gestellten Artikel (BT-152)
            # Code der Umsatzsteuerkategorie des in Rechnung gestellten Artikels (BT-151)
            set_combo_box_value(item_dialog.cb_item_vat_code, data_item.get("vatCode"), D_VAT_CODE)
            item_dialog.le_item_id.setText(data_item.get("id", ""))  # Artikel-Nr. (BT-155)
            # Startdatum (BT-134)
            item_billing_period_start = data_item.get("billingPeriodStart")
            if item_billing_period_start:
                item_billing_period_start_datetime = datetime.strptime(str(item_billing_period_start), DATE_FORMAT_XML)
                qdate = QDate(item_billing_period_start_datetime.year, item_billing_period_start_datetime.month, item_billing_period_start_datetime.day)
                item_dialog.de_item_billing_period_start.setDate(qdate)
            # Enddatum (BT-135)
            item_billing_period_end = data_item.get("billingPeriodEnd")
            if item_billing_period_end:
                item_billing_period_end_datetime = datetime.strptime(str(item_billing_period_end), DATE_FORMAT_XML)
                qdate = QDate(item_billing_period_end_datetime.year, item_billing_period_end_datetime.month, item_billing_period_end_datetime.day)
                item_dialog.de_item_billing_period_end.setDate(qdate)
            item_dialog.cb_item_billing_period.setChecked(bool(item_billing_period_start or item_billing_period_end))
            item_dialog.le_item_order_position.setText(data_item.get("orderPosition", ""))  # Referenz zur Bestellposition (BT-132)
            # Objektkennung auf Ebene der Rechnungsposition (BT-128)
            item_object_references = data_item.get("objectReferences", [])
            if len(item_object_references) > 0:
                item_dialog.le_object_reference.setText(item_object_references[0].get("id", ""))
            else:
                item_dialog.le_object_reference.setText("")
            item_dialog.pte_item_description.setPlainText(data_item.get("description", ""))  # Artikelbeschreibung (BT-154)
            item_dialog.dsb_item_quantity.setValue(data_item.get("quantity", ""))  # Menge (BT-129)
            # Einheit (BT-130) D_UNIT
            set_combo_box_value(item_dialog.cb_item_quantity_unit, data_item.get("quantityUnit"), D_UNIT)
            item_dialog.dsb_item_net_unit_price.setValue(data_item.get("netUnitPrice", 0))  # Einzelpreis (Netto) (BT-146)
            item_dialog.dsb_item_basis_quantity.setValue(data_item.get("basisQuantity", 1))  # Basismenge zum Artikelpreis (BT-149)

        # Nachlässe
        for allowance_idx, data_allowance in enumerate(data.setdefault("allowances", [])):
            self.add_discount()
            charge_allowance: Ui_InvoiceDiscountsData = dialog.discounts_widgets[allowance_idx]
            charge_allowance.dsb_basis_amount.setValue(data_allowance.get("basisAmount", 0))  # Grundbetrag (BT-93)
            charge_allowance.dsb_net_amount.setValue(data_allowance.get("netAmount", 0))  # Betrag (Netto) (BT-92)
            charge_allowance.dsb_percent.setValue(data_allowance.get("percent", 0))  # Prozent (BT-94)
            charge_allowance.le_reason.setText(data_allowance.get("reason", ""))  # Grund (BT-97)
            # Code des Grundes (BT-98)
            set_combo_box_value(charge_allowance.cb_reason_code, data_allowance.get("reasonCode"), D_UNIT)
            # Steuerkategorie (BT-95)
            set_combo_box_value(charge_allowance.cb_vat_code, data_allowance.get("vatCode"), D_VAT_CODE)
            charge_allowance.dsb_vat_rate.setValue(data_allowance.get("vatRate", self.default_tax_rate))  # Steuersatz (BT-96)

        # Zuschläge
        for charge_idx, data_charge in enumerate(data.setdefault("charges", [])):
            self.add_surcharge()
            charge_dialog: Ui_InvoiceSurchargesData = dialog.surcharges_widgets[charge_idx]
            charge_dialog.dsb_basis_amount.setValue(data_charge.get("basisAmount", 0))  # Grundbetrag (BT-100)
            charge_dialog.dsb_net_amount.setValue(data_charge.get("netAmount", 0))  # Betrag (Netto) (BT-99)
            charge_dialog.dsb_percent.setValue(data_charge.get("percent", 0))  # Prozent (BT-101)
            charge_dialog.le_reason.setText(data_charge.get("reason", ""))  # Grund (BT-104)
            # Code des Grundes (BT-105)
            set_combo_box_value(charge_dialog.cb_reason_code, data_charge.get("reasonCode"), D_UNIT)
            # Steuerkategorie (BT-102)
            set_combo_box_value(charge_dialog.cb_vat_code, data_charge.get("vatCode"), D_VAT_CODE)
            charge_dialog.dsb_vat_rate.setValue(data_charge.get("vatRate", self.default_tax_rate))  # Steuersatz (BT-103)

        self.update_tax_widget(data)  # update taxes to write exemption reason to UI

        data_totals = data.setdefault("totals", {})
        dialog.dsb_payed_amount.setValue(data_totals.get("paidAmount", 0) or 0)  # Vorauszahlungsbetrag (BT-113)
        dialog.dsb_rounded_amount.setValue(data_totals.get("roundingAmount", 0) or 0)  # Rundungsbetrag (BT-114)
