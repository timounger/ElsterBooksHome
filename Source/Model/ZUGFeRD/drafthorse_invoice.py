"""!
********************************************************************************
@file   drafthorse_invoice.py
@brief  Create drafthorse invoices
********************************************************************************
"""

# pylint: disable=protected-access
import os
import logging
from typing import Optional, Any
from datetime import datetime
from decimal import Decimal
import copy
import shutil
from pathlib import Path
from lxml import etree

from drafthorse.models.accounting import ApplicableTradeTax, TradeAllowanceCharge, CategoryTradeTax
from drafthorse.models.document import Document
from drafthorse.models.note import IncludedNote
from drafthorse.models.tradelines import LineItem
from drafthorse.models.party import TaxRegistration
from drafthorse.models.trade import PaymentTerms, SellerTradeParty
from drafthorse.models.references import AdditionalReferencedDocument
from drafthorse.models.payment import PaymentMeans
from drafthorse.pdf import attach_xml

from Source.version import __title__
from Source.Util.app_data import SCHEMATA_PATH, run_subprocess
from Source.Model.data_handler import DATE_FORMAT_XML, delete_file
from Source.Model.ZUGFeRD.drafthorse_data import EN_16931
from Source.Model.ZUGFeRD.drafthorse_convert import normalize_decimal
from Source.Model.contacts import EContactFields, CONTACT_ADDRESS_FIELD, CONTACT_CONTACT_FIELD
from Source.Model.company import ECompanyFields, COMPANY_ADDRESS_FIELD, COMPANY_CONTACT_FIELD, \
    COMPANY_PAYMENT_FIELD

log = logging.getLogger(__title__)

FACTURE_X_EN16931_SCHEMA_FILE = "3_Factur-X_1.08_EN16931/FACTUR-X_EN16931.xsd"
FACTURE_X_EXTENDED_SCHEMA_FILE = "4_Factur-X_1.08_EXTENDED/FACTUR-X_EXTENDED.xsd"

TAX_TYPE = "VAT"  # fixed value
TAX_CODE = "FC"
UST_CODE = "VA"


###########################
##   Create drafthorse   ##
###########################

def convert_json_to_trade_party(trade_party: SellerTradeParty, trade_party_data: dict[str, str | dict[str, str]]) -> None:
    """!
    @brief Convert JSON to trade party in drafthorse document
    @param trade_party : trade party of drafthorse document
    @param trade_party_data : trade party invoice data
    """
    name = trade_party_data["name"]  # Unternehmen (BT-27)
    trade_name = trade_party_data["tradeName"]  # Handelsname (BT-28)
    ident_id = trade_party_data["id"]  # Verkäuferkennung (BT-29)
    trade_id = trade_party_data["tradeId"]  # Registernummer (BT-30)
    ust_id = trade_party_data["vatId"]  # Umsatzsteuer-ID (BT-31)
    tax_id = trade_party_data["taxId"]  # Steuernummer (BT-32)
    legal_notes = trade_party_data.get("legalInfo", "")  # Rechtliche Informationen (BT-33)
    electronic_address = trade_party_data["electronicAddress"]  # Elektronische Adresse (BT-34)
    # Anschrift
    address_data = trade_party_data["address"]
    street1 = address_data["line1"]  # Straße 1 (BT-35)
    street2 = address_data["line2"]  # Straße 2 (BT-36)
    postcode = address_data["postCode"]  # PLZ (BT-38)
    city = address_data["city"]  # Ort (BT-37)
    country = address_data["countryCode"]  # Land (BT-40) D_COUNTRY_CODE
    # Kontakt
    contact_data = trade_party_data["contact"]
    person = contact_data["name"]  # Name (BT-41)
    email = contact_data["email"]  # E-Mail (BT-43)
    phone = contact_data["phone"]  # Telefon (BT-42)

    trade_party.name = name
    if trade_name:
        trade_party.legal_organization.trade_name = trade_name
    if ident_id:
        trade_party.id = ident_id
    if trade_id:
        trade_party.legal_organization.id = trade_id
    d_tax_data = {TAX_CODE: tax_id, UST_CODE: ust_id}
    for key, value in d_tax_data.items():
        if value:
            tr = TaxRegistration()
            tr.id._text = value
            tr.id._scheme_id = key
            trade_party.tax_registrations.add(tr)
    if legal_notes:
        trade_party.description = legal_notes
    if electronic_address:
        trade_party.electronic_address.uri_ID = electronic_address
    if street1:
        trade_party.address.line_one = street1
    if street2:
        trade_party.address.line_two = street2
    if postcode:
        trade_party.address.postcode = postcode
    if city:
        trade_party.address.city_name = city
    trade_party.address.country_id = country
    if person:
        trade_party.contact.person_name = person
    if email:
        trade_party.contact.email.address = email
    if phone:
        trade_party.contact.telephone.number = phone


