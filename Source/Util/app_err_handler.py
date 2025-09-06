"""!
********************************************************************************
@file   app_err_handler.py
@brief  Error handler to catch all unexpected exceptions to prevent application crashes
********************************************************************************
"""

# Source: https://timlehr.com/python-exception-hooks-with-qt-message-box/

import sys
import traceback
import logging
from typing import Optional, Any, TYPE_CHECKING
from types import TracebackType

from PyQt6.QtWidgets import QMessageBox, QApplication
from PyQt6.QtCore import QObject, pyqtSignal

from Source.version import __title__
from Source.Util.app_data import clear_settings

if TYPE_CHECKING:
    from Source.Controller.main_window import MainWindow

log = logging.getLogger(__title__)

B_CLOSE_WITH_REPAIR_DIALOG = False


class UncaughtHook(QObject):
    """!
    @brief Global exception handler. Overrides system exception hook to catch all unexpected errors.
    """
    exception_caught = pyqtSignal(object)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        log.debug("Initializing Exception Handler")

        super().__init__(*args, **kwargs)

        self.main_window_controller: "MainWindow | None" = None
        self.crash_arrived = False

        # this registers the exception_hook() function as hook with the Python interpreter
        sys.excepthook = self.exception_hook

        # connect signal to execute the message box function always on main thread
        self.exception_caught.connect(self.show_exception_box)

    def show_exception_box(self, s_log_msg: str) -> None:
        """!
        @brief Displays the error message box
        @param s_log_msg : the error message to be displayed in details section
        """
        # check if QApplication instance is available
        self.crash_arrived = True
        if (QApplication is not None) and (QApplication.instance() is not None):
            dialog = QMessageBox(self.main_window_controller)
            dialog.setWindowTitle("Error")
            dialog.setText("Ein unerwarteter Fehler ist aufgetreten\t\t\t\t")
            dialog.addButton(QMessageBox.StandardButton.Close)
            close_btn = dialog.button(QMessageBox.StandardButton.Close)
            if close_btn is not None:
                close_btn.setText("Schließen")
            if B_CLOSE_WITH_REPAIR_DIALOG:
                dialog.addButton("Reparieren", QMessageBox.ButtonRole.ResetRole)
            dialog.setDetailedText(s_log_msg)
            dialog.close()
            choice = dialog.exec()

            if B_CLOSE_WITH_REPAIR_DIALOG:
                choice = choice not in [QMessageBox.StandardButton.Close]
                if choice:
                    clear_settings()
                if self.main_window_controller:
                    self.main_window_controller.close()
                else:
                    sys.exit(1)
        else:
            log.error("Can't show Exception Display - No QApplication instance available.")

    def exception_hook(self, exc_type: type[BaseException], exc_value: BaseException, exc_traceback: Optional[TracebackType] = None) -> None:
        """!
        @brief Custom exception hook. It is triggered each time an uncaught exception occurs.
        @param exc_type : exception type
        @param exc_value : exception value
        @param exc_traceback : exception traceback
        """
        if issubclass(exc_type, KeyboardInterrupt):
            # ignore keyboard interrupt to support console application
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
        else:
            log_msg = "\n".join([f"{exc_type.__name__}: {exc_value}",
                                 "".join(traceback.format_tb(exc_traceback))])
            log.error(log_msg)

            # trigger message box show
            self.exception_caught.emit(log_msg)

    def set_main_window_controller(self, main_window_controller: "MainWindow") -> None:
        """!
        @brief Sets the main window controller in order to unblock the UI after a critical exception is caught.
        @param main_window_controller : main window controller
        """
        self.main_window_controller = main_window_controller
