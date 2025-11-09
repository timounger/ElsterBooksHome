"""!
********************************************************************************
@file   drafthorse_import.py
@brief  Create drafthorse invoices
********************************************************************************
"""

# pylint: disable=protected-access
import logging
from typing import Optional, Any
from datetime import datetime
from decimal import Decimal
from drafthorse.models.document import Document
import fitz  # PyMuPDF

from PyQt6.QtCore import QDate, Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QAbstractSpinBox, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox, \
    QPlainTextEdit, QLineEdit, QLabel

from Source.version import __title__
from Source.Model.data_handler import DATE_FORMAT_JSON, DATE_FORMAT_XML, EReceiptFields, fill_data, D_RECEIPT_TEMPLATE, XML_TYPE
from Source.Model.ZUGFeRD.drafthorse_data import D_INVOICE_TYPE, D_CURRENCY, D_COUNTRY_CODE, D_PAYMENT_METHOD, \
    D_VAT_CODE, D_UNIT, D_ALLOWANCE_REASON_CODE, D_EXEMPTION_REASON_CODE, D_CHARGE_REASON_CODE
from Source.Model.ZUGFeRD.drafthorse_convert import convert_facturx_to_json
from Source.Views.widgets.invoice_item_data_ui import Ui_InvoiceItemData
from Source.Views.widgets.invoice_item_discounts_data_ui import Ui_InvoiceItemDiscountsData
from Source.Views.widgets.invoice_item_surcharges_data_ui import Ui_InvoiceItemSurchargeData
from Source.Views.widgets.invoice_discounts_data_ui import Ui_InvoiceDiscountsData
from Source.Views.widgets.invoice_surcharges_data_ui import Ui_InvoiceSurchargesData
from Source.Views.widgets.invoice_tax_data_ui import Ui_InvoiceTaxData
from Source.Views.widgets.invoice_data_ui import Ui_InvoiceData

log = logging.getLogger(__title__)

###########################
##    Set Widget Utils   ##
###########################


def create_value_description(entry: str, d_items: dict[str, str]) -> str:
    """!
    @brief Create value description
    @param entry : value
    @param d_items : value description
    @return description value
    """
    description = d_items.get(entry, "Unbekannt")
    description_value = f"{entry} - {description}"
    return description_value


def set_combo_box_value(widget: QComboBox, entry: str, d_items: dict[str, str]) -> None:
    """!
    @brief Set combobox box value
    @param widget : widget
    @param entry : default value
    @param d_items : items in combo box
    """
    widget.setCurrentText(create_value_description(entry, d_items))


def set_combo_box_items(widget: QComboBox, entry: str, d_items: dict[str, str]) -> None:
    """!
    @brief Set combobox box with items and set default
    @param widget : widget
    @param entry : default value
    @param d_items : items in combo box
    """
    for i, key in enumerate(d_items):
        widget.addItem(create_value_description(key, d_items), key)
        if key == entry:  # set default
            widget.setCurrentIndex(i)


def set_combo_box_read_only(widget: QComboBox, entry: str, d_items: dict[str, str]) -> None:
    """!
    @brief Set combobox box with single value and set as read only without focus
    @param widget : widget
    @param entry : entry
    @param d_items : items in combo box
    """
    widget.addItem(create_value_description(entry, d_items), entry)
    widget.setCurrentIndex(0)
    widget.setEditable(True)  # required before set read only line
    widget.lineEdit().setReadOnly(True)  # do not open combo box if click on text
    COMBO_BOX_READ_ONLY_STYLE = \
        """
        QComboBox::drop-down {
            border: 0px;
        }
        QComboBox::down-arrow {
            image: none;
            width: 0px;
        }
        """
    widget.setStyleSheet(COMBO_BOX_READ_ONLY_STYLE)  # set stylesheet without dropdown button
    widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # disable mouse focus
    widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)  # disable mouse focus


def set_date_read_only(widget: QDateEdit, date_string: str) -> None:
    """!
    @brief Set date as read only without focus
    @param widget : widget
    @param date_string : date as string in format DATE_FORMAT_XML
    """
    date_datetime = datetime.strptime(str(date_string), DATE_FORMAT_XML)
    qdate = QDate(date_datetime.year, date_datetime.month, date_datetime.day)
    widget.setDate(qdate)
    widget.setReadOnly(True)
    widget.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
    widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # disable mouse focus
    widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)  # disable mouse focus


def set_spin_box_read_only(widget: QSpinBox | QDoubleSpinBox, value: int | float, max_decimals: Optional[int] = None) -> None:
    """!
    @brief Set spin box as read only without focus
    @param widget : widget
    @param value : value to set
    @param max_decimals : reduce decimals to minimum required with this maximum
    """
    if max_decimals is not None:
        if isinstance(widget, QDoubleSpinBox):
            d = Decimal(str(value)).normalize()
            if d == d.to_integral():
                decimals = 0
            else:
                decimals = -int(d.as_tuple().exponent)
            decimals = min(decimals, max_decimals)
            widget.setDecimals(decimals)
        else:
            raise TypeError("Widget is not QDoubleSpinBox to set Decimals")
    widget.setValue(value)
    widget.setReadOnly(True)
    widget.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
    widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # disable mouse focus
    widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)  # disable mouse focus


def set_line_edit_read_only(widget: QLineEdit, value: str, d_items: Optional[dict[str, str]] = None) -> None:
    """!
    @brief Set label as read only and optional with description for value
    @param widget : widget
    @param value : value to set
    @param d_items : translation items
    """
    if d_items is not None:
        value = create_value_description(value, d_items)
    widget.setText(value)
    widget.setReadOnly(True)