def convert_json_to_drafthorse_doc(invoice_data: dict[Any, Any]) -> Document:
    """!
    @brief Convert JSON to drafthorse document
    @param invoice_data : invoice data
    @return filled drafthorse doc
    """
    doc = Document()
    doc.context.guideline_parameter.id = EN_16931

    # Rechnungsdaten
    doc.header.id = invoice_data["number"]  # Rechnungsnummer (BT-1)
    doc.header.issue_date_time = datetime.strptime(invoice_data["issueDate"], DATE_FORMAT_XML)  # Rechnungsdatum (BT-2)  Format: YYYY-MM-DD
    doc.header.type_code = invoice_data["typeCode"]  # Rechnungstyp (BT-3) D_INVOICE_TYPE
    doc.trade.settlement.currency_code = invoice_data["currencyCode"]  # Währung (BT-5) D_CURRENCY
    # Leistungs-/Lieferdatum (BT-72)
    delivery_date = invoice_data.get("deliveryDate", "")
    if delivery_date:
        doc.trade.delivery.event.occurrence = datetime.strptime(delivery_date, DATE_FORMAT_XML)
    # Rechnungszeitraum (BT-73, BT-74)
    from_date = invoice_data.get("billingPeriodStartDate", "")
    to_date = invoice_data.get("billingPeriodEndDate", "")
    if from_date and to_date:
        doc.trade.settlement.period.start = datetime.strptime(from_date, DATE_FORMAT_XML)
        doc.trade.settlement.period.end = datetime.strptime(to_date, DATE_FORMAT_XML)
    doc.trade.agreement.buyer_reference = invoice_data.get("buyerReference", "")  # Käuferreferenz (BT-10)
    project_reference = invoice_data.get("projectReference", "")  # Projektnummer (BT-11)
    if project_reference:
        doc.trade.agreement.procuring_project_type.id = project_reference
        doc.trade.agreement.procuring_project_type.name = "?"  # fix value
    doc.trade.agreement.contract.issuer_assigned_id = invoice_data.get("contractReference", "")  # Vertragsnummer (BT-12)
    doc.trade.agreement.buyer_order.issuer_assigned_id = invoice_data.get("purchaseOrderReference", "")  # Bestellnummer (BT-13)
    doc.trade.agreement.seller_order.issuer_assigned_id = invoice_data.get("salesOrderReference", "")  # Auftragsnummer (BT-14)
    receiving_advice_reference = invoice_data.get("receivingAdviceReference", {})  # Wareneingangsmeldung (BT-15)
    if receiving_advice_reference:
        if receiving_advice_reference["id"]:  # write only date if reference exists
            doc.trade.delivery.receiving_advice.issuer_assigned_id = receiving_advice_reference["id"]
            doc.trade.delivery.receiving_advice.issue_date_time = datetime.strptime(receiving_advice_reference["issueDate"], DATE_FORMAT_XML)
    despatch_advice_reference = invoice_data.get("despatchAdviceReference", {})  # Versandanzeige (BT-16)
    if despatch_advice_reference:
        if despatch_advice_reference["id"]:  # write only date if reference exists
            doc.trade.delivery.despatch_advice.issuer_assigned_id = despatch_advice_reference["id"]
            doc.trade.delivery.despatch_advice.issue_date_time = datetime.strptime(despatch_advice_reference["issueDate"], DATE_FORMAT_XML)
    tender_references = invoice_data.get("tenderReferences", {})  # Ausschreibung/Los (BT-17)
    if tender_references:
        for tender_reference in tender_references:
            if tender_reference["id"]:  # write only date if reference exists
                ref_doc = AdditionalReferencedDocument()
                ref_doc.issuer_assigned_id = tender_reference["id"]
                ref_doc.type_code = tender_reference["typeCode"]
                doc.trade.agreement.additional_references.add(ref_doc)
            break  # only one in dict
    object_references = invoice_data.get("objectReferences", {})  # Objektreferenz (BT-18)
    if object_references:
        for object_reference in object_references:
            if object_reference["id"]:  # write only date if reference exists
                ref_doc = AdditionalReferencedDocument()
                ref_doc.issuer_assigned_id = object_reference["id"]
                ref_doc.type_code = object_reference["typeCode"]
                doc.trade.agreement.additional_references.add(ref_doc)
            break  # only one in dict
    buyer_accounting_accounts = invoice_data.get("buyerAccountingAccounts", {})  # Buchungskonto des Käufers (BT-19)
    if buyer_accounting_accounts:
        for buyer_accounting_account in buyer_accounting_accounts:
            if buyer_accounting_account["id"]:  # write only date if reference exists
                doc.trade.settlement.accounting_account.id = buyer_accounting_account["id"]
            break  # only one in dict
    invoice_references = invoice_data.get("invoiceReferences", {})  # Rechnungsreferenz (BT-25, BT-26)
    if invoice_references:
        for invoice_reference in invoice_references:
            if invoice_reference["id"]:
                doc.trade.settlement.invoice_referenced_document.issuer_assigned_id = invoice_reference["id"]
                doc.trade.settlement.invoice_referenced_document.issue_date_time = datetime.strptime(invoice_reference["issueDate"], DATE_FORMAT_XML)
            break  # only one in dict
    # Bemerkung (BT-22)
    notes = invoice_data["note"]
    if notes:
        if isinstance(notes, list):
            notes = "\n".join(notes)
        doc.header.notes.add(IncludedNote(content=notes))

    # Rechnungssteller
    convert_json_to_trade_party(doc.trade.agreement.seller, invoice_data["seller"])

    # Rechnungsempfänger
    convert_json_to_trade_party(doc.trade.agreement.buyer, invoice_data["buyer"])

    # Zahlungsdetails
    payment = invoice_data["payment"]
    for payment_method in payment["methods"]:
        payment_type = payment_method["typeCode"]  # Zahlungsart (BT-81)
        account_name = payment_method["accountName"]  # Kontoinhaber (BT-85)
        iban = payment_method["iban"]  # IBAN (BT-84)
        bic = payment_method["bic"]  # BIC (BT-86)
        settlement = doc.trade.settlement
        payment_means_option = PaymentMeans()
        payment_means_option.type_code = payment_type
        payment_means_option.payee_account.account_name = account_name
        payment_means_option.payee_account.iban = iban
        payment_means_option.payee_institution.bic = bic
        settlement.payment_means.add(payment_means_option)
    # ---
    reference = payment.get("reference", "")  # Verwendungszweck (BT-83)
    terms = payment.get("terms", "")  # Zahlungsbedingungen (BT-20)
    payment_date = invoice_data.get("dueDate", "")
    if payment_date:
        payment_terms_date = datetime.strptime(payment_date, DATE_FORMAT_XML)  # Fälligkeitsdatum (BT-9)
    else:
        payment_terms_date = None
    if reference:
        settlement.payment_reference = reference
    if terms or payment_terms_date:
        pt = PaymentTerms()
        if terms:
            if isinstance(terms, list):
                terms = "\n".join(terms)
            pt.description = terms
        if payment_terms_date:
            pt.due = payment_terms_date
        settlement.terms.add(pt)

    # Lieferdetails
    if "delivery" in invoice_data:
        data_delivery = invoice_data["delivery"]
        doc.trade.delivery.ship_to.name = data_delivery["recipientName"]  # Name des Empfängers (BT-70)
        doc.trade.delivery.ship_to.id = data_delivery["locationId"]  # Kennung des Lieferorts (BT-71)
        data_delivery_address = data_delivery["address"]
        doc.trade.delivery.ship_to.address.line_one = data_delivery_address["line1"]  # Straße 1 (BT-75)
        doc.trade.delivery.ship_to.address.line_two = data_delivery_address["line2"]  # Straße 2 (BT-76)
        doc.trade.delivery.ship_to.address.line_three = data_delivery_address["line3"]  # Zusatz (BT-165)
        doc.trade.delivery.ship_to.address.postcode = data_delivery_address["postCode"]  # PLZ (BT-78)
        doc.trade.delivery.ship_to.address.city_name = data_delivery_address["city"]  # Ort (BT-77)
        doc.trade.delivery.ship_to.address.country_id = data_delivery_address["countryCode"]  # Land (BT-80)
        doc.trade.delivery.ship_to.address.country_subdivision = data_delivery_address["region"]  # Region (BT-79)

    # Positionen
    for item_number, item_data in enumerate(invoice_data["items"], start=1):
        li = LineItem()
        li.document.line_id = str(item_number)  # Position (BT-126)
        li.product.name = item_data["name"]  # Name (BT-153)
        li.product.seller_assigned_id = item_data.get("id", "")  # Artikel-Nr. (BT-155)
        vat_rate = item_data["vatRate"]  # Steuersatz (BT-152)
        li.settlement.trade_tax.rate_applicable_percent = Decimal(f"{vat_rate:.2f}")
        li.settlement.trade_tax.category_code = item_data["vatCode"]  # Steuerkategorie (BT-151)
        if item_data.get("billingPeriodStart", ""):
            li.settlement.period.start = datetime.strptime(item_data["billingPeriodStart"], DATE_FORMAT_XML)  # Startdatum (BT-134)
        if item_data.get("billingPeriodEnd", ""):
            li.settlement.period.end = datetime.strptime(item_data["billingPeriodEnd"], DATE_FORMAT_XML)  # Enddatum (BT-135)
        li.agreement.buyer_order.line_id = item_data.get("orderPosition", "")  # Auftragsposition (BT-132)
        object_references = item_data.setdefault("objectReferences", [])  # Objektreferenz (BT-128)
        for object_reference in object_references:
            li.settlement.additional_referenced_document.issuer_assigned_id = object_reference["id"]
            li.settlement.additional_referenced_document.type_code = object_reference["typeCode"]
            break  # only one possible
        description = item_data.get("description", "")  # Beschreibung (BT-154)
        if description:
            li.product.description = description
        quantity = item_data["quantity"]  # Menge (BT-129)
        normalized_quantity = normalize_decimal(quantity)  # use only required floating data (up to 4)
        quantity_unit = item_data["quantityUnit"]  # Einheit (BT-130) D_UNIT
        li.delivery.billed_quantity = (normalized_quantity, quantity_unit)
        price = item_data["netUnitPrice"]  # Einzelpreis (Netto) (BT-146)
        li.agreement.net.amount = Decimal(f"{price:.2f}")
        li.settlement.trade_tax.type_code = TAX_TYPE
        basis_quantity = item_data.get("basisQuantity", 1)
        if basis_quantity not in [0, 1]:  # write only if required
            normalized_basis_quantity = normalize_decimal(basis_quantity)  # use only required floating data (up to 4)
            li.agreement.net.basis_quantity = (normalized_basis_quantity, quantity_unit)  # Basismenge (BT-149)
        sum_price = item_data["netAmount"]  # Gesamtpreis (Netto) (BT-131)
        li.settlement.monetary_summation.total_amount = Decimal(f"{sum_price:.2f}")
        # Nachlässe
        for allowance_data in item_data.get("allowances", []):
            trade_allowance = TradeAllowanceCharge()
            trade_allowance.indicator = False
            basis_amount = sum_price  # TODO Wert stimmt nicht mehr wenn oben Zu/Abschläge einberechnet werden "basisAmount" verwenden
            trade_allowance.basis_amount = Decimal(f"{basis_amount:.2f}")
            net_amount = allowance_data["netAmount"]  # Betrag (Netto) (BT-136)
            trade_allowance.actual_amount = Decimal(f"{net_amount:.2f}")
            percent = allowance_data["percent"]  # Prozent (BT-138)
            trade_allowance.calculation_percent = Decimal(f"{percent:.2f}")
            trade_allowance.reason = allowance_data["reason"]  # Grund (BT-139)
            trade_allowance.reason_code = allowance_data["reasonCode"]  # Code des Grundes (BT-140)
            li.settlement.allowance_charge.add(trade_allowance)
        # Zuschläge
        for charge_data in item_data.get("charges", []):
            trade_charge = TradeAllowanceCharge()
            trade_charge.indicator = True
            basis_amount = sum_price  # TODO Wert stimmt nicht mehr wenn oben Zu/Abschläge einberechnet werden "basisAmount" verwenden
            trade_charge.basis_amount = Decimal(f"{basis_amount:.2f}")
            net_amount = charge_data["netAmount"]  # Betrag (Netto) (BT-141)
            trade_charge.actual_amount = Decimal(f"{net_amount:.2f}")
            percent = charge_data["percent"]  # Prozent (BT-143)
            trade_charge.calculation_percent = Decimal(f"{percent:.2f}")
            trade_charge.reason = charge_data["reason"]  # Grund (BT-144)
            trade_charge.reason_code = charge_data["reasonCode"]  # Code des Grundes (BT-145)
            li.settlement.allowance_charge.add(trade_charge)
        doc.trade.items.add(li)

    # Nachlässe
    for allowance_data in invoice_data.get("allowances", []):
        trade_allowance = TradeAllowanceCharge()
        trade_allowance.indicator = False
        basis_amount = allowance_data["basisAmount"]  # Grundbetrag (BT-93)
        trade_allowance.basis_amount = Decimal(f"{basis_amount:.2f}")
        net_amount = allowance_data["netAmount"]  # Betrag (Netto) (BT-92)
        trade_allowance.actual_amount = Decimal(f"{net_amount:.2f}")
        percent = allowance_data["percent"]  # Prozent (BT-94)
        trade_allowance.calculation_percent = Decimal(f"{percent:.2f}")
        trade_allowance.reason = allowance_data["reason"]  # Grund (BT-97)
        trade_allowance.reason_code = allowance_data["reasonCode"]  # Code des Grundes (BT-98)
        trade_tax = CategoryTradeTax()
        trade_tax.category_code = allowance_data["vatCode"]  # Steuerkategorie (BT-95)
        vat_rate = allowance_data["vatRate"]  # Steuersatz (BT-96)
        trade_tax.rate_applicable_percent = Decimal(f"{vat_rate:.2f}")
        trade_tax.type_code = TAX_TYPE
        trade_allowance.trade_tax.add(trade_tax)
        doc.trade.settlement.allowance_charge.add(trade_allowance)

    # Zuschläge
    for charge_data in invoice_data.get("charges", []):
        trade_charge = TradeAllowanceCharge()
        trade_charge.indicator = True
        basis_amount = charge_data["basisAmount"]  # Grundbetrag (BT-100)
        trade_charge.basis_amount = Decimal(f"{basis_amount:.2f}")
        net_amount = charge_data["netAmount"]  # Betrag (Netto) (BT-99)
        trade_charge.actual_amount = Decimal(f"{net_amount:.2f}")
        percent = charge_data["percent"]  # Prozent (BT-101)
        trade_charge.calculation_percent = Decimal(f"{percent:.2f}")
        trade_charge.reason = charge_data["reason"]  # Grund (BT-104)
        trade_charge.reason_code = charge_data["reasonCode"]  # Code des Grundes (BT-105)
        trade_tax = CategoryTradeTax()
        trade_tax.category_code = charge_data["vatCode"]  # Steuerkategorie (BT-102)
        vat_rate = charge_data["vatRate"]  # Steuersatz (BT-103)
        trade_tax.rate_applicable_percent = Decimal(f"{vat_rate:.2f}")
        trade_tax.type_code = TAX_TYPE
        trade_charge.trade_tax.add(trade_tax)
        doc.trade.settlement.allowance_charge.add(trade_charge)

    # Steuern
    for _tax_name, tax_data in invoice_data["taxes"].items():
        trade_tax = ApplicableTradeTax()
        tax_sum = tax_data["vatAmount"]  # Steuerbetrag (BT-117)
        trade_tax.calculated_amount = Decimal(f"{tax_sum:.2f}")
        net_sum = tax_data["netAmount"]  # Gesamt (Netto) (BT-116)
        trade_tax.basis_amount = Decimal(f"{net_sum:.2f}")
        trade_tax.type_code = TAX_TYPE
        trade_tax.category_code = tax_data["code"]  # Steuerkategorie (BT-118)
        tax_rate = tax_data["rate"]  # Steuersatz (BT-119)
        trade_tax.rate_applicable_percent = Decimal(f"{tax_rate:.2f}")
        exemption_reason = tax_data.get("exemptionReason", "")
        if exemption_reason:
            trade_tax.exemption_reason = exemption_reason  # Befreiungsgrund (BT-120)
        exemption_reason_code = tax_data.get("exemptionReasonCode", "")
        if exemption_reason_code:
            trade_tax.exemption_reason_code = exemption_reason_code  # Code für Befreiungsgrund (BT-121)
        doc.trade.settlement.trade_tax.add(trade_tax)

    # Gesamtsummen
    data_totals = invoice_data["totals"]
    settlement = doc.trade.settlement
    line_total = data_totals["itemsNetAmount"]  # Summe Positionen (Netto) (BT-106)
    settlement.monetary_summation.line_total = Decimal(f"{line_total:.2f}")
    charge_total = data_totals["chargesNetAmount"]  # Summe Zuschläge (Netto) (BT-108)
    if charge_total != 0:  # optional field write only if required
        settlement.monetary_summation.charge_total = Decimal(f"{charge_total:.2f}")
    allowance_total = data_totals["allowancesNetAmount"]  # Summe Nachlässe (Netto) (BT-107)
    if allowance_total != 0:  # optional field write only if required
        settlement.monetary_summation.allowance_total = Decimal(f"{allowance_total:.2f}")
    tax_basis_total = data_totals["netAmount"]  # Gesamt (Netto) (BT-109)
    settlement.monetary_summation.tax_basis_total = Decimal(f"{tax_basis_total:.2f}")
    prepaid_total = data_totals["paidAmount"]  # Gezahlter Betrag (BT-113)
    if prepaid_total != 0:  # optional field write only if required
        settlement.monetary_summation.prepaid_total = Decimal(f"{prepaid_total:.2f}")
    rounding_amount = data_totals["roundingAmount"]  # Rundungsbetrag (BT-114)
    if rounding_amount != 0:  # optional field write only if required
        settlement.monetary_summation.rounding_amount = Decimal(f"{rounding_amount:.2f}")
    tax_total = data_totals["vatAmount"]  # Summe Umsatzsteuer (BT-110)
    currency_code = invoice_data["currencyCode"]  # Währung (BT-5) D_CURRENCY
    settlement.monetary_summation.tax_total = (Decimal(f"{tax_total:.2f}"), currency_code)  # currency required at this field
    grand_total = data_totals["grossAmount"]  # Gesamt (Brutto) (BT-112)
    settlement.monetary_summation.grand_total = Decimal(f"{grand_total:.2f}")
    due_amount = data_totals["dueAmount"]  # Fälliger Betrag (BT-115)
    settlement.monetary_summation.due_amount = Decimal(f"{due_amount:.2f}")

    return doc


