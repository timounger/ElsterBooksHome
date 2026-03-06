"""!
********************************************************************************
@file   open_ai.py
@brief  Parse invoice data via OpenAI API with structured output prompts.
        https://platform.openai.com/docs/guides/structured-outputs
********************************************************************************
"""

import logging
import openai
from openai import AuthenticationError

from Source.version import __title__
from Source.Util.app_data import read_gpt_api_key, read_gpt_model, write_gpt_model, write_gpt_api_key
from Source.Model.ai_data import InvoiceData, create_user_message, validate_answer
from Source.Worker.base_ai import BaseAIWorker

log = logging.getLogger(__title__)

DEFAULT_GPT_MODEL = "gpt-4o-mini"  # possible models ["gpt-4o-mini", "gpt-4o-2024-08-06"]


class OpenAI(BaseAIWorker):
    """!
    @brief Class for parsing invoice data with OpenAI.
    """

    def __init__(self) -> None:
        self.openai_client = None
        super().__init__(
            default_model=DEFAULT_GPT_MODEL,
            read_model=read_gpt_model,
            write_model=write_gpt_model,
            read_api_key=read_gpt_api_key,
            write_api_key=write_gpt_api_key,
        )

    def initialize_client(self) -> None:
        """!
        @brief Initialize OpenAI client with the current API key.
        """
        self.init_check = True
        self.ready = False
        self.openai_client = None
        if self.api_key:
            try:
                openai.api_key = self.api_key
                openai.models.list()
            except AuthenticationError:
                log.warning("Invalid API key.")
            except Exception as e:
                log.warning("An error occurred: %s", e)
            else:
                self.openai_client = openai  # type: ignore
                self.ready = True
                log.info("OpenAI-Client successfully initialized.")

    def ask_ai(self, text: str) -> InvoiceData | None:
        """!
        @brief Send document text to OpenAI and parse structured invoice data from the response.
        @param text : document text to parse for invoice data.
        @return Parsed invoice data or None on failure.
        """
        document_data = None
        if self.openai_client is None:
            log.warning("OpenAI client not initialized")
            return None

        messages = [
            {
                "role": "user",
                "content": create_user_message(text),
            }]

        try:
            response = self.openai_client.responses.parse(
                model=self.model,
                input=messages,
                text_format=InvoiceData,
            )
            document_data = response.output_parsed
        except Exception as e:
            log.warning("Error during ask OpenAI: %s", e)
        else:
            document_data = validate_answer(document_data)

        return document_data
