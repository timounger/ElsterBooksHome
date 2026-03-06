"""!
********************************************************************************
@file   monitor.py
@brief  Handle window scaling, theme management, and UI state persistence.
********************************************************************************
"""

import logging
from typing import TYPE_CHECKING
import qdarktheme
import darkdetect

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QDialog  # pylint: disable=unused-import

from Source.version import __title__
from Source.Util.app_data import ETheme, DEFAULT_WIN_WIDTH, DEFAULT_WIN_HEIGHT, read_window_state, write_window_state, \
    read_theme_settings, write_theme_settings, ICON_THEME_LIGHT, ICON_THEME_DARK, ICON_HELP_LIGHT, ICON_HELP_DARK, ICON_APP, \
    ICON_GITHUB_LIGHT, ICON_GITHUB_DARK
if TYPE_CHECKING:
    from Source.Controller.main_window import MainWindow

log = logging.getLogger(__title__)


class MonitorScale:
    """!
    @brief Class to scale text and item positions.
    @param ui : main window object.
    """

    def __init__(self, ui: "MainWindow") -> None:
        self.ui = ui
        self.ui.setMinimumWidth(DEFAULT_WIN_WIDTH)
        self.ui.setMinimumHeight(DEFAULT_WIN_HEIGHT)
        # window geometry and state
        geometry, state = read_window_state()
        if (geometry is not None) and (state is not None):
            self.ui.restoreGeometry(geometry)
            self.ui.restoreState(state)
        else:
            write_window_state(self.ui.saveGeometry(), self.ui.saveState())
        # Theme
        self.selected_theme = read_theme_settings()
        log.debug("Select Theme: %s", self.selected_theme)
        self.active_theme = ETheme.LIGHT
        self.resolve_active_theme(self.selected_theme)
        self.update_icons(update_all=True)  # force update icons

    def resolve_active_theme(self, selected_theme: ETheme | None = None) -> None:
        """!
        @brief Resolve selected theme to active theme.
        @param selected_theme : theme enum to resolve (AUTO/SYSTEM are mapped to LIGHT/DARK)
        """
        if selected_theme is None:
            selected_theme = self.selected_theme
        previous_theme = self.active_theme
        match selected_theme:
            case ETheme.LIGHT:
                self.active_theme = ETheme.LIGHT
            case ETheme.DARK:
                self.active_theme = ETheme.DARK
            case ETheme.CLASSIC:
                self.active_theme = ETheme.CLASSIC
            case ETheme.SYSTEM:
                self.active_theme = ETheme.LIGHT if darkdetect.isLight() else ETheme.DARK
            case _:
                self.ui.set_status(f"Invalid theme change: {selected_theme}", True)  # state not possible
        if previous_theme != self.active_theme:
            self.update_icons()
            self.apply_dialog_theme(self.ui, update_dashboard=True)

    def apply_theme(self, selected_theme: ETheme) -> None:
        """!
        @brief Apply the selected theme and persist the setting.
        @param selected_theme : theme mode to set.
        """
        self.selected_theme = selected_theme
        write_theme_settings(self.selected_theme)
        self.resolve_active_theme(self.selected_theme)
        self.show_theme_status()

    def show_theme_status(self) -> None:
        """!
        @brief Show status message for the active theme.
        """
        match self.selected_theme:
            case ETheme.LIGHT:
                self.ui.set_status("Heller Modus aktiviert")
            case ETheme.DARK:
                self.ui.set_status("Dunkler Modus aktiviert")
            case ETheme.CLASSIC:
                pass
            case ETheme.SYSTEM:
                self.ui.set_status("System Standard Modus aktiviert")
            case _:
                self.ui.set_status(f"Invalid theme setting: {self.selected_theme}", True)  # state not possible

    def apply_dialog_theme(self, dialog: "QDialog | MainWindow", update_dashboard: bool = False) -> None:
        """!
        @brief Apply the active theme stylesheet to a dialog or window.
        @param dialog : Dialog or window to apply the theme to.
        @param update_dashboard : Whether to also refresh the dashboard charts.
        """
        match self.active_theme:
            case ETheme.LIGHT:
                dialog.setStyleSheet(qdarktheme.load_stylesheet("light", corner_shape="rounded"))
            case ETheme.DARK:
                dialog.setStyleSheet(qdarktheme.load_stylesheet("dark", corner_shape="rounded"))
            case ETheme.CLASSIC:
                self.ui.set_status(f"Invalid actual theme: {self.active_theme}", True)  # state not possible
            case _:
                self.ui.set_status(f"Invalid actual theme: {self.active_theme}", True)  # state not possible
        if not self.ui.init_phase and update_dashboard:  # tabs only after init phase available
            self.ui.update_all_tabs()

    def is_light_theme(self) -> bool:
        """!
        @brief Check if active theme is light.
        @return True if active theme is light
        """
        return self.active_theme != ETheme.DARK

    def update_icons(self, update_all: bool = False) -> None:
        """!
        @brief Update icons based on active theme.
        @param update_all : [True] include theme-independent icons; [False] only theme-dependent icons
        """
        is_light = self.is_light_theme()
        self.ui.menu_style.setIcon(QIcon(ICON_THEME_LIGHT if is_light else ICON_THEME_DARK))
        self.ui.action_help.setIcon(QIcon(ICON_HELP_LIGHT if is_light else ICON_HELP_DARK))
        if update_all:
            self.ui.action_about_app.setIcon(QIcon(ICON_APP))
        self.ui.action_support.setIcon(QIcon(ICON_GITHUB_LIGHT if is_light else ICON_GITHUB_DARK))
        if is_light:
            self.ui.frame_update_banner.setStyleSheet("background-color: #ffffaf")
            self.ui.btn_update.setStyleSheet("color: blue")
        else:
            self.ui.frame_update_banner.setStyleSheet("background-color: #EBBC4E")
            self.ui.lbl_update_banner.setStyleSheet("color: black")
            self.ui.btn_update.setStyleSheet("color: darkblue")
            self.ui.btn_close_update_banner.setStyleSheet("background: transparent; border: none; color: black")