def set_plain_text_read_only(widget: QPlainTextEdit, value: str) -> None:
    """!
    @brief Set label as read only
    @param widget : widget
    @param value : value to set
    """
    widget.setPlainText(value)
    widget.setReadOnly(True)


def set_optional_entry(widget: QLineEdit | QPlainTextEdit | QSpinBox | QDoubleSpinBox | QDateEdit,
                       value: str,
                       other_widget: Optional[QLabel | list[QLabel]] = None) -> None:
    """!
    @brief Set optional entry
    @param widget : widget
    @param value : value to set
    @param other_widget : other widgets
    """
    if value:
        if isinstance(widget, QDateEdit):
            set_date_read_only(widget, value)
        elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
            set_spin_box_read_only(widget, value)
        elif isinstance(widget, QLineEdit):
            set_line_edit_read_only(widget, value)
        elif isinstance(widget, QPlainTextEdit):
            set_plain_text_read_only(widget, value)
        else:
            raise TypeError(f"Invalid Optional widget '{type(widget)}'")
    else:
        widget.hide()
        if other_widget is not None:
            if isinstance(other_widget, list):
                for other_widget_item in other_widget:
                    other_widget_item.hide()
            else:
                other_widget.hide()


###########################
##   Drafthorse Import   ##
###########################

def extract_xml_from_pdf(pdf_path: str) -> bytes | None:
    """!
    @brief Extract XML content from PDF
    @param pdf_path : PDF file path
    @return XML content
    """
    file_content = None
    doc = fitz.open(pdf_path)

    # check attachments
    for i in range(doc.embfile_count()):
        attachment = doc.embfile_info(i)
        file_name = attachment['name']
        if file_name.endswith(XML_TYPE):
            file_content = doc.embfile_get(attachment['name'])
            break

    # in some cases: check for embedded x-invoice
    if file_content is None:
        for i in range(doc.xref_length()):
            try:
                obj = doc.xref_object(i, compressed=True)
                if "/Type/EmbeddedFile" in obj:
                    # filename = doc.xref_get_key(i, "UF")[1] or f"embedded_{i}.xml"  # get filename
                    file_content = doc.xref_stream(i)  # extract stream
                    break
            except Exception:
                file_content = None
    return file_content


def extract_xml_from_xinvoice(xml_path: str) -> bytes:
    """!
    @brief Extract XML content from xinvoice
    @param xml_path : XML file path
    @return XML content
    """
    with open(xml_path, "rb") as file:
        file_content = file.read()
    return file_content


def check_zugferd(pdf_path: str) -> bool:
    """!
    @brief Check if document ZUGFeRD
    @param pdf_path : PDF file path
    @return status if document is ZUGFeRD
    """
    b_is_zugferd = False
    xml_content = extract_xml_from_pdf(pdf_path)
    if xml_content is not None:
        try:
            _doc = Document.parse(xml_content)
        except TypeError:
            pass
        else:
            b_is_zugferd = True
    return b_is_zugferd


def check_xinvoice(xml_path: str) -> bool:
    """!
    @brief Check if document xinvoice
    @param xml_path : XML file path
    @return status if document is xinvoice
    """
    b_is_xinvoice = False
    xml_content = extract_xml_from_xinvoice(xml_path)
    if xml_content is not None:
        try:
            _doc = Document.parse(xml_content)
        except TypeError:
            pass
        else:
            b_is_xinvoice = True
    return b_is_xinvoice


def import_invoice(xml_content: Optional[bytes], is_income: bool, income_group: str = "", expenditure_group: str = "") -> dict[EReceiptFields, Any]:
    """!
    @brief Import invoice
    @param xml_content : XML content
    @param is_income : True: is income; False: is expenditure
    @param income_group : income group
    @param expenditure_group : expenditure group
    @return data
    """
    if xml_content is not None:
        doc = Document.parse(xml_content)
        invoice_date = doc.header.issue_date_time._value
        if invoice_date:
            invoice_date = datetime.strptime(str(invoice_date), DATE_FORMAT_XML)
            invoice_date = invoice_date.strftime(DATE_FORMAT_JSON)
        else:
            invoice_date = ""
        if is_income:
            trade_partner = str(doc.trade.agreement.buyer.name)
        else:
            trade_partner = str(doc.trade.agreement.seller.name)
        invoice_number = str(doc.header.id)

        deliver_date = doc.trade.delivery.event.occurrence._value
        if deliver_date:
            deliver_date = datetime.strptime(str(deliver_date), DATE_FORMAT_XML)
            deliver_date = deliver_date.strftime(DATE_FORMAT_JSON)
        else:
            deliver_date = ""

        description = ""
        for child in doc.trade.items.children:
            description = str(child.product.name)[:100]  # limit description
            break

        gross = doc.trade.settlement.monetary_summation.grand_total._amount
        net = doc.trade.settlement.monetary_summation.tax_basis_total._amount

        b_success = True
    else:
        b_success = False

    receipt: dict[EReceiptFields, Any] = {}
    if b_success:
        receipt[EReceiptFields.TRADE_PARTNER] = trade_partner
        receipt[EReceiptFields.DESCRIPTION] = description
        receipt[EReceiptFields.INVOICE_DATE] = invoice_date
        receipt[EReceiptFields.INVOICE_NUMBER] = invoice_number
        receipt[EReceiptFields.DELIVER_DATE] = deliver_date
        receipt[EReceiptFields.AMOUNT_GROSS] = float(gross)
        receipt[EReceiptFields.AMOUNT_NET] = float(net)
        receipt[EReceiptFields.BAR] = False
        receipt[EReceiptFields.GROUP] = income_group if is_income else expenditure_group
        receipt = fill_data(D_RECEIPT_TEMPLATE, receipt)
    return receipt


