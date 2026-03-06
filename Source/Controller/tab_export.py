"""!
********************************************************************************
@file   tab_export.py
@brief  Tab for exporting reports, backups, and PDFs.
********************************************************************************
"""

import os
import logging
import subprocess
from datetime import datetime
import shutil
from pathlib import Path
from typing import TYPE_CHECKING
import fitz  # PyMuPDF

from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtWidgets import QFileDialog

from Source.version import __title__
from Source.Util.app_data import EXPORT_PATH, REL_PATH, open_explorer, GIT_IGNORE_FILE, CREATE_GIT_PATH, \
    ICON_OPEN_FOLDER_LIGHT, ICON_OPEN_FOLDER_DARK, ICON_GIT_COMMIT, ICON_GIT_PULL, ICON_GIT_PUSH, ICON_CREATE_REPO
from Source.Model.data_handler import PDF_FILE_TYPES, MONTH_NAMES, create_repo, check_git_changes, commit_all_changes, \
    PORTABLE_GIT_EXE, check_repo_exists, git_add, MONTHS_IN_YEAR
from Source.Model.company import LOGO_BRIEF_PATH, COMPANY_BOOKING_FIELD, COMPANY_DEFAULT_FIELD, ECompanyFields
from Source.Model.export import ExportReport, EReportType
from Source.Views.tabs.tab_export_ui import Ui_Export
from Source.Worker.tools_downloader import ToolsDownloader
from Source.Controller.dialog_commit import CommitDialog
from Source.Controller.dialog_banking import BankingDialog
if TYPE_CHECKING:
    from Source.Controller.main_window import MainWindow

log = logging.getLogger(__title__)

NO_SPEC = "Keine Angabe"
QUARTER_NAMES = ["I. Kalendervierteljahr", "II. Kalendervierteljahr", "III. Kalendervierteljahr", "IV. Kalendervierteljahr"]
PRE_TAX_DAY_LIMIT = 10


