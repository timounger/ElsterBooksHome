"""!
********************************************************************************
@file   monitor.py
@brief  handle windows size and scale factor and update items
********************************************************************************
"""

import logging
from typing import Optional, TYPE_CHECKING
import qdarktheme
import darkdetect

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QDialog  # pylint: disable=unused-import

from Source.version import __title__
from Source.Util.app_data import ETheme, I_DEFAULT_WIN_WIDTH, I_DEFAULT_WIN_HEIGHT, read_window_state, save_window_state, \
    read_theme_settings, write_theme_settings, ICON_THEME_LIGHT, ICON_THEME_DARK, ICON_HELP_LIGHT, ICON_HELP_DARK, ICON_APP, \
    ICON_GITHUB_LIGHT, ICON_GITHUB_DARK
if TYPE_CHECKING:
    from Source.Controller.main_window import MainWindow

log = logging.getLogger(__title__)


class MonitorScale:
    """!
    @brief Class to scale text and item positions.
    @param ui : main window object
    """

    def __init__(self, ui: "MainWindow") -> None:
        self.ui = ui
        self.ui.setMinimumWidth(I_DEFAULT_WIN_WIDTH)
        self.ui.setMinimumHeight(I_DEFAULT_WIN_HEIGHT)
        # window geometry and state
        o_geometry, o_state = read_window_state()
        if (o_geometry is not None) and (o_state is not None):
            self.ui.restoreGeometry(o_geometry)
            self.ui.restoreState(o_state)
        else:
            save_window_state(self.ui.saveGeometry(), self.ui.saveState())
        # Theme
        self.e_style = read_theme_settings()
        log.debug("Select Theme: %s", self.e_style)
        self.e_actual_theme = ETheme.LIGHT
        self.check_for_style_change(self.e_style)

    def check_for_style_change(self, e_style: Optional[ETheme] = None) -> None:
        """!
        @brief Check for style change
        @param e_style : style to set
        """
        if e_style is None:
            e_style = self.e_style
        old_style = self.e_actual_theme
        match e_style:
            case ETheme.LIGHT:
                self.e_actual_theme = ETheme.LIGHT
            case ETheme.DARK:
                self.e_actual_theme = ETheme.DARK
            case ETheme.CLASSIC:
                self.e_actual_theme = ETheme.CLASSIC
            case ETheme.SYSTEM:
                self.e_actual_theme = ETheme.LIGHT if darkdetect.isLight() else ETheme.DARK
            case _:
                self.ui.set_status(f"Invalid theme change: {e_style}", True)  # state not possible
        if old_style != self.e_actual_theme:
            self.update_icons()
            self.set_dialog_style(self.ui, update_dashboard=True)

    def update_darkmode_status(self, e_style: ETheme) -> None:
        """!
        @brief Update dark mode status.
        @param e_style : select theme mode
        """
        self.e_style = e_style
        write_theme_settings(self.e_style)
        self.check_for_style_change(self.e_style)
        self.set_dialog_style(self.ui, update_dashboard=True)
        self.set_change_theme_status()
        self.update_icons()

    def set_change_theme_status(self) -> None:
        """!
        @brief Set dialog theme style.
        """
        match self.e_style:
            case ETheme.LIGHT:
                self.ui.set_status("Heller Modus aktiviert")
            case ETheme.DARK:
                self.ui.set_status("Dunkler Modus aktiviert")
            case ETheme.CLASSIC:
                pass
            case ETheme.SYSTEM:
                self.ui.set_status("System Standard Modus aktiviert")
            case _:
                self.ui.set_status(f"Invalid theme setting: {self.e_style}", True)  # state not possible

    def set_dialog_style(self, dialog: "QDialog | MainWindow", update_dashboard: bool = False) -> None:
        """!
        @brief Set dialog theme style.
        @param dialog : set style to this dialog
        @param update_dashboard : update dashboard
        """
        match self.e_actual_theme:
            case ETheme.LIGHT:
                dialog.setStyleSheet(qdarktheme.load_stylesheet("light", corner_shape="rounded"))
            case ETheme.DARK:
                dialog.setStyleSheet(qdarktheme.load_stylesheet("dark", corner_shape="rounded"))
            case ETheme.CLASSIC:
                pass
            case _:
                self.ui.set_status(f"Invalid actual theme: {self.e_actual_theme}", True)  # state not possible
        if not self.ui.init_phase and update_dashboard:  # tabs only after init phase available
            self.ui.update_all_tabs()

    def is_light_theme(self) -> bool:
        """!
        @brief get status for active light theme (or classic -> not dark).
        @return status if theme is light
        """
        light_status = bool(self.e_actual_theme != ETheme.DARK)
        return light_status

    def update_icons(self) -> None:
        """!
        @brief Update icons to change between light and dark items depend on theme state.
        """
        b_light_theme = self.is_light_theme()
        self.ui.menu_style.setIcon(QIcon(ICON_THEME_LIGHT if b_light_theme else ICON_THEME_DARK))
        self.ui.action_help.setIcon(QIcon(ICON_HELP_LIGHT if b_light_theme else ICON_HELP_DARK))
        self.ui.action_about_app.setIcon(QIcon(ICON_APP))
        self.ui.action_support.setIcon(QIcon(ICON_GITHUB_LIGHT if b_light_theme else ICON_GITHUB_DARK))
