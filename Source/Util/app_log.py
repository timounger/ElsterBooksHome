"""!
********************************************************************************
@file   app_log.py
@brief  Logging class to store and manage log configuration
********************************************************************************
"""

import logging
from typing import TYPE_CHECKING

from Source.version import __title__
from Source.Util.colored_log import get_format, ColorFormatter, S_LOG_DATE_FORMAT
if TYPE_CHECKING:
    from Source.Controller.main_window import MainWindow

log = logging.getLogger(__title__)
formatter = logging.Formatter(fmt=get_format(line_no=False, threads=False), datefmt=S_LOG_DATE_FORMAT)
color_formatter = ColorFormatter(line_no=True, threads=True, data_format=None)

S_LOGGING_FILE = "app_log.log"


class LogConfig:
    """!
    @brief Log configuration. Supports dynamic change of log level
    @param i_log_level : integer representing the initial log level
    """

    def __init__(self, i_log_level: int) -> None:
        self.ui: "MainWindow | None" = None
        self.i_log_level = i_log_level
        self.root_logger = logging.getLogger()

        # Clear existing handlers
        self.root_logger.handlers.clear()

        # initialize console handler to print log messages to stdout stream
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(color_formatter)
        console_handler.setLevel(self.i_log_level)
        self.root_logger.addHandler(console_handler)

        # save log messages additionally to a log file
        file_handler = logging.FileHandler(S_LOGGING_FILE)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(self.i_log_level)
        self.root_logger.addHandler(file_handler)

    def update_log_level(self, i_log_level: int) -> None:
        """!
        @brief Sets a new log level for all handlers
        @param i_log_level : new log level
        """
        s_text = f"Verbosität eingestellt auf {logging.getLevelName(i_log_level)}"
        if self.ui is not None:
            self.ui.set_status(s_text)
        else:
            log.debug(s_text)

        self.i_log_level = i_log_level
        self.root_logger.setLevel(i_log_level)
        # update log level for each log handler
        for handler in self.root_logger.handlers:
            handler.setLevel(i_log_level)
