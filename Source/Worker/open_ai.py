"""!
********************************************************************************
@file   open_ai.py
@brief  Handle Open AI functions via ChatGPT with enhanced prompts
        https://platform.openai.com/docs/guides/structured-outputs
********************************************************************************
"""

import logging
import openai
from openai import AuthenticationError

from PyQt6.QtCore import QThread, pyqtSignal

from Source.version import __title__
from Source.Util.app_data import read_api_key, read_gpt_model, write_gpt_model
from Source.Model.ai_data import InvoiceData, create_user_message, validate_answer, get_ai_document_text, EMPTY_INVOICE_DATA

log = logging.getLogger(__title__)

DEFAULT_GPT_MODEL = "gpt-4o-mini"  # possible models ["gpt-4o-mini", "gpt-4o-2024-08-06"]


class OpenAI(QThread):
    """!
    @brief Class for parse invoice data with OpenAI
    """
    finish_signal = pyqtSignal(InvoiceData)

    def __init__(self) -> None:
        super().__init__()
        self.init_check = False
        self.b_ready = False
        self.file_path = None  # file to detect in actual call
        self.openai_client = None
        self.model = DEFAULT_GPT_MODEL
        self.set_model(read_gpt_model())
        self.api_key = read_api_key()
        self.initialize_openai_client()

    def set_model(self, model: str) -> None:
        """!
        @brief Set model
        @param model : model
        """
        self.model = model if model else DEFAULT_GPT_MODEL
        write_gpt_model(self.model)

    def get_ready_state(self) -> bool:
        """!
        @brief Get ready state.
        @return ready state
        """
        if not self.init_check:
            self.initialize_openai_client()
        return self.b_ready

    def initialize_openai_client(self) -> None:
        """!
        @brief Initialize OpenAI client
        """
        self.init_check = True
        self.openai_client = None
        if self.api_key:
            try:
                # Set the API key
                openai.api_key = self.api_key
                # Test by making a simple API request (e.g., list available models)
                openai.models.list()  # Liste der verfügbaren Modelle
            except AuthenticationError:
                log.warning("Invalid API key.")
            except Exception as e:
                log.warning("An error occurred: %s", e)
            else:
                self.openai_client = openai  # type: ignore
                self.b_ready = True
                log.info("OpenAI-Client successfully initialized.")

    def ask_openai(self, text: str) -> InvoiceData | None:
        """!
        @brief Ask OpenAI
        @param text : document text
        @return invoice data
        """
        document_data = None
        messages = [
            {
                "role": "user",
                "content": create_user_message(text),
            }]

        try:
            response = self.openai_client.beta.chat.completions.parse(
                model=self.model,  # only this model support structured output
                messages=messages,
                response_format=InvoiceData,
            )
            document_data = response.choices[0].message.parsed
        except Exception as e:
            log.warning("Error during ask OpenAI: %s", e)
            document_data = None
        else:
            document_data = validate_answer(document_data)

        return document_data

    def run(self) -> None:
        """!
        @brief Run OpenAI to get invoice data from PDF
        """
        invoice_data = None
        text = get_ai_document_text(self.file_path)
        if text:
            invoice_data = self.ask_openai(text)
        if invoice_data is None:
            invoice_data = EMPTY_INVOICE_DATA
        self.finish_signal.emit(invoice_data)