class TabExport:
    """!
    @brief Controller for the Export tab.
    @param ui : main window
    @param tab_idx : Index of this tab in the tab widget
    """

    def __init__(self, ui: "MainWindow", tab_idx: int) -> None:
        self.ui = ui
        title = "Export"
        tab = ui.tabWidget.widget(tab_idx)
        self.ui.tabWidget.setTabText(tab_idx, title)
        self.ui_export = Ui_Export()
        self.ui_export.setupUi(tab)
        self.ui_export.lbl_title.setText(title)
        # open folder button
        self.ui_export.btn_open_folder.setText("")
        # TODO Icon bei Themen wechseln updaten
        self.ui_export.btn_open_folder.setIcon(QIcon(ICON_OPEN_FOLDER_LIGHT if self.ui.model.monitor.is_light_theme() else ICON_OPEN_FOLDER_DARK))
        self.ui_export.btn_open_folder.clicked.connect(self.open_export_folder_btn_clicked)
        # tax buttons
        self.ui_export.btn_ust_pre.setText(EReportType.UST_PRE)
        self.ui_export.btn_ust_pre.clicked.connect(self.ust_pre_btn_clicked)
        self.ui_export.btn_ust.setText(EReportType.UST)
        self.ui_export.btn_ust.clicked.connect(self.ust_btn_clicked)
        self.update_eur_btn()
        self.ui_export.btn_eur.clicked.connect(self.eur_btn_clicked)
        self.ui_export.btn_datev.setText(EReportType.DATEV)
        self.ui_export.btn_datev.clicked.connect(self.datev_btn_clicked)
        self.ui_export.btn_homeoffice_flat.hide()
        self.ui_export.btn_travel_expenses.hide()
        # export buttons
        self.ui_export.btn_export.setText(EReportType.EXPORT_TOTAL)
        self.ui_export.btn_export.clicked.connect(self.export_btn_clicked)
        self.ui_export.btn_backup.clicked.connect(self.create_backup)
        # Transactions
        self.ui_export.btn_transactions.clicked.connect(self.transactions_btn_clicked)
        # PDF buttons
        self.ui_export.btn_pdf_combine.clicked.connect(self.pdf_combine_btn_clicked)
        # data update buttons
        self.ui_export.btn_update_data.clicked.connect(self.update_btn_clicked)
        self.ui_export.btn_update_data_rename.clicked.connect(self.update_all_btn_clicked)
        self.ui_export.btn_data_clean.clicked.connect(self.clean_data_clicked)
        # git buttons
        self.ui_export.btn_git_commit.setIcon(QIcon(ICON_GIT_COMMIT))
        self.ui_export.btn_git_push.setIcon(QIcon(ICON_GIT_PUSH))
        self.ui_export.btn_git_pull.setIcon(QIcon(ICON_GIT_PULL))
        self.ui_export.btn_git_create_repo.setIcon(QIcon(ICON_CREATE_REPO))
        self.ui_export.btn_git_commit.clicked.connect(self.git_commit_btn_clicked)
        self.ui_export.btn_git_push.clicked.connect(self.git_push_btn_clicked)
        self.ui_export.btn_git_pull.clicked.connect(self.git_pull_btn_clicked)
        self.ui_export.btn_git_create_repo.clicked.connect(self.git_create_repo_btn_clicked)
        # tool buttons
        self.ui_export.btn_download_tools.clicked.connect(self.download_tools_btn_clicked)

        current_year = datetime.now().year
        current_month = datetime.now().month
        current_day = datetime.now().day
        max_month = MONTHS_IN_YEAR
        max_quarter = len(QUARTER_NAMES)
        # set period values
        self.ui_export.combo_period.addItem(NO_SPEC, None)
        for month_number, month_name in enumerate(MONTH_NAMES, start=1):
            self.ui_export.combo_period.addItem(month_name, [month_number])
        for quarter_idx, quarter_name in enumerate(QUARTER_NAMES):
            self.ui_export.combo_period.addItem(quarter_name, [(quarter_idx * 3) + i for i in range(1, 4)])
        if current_day > PRE_TAX_DAY_LIMIT:  # tax preregistration is relevant up to this days for last month
            relevant_month = current_month
        else:
            relevant_month = max_month if (current_month == 1) else current_month - 1
        quarterly_tax = self.ui.tab_settings.company_data[COMPANY_DEFAULT_FIELD][ECompanyFields.QUARTERLY_SALES_TAX]
        if quarterly_tax:
            months_in_quarter = int(max_month / max_quarter)
            quarter = int((relevant_month + (months_in_quarter - 1)) / months_in_quarter)
            self.ui_export.combo_period.setCurrentIndex(self.ui_export.combo_period.findText(QUARTER_NAMES[quarter - 1]))
        else:
            self.ui_export.combo_period.setCurrentIndex(self.ui_export.combo_period.findText(MONTH_NAMES[relevant_month - 1]))
        # set year
        active_year = current_year
        if (current_month == 1) and (current_day <= PRE_TAX_DAY_LIMIT):
            active_year -= 1
        self.ui_export.sb_year.setValue(active_year)

        self.tools_downloader = ToolsDownloader()
        self.tools_downloader.status_signal.connect(self.download_tools_status)
        self.tools_downloader.finish_signal.connect(self.download_tools_finish)

        self.update_export_data()

        # TODO disable while buttons unused
        self.ui_export.btn_git_push.hide()
        self.ui_export.btn_git_pull.hide()
        self.ui_export.line_data_update.hide()

    def update_export_data(self) -> None:
        """!
        @brief Updates UI elements and buttons for the export tab.
        """
        self.ui_export.company_logo.setPixmap(QPixmap(os.path.join(self.ui.model.data_path, LOGO_BRIEF_PATH)))

        if os.path.isfile(PORTABLE_GIT_EXE):
            self.ui_export.groupBox_5_git.setVisible(True)
            if check_repo_exists():
                self.ui_export.btn_git_create_repo.hide()
                self.ui_export.line_git_actions.show()
                self.ui_export.btn_git_commit.show()
                self.ui_export.btn_git_push.show()
                self.ui_export.btn_git_pull.show()
            else:
                self.ui_export.btn_git_create_repo.show()
                self.ui_export.line_git_actions.hide()
                self.ui_export.btn_git_commit.hide()
                self.ui_export.btn_git_push.hide()
                self.ui_export.btn_git_pull.hide()
            self.ui_export.groupBox_6_tools.setVisible(False)
        else:
            self.ui_export.groupBox_5_git.setVisible(False)
            self.ui_export.groupBox_6_tools.setVisible(True)

    def update_eur_btn(self) -> None:
        """!
        @brief Updates the EUR/GUV button text depending on profit calculation settings.
        """
        btn_text = EReportType.GUV if (self.ui.tab_settings.company_data[COMPANY_BOOKING_FIELD][ECompanyFields.PROFIT_CALCULATION_CAPITAL]) else EReportType.EUR
        self.ui_export.btn_eur.setText(btn_text)

    def create_export(self, report_type: EReportType) -> None:
        """!
        @brief Creates the selected export report.
        @param report_type : Report type.
        """
        year = None
        months = None
        period = None
        match report_type:
            case EReportType.UST_PRE:
                period = self.ui_export.combo_period.currentText()
                months = self.ui_export.combo_period.currentData()
                year = self.ui_export.sb_year.value()
            case EReportType.UST | EReportType.EUR | EReportType.GUV | EReportType.DATEV:
                year = self.ui_export.sb_year.value()

        export_report = ExportReport(self.ui, report_type, year=year, months=months, period=period)
        self.ui.block_ui()
        if not os.path.exists(EXPORT_PATH):
            os.makedirs(EXPORT_PATH)
        file_name = f"{EXPORT_PATH}/{report_type.value}"
        if year is not None:
            file_name += f"_{year}"
        if period is not None:
            file_name += f"_{period}"
        file_name += ".xlsx"
        try:
            export_report.create_xlsx_report(file_name)
        except PermissionError:
            self.ui.unblock_ui()
            self.ui.set_status(f"Datei kann nicht geschrieben werden: {file_name}", highlight=True)
        else:
            if report_type != EReportType.DATEV:
                self.ui.unblock_ui()
                self.ui.set_status(f"Datei wurde erstellt: {file_name}")
                os.startfile(os.path.abspath(file_name))
            else:
                self.ui.unblock_ui()

    def create_backup(self) -> None:
        """!
        @brief Creates a ZIP backup of the project folder and copies it to the clipboard.
        """
        source_folder = Path(REL_PATH)
        if source_folder.exists():
            self.ui.block_ui()
            now = datetime.now()
            suffix = now.strftime("%Y-%m-%d_%Hh%Mm%Ss")
            out_path = f"{EXPORT_PATH}/Backup_{suffix}"
            shutil.make_archive(out_path, 'zip', source_folder)
            out_path += ".zip"
            # copy folder content to clipboard
            subprocess.run(["powershell", "Set-Clipboard", "-LiteralPath", out_path], check=False)
            open_explorer(out_path)
            self.ui.unblock_ui()
            self.ui.set_status(f"Sicherung wurde erstellt: {out_path}")
        else:
            self.ui.set_status(f"Der Ordner existiert nicht: {source_folder}", highlight=True)

    def combine_pdf(self) -> None:
        """!
        @brief Combines multiple PDF files into a single PDF.
        """
        selected_files, _ = QFileDialog.getOpenFileNames(parent=self.ui, caption="PDF kombinieren",
                                                         directory=self.ui.model.get_last_path(),
                                                         filter=PDF_FILE_TYPES)
        if selected_files:
            now = datetime.now()
            suffix = now.strftime("%Y-%m-%d_%Hh%Mm%Ss")
            _path, file_name = os.path.split(selected_files[0])
            file_name, _file_type = os.path.splitext(file_name)
            out_file = os.path.join(EXPORT_PATH, f"{file_name}_Combined_{suffix}.pdf")
            with fitz.open() as combined_pdf:
                for pdf_file in selected_files:
                    with fitz.open(pdf_file) as actual_pdf:
                        combined_pdf.insert_pdf(actual_pdf)
                combined_pdf.save(out_file)
            open_explorer(out_file)

    def ust_pre_btn_clicked(self) -> None:
        """!
        @brief Generate Umsatzsteuervoranmeldung (quarterly VAT pre-declaration) report.
        """
        self.create_export(EReportType.UST_PRE)

    def ust_btn_clicked(self) -> None:
        """!
        @brief Generate annual Umsatzsteuererklärung (VAT declaration) report.
        """
        self.create_export(EReportType.UST)

    def eur_btn_clicked(self) -> None:
        """!
        @brief Generate EÜR (Einnahmenüberschussrechnung) or GuV (Gewinn- und Verlustrechnung) report.
        """
        report_type = EReportType.EUR if (self.ui_export.btn_eur.text() == EReportType.EUR) else EReportType.GUV
        self.create_export(report_type)

    def export_btn_clicked(self) -> None:
        """!
        @brief Generate combined export with all financial reports and documents.
        """
        self.create_export(EReportType.EXPORT_TOTAL)

    def datev_btn_clicked(self) -> None:
        """!
        @brief Export accounting data in DATEV format for tax consultant upload.
        """
        self.create_export(EReportType.DATEV)

    def open_export_folder_btn_clicked(self) -> None:
        """!
        @brief Opens the export folder in the file explorer.
        """
        if not os.path.exists(EXPORT_PATH):
            os.makedirs(EXPORT_PATH)
        open_explorer(EXPORT_PATH, open_folder=True)

    def transactions_btn_clicked(self) -> None:
        """!
        @brief Opens the banking dialog.
        """
        BankingDialog(self.ui)

    def pdf_combine_btn_clicked(self) -> None:
        """!
        @brief Calls the PDF combine routine.
        """
        self.combine_pdf()

    def update_btn_clicked(self) -> None:
        """!
        @brief Updates all tabs data without renaming files.
        """
        self.ui.update_all_tabs(update=True, rename=False)
        self.ui.set_status("Daten wurden aktualisiert")

    def update_all_btn_clicked(self) -> None:
        """!
        @brief Updates all tabs data including file renaming.
        """
        self.ui.update_all_tabs(update=True, rename=True)
        self.ui.set_status("Daten inklusive Dateiumbenennung wurden vorgenommen")

    def git_commit_btn_clicked(self) -> None:
        """!
        @brief Opens commit dialog and commits changes if confirmed.
        """
        has_changes, changes_summary = check_git_changes()
        if has_changes:
            commit_dialog = CommitDialog(self.ui, changes_summary)
            if commit_dialog.is_commit:
                commit_all_changes(commit_dialog.commit_message)
                self.ui.set_status("Daten committed")
        else:
            self.ui.set_status("Keine Änderungen vorhanden", highlight=True)

    def git_push_btn_clicked(self) -> None:
        """!
        @brief Push local commits to the remote Git repository.
        """
        self.ui.set_status("TODO noch nicht implementiert", highlight=True)  # TODO

    def git_pull_btn_clicked(self) -> None:
        """!
        @brief Pull changes from the remote Git repository.
        """
        self.ui.set_status("TODO noch nicht implementiert", highlight=True)  # TODO

    def git_create_repo_btn_clicked(self) -> None:
        """!
        @brief Creates a new Git repository and writes a .gitignore template.
        """
        success = create_repo()
        if success:
            # read template
            with open(GIT_IGNORE_FILE, "r", encoding="utf-8") as file:
                git_ignore_content = file.read()
            # write to new file
            git_ignore_file_path = os.path.join(CREATE_GIT_PATH, ".gitignore")
            with open(git_ignore_file_path, "w", encoding="utf-8") as file:
                file.write(git_ignore_content)
            git_add(git_ignore_file_path)
            self.ui.set_status("Git Repo erstellt!")
        else:
            self.ui.set_status("Repo konnte nicht erstellt werden", highlight=True)
        self.update_export_data()

    def clean_data_clicked(self) -> None:
        """!
        @brief Cleans all data in tabs (documents, income, expenditure).
        """
        self.ui.update_all_tabs()
        self.ui.tab_document.clean_data()
        self.ui.tab_income.clean_data()
        self.ui.tab_expenditure.clean_data()
        self.ui.set_status("Daten bereinigt")

    def download_tools_btn_clicked(self) -> None:
        """!
        @brief Starts downloading external tools.
        """
        self.ui_export.btn_download_tools.setEnabled(False)
        self.tools_downloader.start()

    def download_tools_status(self, text: str) -> None:
        """!
        @brief Updates status message during download.
        @param text : download status
        """
        self.ui.set_status(text)

    def download_tools_finish(self) -> None:
        """!
        @brief Called when tool download finishes and updates UI.
        """
        self.ui_export.btn_download_tools.setEnabled(True)
        self.update_export_data()
