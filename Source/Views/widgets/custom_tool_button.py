"""!
********************************************************************************
@file   custom_tool_button.py
@brief  QToolButton with menu that updates default action on selection
********************************************************************************
"""

from PyQt6 import QtCore
from PyQt6.QtWidgets import QToolButton, QWidget
from PyQt6.QtGui import QAction


class CustomToolButton(QToolButton):
    """!
    @brief QToolButton with dropdown menu that sets the most recently triggered action as the new default
    @param parent : parent widget
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.triggered.connect(self.set_recent_action_as_default)

    def set_recent_action_as_default(self, action: QAction) -> None:
        """!
        @brief Set the triggered action as the default button action while preserving the original icon
        @param action : triggered action
        """
        icon = self.icon()
        self.setDefaultAction(action)
        self.setIcon(icon)
