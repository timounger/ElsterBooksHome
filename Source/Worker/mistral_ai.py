"""!
********************************************************************************
@file   mistral_ai.py
@brief  Parse invoice data via Mistral AI API with structured output prompts.
        https://docs.mistral.ai/capabilities/structured_output
********************************************************************************
"""

import logging
import json
from pydantic import ValidationError
from mistralai import Mistral

from Source.version import __title__
from Source.Util.app_data import read_mistral_api_key, read_mistral_model, write_mistral_model, write_mistral_api_key
from Source.Model.ai_data import InvoiceData, create_user_message, validate_answer
from Source.Worker.base_ai import BaseAIWorker

log = logging.getLogger(__title__)

DEFAULT_MISTRAL_MODEL = "mistral-small-latest"  # possible models ["mistral-small-latest", "mistral-medium-latest"]


class MistralAI(BaseAIWorker):
    """!
    @brief Class for parsing invoice data with Mistral.
    """

    def __init__(self) -> None:
        self.mistral_client = None
        super().__init__(
            default_model=DEFAULT_MISTRAL_MODEL,
            read_model=read_mistral_model,
            write_model=write_mistral_model,
            read_api_key=read_mistral_api_key,
            write_api_key=write_mistral_api_key,
        )

    def initialize_client(self) -> None:
        """!
        @brief Initialize Mistral client with the current API key.
        """
        self.init_check = True
        self.ready = False
        self.mistral_client = None
        if self.api_key:
            try:
                mistral_client = Mistral(api_key=self.api_key)
                mistral_client.models.list()
            except Exception as e:
                log.warning("An error occurred: %s", e)
            else:
                self.mistral_client = mistral_client  # type: ignore
                self.ready = True
                log.info("Mistral-Client successfully initialized.")

    def ask_ai(self, text: str) -> InvoiceData | None:
        """!
        @brief Send document text to Mistral and parse structured invoice data from the response.
        @param text : document text to parse for invoice data.
        @return Parsed invoice data or None on failure.
        """
        document_data = None
        if self.mistral_client is None:
            log.warning("Mistral client not initialized")
            return None

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
            if not response.choices or response.choices[0].message.content is None:
                log.warning("Mistral returned empty response")
                return document_data
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
        else:
            document_data = validate_answer(document_data)

        return document_data
