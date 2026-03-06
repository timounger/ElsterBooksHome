"""!
********************************************************************************
@file   gemini_ai.py
@brief  Parse invoice data via Google Gemini API with structured output prompts.
        https://ai.google.dev/gemini-api/docs/structured-output?hl=de&example=recipe
********************************************************************************
"""

import logging
from google import genai

from Source.version import __title__
from Source.Util.app_data import read_gemini_api_key, read_gemini_model, write_gemini_model, write_gemini_api_key
from Source.Model.ai_data import InvoiceData, create_user_message, validate_answer
from Source.Worker.base_ai import BaseAIWorker

log = logging.getLogger(__title__)

DEFAULT_GEMINI_MODEL = "gemini-2.0-flash-lite"  # possible models ["gemini-2.0-flash-lite", "gemini-3-flash-preview"]


class GeminiAI(BaseAIWorker):
    """!
    @brief Class for parsing invoice data with Gemini.
    """

    def __init__(self) -> None:
        self.gemini_client = None
        super().__init__(
            default_model=DEFAULT_GEMINI_MODEL,
            read_model=read_gemini_model,
            write_model=write_gemini_model,
            read_api_key=read_gemini_api_key,
            write_api_key=write_gemini_api_key,
        )

    def initialize_client(self) -> None:
        """!
        @brief Initialize Gemini client with the current API key.
        """
        self.init_check = True
        self.ready = False
        self.gemini_client = None
        if self.api_key:
            try:
                gemini_client = genai.Client(api_key=self.api_key)
                gemini_client.models.list()
            except Exception as e:
                log.warning("An error occurred: %s", e)
            else:
                self.gemini_client = gemini_client  # type: ignore
                self.ready = True
                log.info("Gemini-Client successfully initialized.")

    def ask_ai(self, text: str) -> InvoiceData | None:
        """!
        @brief Send document text to Gemini and parse structured invoice data from the response.
        @param text : document text to parse for invoice data.
        @return Parsed invoice data or None on failure.
        """
        document_data = None
        if self.gemini_client is None:
            log.warning("Gemini client not initialized")
            return None

        try:
            response = self.gemini_client.models.generate_content(
                model=self.model,
                contents=create_user_message(text),
                config={
                    "response_mime_type": "application/json",
                    "response_json_schema": InvoiceData.model_json_schema(),
                },
            )
            document_data = InvoiceData.model_validate_json(response.text)
        except Exception as e:
            log.warning("Error during ask Gemini: %s", e)
        else:
            document_data = validate_answer(document_data)

        return document_data
