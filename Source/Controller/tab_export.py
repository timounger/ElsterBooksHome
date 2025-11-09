"""!
********************************************************************************
@file   tab_export.py
@brief  Export Tab
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
from Source.Model.data_handler import PDF_FILE_TYPES, L_MONTH_NAMES, create_repo, check_git_changes, commit_all_changes, \
    PORTABLE_GIT_EXE, check_repo_exists, git_add, I_MONTH_IN_YEAR
from Source.Model.company import LOGO_BRIEF_PATH, COMPANY_BOOKING_FIELD, COMPANY_DEFAULT_FIELD, ECompanyFields
from Source.Model.export import ExportReport, EReportType
from Source.Views.tabs.tab_export_ui import Ui_Export
from Source.Worker.tools_downloader import ToolsDownloader
from Source.Controller.dialog_commit import CommitDialog
from Source.Controller.dialog_banking import BankingDialog
if TYPE_CHECKING:
    from Source.Controller.main_window import MainWindow

log = logging.getLogger(__title__)

S_NO_SPEC = "Keine Angabe"
L_QUARTER = ["I. Kalendervierteljahr", "II. Kalendervierteljahr", "III. Kalendervierteljahr", "IV. Kalendervierteljahr"]
PRE_TAX_DAY_LIMIT = 10


class TabExport:
    """!
    @brief Export dialog tab.
    @param ui : main window
    @param tab_idx : tab index
    """

    def __init__(self, ui: "MainWindow", tab_idx: int) -> None:
        self.ui = ui
        s_title = "Export"
        tab = ui.tabWidget.widget(tab_idx)
        self.ui.tabWidget.setTabText(tab_idx, s_title)
        self.ui_export = Ui_Export()
        self.ui_export.setupUi(tab)
        self.ui_export.lbl_title.setText(s_title)
        # open folder button
        self.ui_export.btn_open_folder.setText("")
        # TODO Icon bei Themen wechseln updaten
        self.ui_export.btn_open_folder.setIcon(QIcon(ICON_OPEN_FOLDER_LIGHT if self.ui.model.c_monitor.is_light_theme() else ICON_OPEN_FOLDER_DARK))
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
        max_month = I_MONTH_IN_YEAR
        max_quarter = len(L_QUARTER)
        # set period values
        self.ui_export.cb_period.addItem(S_NO_SPEC, None)
        for month_number, month_name in enumerate(L_MONTH_NAMES, start=1):
            self.ui_export.cb_period.addItem(month_name, [month_number])
        for quarter_idx, quarter_name in enumerate(L_QUARTER):
            self.ui_export.cb_period.addItem(quarter_name, [(quarter_idx * 3) + i for i in range(1, 4)])
        if current_day > PRE_TAX_DAY_LIMIT:  # tax preregistration is relevant up to this days for last month
            relevant_month = current_month
        else:
            relevant_month = max_month if (current_month == 1) else current_month - 1
        b_quarterly_tax = self.ui.tab_settings.company_data[COMPANY_DEFAULT_FIELD][ECompanyFields.QUARTERLY_SALES_TAX]
        if b_quarterly_tax:
            months_in_quarter = int(max_month / max_quarter)
            i_quarter = int((relevant_month + (months_in_quarter - 1)) / months_in_quarter)
            self.ui_export.cb_period.setCurrentIndex(self.ui_export.cb_period.findText(L_QUARTER[i_quarter - 1]))
        else:
            self.ui_export.cb_period.setCurrentIndex(self.ui_export.cb_period.findText(L_MONTH_NAMES[relevant_month - 1]))
        # set year
        active_year = current_year
        if (current_month == 1) and (current_day <= PRE_TAX_DAY_LIMIT):
            active_year -= 1
        self.ui_export.sb_year.setValue(current_year)

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
        @brief Update export data.
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
        @brief Update EUR button.
        """
        btn_text = EReportType.GUV if (self.ui.tab_settings.company_data[COMPANY_BOOKING_FIELD][ECompanyFields.PROFIT_CALCULATION_CAPITAL]) else EReportType.EUR
        self.ui_export.btn_eur.setText(btn_text)

    def create_export(self, e_type: EReportType) -> None:
        """!
        @brief Create export
        @param e_type : report type
        """
        i_year = None
        l_months = None
        s_period = None
        match e_type:
            case EReportType.UST_PRE:
                s_period = self.ui_export.cb_period.currentText()
                l_months = self.ui_export.cb_period.currentData()
                i_year = self.ui_export.sb_year.value()
            case EReportType.UST | EReportType.EUR | EReportType.GUV | EReportType.DATEV:
                i_year = self.ui_export.sb_year.value()

        export_report = ExportReport(self.ui, e_type, i_year=i_year, l_months=l_months, period=s_period)
        self.ui.block_ui()
        if not os.path.exists(EXPORT_PATH):
            os.makedirs(EXPORT_PATH)
        file_name = f"{EXPORT_PATH}/{e_type.value}"
        if i_year is not None:
            file_name += f"_{str(i_year)}"
        if s_period is not None:
            file_name += f"_{s_period}"
        file_name += ".xlsx"
        try:
            export_report.create_xlsx_report(file_name)
        except PermissionError:
            self.ui.unblock_ui()
            self.ui.set_status(f"Datei kann nicht geschrieben werden: {file_name}", b_highlight=True)
        else:
            if e_type != EReportType.DATEV:
                self.ui.unblock_ui()
                self.ui.set_status(f"Datei wurde erstellt: {file_name}")
                with subprocess.Popen(["start", "", file_name], shell=True):
                    pass
            else:
                self.ui.unblock_ui()

    def create_backup(self) -> None:
        """!
        @brief Create backup
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
            command = f"powershell Set-Clipboard -LiteralPath {out_path}"
            os.system(command)
            open_explorer(out_path)
            self.ui.unblock_ui()
            self.ui.set_status(f"Sicherung wurde erstellt: {out_path}.zip")
        else:
            self.ui.set_status(f"Der Ordner existiert nicht: {source_folder}", b_highlight=True)

    def combine_pdf(self) -> None:
        """!
        @brief Combine PDF
        """
        l_select_files, _ = QFileDialog.getOpenFileNames(parent=self.ui, caption="PDF kombinieren",
                                                         directory=self.ui.model.get_last_path(),
                                                         filter=PDF_FILE_TYPES)
        if l_select_files:
            now = datetime.now()
            suffix = now.strftime("%Y-%m-%d_%Hh%Mm%Ss")
            _path, file_name = os.path.split(l_select_files[0])
            file_name, _file_type = os.path.splitext(file_name)
            out_file = os.path.join(EXPORT_PATH, f"{file_name}_Combined_{suffix}.pdf")
            combined_pdf = fitz.open()
            for pdf_file in l_select_files:
                actual_pdf = fitz.open(pdf_file)
                combined_pdf.insert_pdf(actual_pdf)
                actual_pdf.close()
            combined_pdf.save(out_file)
            combined_pdf.close()
            open_explorer(out_file)

    def ust_pre_btn_clicked(self) -> None:
        """!
        @brief UST pre button clicked.
        """
        self.create_export(EReportType.UST_PRE)

    def ust_btn_clicked(self) -> None:
        """!
        @brief UST button clicked.
        """
        self.create_export(EReportType.UST)

    def eur_btn_clicked(self) -> None:
        """!
        @brief EUR button clicked.
        """
        e_report_type = EReportType.EUR if (self.ui_export.btn_eur.text() == EReportType.EUR) else EReportType.GUV
        self.create_export(e_report_type)

    def export_btn_clicked(self) -> None:
        """!
        @brief Export button clicked.
        """
        self.create_export(EReportType.EXPORT_TOTAL)

    def datev_btn_clicked(self) -> None:
        """!
        @brief DATEV button clicked.
        """
        self.create_export(EReportType.DATEV)

    def open_export_folder_btn_clicked(self) -> None:
        """!
        @brief Open export folder button clicked.
        """
        if not os.path.exists(EXPORT_PATH):
            os.makedirs(EXPORT_PATH)
        open_explorer(EXPORT_PATH, b_open_input=True)

    def transactions_btn_clicked(self) -> None:
        """!
        @brief Transactions button clicked.
        """
        BankingDialog(self.ui)

    def pdf_combine_btn_clicked(self) -> None:
        """!
        @brief PDF combine button clicked.
        """
        self.combine_pdf()

    def update_btn_clicked(self) -> None:
        """!
        @brief Update data button clicked.
        """
        self.ui.update_all_tabs(update=True, rename=False)
        self.ui.set_status("Daten wurden aktualisiert")

    def update_all_btn_clicked(self) -> None:
        """!
        @brief Update data inclusive file renaming button clicked.
        """
        self.ui.update_all_tabs(update=True, rename=True)
        self.ui.set_status("Daten inklusive Dateiumbenennung wurden vorgenommen")

    def git_commit_btn_clicked(self) -> None:
        """!
        @brief Git commit button clicked.
        """
        b_changes, s_changes = check_git_changes()
        if b_changes:
            commit_dialog = CommitDialog(self.ui, s_changes)
            if commit_dialog.b_commit:
                commit_all_changes(commit_dialog.commit_message)
                self.ui.set_status("Daten committed")
        else:
            self.ui.set_status("Keine Änderungen vorhanden", b_highlight=True)

    def git_push_btn_clicked(self) -> None:
        """!
        @brief Git push button clicked.
        """
        self.ui.set_status("TODO noch nicht implementiert", b_highlight=True)  # TODO

    def git_pull_btn_clicked(self) -> None:
        """!
        @brief Git pull button clicked.
        """
        self.ui.set_status("TODO noch nicht implementiert", b_highlight=True)  # TODO

    def git_create_repo_btn_clicked(self) -> None:
        """!
        @brief Git create repo button clicked.
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
            self.ui.set_status("Repo konnte nicht erstellt werden", b_highlight=True)
        self.update_export_data()

    def clean_data_clicked(self) -> None:
        """!
        @brief Clean data button clicked.
        """
        self.ui.update_all_tabs()
        self.ui.tab_document.clean_data()
        self.ui.tab_income.clean_data()
        self.ui.tab_expenditure.clean_data()
        self.ui.set_status("Daten bereinigt")

    def download_tools_btn_clicked(self) -> None:
        """!
        @brief Download tools button clicked.
        """
        self.ui_export.btn_download_tools.setEnabled(False)
        self.tools_downloader.start()

    def download_tools_status(self, text: str) -> None:
        """!
        @brief Download tools status.
        @param text : download status
        """
        self.ui.set_status(text)

    def download_tools_finish(self) -> None:
        """!
        @brief Download tools finish.
        """
        self.ui_export.btn_download_tools.setEnabled(True)
        self.update_export_data()
