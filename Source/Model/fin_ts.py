"""!
********************************************************************************
@file   fin_ts.py
@brief  FinTS banking protocol integration.
        doc: https://python-fints.readthedocs.io/en/latest/
********************************************************************************
"""

import os
import logging
import enum
import csv
from datetime import datetime
from typing import TYPE_CHECKING, NamedTuple
from fints.utils import minimal_interactive_cli_bootstrap
from fints.client import FinTS3PinTanClient, NeedTANResponse, Transaction
from fints.camt_parser import camt053_to_dict
from fints.exceptions import FinTSClientError, FinTSClientPINError, FinTSClientTemporaryAuthError, FinTSSCARequiredError, \
    FinTSDialogError, FinTSDialogStateError, FinTSDialogOfflineError, FinTSDialogInitError, FinTSConnectionError, \
    FinTSUnsupportedOperation, FinTSNoResponseError
from fints.hhd.flicker import terminal_flicker_unix

from PyQt6.QtWidgets import QMessageBox, QInputDialog, QPlainTextEdit

from Source.version import __title__
from Source.Util.app_data import EXPORT_PATH, FINTS_INSTITUTE_FILE
from Source.Util.openpyxl_util import XLSCreator, NUMBER_FORMAT_EUR, NUMBER_FORMAT_DATETIME, COLOR_RED
from Source.Model.data_handler import DATE_FORMAT_JSON, delete_file
if TYPE_CHECKING:
    from Source.Controller.main_window import MainWindow

log = logging.getLogger(__title__)

GUI_INPUT = True
WRITE_SESSION_DATA = False
if WRITE_SESSION_DATA:
    DATAFILE = "fints_client.dat"

PRODUCT_ID = "ECA9BC32B4506B9F36923DCE7"  # registered ID for ElsterBooks
PRODUCT_VERSION = "3.0"

TRANSACTIONS_CSV_FILE_PATH = os.path.join(EXPORT_PATH, "transactions.csv")
TRANSACTIONS_XLS_FILE_PATH = os.path.join(EXPORT_PATH, "Transaktionen.xlsx")
DATE_TRANSITION_FORMAT = "%Y-%m-%d"
COLOR_GREEN_DARK = "008000"


class FinTSInstitute(NamedTuple):
    """!
    @brief FinTS institute data.
    """
    blz: str
    bic: str
    institute: str
    url: str


class TransactionItem(NamedTuple):
    """!
    @brief Single bank transaction entry from FinTS with date and amount.
    """
    date: datetime
    amount: float
    purpose: str
    text: str
    applicant_name: str
    customer_reference: str


class TanMechanisms(str, enum.Enum):
    """!
    @brief TAN mechanism codes.
    """
    SMART_TAN_PLUS_MANUELL = "962"  # Smart-TAN plus manuell
    SMART_TAN_PLUS_OPTICAL = "972"  # Smart-TAN plus optisch / USB
    SMART_TAN_PLUS_PHOTO = "982"  # Smart-TAN photo
    SECURE_GO_PLUS = "946"  # SecureGo plus (Direktfreigabe)


ALLOWED_TAN_MECHANISMS = [TanMechanisms.SMART_TAN_PLUS_MANUELL, TanMechanisms.SECURE_GO_PLUS]


def get_fints_institutes() -> list[FinTSInstitute]:
    """!
    @brief Read FinTS institute data from CSV file.
    @return list of FinTS institute entries.
    """
    institutes = []
    with open(FINTS_INSTITUTE_FILE, mode="r", encoding="latin1", newline="") as csv_file:
        reader = csv.reader(csv_file, delimiter=";", quotechar='"')
        next(reader)  # skip header
        for row in reader:
            blz = row[1]
            bic = row[2]
            institute = row[3]
            url = row[24]
            if blz and institute and url:
                institutes.append(FinTSInstitute(blz, bic, institute, url))
    return institutes


