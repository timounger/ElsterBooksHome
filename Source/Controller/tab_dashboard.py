"""!
********************************************************************************
@file   tab_dashboard.py
@brief Tab for displaying dashboard information.
********************************************************************************
"""

import os
import logging
import math
from typing import TYPE_CHECKING
from datetime import datetime, timedelta
from collections import defaultdict

from PyQt6.QtCharts import QBarCategoryAxis, QBarSeries, QBarSet, QChart, QChartView, QValueAxis
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QPixmap, QFont
from PyQt6.QtWidgets import QGraphicsSimpleTextItem

from Source.version import __title__
from Source.Model.company import LOGO_BRIEF_PATH, validate_company
from Source.Model.data_handler import EReceiptFields, DATE_FORMAT_JSON, MONTH_NAMES_SHORT, MONTHS_IN_YEAR
from Source.Model.income import get_income_files, validate_income
from Source.Model.expenditure import get_expenditure_files, validate_expenditure
from Source.Model.contacts import EContactFields, validate_contact
from Source.Model.document import EDocumentFields, get_document_files, validate_document
from Source.Model.ZUGFeRD.drafthorse_import import set_spin_box_read_only
from Source.Views.tabs.tab_dashboard_ui import Ui_Dashboard
if TYPE_CHECKING:
    from Source.Controller.main_window import MainWindow

log = logging.getLogger(__title__)


def round_to_nearest_integer(number: float, round_len: int = 2) -> int:
    """!
    @brief Round a number up to the next decimal step.
    @param number : Number to round.
    @param round_len : Number of leading digits to keep.
    @return Rounded number.
    """
    number = int(math.ceil(number))
    str_number = str(number)
    if len(str_number) > round_len and str_number[round_len] != "0":
        first_digits = int(str_number[:round_len])
        last_bytes = str_number[round_len:]
        multiple = int("1" + ("0" * len(last_bytes)))
        rounded_number = (first_digits + 1) * multiple
    else:
        rounded_number = number
    return rounded_number


def calc_chart_data(invoice_dates: list[str], values: list[float]) -> list[float]:
    """!
    @brief Calculate monthly chart data for the last 12 months.
    @param invoice_dates : List of invoice date strings.
    @param values : List of corresponding amounts.
    @return Aggregated monthly values for the last 12 months.
    """
    today = datetime.today()
    monthly_sums: defaultdict[tuple[int, int], float] = defaultdict(int)

    for date, amount in zip(invoice_dates, values):
        try:
            date_obj = datetime.strptime(date, DATE_FORMAT_JSON)
        except ValueError:
            pass  # invalid date format
        else:
            if date_obj > today - timedelta(days=365):  # only value from last 12 months
                key = (date_obj.year, date_obj.month)
                monthly_sums[key] += amount

    last_12_months = []
    for i in range(MONTHS_IN_YEAR):
        month = today.month - i
        year = today.year
        if month <= 0:
            month += MONTHS_IN_YEAR
            year -= 1
        last_12_months.append(monthly_sums.get((year, month), 0))

    last_12_months = last_12_months[::-1]
    return last_12_months


