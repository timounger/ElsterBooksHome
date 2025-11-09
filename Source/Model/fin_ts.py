"""!
********************************************************************************
@file   fin_ts.py
@brief  FinTS: banking protocol
        doc: https://python-fints.readthedocs.io/en/latest/
********************************************************************************
"""

import os
import logging
import enum
import csv
from datetime import datetime
from typing import NamedTuple
from fints.utils import minimal_interactive_cli_bootstrap
from fints.client import FinTS3PinTanClient, NeedTANResponse
from fints.exceptions import FinTSClientError, FinTSClientPINError, FinTSClientTemporaryAuthError, FinTSSCARequiredError, \
    FinTSDialogError, FinTSDialogStateError, FinTSDialogOfflineError, FinTSDialogInitError, FinTSConnectionError, \
    FinTSUnsupportedOperation, FinTSNoResponseError
from fints.hhd.flicker import terminal_flicker_unix

from PyQt6.QtWidgets import QMessageBox, QInputDialog

from Source.version import __title__
from Source.Util.app_data import EXPORT_PATH, FINTS_INSTITUTE_FILE
from Source.Util.openpyxl_util import XLSCreator, NUMBER_FORMAT_EUR, NUMBER_FORMAT_DATETIME, COLOR_RED
from Source.Model.data_handler import DATE_FORMAT_JSON, delete_file

log = logging.getLogger(__title__)

B_GUI_INPUT = True
B_WRITE_SESSION_DATA = False
if B_WRITE_SESSION_DATA:
    DATAFILE = "fints_client.dat"

PRODUCT_ID = "ECA9BC32B4506B9F36923DCE7"  # registered ID for ElsterBooks
PRODUCT_VERSION = "3.0"

TRANSACTIONS_CSV_FILE_PATH = os.path.join(EXPORT_PATH, "transactions.csv")
TRANSACTIONS_XLS_FILE_PATH = os.path.join(EXPORT_PATH, "Transaktionen.xlsx")
S_DATE_TRANSITION_FORMAT = "%Y-%m-%d"
COLOR_RED_DARK = "008000"


class FinTSInstitute(NamedTuple):
    """!
    @brief FinTS Institute data
    """
    blz: str
    bic: str
    institute: str
    url: str


class Transaction(NamedTuple):
    """!
    @brief Transaction data
    """
    date: datetime
    amount: float
    purpose: str
    text: str
    applicant_name: str
    customer_reference: str


class TanMechanisms(str, enum.Enum):
    """!
    @brief tan mechanisms code
    """
    SMART_TAN_PLUS_MANUELL = "962"  # Smart-TAN plus manuell
    SMART_TAN_PLUS_OPTICAL = "972"  # Smart-TAN plus optisch / USB
    SMART_TAN_PLUS_PHOTO = "982"  # Smart-TAN photo
    SECURE_GO_PLUS = "946"  # SecureGo plus (Direktfreigabe)


L_ALLOWED_TAN_MECHANISMS = [TanMechanisms.SMART_TAN_PLUS_MANUELL, TanMechanisms.SECURE_GO_PLUS]


def get_fints_institutes() -> list[FinTSInstitute]:
    """!
    @brief Get FinTS institute
    @return FinTS institutes
    """
    l_institutes = []
    with open(FINTS_INSTITUTE_FILE, mode="r", encoding="latin1", newline="") as csv_file:
        reader = csv.reader(csv_file, delimiter=";", quotechar='"')
        for i, row in enumerate(reader):
            if i != 0:
                blz = row[1]
                bic = row[2]
                instutute = row[3]
                url = row[24]
                if blz and instutute and url:
                    l_institutes.append(FinTSInstitute(blz, bic, instutute, url))
    return l_institutes


def read_data_from_transaction_file(transaction_file: str = TRANSACTIONS_CSV_FILE_PATH) -> list[list[str]]:
    """!
    @brief Read data from transaction file
    @param transaction_file : file to read
    @return transaction data
    """
    l_transactions = []
    if os.path.exists(transaction_file):
        with open(transaction_file, mode="r", encoding="utf-8", newline="") as csv_file:
            reader = csv.reader(csv_file, delimiter=";", quotechar='"')
            for row in reader:
                l_transactions.append(row)
    return l_transactions


