"""!
********************************************************************************
@file   ollama_ai.py
@brief  Parse invoice data via local Ollama models with structured output prompts.
        https://ollama.com/blog/structured-outputs
********************************************************************************
"""

import logging
import subprocess
import enum
from ollama import chat

from Source.version import __title__
from Source.Util.app_data import run_subprocess, read_ollama_model, write_ollama_model
from Source.Model.ai_data import InvoiceData, create_user_message, validate_answer
from Source.Worker.base_ai import BaseAIWorker

log = logging.getLogger(__title__)


class EOllamaModel(str, enum.Enum):
    """!
    @brief Available Ollama model identifiers. See https://ollama.com/library
    """
    # Meta
    LLAMA3_1_8B = "llama3.1:8b"  # 4.9GB
    LLAMA3_1_70B = "llama3.1:70b"  # 43GB
    LLAMA3_2_1B = "llama3.2:1b"  # 1.3GB
    LLAMA3_2_3B = "llama3.2:3b"  # 2GB
    LLAMA3_3_70B = "llama3.3:70b"  # 43GB
    # Mistral
    MISTRAL_7B = "mistral:7b"  # 4.4GB
    MISTRAL_SMALL_22B = "mistral-small:22b"  # 13GB
    MISTRAL_SMALL_24B = "mistral-small:24b"  # 14GB
    MISTRAL_SMALL3_1_24B = "mistral-small3.1:24b"  # 15GB
    MISTRAL_SMALL3_2_24B = "mistral-small3.2:24b"  # 15GB
    # Microsoft
    PHI3_3_3B = "phi3:3.8b"  # 2.2GB
    PHI3_14B = "phi3:14b"  # 7.9GB
    PHI4_14B = "phi4:14b"  # 9.1GB
    # Deepseek
    DEEPSEEK_R1_1_5B = "deepseek-r1:1.5b"  # 1.1GB
    DEEPSEEK_R1_7B = "deepseek-r1:7b"  # 4.7GB
    DEEPSEEK_R1_8B = "deepseek-r1:8b"  # 5.2GB
    DEEPSEEK_R1_14B = "deepseek-r1:14b"  # 9GB
    DEEPSEEK_R1_32B = "deepseek-r1:32b"  # 20GB
    DEEPSEEK_R1_70B = "deepseek-r1:70b"  # 43GB


DEFAULT_OLLAMA_MODEL = EOllamaModel.LLAMA3_1_8B.value


class OllamaAI(BaseAIWorker):
    """!
    @brief Class for parsing invoice data with Ollama AI.
    """

    def __init__(self) -> None:
        self.ollama_installed = False
        self.models: list[str] = []
        super().__init__(
            default_model=DEFAULT_OLLAMA_MODEL,
            read_model=read_ollama_model,
            write_model=write_ollama_model,
        )

    def initialize_client(self) -> None:
        """!
        @brief Check Ollama installation, list models, and set readiness status.
        """
        self.init_check = True
        self.ready = False
        self.ollama_installed = self.check_ollama_installed()
        if self.ollama_installed:
            self.models = self.list_available_models()
        if self.model in self.models:
            self.ready = True

    def check_ollama_installed(self) -> bool:
        """!
        @brief Check if Ollama is installed.
        @return True if Ollama is installed, False otherwise.
        """
        ollama_installed = False
        try:
            run_subprocess(["ollama", "--version"])
        except FileNotFoundError:
            log.debug("Ollama is not installed")
        except subprocess.CalledProcessError as e:
            log.debug("Ollama process error: %s", e)
        else:
            ollama_installed = True
        log.debug("Ollama installed status: %s", ollama_installed)
        return ollama_installed

    def list_available_models(self) -> list[str]:
        """!
        @brief Query locally installed Ollama models via CLI.
        @return List of available model names.
        """
        models = []
        try:
            result = run_subprocess(["ollama", "list"])
            lines = result.stdout.strip().split("\n")
            model_lines = lines[1:]
            for line in model_lines:
                parts = line.split()
                if parts:
                    models.append(parts[0])
        except subprocess.CalledProcessError as e:
            log.debug("Ollama process error: %s", e)
        log.debug("Installed models: %s", models)
        return models

    def ask_ai(self, text: str) -> InvoiceData | None:
        """!
        @brief Send document text to Ollama and parse structured invoice data from the response.
        @param text : document text to parse for invoice data.
        @return Parsed invoice data or None on failure.
        """
        document_data = None
        messages = [
            {
                "role": "user",
                "content": create_user_message(text),
            }]

        try:
            response = chat(messages=messages, model=self.model, format=InvoiceData.model_json_schema())
            if response.message.content is None:  # pylint: disable=no-member
                raise ValueError("Empty response from Ollama")
            document_data = InvoiceData.model_validate_json(response.message.content)  # pylint: disable=no-member
        except Exception as e:
            log.warning("Error during ask Ollama: %s", e)
        else:
            document_data = validate_answer(document_data)

        return document_data
