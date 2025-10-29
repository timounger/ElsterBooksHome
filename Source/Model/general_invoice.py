"""!
********************************************************************************
@file   general_invoice.py
@brief  Create general invoice
********************************************************************************
"""

import os
import logging
from typing import Optional, Any
import subprocess
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.drawing.image import Image
from openpyxl.styles.borders import Border, Side
from openpyxl.utils import get_column_letter
import qrcode

from Source.version import __title__
from Source.Util.app_data import EXPORT_PATH, LOGO_ZUGFERD, EInvoiceOption
from Source.Util.openpyxl_util import XLSCreator
from Source.Model.data_handler import get_file_name, convert_xlsx_to_pdf
from Source.Model.ZUGFeRD.drafthorse_data import D_INVOICE_TYPE, D_CURRENCY, \
    D_COUNTRY_CODE, D_PAYMENT_METHOD, D_VAT_CODE, D_UNIT
from Source.Model.ZUGFeRD.drafthorse_import import create_value_description
from Source.Model.ZUGFeRD.drafthorse_invoice import add_xml_to_pdf, create_factur_xml, convert_json_to_drafthorse_doc, fill_invoice_data

log = logging.getLogger(__title__)

COLOR_LIGHT_GREY = "F2F2F2"
COLOR_LIGHT_BLUE = "CFF1FF"
COLOR_MIDDLE_GREY = "E0E0E0"
WHITE_BORDER = Border(right=Side(style="medium", color="FFFFFF"))
SECTION_KEY = "SECTION_KEY"

QR_CODE_FILE_PATH = os.path.join(EXPORT_PATH, "payment_qr.png")


def write_data_to_excel(xls_creator: XLSCreator, ws: Worksheet, i_row: int, d_data: dict[str, str], title: Optional[str] = None) -> int:
    """!
    @brief Write content to excel
    @param xls_creator : XLS creator
    @param ws : worksheet
    @param i_row : row number
    @param d_data : row data
    @param title : title of data
    @return next row index
    """
    description_column = 1
    content_column = 4
    description_column_letter = get_column_letter(description_column)
    description_column_letter_end = get_column_letter(content_column - 1)
    content_column_letter = get_column_letter(content_column)
    content_column_letter_end = get_column_letter(9)
    if title is not None:
        xls_creator.set_cell(ws, i_row, description_column, title, fill_color=COLOR_LIGHT_BLUE, border=WHITE_BORDER, bold=True)
        xls_creator.set_cell(ws, i_row, content_column, fill_color=COLOR_LIGHT_BLUE, border=WHITE_BORDER, bold=True)
        ws.merge_cells(f"{description_column_letter}{i_row}:{description_column_letter_end}{i_row}")
        ws.merge_cells(f"{content_column_letter}{i_row}:{content_column_letter_end}{i_row}")
        i_row += 1
    i_cnt = 0
    last_section_name = ""
    for description, content in d_data.items():
        if content \
                and (description != "Leistungs-/Abrechnungszeitraum" or content != " bis ") \
                and (description != "Basismenge" or content != 1):
            if content == SECTION_KEY:
                last_section_name = description
            else:
                if last_section_name:
                    fill_color = COLOR_MIDDLE_GREY
                    bold = True
                    xls_creator.set_cell(ws, i_row, description_column, last_section_name, fill_color=fill_color, border=WHITE_BORDER, bold=bold)
                    xls_creator.set_cell(ws, i_row, content_column, "", align="left", wrap_text=True, fill_color=fill_color, border=WHITE_BORDER)
                    ws.merge_cells(f"{description_column_letter}{i_row}:{description_column_letter_end}{i_row}")
                    ws.merge_cells(f"{content_column_letter}{i_row}:I{i_row}")
                    i_cnt = 0  # clear to start with white after section
                    i_row += 1
                    last_section_name = ""
                fill_color = COLOR_LIGHT_GREY if (i_cnt % 2) else None
                xls_creator.set_cell(ws, i_row, description_column, description, fill_color=fill_color, border=WHITE_BORDER)
                xls_creator.set_cell(ws, i_row, content_column, content, align="left", wrap_text=True, fill_color=fill_color, border=WHITE_BORDER)
                ws.merge_cells(f"{description_column_letter}{i_row}:{description_column_letter_end}{i_row}")
                ws.merge_cells(f"{content_column_letter}{i_row}:I{i_row}")
                i_cnt += 1
                i_row += 1
    i_row += 1
    return i_row


