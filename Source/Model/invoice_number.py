"""!
********************************************************************************
@file   invoice_number.py
@brief  Create invoice number
********************************************************************************
"""

import logging
import enum
import re

from PyQt6.QtCore import QDate

from Source.Model.data_handler import DATE_FORMAT
from Source.version import __title__
from Source.Model.data_handler import EReceiptFields
from Source.Model.company import COMPANY_DEFAULT_FIELD, ECompanyFields

log = logging.getLogger(__title__)


class SeqReset(str, enum.Enum):
    """!
    @brief Available Sequence reset options
    """
    NONE = "none"
    DAILY = "daily"
    MONTHLY = "monthly"
    YEARLY = "yearly"


RESET_PATTERN = "|".join(e.value for e in SeqReset)

SEQ_PATTERN = (
    r"\{SEQ"
    fr"(?::({RESET_PATTERN}))?"
    r"(?::(\d+))?"
    r"(?::(\d+))?"
    r"(?::(\d+))?"
    r"\}"
)
TOTAL_PATTERN = r".*(" + SEQ_PATTERN + r").*"


class InvoiceNumber:
    """!
    @brief Class to get next invoice number.
    @param ui : main window object
    """

    def __init__(self, ui: "MainWindow") -> None:
        self.ui = ui
        self.last_invoice_numbers = []
        for income in self.ui.tab_income.l_data:
            self.last_invoice_numbers.append(income[EReceiptFields.INVOICE_NUMBER])
        self.last_invoice_dates = []
        for income in self.ui.tab_income.l_data:
            self.last_invoice_dates.append(income[EReceiptFields.INVOICE_DATE])
        self.pattern = self.ui.tab_settings.company_data[COMPANY_DEFAULT_FIELD][ECompanyFields.INVOICE_NUMBER]
        # self.pattern = "{YYYY}-{SEQ:daily:4}"

    def set_date_in_pattern(self, date: QDate, pattern: str) -> str:
        """!
        @brief Set date in pattern
        @param date : date
        @param pattern : pattern
        @return pattern with date placeholders replaced
        """
        date_replacements = {
            "{YYYY}": str(date.year()),
            "{YY}": str((date.year() % 100)).zfill(2),
            "{Y}": str(date.year() % 10),
            "{MM}": str(date.month()).zfill(2),
            "{DD}": str(date.day()).zfill(2),
        }
        for key, val in date_replacements.items():
            pattern = pattern.replace(key, val)
        return pattern

    def needs_reset(self, reset_mode: str, last_date: QDate, current_date: QDate) -> bool:
        """!
        @brief Get reset status for sequence in invoice number.
        @param reset_mode : reset mode
        @param last_date : last date
        @param current_date : current date
        @return reset status of sequence
        """
        b_needs_reset = False
        match reset_mode:
            case SeqReset.NONE:
                b_needs_reset = False
            case SeqReset.DAILY:
                b_needs_reset = bool(last_date != current_date)
            case SeqReset.MONTHLY:
                b_needs_reset = bool((last_date.year() != current_date.year()) or (last_date.month() != current_date.month()))
            case SeqReset.YEARLY:
                b_needs_reset = bool(last_date.year() != current_date.year())
        return b_needs_reset

    def create_invoice_number(self, date: QDate) -> str:
        """!
        @brief Get invoice number depend on invoice pattern definition.
            Supported Pattern:
            - {YYYY} 4-digit year
            - {YY} 2-digit year
            - {Y} 1-digit year
            - {MM} month (01-12)
            - {DD} day (01-31)
            - {SEQ:reset:length:start:increment} - parameters after SEQ are optional
        @param date : date to create invoice number
        @return invoice number
        """
        invoice_number = ""
        template = self.set_date_in_pattern(date, self.pattern)

        # replace sequence
        match = re.search(TOTAL_PATTERN, template)
        if match:
            sequence_entry = match.group(1)  # only SEQ block
            reset_mode = match.group(2) or SeqReset.NONE.value
            seq_length = int(match.group(3)) if match.group(3) else 0
            seq_start = int(match.group(4)) if match.group(4) else 1
            seq_increment = int(match.group(5)) if match.group(5) else 1

            for last_number, last_date in zip(reversed(self.last_invoice_numbers), reversed(self.last_invoice_dates)):
                if last_number:
                    last_qdate = QDate.fromString(last_date, DATE_FORMAT)
                    last_template = self.set_date_in_pattern(last_qdate, self.pattern)
                    last_compare = last_template.replace(sequence_entry, "")
                    last_sequence = last_number.replace(last_compare, "")
                    if len(last_sequence) == seq_length and last_sequence.isdigit():
                        last_seq_int = int(last_sequence)
                        if not self.needs_reset(reset_mode, last_qdate, date):
                            seq_start = last_seq_int + seq_increment
                        break

            # check for present seq
            sequence_end = int("9" * seq_length) if (seq_length > 0) else 999999999
            for seq in range(seq_start, sequence_end + 1, seq_increment):
                prepared_invoice_number = template.replace(sequence_entry, str(seq).zfill(seq_length))
                if prepared_invoice_number not in self.last_invoice_numbers:
                    invoice_number = prepared_invoice_number
                    break
        return invoice_number
