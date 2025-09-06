"""!
********************************************************************************
@file   drafthorse_data.py
@brief  ZUGFeRD data
        For new drafthorse data add to following functions:
        - Doku: D_DEFAULT_INVOICE_DATA
        - View XML: convert_facturx_to_json
        - View XML: visualize_xml_invoice
        - Write XML: convert_json_to_drafthorse_doc
        - JSON Export: read_ui_data_to_json
        - JSON Import: write_json_data_to_ui
        - EXCEL: convert_json_to_invoice
********************************************************************************
"""

EN_16931 = "urn:cen.eu:en16931:2017"  # COMFORT
# EXTENDED = "urn:cen.eu:en16931:2017#conformant#urn:factur-x.eu:1p0:extended"
# BASIC = "urn:cen.eu:en16931:2017#compliant#urn:factur-x.eu:1p0:basic"
# BASIC_WL = "urn:factur-x.eu:1p0:basicwl"
# MINIMUM = "urn:factur-x.eu:1p0:minimum"

# ZUGFeRD data in json format
# PDF24 Creator - Modul: Rechnung erstellen
# Version 11.26.1

# Rechnungstyp (BT-3) Code für den Rechnungstyp
D_INVOICE_TYPE = {
    # "71": "Request for payment",
    # "80": "Debit note related to goods or services",
    # "81": "Credit note related to goods or services",
    # "82": "Metered services invoice",
    # "83": "Credit note related to financial adjustments",
    # "84": "Debit note related to financial adjustments",
    # "102": "Tax notification",
    # "130": "Rechnungsdatenblatt",
    # "202": "Verkürzte Baurechnung",
    # "203": "Vorläufige Baurechnung",
    # "204": "Baurechnung",
    # "211": "Zwischen-(abschlags-)rechnung",
    # "218": "Final payment request based on completion of work",
    # "219": "Payment request for completed units",
    # "261": "Self billed credit note",
    # "262": "Consolidated credit note - goods and services",
    # "295": "Price variation invoice",
    # "296": "Credit note for price variation",
    # "308": "Delcredere credit note",
    "325": "Proformarechnung",
    "326": "Teilrechnung",
    # "331": "Commercial invoice which includes a packing list",
    "380": "Rechnung",  # Default  Handelsrechnung
    "381": "Gutschriftanzeige",
    # "382": "Provisionsmitteilung",
    "383": "Belastungsanzeige",
    "384": "Rechnungskorrektur",
    # "385": "Konsolidierte Rechnung",
    "386": "Vorauszahlungsrechnung",
    "387": "Mietrechnung",
    "388": "Steuerrechnung",
    "389": "Selbstfakturierte Rechnung",  # Selbst ausgestellte Rechnung (Gutschrift im Gutschriftsverfahren)
    # "390": "Delkredere-Rechnung",
    "393": "Inkasso-Rechnung",
    "394": "Leasing-Rechnung",
    # "395": "Konsignationsrechnung",
    # "396": "Inkasso-Gutschrift",
    # "420": "Optical Character Reading (OCR) payment credit note",
    # "456": "Belastungsanzeige"
    # "457": "Storno einer Belastung",
    # "458": "Storno einer Gutschrift",
    # "527": "Self billed debit note",
    # "532": "Gutschrift des Spediteurs",
    # "553": "Forwarder’s invoice discrepancy report",
    "575": "Rechnung des Versicherers",
    "623": "Speditionsrechnung",
    # "633": "Hafenkostenrechnung",
    # "751": "Invoice information for accounting purposes",
    "780": "Frachtrechnung",
    # "817": "Claim notification",
    # "870": "Konsulatsfaktura",
    "875": "Teilrechnung für Bauleistungen",  # Partial construction invoice
    "876": "Teilschlussrechnung für Bauleistungen",  # Partial final construction invoice
    "877": "Schlussrechnung für Bauleistungen",  # Final construction invoice
    "935": "Zollrechnung"
}

