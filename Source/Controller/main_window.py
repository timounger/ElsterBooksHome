"""!
********************************************************************************
@file   main_window.py
@brief  View controller for the main window
********************************************************************************
"""

import sys
import logging
from typing import Optional, Any
import webbrowser

from PyQt6.QtGui import QIcon, QStatusTipEvent, QCloseEvent, QResizeEvent
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QApplication, QCheckBox
from PyQt6.QtCore import QObject, pyqtSignal, QEvent, QTimer

from Source.version import __title__, __issue__
from Source.Util.app_data import save_window_state, ICON_APP, ETab, group_menu, \
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
from Source.Controller.dialog_about import show_about_dialog
from Source.Controller.dialog_commit import CommitDialog
from Source.Model.model import Model
from Source.Model.data_handler import check_git_changes, commit_all_changes
from Source.Model.update_service import get_tool_update_status, compare_versions, S_UPDATE_URL

log = logging.getLogger(__title__)

STATUS_TEXT_TIME = 3000
STATUS_HIGHLIGHT_TEXT_TIME = 5000
STATUS_WARNING_TEXT_TIME = 15000

DEFAULT_STYLE = "None"
WARNING_STYLE = "orange"
WARNING_STYLE_DARK = "darkorange"
HIGHLIGHT_STYLE = "red"
LOCKED_STYLE = "grey"


class StatusTipFilter(QObject):
    """!
    @brief Event Filter.
    """

    def eventFilter(self, watched: Optional[QObject], event: Optional[QEvent]) -> bool:  # pylint: disable=invalid-name
        """!
        @brief Filter to prevent tip event (statusbar message no longer disappears on menu hover).
        @param watched : object
        @param event : arrived event
        @return return event filter
        """
        if isinstance(event, QStatusTipEvent):
            b_return = True
        else:
            b_return = super().eventFilter(watched, event)
        return b_return


