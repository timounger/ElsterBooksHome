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
from PyQt6.QtCore import QSharedMemory  # pylint: disable=wrong-import-position

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from Source.version import __title__, __version__  # pylint: disable=wrong-import-position
from Source.Util.app_data import I_LOG_LEVEL_DEFAULT, ICON_APP  # pylint: disable=wrong-import-position
from Source.Util.app_err_handler import UncaughtHook  # pylint: disable=wrong-import-position
from Source.Util.app_log import LogConfig  # pylint: disable=wrong-import-position

from Source.Controller.main_window import MainWindow  # pylint: disable=wrong-import-position
from Source.Controller.splash_screen import create_splash_screen, F_MIN_SPLASH_SCREEN_TIME  # pylint: disable=wrong-import-position
# autopep8: on

log = logging.getLogger(__title__)


def start_application() -> tuple[QApplication, MainWindow]:
    """!
    @brief Start application
    @return windows and application object
    """
    log_config = LogConfig(I_LOG_LEVEL_DEFAULT)
    # write default setting here
    log_config.update_log_level(I_LOG_LEVEL_DEFAULT)
    log.debug("Starting application")
    log.debug("Running from %s", os.getcwd())

    # Application
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(ICON_APP))  # set icon direct

    # Set custom application id to show correct icon instead of Python in the task bar
    try:
        from ctypes import windll  # only exists on windows. # pylint: disable=import-outside-toplevel
        app_id = __title__ + "." + __version__
        log.debug("Setting explicit app user model id: %s", app_id)
        windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except ImportError:
        pass

    splash = create_splash_screen()

    f_start_time = time.time()
    splash.show()

    app.processEvents()

    # Exception Handler
    qt_exception_hook = UncaughtHook()
    window = MainWindow(qt_exception_hook, log_config)

    window.setWindowIcon(QIcon(ICON_APP))  # set icon again if not set before
    qt_exception_hook.set_main_window_controller(window)

    f_inti_time = time.time() - f_start_time
    if f_inti_time < F_MIN_SPLASH_SCREEN_TIME:
        time.sleep(F_MIN_SPLASH_SCREEN_TIME - f_inti_time)

    splash.close()

    return app, window


if __name__ == "__main__":
    shared_memory = QSharedMemory(__title__)  # need to use as global variable
    if not shared_memory.create(1):
        sys.exit("Another instance is already running")
    o_app, o_window = start_application()
    o_window.show()
    sys.exit(o_app.exec())