# Währung (BT-5)
# ISO 4217 Maintenance Agency „Codes for the representation of currencies and funds"
# https://www.iso.org/iso-4217-currency-codes.html
D_CURRENCY = {
    "AED": "United Arab Emirates Dirham - د.إ",
    "AFN": "Afghan Afghani - ؋",
    "ALL": "Albanian Lek - L",
    "AMD": "Armenian Dram - ֏",
    "ANG": "Netherlands Antillean Guilder - ƒ",
    "AOA": "Angolan Kwanza - Kz",
    "ARS": "Argentine Peso - $",
    "AUD": "Australian Dollar - A$",
    "AWG": "Aruban Florin - ƒ",
    "AZN": "Azerbaijani Manat - ₼",
    "BAM": "Bosnia and Herzegovina Convertible Mark - KM",
    "BBD": "Barbadian Dollar - Bds$",
    "BDT": "Bangladeshi Taka - ৳",
    "BGN": "Bulgarian Lev - лв",
    "BHD": "Bahraini Dinar - .د.ب",
    "BIF": "Burundian Franc - FBu",
    "BMD": "Bermudian Dollar - $",
    "BND": "Brunei Dollar - B$",
    "BOB": "Bolivian Boliviano - Bs.",
    "BRL": "Brazilian Real - R$",
    "BSD": "Bahamian Dollar - B$",
    "BTN": "Bhutanese Ngultrum - Nu.",
    "BWP": "Botswana Pula - P",
    "BYN": "Belarusian Ruble - Br",
    "BZD": "Belize Dollar - BZ$",
    "CAD": "Canadian Dollar - CA$",
    "CDF": "Congolese Franc - FC",
    "CHF": "Swiss Franc - CHF",
    "CLP": "Chilean Peso - CLP$",
    "CNY": "Chinese Yuan Renminbi - ¥",
    "COP": "Colombian Peso - COL$",
    "CRC": "Costa Rican Colon - ₡",
    "CUC": "Cuban Convertible Peso - CUC$",
    "CUP": "Cuban Peso - CUP$",
    "CVE": "Cape Verdean Escudo - $",
    "CZK": "Czech Koruna - Kč",
    "DJF": "Djiboutian Franc - Fdj",
    "DKK": "Danish Krone - kr",
    "DOP": "Dominican Peso - RD$",
    "DZD": "Algerian Dinar - دج",
    "EGP": "Egyptian Pound - £",
    "ERN": "Eritrean Nakfa - Nfk",
    "ETB": "Ethiopian Birr - Br",
    "EUR": "Euro - €",
    "FJD": "Fijian Dollar - FJ$",
    "FKP": "Falkland Islands Pound - £",
    "FOK": "Faroese Króna - kr",
    "GBP": "Pound Sterling - £",
    "GEL": "Georgian Lari - ₾",
    "GGP": "Guernsey Pound - £",
    "GHS": "Ghanaian Cedi - ₵",
    "GIP": "Gibraltar Pound - £",
    "GMD": "Gambian Dalasi - D",
    "GNF": "Guinean Franc - FG",
    "GTQ": "Guatemalan Quetzal - Q",
    "GYD": "Guyanese Dollar - GY$",
    "HKD": "Hong Kong Dollar - HK$",
    "HNL": "Honduran Lempira - L",
    "HRK": "Croatian Kuna (bis 2022) - kn",
    "HTG": "Haitian Gourde - G",
    "HUF": "Hungarian Forint - Ft",
    "IDR": "Indonesian Rupiah - Rp",
    "ILS": "Israeli New Shekel - ₪",
    "IMP": "Isle of Man Pound - £",
    "INR": "Indian Rupee - ₹",
    "IQD": "Iraqi Dinar - ع.د",
    "IRR": "Iranian Rial - ﷼",
    "ISK": "Icelandic Krona - kr",
    "JEP": "Jersey Pound - £",
    "JMD": "Jamaican Dollar - J$",
    "JOD": "Jordanian Dinar - د.ا",
    "JPY": "Japanese Yen - ¥",
    "KES": "Kenyan Shilling - KSh",
    "KGS": "Kyrgyzstani Som - с",
    "KHR": "Cambodian Riel - ៛",
    "KID": "Kiribati Dollar - $",
    "KMF": "Comorian Franc - CF",
    "KPW": "North Korean Won - ₩",
    "KRW": "South Korean Won - ₩",
    "KWD": "Kuwaiti Dinar - د.ك",
    "KYD": "Cayman Islands Dollar - CI$",
    "KZT": "Kazakhstani Tenge - ₸",
    "LAK": "Lao Kip - ₭",
    "LBP": "Lebanese Pound - ل.ل",
    "LKR": "Sri Lankan Rupee - Rs",
    "LRD": "Liberian Dollar - L$",
    "LSL": "Lesotho Loti - L",
    "LYD": "Libyan Dinar - ل.د",
    "MAD": "Moroccan Dirham - د.م.",
    "MDL": "Moldovan Leu - L",
    "MGA": "Malagasy Ariary - Ar",
    "MKD": "Macedonian Denar - ден",
    "MMK": "Myanmar Kyat - K",
    "MNT": "Mongolian Tögrög - ₮",
    "MOP": "Macanese Pataca - MOP$",
    "MRU": "Mauritanian Ouguiya - UM",
    "MUR": "Mauritian Rupee - ₨",
    "MVR": "Maldivian Rufiyaa - Rf",
    "MWK": "Malawian Kwacha - MK",
    "MXN": "Mexican Peso - MX$",
    "MYR": "Malaysian Ringgit - RM",
    "MZN": "Mozambican Metical - MT",
    "NAD": "Namibian Dollar - N$",
    "NGN": "Nigerian Naira - ₦",
    "NIO": "Nicaraguan Córdoba - C$",
    "NOK": "Norwegian Krone - kr",
    "NPR": "Nepalese Rupee - ₨",
    "NZD": "New Zealand Dollar - NZ$",
    "OMR": "Omani Rial - ﷼",
    "PAB": "Panamanian Balboa - B/.",
    "PEN": "Peruvian Sol - S/",
    "PGK": "Papua New Guinean Kina - K",
    "PHP": "Philippine Peso - ₱",
    "PKR": "Pakistani Rupee - ₨",
    "PLN": "Polish Zloty - zł",
    "PYG": "Paraguayan Guarani - ₲",
    "QAR": "Qatari Rial - ﷼",
    "RON": "Romanian Leu - lei",
    "RSD": "Serbian Dinar - din",
    "RUB": "Russian Ruble - ₽",
    "RWF": "Rwandan Franc - RF",
    "SAR": "Saudi Riyal - ﷼",
    "SBD": "Solomon Islands Dollar - SI$",
    "SCR": "Seychellois Rupee - ₨",
    "SDG": "Sudanese Pound - SDG",
    "SEK": "Swedish Krona - kr",
    "SGD": "Singapore Dollar - S$",
    "SHP": "Saint Helena Pound - £",
    "SLE": "Sierra Leonean Leone - Le",
    "SLL": "Sierra Leonean Leone (bis 2022) - Le",
    "SOS": "Somali Shilling - Sh",
    "SRD": "Surinamese Dollar - SRD$",
    "SSP": "South Sudanese Pound - £",
    "STN": "São Tomé and Príncipe Dobra - Db",
    "SYP": "Syrian Pound - £",
    "SZL": "Swazi Lilangeni - L",
    "THB": "Thai Baht - ฿",
    "TJS": "Tajikistani Somoni - ЅМ",
    "TMT": "Turkmenistani Manat - m",
    "TND": "Tunisian Dinar - د.ت",
    "TOP": "Tongan Paʻanga - T$",
    "TRY": "Turkish Lira - ₺",
    "TTD": "Trinidad and Tobago Dollar - TT$",
    "TVD": "Tuvaluan Dollar - TVD$",
    "TWD": "New Taiwan Dollar - NT$",
    "TZS": "Tanzanian Shilling - TSh",
    "UAH": "Ukrainian Hryvnia - ₴",
    "UGX": "Ugandan Shilling - USh",
    "USD": "United States Dollar - $",
    "UYU": "Uruguayan Peso - $U",
    "UZS": "Uzbekistani Som - so'm",
    "VES": "Venezuelan Bolívar - Bs.",
    "VND": "Vietnamese Dong - ₫",
    "VUV": "Vanuatu Vatu - VT",
    "WST": "Samoan Tala - WS$",
    "XAF": "Central African CFA Franc - FCFA",
    "XCD": "East Caribbean Dollar - EC$",
    "XOF": "West African CFA Franc - CFA",
    "XPF": "CFP Franc (French Pacific Franc) - ₣",
    "YER": "Yemeni Rial - ﷼",
    "ZAR": "South African Rand - R",
    "ZMW": "Zambian Kwacha - ZK",
    "ZWL": "Zimbabwean Dollar - Z$"
}

