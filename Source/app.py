"""!
********************************************************************************
@file   app.py
@brief  Application entry file
********************************************************************************
"""

# autopep8: off
import sys
import os
import time
import logging

from PyQt6.QtGui import QIcon  # pylint: disable=wrong-import-position
from PyQt6.QtWidgets import QApplication  # pylint: disable=wrong-import-position
from PyQt6.QtCore import QSharedMemory, QTimer  # pylint: disable=wrong-import-position

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from Source.version import __title__, __version__  # pylint: disable=wrong-import-position
from Source.Util.app_data import I_LOG_LEVEL_DEFAULT, ICON_APP  # pylint: disable=wrong-import-position
from Source.Util.app_err_handler import UncaughtHook  # pylint: disable=wrong-import-position
from Source.Util.app_log import LogConfig  # pylint: disable=wrong-import-position
from Source.Controller.main_window import MainWindow  # pylint: disable=wrong-import-position
from Source.Controller.splash_screen import create_splash_screen, F_MIN_SPLASH_SCREEN_TIME  # pylint: disable=wrong-import-position
# autopep8: on

log = logging.getLogger(__title__)


def start_application() -> QApplication:
    """!
    @brief Start application
    @return application instance
    """
    # Logging setup
    log_config = LogConfig(I_LOG_LEVEL_DEFAULT)
    log_config.update_log_level(I_LOG_LEVEL_DEFAULT)
    log.debug("Starting application")
    log.debug("Running from %s", os.getcwd())

    # Initialize QApplication
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(ICON_APP))

    # Set custom Windows app user model ID (taskbar icon)
    try:
        from ctypes import windll  # only exists on windows. # pylint: disable=import-outside-toplevel
        app_id = f"{__title__}.{__version__}"
        log.debug("Setting explicit app user model ID: %s", app_id)
        windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except ImportError:
        log.debug("Windows-specific app user model ID not set")

    # Splash screen
    splash = create_splash_screen()
    f_start_time = time.time()
    splash.show()
    app.processEvents()

    # Exception handler and main window
    qt_exception_hook = UncaughtHook()
    window = MainWindow(qt_exception_hook, log_config)
    window.setWindowIcon(QIcon(ICON_APP))  # ensure icon is set
    qt_exception_hook.set_main_window_controller(window)

    # Ensure minimum splash screen display time
    f_init_time = time.time() - f_start_time
    remaining_time_ms = max(int((F_MIN_SPLASH_SCREEN_TIME - f_init_time) * 1000), 0)

    def show_main_window():
        """!
        @brief Close splash screen and show main window
        """
        splash.close()
        window.show()

    QTimer.singleShot(remaining_time_ms, show_main_window)

    return app


if __name__ == "__main__":
    # Prevent multiple instances
    shared_memory = QSharedMemory(__title__)
    if not shared_memory.create(1):
        sys.exit("Another instance is already running")

    app_instance = start_application()
    sys.exit(app_instance.exec())
