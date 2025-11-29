"""!
********************************************************************************
@file   dialog_about.py
@brief  Create about dialog
********************************************************************************
"""

import sys
import logging
from typing import TYPE_CHECKING, Any, Optional
import markdown

from PyQt6.QtGui import QIcon, QPixmap, QPainter, QTransform, QCloseEvent
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtSvg import QSvgRenderer

from Source.version import __title__, __description__, __version__, __website__, __copyright__, __license__, GIT_SHORT_SHA, BUILD_NAME
from Source.Util.app_data import ICON_APP, ICON_UPDATE_LIGHT, ICON_UPDATE_DARK, ICON_TICK_GREEN, ICON_CROSS_RED, thread_dialog, \
    ICON_LICENSE_LIGHT, ICON_LICENSE_DARK, LICENSE_FILE
from Source.Views.dialogs.dialog_about_ui import Ui_AboutDialog
from Source.Model.update_service import get_tool_update_status
from Source.Worker.update_downloader import UpdateDownloader, generate_and_start_updater_script
if TYPE_CHECKING:
    from Source.Controller.main_window import MainWindow

log = logging.getLogger(__title__)


class LicenseDialog(QDialog):
    """!
    @brief License dialog.
    @param ui : main window
    """

    def __init__(self, ui: "MainWindow", *args: Any, **kwargs: Any) -> None:
        super().__init__(parent=ui, *args, **kwargs)  # type: ignore
        self.resize(600, 400)
        self.setWindowTitle("Lizenz")
        layout = QVBoxLayout(self)
        te_text = QTextEdit(self)
        te_text.setReadOnly(True)
        with open(LICENSE_FILE, mode="r", encoding="utf-8") as f:
            text = f.read()
            text = text[text.find("#"):]
            te_text.setHtml(markdown.markdown(text))
        layout.addWidget(te_text)
        thread_dialog(self)

    def show_dialog(self) -> None:
        """!
        @brief Show dialog
        """
        self.show()
        self.exec()