# Land (BT-40) (BT-55) (BT-80)
D_COUNTRY_CODE = {
    "AD": "Andorra",
    "AT": "Austria",
    "AL": "Albania",
    "BY": "Belarus",
    "BE": "Belgium",
    "BA": "Bosnia and Herzegovina",
    "BG": "Bulgaria",
    "CA": "Canada",
    "HR": "Croatia",
    "CY": "Cyprus",
    "CZ": "Czechia",
    "DK": "Denmark",
    "EE": "Estonia",
    "FI": "Finland",
    "FR": "France",
    "DE": "Germany",  # Default
    "GR": "Greece",
    "HU": "Hungary",
    "IS": "Iceland",
    "IE": "Ireland",
    "IT": "Italy",
    "LV": "Latvia",
    "LI": "Liechtenstein",
    "LT": "Lithuania",
    "LU": "Luxembourg",
    "MT": "Malta",
    "MA": "Morocco",
    "MD": "Moldova, Republic of",
    "MC": "Monaco",
    "ME": "Montenegro",
    "NL": "Netherlands",
    "MK": "North Macedonia",
    "NO": "Norway",
    "PL": "Poland",
    "PT": "Portugal",
    "RO": "Romania",
    "RU": "Russian Federation",
    "SM": "San Marino",
    "SK": "Slovakia",
    "SI": "Slovenia",
    "ES": "Spain",
    "RS": "Serbia",
    "SE": "Sweden",
    "CH": "Switzerland",
    "TR": "Turkey",
    "UA": "Ukraine",
    "AE": "United Arab Emirates",
    "GB": "United Kingdom",
    "US": "United States of America",
    "VA": "Vatican City"
}