def generate_epc_qr(invoice_data: dict[str, Any], box_size: int = 4, border: int = 2):
    if os.path.exists(QR_CODE_FILE_PATH):
        os.remove(QR_CODE_FILE_PATH)

    data_payment = invoice_data["payment"]
    if len(data_payment["methods"]) > 0:
        payment_method = data_payment["methods"][0]
        name = payment_method["accountName"]  # Name des Zahlungskontos (BT-85)
        iban = payment_method["iban"]  # Kennung des Zahlungskontos (BT-84)
        bic = payment_method["bic"]  # Kennung des Zahlungsdienstleisters (BT-86)
        # d_data["Zahlungsart"] = create_value_description(payment_method["typeCode"], D_PAYMENT_METHOD)  # Code für die Zahlungsart D_PAYMENT_METHOD (BT-81)
        # d_data["Name der Bank"] = payment_method["bankName"]  # Name der Bank
    else:
        name = "",
        iban = "",
        bic = ""
    reference = data_payment["reference"]  # Verwendungszweck (BT-83)
    amount = invoice_data["totals"]["dueAmount"]  # Fälliger Betrag (BT-115)
    currency_code = invoice_data["currencyCode"]

    if amount:  # generate only for present amount
        # Build EPC string
        epc_data = [
            "BCD",                    # Service tag (fix)
            "002",                    # Version (001 (older) or 002)
            "1",                      # Character set (1 = UTF-8)
            "SCT",                    # Identification (SEPA Credit Transfer)
            bic,                      # BIC (optional, need in version 1)
            name,                     # Beneficiary name
            iban,                     # IBAN
            f"{currency_code}{amount:.2f}",  # Amount
            "",                       # Purpose (optional)
            reference,                # Structured reference
            ""                        # Unstructured remittance
        ]

        epc_string = "\n".join(epc_data)

        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=box_size, border=border)
        qr.add_data(epc_string)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img.save(QR_CODE_FILE_PATH)
    else:
        img = None
    return img


###########################
##     Create Invoice    ##
###########################