def import_zugferd(pdf_path: str, is_income: bool,
                   income_group: str = "", expenditure_group: str = "") -> dict[EReceiptFields, Any]:
    """!
    @brief Read items from ZUGFeRD file
    @param pdf_path : PDF file path
    @param is_income : True: is income; False: is expenditure
    @param income_group : income group
    @param expenditure_group : expenditure group
    @return data
    """
    xml_content = extract_xml_from_pdf(pdf_path)
    data = import_invoice(xml_content, is_income, income_group, expenditure_group)
    return data


def import_xinvoice(xml_path: str, is_income: bool,
                    income_group: str = "", expenditure_group: str = "") -> dict[EReceiptFields, Any]:
    """!
    @brief Read items from ZUGFeRD file
    @param xml_path : XML file path
    @param is_income : True: is income; False: is expenditure
    @param income_group : income group
    @param expenditure_group : expenditure group
    @return import success status
    """
    xml_content = extract_xml_from_xinvoice(xml_path)
    data = import_invoice(xml_content, is_income, income_group, expenditure_group)
    return data


def visualize_xml_invoice(dialog: Ui_InvoiceData, xml_content: str) -> None:
    """!
    @brief Visualize xml invoice in dialog.
    @param dialog : invoice dialog
    @param xml_content : xml content of invoice
    """
    data = convert_facturx_to_json(xml_content)

    # Rechnungstitel
    dialog.lbl_invoice_title.hide()
    dialog.le_invoice_title.hide()
    # Rechnungsnummer (BT-1)
    invoice_number = data["number"]
    set_line_edit_read_only(dialog.le_invoice_number, invoice_number)
    # Rechnungsdatum (BT-2)
    set_date_read_only(dialog.de_invoice_date, data["issueDate"])
    # Code für den Rechnungstyp (BT-3)
    set_combo_box_read_only(dialog.cb_invoice_type, data["typeCode"], D_INVOICE_TYPE)
    # Code für die Rechnungswährung (BT-5)
    set_combo_box_read_only(dialog.cb_currency, data["currencyCode"], D_CURRENCY)
    # Fälligkeitsdatum der Zahlung (BT-9)
    due_date = data["dueDate"]
    if due_date:
        set_date_read_only(dialog.de_due_date, due_date)
        due_date_datetime = datetime.strptime(due_date, DATE_FORMAT_XML)
        invoice_date_datetime = datetime.strptime(str(data["issueDate"]), DATE_FORMAT_XML)
        set_spin_box_read_only(dialog.sb_due_days, (due_date_datetime - invoice_date_datetime).days)
    else:
        dialog.lbl_due_date.hide()
        dialog.de_due_date.hide()
        dialog.sb_due_days.hide()
        dialog.lbl_due_days.hide()
    # Tatsächliches Lieferdatum (BT-72)
    set_optional_entry(dialog.de_deliver_date, data["deliveryDate"], dialog.lbl_deliver_date)
    # Anfangsdatum des Rechnungszeitraums (BT-73)
    accounting_period_start = data["billingPeriodStartDate"]
    set_optional_entry(dialog.de_accounting_date_from, accounting_period_start, dialog.de_accounting_date_from)
    # Enddatum des Rechnungszeitraums (BT-74)
    accounting_period_end = data["billingPeriodEndDate"]
    set_optional_entry(dialog.de_accounting_date_to, accounting_period_end, dialog.lbl_accounting_to)
    if not accounting_period_start and not accounting_period_end:  # hide if both dates not available
        dialog.lbl_accounting_period.hide()
    dialog.cb_accounting_date.hide()
    # Käuferreferenz (BT-10)
    set_optional_entry(dialog.le_buyer_reference, data["buyerReference"], dialog.lbl_buyer_reference)
    # Projektnummer (BT-11)
    set_optional_entry(dialog.le_project_number, data["projectReference"], dialog.lbl_project_number)
    # Vertragsnummer (BT-12)
    set_optional_entry(dialog.le_contract_number, data["contractReference"], dialog.lbl_contract_number)
    # Bestellnummer (BT-13)
    set_optional_entry(dialog.le_order_number, data["purchaseOrderReference"], dialog.lbl_order_number)
    # Auftragsnummer (BT-14)
    set_optional_entry(dialog.le_assignment_number, data["salesOrderReference"], dialog.lbl_assignment_number)
    # Wareneingangsmeldung (BT-15)
    receiving_advice_reference_id = data["receivingAdviceReference"]["id"]
    receiving_advice_reference_date = data["receivingAdviceReference"]["issueDate"]
    if not receiving_advice_reference_id and not receiving_advice_reference_date:
        dialog.lbl_receiving_advice_referenced_document.hide()
    set_optional_entry(dialog.le_receiving_referenced_document, receiving_advice_reference_id)
    set_optional_entry(dialog.de_receiving_advice_referenced_document, receiving_advice_reference_date, dialog.lbl_receiving_document_date)
    # Versandanzeige (BT-16)
    despatch_advice_reference_id = data["despatchAdviceReference"]["id"]
    despatch_advice_reference_date = data["despatchAdviceReference"]["issueDate"]
    if not despatch_advice_reference_id and not despatch_advice_reference_date:
        dialog.lbl_despatch_advice_referenced_document.hide()
    set_optional_entry(dialog.le_despatch_advice_referenced_document, despatch_advice_reference_id)
    set_optional_entry(dialog.de_despatch_advice_referenced_document, despatch_advice_reference_date, dialog.lbl_despatch_advice_referenced_document_date)
    # Ausschreibung/Los (BT-17)
    tender_references = data["tenderReferences"]
    if len(tender_references) > 0:
        tender_references_id = tender_references[0]["id"]
        set_optional_entry(dialog.le_additional_referenced_document, tender_references_id, dialog.lbl_additional_referenced_document)
    else:
        dialog.lbl_additional_referenced_document.hide()
        dialog.le_additional_referenced_document.hide()
    # Objektreferenz (BT-18)
    object_references = data["objectReferences"]
    if len(object_references) > 0:
        object_references_id = object_references[0]["id"]
        set_optional_entry(dialog.le_object_reference, object_references_id, dialog.lbl_object_reference)
    else:
        dialog.lbl_object_reference.hide()
        dialog.le_object_reference.hide()
    # Buchungskonto des Käufers (BT-19)
    buyer_accounting_accounts = data["buyerAccountingAccounts"]
    if len(buyer_accounting_accounts) > 0:
        buyer_accounting_accounts_id = buyer_accounting_accounts[0]["id"]
        set_optional_entry(dialog.le_booking_account_buyer, buyer_accounting_accounts_id, dialog.lbl_booking_account_buyer)
    else:
        dialog.lbl_booking_account_buyer.hide()
        dialog.le_booking_account_buyer.hide()
    # Rechnungsreferenz (BT-25, BT-26)
    invoice_references = data["invoiceReferences"]
    if len(invoice_references) > 0:
        invoice_references_id = invoice_references[0]["id"]
        invoice_references_date = invoice_references[0]["issueDate"]
        if invoice_references_id or invoice_references_date:
            set_line_edit_read_only(dialog.le_invoice_reference, invoice_references_id)
            set_date_read_only(dialog.de_invoice_reference, invoice_references_date)
        else:
            dialog.lbl_invoice_reference.hide()
            dialog.le_invoice_reference.hide()
            dialog.lbl_invoice_reference_date.hide()
            dialog.de_invoice_reference.hide()
    else:
        dialog.lbl_invoice_reference.hide()
        dialog.le_invoice_reference.hide()
        dialog.lbl_invoice_reference_date.hide()
        dialog.de_invoice_reference.hide()
    # Bemerkung (BT-22)
    set_optional_entry(dialog.pte_note, data["note"], dialog.lbl_note)
    # Einleitungstext
    dialog.lbl_introduction_text.hide()
    dialog.pte_introduction_text.hide()

    data_seller = data["seller"]
    # Name des Verkäufers (BT-27)
    seller_name = data_seller["name"]
    set_line_edit_read_only(dialog.le_seller_company, seller_name)
    # Handelsname (BT-28)
    set_optional_entry(dialog.le_seller_name, data_seller["tradeName"], dialog.lbl_seller_name)
    # Verkäuferkennung (BT-29)
    set_optional_entry(dialog.le_seller_recognition, data_seller["id"], dialog.lbl_seller_recognition)
    # Registernummer (BT-30)
    set_optional_entry(dialog.le_seller_register_number, data_seller["tradeId"], dialog.lbl_seller_register_number)
    # Umsatzsteuer-Identifikationsnummer des Verkäufers (BT-31)
    set_optional_entry(dialog.le_seller_vat, data_seller["vatId"], dialog.lbl_seller_vat)
    # Steuernummer des Verkäufers (BT-32)
    set_optional_entry(dialog.le_seller_tax_number, data_seller["taxId"], dialog.lbl_seller_tax_number)
    # WEEE-Nummer
    dialog.lbl_seller_weee_number.hide()
    dialog.le_seller_weee_number.hide()
    # Rechtliche Informationen (BT-33)
    set_optional_entry(dialog.pte_seller_law_info, data_seller["legalInfo"], dialog.lbl_seller_law_info)
    # seller electric address (BT-34)
    set_optional_entry(dialog.le_seller_electric_address, data_seller["electronicAddress"], dialog.lbl_seller_electric_address)
    # Webseite
    dialog.lbl_seller_website.hide()
    dialog.le_seller_website.hide()
    # Zeile 1 der Verkäuferanschrift (BT-35)
    set_optional_entry(dialog.le_seller_street_1, data_seller["address"]["line1"], dialog.lbl_seller_street_1)
    # Zeile 2 der Verkäuferanschrift (BT-36)
    set_optional_entry(dialog.le_seller_street_2, data_seller["address"]["line2"], dialog.lbl_seller_street_2)
    # Postleitzahl der Verkäuferanschrift (BT-38)
    set_optional_entry(dialog.le_seller_plz, data_seller["address"]["postCode"], dialog.lbl_seller_plz)
    # Stadt der Verkäuferanschrift (BT-37)
    set_optional_entry(dialog.le_seller_city, data_seller["address"]["city"], dialog.lbl_seller_city)
    # Ländercode der Verkäuferanschrift (BT-40)
    set_combo_box_read_only(dialog.cb_seller_country, data_seller["address"]["countryCode"], D_COUNTRY_CODE)
    # Kontaktstelle des Verkäufers (BT-41)
    seller_contact_name = data_seller["contact"]["name"]
    set_optional_entry(dialog.le_seller_contact_name, seller_contact_name, dialog.lbl_seller_contact_name)
    # E-Mail-Adresse der Kontaktstelle des Verkäufers (BT-43)
    seller_contact_mail = data_seller["contact"]["email"]
    set_optional_entry(dialog.le_seller_contact_mail, seller_contact_mail, dialog.lbl_seller_contact_mail)
    # Telefonnummer der Kontaktstelle des Verkäufers (BT-42)
    seller_contact_phone = data_seller["contact"]["phone"]
    set_optional_entry(dialog.le_seller_contact_phone, seller_contact_phone, dialog.lbl_seller_contact_phone)
    # seller fax
    dialog.lbl_seller_contact_fax.hide()
    dialog.le_seller_contact_fax.hide()
    if not seller_contact_name and not seller_contact_mail and not seller_contact_phone:
        dialog.line_seller_contact.hide()
        dialog.lbl_seller_contact.hide()
    # seller logo
    dialog.line_seller_logo.hide()
    dialog.lbl_seller_logo.hide()
    dialog.btn_seller_logo_select.hide()
    dialog.lbl_seller_logo_preview.hide()
    dialog.lbl_seller_logo_path.hide()

    data_buyer = data["buyer"]
    # Name des Käufers (BT-44)
    set_line_edit_read_only(dialog.le_buyer_company, data_buyer["name"])
    # Handelsname (BT-45)
    set_optional_entry(dialog.le_buyer_name, data_buyer["tradeName"], dialog.lbl_buyer_name)
    # Käuferkennung (BT-46)
    set_optional_entry(dialog.le_buyer_recognition, data_buyer["id"], dialog.lbl_buyer_recognition)
    # Registernummer (BT-47)
    set_optional_entry(dialog.le_buyer_register_number, data_buyer["tradeId"], dialog.lbl_buyer_register_number)
    # Umsatzsteuer-Identifikationsnummer des Käufers (BT-48)
    set_optional_entry(dialog.le_buyer_vat, data_buyer["vatId"], dialog.lbl_buyer_vat)
    # Elektronische Adresse (BT-49)
    set_optional_entry(dialog.le_buyer_electric_address, data_buyer["electronicAddress"], dialog.lbl_buyer_electric_address)
    # Zeile 1 der Käuferanschrift (BT-50)
    set_optional_entry(dialog.le_buyer_street_1, data_buyer["address"]["line1"], dialog.lbl_buyer_street_1)
    # Zeile 2 der Käuferanschrift (BT-51)
    set_optional_entry(dialog.le_buyer_street_2, data_buyer["address"]["line2"], dialog.lbl_buyer_street_2)
    # Postleitzahl der Käuferanschrift (BT-53)
    set_optional_entry(dialog.le_buyer_plz, data_buyer["address"]["postCode"], dialog.lbl_buyer_plz)
    # Stadt der Käuferanschrift (BT-52)
    set_optional_entry(dialog.le_buyer_city, data_buyer["address"]["city"], dialog.lbl_buyer_city)
    # Ländercode der Käuferanschrift (BT-55)
    set_combo_box_read_only(dialog.cb_buyer_country, data_buyer["address"]["countryCode"], D_COUNTRY_CODE)
    # Kontaktstelle des Käufers (BT-56)
    buyer_contact_name = data_buyer["contact"]["name"]
    set_optional_entry(dialog.le_buyer_contact_name, buyer_contact_name, dialog.lbl_buyer_contact_name)
    # E-Mail-Adresse der Kontaktstelle des Käufers (BT-58)
    buyer_contact_mail = data_buyer["contact"]["email"]
    set_optional_entry(dialog.le_buyer_contact_mail, buyer_contact_mail, dialog.lbl_buyer_contact_mail)
    # Telefonnummer der Kontaktstelle des Käufers (BT-57)
    buyer_contact_phone = data_buyer["contact"]["phone"]
    set_optional_entry(dialog.le_buyer_contact_phone, buyer_contact_phone, dialog.lbl_buyer_contact_phone)
    if not buyer_contact_name and not buyer_contact_mail and not buyer_contact_phone:
        dialog.line_buyer_contact.hide()
        dialog.lbl_buyer_contact.hide()

    data_payment = data["payment"]
    if len(data_payment["methods"]) > 0:
        payment_method = data_payment["methods"][0]  # TODO mehrere Zahlungsoptionen ermöglichen
        # Code für die Zahlungsart D_PAYMENT_METHOD (BT-81)
        payment_method_code = payment_method["typeCode"]
        if payment_method_code:
            set_combo_box_read_only(dialog.cb_payment_method, payment_method_code, D_PAYMENT_METHOD)
        else:
            dialog.lbl_payment_method.hide()
            dialog.cb_payment_method.hide()
        # Name des Zahlungskontos (BT-85)
        set_optional_entry(dialog.le_account_holder, payment_method["accountName"], dialog.lbl_account_holder)
        # Kennung des Zahlungskontos (BT-84)
        set_optional_entry(dialog.le_iban, payment_method["iban"], dialog.lbl_iban)
        # Kennung des Zahlungsdienstleisters (BT-86)
        set_optional_entry(dialog.le_bic, payment_method["bic"], dialog.lbl_bic)
    else:
        dialog.lbl_payment_method.hide()
        dialog.cb_payment_method.hide()
        dialog.lbl_account_holder.hide()
        dialog.le_account_holder.hide()
        dialog.lbl_iban.hide()
        dialog.le_iban.hide()
        dialog.lbl_bic.hide()
        dialog.le_bic.hide()
    # bank name
    dialog.lbl_bank_name.hide()
    dialog.le_bank_name.hide()
    # Verwendungszweck (BT-83)
    payment_purpose = data_payment["reference"]
    set_optional_entry(dialog.le_payment_purpose, payment_purpose, dialog.lbl_payment_purpose)
    # Zahlungsbedingungen (BT-20)
    payment_terms = data_payment["terms"]
    set_optional_entry(dialog.pte_payment_terms, payment_terms, dialog.lbl_payment_terms)
    if not payment_purpose and not payment_terms:
        dialog.line_payment.hide()

    data_delivery = data["delivery"]
    # Name des Waren- oder Dienstleistungsempfängers (BT-70)
    delivery_recipient_name = data_delivery["recipientName"]
    set_optional_entry(dialog.le_deliver_name, delivery_recipient_name, dialog.lbl_deliver_name)
    # Kennung des Lieferorts (BT-71)
    delivery_location_id = data_delivery["locationId"]
    set_optional_entry(dialog.le_deliver_place_ident, delivery_location_id, dialog.lbl_deliver_place_ident)
    # Zeile 1 der Lieferanschrift (BT-75)
    delivery_street_1 = data_delivery["address"]["line1"]
    set_optional_entry(dialog.le_deliver_street_1, delivery_street_1, dialog.lbl_deliver_street_1)
    # Zeile 2 der Lieferanschrift (BT-76)
    delivery_street_2 = data_delivery["address"]["line2"]
    set_optional_entry(dialog.le_deliver_street_2, delivery_street_2, dialog.lbl_deliver_street_2)
    # Zeile 3 der Lieferanschrift (BT-165)
    delivery_street_3 = data_delivery["address"]["line3"]
    set_optional_entry(dialog.le_deliver_addition, delivery_street_3, dialog.lbl_deliver_addition)
    # Postleitzahl der Lieferanschrift (BT-78)
    delivery_plz = data_delivery["address"]["postCode"]
    set_optional_entry(dialog.le_deliver_plz, delivery_plz, dialog.lbl_deliver_plz)
    # Stadt der Lieferanschrift (BT-77)
    delivery_city = data_delivery["address"]["city"]
    set_optional_entry(dialog.le_deliver_city, delivery_city, dialog.lbl_deliver_city)
    # Ländercode der Lieferanschrift (BT-80)
    delivery_country = data_delivery["address"]["countryCode"]
    if delivery_country:
        set_combo_box_read_only(dialog.cb_deliver_country, delivery_country, D_COUNTRY_CODE)
    else:
        dialog.lbl_deliver_country.hide()
        dialog.cb_deliver_country.hide()
    # Stadt der Lieferanschrift (BT-79)
    delivery_region = data_delivery["address"]["region"]
    set_optional_entry(dialog.le_deliver_region, delivery_region, dialog.lbl_deliver_region)
    if all(not x for x in [delivery_street_1, delivery_street_2, delivery_street_3,
                           delivery_plz, delivery_city, delivery_country, delivery_region]):
        dialog.lbl_deliver_address.hide()
        b_delivery_address = False
    else:
        b_delivery_address = True
    if not b_delivery_address and not delivery_recipient_name and not delivery_location_id:
        dialog.groupBox_5_delivery.hide()

    # position
    if dialog.groupBox_6_position.layout() is None:  # ensure that layout exists
        layout = QVBoxLayout(dialog.groupBox_6_position)
        dialog.groupBox_6_position.setLayout(layout)
    else:
        layout = dialog.groupBox_6_position.layout()
    for item_pos, data_item in enumerate(data["items"]):
        # create item widget
        item_dialog = Ui_InvoiceItemData()  # new item instance
        widget = QWidget()  # new container widget
        item_dialog.setupUi(widget)
        layout.addWidget(widget)  # insert widget in layout
        # fill data
        item_dialog.groupBox.setTitle(f"Position {item_pos + 1}")
        # Name (BT-153)
        set_line_edit_read_only(item_dialog.le_item_name, data_item["name"])
        # Umsatzsteuersatz für den in Rechnung gestellten Artikel (BT-152)
        set_spin_box_read_only(item_dialog.dsb_item_vat_rate, data_item["vatRate"], max_decimals=2)
        # Code der Umsatzsteuerkategorie des in Rechnung gestellten Artikels (BT-151)
        set_combo_box_read_only(item_dialog.cb_item_vat_code, data_item["vatCode"], D_VAT_CODE)
        # Artikel-Nr. (BT-155)
        set_optional_entry(item_dialog.le_item_id, data_item["id"], item_dialog.lbl_item_id)
        # Startdatum (BT-134)
        set_optional_entry(item_dialog.de_item_billing_period_start, data_item["billingPeriodStart"], item_dialog.lbl_item_billing_period_start)
        # Enddatum (BT-135)
        set_optional_entry(item_dialog.de_item_billing_period_end, data_item["billingPeriodEnd"], item_dialog.lbl_item_billing_period_end)
        item_dialog.cb_item_billing_period.hide()
        # Referenz zur Bestellposition (BT-132)
        set_optional_entry(item_dialog.le_item_order_position, data_item["orderPosition"], item_dialog.lbl_item_order_position)
        # Objektkennung auf Ebene der Rechnungsposition (BT-128)
        item_object_references = data_item["objectReferences"]
        if len(item_object_references) > 0:
            set_optional_entry(item_dialog.le_object_reference, item_object_references[0]["id"], item_dialog.lbl_object_reference)
        else:
            item_dialog.lbl_object_reference.hide()
            item_dialog.le_object_reference.hide()
        # Artikelbeschreibung (BT-154)
        set_optional_entry(item_dialog.pte_item_description, data_item["description"], item_dialog.lbl_item_description)
        # Menge (BT-129)
        set_spin_box_read_only(item_dialog.dsb_item_quantity, data_item["quantity"], max_decimals=4)
        # Einheit (BT-130) D_UNIT
        set_combo_box_read_only(item_dialog.cb_item_quantity_unit, data_item["quantityUnit"], D_UNIT)
        # Einzelpreis (Netto) (BT-146)
        set_spin_box_read_only(item_dialog.dsb_item_net_unit_price, data_item["netUnitPrice"])
        # Einzelpreis (Brutto)
        item_dialog.lbl_item_gross_unit_price.hide()
        item_dialog.dsb_item_gross_unit_price.hide()
        item_dialog.lbl_item_gross_unit_price_symbol.hide()
        # Basismenge zum Artikelpreis (BT-149)
        set_optional_entry(item_dialog.dsb_item_basis_quantity, data_item["basisQuantity"], item_dialog.lbl_item_basis_quantity)
        # Steuerbetrag
        item_dialog.lbl_item_vat_amount.hide()
        item_dialog.dsb_item_vat_amount.hide()
        item_dialog.lbl_item_vat_amount_symbol.hide()
        # Gesamtpreis (Netto) (BT-131)
        set_spin_box_read_only(item_dialog.dsb_item_net_amount, data_item["netAmount"])
        # Gesamtpreis (Brutto)
        item_dialog.lbl_item_gross_price.hide()
        item_dialog.dsb_item_gross_price.hide()
        item_dialog.lbl_item_gross_price_symbol.hide()
        # Item Zuschläge/Nachlässe
        data_item_allowances = data_item.get("allowances", [])
        data_item_charges = data_item.get("charges", [])
        if data_item_allowances or data_item_charges:
            if item_dialog.widget_charge.layout() is None:  # ensure that layout exists
                layout_charge = QVBoxLayout(item_dialog.widget_charge)
                item_dialog.widget_charge.setLayout(layout_charge)
            else:
                layout_charge = item_dialog.widget_charge.layout()
            # Nachlässe
            for data_item_allowance in data_item_allowances:
                item_discount_dialog = Ui_InvoiceItemDiscountsData()
                discount_widget = QWidget()
                item_discount_dialog.setupUi(discount_widget)
                layout_charge.addWidget(discount_widget)  # insert widget in layout
                set_spin_box_read_only(item_discount_dialog.dsb_percent, data_item_allowance["percent"])  # Prozent (BT-138)
                set_spin_box_read_only(item_discount_dialog.dsb_net_amount, data_item_allowance["netAmount"])  # Betrag (Netto) (BT-136)
                set_line_edit_read_only(item_discount_dialog.le_reason, data_item_allowance["reason"])  # Grund (BT-139)
                set_combo_box_read_only(item_discount_dialog.cb_reason_code, data_item_allowance["reasonCode"], D_ALLOWANCE_REASON_CODE)  # Code des Grundes (BT-140)
            # Zuschläge
            for data_item_charge in data_item_charges:
                item_surcharge_dialog = Ui_InvoiceItemSurchargeData()
                surcharge_widget = QWidget()
                item_surcharge_dialog.setupUi(surcharge_widget)
                layout_charge.addWidget(surcharge_widget)  # insert widget in layout
                set_spin_box_read_only(item_surcharge_dialog.dsb_percent, data_item_charge["percent"])  # Prozent (BT-143)
                set_spin_box_read_only(item_surcharge_dialog.dsb_net_amount, data_item_charge["netAmount"])  # Betrag (Netto) (BT-141)
                set_line_edit_read_only(item_surcharge_dialog.le_reason, data_item_charge["reason"])  # Grund (BT-144)
                set_combo_box_read_only(item_surcharge_dialog.cb_reason_code, data_item_charge["reasonCode"], D_CHARGE_REASON_CODE)  # Code des Grundes (BT-145)
        else:
            item_dialog.line_charge.hide()

    # Nachlässe
    data_allowances = data["allowances"]
    if len(data_allowances) > 0:
        if dialog.groupBox_7_discounts.layout() is None:  # ensure that layout exists
            layout = QVBoxLayout(dialog.groupBox_7_discounts)
            dialog.groupBox_7_discounts.setLayout(layout)
        else:
            layout = dialog.groupBox_7_discounts.layout()
        for data_allowance in data_allowances:
            # create discount widget
            discount_dialog = Ui_InvoiceDiscountsData()
            widget = QWidget()  # new container widget
            discount_dialog.setupUi(widget)
            layout.addWidget(widget)  # insert widget in layout
            # Grundbetrag (BT-93)
            set_spin_box_read_only(discount_dialog.dsb_basis_amount, data_allowance["basisAmount"])
            # Prozent (BT-94)
            set_spin_box_read_only(discount_dialog.dsb_percent, data_allowance["percent"])
            # Betrag (Netto) (BT-92)
            set_spin_box_read_only(discount_dialog.dsb_net_amount, data_allowance["netAmount"])
            # Steuersatz (BT-96)
            set_spin_box_read_only(discount_dialog.dsb_vat_rate, data_allowance["vatRate"], max_decimals=2)
            # Steuerkategorie (BT-95)
            set_combo_box_read_only(discount_dialog.cb_vat_code, data_allowance["vatCode"], D_VAT_CODE)
            # Betrag Brutto
            discount_dialog.lbl_gross_amount.hide()
            discount_dialog.dsb_gross_amount.hide()
            discount_dialog.lbl_gross_amount_symbol.hide()
            # Steuerbetrag (Netto)
            discount_dialog.lbl_vat_amount.hide()
            discount_dialog.dsb_vat_amount.hide()
            discount_dialog.lbl_vat_amount_symbol.hide()
            # Grund (BT-97)
            set_line_edit_read_only(discount_dialog.le_reason, data_allowance["reason"])
            # Code des Grundes (BT-98)
            set_combo_box_read_only(discount_dialog.cb_reason_code, data_allowance["reasonCode"], D_ALLOWANCE_REASON_CODE)
    else:
        dialog.groupBox_7_discounts.hide()

    # Zuschläge
    data_charges = data["charges"]
    if len(data_charges) > 0:
        if dialog.groupBox_8_surcharges.layout() is None:  # ensure that layout exists
            layout = QVBoxLayout(dialog.groupBox_8_surcharges)
            dialog.groupBox_8_surcharges.setLayout(layout)
        else:
            layout = dialog.groupBox_8_surcharges.layout()
        for data_allowance in data_charges:
            # create surcharge widget
            surcharge_dialog = Ui_InvoiceSurchargesData()
            widget = QWidget()  # new container widget
            surcharge_dialog.setupUi(widget)
            layout.addWidget(widget)  # insert widget in layout
            # Grundbetrag (BT-100)
            set_spin_box_read_only(surcharge_dialog.dsb_basis_amount, data_allowance["basisAmount"])
            # Prozent (BT-101)
            set_spin_box_read_only(surcharge_dialog.dsb_percent, data_allowance["percent"])
            # Betrag (Netto) (BT-99)
            set_spin_box_read_only(surcharge_dialog.dsb_net_amount, data_allowance["netAmount"])
            # Steuersatz (BT-103)
            set_spin_box_read_only(surcharge_dialog.dsb_vat_rate, data_allowance["vatRate"], max_decimals=2)
            # Steuerkategorie (BT-102)
            set_combo_box_read_only(surcharge_dialog.cb_vat_code, data_allowance["vatCode"], D_VAT_CODE)
            # Betrag Brutto
            surcharge_dialog.lbl_gross_amount.hide()
            surcharge_dialog.dsb_gross_amount.hide()
            surcharge_dialog.lbl_gross_amount_symbol.hide()
            # Steuerbetrag (Netto)
            surcharge_dialog.lbl_vat_amount.hide()
            surcharge_dialog.dsb_vat_amount.hide()
            surcharge_dialog.lbl_vat_amount_symbol.hide()
            # Grund (BT-104)
            set_line_edit_read_only(surcharge_dialog.le_reason, data_allowance["reason"])
            # Code des Grundes (BT-105)
            set_combo_box_read_only(surcharge_dialog.cb_reason_code, data_allowance["reasonCode"], D_CHARGE_REASON_CODE)
    else:
        dialog.groupBox_8_surcharges.hide()

    # Steuern
    if dialog.groupBox_9_tax.layout() is None:  # ensure that layout exists
        layout = QVBoxLayout(dialog.groupBox_9_tax)
        dialog.groupBox_9_tax.setLayout(layout)
    else:
        layout = dialog.groupBox_9_tax.layout()
    for _tax_name, tax_data in data["taxes"].items():
        # create item widget
        tax_dialog = Ui_InvoiceTaxData()
        widget = QWidget()  # new container widget
        tax_dialog.setupUi(widget)
        layout.addWidget(widget)  # insert widget in layout
        # Steuerkategorie (BT-118)
        set_line_edit_read_only(tax_dialog.le_tax_category, tax_data["code"], D_VAT_CODE)
        # Steuersatz (BT-119)
        set_spin_box_read_only(tax_dialog.dsb_tax_rate, tax_data["rate"], max_decimals=2)
        # Gesamt (Netto) (BT-116)
        set_spin_box_read_only(tax_dialog.dsb_tax_net, tax_data["netAmount"])
        # Steuerbetrag (BT-117)
        set_spin_box_read_only(tax_dialog.dsb_tax_amount, tax_data["vatAmount"])
        # Gesamt (Brutto)
        set_spin_box_read_only(tax_dialog.dsb_tax_gross, tax_data["netAmount"] + tax_data["vatAmount"])
        # hide to prevent too long width in view
        tax_dialog.lbl_tax_gross.hide()
        tax_dialog.dsb_tax_gross.hide()
        tax_dialog.lbl_tax_gross_symbol.hide()
        # Befreiungsgrund (BT-120)
        set_optional_entry(tax_dialog.le_exemption_reason, tax_data.get("exemptionReason", ""), tax_dialog.lbl_exemption_reason)
        # Code für Befreiungsgrund (BT-121)
        exemption_reason_code = tax_data.get("exemptionReasonCode", "")
        if exemption_reason_code:
            set_combo_box_read_only(tax_dialog.cb_exemption_reason_code, exemption_reason_code, D_EXEMPTION_REASON_CODE)
        else:
            tax_dialog.lbl_exemption_reason_code.setVisible(False)
            tax_dialog.cb_exemption_reason_code.setVisible(False)

    data_totals = data["totals"]
    # Summe der Nettobeträge aller Rechnungspositionen (BT-106)
    set_spin_box_read_only(dialog.dsb_sum_positions, data_totals["itemsNetAmount"])
    # Summe der Zuschläge auf Dokumentenebene (BT-108)
    set_optional_entry(dialog.dsb_sum_surcharges, data_totals["chargesNetAmount"], [dialog.lbl_sum_surcharges, dialog.lbl_sum_surcharges_symbol])
    # Summe der Abschläge auf Dokumentenebene (BT-107)
    set_optional_entry(dialog.dsb_sum_discounts, data_totals["allowancesNetAmount"], [dialog.lbl_sum_discounts, dialog.lbl_sum_discounts_symbol])
    # Rechnungsgesamtbetrag ohne Umsatzsteuer (BT-109)
    set_spin_box_read_only(dialog.dsb_sum_net, data_totals["netAmount"])
    # Summe Umsatzsteuer (BT-110)
    set_optional_entry(dialog.dsb_sum_vat, data_totals["vatAmount"], [dialog.lbl_sum_vat, dialog.lbl_sum_vat_symbol])
    # Rechnungsgesamtbetrag einschließlich Umsatzsteuer (BT-112)
    set_optional_entry(dialog.dsb_sum_gross, data_totals["grossAmount"], [dialog.lbl_sum_gross, dialog.lbl_sum_gross_symbol])
    # Vorauszahlungsbetrag (BT-113)
    set_optional_entry(dialog.dsb_payed_amount, data_totals["paidAmount"], [dialog.lbl_payed_amount, dialog.lbl_payed_amount_symbol])
    # Rundungsbetrag (BT-114)
    set_optional_entry(dialog.dsb_rounded_amount, data_totals["roundingAmount"], [dialog.lbl_rounded_amount, dialog.lbl_rounded_amount_symbol])
    # Fälliger Zahlungsbetrag (BT-115)
    set_optional_entry(dialog.dsb_amount_due, data_totals["dueAmount"], [dialog.lbl_amount_due, dialog.lbl_amount_due_symbol])
