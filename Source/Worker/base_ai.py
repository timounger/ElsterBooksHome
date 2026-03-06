"""!
********************************************************************************
@file   base_ai.py
@brief  Base class for AI invoice data extraction workers.
********************************************************************************
"""

import logging
from abc import abstractmethod
from typing import Callable

from PyQt6.QtCore import QThread, pyqtSignal

from Source.version import __title__
from Source.Model.ai_data import InvoiceData, get_ai_document_text, EMPTY_INVOICE_DATA

log = logging.getLogger(__title__)


class BaseAIWorker(QThread):
    """!
    @brief Base class for AI workers that extract invoice data from documents.
    """
    finish_signal = pyqtSignal(InvoiceData)

    def __init__(self, default_model: str,
                 read_model: Callable[[], str], write_model: Callable[[str], None],
                 read_api_key: Callable[[], str] | None = None,
                 write_api_key: Callable[[str], None] | None = None) -> None:
        """!
        @brief Initialize base AI worker.
        @param default_model : default model name.
        @param read_model : function to read persisted model.
        @param write_model : function to write persisted model.
        @param read_api_key : function to read persisted API key (None for local models).
        @param write_api_key : function to write persisted API key (None for local models).
        """
        super().__init__()
        self.init_check = False
        self.ready = False
        self.file_path: str | None = None  # file path to process in run()
        self._default_model = default_model
        self._write_model = write_model
        self._write_api_key = write_api_key
        self.model = default_model
        self.set_model(read_model())
        self.api_key = read_api_key() if read_api_key else ""
        self.initialize_client()

    def set_model(self, model: str) -> None:
        """!
        @brief Set model and persist it.
        @param model : model name to use.
        """
        self.model = model if model else self._default_model
        self._write_model(self.model)

    def set_api_key(self, api_key: str) -> None:
        """!
        @brief Set API key and persist it.
        @param api_key : API key to use.
        """
        self.api_key = api_key
        if self._write_api_key:
            self._write_api_key(self.api_key)

    def get_ready_state(self) -> bool:
        """!
        @brief Check if the AI client has been initialized and is ready to process requests.
        @return True if the AI client is ready, False otherwise.
        """
        if not self.init_check:
            self.initialize_client()
        return self.ready

    @abstractmethod
    def initialize_client(self) -> None:
        """!
        @brief Set up the AI client connection and verify availability.
        """

    @abstractmethod
    def ask_ai(self, text: str) -> InvoiceData | None:
        """!
        @brief Query the AI model with document text.
        @param text : document text to parse for invoice data.
        @return Parsed invoice data or None on failure.
        """

    def run(self) -> None:
        """!
        @brief Extract text from document and get invoice data via AI.
        """
        invoice_data = None
        if self.file_path is None:
            self.finish_signal.emit(EMPTY_INVOICE_DATA)
            return
        text = get_ai_document_text(self.file_path)
        if text:
            invoice_data = self.ask_ai(text)
        if invoice_data is None:
            invoice_data = EMPTY_INVOICE_DATA
        if not self.isInterruptionRequested():
            self.finish_signal.emit(invoice_data)