def convert_json_to_invoice(invoice_data: dict[str, Any], e_invoice_option: EInvoiceOption, create_qr_code: bool = False) -> None | str:
    """!
    @brief Convert JSON to invoice.
    @param invoice_data : invoice data as JSON
    @param e_invoice_option : invoice option
    @param create_qr_code : create QR Code status
    @return invoice file name
    """
    fill_invoice_data(invoice_data)

    b_create_xml = bool(e_invoice_option in [EInvoiceOption.XML, EInvoiceOption.ZUGFERD])
    b_create_excel = bool(e_invoice_option in [EInvoiceOption.EXCEL, EInvoiceOption.PDF, EInvoiceOption.ZUGFERD])
    b_convert_to_pdf = bool(e_invoice_option in [EInvoiceOption.PDF, EInvoiceOption.ZUGFERD])
    b_zugferd = bool(e_invoice_option == EInvoiceOption.ZUGFERD)

    if b_create_excel:
        xls_creator = XLSCreator()
        ws = xls_creator.workbook.active
        ws.title = "Rechnung"
        xls_creator.set_page_marcins(ws, left=2.0, right=0.2, top=1.2, bottom=0.5)
        ws.column_dimensions["A"].width = 14
        ws.column_dimensions["B"].width = 10
        i_row = 1
        # logo
        img_path = invoice_data["seller"]["logoData"]
        if img_path and os.path.exists(img_path):
            img = Image(img_path)
            ws.add_image(img, 'H1')
        if b_zugferd:
            ws.add_image(Image(LOGO_ZUGFERD), f"A{i_row}")
            xls_creator.set_cell(ws, i_row, 2, f"invoice by {__title__}", bold=True, italic=True)
        ws.row_dimensions[i_row].height = 19
        i_row += 3
        # QR code
        if create_qr_code:
            qr_code = generate_epc_qr(invoice_data)
            if qr_code and os.path.exists(QR_CODE_FILE_PATH):
                xls_creator.set_cell(ws, i_row, 1, f"Zum Bezahlen scannen")
                i_row += 1
                ws.add_image(Image(QR_CODE_FILE_PATH), f"A{i_row}")
                i_row += 7
        # title
        invoice_title = invoice_data["title"] if invoice_data["title"] else "Rechnung"
        xls_creator.set_cell(ws, i_row, 1, invoice_title, font_size=24)
        i_row += 1

    if b_create_xml:
        doc = convert_json_to_drafthorse_doc(invoice_data)

    if b_create_excel:
        # Header
        d_data = {}
        d_data["Rechnungsnummer"] = invoice_data["number"]  # Rechnungsnummer (BT-1)
        d_data["Rechnungsdatum"] = invoice_data["issueDate"]  # Rechnungsdatum (BT-2)
        d_data["Rechnungstyp"] = create_value_description(invoice_data["typeCode"], D_INVOICE_TYPE)  # Code für den Rechnungstyp (BT-3)
        d_data["Währung"] = create_value_description(invoice_data["currencyCode"], D_CURRENCY)  # Code für die Rechnungswährung (BT-5)
        d_data["Fälligkeitsdatum"] = invoice_data["dueDate"]  # Fälligkeitsdatum der Zahlung (BT-9)
        d_data["Leistungs-/Lieferdatum"] = invoice_data["deliveryDate"]  # Tatsächliches Lieferdatum (BT-72)
        d_data["Leistungs-/Abrechnungszeitraum"] = invoice_data["billingPeriodStartDate"] + " bis " + invoice_data["billingPeriodEndDate"]  # Rechnungszeitraum (BT-73, BT-74)
        d_data["Käuferreferenz"] = invoice_data["buyerReference"]  # Käuferreferenz (BT-10)
        d_data["Projektnummer"] = invoice_data["projectReference"]  # Projektnummer (BT-11)
        d_data["Vertragsnummer"] = invoice_data["contractReference"]  # Vertragsnummer (BT-12)
        d_data["Bestellnummer"] = invoice_data["purchaseOrderReference"]  # Bestellnummer (BT-13)
        d_data["Auftragsnummer"] = invoice_data["salesOrderReference"]  # Auftragsnummer (BT-14)
        receiving_advice_reference = invoice_data.get("receivingAdviceReference", {})  # Wareneingangsmeldung (BT-15)
        if receiving_advice_reference:
            if receiving_advice_reference["id"]:
                text = receiving_advice_reference["id"]
                date = receiving_advice_reference["issueDate"]
                d_data["Wareneingangsmeldung"] = f"{text} ({date})"
        despatch_advice_reference = invoice_data.get("despatchAdviceReference", {})  # Versandanzeige (BT-16)
        if despatch_advice_reference:
            if despatch_advice_reference["id"]:  # write only date if reference exists
                text = despatch_advice_reference["id"]
                date = despatch_advice_reference["issueDate"]
                d_data["Versandanzeige"] = f"{text} ({date})"
        tender_references = invoice_data.get("tenderReferences", [])  # Ausschreibung/Los (BT-17)
        if tender_references:
            for tender_reference in tender_references:
                d_data["Ausschreibung/Los"] = tender_reference["id"]
                break  # only one in dict
        object_references = invoice_data.get("objectReferences", [])  # Objektreferenz (BT-18)
        if object_references:
            for object_reference in object_references:
                d_data["Objektreferenz"] = object_reference["id"]
                break  # only one in dict
        buyer_accounting_accounts = invoice_data.get("buyerAccountingAccounts", [])  # Buchungskonto des Käufers (BT-19)
        if buyer_accounting_accounts:
            for buyer_accounting_account in buyer_accounting_accounts:
                text = buyer_accounting_account["id"]
                if text:
                    d_data["Buchungskonto des Käufers"] = text
                break  # only one in dict
        invoice_references = invoice_data.get("invoiceReferences", [])  # Rechnungsreferenz (BT-25, BT-26)
        if invoice_references:
            for invoice_reference in invoice_references:
                if invoice_reference["id"]:
                    text = invoice_reference["id"]
                    date = invoice_reference["issueDate"]
                    d_data["Rechnungsreferenz"] = f"{text} ({date})"
                break  # only one in dict
        d_data["Bemerkung"] = invoice_data["note"]  # Bemerkung (BT-22)
        d_data["Einleitungstext"] = invoice_data["introText"]  # Einleitungstext
        i_row = write_data_to_excel(xls_creator, ws, i_row, d_data, "Rechnungsdaten")

        # Seller
        d_data = {}
        seller_data = invoice_data["seller"]
        d_data["Unternehmen"] = seller_data["name"]  # Unternehmen (BT-27)
        d_data["Handelsname"] = seller_data["tradeName"]  # Handelsname (BT-28)
        d_data["Verkäuferkennung"] = seller_data["id"]  # Verkäuferkennung (BT-29)
        d_data["Registernummer"] = seller_data["tradeId"]  # Registernummer (BT-30)
        d_data["Umsatzsteuer-ID"] = seller_data["vatId"]  # Umsatzsteuer-ID (BT-31)
        d_data["Steuernummer"] = seller_data["taxId"]  # Steuernummer (BT-32)
        d_data["WEE-Nummer"] = seller_data["weeeId"]  # WEEE-Nummer
        d_data["Rechtliche Informationen"] = seller_data["legalInfo"]  # Rechtliche Informationen (BT-33)
        d_data["Elektronische Adresse"] = seller_data["electronicAddress"]  # Elektronische Adresse (BT-34)
        d_data["Webseite"] = seller_data["websiteText"]  # Webseite Text
        # Anschrift
        seller_address = seller_data["address"]
        d_data["Anschrift"] = SECTION_KEY
        d_data["Straße 1"] = seller_address["line1"]  # Straße 1 (BT-35)
        d_data["Straße 2"] = seller_address["line2"]  # Straße 2 (BT-36)
        d_data["PLZ"] = seller_address["postCode"]  # PLZ (BT-38)
        d_data["Ort"] = seller_address["city"]  # Ort (BT-37)
        d_data["Land"] = create_value_description(seller_address["countryCode"], D_COUNTRY_CODE)  # Land (BT-40) D_COUNTRY_CODE
        # Kontakt
        seller_contact = seller_data["contact"]
        d_data["Kontakt"] = SECTION_KEY
        d_data["Name"] = seller_contact["name"]  # Name (BT-41)
        d_data["E-Mail"] = seller_contact["email"]  # E-Mail (BT-43)
        d_data["Telefon"] = seller_contact["phone"]  # Telefon (BT-42)
        d_data["Fax"] = seller_contact["fax"]  # Fax
        i_row = write_data_to_excel(xls_creator, ws, i_row, d_data, "Rechnungssteller")

        # Buyer
        d_data = {}
        buyer_data = invoice_data["buyer"]
        d_data["Unternehmen"] = buyer_data["name"]  # Unternehmen (BT-44)
        d_data["Handelsname"] = buyer_data["tradeName"]  # Handelsname (BT-45)
        d_data["Käuferkennung"] = buyer_data["id"]  # Käuferkennung (BT-46)
        d_data["Registernummer"] = buyer_data["tradeId"]  # Registernummer (BT-47)
        d_data["Umsatzsteuer-ID"] = buyer_data["vatId"]  # Umsatzsteuer-ID (BT-48)
        d_data["Elektronische Adresse"] = buyer_data["electronicAddress"]  # Elektronische Adresse (BT-49)
        # Anschrift
        buyer_address = buyer_data["address"]
        d_data["Anschrift"] = SECTION_KEY
        d_data["Straße 1"] = buyer_address["line1"]  # Straße 1 (BT-50)
        d_data["Straße 2"] = buyer_address["line2"]  # Straße 2 (BT-51)
        d_data["PLZ"] = buyer_address["postCode"]  # PLZ (BT-53)
        d_data["Ort"] = buyer_address["city"]  # Ort (BT-52)
        d_data["Land"] = create_value_description(buyer_address["countryCode"], D_COUNTRY_CODE)  # Land (BT-55) D_COUNTRY_CODE
        # Kontakt
        buyer_contact = buyer_data["contact"]
        d_data["Kontakt"] = SECTION_KEY
        d_data["Name"] = buyer_contact["name"]  # Name (BT-56)
        d_data["E-Mail"] = buyer_contact["email"]  # E-Mail (BT-58)
        d_data["Telefon"] = buyer_contact["phone"]  # Telefon (BT-57)
        i_row = write_data_to_excel(xls_creator, ws, i_row, d_data, "Rechnungsempfänger")

        # Zahlungsdetails
        d_data = {}
        data_payment = invoice_data["payment"]
        if len(data_payment["methods"]) > 0:
            payment_method = data_payment["methods"][0]
            d_data["Zahlungsart"] = create_value_description(payment_method["typeCode"], D_PAYMENT_METHOD)  # Code für die Zahlungsart D_PAYMENT_METHOD (BT-81)
            d_data["Kontoinhaber"] = payment_method["accountName"]  # Name des Zahlungskontos (BT-85)
            d_data["IBAN"] = payment_method["iban"]  # Kennung des Zahlungskontos (BT-84)
            d_data["BIC"] = payment_method["bic"]  # Kennung des Zahlungsdienstleisters (BT-86)
            d_data["Name der Bank"] = payment_method["bankName"]  # Name der Bank
        d_data["Verwendungszweck"] = data_payment["reference"]  # Verwendungszweck (BT-83)
        d_data["Zahlungsbedienungen"] = data_payment["terms"]  # Zahlungsbedingungen (BT-20)
        i_row = write_data_to_excel(xls_creator, ws, i_row, d_data, "Zahlungsdetails")

        # Lieferdetails
        if "delivery" in invoice_data:
            d_data = {}
            data_delivery = invoice_data["delivery"]
            d_data["Name des Empfängers"] = data_delivery["recipientName"]  # Name des Empfängers (BT-70)
            d_data["Kennung des Lieferorts"] = data_delivery["locationId"]  # Kennung des Lieferorts (BT-71)
            d_data["Lieferadresse"] = SECTION_KEY
            data_delivery_address = data_delivery["address"]
            d_data["Straße 1"] = data_delivery_address["line1"]  # Straße 1 (BT-75)
            d_data["Straße 2"] = data_delivery_address["line2"]  # Straße 2 (BT-76)
            d_data["Zusatz"] = data_delivery_address["line3"]  # Zusatz (BT-165)
            d_data["PLZ"] = data_delivery_address["postCode"]  # PLZ (BT-78)
            d_data["Ort"] = data_delivery_address["city"]  # Ort (BT-77)
            if data_delivery_address["city"]:
                d_data["Land"] = create_value_description(data_delivery_address["countryCode"], D_COUNTRY_CODE)  # Land (BT-80)
            d_data["Region"] = data_delivery_address["region"]  # Region (BT-79)
            i_row = write_data_to_excel(xls_creator, ws, i_row, d_data, "Lieferdetails")

        # Positionen
        for item_number, data_item in enumerate(invoice_data["items"], start=1):
            d_data = {}
            d_data["Name"] = data_item["name"]  # Name (BT-153)
            d_data["Artikel-Nr."] = data_item["id"]  # Artikel-Nr. (BT-155)
            d_data["Steuersatz"] = data_item["vatRate"]  # Steuersatz (BT-152)
            d_data["Steuerkategorie"] = create_value_description(data_item["vatCode"], D_VAT_CODE)  # Steuerkategorie (BT-151)
            d_data["Startdatum"] = data_item["billingPeriodStart"]  # Startdatum (BT-134)
            d_data["Enddatum"] = data_item["billingPeriodEnd"]  # Enddatum (BT-135)
            d_data["Auftragsposition"] = data_item["orderPosition"]  # Auftragsposition (BT-132)
            object_references = data_item.get("objectReferences", [])
            if len(object_references) > 0:
                for object_reference in object_references:
                    d_data["Objektreferenz"] = object_reference.get("id", "")  # Objektreferenz (BT-128)
                    break
            d_data["Beschreibung"] = data_item["description"]  # Beschreibung (BT-154)
            d_data["Menge"] = data_item["quantity"]  # Menge (BT-129)
            d_data["Einheit"] = create_value_description(data_item["quantityUnit"], D_UNIT)  # Einheit (BT-130) D_UNIT
            d_data["Einzelpreis"] = data_item["netUnitPrice"]  # Einzelpreis (Netto) (BT-146)
            d_data["Basismenge"] = data_item["basisQuantity"]  # Basismenge (BT-149)
            d_data["Gesamtpreis (Netto)"] = data_item["netAmount"]  # Gesamtpreis (Netto) (BT-131)
            i_row = write_data_to_excel(xls_creator, ws, i_row, d_data, f"Position {item_number}")

        # Nachlässe
        d_data = {}
        for allowance_data in invoice_data.get("allowances", []):
            d_data["Grundbetrag"] = allowance_data["basisAmount"]  # Grundbetrag (BT-93)
            d_data["Betrag (Netto)"] = allowance_data["netAmount"]  # Betrag (Netto) (BT-92)
            d_data["Prozent"] = allowance_data["percent"]  # Prozent (BT-94)
            d_data["Grund"] = allowance_data["reason"]  # Grund (BT-97)
            d_data["Code des Grundes"] = allowance_data["reasonCode"]  # Code des Grundes (BT-98)
            d_data["Steuerkategorie"] = allowance_data["vatCode"]  # Steuerkategorie (BT-95)
            d_data["Steuersatz"] = allowance_data["vatRate"]  # Steuersatz (BT-96)
            i_row = write_data_to_excel(xls_creator, ws, i_row, d_data, "Nachlass")

        # Zuschlag
        d_data = {}
        for charge_data in invoice_data.get("charges", []):
            d_data["Grundbetrag"] = charge_data["basisAmount"]  # Grundbetrag (BT-100)
            d_data["Betrag (Netto)"] = charge_data["netAmount"]  # Betrag (Netto) (BT-99)
            d_data["Prozent"] = charge_data["percent"]  # Prozent (BT-101)
            d_data["Grund"] = charge_data["reason"]  # Grund (BT-104)
            d_data["Code des Grundes"] = charge_data["reasonCode"]  # Code des Grundes (BT-105)
            d_data["Steuerkategorie"] = charge_data["vatCode"]  # Steuerkategorie (BT-102)
            d_data["Steuersatz"] = charge_data["vatRate"]  # Steuersatz (BT-103)
            i_row = write_data_to_excel(xls_creator, ws, i_row, d_data, "Zuschlag")

        # Steuern
        d_data = {}
        for tax_name, tax_data in invoice_data["taxes"].items():
            d_data["Steuerkategorie"] = create_value_description(tax_data["code"], D_VAT_CODE)  # Steuerkategorie (BT-118)
            d_data["Steuersatz"] = tax_data["rate"]  # Steuersatz (BT-119)
            d_data["Gesamt (Netto)"] = tax_data["netAmount"]  # Gesamt (Netto) (BT-116)
            d_data["Steuerbetrag"] = tax_data["vatAmount"]  # Steuerbetrag (BT-117)
            d_data["Grund der Steuerbefreiung"] = tax_data.get("exemptionReason", "")  # Befreiungsgrund (BT-120)
            d_data["Grund der Steuerbefreiung (Code)"] = tax_data.get("exemptionReasonCode", "")  # Code für Befreiungsgrund (BT-121)
            i_row = write_data_to_excel(xls_creator, ws, i_row, d_data, f"Steuern {tax_name}")

        # Gesamtsummen
        d_data = {}
        data_totals = invoice_data["totals"]
        d_data["Summe Positionen (Netto)"] = data_totals["itemsNetAmount"]  # Summe Positionen (Netto) (BT-106)
        d_data["Summe Zuschläge (Netto)"] = data_totals["chargesNetAmount"]  # Summe Zuschläge (Netto) (BT-108)
        d_data["Summe Nachlässe (Netto)"] = data_totals["allowancesNetAmount"]  # Summe Nachlässe (Netto) (BT-107)
        d_data["Gesamt (Netto)"] = data_totals["netAmount"]  # Gesamt (Netto) (BT-109)
        d_data["Summe Umsatzsteuer"] = data_totals["vatAmount"]  # Summe Umsatzsteuer (BT-110)
        d_data["Gesamt (Brutto)"] = data_totals["grossAmount"]  # Gesamt (Brutto) (BT-112)
        d_data["Gezahlter Betrag"] = data_totals["paidAmount"]  # Gezahlter Betrag (BT-113)
        d_data["Rundungsbetrag"] = data_totals["roundingAmount"]  # Rundungsbetrag (BT-114)
        d_data["Fälliger Betrag"] = data_totals["dueAmount"]  # Fälliger Betrag (BT-115)
        i_row = write_data_to_excel(xls_creator, ws, i_row, d_data, "Gesamtsummen")

    # save file
    if not os.path.exists(EXPORT_PATH):
        os.makedirs(EXPORT_PATH)
    invoice_number = invoice_data["number"]
    buyer_name = invoice_data["buyer"]["name"]  # Unternehmen (BT-44)
    file_description = get_file_name(f"Rechnung_{invoice_number}_{buyer_name}")
    file_name = f"{EXPORT_PATH}/{file_description}"

    valid_xml = True
    if b_create_xml:
        file_name_xml = f"{file_name}.xml"
        valid_xml = create_factur_xml(doc, file_name_xml)

    if b_create_excel:
        file_name_excel = f"{file_name}.xlsx"
        xls_creator.save(filename=file_name_excel)
        if os.path.exists(QR_CODE_FILE_PATH):
            os.remove(QR_CODE_FILE_PATH)

    file_to_open = None
    if b_create_xml:
        file_to_open = file_name_xml
    if valid_xml:  # continue only if xml is valid or not created
        if b_create_excel:
            file_to_open = file_name_excel
        if b_convert_to_pdf:
            # Convert Excel to PDF with LibreOffice
            file_name_pdf = f"{file_name}.pdf"
            convert_xlsx_to_pdf(file_name_excel)
            file_to_open = file_name_pdf
        if b_zugferd:
            # Add XML to PDF
            add_xml_to_pdf(file_name_pdf, file_name_xml)
            # remove Excel and XML File
            os.remove(file_name_xml)
            os.remove(file_name_excel)
    else:
        file_to_open = None  # do not open if failed

    return file_to_open


def create_general_invoice(invoice_data: dict[str, Any], e_invoice_option: EInvoiceOption, create_qr_code: bool) -> None:
    """!
    @brief Create invoice.
    @param invoice_data : invoice data as JSON
    @param e_invoice_option : invoice option
    @param create_qr_code : create qr code
    """
    file = convert_json_to_invoice(invoice_data, e_invoice_option, create_qr_code)

    if file is not None:
        with subprocess.Popen(["start", "", file], shell=True):
            pass
