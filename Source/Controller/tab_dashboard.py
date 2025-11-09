"""!
********************************************************************************
@file   tab_dashboard.py
@brief  Dashboard Tab
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

from Source.version import __title__
from Source.Model.company import LOGO_BRIEF_PATH, validate_company, COMPANY_BOOKING_FIELD, ECompanyFields
from Source.Model.data_handler import EReceiptFields, DATE_FORMAT_JSON, L_MONTH_NAMES_SHORT, I_MONTH_IN_YEAR
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
    @brief round number to next step
    @param number : number to round
    @param round_len : number of chars to round
    @return rounded number
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


def calc_chart_data(l_invoice_date: list[str], l_value: list[float]) -> list[float]:
    """!
    @brief Calculate chart data.
    @param l_invoice_date : list with data
    @param l_value : list with values
    @return list with data of last 12 months
    """
    today = datetime.today()
    monthly_sums: defaultdict[tuple[int, int], float] = defaultdict(int)

    for date, amount in zip(l_invoice_date, l_value):
        try:
            date_obj = datetime.strptime(date, DATE_FORMAT_JSON)
        except ValueError:
            pass  # invalid date format
        else:
            if date_obj > today - timedelta(days=365):  # only value from last 12 months
                key = (date_obj.year, date_obj.month)
                monthly_sums[key] += amount

    last_12_months = []
    for i in range(I_MONTH_IN_YEAR):
        month = today.month - i
        year = today.year
        if month <= 0:
            month += I_MONTH_IN_YEAR
            year -= 1
        last_12_months.append(monthly_sums.get((year, month), 0))

    last_12_months = last_12_months[::-1]
    return last_12_months


def check_valid_tax(gross: float, net: float, l_vat_rates: list[int | float]) -> bool:
    """!
    @brief Check if tax is valid TODO abschaltbar oder konfigurierbar machen da bei mischrechnungen auftauchen kann.
    @param gross : gross
    @param net : net
    @param l_vat_rates : possible vat rates
    @return valid status
    """
    valid = True
    return valid


class TabDashboard:
    """!
    @brief Dashboard dialog tab.
    @param ui : main window
    @param tab_idx : tab index
    """

    def __init__(self, ui: "MainWindow", tab_idx: int) -> None:
        self.ui = ui
        s_title = "Übersicht"
        tab = ui.tabWidget.widget(tab_idx)
        self.tab = tab
        self.ui_dashboard = Ui_Dashboard()
        self.ui_dashboard.setupUi(tab)
        self.ui_dashboard.lbl_title.setText(s_title)
        self.ui_dashboard.dashboard_text.setFont(QFont("Consolas", 14))
        ui.tabWidget.setTabText(tab_idx, s_title)

        self.ui_dashboard.dashboard_text.setReadOnly(True)
        self.l_warnings: list[str] = []

    def update_dashboard_data(self) -> None:
        """!
        @brief Update dashboard data.
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
        data = ""
        for warning in self.l_warnings:
            data += f"\n{warning}"
        if len(self.l_warnings) > 0:
            self.ui_dashboard.dashboard_text.setTextColor(QColor("orange"))
            self.ui.set_status("Falsche Daten vorhanden.", b_warning=True)
        else:
            color = "black" if self.ui.model.c_monitor.is_light_theme() else "white"
            self.ui_dashboard.dashboard_text.setTextColor(QColor(color))
        if not data:
            data = "✅ Alles in Ordnung!"
        self.ui_dashboard.dashboard_text.setText(data)
        self.update_chart()

    def update_chart(self) -> None:
        """!
        @brief Update chart.
        """
        # data
        l_income = calc_chart_data(self.ui.tab_income.l_invoice_date, self.ui.tab_income.l_value)
        l_expenditure = calc_chart_data(self.ui.tab_expenditure.l_invoice_date, self.ui.tab_expenditure.l_value)
        l_expenditure = [-x for x in l_expenditure]  # expenditure are negative
        d_data = {
            "Einnahmen": l_income,
            "Ausgaben": l_expenditure
        }

        today = datetime.today()
        month_names = []
        for i in range(0, I_MONTH_IN_YEAR):
            month = today.month - i
            year = today.year
            if month <= 0:
                month += I_MONTH_IN_YEAR
                year -= 1
            month_names.append(L_MONTH_NAMES_SHORT[month - 1])
        month_names.reverse()

        l_numbers = [value for values_list in d_data.values() for value in values_list]

        min_value = min(l_numbers)
        max_value = max(l_numbers)
        max_range = max(abs(min_value), abs(max_value))
        max_range = round_to_nearest_integer(max_range)
        steps = 5

        series = QBarSeries()
        series.setBarWidth(0.8)
        series.setLabelsVisible(True)
        series.setLabelsPosition(QBarSeries.LabelsPosition.LabelsOutsideEnd)
        for key, value in d_data.items():
            bar_set = QBarSet(key)
            income_color = QColor("lightgreen") if self.ui.model.c_monitor.is_light_theme() else QColor("green")
            expenditure_color = QColor(255, 71, 77) if self.ui.model.c_monitor.is_light_theme() else QColor("red")
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
        color = "white" if self.ui.model.c_monitor.is_light_theme() else "lightgrey"  # default dark QColor(33, 33, 33)
        chart.setBackgroundBrush(QColor(color))
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)  # Antialiasing TextAntialiasing SmoothPixmapTransform

        # delete all old QChartView(s) before set new to prevent lagging
        for i in reversed(range(self.ui_dashboard.gridLayout_2.count())):
            item = self.ui_dashboard.gridLayout_2.itemAt(i)
            widget = item.widget()
            if isinstance(widget, QChartView):
                self.ui_dashboard.gridLayout_2.takeAt(i)
                widget.deleteLater()

        # Set central widget
        self.ui_dashboard.gridLayout_2.addWidget(chart_view, 0, 0, 1, self.ui_dashboard.gridLayout_2.columnCount())

    def check_data(self) -> None:
        """!
        @brief Check data.
        """
        tax_rates = self.ui.tab_settings.company_data[COMPANY_BOOKING_FIELD][ECompanyFields.TAX_RATES]
        self.l_warnings = []
        l_ids = []
        # company
        self.l_warnings += validate_company(self.ui.tab_settings.company_data)
        # income
        for income in self.ui.tab_income.l_data:
            self.l_warnings += validate_income(income)
            s_id = income[EReceiptFields.ID][:8]
            if s_id not in l_ids:
                l_ids.append(s_id)
            else:
                self.l_warnings.append(f"Einnahme ID vergeben: {s_id}")
            if not check_valid_tax(income[EReceiptFields.AMOUNT_GROSS], income[EReceiptFields.AMOUNT_NET], tax_rates):
                self.l_warnings.append(f"Einnahme USt. falsch: {s_id}")
        files = get_income_files(self.ui.model.data_path)
        if len(files) != len(self.ui.tab_income.l_data):
            self.l_warnings.append("Einnahme ungültige Anhang Anzahl")
        for file_name in files:
            if file_name[-8:] not in l_ids:
                self.l_warnings.append(f"Einnahme Datei ohne Meta Daten: {file_name}")
        # expenditure
        for expenditure in self.ui.tab_expenditure.l_data:
            self.l_warnings += validate_expenditure(expenditure)
            s_id = expenditure[EReceiptFields.ID][:8]
            if s_id not in l_ids:
                l_ids.append(s_id)
            else:
                self.l_warnings.append(f"Ausgaben ID vergeben: {s_id}")
            if not check_valid_tax(expenditure[EReceiptFields.AMOUNT_GROSS], expenditure[EReceiptFields.AMOUNT_NET], tax_rates):
                self.l_warnings.append(f"Ausgabe USt. falsch: {s_id}")
        files = get_expenditure_files(self.ui.model.data_path)
        if len(files) != len(self.ui.tab_expenditure.l_data):
            self.l_warnings.append("Ausgabe ungültige Anhang Anzahl")
        for file_name in files:
            if file_name[-8:] not in l_ids:
                self.l_warnings.append(f"Ausgabe Datei ohne Meta Daten: {file_name}")
        # contacts
        for contact in self.ui.tab_contacts.l_data:
            self.l_warnings += validate_contact(contact)
            s_id = contact[EContactFields.ID][:8]
            if s_id not in l_ids:
                l_ids.append(s_id)
            else:
                self.l_warnings.append(f"Kontakt ID vergeben: {s_id}")
        # documents
        for document in self.ui.tab_document.l_data:
            self.l_warnings += validate_document(document)
            s_id = document[EDocumentFields.ID][:8]
            if s_id not in l_ids:
                l_ids.append(s_id)
            else:
                self.l_warnings.append(f"Dokumenten ID vergeben: {s_id}")
        files = get_document_files(self.ui.model.data_path)
        if len(files) != len(self.ui.tab_document.l_data):
            self.l_warnings.append("Dokumente ungültige Anhang Anzahl")
        for file_name in files:
            if file_name[-8:] not in l_ids:
                self.l_warnings.append(f"Dokumente Datei ohne Meta Daten: {file_name}")