def create_transaction_file(l_transactions: list[list[str]]) -> None:
    """!
    @brief Create transaction file
    @param l_transactions : transactions
    """
    if not os.path.exists(EXPORT_PATH):
        os.makedirs(EXPORT_PATH)
    with open(TRANSACTIONS_CSV_FILE_PATH, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerow(["Datum", "Betrag", "Verwendungszweck", "Buchungstext", "Auftraggeber", "Referenz"])
        for transaction in l_transactions:
            writer.writerow(transaction)


def create_transaction_xls_file(l_transactions: list[Transaction]) -> None:
    """!
    @brief Create transaction XLS Report
    @param l_transactions : transactions
    """
    header = ["Datum", "Betrag", "Auftraggeber", "Verwendungszweck", "Buchungstext", "Referenz"]
    if not os.path.exists(EXPORT_PATH):
        os.makedirs(EXPORT_PATH)
    xls_creator = XLSCreator()
    worksheet = xls_creator.workbook.active
    worksheet.title = "Transaktionen"
    worksheet.column_dimensions["A"].width = 10  # Datum
    worksheet.column_dimensions["B"].width = 15  # Betrag
    worksheet.column_dimensions["C"].width = 30  # Auftraggeber
    worksheet.column_dimensions["D"].width = 50  # Verwendungszweck
    worksheet.column_dimensions["E"].width = 20  # Buchungstext
    worksheet.column_dimensions["F"].width = 20  # Referenz
    for i, title in enumerate(header):
        xls_creator.set_cell(worksheet, 1, i + 1, title, bold=True)
    i_transaction = 0
    for transaction in reversed(l_transactions):
        color = COLOR_RED_DARK if transaction.amount >= 0 else COLOR_RED
        xls_creator.set_cell(worksheet, i_transaction + 2, 1, transaction.date.strftime(DATE_FORMAT_JSON), number_format=NUMBER_FORMAT_DATETIME)
        xls_creator.set_cell(worksheet, i_transaction + 2, 2, transaction.amount, color=color, number_format=NUMBER_FORMAT_EUR)
        xls_creator.set_cell(worksheet, i_transaction + 2, 3, str(transaction.applicant_name))
        xls_creator.set_cell(worksheet, i_transaction + 2, 4, str(transaction.purpose))
        xls_creator.set_cell(worksheet, i_transaction + 2, 5, str(transaction.text))
        xls_creator.set_cell(worksheet, i_transaction + 2, 6, str(transaction.customer_reference))
        i_transaction += 1
    xls_creator.set_table(worksheet, max_col=len(header), max_row=i_transaction + 1, min_col=1, min_row=1)
    xls_creator.save(TRANSACTIONS_XLS_FILE_PATH)


def delete_transaction_files() -> None:
    """!
    @brief Delete transactions files
    """
    delete_file(TRANSACTIONS_CSV_FILE_PATH)
    delete_file(TRANSACTIONS_XLS_FILE_PATH)


class FinTs:
    """!
    @brief Class to get transaction data via FinTS
    @param ui : main window
    @param pte_output : text widget for result response
    """

    def __init__(self, ui, pte_output) -> None:
        self.ui = ui
        self.pte_output = pte_output
        self.l_fints_institutes = get_fints_institutes()
        self.bank_code = ""
        self.fints_url = ""
        self.user_id = ""
        self.pin = ""
        self.iban = ""
        self.tan_mechanism = ""
        self.client = None

    def get_transactions(self) -> list[Transaction]:
        """!
        @brief Get transaction from CSV file
        @return transactions
        """
        l_transaction = []
        l_raw_data = read_data_from_transaction_file()
        for i, row in enumerate(l_raw_data):
            if i != 0:
                amount = float(row[1].replace("EUR", "").strip())
                transaction = Transaction(datetime.strptime(row[0], S_DATE_TRANSITION_FORMAT), amount,
                                          row[2], row[3], row[4], row[5])
                l_transaction.append(transaction)
        try:
            create_transaction_xls_file(l_transaction)
        except PermissionError:
            self.ui.set_status("Transaktionen Datei konnte nicht erstellt werden", b_highlight=True)
        return l_transaction

    def ask_for_tan(self, client: FinTS3PinTanClient, response):
        """!
        @brief Ask for TAN
        @param client : client
        @param response : response
        @return answer
        """
        self.pte_output.setPlainText(response.challenge)
        if getattr(response, 'challenge_hhduc', None):
            if B_GUI_INPUT:
                if False:
                    self.pte_output.setPlainText(response.challenge_hhduc)  # TODO in GUI not work
            else:
                try:
                    terminal_flicker_unix(response.challenge_hhduc)
                except KeyboardInterrupt:
                    pass
        if response.decoupled:
            if B_GUI_INPUT:
                QMessageBox.information(self.ui, "Fortfahren", "Bitte klicke OK, nachdem Sie die Transaktion bestätigt haben.")
                tan = None
            else:
                tan = input('Please press enter after confirming the transaction in your app:')
        else:
            if B_GUI_INPUT:
                text, _ok = QInputDialog.getText(self.ui, "TAN Verfahren", "Bitte geben Sie die TAN ein.")
                tan = text
            else:
                tan = input('Please enter TAN:')
        return client.send_tan(response, tan)

    def connect_client(self) -> tuple[bool, str]:
        """!
        @brief Connect Client
        @return success status and status text
        """
        success = False
        success_text = "Fehler"
        # load existing client states
        client_data = None
        if B_WRITE_SESSION_DATA:
            if os.path.exists(DATAFILE):
                with open(DATAFILE, "rb") as f:
                    client_data = f.read()
        try:
            self.client = FinTS3PinTanClient(
                bank_identifier=self.bank_code,
                user_id=self.user_id,
                pin=self.pin,
                server=self.fints_url,
                from_data=client_data,
                product_id=PRODUCT_ID,
                product_version=PRODUCT_VERSION,
            )

            if not B_GUI_INPUT:
                minimal_interactive_cli_bootstrap(self.client)

            _accounts = self.client.get_sepa_accounts()  # call account data to check connection

        except (FinTSClientError, FinTSClientPINError, FinTSClientTemporaryAuthError,
                FinTSSCARequiredError, FinTSDialogError, FinTSDialogStateError,
                FinTSDialogOfflineError, FinTSDialogInitError, FinTSConnectionError,
                FinTSUnsupportedOperation, FinTSNoResponseError, ValueError) as e:
            err_msg = str(e)
            match err_msg:
                case "Couldn't establish dialog with bank, Authentication data wrong?":
                    success_text = "FinTS Adresse kann nicht erreicht werden."
                case "Bad status code 404":
                    success_text = "FinTS falsch"
                case "Error during dialog initialization, PIN wrong?":
                    success_text = "Falsche Nutzerdaten (Alias oder PW)"
                case "Could not find system_id":
                    success_text = "Falsche BLZ"  # or product ID not valid
                case _:
                    success_text = f"FinTS Fehler: {err_msg}"
        except Exception as e:
            err_msg = str(e)
            success_text = "Unbekannter Fehler: {err_msg}"
        else:
            success_text = "Erfolgreich verbunden"
            success = True

        return success, success_text

    def get_accounts(self) -> dict[str, str]:
        """!
        @brief Get accounts
        @return accounts
        """
        d_accounts = {}
        with self.client:
            info = self.client.get_information()
            info_accounts = info.get("accounts")
            for account in info_accounts:
                iban = account.get("iban")
                product_name = account.get("product_name")
                d_accounts[f"{iban} {product_name}"] = iban
        return d_accounts

    def get_tan_mechanism(self) -> dict[str, str]:
        """!
        @brief Get TAN mechanism
        @return TAN mechanisms
        """
        d_tan_mechanism = {}
        with self.client:
            tan_mechanisms = self.client.get_tan_mechanisms()
            for _tan_code, tan_mechanism in tan_mechanisms.items():
                if tan_mechanism.security_function in L_ALLOWED_TAN_MECHANISMS:
                    d_tan_mechanism[tan_mechanism.security_function] = f"{tan_mechanism.security_function} {tan_mechanism.name}"
        return d_tan_mechanism

    def get_and_create_transaction(self) -> tuple[bool, str]:
        """!
        @brief Get and create transactions
        @return success status and status text
        """
        success = False
        success_text = "Unbekannt"
        if self.tan_mechanism:
            self.client.set_tan_mechanism(self.tan_mechanism)

        with self.client:
            accounts = self.client.get_sepa_accounts()

            select_account = None
            for account in accounts:
                if account.iban == self.iban:
                    select_account = account
                    break

            if select_account is not None:
                response = self.client.get_transactions(select_account)
                if isinstance(response, NeedTANResponse):
                    transactions = self.ask_for_tan(self.client, response)
                else:
                    transactions = response
                    log.warning("Keine TAN Eingabe erforderlich")

                l_transactions = []
                for transaction in transactions:
                    data = transaction.data
                    l_transactions.append([
                        data.get("date"),
                        data.get("amount"),
                        data.get("purpose"),
                        data.get("text"),
                        data.get("applicant_name"),
                        data.get("customer_reference")
                    ])

                create_transaction_file(l_transactions)

                if B_WRITE_SESSION_DATA:
                    client_blob = self.client.deconstruct(including_private=True)
                    with open(DATAFILE, "wb") as f:
                        f.write(client_blob)

                success = True
                success_text = f"Es wurden {len(transactions)} Transaktionen für das Konto {account.iban} gefunden."
            else:
                success_text = "Account nicht gefunden"
        return success, success_text