# Zahlungsart (BT-81)
D_PAYMENT_METHOD = {
    "1": "Nicht definiert",
    "30": "Überweisung",
    "42": "Zahlung auf Bankkonto",
    "58": "SEPA-Überweisung",  # Default
    "59": "SEPA-Lastschrift"
}

# Einheit (BT-130)
D_UNIT = {
    "H87": "Stück",  # Default
    "C62": "Eins",
    "LS": "Pauschale",
    "P1": "Prozent",
    "MIN": "Minute",
    "HUR": "Stunde",
    "DAY": "Tag",
    "WEE": "Woche",
    "MON": "Monat",
    "GRM": "Gramm",
    "KGM": "Kilogramm",
    "TNE": "Tonne",
    "CMT": "Zentimeter",
    "MTR": "Meter",
    "KMT": "Kilometer",
    "MTK": "Quadratmeter",
    "CMK": "Quadratzentimeter",
    "HAR": "Hektar",
    "LTR": "Liter",
    "MTQ": "Kubikmeter",
    "KWH": "Kilowattstunde"
}

# Code der Umsatzsteuerkategorie des in Rechnung gestellten Artikels (BT-151)
D_VAT_CODE = {
    "S": "Standard Rate",  # default
    "Z": "Nach dem Nullsatz zu versteuernde Waren",
    "E": "Steuerbefreit",
    "AE": "Umkehrung der Steuerschuldschaft",
    "K": "Umsatzsteuerbefreit für innergemeinschaftliche Warenlieferungen",
    "G": "Freier Ausfuhrartikel, Steuer nicht erhoben",
    "O": "Dienstleistungen außerhalb des Steueranwendungsbereichs",
    "L": "Allgemeine indirekte Steuer der kanarischen Inseln",
    "M": "IPSI (Steuer für Ceuta/Melilla)"
}

# Code für Befreiungsgrund (BT-121)
D_EXEMPTION_REASON_CODE = {
    "": "",  # default
    "BR-AE-10": "Umkehrung der Steuerschuldnerschaft",
    "BR-E-10": "Steuerbefreit",
    "BR-G-10": "Steuer nicht erhoben aufgrund von Export außerhalb der EU",
    "BR-IC-10": "Kein Ausweis der Umsatzsteuer bei innergemeinschaftlichen Lieferungen",
    "BR-IG-10": "IGIC (Kanarische Inseln)",
    "BR-IP-10": "IPSI (Ceuta/Melilla)",
    "BR-O-10": "Nicht steuerbar",
    "BR-S-10": "Umsatzsteuer mit Normalsatz",
    "BR-Z-10": "Umsatzsteuer mit Nullsatz"
}

# Code für den Grund des Abschlag (BT-98) (BT-140)
D_ALLOWANCE_REASON_CODE = {
    "": "",  # default
    "41": "Bonus for works ahead of schedule",
    "42": "Other bonus",
    "60": "Manufacturer's consumer discount",
    "62": "Due to military status",
    "63": "Due to work accident",
    "64": "Special agreement",
    "65": "Production error discount",
    "66": "New outlet discount",
    "67": "Sample discount",
    "68": "End-of-range discount",
    "70": "Incoterm discount",
    "71": "Point of sales threshold allowance",
    "88": "Material surcharge/deduction",
    "95": "Discount",
    "100": "Special rebate",
    "102": "Fixed long term",
    "103": "Temporary",
    "104": "Standard",
    "105": "Yearly turnover"
}