def eval_factur_xml(xml_file_path: str | bytes, extended: bool = False) -> tuple[bool, str]:
    """!
    @brief Evaluate facture xml
    @param xml_file_path : xml file path or content
    @param extended : True: check for extended; False: check for EN16931
    @return valid state
    """
    # load XSD scheme
    warning_text = ""
    scheme_file = FACTURE_X_EXTENDED_SCHEMA_FILE if extended else FACTURE_X_EN16931_SCHEMA_FILE
    xsd_file = os.path.join(SCHEMATA_PATH, scheme_file)
    with open(xsd_file, 'rb') as f:
        schema_doc = etree.parse(f)
        schema = etree.XMLSchema(schema_doc)

    xml_doc = None
    if isinstance(xml_file_path, bytes):
        xml_doc = etree.fromstring(xml_file_path)
    else:
        try:
            with open(xml_file_path, 'rb') as f:
                xml_doc = etree.parse(f)
        except (etree.XMLSchemaParseError, etree.XMLSyntaxError) as _e:
            xml_doc = None

    if xml_doc is not None:
        is_valid = schema.validate(xml_doc)

        if not is_valid:
            warning_text = "Invalid XML Scheme:"
            for error in schema.error_log:  # pylint: disable=not-an-iterable
                warning_text += f"\n{error.message} (Line {error.line})"
            log.info(warning_text)
    else:
        is_valid = False
        warning_text = f"Invalid XML File: {xml_file_path}"
        log.warning(warning_text)
    return is_valid, warning_text


