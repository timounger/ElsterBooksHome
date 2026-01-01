"""!
********************************************************************************
@file   mistral_ai.py
@brief  Handle Mistral AI functions
        https://docs.mistral.ai/capabilities/structured_output
********************************************************************************
"""

import logging
import json
from pydantic import ValidationError
from mistralai import Mistral

from PyQt6.QtCore import QThread, pyqtSignal

from Source.version import __title__
from Source.Util.app_data import read_mistral_api_key, read_mistral_model, write_mistral_model, write_mistral_api_key
from Source.Model.ai_data import InvoiceData, create_user_message, validate_answer, get_ai_document_text, EMPTY_INVOICE_DATA

log = logging.getLogger(__title__)

DEFAULT_MISTRAL_MODEL = "mistral-small-latest"  # possible models ["mistral-small-latest", "mistral-medium-latest"]


class MistralAI(QThread):
    """!
    @brief Class for parse invoice data with Mistral
    """
    finish_signal = pyqtSignal(InvoiceData)

    def __init__(self) -> None:
        super().__init__()
        self.init_check = False
        self.b_ready = False
        self.file_path = None  # file to detect in actual call
        self.mistral_client = None
        self.model = DEFAULT_MISTRAL_MODEL
        self.set_model(read_mistral_model())
        self.api_key = read_mistral_api_key()  # TODO Set Befehl um während Nutzung zu ändern
        self.initialize_mistral_client()

    def set_model(self, model: str) -> None:
        """!
        @brief Set model
        @param model : model
        """
        self.model = model if model else DEFAULT_MISTRAL_MODEL
        write_mistral_model(self.model)

    def set_api_key(self, api_key: str) -> None:
        """!
        @brief Set API key
        @param api_key : API key
        """
        self.api_key = api_key
        write_mistral_api_key(self.api_key)

    def get_ready_state(self) -> bool:
        """!
        @brief Get ready state.
        @return ready state
        """
        if not self.init_check:
            self.initialize_mistral_client()
        return self.b_ready

    def initialize_mistral_client(self) -> None:
        """!
        @brief Initialize Mistral client
        """
        self.init_check = True
        self.b_ready = False
        self.mistral_client = None
        if self.api_key:
            try:
                # Set the API key
                mistral_client = Mistral(api_key=self.api_key)
                # Test by making a simple API request (e.g., list available models)
                mistral_client.models.list()  # Liste der verfügbaren Modelle
            except Exception as e:
                log.warning("An error occurred: %s", e)
            else:
                self.mistral_client = mistral_client  # type: ignore
                self.b_ready = True
                log.info("Mistral-Client successfully initialized.")

    def ask_mistral(self, text: str) -> InvoiceData | None:
        """!
        @brief Ask Mistral
        @param text : document text
        @return invoice data
        """
        document_data = None

        system_prompt = (
            "Return ONLY valid JSON with exactly these fields:\n"
            "- invoice_date (string)\n"
            "- invoice_number (string)\n"
            "- gross_amount (number)\n"
            "- net_amount (number)\n"
            "- seller_name (string)\n"
            "- buyer_name (string)\n"
            "- description (string)\n"
        )

        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": create_user_message(text),
            }]

        try:
            response = self.mistral_client.chat.complete(
                model=self.model,
                messages=messages
            )
            raw_content = response.choices[0].message.content

            # clean json
            raw_content = raw_content.strip()
            if raw_content.startswith("```"):
                raw_content = raw_content.strip("`")
                if raw_content.lower().startswith("json"):
                    raw_content = raw_content[4:].strip()

            # json -> dict
            data = json.loads(raw_content)

            # mapping
            document_data = InvoiceData.model_validate(data)
        except json.JSONDecodeError as e:
            log.warning("Mistral returned invalid JSON: %s", e)
        except ValidationError as e:
            log.warning("InvoiceData validation failed: %s", e)
        except Exception as e:
            log.warning("Error during ask Mistral: %s", e)
            document_data = None
        else:
            document_data = validate_answer(document_data)

        return document_data

    def run(self) -> None:
        """!
        @brief Extract text from PDF and get invoice data via Mistral
        """
        invoice_data = None
        text = get_ai_document_text(self.file_path)
        if text:
            invoice_data = self.ask_mistral(text)
        if invoice_data is None:
            invoice_data = EMPTY_INVOICE_DATA
        self.finish_signal.emit(invoice_data)