# Code für den Grund des Zuschlag (BT-105) (BT-145)
# https://www.xrepository.de/details/urn:xoev-de:kosit:codeliste:untdid.7161_2
D_CHARGE_REASON_CODE = {
    "": "",  # default
    "AA": "Advertising",
    "AAA": "Telecommunication",
    "AAC": "Technical modification",
    "AAD": "Job-order production",
    "AAE": "Outlays",
    "AAF": "Off-premises",
    "AAH": "Additional processing",
    "AAI": "Attesting",
    "AAS": "Acceptance",
    "AAT": "Rush delivery",
    "AAV": "Special construction",
    "AAY": "Airport facilities",
    "AAZ": "Concession",
    "ABA": "Compulsory storage",
    "ABB": "Fuel removal",
    "ABC": "Into plane",
    "ABD": "Overtime",
    "ABF": "Tooling",
    "ABK": "Miscellaneous",
    "ABL": "Additional packaging",
    "ABN": "Dunnage",
    "ABR": "Containerisation",
    "ABS": "Carton packing",
    "ABT": "Hessian wrapped",
    "ABU": "Polyethylene wrap packing",
    "ACF": "Miscellaneous treatment",
    "ACG": "Enamelling treatment",
    "ACH": "Heat treatment",
    "ACI": "Plating treatment",
    "ACJ": "Painting",
    "ACK": "Polishing",
    "ACL": "Priming",
    "ACM": "Preservation treatment",
    "ACS": "Fitting",
    "ADC": "Consolidation",
    "ADE": "Bill of lading",
    "ADJ": "Airbag",
    "ADK": "Transfer",
    "ADL": "Slipsheet",
    "ADM": "Binding",
    "ADN": "Repair or replacement of broken returnable package",
    "ADO": "Efficient logistics",
    "ADP": "Merchandising",
    "ADQ": "Product mix",
    "ADR": "Other services",
    "ADT": "Pick-up",
    "ADW": "Chronic illness",
    "ADY": "New product introduction",
    "ADZ": "Direct delivery",
    "AEA": "Diversion",
    "AEB": "Disconnect",
    "AEC": "Distribution",
    "AED": "Handling of hazardous cargo",
    "AEF": "Rents and leases",
    "AEH": "Location differential",
    "AEI": "Aircraft refueling",
    "AEJ": "Fuel shipped into storage",
    "AEK": "Cash on delivery",
    "AEL": "Small order processing service",
    "AEM": "Clerical or administrative services",
    "AEN": "Guarantee",
    "AEO": "Collection and recycling",
    "AEP": "Copyright fee collection",
    "AES": "Veterinary inspection service",
    "AET": "Pensioner service",
    "AEU": "Medicine free pass holder",
    "AEV": "Environmental protection service",
    "AEW": "Environmental clean-up service",
    "AEX": "National cheque processing service outside account area",
    "AEY": "National payment service outside account area",
    "AEZ": "National payment service within account area",
    "AJ": "Adjustments",
    "AU": "Authentication",
    "CA": "Cataloguing",
    "CAB": "Cartage",
    "CAD": "Certification",
    "CAE": "Certificate of conformance",
    "CAF": "Certificate of origin",
    "CAI": "Cutting",
    "CAJ": "Consular service",
    "CAK": "Customer collection",
    "CAL": "Payroll payment service",
    "CAM": "Cash transportation",
    "CAN": "Home banking service",
    "CAO": "Bilateral agreement service",
    "CAP": "Insurance brokerage service",
    "CAQ": "Cheque generation",
    "CAR": "Preferential merchandising location",
    "CAS": "Crane",
    "CAT": "Special colour service",
    "CAU": "Sorting",
    "CAV": "Battery collection and recycling",
    "CAW": "Product take back fee",
    "CAX": "Quality control released",
    "CAY": "Quality control held",
    "CAZ": "Quality control embargo",
    "CD": "Car loading",
    "CG": "Cleaning",
    "CS": "Cigarette stamping",
    "CT": "Count and recount",
    "DAB": "Layout/design",
    "DAC": "Assortment allowance",
    "DAD": "Driver assigned unloading",
    "DAF": "Debtor bound",
    "DAG": "Dealer allowance",
    "DAH": "Allowance transferable to the consumer",
    "DAI": "Growth of business",
    "DAJ": "Introduction allowance",
    "DAK": "Multi-buy promotion",
    "DAL": "Partnership",
    "DAM": "Return handling",
    "DAN": "Minimum order not fulfilled charge",
    "DAO": "Point of sales threshold allowance",
    "DAP": "Wholesaling discount",
    "DAQ": "Documentary credits transfer commission",
    "DL": "Delivery",
    "EG": "Engraving",
    "EP": "Expediting",
    "ER": "Exchange rate guarantee",
    "FAA": "Fabrication",
    "FAB": "Freight equalization",
    "FAC": "Freight extraordinary handling",
    "FC": "Freight service",
    "FH": "Filling/handling",
    "FI": "Financing",
    "GAA": "Grinding",
    "HAA": "Hose",
    "HD": "Handling",
    "HH": "Hoisting and hauling",
    "IAA": "Installation",
    "IAB": "Installation and warranty",
    "ID": "Inside delivery",
    "IF": "Inspection",
    "IR": "Installation and training",
    "IS": "Invoicing",
    "KO": "Koshering",
    "L1": "Carrier count",
    "LA": "Labelling",
    "LAA": "Labour",
    "LAB": "Repair and return",
    "LF": "Legalisation",
    "MAE": "Mounting",
    "MI": "Mail invoice",
    "ML": "Mail invoice to each location",
    "NAA": "Non-returnable containers",
    "OA": "Outside cable connectors",
    "PA": "Invoice with shipment",
    "PAA": "Phosphatizing (steel treatment)",
    "PC": "Packing",
    "PL": "Palletizing",
    "RAB": "Repacking",
    "RAC": "Repair",
    "RAD": "Returnable container",
    "RAF": "Restocking",
    "RE": "Re-delivery",
    "RF": "Refurbishing",
    "RH": "Rail wagon hire",
    "RV": "Loading",
    "SA": "Salvaging",
    "SAA": "Shipping and handling",
    "SAD": "Special packaging",
    "SAE": "Stamping",
    "SAI": "Consignee unload",
    "SG": "Shrink-wrap",
    "SH": "Special handling",
    "SM": "Special finish",
    "SU": "Set-up",
    "TAB": "Tank renting",
    "TAC": "Testing",
    "TT": "Transportation - third party billing",
    "TV": "Transportation by vendor",
    "V1": "Drop yard",
    "V2": "Drop dock",
    "WH": "Warehousing",
    "XAA": "Combine all same day shipment",
    "YY": "Split pick-up",
    "ZZZ": "Mutually defined"
}