def create_factur_xml(doc: Document, file_name_xml: str) -> bool:
    """!
    @brief Create facture xml
    @param doc : document
    @param file_name_xml : xml file name to create
    @return valid status of xml
    """
    # Possible schema: FACTUR-X_MINIMUM, FACTUR-X_BASIC, FACTUR-X_BASICWL, FACTUR-X_EN16931, FACTUR-X_EXTENDED
    xml = doc.serialize(schema="FACTUR-X_EN16931")
    with open(file_name_xml, mode="w", encoding="utf-8") as file:
        file.write(xml.decode("utf-8"))
    is_valid, _warning_text = eval_factur_xml(file_name_xml)
    if not is_valid:
        log.error("Remove Invalid XMl file: %s", file_name_xml)
        delete_file(file_name_xml)  # delete if not valid
    return is_valid


def write_customer_to_json(invoice_data: dict, contact: dict[str, str | dict[str, str]]) -> None:
    """!
    @brief Write customer to buyer in JSON
    @param invoice_data : invoice data
    @param contact : contact data
    """
    data_buyer = invoice_data.setdefault("buyer", {})
    if contact:
        data_buyer["name"] = contact[EContactFields.NAME]  # Name des Käufers (BT-44) TODO textumbruch benötigt?
        data_buyer["tradeName"] = contact[EContactFields.TRADE_NAME]  # Handelsname (BT-45)
        data_buyer["id"] = contact[EContactFields.CUSTOMER_NUMBER]  # Käuferkennung (BT-46)
        data_buyer["tradeId"] = contact[EContactFields.TRADE_ID]  # Registernummer (BT-47)
        data_buyer["vatId"] = contact[EContactFields.VAT_ID]  # Umsatzsteuer-Identifikationsnummer des Käufers (BT-48)
        data_buyer["electronicAddress"] = contact[EContactFields.ELECTRONIC_ADDRESS]  # Elektronische Adresse (BT-49)
        address_data = contact[CONTACT_ADDRESS_FIELD]
        data_buyer_address = data_buyer.setdefault("address", {})
        data_buyer_address["line1"] = address_data[EContactFields.STREET_1]  # Zeile 1 der Käuferanschrift (BT-50)
        data_buyer_address["line2"] = address_data[EContactFields.STREET_2]  # Zeile 2 der Käuferanschrift (BT-51)
        data_buyer_address["postCode"] = address_data[EContactFields.PLZ]  # Postleitzahl der Käuferanschrift (BT-53)
        data_buyer_address["city"] = address_data[EContactFields.CITY]  # Stadt der Käuferanschrift (BT-52)
        data_buyer_address["countryCode"] = address_data[EContactFields.COUNTRY]  # Ländercode der Käuferanschrift (BT-55)
        contact_data = contact[CONTACT_CONTACT_FIELD]
        data_buyer_contact = data_buyer.setdefault("contact", {})
        data_buyer_contact["name"] = f"{contact_data[EContactFields.FIRST_NAME]} {contact_data[EContactFields.LAST_NAME]}".strip()  # Kontaktstelle des Käufers (BT-56)
        data_buyer_contact["email"] = contact_data[EContactFields.MAIL]  # E-Mail-Adresse der Kontaktstelle des Käufers (BT-58)
        data_buyer_contact["phone"] = contact_data[EContactFields.PHONE]  # Telefonnummer der Kontaktstelle des Käufers (BT-57)