class AboutDialog(QDialog, Ui_AboutDialog):
    """!
    @brief About dialog.
    @param ui : main window
    @param auto_update : start update direct
    """

    def __init__(self, ui: "MainWindow", auto_update: bool = False, *args: Any, **kwargs: Any) -> None:
        super().__init__(parent=ui, *args, **kwargs)  # type: ignore
        self.setupUi(self)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        self.setWindowFlag(Qt.WindowType.WindowMinMaxButtonsHint, False)
        self.ui = ui
        self.auto_update = auto_update

        self.b_download_finished = False
        self.angle = 0
        self.timer = QTimer(self.lbl_update_icon)
        self.timer.timeout.connect(self.rotate)

        self.update_downloader = UpdateDownloader()
        self.update_downloader.status_signal.connect(self.download_update_status)
        self.update_downloader.finish_signal.connect(self.download_update_finish)

        thread_dialog(self)

    def show_dialog(self) -> None:
        """!
        @brief Show dialog
        """
        log.debug("Starting About dialog")

        self.ui.model.c_monitor.set_dialog_style(self)

        self.lbl_productName.setText(__title__)
        self.lbl_productDescription.setText(__description__)

        btn_text = ""
        lbl_text = ""
        icon = ""
        newer_tool_version = get_tool_update_status()
        if newer_tool_version is not None:
            if newer_tool_version:
                btn_text = f"Update auf Version {newer_tool_version} durchführen"
                self.update_downloader.latest_version = newer_tool_version
            else:
                lbl_text = f"{__title__} ist aktuell"
                icon = ICON_TICK_GREEN
        else:
            lbl_text = "Die Versionsaktualität konnte nicht überprüft werden."
            icon = ICON_CROSS_RED

        # buttons
        self.btn_update.clicked.connect(self.update_btn_clicked)
        if not btn_text:
            self.btn_update.hide()
        self.btn_update.setText(btn_text)
        # icon
        if icon:
            self.lbl_update_icon.setPixmap(QPixmap(icon))
        else:
            self.lbl_update_icon.hide()
        # label
        if not lbl_text:
            self.lbl_update_status.hide()
        self.lbl_update_status.setText(lbl_text)

        if self.auto_update:
            self.update_btn_clicked()

        # Version info text
        version_info = f"Version: {__version__}"
        version_info += "  Prerelease Build"
        self.lbl_version.setStyleSheet("color: orange;")
        license_text = __license__
        home_link = f"Home: <a href=\"{__website__}\">{__website__}</a>"
        if GIT_SHORT_SHA is not None:
            version_info += f"\nGit SHA: {GIT_SHORT_SHA}"
        if BUILD_NAME:
            version_info += f'\nonly for "{BUILD_NAME}"'
        self.lbl_version.setText(version_info)
        self.lbl_copyright.setText(__copyright__)
        self.lbl_license.setText(license_text)
        self.btn_license.setIcon(QIcon(ICON_LICENSE_LIGHT if self.ui.model.c_monitor.is_light_theme() else ICON_LICENSE_DARK))
        self.btn_license.clicked.connect(lambda: LicenseDialog(self.ui))
        self.lbl_home.setText(home_link)
        self.lbl_home.setOpenExternalLinks(True)
        self.imagePlaceholder.setPixmap(QPixmap(ICON_APP))
        self.setWindowTitle(f"Über {__title__}")
        self.setWindowIcon(QIcon(ICON_APP))

        self.show()
        self.exec()

    def update_btn_clicked(self) -> None:
        """!
        @brief Update button clicked
        """
        if not self.b_download_finished:
            if self.timer.isActive():
                self.timer.stop()
            # buttons
            self.btn_update.hide()
            # icon
            container_size = 48  # slightly larger than your icon, space for rotation
            icon_size = 32  # Original size of the SVG
            b_light_theme = self.ui.model.c_monitor.is_light_theme()
            renderer = QSvgRenderer(ICON_UPDATE_LIGHT if b_light_theme else ICON_UPDATE_DARK)
            pixmap = QPixmap(container_size, container_size)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            offset = (container_size - icon_size) / 2
            renderer.render(painter, QRectF(offset, offset, icon_size, icon_size))  # Draw SVG centered
            painter.end()
            self.lbl_update_icon.show()
            self.lbl_update_icon.setPixmap(pixmap)
            self.lbl_update_icon.setFixedSize(container_size, container_size)
            self.lbl_update_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.lbl_update_icon._original_pixmap = pixmap  # Save original for rotation
            # label
            self.lbl_update_status.show()
            lbl_text = "Update wird heruntergeladen"
            self.lbl_update_status.setText(lbl_text)

            self.start_label_rotation()
            self.update_downloader.start()
        else:
            generate_and_start_updater_script()
            sys.exit()

    def rotate(self) -> None:
        """!
        @brief Rotate update icon
        """
        original = self.lbl_update_icon._original_pixmap
        size = original.width()
        rotated_pixmap = QPixmap(size, size)
        rotated_pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(rotated_pixmap)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        transform = QTransform()
        transform.translate(size / 2, size / 2)
        transform.rotate(self.angle)
        transform.translate(-size / 2, -size / 2)

        painter.setTransform(transform)
        painter.drawPixmap(0, 0, original)
        painter.end()

        step_deg = 5
        self.lbl_update_icon.setPixmap(rotated_pixmap)
        self.angle = (self.angle + step_deg) % 360

    def start_label_rotation(self) -> None:
        """!
        @brief Start rotation
        """
        speed_ms = 25
        self.timer.start(speed_ms)

    def stop_label_rotation(self) -> None:
        """!
        @brief Stop rotation
        """
        self.timer.stop()

    def download_update_status(self, text: str) -> None:
        """!
        @brief Update download status
        @param text : update process status text
        """
        self.lbl_update_status.setText(f"Update wird heruntergeladen - {text}")

    def download_update_finish(self, success_status: bool) -> None:
        """!
        @brief Download update finished
        @param success_status : success status of download
        """
        if self.timer.isActive():
            self.timer.stop()
        if success_status:
            # buttons
            self.btn_update.show()
            self.btn_update.setText(f"Zum Abschließen des Updates hier klicken!\n{__title__} muss anschließend manuell gestartet werden.")
            # icon
            self.lbl_update_icon.hide()
            # label
            self.lbl_update_status.hide()
            self.b_download_finished = True
        else:
            # buttons
            self.btn_update.show()
            self.btn_update.setText("Update wiederholen")
            # icon
            self.lbl_update_icon.show()
            self.lbl_update_icon.setPixmap(QPixmap(ICON_CROSS_RED))
            # label
            self.lbl_update_status.show()
            self.lbl_update_status.setText("Update fehlgeschlagen")

    def closeEvent(self, event: Optional[QCloseEvent]) -> None:  # pylint: disable=invalid-name
        """!
        @brief Default close Event Method to handle application close
        @param event : arrived event
        """
        self.update_downloader.terminate()
        if event is not None:
            event.accept()