D_DEFAULT_INVOICE_DATA = \
    {
        # Nachlässe
        "allowances": [
            {
                "basisAmount": "",  # Grundbetrag (BT-100)
                "grossAmount": "",  # Betrag Brutto
                "netAmount": "",  # Betrag (Netto) (BT-99)
                "percent": "",  # Prozent (BT-101)
                "reason": "",  # Grund (BT-104)
                "reasonCode": "",  # Code des Grundes (BT-105)
                "type": "percentage",  # not required TODO absolute oder percentage
                "vatAmount": "",  # Steuerbetrag (Netto)
                "vatCode": "S",  # Steuerkategorie (BT-102)
                "vatRate": ""  # Steuersatz (BT-103)
            }
        ],
        # Anlagen
        "attachments": [],
        "billingPeriodEndDate": "",  # Leistungs-/Abrechnungszeitraum bis (BT-74)
        "billingPeriodStartDate": "",  # Leistungs-/Abrechnungszeitraum von (BT-73)
        # Rechnungsempfänger
        "buyer": {
            "address": {
                "city": "",  # Ort (BT-52)
                "countryCode": "",  # Land (BT-55) D_COUNTRY_CODE
                "line1": "",  # Straße 1 (BT-50)
                "line2": "",  # Straße 2 (BT-51)
                "postCode": ""  # PLZ (BT-53)
            },
            "contact": {
                "email": "",  # E-Mail (BT-58)
                "name": "",  # Name (BT-56)
                "phone": ""  # Telefon (BT-57)
            },
            "electronicAddress": "",  # Elektronische Adresse (BT-49)
            "electronicAddressTypeCode": "EM",
            "id": "",  # Käuferkennung (BT-46)
            "idTypeCode": "id",
            "name": "",  # Unternehmen (BT-44)
            "tradeId": "",  # Registernummer (BT-47)
            "tradeName": "",  # Handelsname (BT-45)
            "vatId": ""  # Umsatzsteuer-ID (BT-48)
        },
        "buyerAccountingAccounts": [],  # Buchungskonto des Käufers (BT-19)
        "buyerReference": "",  # Käuferreferenz (BT-10)
        "buyerReferenceDisabled": False,
        # Zuschläge
        "charges": [
            {
                "basisAmount": "",  # Grundbetrag (BT-93)
                "grossAmount": "",  # Betrag Brutto
                "netAmount": "",  # Betrag (Netto) (BT-92)
                "percent": "",  # Prozent (BT-94)
                "reason": "",  # Grund (BT-97)
                "reasonCode": "",  # Code des Grundes (BT-98)
                "type": "percentage",  # not required
                "vatAmount": "",  # Steuerbetrag (Netto)
                "vatCode": "S",  # Steuerkategorie (BT-95)
                "vatRate": ""  # Steuersatz (BT-96)
            }
        ],
        "contractReference": "",  # Vertragsnummer (BT-12)
        "currencyCode": "EUR",  # Währung (BT-5) D_CURRENCY
        "currencySymbol": "€",  # Währung Symbol
        # Zahlungsdetails
        "delivery": {
            # Lieferadresse
            "address": {
                "city": "",  # Ort (BT-77)
                "countryCode": "",  # Land (BT-80) D_COUNTRY_CODE
                "line1": "",  # Straße 1 (BT-75)
                "line2": "",  # Straße 2 (BT-76)
                "line3": "",  # Zusatz (BT-165)
                "postCode": "",  # PLZ (BT-78)
                "region": ""  # Region (BT-79)
            },
            "locationId": "",  # Kennung des Lieferorts (BT-71)
            "recipientName": ""  # Name des Empfängers (BT-70)
        },
        "deliveryDate": "",  # Leistungs-/Lieferdatum (BT-72)  Format: YYYY-MM-DD
        "despatchAdviceReference": {  # Versandanzeige (BT-16)
            "id": "",  # ID
            "issueDate": ""  # Datum
        },
        "dueDate": "",  # Fälligkeitsdatum (BT-9)  Format: YYYY-MM-DD
        "introText": "",  # Einleitungstext
        "invoiceReferences": [],  # Rechnungsreferenz (BT-25, BT-26)
        "issueDate": "",  # Rechnungsdatum (BT-2)  Format: YYYY-MM-DD
        # Positionen - Reihenfolge ist Position (BT-126)
        "items": [
            {
                "allowances": [  # Nachlässe
                    {
                        "basisAmount": "",  # Grundbetrag (nicht in PDF24 aber in xml)
                        "netAmount": "",  # Betrag (Netto) (BT-136)
                        "percent": "",  # Prozent (BT-138)
                        "reason": "",  # Grund (BT-139)
                        "reasonCode": "",  # Code des Grundes (BT-140)
                        "type": "percentage"  # not required
                    }
                ],
                "basisQuantity": 1,  # Basismenge (BT-149)
                "billingPeriodEnd": "",  # Enddatum (BT-135)
                "billingPeriodStart": "",  # Startdatum (BT-134)
                "charges": [  # Zuschläge
                    {
                        "basisAmount": "",  # Grundbetrag (nicht in PDF24 aber in xml)
                        "netAmount": "",  # Betrag (Netto) (BT-141)
                        "percent": "",  # Prozent (BT-143)
                        "reason": "",  # Grund (BT-144)
                        "reasonCode": "",  # Code des Grundes (BT-145)
                        "type": "percentage"  # not required
                    }
                ],
                "description": "",  # Beschreibung (BT-154)
                "grossAmount": None,  # Gesamtpreis (Brutto)
                "grossUnitPrice": None,  # Einzelpreis (Brutto)
                "id": "",  # Artikel-Nr. (BT-155)
                "name": "",  # Name (BT-153)
                "netAmount": None,  # Gesamtpreis (Netto) (BT-131)
                "netUnitPrice": None,  # Einzelpreis (Netto) (BT-146)
                "objectReferences": [  # Objektreferenz (BT-128)
                    {
                        "id": "",  # ID to set
                        "typeCode": "130"  # fix 130
                    }
                ],
                "orderPosition": "",  # Auftragsposition (BT-132)
                "quantity": 1,  # Menge (BT-129)
                "quantityUnit": "H87",  # Einheit (BT-130) D_UNIT
                "quantityUnitSymbol": "",  # Einheit Symbol
                "vatAmount": None,  # Steuerbetrag
                "vatCode": "S",  # Steuerkategorie (BT-151)
                "vatRate": 19  # Steuersatz (BT-152)
            }
        ],
        "note": "",  # Bemerkung (BT-22)
        "number": "",  # Rechnungsnummer (BT-1)
        "objectReferences": [  # Objektreferenz (BT-18)
            {
                "id": "",  # ID to set
                "typeCode": "130"  # fix 130
            }
        ],
        # Ausgabeoptionen
        "outputOptions": {
            "attachmentsEmbedMode": "pdf",
            "dateFormat": "dd.mm.yyyy",
            "decimalSeparator": ",",
            "format": "zugferd:xrechnung",
            "langCode": "de",
            "logoDisplayMode": "auto",
            "pageNumbersDisplayMode": "bottom-center",
            "paymentQrCodeDisplayMode": "shown",
            "quantityUnitDisplayMode": "combined",
            "taxCategoryDisplayMode": "shown",
            "taxDisplayMode": "shown",
            "taxExemptionReasonsDisplayMode": "shown",
            "thousandsSeparator": "."
        },
        "payment": {
            "methods": [
                {
                    "accountName": "",  # Kontoinhaber (BT-85)
                    "ban": "",
                    "bankName": "",  # Name der Bank
                    "bic": "",  # BIC (BT-86)
                    "iban": "",  # IBAN (BT-84)
                    "typeCode": "58"  # Zahlungsart (BT-81) D_PAYMENT_METHOD
                }
            ],
            "reference": "",  # Verwendungszweck (BT-83)
            "terms": ""  # Zahlungsbedingungen (BT-20) z.B.: Bitte überweisen Sie den Rechnungsbetrag in Höhe von [Endbetrag] [Währung] bis zum Fälligkeitsdatum [Fälligkeitsdatum].
        },
        "projectReference": "",  # Projektnummer (BT-11)
        "purchaseOrderReference": "",  # Bestellnummer (BT-13)
        "receivingAdviceReference": {  # Wareneingangsmeldung (BT-15)
            "id": "",  # ID
            "issueDate": ""  # Datum
        },
        "salesOrderReference": "",  # Auftragsnummer (BT-14)
        # Rechnungssteller
        "seller": {
            "address": {
                "city": "",  # Ort (BT-37)
                "countryCode": "",  # Land (BT-40) D_COUNTRY_CODE
                "line1": "",  # Straße 1 (BT-35)
                "line2": "",  # Straße 2 (BT-36)
                "postCode": ""  # PLZ (BT-38)
            },
            "applicableRule": "",  # Anzuwendende Regelung: Deutsche Kleinunternehmerregelung nach $ 19 UStG "germany-p19-ustg"
            "contact": {
                "email": "",  # E-Mail (BT-43)
                "fax": "",  # Fax
                "name": "",  # Name (BT-41)
                "phone": ""  # Telefon (BT-42)
            },
            "electronicAddress": "",  # Elektronische Adresse (BT-34)
            "electronicAddressTypeCode": "EM",
            "id": "",  # Verkäuferkennung (BT-29)
            "legalInfo": "",  # Rechtliche Informationen (BT-33) z.B "Kein Ausweis von Umsatzsteuer, da Kleinunternehmer gemäß §19 UStG."
            "logoData": "",  # Logo Pfad
            "name": "",  # Unternehmen (BT-27)
            "taxId": "",  # Steuernummer (BT-32)
            "tradeId": "",  # Registernummer (BT-30)
            "tradeName": "",  # Handelsname (BT-28)
            "vatId": "",  # Umsatzsteuer-ID (BT-31)
            "websiteText": "",  # Webseite Text
            "websiteUrl": "",  # Webseite URL
            "weeeId": ""  # WEEE-Nummer
        },
        # Steuern
        "taxes": {
            "S-19": {
                "code": "S",  # Steuerkategorie (BT-118)
                "exemptionReason": "",  # Befreiungsgrund (BT-120)
                "exemptionReasonCode": "",  # Code für Befreiungsgrund (BT-121)
                "netAmount": 100,  # Gesamt (Netto) (BT-116)
                "rate": 19,  # Steuersatz (BT-119)
                "vatAmount": 19  # Steuerbetrag (BT-117)
            },
            "S-7": {
                "code": "S",
                "exemptionReason": "",
                "exemptionReasonCode": "",
                "netAmount": 400,
                "rate": 7,
                "vatAmount": 28
            }
        },
        "tenderReferences": [],  # Ausschreibung/Los (BT-17)
        "title": "Rechnung",  # Rechnungstitel
        "totals": {
            "allowancesNetAmount": None,  # Summe Nachlässe (Netto) (BT-107)
            "chargesNetAmount": None,  # Summe Zuschläge (Netto) (BT-108)
            "dueAmount": None,  # Fälliger Betrag (BT-115)
            "grossAmount": None,  # Gesamt (Brutto) (BT-112)
            "itemsNetAmount": None,  # Summe Positionen (Netto) (BT-106)
            "netAmount": None,  # Gesamt (Netto) (BT-109)
            "paidAmount": 0,  # Gezahlter Betrag (BT-113)
            "roundingAmount": 0,  # Rundungsbetrag (BT-114)
            "vatAmount": None  # Summe Umsatzsteuer (BT-110)
        },
        "typeCode": "380"  # Rechnungstyp (BT-3) D_INVOICE_TYPE
    }