def write_company_to_json(invoice_data: dict, company: dict[Any, Any], logo_path: Optional[str] = None) -> None:
    """!
    @brief Write customer to buyer in JSON
    @param invoice_data : invoice data
    @param company : company data
    @param logo_path : logo path
    """
    data_seller = invoice_data.setdefault("seller", {})
    data_seller["name"] = company[ECompanyFields.NAME]  # Unternehmen (BT-27)
    data_seller["tradeName"] = company[ECompanyFields.TRADE_NAME]  # Handelsname (BT-28)
    data_seller["id"] = ""  # Verkäuferkennung (BT-29)
    data_seller["tradeId"] = company[ECompanyFields.TRADE_ID]  # Registernummer (BT-30)
    data_seller["vatId"] = company[ECompanyFields.VAT_ID]  # Umsatzsteuer-ID (BT-31)
    data_seller["taxId"] = company[ECompanyFields.TAX_ID]  # Steuernummer (BT-32)
    data_seller["weeeId"] = ""  # WEE-Nummer
    data_seller["legalInfo"] = company[ECompanyFields.LEGAL_INFO]  # Rechtliche Informationen (BT-33)
    data_seller["electronicAddress"] = company[ECompanyFields.ELECTRONIC_ADDRESS]  # Elektronische Adresse (BT-34)
    data_seller["websiteText"] = company[ECompanyFields.WEBSITE_TEXT]  # Webseite Text
    data_seller["logoData"] = logo_path if logo_path else ""  # logo
    address_data = company[COMPANY_ADDRESS_FIELD]
    data_seller_address = data_seller.setdefault("address", {})
    data_seller_address["line1"] = address_data[ECompanyFields.STREET_1]  # Straße 1 (BT-35)
    data_seller_address["line2"] = address_data[ECompanyFields.STREET_2]  # Straße 2 (BT-36)
    data_seller_address["postCode"] = address_data[ECompanyFields.PLZ]  # PLZ (BT-38)
    data_seller_address["city"] = address_data[ECompanyFields.CITY]  # Ort (BT-37)
    data_seller_address["countryCode"] = address_data[ECompanyFields.COUNTRY]  # Land (BT-40) D_COUNTRY_CODE
    contact_data = company[COMPANY_CONTACT_FIELD]
    data_seller_contact = data_seller.setdefault("contact", {})
    data_seller_contact["name"] = f"{contact_data[ECompanyFields.FIRST_NAME]} {contact_data[ECompanyFields.LAST_NAME]}".strip()  # Name (BT-41)
    data_seller_contact["email"] = contact_data[ECompanyFields.MAIL]  # E-Mail (BT-43)
    data_seller_contact["phone"] = contact_data[ECompanyFields.PHONE]  # Telefon (BT-42)
    data_seller_contact["fax"] = ""  # Fax

    payment_data = company[COMPANY_PAYMENT_FIELD]
    data_payment = invoice_data.setdefault("payment", {})
    data_methods = data_payment.setdefault("methods", [])
    method = {}
    method["bankName"] = payment_data[ECompanyFields.BANK_NAME]  # Name der Bank
    method["bic"] = payment_data[ECompanyFields.BANK_BIC]  # BIC (BT-86)
    method["iban"] = payment_data[ECompanyFields.BANK_IBAN]  # IBAN (BT-84)
    method["accountName"] = payment_data[ECompanyFields.BANK_OWNER]  # Kontoinhaber (BT-85)
    method["typeCode"] = "58"  # Zahlungsart (BT-81) D_PAYMENT_METHOD
    data_methods.append(method)