class TabDashboard:
    """!
    @brief Controller for the Dashboard tab.
    @param ui : main window
    @param tab_idx : Index of this tab in the tab widget
    """

    def __init__(self, ui: "MainWindow", tab_idx: int) -> None:
        self.ui = ui
        title = "Übersicht"
        tab = ui.tabWidget.widget(tab_idx)
        self.tab = tab
        self.ui_dashboard = Ui_Dashboard()
        self.ui_dashboard.setupUi(tab)
        self.ui_dashboard.lbl_title.setText(title)
        self.ui_dashboard.dashboard_text.setFont(QFont("Consolas", 14))
        ui.tabWidget.setTabText(tab_idx, title)

        self.ui_dashboard.dashboard_text.setReadOnly(True)
        self.warnings: list[str] = []

    def update_dashboard_data(self) -> None:
        """!
        @brief Updates the dashboard values, warnings and chart.
        """
        self.ui_dashboard.company_logo.setPixmap(QPixmap(os.path.join(self.ui.model.data_path, LOGO_BRIEF_PATH)))
        income_gross = self.ui.tab_income.total_gross
        income_net = self.ui.tab_income.total_net
        expenditure_gross = self.ui.tab_expenditure.total_gross
        expenditure_net = self.ui.tab_expenditure.total_net
        diff_gross = income_gross - expenditure_gross
        diff_net = income_net - expenditure_net
        set_spin_box_read_only(self.ui_dashboard.dsb_income_gross, income_gross)
        set_spin_box_read_only(self.ui_dashboard.dsb_expenditure_gross, expenditure_gross)
        set_spin_box_read_only(self.ui_dashboard.dsb_profit_gross, diff_gross)
        set_spin_box_read_only(self.ui_dashboard.dsb_income_net, income_net)
        set_spin_box_read_only(self.ui_dashboard.dsb_expenditure_net, expenditure_net)
        set_spin_box_read_only(self.ui_dashboard.dsb_profit_net, diff_net)
        data = "\n".join(str(warning) for warning in self.warnings)
        if self.warnings:
            self.ui_dashboard.dashboard_text.setTextColor(QColor("orange"))
            self.ui.set_status("Falsche Daten vorhanden.", warning=True)
        else:
            color = "black" if self.ui.model.monitor.is_light_theme() else "white"
            self.ui_dashboard.dashboard_text.setTextColor(QColor(color))
        if not data:
            data = "✅ Alles in Ordnung!"
        self.ui_dashboard.dashboard_text.setText(data)
        self.update_chart()

    def update_chart(self) -> None:
        """!
        @brief Updates the bar chart with income and expenditure data.
        """
        # data
        income_values = calc_chart_data(self.ui.tab_income.invoice_dates, self.ui.tab_income.values)
        expenditure_values = calc_chart_data(self.ui.tab_expenditure.invoice_dates, self.ui.tab_expenditure.values)
        expenditure_values = [-x for x in expenditure_values]  # expenditure are negative
        chart_data = {
            "Einnahmen": income_values,
            "Ausgaben": expenditure_values
        }

        today = datetime.today()
        month_names = []
        for i in range(0, MONTHS_IN_YEAR):
            month = today.month - i
            year = today.year
            if month <= 0:
                month += MONTHS_IN_YEAR
                year -= 1
            month_names.append(MONTH_NAMES_SHORT[month - 1])
        month_names.reverse()

        all_values = [value for values_list in chart_data.values() for value in values_list]

        min_value = min(all_values)
        max_value = max(all_values)
        max_range = max(abs(min_value), abs(max_value))
        max_range = round_to_nearest_integer(max_range)
        steps = 5

        series = QBarSeries()
        series.setBarWidth(0.8)
        series.setLabelsVisible(True)
        series.setLabelsPosition(QBarSeries.LabelsPosition.LabelsOutsideEnd)
        income_color = QColor(0x40, 0xC0, 0x57) if self.ui.model.monitor.is_light_theme() else QColor("green")
        expenditure_color = QColor(0xFA, 0x52, 0x52) if self.ui.model.monitor.is_light_theme() else QColor("red")
        for key, value in chart_data.items():
            bar_set = QBarSet(key)
            q_color = income_color if key == "Einnahmen" else expenditure_color
            bar_set.setBrush(q_color)
            bar_set.append(value)
            bar_set.setLabelColor(QColor("black"))
            bar_set.setLabelFont(QFont("Arial", 8, weight=QFont.Weight.Bold))
            series.append(bar_set)

        # Create chart
        chart = QChart()
        chart.addSeries(series)
        # chart.setTitle("Umsatz")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)  # SeriesAnimations GridAxisAnimations AllAnimations
        chart.setAnimationDuration(1000)

        # x-axis
        axis_x = QBarCategoryAxis()
        axis_x.append(month_names)
        # axis_x.setTitleText("Zeitraum")
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        # y-axis
        axis_y = QValueAxis()
        axis_y.setLabelFormat("%d")  # hide decimal digits
        axis_y.setTickCount(steps)
        axis_y.setRange(-max_range, max_range)
        axis_y.setTitleText("Betrag [€]")
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

        # Create chart view
        color = QColor(0xF8, 0xF9, 0xFA) if self.ui.model.monitor.is_light_theme() else QColor(0xBE, 0xBE, 0xBE)  # default dark QColor(33, 33, 33)
        chart.setBackgroundBrush(QColor(color))
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)  # Antialiasing TextAntialiasing SmoothPixmapTransform

        # note text
        note = QGraphicsSimpleTextItem("Alle Bruttobeträge nach Rechnungsdatum")
        note.setFont(QFont("Segoe UI", 10, weight=QFont.Weight.Bold))
        scene = chart.scene()
        assert scene is not None
        scene.addItem(note)
        note.setPos(40, 40)

        # delete all old QChartView(s) before set new to prevent lagging
        for i in reversed(range(self.ui_dashboard.gridLayout_2.count())):
            item = self.ui_dashboard.gridLayout_2.itemAt(i)
            if item is None:
                continue
            widget = item.widget()
            if isinstance(widget, QChartView):
                self.ui_dashboard.gridLayout_2.takeAt(i)
                widget.deleteLater()

        # Set central widget
        self.ui_dashboard.gridLayout_2.addWidget(chart_view, 0, 0, 1, self.ui_dashboard.gridLayout_2.columnCount())

    def check_data(self) -> None:
        """!
        @brief Validates all stored data and collects warnings.
        """
        self.warnings = []
        ids = []
        # company
        self.warnings += validate_company(self.ui.tab_settings.company_data)
        # income
        for income in self.ui.tab_income.receipts:
            self.warnings += validate_income(income)
            short_id = income[EReceiptFields.ID][:8]
            if short_id not in ids:
                ids.append(short_id)
            else:
                self.warnings.append(f"Einnahme ID vergeben: {short_id}")
        files = get_income_files(self.ui.model.data_path)
        if len(files) != len(self.ui.tab_income.receipts):
            self.warnings.append("Einnahme ungültige Anhang Anzahl")
        for file_name in files:
            if file_name[-8:] not in ids:
                self.warnings.append(f"Einnahme Datei ohne Meta Daten: {file_name}")
        # expenditure
        for expenditure in self.ui.tab_expenditure.receipts:
            self.warnings += validate_expenditure(expenditure)
            short_id = expenditure[EReceiptFields.ID][:8]
            if short_id not in ids:
                ids.append(short_id)
            else:
                self.warnings.append(f"Ausgaben ID vergeben: {short_id}")
        files = get_expenditure_files(self.ui.model.data_path)
        if len(files) != len(self.ui.tab_expenditure.receipts):
            self.warnings.append("Ausgabe ungültige Anhang Anzahl")
        for file_name in files:
            if file_name[-8:] not in ids:
                self.warnings.append(f"Ausgabe Datei ohne Meta Daten: {file_name}")
        # contacts
        for contact in self.ui.tab_contacts.contacts:
            self.warnings += validate_contact(contact)
            short_id = contact[EContactFields.ID][:8]
            if short_id not in ids:
                ids.append(short_id)
            else:
                self.warnings.append(f"Kontakt ID vergeben: {short_id}")
        # documents
        for document in self.ui.tab_document.documents:
            self.warnings += validate_document(document)
            short_id = document[EDocumentFields.ID][:8]
            if short_id not in ids:
                ids.append(short_id)
            else:
                self.warnings.append(f"Dokumenten ID vergeben: {short_id}")
        files = get_document_files(self.ui.model.data_path)
        if len(files) != len(self.ui.tab_document.documents):
            self.warnings.append("Dokumente ungültige Anhang Anzahl")
        for file_name in files:
            if file_name[-8:] not in ids:
                self.warnings.append(f"Dokumente Datei ohne Meta Daten: {file_name}")
