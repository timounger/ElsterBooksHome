import typing
from PyQt6 import QtCore
from PyQt6.QtWidgets import QToolButton, QWidget
from PyQt6.QtGui import QAction

class CustomToolButton(QToolButton):
    def __init__(self, parent: typing.Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.triggered.connect(self.set_recent_action_as_default)

    def set_recent_action_as_default(self, action: QAction) -> None:
        icon = self.icon()
        self.setDefaultAction(action)
        self.setIcon(icon)