def fill_invoice_data(invoice_data: dict) -> None:
    """!
    @brief Fill invoice data
    @param invoice_data : invoice data
    """
    if not invoice_data["seller"]["taxId"]:
        invoice_data["seller"]["taxId"] = "KEINE"  # required for seller
    if not invoice_data["seller"]["vatId"]:
        invoice_data["seller"]["vatId"] = "KEINE"  # required for seller
    if "taxId" not in invoice_data["buyer"]:
        invoice_data["buyer"]["taxId"] = ""  # set empty for common trade party

    INVOICE_NUMBER_PATTERN = "{number}"
    invoice_data["payment"]["reference"] = invoice_data["payment"]["reference"].replace(INVOICE_NUMBER_PATTERN, invoice_data["number"])

    tax_data = {}
    items_net_amount = 0
    total_gross = 0
    total_vat = 0
    tax_data_copy = copy.deepcopy(invoice_data.get("taxes", {}))

    for data_item in invoice_data["items"]:
        item_quantity = data_item["quantity"]  # Menge (BT-129)
        item_basis_quantity = data_item.get("basisQuantity", 1)  # Basismenge (BT-149)
        net_unit_price = data_item["netUnitPrice"]  # Einzelpreis (Netto) (BT-146)
        vat_rate = data_item["vatRate"]  # Steuersatz (BT-152)
        vat_code = data_item["vatCode"]  # Code der Umsatzsteuerkategorie des in Rechnung gestellten Artikels (BT-151)

        gross_unit_price = round(net_unit_price * (1 + (vat_rate / 100)), 2)
        net_amount = (item_quantity * net_unit_price) / item_basis_quantity
        gross_amount = (item_quantity * gross_unit_price) / item_basis_quantity
        vat_amount = gross_amount - net_amount
        vat_rate_normalized = normalize_decimal(vat_rate)
        vat_key = f"{vat_code}-{vat_rate_normalized}"
        if vat_key in tax_data:
            tax_data[vat_key]["netAmount"] += net_amount
            tax_data[vat_key]["vatAmount"] += vat_amount
        else:
            if vat_key in tax_data_copy:
                exemption_reason = tax_data_copy[vat_key].get("exemptionReason", "")  # Befreiungsgrund (BT-120)
                exemption_reason_code = tax_data_copy[vat_key].get("exemptionReasonCode", "")  # Code für Befreiungsgrund (BT-121)
            else:
                exemption_reason = ""
                exemption_reason_code = ""
            vat_value = {
                "code": vat_code,
                "exemptionReason": exemption_reason,
                "exemptionReasonCode": exemption_reason_code,
                "netAmount": net_amount,
                "rate": vat_rate,
                "vatAmount": vat_amount
            }
            tax_data[vat_key] = vat_value
        items_net_amount += net_amount
        total_gross += gross_amount
        total_vat += vat_amount

        data_item["netAmount"] = net_amount  # Gesamtpreis (Netto) (BT-131)
        data_item["vatAmount"] = vat_amount  # Steuerbetrag
        data_item["grossAmount"] = gross_amount  # Gesamtpreis (Brutto)
        data_item["grossUnitPrice"] = gross_unit_price  # Einzelpreis (Brutto)

    # TODO Zuschläge und Nachlässe berücksichtigen

    invoice_data["taxes"] = tax_data

    data_totals = invoice_data["totals"]
    data_totals["itemsNetAmount"] = items_net_amount  # Summe Positionen (Netto) (BT-106)
    data_totals["chargesNetAmount"] = 0  # TODO
    data_totals["allowancesNetAmount"] = 0  # TODO
    charges_net_amount = data_totals["chargesNetAmount"]  # Summe Zuschläge (Netto) (BT-108)
    allowances_net_amount = data_totals["allowancesNetAmount"]  # Summe Nachlässe (Netto) (BT-107)
    paid_amount = data_totals["paidAmount"]  # Gezahlter Betrag (BT-113)
    rounding_amount = data_totals["roundingAmount"]  # Rundungsbetrag (BT-114)
    data_totals["netAmount"] = round(items_net_amount + charges_net_amount - allowances_net_amount, 2)  # Gesamt (Netto) (BT-109)
    data_totals["vatAmount"] = round(total_vat, 2)  # Summe Umsatzsteuer (BT-110)
    data_totals["grossAmount"] = round(total_gross, 2)  # Gesamt (Brutto) (BT-112)
    data_totals["dueAmount"] = round((total_gross + rounding_amount) - paid_amount, 2)  # Fälliger Betrag (BT-115)


