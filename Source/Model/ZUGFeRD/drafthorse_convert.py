"""!
********************************************************************************
@file   drafthorse_convert.py
@brief  ZUGFeRD convert
********************************************************************************
"""

# pylint: disable=protected-access
from typing import Any
from decimal import Decimal, ROUND_HALF_UP
from drafthorse.models.document import Document


def normalize_decimal(value: Any, max_decimals: int = 4) -> Decimal:
    """!
    @brief Normalize decimal
    @param value : value
    @param max_decimals : maximal decimals
    @return decimal value
    """
    d = Decimal(str(value)).quantize(Decimal("1." + "0" * max_decimals), rounding=ROUND_HALF_UP)
    s = format(d.normalize(), 'f')  # Convert to f-format to avoid exponents
    if '.' in s:  # If there is a decimal point, remove only superfluous decimal places.
        s = s.rstrip('0').rstrip('.')
    if s == '':  # If everything has been removed write 0
        s = '0'
    return Decimal(s)  # convert back to decimal


def convert_to_amount(entry: Any) -> float | None:
    """!
    @brief Convert to amount
    @param entry : entry to convert
    @return float value
    """
    if entry and (entry != " "):
        float_value = float(entry)
    else:
        float_value = None
    return float_value


def convert_to_date_string(entry: Any) -> str:
    """!
    @brief Convert to date string
    @param entry : entry to convert
    @return date string value
    """
    string_value = str(entry)
    if string_value and (string_value != "None") and (string_value != " "):
        string_value = str(entry)
    else:
        string_value = ""
    return string_value


