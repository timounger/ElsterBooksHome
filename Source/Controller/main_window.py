"""!
********************************************************************************
@file   main_window.py
@brief  Controller for the main application window.
********************************************************************************
"""

import logging
from typing import Any
import webbrowser

from PyQt6.QtGui import QIcon, QCloseEvent
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import QTimer

from Source.version import __title__, __issue__
from Source.version import BUILD_NAME
from Source.Util.app_data import write_window_state, ETab, group_menu, \
    ICON_HELP_LIGHT, ICON_HELP_DARK, ETheme, read_last_tab, write_last_tab, \
    read_update_version, write_update_version
from Source.Util.app_err_handler import UncaughtHook
from Source.Util.app_log import LogConfig
from Source.Views.mainwindow_ui import Ui_MainWindow
from Source.Controller.tab_dashboard import TabDashboard
from Source.Controller.tab_contacts import TabContacts
from Source.Controller.tab_income import TabIncome
from Source.Controller.tab_expenditure import TabExpenditure
from Source.Controller.tab_document import TabDocument
from Source.Controller.tab_export import TabExport
from Source.Controller.tab_settings import TabSettings
from Source.Controller.help_dialog import create_help_dialog
from Source.Controller.dialog_about import AboutDialog
from Source.Controller.dialog_commit import CommitDialog
from Source.Controller.dialog_receipt import ReceiptDialog
from Source.Model.model import Model
from Source.Model.data_handler import check_git_changes, commit_all_changes
from Source.Model.update_service import get_tool_update_status, is_newer_version
from Source.Worker.update_downloader import delete_temp_update_files

log = logging.getLogger(__title__)

STATUS_TEXT_TIME = 3000
STATUS_HIGHLIGHT_TEXT_TIME = 5000
STATUS_WARNING_TEXT_TIME = 15000

DEFAULT_STYLE = "transparent"
WARNING_STYLE = "orange"
WARNING_STYLE_DARK = "darkorange"
HIGHLIGHT_STYLE = "red"
LOCKED_STYLE = "grey"