def add_xml_to_pdf(pdf_file: str, xml_file: str) -> None:
    """!
    @brief Attach XML to an existing PDF.
           Note that the existing PDF should be compliant to PDF/A-3!
           You can validate this here: https://www.pdf-online.com/osa/validate.aspx
    @param pdf_file : PDF file
    @param xml_file : XML file
    """
    with open(xml_file, 'rb') as file:
        xml_data = file.read()

    with open(pdf_file, "rb") as file:
        new_pdf_bytes = attach_xml(file.read(), xml_data)

    with open(pdf_file, "wb") as f:
        f.write(new_pdf_bytes)


def set_valid_pdf_profile(pdf_file: str) -> None:
    """!
    @brief Set valid profile in PDF via ghostscript.
    @param pdf_file : PDF file
    """
    file_path = Path(pdf_file)
    temp_file = file_path.with_name(file_path.stem + "_temp.pdf")
    shutil.copy2(pdf_file, temp_file)
    gs_command = [
        "gswin64c",
        "-dPDFA=3",
        "-dBATCH",
        "-dNOPAUSE",
        "-sDEVICE=pdfwrite",
        "-dPDFACompatibilityPolicy=1",
        "-dUseCIEColor=true",  # zwingt CIE-basierte Farbkonvertierung
        "-sColorConversionStrategy=RGB",
        "-sProcessColorModel=DeviceRGB",
        "-sPDFACompatibilityPolicy=1",
        # r"-sOutputICCProfile=C:\Windows\System32\spool\drivers\color\sRGB Color Space Profile.icm",
        # r"-sOutputICCProfile=C:\Program Files\gs\gs9.56.1\iccprofiles\srgb.icc",
        "-dEmbedAllFonts=true",
        "-dSubsetFonts=false",
        f"-sOutputFile={pdf_file}",
        temp_file,
    ]
    _result = run_subprocess(gs_command)
    delete_file(temp_file)
