"""!
********************************************************************************
@file   ollama_ai.py
@brief  Ollama AI
        https://ollama.com/blog/structured-outputs
********************************************************************************
"""

import logging
import subprocess
import enum
from ollama import chat
import psutil

from PyQt6.QtCore import QThread, pyqtSignal

from Source.version import __title__
from Source.Util.app_data import run_subprocess, read_ollama_model, write_ollama_model
from Source.Model.ai_data import InvoiceData, create_user_message, validate_answer, get_ai_document_text, EMPTY_INVOICE_DATA

log = logging.getLogger(__title__)


class EOllamaModel(str, enum.Enum):
    """!
    @brief Ollama model
    """
    DEEPSEEK_R1_70B = "deepseek-r1:70b"  # 43GB
    DEEPSEEK_R1_32B = "deepseek-r1:32b"  # 20GB
    DEEPSEEK_R1_14B = "deepseek-r1:14b"  # 9GB
    DEEPSEEK_R1_8B = "deepseek-r1:8b"  # 4.9GB
    LLAMA3_3_70B = "llama3.3:70b"  # 43GB
    PHI4_14B = "phi4:14b"  # 9.1GB
    LLAMA3_2_3B = "llama3.2:3b"  # 2GB
    LLAMA3_1_8B = "llama3.1:8b"  # 4.9GB
    LLAMA3_1_70B = "llama3.1:70b"  # 43GB


# set highest RAM at top for best auto selection
D_OLLAMA_RAM_RES = {
    EOllamaModel.LLAMA3_1_8B.value: 4.9,
    EOllamaModel.LLAMA3_2_3B.value: 2,
    EOllamaModel.LLAMA3_3_70B.value: 43,
}

I_RAM_OFFSET = 5  # more RAM in GB that model use


class OllamaAI(QThread):
    """!
    @brief Class for parse invoice data with Ollama AI
    """
    finish_signal = pyqtSignal(InvoiceData)

    def __init__(self) -> None:
        super().__init__()
        self.init_check = False
        self.model = read_ollama_model()  # selected model
        self.l_models = []
        self.i_ram_size = 0
        self.b_ollama_installed = False
        self.b_ready = False
        self.file_path = None  # file to detect in actual call
        self.initialize_ollama()

    def set_model(self, model: str) -> None:
        """!
        @brief Set model
        @param model : model
        """
        if self.model:
            model = self.model  # use custom model if present

        self.b_ready = False
        if not self.b_ollama_installed:
            log.debug("Ollama not installed model to: %s", model)
        elif model not in self.l_models:
            log.debug("Model not installed: %s", model)
        else:
            self.model = model
            self.b_ready = True
            log.debug("Changing Ollama model to: %s", model)
        log.debug("Ollama ready status: %s", self.b_ready)
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
        self.i_ram_size = self.get_ram_size()
        self.b_ollama_installed = self.check_ollama_installed()
        if self.b_ollama_installed:
            self.l_models = self.list_available_models()
        if not self.model:
            self.set_auto_model()
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

    def get_ram_size(self) -> int:
        """!
        @brief Set auto model for Ollama AI
        @return total RAM size in GB (rounded as integer)
        """
        total_ram = psutil.virtual_memory().total
        total_ram_gb = round(total_ram / (1024 ** 3))
        log.debug("Total RAM: %s GB", total_ram_gb)
        return total_ram_gb

    def set_auto_model(self) -> None:
        """!
        @brief Set auto model for Ollama AI
        """
        for model, req_ram in D_OLLAMA_RAM_RES.items():
            if (req_ram + I_RAM_OFFSET <= self.i_ram_size) and (model in self.l_models):
                log.debug("Set auto model: %s", model)
                self.set_model(model)
                break

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
        @brief Run Ollama to get invoice data from PDF
        """
        invoice_data = None
        text = get_ai_document_text(self.file_path)
        if text:
            invoice_data = self.ask_ollama(text)
        if invoice_data is None:
            invoice_data = EMPTY_INVOICE_DATA
        self.finish_signal.emit(invoice_data)