class MainWindow(QMainWindow, Ui_MainWindow):
    """!
    @brief The view-controller for main window. Entry point of application.
           Provides general methods that may be called by any other controller.
    @param qt_exception_hook : global exception hook for crash handling.
    @param log_config : log configuration of the application.
    """

    def __init__(self, qt_exception_hook: UncaughtHook, log_config: LogConfig, *args: Any, **kwargs: Any) -> None:  # pylint: disable=keyword-arg-before-vararg
        log.debug("Initializing Main Window")
        super().__init__(*args, **kwargs)
        self.qt_exception_hook = qt_exception_hook
        self.gui_locked = False
        self.init_phase = True
        self.warning_active = False
        self.setupUi(self)
        self.setWindowTitle(__title__)
        self.dialog_help = create_help_dialog(self)

        # Init settings
        log.debug("Initializing main configuration")

        self.model = Model(self, log_config)
        log_config.ui = self
        self.model.monitor.apply_theme(self.model.monitor.selected_theme)

        self.status_timer = QTimer(self)  # statusbar timer
        self.status_timer.setSingleShot(True)
        self.status_timer.timeout.connect(self.clear_status)

        # Action Group Log Verbosity
        menu_action = self.menu_log_verbosity.menuAction()
        if menu_action is not None:
            menu_action.setVisible(False)

        # Action Group theme
        self.ag_theme = group_menu(self,
                                   [self.action_light, self.action_dark, self.action_system],
                                   self.model.monitor.selected_theme,
                                   [ETheme.LIGHT, ETheme.DARK, ETheme.SYSTEM])

        # Dark Mode
        self.action_light.triggered.connect(lambda: self.model.monitor.apply_theme(ETheme.LIGHT))
        self.action_dark.triggered.connect(lambda: self.model.monitor.apply_theme(ETheme.DARK))
        self.action_normal.setVisible(False)
        self.action_system.triggered.connect(lambda: self.model.monitor.apply_theme(ETheme.SYSTEM))
        # help
        self.action_help.triggered.connect(self.show_help_dialog)
        self.action_about_app.triggered.connect(lambda: AboutDialog(self))
        self.action_support.triggered.connect(lambda: webbrowser.open(__issue__))

        # Set tabs
        self.tab_settings = TabSettings(self, ETab.SETTINGS)  # call settings first -> used in other tabs
        self.tab_dashboard = TabDashboard(self, ETab.DASHBOARD)
        self.tab_contacts = TabContacts(self, ETab.CONTACTS)
        self.tab_income = TabIncome(self, ETab.INCOME)
        self.tab_expenditure = TabExpenditure(self, ETab.EXPENDITURE)
        self.tab_document = TabDocument(self, ETab.DOCUMENT)
        self.tab_export = TabExport(self, ETab.EXPORT)

        ReceiptDialog(self)  # init without show dialog to pre-load resources

        # active tab
        self.tabWidget.setCurrentIndex(read_last_tab())

        # handle update
        if not BUILD_NAME:
            delete_temp_update_files()

            newer_tool_version = get_tool_update_status()
            # show newer version if present and not hidden before
            if newer_tool_version and (is_newer_version(read_update_version(), newer_tool_version)):
                self.lbl_update_banner.setText("Neue Version verfügbar!")
                self.btn_update.setText(f"Update auf Version {newer_tool_version} durchführen")
                self.btn_close_update_banner.clicked.connect(lambda: self.close_update_banner_clicked(newer_tool_version))
                self.btn_update.clicked.connect(self.update_btn_clicked)
            else:
                self.frame_update_banner.setVisible(False)
        else:
            self.frame_update_banner.setVisible(False)

        self.clear_status(override=True)
        self.init_phase = False
        self.update_all_tabs()  # call at least for log

    def update_btn_clicked(self) -> None:
        """!
        @brief Handles the Update button click and starts the update dialog.
        """
        self.frame_update_banner.setVisible(False)
        AboutDialog(self, auto_update=True)

    def close_update_banner_clicked(self, newer_tool_version: str) -> None:
        """!
        @brief Hides the update banner and stores the newer tool version.
        @param newer_tool_version : Latest available tool version
        """
        write_update_version(newer_tool_version)  # write newest version for don't remember again
        self.frame_update_banner.setVisible(False)

    def update_all_tabs(self, update: bool = False, rename: bool = False) -> None:
        """!
        @brief Updates the data displayed in all tabs.
        @param update : update status of JSON file
        @param rename : rename status of file name
        """
        update_dashboard = False  # update only one time after all tables set to prevent multiple errors
        self.tab_contacts.set_table_data(update=update, rename=rename, update_dashboard=update_dashboard)
        self.tab_income.set_table_data(update=update, rename=rename, update_dashboard=update_dashboard)
        self.tab_expenditure.set_table_data(update=update, rename=rename, update_dashboard=update_dashboard)
        self.tab_document.set_table_data(update=update, rename=rename, update_dashboard=update_dashboard)
        self.tab_dashboard.check_data()
        self.tab_dashboard.update_dashboard_data()

    def closeEvent(self, event: QCloseEvent | None) -> None:  # pylint: disable=invalid-name
        """!
        @brief Handles application shutdown and triggers optional auto-commit.
        @param event : Close event
        """
        log.debug("Close Event")
        write_last_tab(self.tabWidget.currentIndex())
        write_window_state(self.saveGeometry(), self.saveState())
        self.tab_export.tools_downloader.requestInterruption()
        has_changes, changes_summary = check_git_changes()
        if has_changes:
            commit_dialog = CommitDialog(self, changes_summary)
            if commit_dialog.is_commit:
                commit_all_changes(commit_dialog.commit_message)
        if event is not None:
            event.accept()

    def set_ui(self, enabled: bool) -> None:
        """!
        @brief Enables or disables the main UI controls.
        @param enabled : True to enable, False to disable.
        """
        self.menu_settings.setEnabled(enabled)
        self.menu_help.setEnabled(enabled)
        self.tabWidget.setEnabled(enabled)

    def block_ui(self) -> None:
        """!
        @brief Disables the main UI to prevent user interaction.
        """
        log.debug("Block UI")
        self.set_ui(False)
        self.gui_locked = True
        self.set_status("")

    def unblock_ui(self) -> None:
        """!
        @brief Re-enables the main UI after a blocking operation finishes.
        """
        log.debug("Unblock UI")
        self.set_ui(True)
        self.gui_locked = False
        self.status_timer.stop()  # stop timer to deactivate unlock diagnostic directly after clear status
        self.clear_status()

    def show_help_dialog(self) -> None:
        """!
        @brief Opens the application help dialog.
        """
        log.debug("Starting help dialog")
        icon = ICON_HELP_LIGHT if self.model.monitor.is_light_theme() else ICON_HELP_DARK
        self.dialog_help.setWindowTitle("Hilfe")
        self.dialog_help.setWindowIcon(QIcon(icon))
        self.dialog_help.show()

    def set_status(self, text: str, warning: bool = False, timeout: int | None = None, highlight: bool = False) -> None:
        """!
        @brief Displays a status message and logs it, optionally highlighted or timed.
        @param text : Text to set.
        @param warning : True for warning, False for normal info.
        @param highlight : True for highlighted text, False for normal text.
        @param timeout : Timeout for status text in ms. If None use default time.
        """
        if warning:
            log.warning(text)
        else:
            log.info(text)

        if self.gui_locked:
            self.statusbar.showMessage("Das Fenster ist gesperrt!")
            self.statusbar.setStyleSheet(f"background-color: {LOCKED_STYLE};")
        else:
            if warning or not self.warning_active:
                if hasattr(self, "status_timer"):
                    if timeout is None:
                        if warning:
                            timeout = STATUS_WARNING_TEXT_TIME
                        else:
                            timeout = STATUS_HIGHLIGHT_TEXT_TIME if highlight else STATUS_TEXT_TIME
                    self.status_timer.start(timeout)
                if warning:
                    foreground = None
                    background = WARNING_STYLE if self.model.monitor.is_light_theme() else WARNING_STYLE_DARK
                    self.warning_active = True
                else:
                    foreground = HIGHLIGHT_STYLE if highlight else None
                    background = DEFAULT_STYLE
                    self.warning_active = False
                self.statusbar.showMessage(text)
                style_parts = []
                if background is not None:
                    style_parts.append(f"background-color: {background};")
                if foreground is not None:
                    style_parts.append(f"color: {foreground};")
                self.statusbar.setStyleSheet(" ".join(style_parts))

    def clear_status(self, override: bool = False) -> None:
        """!
        @brief Clears the current status bar message unless a warning is active.
        @param override : True to force clearing even if a message is active.
        """
        if not self.gui_locked:
            if not self.status_timer.isActive() or (override and not self.warning_active):
                self.statusbar.showMessage("")
                self.statusbar.setStyleSheet(f"background-color: {DEFAULT_STYLE};")
                self.warning_active = False