def convert_facturx_to_json(xml_content: bytes) -> dict[str, Any]:
    """!
    @brief Convert facturx to json. See template D_DEFAULT_INVOICE_DATA is based on on PDF24 e-invoice format
    @param xml_content : XML content
    @return JSON content
    """
    doc = Document.parse(xml_content)
    data: dict[str, Any] = {}
    # data[""] = doc.context.guideline_parameter.id  # Anwendungsempfehlung (BT-24) (fix not in json) Code: urn:cen.eu:en16931:2017 Codename: Profile EN16931
    # === Rechnungsdaten ===
    header = doc.header
    data["number"] = str(header.id)  # Rechnungsnummer (BT-1)
    data["issueDate"] = str(header.issue_date_time._value)  # Rechnungsdatum (BT-2)
    data["typeCode"] = str(header.type_code)  # Rechnungstyp (BT-3) D_INVOICE_TYPE
    data["currencyCode"] = str(doc.trade.settlement.currency_code)  # Währung (BT-5) D_CURRENCY
    if len(doc.trade.settlement.terms.children) > 0:
        data["dueDate"] = convert_to_date_string(doc.trade.settlement.terms.children[0].due._value)  # Fälligkeitsdatum (BT-9)
    else:
        data["dueDate"] = ""
    data["deliveryDate"] = convert_to_date_string(doc.trade.delivery.event.occurrence._value)  # Leistungs-/Lieferdatum (BT-72)
    data["billingPeriodStartDate"] = convert_to_date_string(doc.trade.settlement.period.start)  # Leistungs-/Abrechnungszeitraum von (BT-73)
    data["billingPeriodEndDate"] = convert_to_date_string(doc.trade.settlement.period.end)  # Leistungs-/Abrechnungszeitraum bis (BT-74)
    data["buyerReference"] = str(doc.trade.agreement.buyer_reference)  # Käuferreferenz (BT-10)
    data["projectReference"] = str(doc.trade.agreement.procuring_project_type.id)  # Projektnummer (BT-11)
    data["contractReference"] = str(doc.trade.agreement.contract.issuer_assigned_id._text)  # Vertragsnummer (BT-12)
    data["purchaseOrderReference"] = str(doc.trade.agreement.buyer_order.issuer_assigned_id._text)  # Bestellnummer (BT-13)
    data["salesOrderReference"] = str(doc.trade.agreement.seller_order.issuer_assigned_id._text)  # Auftragsnummer (BT-14)
    data_receiving_advice_reference = data.setdefault("receivingAdviceReference", {})
    data_receiving_advice_reference["id"] = str(doc.trade.delivery.receiving_advice.issuer_assigned_id._text)  # Wareneingangsmeldung Nummer (BT-15)
    data_receiving_advice_reference["issueDate"] = convert_to_date_string(doc.trade.delivery.receiving_advice.issue_date_time._value)  # Wareneingangsmeldung Datum (BT-15)
    data_despatch_advice_reference = data.setdefault("despatchAdviceReference", {})
    data_despatch_advice_reference["id"] = str(doc.trade.delivery.despatch_advice.issuer_assigned_id._text)  # Versandanzeige Nummer (BT-16)
    data_despatch_advice_reference["issueDate"] = convert_to_date_string(doc.trade.delivery.despatch_advice.issue_date_time._value)  # Versandanzeige Datum (BT-16)
    data_tender_references = data.setdefault("tenderReferences", [])
    data_object_references = data.setdefault("objectReferences", [])
    for child in doc.trade.agreement.additional_references.children:
        type_code = str(child.type_code)
        reference = {}
        if type_code == "50":  # Ausschreibung/Los (BT-17)
            reference["id"] = str(child.name)
            reference["typeCode"] = type_code
            data_tender_references.append(reference)
        elif type_code == "130":  # Objektreferenz (BT-18)
            reference["id"] = str(child.name)
            reference["typeCode"] = type_code
            data_object_references.append(reference)
    data_buyer_accounting_accounts = data.setdefault("buyerAccountingAccounts", [])
    data_account = {}
    data_account["id"] = str(doc.trade.settlement.accounting_account.id)  # Buchungskonto des Käufers (BT-19)
    data_buyer_accounting_accounts.append(data_account)
    data_invoice_references = data.setdefault("invoiceReferences", [])
    data_invoice = {}
    data_invoice["id"] = str(doc.trade.settlement.invoice_referenced_document.issuer_assigned_id._text)  # Rechnungsreferenz ID (BT-25)
    data_invoice["issueDate"] = convert_to_date_string(doc.trade.settlement.invoice_referenced_document.issue_date_time._value)  # Rechnungsreferenz Datum (BT-26)
    data_invoice_references.append(data_invoice)
    l_notes = []
    for child in header.notes.children:
        l_notes.append(str(child.content))
    data["note"] = "\n".join(l_notes)  # Freitext zur Rechnung (BT-22)
    # === Rechnungssteller ===
    seller = doc.trade.agreement.seller
    data_seller = data.setdefault("seller", {})
    data_seller["name"] = str(seller.name)  # Unternehmen (BT-27)
    # Handelsname (BT-28) Ein Name, unter dem der Verkäufer bekannt ist, sofern abweichend vom Namen des Verkäufers (auch als Firmenname bekannt)
    data_seller["tradeName"] = str(seller.legal_organization.trade_name)
    data_seller["id"] = str(seller.id)  # Verkäuferkennung (BT-29) Kennung des Verkäufers
    data_seller["tradeId"] = str(seller.legal_organization.id._text)  # Registernummer (BT-30)
    data_seller["taxId"] = ""
    data_seller["vatId"] = ""
    for child in seller.tax_registrations.children:
        if child.id._scheme_id == "FC":
            data_seller["taxId"] = str(child.id._text)  # Steuernummer (BT-32)
        elif child.id._scheme_id == "VA":
            data_seller["vatId"] = str(child.id._text)  # Umsatzsteuer-ID (BT-31)
    data_seller["legalInfo"] = str(seller.description)  # Rechtliche Informationen (BT-33)
    data_seller["electronicAddress"] = str(seller.electronic_address.uri_ID._text)  # Elektronische Adresse (BT-34)
    data_seller["electronicAddressTypeCode"] = str(seller.electronic_address.uri_ID._scheme_id)  # Elektronische Adresse (schemeID) (BT-34)
    # Anschrift
    data_seller_address = data_seller.setdefault("address", {})
    data_seller_address["city"] = str(seller.address.city_name)  # Ort (BT-37)
    data_seller_address["countryCode"] = str(seller.address.country_id)  # Land (BT-40)
    data_seller_address["line1"] = str(seller.address.line_one)  # Straße 1 (BT-35)
    data_seller_address["line2"] = str(seller.address.line_two)  # Straße 2 (BT-36)
    data_seller_address["postCode"] = str(seller.address.postcode)  # PLZ (BT-38)
    # Kontakt
    data_seller_contact = data_seller.setdefault("contact", {})
    data_seller_contact["name"] = str(seller.contact.person_name)  # Kontakt Name (BT-41)
    data_seller_contact["email"] = str(seller.contact.email.address)  # Kontakt E-Mail (BT-43)
    data_seller_contact["phone"] = str(seller.contact.telephone.number)  # Kontakt Telefon (BT-42)
    # === Rechnungsempfänger ===
    buyer = doc.trade.agreement.buyer
    data_buyer = data.setdefault("buyer", {})
    data_buyer["name"] = str(buyer.name)  # Unternehmen (BT-44)
    data_buyer["tradeName"] = str(buyer.legal_organization.trade_name)  # Handelsname (BT-45)
    data_buyer["id"] = str(buyer.id)  # Käuferkennung (BT-46) Kennung des Käufers
    data_buyer["tradeId"] = str(buyer.legal_organization.id._text)  # Registernummer (BT-47)
    data_buyer["vatId"] = ""
    for child in buyer.tax_registrations.children:
        if child.id._scheme_id == "VA":
            data_buyer["vatId"] = str(child.id._text)  # Umsatzsteuer-ID (BT-48)
    data_buyer["electronicAddress"] = str(buyer.electronic_address.uri_ID._text)  # Elektronische Adresse (BT-49)
    data_buyer["electronicAddressTypeCode"] = str(seller.electronic_address.uri_ID._scheme_id)  # Elektronische Adresse (schemeID) (BT-49)
    # Anschrift
    data_buyer_address = data_buyer.setdefault("address", {})
    data_buyer_address["city"] = str(buyer.address.city_name)  # Ort (BT-52)
    data_buyer_address["countryCode"] = str(buyer.address.country_id)  # Land (BT-55)
    data_buyer_address["line1"] = str(buyer.address.line_one)  # Straße 1 (BT-50)
    data_buyer_address["line2"] = str(buyer.address.line_two)  # Straße 2 (BT-51)
    data_buyer_address["postCode"] = str(buyer.address.postcode)  # PLZ (BT-53)
    # Kontakt
    data_buyer_contact = data_buyer.setdefault("contact", {})
    data_buyer_contact["name"] = str(buyer.contact.person_name)  # Kontakt Name (BT-56)
    data_buyer_contact["email"] = str(buyer.contact.email.address)  # Kontakt E-Mail (BT-58)
    data_buyer_contact["phone"] = str(buyer.contact.telephone.number)  # Kontakt Telefon (BT-57)
    # === Zahlungsdetails ===
    data_payment = data.setdefault("payment", {})
    data_methods = data_payment.setdefault("methods", [])
    for payment in doc.trade.settlement.payment_means.children:
        data_method = {}
        data_method["typeCode"] = str(payment.type_code)  # Zahlungsart (BT-81)
        data_method["accountName"] = str(payment.payee_account.account_name)  # Kontoinhaber (BT-85)
        data_method["iban"] = str(payment.payee_account.iban)  # IBAN (BT-84)
        data_method["bic"] = str(payment.payee_institution.bic)  # BIC (BT-86)
        data_methods.append(data_method)  # multiple in PDF24 but only one in facturx
    # ---
    data_payment["reference"] = str(doc.trade.settlement.payment_reference)  # Verwendungszweck (BT-83)
    if len(doc.trade.settlement.terms.children) > 0:
        data_payment["terms"] = str(doc.trade.settlement.terms.children[0].description)  # Zahlungsbedienungen (BT-20)
    else:
        data_payment["terms"] = ""
    # === Lieferdetails ===
    delivery = doc.trade.delivery
    data_delivery = data.setdefault("delivery", {})
    data_delivery["recipientName"] = str(delivery.ship_to.name)  # Name des Empfängers (BT-70)
    data_delivery["locationId"] = str(delivery.ship_to.id)  # Kennung des Lieferorts (BT-71)
    # Lieferadresse
    data_delivery_address = data_delivery.setdefault("address", {})
    data_delivery_address["line1"] = str(delivery.ship_to.address.line_one)  # Straße 1 (BT-75)
    data_delivery_address["line2"] = str(delivery.ship_to.address.line_two)  # Straße 2 (BT-76)
    data_delivery_address["line3"] = str(delivery.ship_to.address.line_three)  # Zusatz (BT-165)
    data_delivery_address["postCode"] = str(delivery.ship_to.address.postcode)  # PLZ (BT-78)
    data_delivery_address["city"] = str(delivery.ship_to.address.city_name)  # Ort (BT-77)
    data_delivery_address["countryCode"] = str(delivery.ship_to.address.country_id)  # Land (BT-80)
    data_delivery_address["region"] = str(delivery.ship_to.address.country_subdivision)  # Region (BT-79)
    # Positionen
    data_items = data.setdefault("items", [])
    for child in doc.trade.items.children:
        data_item: dict[str, Any] = {}
        # str(child.document.line_id) Position (BT-126) is index in array
        data_item["name"] = str(child.product.name)  # Name (BT-153)
        data_item["vatRate"] = int(child.settlement.trade_tax.rate_applicable_percent._value)  # Steuersatz (BT-152)
        data_item["vatCode"] = str(child.settlement.trade_tax.category_code)  # Steuerkategorie (BT-151)
        data_item["id"] = str(child.product.seller_assigned_id._text)  # Artikel-Nr. (BT-155)
        data_item["billingPeriodStart"] = convert_to_date_string(child.settlement.period.start)  # Startdatum (BT-134)
        data_item["billingPeriodEnd"] = convert_to_date_string(child.settlement.period.end)  # Enddatum (BT-135)
        data_item["orderPosition"] = str(child.agreement.buyer_order.line_id)  # Auftragsposition (BT-132)
        data_object_references = data_item.setdefault("objectReferences", [])
        data_object = {}
        data_object["id"] = str(child.settlement.additional_referenced_document.uri_id)  # Objektreferenz (BT-128)
        data_object["typeCode"] = str(child.settlement.additional_referenced_document.type_code)  # Objektreferenz (BT-128)
        data_object_references.append(data_object)
        data_item["description"] = str(child.product.description)  # Beschreibung (BT-154)
        data_item["quantity"] = float(child.delivery.billed_quantity._amount)  # Menge (BT-129)
        data_item["quantityUnit"] = str(child.delivery.billed_quantity._unit_code)  # Einheit (BT-130) D_UNIT
        data_item["netUnitPrice"] = float(child.agreement.net.amount._value)  # Einzelpreis (Netto) (BT-146)
        data_item["basisQuantity"] = float(child.agreement.net.basis_quantity._amount or 0)  # Basismenge (BT-149) note: or with 0 if value is empty use 0
        data_item["netAmount"] = float(child.settlement.monetary_summation.total_amount._value)  # Gesamtpreis (Netto) (BT-131)
        # Nachlässe/Zuschläge
        data_item_charges = data_item.setdefault("charges", [])
        data_item_allowances = data_item.setdefault("allowances", [])
        for ac_child in child.settlement.allowance_charge.children:
            data_item_charge: dict[str, Any] = {}
            data_item_charge["basisAmount"] = float(ac_child.basis_amount._value or 0)  # Grundbetrag (nicht in PDF24 aber in xml)
            data_item_charge["percent"] = int(ac_child.calculation_percent._value or 0)  # Prozent BT-138) (BT-143)
            data_item_charge["netAmount"] = float(ac_child.actual_amount._value)  # Betrag (Netto) (BT-136) (BT-141)
            data_item_charge["reason"] = str(ac_child.reason)  # Grund (BT-139) (BT-144)
            data_item_charge["reasonCode"] = str(ac_child.reason_code)  # Code des Grundes (BT-140) (BT-145)
            b_charge = ac_child.indicator._value  # False: allowance; True: charge
            if b_charge:
                data_item_charges.append(data_item_charge)
            else:
                data_item_allowances.append(data_item_charge)
        data_items.append(data_item)
    # Nachlässe/Zuschläge
    data_charges = data.setdefault("charges", [])
    data_allowances = data.setdefault("allowances", [])
    for child in doc.trade.settlement.allowance_charge.children:
        data_charge: dict[str, Any] = {}
        data_charge["basisAmount"] = float(child.basis_amount._value or 0)  # Grundbetrag (BT-93) (BT-100)
        data_charge["percent"] = int(child.calculation_percent._value or 0)  # Prozent (BT-94) (BT-101)
        data_charge["netAmount"] = float(child.actual_amount._value)  # Betrag (Netto) (BT-92) (BT-99)
        data_charge["reason"] = str(child.reason)  # Grund (BT-97) (BT-104)
        data_charge["reasonCode"] = str(child.reason_code)  # Code des Grundes (BT-98) (BT-105)
        for trade_tax in child.trade_tax.children:
            data_charge["vatRate"] = int(trade_tax.rate_applicable_percent._value)  # Steuersatz (BT-96) (BT-103)
            data_charge["vatCode"] = str(trade_tax.category_code)  # Steuerkategorie (BT-95) (BT-102)
            break
        b_charge = child.indicator._value  # False: allowance; True: charge
        if b_charge:
            data_charges.append(data_charge)
        else:
            data_allowances.append(data_charge)
    # Steuern
    data_taxes = data.setdefault("taxes", {})
    for child in doc.trade.settlement.trade_tax.children:
        tax_data: dict[str, Any] = {}
        vat_code = str(child.category_code)
        tax_data["code"] = vat_code  # Steuerkategorie (BT-118)
        tax_data["exemptionReason"] = str(child.exemption_reason)  # Befreiungsgrund (BT-120)
        tax_data["exemptionReasonCode"] = str(child.exemption_reason_code)  # Code für Befreiungsgrund (BT-121)
        tax_data["netAmount"] = float(child.basis_amount._value)  # Gesamt (Netto) (BT-116)
        vat_rate = float(child.rate_applicable_percent._value)
        tax_data["rate"] = vat_rate  # Steuersatz (BT-119)
        tax_data["vatAmount"] = float(child.calculated_amount._value)  # Steuerbetrag (BT-117)
        vat_key = f"{vat_code}-{vat_rate}"
        data_taxes[vat_key] = tax_data
    # Gesamtsummen
    monetary_summation = doc.trade.settlement.monetary_summation
    data_totals = data.setdefault("totals", {})
    data_totals["itemsNetAmount"] = convert_to_amount(monetary_summation.line_total._value)  # Summe Positionen (Netto) (BT-106)
    data_totals["chargesNetAmount"] = convert_to_amount(monetary_summation.charge_total._value)  # Summe Zuschläge (Netto) (BT-108)
    data_totals["allowancesNetAmount"] = convert_to_amount(monetary_summation.allowance_total._value)  # Summe Nachlässe (Netto) (BT-107)
    data_totals["netAmount"] = convert_to_amount(monetary_summation.tax_basis_total._amount)  # Gesamt (Netto) (BT-109)
    data_totals["vatAmount"] = convert_to_amount(monetary_summation.tax_total._amount)  # Summe Umsatzsteuer (BT-110)
    data_totals["grossAmount"] = convert_to_amount(monetary_summation.grand_total._amount)  # Gesamt (Brutto) (BT-112)
    data_totals["paidAmount"] = convert_to_amount(monetary_summation.prepaid_total._value)  # Gezahlter Betrag (BT-113)
    data_totals["roundingAmount"] = convert_to_amount(monetary_summation.rounding_amount._value)  # Rundungsbetrag (BT-114)
    data_totals["dueAmount"] = convert_to_amount(monetary_summation.due_amount._value)  # Fälliger Betrag (BT-115)

    return data