def read_data_from_transaction_file(transaction_file: str = TRANSACTIONS_CSV_FILE_PATH) -> list[list[str]]:
    """!
    @brief Read data from transaction CSV file.
    @param transaction_file : path to transaction CSV file.
    @return list of transaction row data.
    """
    transactions = []
    if os.path.exists(transaction_file):
        with open(transaction_file, mode="r", encoding="utf-8", newline="") as csv_file:
            reader = csv.reader(csv_file, delimiter=";", quotechar='"')
            for row in reader:
                transactions.append(row)
    return transactions


def create_transaction_file(transactions: list[list[str]]) -> None:
    """!
    @brief Create transaction CSV file.
    @param transactions : list of transaction row data.
    """
    if not os.path.exists(EXPORT_PATH):
        os.makedirs(EXPORT_PATH)
    with open(TRANSACTIONS_CSV_FILE_PATH, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerow(["Datum", "Betrag", "Verwendungszweck", "Buchungstext", "Auftraggeber", "Referenz"])
        for transaction in transactions:
            writer.writerow(transaction)


def create_transaction_xls_file(transactions: list[TransactionItem]) -> None:
    """!
    @brief Create transaction XLS report file.
    @param transactions : list of transaction items.
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
    for idx, transaction in enumerate(reversed(transactions)):
        row = idx + 2
        color = COLOR_GREEN_DARK if transaction.amount >= 0 else COLOR_RED
        xls_creator.set_cell(worksheet, row, 1, transaction.date.strftime(DATE_FORMAT_JSON), number_format=NUMBER_FORMAT_DATETIME)
        xls_creator.set_cell(worksheet, row, 2, transaction.amount, color=color, number_format=NUMBER_FORMAT_EUR)
        xls_creator.set_cell(worksheet, row, 3, str(transaction.applicant_name))
        xls_creator.set_cell(worksheet, row, 4, str(transaction.purpose))
        xls_creator.set_cell(worksheet, row, 5, str(transaction.text))
        xls_creator.set_cell(worksheet, row, 6, str(transaction.customer_reference))
    xls_creator.set_table(worksheet, max_col=len(header), max_row=len(transactions) + 1, min_col=1, min_row=1)
    xls_creator.save(TRANSACTIONS_XLS_FILE_PATH)


def delete_transaction_files() -> None:
    """!
    @brief Delete transaction CSV and XLS files.
    """
    delete_file(TRANSACTIONS_CSV_FILE_PATH)
    delete_file(TRANSACTIONS_XLS_FILE_PATH)


class FinTs:
    """!
    @brief FinTS client for retrieving bank transaction data.
    @param ui : main window instance.
    @param pte_output : text widget for result output.
    """

    def __init__(self, ui: "MainWindow", pte_output: QPlainTextEdit) -> None:
        self.ui = ui
        self.pte_output = pte_output
        self.fints_institutes = get_fints_institutes()
        self.bank_code = ""
        self.fints_url = ""
        self.user_id = ""
        self.pin = ""
        self.iban = ""
        self.tan_mechanism = ""
        self.client: FinTS3PinTanClient | None = None

    def get_transactions(self) -> list[TransactionItem]:
        """!
        @brief Parse transactions from CSV file and create XLS export.
        @return list of parsed transaction items.
        """
        transactions = []
        raw_data = read_data_from_transaction_file()
        for row in raw_data[1:]:  # skip header
            amount = float(row[1].replace("EUR", "").strip())
            transaction = TransactionItem(datetime.strptime(row[0], DATE_TRANSITION_FORMAT), amount,
                                          row[2], row[3], row[4], row[5])
            transactions.append(transaction)
        try:
            create_transaction_xls_file(transactions)
        except PermissionError:
            self.ui.set_status("Transaktionen Datei konnte nicht erstellt werden", highlight=True)
        return transactions

    def ask_for_tan(self, client: FinTS3PinTanClient, response: NeedTANResponse) -> tuple[list[object], list[object]]:
        """!
        @brief Prompt user for TAN input and send it to the bank.
        @param client : FinTS client instance.
        @param response : TAN response from the bank.
        @return result of sending the TAN.
        """
        self.pte_output.setPlainText(response.challenge)
        if getattr(response, 'challenge_hhduc', None):
            if GUI_INPUT:
                pass  # self.pte_output.setPlainText(response.challenge_hhduc)  # TODO in GUI not work
            else:
                try:
                    terminal_flicker_unix(response.challenge_hhduc)
                except KeyboardInterrupt:
                    pass
        if response.decoupled:
            if GUI_INPUT:
                QMessageBox.information(self.ui, "Fortfahren", "Bitte klicke OK, nachdem Sie die Transaktion bestätigt haben.")
                tan = None
            else:
                tan = input('Please press enter after confirming the transaction in your app:')
        else:
            if GUI_INPUT:
                text, _ok = QInputDialog.getText(self.ui, "TAN Verfahren", "Bitte geben Sie die TAN ein.")
                tan = text
            else:
                tan = input('Please enter TAN:')
        result: tuple[list[object], list[object]] = client.send_tan(response, tan)
        return result

    def connect_client(self) -> tuple[bool, str]:
        """!
        @brief Connect to FinTS bank server.
        @return success status and status text.
        """
        success = False
        success_text = "Fehler"
        # load existing client states
        client_data = None
        if WRITE_SESSION_DATA:
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

            if not GUI_INPUT:
                minimal_interactive_cli_bootstrap(self.client)

            self.client.get_sepa_accounts()  # call account data to check connection

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
            success_text = f"Unbekannter Fehler: {err_msg}"
        else:
            success_text = "Erfolgreich verbunden"
            success = True

        return success, success_text

    def get_accounts(self) -> dict[str, str]:
        """!
        @brief Get available bank accounts.
        @return mapping of display label to IBAN.
        """
        account_map = {}
        assert self.client is not None
        with self.client:
            info = self.client.get_information()
            info_accounts = info.get("accounts")
            for account in info_accounts:
                iban = account.get("iban")
                product_name = account.get("product_name")
                account_map[f"{iban} {product_name}"] = iban
        return account_map

    def get_tan_mechanism(self) -> dict[str, str]:
        """!
        @brief Get available TAN mechanisms.
        @return mapping of security function code to display name.
        """
        mechanism_map = {}
        assert self.client is not None
        with self.client:
            tan_mechanisms = self.client.get_tan_mechanisms()
            for _tan_code, tan_mechanism in tan_mechanisms.items():
                if tan_mechanism.security_function in ALLOWED_TAN_MECHANISMS:
                    mechanism_map[tan_mechanism.security_function] = f"{tan_mechanism.security_function} {tan_mechanism.name}"
        return mechanism_map

    def get_and_create_transaction(self) -> tuple[bool, str]:
        """!
        @brief Retrieve transactions from bank and save to CSV file.
        @return success status and status text.
        """
        success = False
        success_text = "Unbekannt"
        assert self.client is not None
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
                    booked_streams, _pending_streams = self.ask_for_tan(self.client, response)
                else:
                    booked_streams = response
                    log.warning("Keine TAN Eingabe erforderlich")

                transactions = []
                for s in booked_streams:
                    for t in camt053_to_dict(s):
                        data = Transaction(t).data
                        amount_entry = data.get("amount")
                        transactions.append([
                            data.get("date"),
                            amount_entry.amount if amount_entry else None,
                            data.get("purpose"),
                            data.get("text"),
                            data.get("applicant_name"),
                            data.get("customer_reference")
                        ])

                create_transaction_file(transactions)

                if WRITE_SESSION_DATA:
                    client_blob = self.client.deconstruct(including_private=True)
                    with open(DATAFILE, "wb") as f:
                        f.write(client_blob)

                success = True
                success_text = f"Es wurden {len(transactions)} Transaktionen für das Konto {select_account.iban} gefunden."
            else:
                success_text = "Account nicht gefunden"
        return success, success_text