class MainWindow(QMainWindow, Ui_MainWindow):
    """!
    @brief The view-controller for main window. Entry point of application.
           Provides general methods that may be called by any other controller.
    @param qt_exception_hook : exception hook
    @param log_config : log configuration of the application
    """
    resized = pyqtSignal()  # need to defined out of scope

    def __init__(self, qt_exception_hook: UncaughtHook, log_config: LogConfig, *args: Any, **kwargs: Any) -> None:  # pylint: disable=keyword-arg-before-vararg
        log.debug("Initializing Main Window")
        super().__init__(*args, **kwargs)
        self.qt_exception_hook = qt_exception_hook
        self.gui_locked = False
        self.init_phase = True
        self.b_warning_active = False
        self.setupUi(self)
        self.setWindowTitle(__title__)
        self.dialog_help = create_help_dialog(self)

        # Init settings
        log.debug("Initializing main configuration")

        self.model = Model(self, log_config)
        log_config.ui = self

        self.model.c_monitor.update_darkmode_status(self.model.c_monitor.e_style)

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
                                   self.model.c_monitor.e_style,
                                   [ETheme.LIGHT, ETheme.DARK, ETheme.SYSTEM])

        # Dark Mode
        self.action_light.triggered.connect(lambda: self.model.c_monitor.update_darkmode_status(ETheme.LIGHT))
        self.action_dark.triggered.connect(lambda: self.model.c_monitor.update_darkmode_status(ETheme.DARK))
        self.action_normal.setVisible(False)
        self.action_system.triggered.connect(lambda: self.model.c_monitor.update_darkmode_status(ETheme.SYSTEM))
        # help
        self.action_help.triggered.connect(self.show_help_dialog)
        self.action_about_app.triggered.connect(lambda: show_about_dialog(self))
        self.action_support.triggered.connect(lambda: webbrowser.open(__issue__))

        self.menubar.installEventFilter(StatusTipFilter(self))

        # Set tabs
        self.tab_settings = TabSettings(self, ETab.SETTINGS)  # call settings first -> used in other tabs
        self.tab_dashboard = TabDashboard(self, ETab.DASHBOARD)
        self.tab_contacts = TabContacts(self, ETab.CONTACTS)
        self.tab_income = TabIncome(self, ETab.INCOME)
        self.tab_expenditure = TabExpenditure(self, ETab.EXPENDITURE)
        self.tab_document = TabDocument(self, ETab.DOCUMENT)
        self.tab_export = TabExport(self, ETab.EXPORT)

        # active tab
        self.tabWidget.setCurrentIndex(read_last_tab())

        newer_tool_version = get_tool_update_status()
        if (newer_tool_version is not None) and (compare_versions(read_update_version(), newer_tool_version)):
            self.show_update_dialog(newer_tool_version)
        self.clear_status(b_override=True)
        self.init_phase = False
        self.update_all_tabs()  # call at least for log

    def update_all_tabs(self, update: bool = False, rename: bool = False) -> None:
        """!
        @brief Update all tabs
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

    def resizeEvent(self, _event: Optional[QResizeEvent]) -> None:
        """!
        @brief Default resize Event Method to handle change of window size
        @param _event : arrived event
        """
        self.resized.emit()

    def closeEvent(self, event: Optional[QCloseEvent]) -> None:  # pylint: disable=invalid-name
        """!
        @brief Default close Event Method to handle application close
        @param event : arrived event
        """
        log.debug("Close Event")
        write_last_tab(self.tabWidget.currentIndex())
        save_window_state(self.saveGeometry(), self.saveState())
        self.tab_export.tools_downloader.terminate()
        b_changes, s_changes = check_git_changes()
        if b_changes:
            commit_dialog = CommitDialog(self, s_changes)
            if commit_dialog.b_commit:
                commit_all_changes(commit_dialog.commit_message)
        if event is not None:
            event.accept()

    def confirm_dialog(self, s_title: str, s_text: str) -> bool:
        """!
        @brief Show confirm dialog to accept with yes or no.
        @param s_title : title
        @param s_text : text
        @return return accept status
        """
        dialog = QMessageBox(self)
        dialog.setWindowTitle(s_title)
        dialog.setWindowIcon(QIcon(ICON_APP))
        dialog.setText(s_text)
        dialog.addButton(QMessageBox.StandardButton.Yes)
        btn_yes = dialog.button(QMessageBox.StandardButton.Yes)
        if btn_yes is not None:
            btn_yes.setText("Ja")
        dialog.addButton(QMessageBox.StandardButton.No)
        btn_no = dialog.button(QMessageBox.StandardButton.No)
        if btn_no is not None:
            btn_no.setText("Nein")
        dialog.close()
        choice = dialog.exec()
        b_accept = choice not in [QMessageBox.StandardButton.No]
        return b_accept

    def set_ui(self, b_state: bool) -> None:
        """!
        @brief Blocks/Unblock the main UI elements.
        @param b_state : state if UI should blocked or unblocked, True: Enable, False: Disable
        """
        self.menu_settings.setEnabled(b_state)
        self.menu_help.setEnabled(b_state)
        self.menu_help.setEnabled(b_state)

    def block_ui(self) -> None:
        """!
        @brief Blocks the main UI elements.
        """
        log.debug("Block UI")
        self.set_ui(False)
        self.gui_locked = True
        self.set_status("")

    def unblock_ui(self) -> None:
        """!
        @brief Unblock the main UI elements.
        """
        log.debug("Unblock UI")
        self.set_ui(True)
        self.gui_locked = False
        self.status_timer.stop()  # stop timer to deactivate unlock diagnostic directly after clear status
        self.clear_status()

    def show_update_dialog(self, newer_tool_version: str) -> None:
        """!
        @brief Show Update dialog.
        @param newer_tool_version : newest tool version
        """
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Update-Dienst")
        dialog.setWindowIcon(QIcon(ICON_APP))
        dialog.setText(f"Neue Version verfügbar! \nUpdate auf Version {newer_tool_version} durchführen?")
        dialog.setIcon(QMessageBox.Icon.Information)
        dialog.addButton(QMessageBox.StandardButton.Yes)
        btn = dialog.button(QMessageBox.StandardButton.Yes)
        if btn is not None:
            btn.setText("Ja")
        dialog.addButton(QMessageBox.StandardButton.No)
        btn = dialog.button(QMessageBox.StandardButton.No)
        if btn is not None:
            btn.setText("Nein")
        box = QCheckBox("Nicht mehr anzeigen")
        dialog.setCheckBox(box)
        dialog.close()
        choice = dialog.exec()
        is_checked = box.isChecked()
        b_update = choice not in [QMessageBox.StandardButton.No, QMessageBox.StandardButton.Close, QMessageBox.StandardButton.Cancel]

        if is_checked:
            write_update_version(newer_tool_version)  # write newest version for don't remember again
        if b_update:
            cb = QApplication.clipboard()
            if cb is not None:
                cb.clear()
                cb.setText(S_UPDATE_URL)
            webbrowser.open_new_tab(S_UPDATE_URL)
            sys.exit()  # exit application without close dialog

    def show_help_dialog(self) -> None:
        """!
        @brief Show help dialog.
        """
        log.debug("Starting help dialog")
        icon = ICON_HELP_LIGHT if self.model.c_monitor.is_light_theme() else ICON_HELP_DARK
        self.dialog_help.setWindowTitle("Hilfe")
        self.dialog_help.setWindowIcon(QIcon(icon))
        self.dialog_help.show()

    def set_status(self, text: str, b_warning: bool = False, i_timeout: Optional[int] = None, b_highlight: bool = False) -> None:
        """!
        @brief Logs a status message to status bar (with timer) and logging handler
        @param text : text to set
        @param b_warning : [True] Text is a warning; [False] normal info
        @param b_highlight : [True] highlight text; [False] normal text
        @param i_timeout : timeout for statustext in "ms". If None use default time
        """
        if b_warning:
            log.warning(text)
        else:
            log.info(text)

        if self.gui_locked:
            self.statusbar.showMessage("Das Fenster ist gesperrt!")
            self.statusbar.setStyleSheet(f"background-color: {LOCKED_STYLE};")
        else:
            if not (not b_warning and self.b_warning_active):
                if hasattr(self, "status_timer"):
                    if i_timeout is None:
                        if b_warning:
                            i_timeout = STATUS_WARNING_TEXT_TIME
                        else:
                            i_timeout = STATUS_HIGHLIGHT_TEXT_TIME if b_highlight else STATUS_TEXT_TIME
                    if i_timeout is None:
                        self.status_timer.stop()
                    else:
                        self.status_timer.start(i_timeout)
                if b_warning:
                    foreground = None
                    background = WARNING_STYLE if self.model.c_monitor.is_light_theme() else WARNING_STYLE_DARK
                    self.b_warning_active = True
                else:
                    foreground = HIGHLIGHT_STYLE if b_highlight else None
                    background = DEFAULT_STYLE
                    self.b_warning_active = False
                self.statusbar.showMessage(text)
                if background is not None:
                    self.statusbar.setStyleSheet(f"background-color: {background};")
                if foreground is not None:
                    self.statusbar.setStyleSheet(f"color: {foreground};")

    def clear_status(self, b_override: bool = False) -> None:
        """!
        @brief Logs a status message to status bar (with timer) and logging handler
        @param b_override : status if actual status should override
        """
        if not self.gui_locked:
            if not self.status_timer.isActive() or (b_override and not self.b_warning_active):
                s_user_text = ""
                self.statusbar.showMessage(s_user_text)
                self.statusbar.setStyleSheet(f"background-color: {DEFAULT_STYLE};")
                self.b_warning_active = False
