"""!
********************************************************************************
@file   ollama_ai.py
@brief  Handle local AI models via Ollama with enhanced prompts
        https://ollama.com/blog/structured-outputs
********************************************************************************
"""

import logging
import subprocess
import enum
from ollama import chat

from PyQt6.QtCore import QThread, pyqtSignal

from Source.version import __title__
from Source.Util.app_data import run_subprocess, read_ollama_model, write_ollama_model
from Source.Model.ai_data import InvoiceData, create_user_message, validate_answer, get_ai_document_text, EMPTY_INVOICE_DATA

log = logging.getLogger(__title__)


class EOllamaModel(str, enum.Enum):
    """!
    @brief Ollama model. See https://ollama.com/library
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


class OllamaAI(QThread):
    """!
    @brief Class for parse invoice data with Ollama AI
    """
    finish_signal = pyqtSignal(InvoiceData)

    def __init__(self) -> None:
        super().__init__()
        self.init_check = False
        self.b_ready = False
        self.file_path = None  # file to detect in actual call
        self.b_ollama_installed = False
        self.l_models = []
        self.model = DEFAULT_OLLAMA_MODEL
        self.set_model(read_ollama_model())
        self.initialize_ollama()

    def set_model(self, model: str) -> None:
        """!
        @brief Set model
        @param model : model
        """
        self.model = model if model else DEFAULT_OLLAMA_MODEL
        write_ollama_model(model)

    def get_ready_state(self) -> bool:
        """!
        @brief Get ready state.
        @return ready state
        """
        if not self.init_check:
            self.initialize_ollama()
        return self.b_ready

    def initialize_ollama(self) -> None:
        """!
        @brief Initialize Ollama
        """
        self.init_check = True
        self.b_ready = False
        self.b_ollama_installed = self.check_ollama_installed()
        if self.b_ollama_installed:
            self.l_models = self.list_available_models()
        if self.model in self.l_models:
            self.b_ready = True

    def check_ollama_installed(self) -> bool:
        """!
        @brief Check if Ollama is installed
        @return installed status
        """
        ollama_installed = False
        try:
            _result = run_subprocess(["ollama", "--version"])
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
        @brief Get available ollama models
        @return list with available models
        """
        models = []
        try:
            result = run_subprocess(["ollama", "list"])
            lines = result.stdout.strip().split("\n")
            model_lines = lines[1:]
            for line in model_lines:
                models.append(line.split()[0])
        except subprocess.CalledProcessError as e:
            log.debug("Ollama process error: %s", e)
        log.debug("Installed models: %s", models)
        return models

    def ask_ollama(self, text: str) -> InvoiceData | None:
        """!
        @brief Ask ollama
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
            response = chat(messages=messages, model=self.model, format=InvoiceData.model_json_schema())
            document_data = InvoiceData.model_validate_json(response.message.content)  # pylint: disable=no-member
        except Exception as e:
            log.warning("Error during ask Ollama: %s", e)
            document_data = None
        else:
            document_data = validate_answer(document_data)

        return document_data

    def run(self) -> None:
        """!
        @brief Extract text from PDF and get invoice data via Ollama
        """
        invoice_data = None
        text = get_ai_document_text(self.file_path)
        if text:
            invoice_data = self.ask_ollama(text)
        if invoice_data is None:
            invoice_data = EMPTY_INVOICE_DATA
        self.finish_signal.emit(invoice_data)
