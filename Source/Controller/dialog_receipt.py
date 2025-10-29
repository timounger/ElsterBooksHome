"""!
********************************************************************************
@file   dialog_receipt.py
@brief  Receipt dialog
********************************************************************************
"""

import os
import logging
import enum
from typing import Optional, Any, TYPE_CHECKING
import copy
import subprocess

from PyQt6.QtGui import QIcon, QAction, QCloseEvent
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QComboBox, QPushButton, QWidget, QSplitter, QMessageBox
from PyQt6.QtCore import QDate, Qt, QPointF
from PyQt6.QtPdf import QPdfDocument
from PyQt6.QtPdfWidgets import QPdfView

from Source.version import __title__
from Source.Util.app_data import ICON_SEARCH_LIST_LIGHT, ICON_SEARCH_LIST_DARK, EAiType, thread_dialog, \
    ICON_ARROW_LEFT_LIGHT, ICON_ARROW_LEFT_DARK, ICON_ARROW_RIGHT_LIGHT, ICON_ARROW_RIGHT_DARK, ICON_WARNING
from Source.Views.dialogs.dialog_receipt_ui import Ui_DialogReceipt
from Source.Views.widgets.invoice_data_ui import Ui_InvoiceData
from Source.Model.income import delete_income, export_income, INCOME_FILE_PATH
from Source.Model.expenditure import delete_expenditure, export_expenditure, EXPENDITURE_FILE_PATH
from Source.Model.data_handler import EReceiptFields, DATE_FORMAT, \
    D_RECEIPT_GROUP, PDF_TYPE, find_file, get_file_name_content, D_RECEIPT_TEMPLATE, EReceiptGroup, calc_vat_rate
from Source.Model.company import COMPANY_DEFAULT_FIELD, COMPANY_BOOKING_FIELD, ECompanyFields, COMPANY_ADDRESS_FIELD
from Source.Model.PreTax.ust_preregistration_import import import_pre_tax, check_pre_tax
from Source.Model.PreTax.ust_import import import_ust, check_ust
from Source.Model.ZUGFeRD.drafthorse_import import extract_xml_from_pdf, visualize_xml_invoice, \
    check_zugferd, check_xinvoice, import_zugferd, import_xinvoice, extract_xml_from_xinvoice
from Source.Model.ZUGFeRD.drafthorse_invoice import eval_factur_xml
if TYPE_CHECKING:
    from Source.Controller.main_window import MainWindow
from Source.Model.ai_data import InvoiceData

log = logging.getLogger(__title__)


class EReceiptType(str, enum.Enum):
    """!
    @brief Receipt type.
    """
    INCOME = "Einnahmen"
    EXPENDITURE = "Ausgaben"
    GENERAL = "Beleg"


class DocView(enum.IntEnum):
    """!
    @brief Index ob document view
    """
    PDF = 0
    XML = 1


class ReceiptDialog(QDialog, Ui_DialogReceipt):
    """!
    @brief Receipt dialog.
    @param ui : main window
    @param data : document data
    @param uid : UID of receipt
    @param file_path : receipt file
    @param receipt_type : receipt type
    """

    def __init__(self, ui: "MainWindow", data: Optional[dict[EReceiptFields, Any]] = None, uid: Optional[str] = None, file_path: Optional[str] = None,  # pylint: disable=keyword-arg-before-vararg
                 receipt_type: EReceiptType = EReceiptType.GENERAL, *args: Any, **kwargs: Any) -> None:
        super().__init__(parent=ui, *args, **kwargs)  # type: ignore
        self.setupUi(self)
        self.setMinimumWidth(900)
        self.setMinimumHeight(500)
        self.setWindowFlags(Qt.WindowType.Window)  # set all window buttons (e.g max window size)
        self.ui = ui
        self.data = data
        self.uid = uid
        self.file_path = file_path  # only set for new receipt
        self.b_gross_changed = False
        self.b_net_changed = False
        self.b_pay_data_changed = False
        self.b_lock_auto_payed_data = False
        self.receipt_type = receipt_type
        self.xml_warnings = ""
        self.default_tax_rate = self.ui.tab_settings.company_data[COMPANY_BOOKING_FIELD][ECompanyFields.TAX_RATES][0]

        # PDF view
        self.pdf_document = QPdfDocument(self)
        self.pdf_view = QPdfView(self)
        self.pdf_view.setDocument(self.pdf_document)
        layout = QVBoxLayout(self.page_pdf)  # set layout for QFrame
        layout.setContentsMargins(0, 0, 0, 0)  # no border
        layout.addWidget(self.pdf_view)

        # XML view
        container_widget = QWidget()
        self.ui_invoice_data = Ui_InvoiceData()
        self.ui_invoice_data.setupUi(container_widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(container_widget)
        layout = QVBoxLayout(self.page_xml)  # layout for full size of scroll area in xml page
        layout.addWidget(self.scroll_area)

        # document view toggle PDF/XML
        self.btn_view_pdf.clicked.connect(lambda: self.doc_view_changed(DocView.PDF))
        self.btn_view_xml.clicked.connect(lambda: self.doc_view_changed(DocView.XML))
        self.doc_view_changed(DocView.PDF)  # set default view

        # add splitter for left/right distance
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.groupBox)
        splitter.addWidget(self.widget_right)
        self.layout().addWidget(splitter)
        splitter.setSizes([390, 610])  # set split ratio

        thread_dialog(self)

    def show_dialog(self) -> None:
        """!
        @brief Show dialog
        """
        log.debug("Starting Receipt dialog")

        self.ui.model.c_monitor.set_dialog_style(self)
        current_date = QDate.currentDate()

        self.lbl_ai_assist_status.setText("")
        self.lbl_xml_valid.setText("")

        if self.data is None:
            self.btn_delete.hide()
            self.detect_data()

        if self.data is not None:
            # invoice number
            self.le_invoice_number.setText(self.data[EReceiptFields.INVOICE_NUMBER])
            # invoice data
            invoice_date = QDate.fromString(self.data[EReceiptFields.INVOICE_DATE], DATE_FORMAT)
            self.de_invoice_date.setDate(invoice_date)
            # deliver date
            self.le_deliver_date.setText(self.data[EReceiptFields.DELIVER_DATE])
            # trade partner
            self.pte_trade_partner.setPlainText(self.data[EReceiptFields.TRADE_PARTNER])
            # description
            self.pte_description.setPlainText(self.data[EReceiptFields.DESCRIPTION])
            # gross
            self.b_gross_changed = True
            self.dsb_gross.setValue(self.data[EReceiptFields.AMOUNT_GROSS])
            # net
            self.b_net_changed = True
            self.dsb_net.setValue(self.data[EReceiptFields.AMOUNT_NET])
            # payment
            self.b_pay_data_changed = True
            pay_date = QDate.fromString(self.data[EReceiptFields.PAYMENT_DATE], DATE_FORMAT)
            if pay_date:
                b_payed = True
                pay_date = QDate.fromString(self.data[EReceiptFields.PAYMENT_DATE], DATE_FORMAT)
            else:
                b_payed = False
                pay_date = current_date
            self.de_payment_date.setDate(pay_date)
            bar_checked = self.data[EReceiptFields.BAR]
            # comment
            self.pte_comment.setPlainText(self.data[EReceiptFields.COMMENT])
            # group
            self.le_group.setText(self.data[EReceiptFields.GROUP])
            # load preview
            if self.file_path is None:
                if self.receipt_type == EReceiptType.INCOME:
                    data_path = os.path.join(self.ui.model.data_path, INCOME_FILE_PATH)
                else:
                    data_path = os.path.join(self.ui.model.data_path, EXPENDITURE_FILE_PATH)
                preview_file = find_file(data_path, self.uid, file_name=self.data[EReceiptFields.ATTACHMENT])
            else:
                preview_file = self.file_path
        else:
            b_payed = self.ui.tab_settings.company_data[COMPANY_DEFAULT_FIELD][ECompanyFields.PAYED]
            bar_checked = self.ui.tab_settings.company_data[COMPANY_DEFAULT_FIELD][ECompanyFields.BAR_PAYED]
            # set actual date date
            actual_date = current_date
            self.de_invoice_date.setDate(actual_date)
            self.de_payment_date.setDate(actual_date)
            # group
            match self.receipt_type:
                case EReceiptType.INCOME:
                    group_text = self.ui.tab_settings.company_data[COMPANY_DEFAULT_FIELD][ECompanyFields.INCOME_GROUP]
                case EReceiptType.EXPENDITURE:
                    group_text = self.ui.tab_settings.company_data[COMPANY_DEFAULT_FIELD][ECompanyFields.EXPENDITURE_GROUP]
                case _:
                    group_text = ""
            self.le_group.setText(group_text)
            self.lbl_ai_assist_status.setText("")
            b_use_file_name_for_content = True
            if self.file_path.lower().endswith(PDF_TYPE.lower()):
                match self.ui.model.ai_type:
                    case EAiType.OPEN_AI:
                        if self.ui.model.c_open_ai.get_ready_state():
                            self.lbl_ai_assist_status.setText("Erkennung läuft...")
                            self.lbl_ai_assist_status.setStyleSheet("color: orange;")
                            self.ui.model.c_open_ai.file_path = self.file_path
                            self.ui.model.c_open_ai.finish_signal.connect(self.set_detected_invoice_data)
                            self.ui.model.c_open_ai.start()
                            b_use_file_name_for_content = False
                    case EAiType.OLLAMA:
                        if self.ui.model.c_ollama_ai.get_ready_state():
                            self.lbl_ai_assist_status.setText("Erkennung läuft...")
                            self.lbl_ai_assist_status.setStyleSheet("color: orange;")
                            self.ui.model.c_ollama_ai.file_path = self.file_path
                            self.ui.model.c_ollama_ai.finish_signal.connect(self.set_detected_invoice_data)
                            self.ui.model.c_ollama_ai.start()
                            b_use_file_name_for_content = False
                    case _:
                        b_use_file_name_for_content = True
            if b_use_file_name_for_content:
                file_date, file_content = get_file_name_content(self.file_path)
                if file_date is not None:
                    invoice_date = QDate.fromString(file_date, DATE_FORMAT)
                    self.de_invoice_date.setDate(invoice_date)
                if file_content is not None:
                    self.pte_description.setPlainText(file_content)
            preview_file = self.file_path
        b_show_pdf_page_arrow = False
        if preview_file is not None:  # load preview
            # load PDF and auto zoom
            self.pdf_document.load(preview_file)
            self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
            self.pdf_view.mouseDoubleClickEvent = lambda event: self.preview_clicked(preview_file)
            xml_content = None
            if preview_file.lower().endswith(PDF_TYPE.lower()):
                b_show_pdf_page_arrow = True
                if check_zugferd(preview_file):
                    xml_content = extract_xml_from_pdf(preview_file)
                    visualize_xml_invoice(self.ui_invoice_data, xml_content)
                else:
                    self.btn_view_pdf.hide()
                    self.btn_view_xml.hide()
            else:
                if check_xinvoice(preview_file):
                    xml_content = extract_xml_from_xinvoice(preview_file)
                    visualize_xml_invoice(self.ui_invoice_data, xml_content)
                    self.btn_view_pdf.hide()
                    self.btn_view_xml.hide()
                    self.doc_view.setCurrentWidget(self.page_xml)  # show xml tab
            if xml_content:
                is_valid, warning_text = eval_factur_xml(xml_content)
                self.xml_warnings = warning_text
                if is_valid:
                    self.lbl_xml_valid.setText("EN16931 konform")
                    self.lbl_xml_valid.setStyleSheet("color: green;")
                    self.btn_xml_warning.hide()
                else:
                    is_valid, _warning_text_ext = eval_factur_xml(xml_content, extended=True)
                    if is_valid:
                        self.lbl_xml_valid.setText("Extended konform")
                        self.lbl_xml_valid.setStyleSheet("color: orange;")
                    else:
                        self.lbl_xml_valid.setText("XML nicht konform")
                        self.lbl_xml_valid.setStyleSheet("color: red;")
                    self.btn_xml_warning.setIcon(QIcon(ICON_WARNING))
                    self.btn_xml_warning.clicked.connect(self.open_xml_warnings)
            else:
                self.btn_xml_warning.hide()
        else:
            self.btn_view_pdf.hide()
            self.btn_view_xml.hide()

        if b_show_pdf_page_arrow and (self.pdf_document.pageCount() > 1):
            self.update_pdf_page(None)
            self.btn_left.clicked.connect(lambda: self.update_pdf_page(False))
            self.btn_right.clicked.connect(lambda: self.update_pdf_page(True))
        else:
            self.btn_left.hide()
            self.btn_right.hide()
            self.lbl_page_number.hide()

        self.setWindowTitle(self.receipt_type.value)
        self.cb_pay_check.setChecked(b_payed)
        self.cb_pay_check.stateChanged.connect(self.on_payed_changed)
        self.cb_bar_check.setChecked(bar_checked)
        self.on_payed_changed(b_payed)
        self.dsb_gross.valueChanged.connect(self.gross_changed)
        self.dsb_net.valueChanged.connect(self.net_changed)
        self.de_invoice_date.dateChanged.connect(self.on_invoice_data_changed)
        self.de_payment_date.dateChanged.connect(self.on_pay_data_changed)
        self.set_vat_rate()
        self.le_tax.setReadOnly(True)
        self.btn_save.clicked.connect(self.save_clicked)
        self.btn_delete.clicked.connect(self.delete_clicked)
        self.btn_cancel.clicked.connect(self.close)
        # group
        action = QAction(QIcon(ICON_SEARCH_LIST_LIGHT if self.ui.model.c_monitor.is_light_theme() else ICON_SEARCH_LIST_DARK), "Wähle eine Kategorie", self.ui)
        action.triggered.connect(self.show_group_dialog)
        self.le_group.addAction(action, QLineEdit.ActionPosition.TrailingPosition)
        self.show()
        self.exec()

    def detect_data(self) -> None:
        """!
        @brief Detect data.
        """
        is_income = bool(self.receipt_type == EReceiptType.INCOME)
        file_path = self.file_path
        company = self.ui.tab_settings.company_data
        company_default = company[COMPANY_DEFAULT_FIELD]
        b_german = bool(company[COMPANY_ADDRESS_FIELD][ECompanyFields.COUNTRY] == "DE")
        if file_path.lower().endswith(PDF_TYPE.lower()):
            # check for auto import
            if is_income:
                b_custom_detect = False
            else:
                b_custom_detect = False
            if not b_custom_detect:
                if b_german and check_pre_tax(file_path):
                    data = import_pre_tax(file_path, is_income=is_income)
                    if data:
                        self.data = data
                        self.lbl_ai_assist_status.setText(f"{EReceiptGroup.UST_VA.value} erkannt!")
                        self.lbl_ai_assist_status.setStyleSheet("color: green;")
                    else:
                        self.lbl_ai_assist_status.setText(f"{EReceiptGroup.UST_VA.value} ist keine Ausgabe")
                        self.lbl_ai_assist_status.setStyleSheet("color: red;")
                elif b_german and check_ust(file_path):
                    data = import_ust(file_path, is_income=is_income)
                    if data:
                        self.data = data
                        self.lbl_ai_assist_status.setText(f"{EReceiptGroup.UST.value} erkannt!")
                        self.lbl_ai_assist_status.setStyleSheet("color: green;")
                    else:
                        self.lbl_ai_assist_status.setText(f"{EReceiptGroup.UST.value} ist keine Ausgabe")
                        self.lbl_ai_assist_status.setStyleSheet("color: red;")
                elif check_zugferd(file_path):
                    data = import_zugferd(file_path, is_income=is_income,
                                          income_group=company_default[ECompanyFields.INCOME_GROUP],
                                          expenditure_group=company_default[ECompanyFields.EXPENDITURE_GROUP])
                    if data:
                        self.data = data
                        self.lbl_ai_assist_status.setText("ZUGFeRD erkannt!")
                        self.lbl_ai_assist_status.setStyleSheet("color: green;")
                    else:
                        self.lbl_ai_assist_status.setText("ZUGFeRD konnte nicht automatisch importiert werden")
                        self.lbl_ai_assist_status.setStyleSheet("color: red;")
        else:
            if check_xinvoice(file_path):
                data = import_xinvoice(file_path, is_income=is_income,
                                       income_group=company_default[ECompanyFields.INCOME_GROUP],
                                       expenditure_group=company_default[ECompanyFields.EXPENDITURE_GROUP])
                if data:
                    self.data = data
                    self.lbl_ai_assist_status.setText("XRechnung erkannt!")
                    self.lbl_ai_assist_status.setStyleSheet("color: green;")
                else:
                    self.lbl_ai_assist_status.setText("XRechnung konnte nicht automatisch importiert werden")
                    self.lbl_ai_assist_status.setStyleSheet("color: red;")

    def closeEvent(self, event: Optional[QCloseEvent]) -> None:  # pylint: disable=invalid-name
        """!
        @brief Default close Event Method to handle application close
        @param event : arrived event
        """
        self.ui.model.c_open_ai.terminate()
        self.ui.model.c_ollama_ai.terminate()
        if event is not None:
            event.accept()

    def update_pdf_page(self, direction: bool | None) -> None:
        """!
        @brief Update PDF page
        @param direction : page direction  (None: init first, False: prev, True: next)
        """
        total_pages = self.pdf_document.pageCount()
        if total_pages > 1:
            current_page = self.pdf_view.pageNavigator().currentPage() + 1
            self.lbl_page_number.show()
            if direction is None:
                page_number = 1
                b_light_theme = self.ui.model.c_monitor.is_light_theme()
                self.btn_left.setIcon(QIcon(ICON_ARROW_LEFT_LIGHT if b_light_theme else ICON_ARROW_LEFT_DARK))
                self.btn_right.setIcon(QIcon(ICON_ARROW_RIGHT_LIGHT if b_light_theme else ICON_ARROW_RIGHT_DARK))
                self.btn_left.show()
                self.btn_right.show()
                self.btn_left.setEnabled(False)
                self.btn_right.setEnabled(True)
            else:
                if direction:
                    page_number = current_page + 1
                else:
                    page_number = current_page - 1
                if page_number == 1:
                    self.btn_left.setEnabled(False)
                    self.btn_right.setEnabled(True)
                elif page_number == total_pages:
                    self.btn_left.setEnabled(True)
                    self.btn_right.setEnabled(False)
            self.pdf_view.pageNavigator().jump(page_number - 1, QPointF(0, 0))
            self.lbl_page_number.setText(f"{page_number}/{total_pages}")

    def open_xml_warnings(self):
        """!
        @brief Open xml warning dialog
        """
        QMessageBox.warning(self, "XML Warnungen", self.xml_warnings)

    def doc_view_changed(self, doc_view: DocView) -> None:
        """!
        @brief Doc view changed. Set doc widget and update button color
        @param doc_view : doc view index
        """
        if self.ui.model.c_monitor.is_light_theme():
            active_fg = "white"
            active_bg = "#007BFF"
            inactive_fg = "#555555"
            inactive_bg = "#e0e0e0"
        else:
            active_fg = "black"
            active_bg = "#3399FF"
            inactive_fg = "#bbbbbb"
            inactive_bg = "#2e2e2e"
        match doc_view:
            case DocView.PDF:
                self.doc_view.setCurrentIndex(DocView.PDF)
                self.btn_view_pdf.setStyleSheet(f"color: {active_fg}; background-color: {active_bg};")
                self.btn_view_xml.setStyleSheet(f"color: {inactive_fg}; background-color: {inactive_bg};")
                self.update_pdf_page(None)
            case DocView.XML:
                self.doc_view.setCurrentIndex(DocView.XML)
                self.btn_view_xml.setStyleSheet(f"color: {active_fg}; background-color: {active_bg};")
                self.btn_view_pdf.setStyleSheet(f"color: {inactive_fg}; background-color: {inactive_bg};")
                self.btn_left.hide()
                self.btn_right.hide()
                self.lbl_page_number.hide()
            case _:
                log.warning("Invalid doc view %s", doc_view)

    def preview_clicked(self, attachment_file: str) -> None:
        """!
        @brief On preview clicked
        @param attachment_file : attachment file
        """
        with subprocess.Popen(["start", "", attachment_file], shell=True):
            pass

    def set_detected_invoice_data(self, invoice_data: InvoiceData) -> None:
        """!
        @brief Set detected invoice data. Do not add if user input text before
        @param invoice_data : invoice data
        """
        if invoice_data is not None:
            # invoice number
            if invoice_data.invoice_number and not self.le_invoice_number.text():
                self.le_invoice_number.setText(invoice_data.invoice_number)
            # invoice data
            current_date = QDate.currentDate()
            if invoice_data.invoice_date and (self.de_invoice_date.date() == current_date):
                invoice_date = QDate.fromString(invoice_data.invoice_date, DATE_FORMAT)
                self.de_invoice_date.setDate(invoice_date)
            # trade partner
            if invoice_data.seller_name and not self.pte_trade_partner.toPlainText():
                self.pte_trade_partner.setPlainText(invoice_data.seller_name)
            # description
            if invoice_data.description and not self.pte_description.toPlainText():
                self.pte_description.setPlainText(invoice_data.description)
            # gross
            if invoice_data.gross_amount and not self.dsb_gross.value():
                self.dsb_gross.setValue(invoice_data.gross_amount)
            # net
            if invoice_data.net_amount and not self.dsb_net.value():
                self.dsb_net.setValue(invoice_data.net_amount)
        self.lbl_ai_assist_status.setText("Erkennung abgeschlossen!")
        self.lbl_ai_assist_status.setStyleSheet("color: green;")

    def gross_changed(self) -> None:
        """!
        @brief Gross changed.
        """
        gross_price = self.dsb_gross.value()
        if gross_price is not None:
            self.b_gross_changed = True
            if not self.b_net_changed:
                if (self.receipt_type == EReceiptType.INCOME) and self.ui.tab_settings.company_data[COMPANY_BOOKING_FIELD][ECompanyFields.SMALL_BUSINESS_REGULATION]:
                    f_net = gross_price  # income for small business regulation is net = gross
                else:
                    f_net = round(gross_price / (1 + (self.default_tax_rate / 100)), 2)
                self.dsb_net.setValue(f_net)
                self.b_net_changed = False
        else:
            self.b_gross_changed = False
        self.set_vat_rate()

    def net_changed(self) -> None:
        """!
        @brief Net changed.
        """
        net_price = self.dsb_net.value()
        if net_price is not None:
            self.b_net_changed = True
            if not self.b_gross_changed:
                if (self.receipt_type == EReceiptType.INCOME) and self.ui.tab_settings.company_data[COMPANY_BOOKING_FIELD][ECompanyFields.SMALL_BUSINESS_REGULATION]:
                    f_gross = net_price  # income for small business regulation is net = gross
                else:
                    f_gross = round(net_price * (1 + (self.default_tax_rate / 100)), 2)
                self.dsb_gross.setValue(f_gross)
                self.b_gross_changed = False
        else:
            self.b_net_changed = False
        self.set_vat_rate()

    def set_vat_rate(self) -> None:
        """!
        @brief Set VAT rate.
        """
        gross = self.dsb_gross.value()
        net = self.dsb_net.value()
        vat_rate = calc_vat_rate(gross, net)
        self.le_tax.setText(str(vat_rate))

    def on_payed_changed(self, state: bool) -> None:
        """!
        @brief Payed setting changed. Update visibility of payed date and bar widget.
        @param state : payed state
        """
        if state:
            self.de_payment_date.show()
            self.lbl_payment_date.show()
            self.cb_bar_check.show()
            self.lbl_bar_check.show()
        else:
            self.de_payment_date.hide()
            self.lbl_payment_date.hide()
            self.cb_bar_check.hide()
            self.lbl_bar_check.hide()

    def on_invoice_data_changed(self, date: QDate) -> None:
        """!
        @brief Invoice date changed.
        @param date : date
        """
        if not self.b_pay_data_changed:
            self.b_lock_auto_payed_data = True
            self.de_payment_date.setDate(date)

    def on_pay_data_changed(self, _date: QDate) -> None:
        """!
        @brief Pay date changed.
        @param _date : date
        """
        if self.b_lock_auto_payed_data:
            self.b_lock_auto_payed_data = False
        else:
            self.b_pay_data_changed = True

    def show_group_dialog(self) -> None:
        """!
        @brief Shows the dialog for selection of the group
        """
        d_receipt_group = {}
        for key, _value in D_RECEIPT_GROUP.items():
            d_receipt_group[str(key.value)] = str(key.value)
        l_group = self.ui.tab_settings.company_data[COMPANY_DEFAULT_FIELD][ECompanyFields.GROUPS]
        for group in l_group:
            if group not in d_receipt_group:
                d_receipt_group[group] = group
        dialog = GroupDialog(self.ui, d_receipt_group, self.le_group)
        dialog.exec()

    def delete_clicked(self) -> None:
        """!
        @brief Delete button clicked.
        """
        if self.uid is not None:
            match self.receipt_type:
                case EReceiptType.INCOME:
                    delete_income(self.ui.model.data_path, self.uid)
                case EReceiptType.EXPENDITURE:
                    delete_expenditure(self.ui.model.data_path, self.uid)
                case _:
                    pass
            self.ui.set_status(f"{self.receipt_type.value} gelöscht")
            self.close()
        else:
            log.warning("Delete file clicked without UID")

    def save_clicked(self) -> None:
        """!
        @brief Save button clicked.
        """
        valid = self.set_data()
        if valid:
            if self.data is not None:
                match self.receipt_type:
                    case EReceiptType.INCOME:
                        export_income(self.ui.model.data_path, self.ui.model.git_add, self.data, self.uid, self.file_path)
                    case EReceiptType.EXPENDITURE:
                        export_expenditure(self.ui.model.data_path, self.ui.model.git_add, self.data, self.uid, self.file_path)
                    case _:
                        pass
                if self.uid is None:
                    self.ui.set_status(f"{self.receipt_type.value} hinzugefügt")
                else:
                    self.ui.set_status(f"{self.receipt_type.value} gespeichert")
                self.close()
            else:
                log.warning("Save file clicked without data")

    def set_data(self) -> bool:
        """!
        @brief Set receipt data.
        @return status if contact data are valid to save
        """
        valid = False
        trade_partner = self.pte_trade_partner.toPlainText()
        description = self.pte_description.toPlainText()
        attachment = self.data.get(EReceiptFields.ATTACHMENT) if (self.data is not None) else None
        gross_price = self.dsb_gross.value()
        if gross_price % 1 == 0:
            gross_price = int(gross_price)
        net_price = self.dsb_net.value()
        if net_price % 1 == 0:
            net_price = int(net_price)
        # reset sheet style before set new
        self.pte_description.setStyleSheet("border: 1px solid palette(dark);")
        self.pte_description.setStyleSheet("border: 1px solid palette(dark);")
        self.dsb_gross.setStyleSheet("border: 1px solid palette(dark);")
        self.dsb_net.setStyleSheet("border: 1px solid palette(dark);")
        if gross_price is None:
            self.dsb_gross.setStyleSheet("border: 2px solid red;")
            self.ui.set_status("Kein Brutto Betrag vorhanden.", b_highlight=True)
        elif net_price is None:
            self.dsb_net.setStyleSheet("border: 2px solid red;")
            self.ui.set_status("Kein Netto Betrag vorhanden.", b_highlight=True)
        elif gross_price < 0:
            self.dsb_gross.setStyleSheet("border: 2px solid red;")
            self.ui.set_status("Brutto Betrag darf nicht negativ sein.", b_highlight=True)
        elif net_price < 0:
            self.dsb_net.setStyleSheet("border: 2px solid red;")
            self.ui.set_status("Netto Betrag darf nicht negativ sein.", b_highlight=True)
        elif net_price > gross_price:
            self.dsb_gross.setStyleSheet("border: 2px solid red;")
            self.dsb_net.setStyleSheet("border: 2px solid red;")
            self.ui.set_status("Netto Betrag darf Brutto nicht übersteigen.", b_highlight=True)
        elif trade_partner or description:
            self.data = copy.deepcopy(D_RECEIPT_TEMPLATE)
            self.data[EReceiptFields.TRADE_PARTNER] = trade_partner
            self.data[EReceiptFields.DESCRIPTION] = description
            self.data[EReceiptFields.INVOICE_NUMBER] = self.le_invoice_number.text()
            self.data[EReceiptFields.INVOICE_DATE] = self.de_invoice_date.date().toString(DATE_FORMAT)
            self.data[EReceiptFields.DELIVER_DATE] = self.le_deliver_date.text()
            self.data[EReceiptFields.AMOUNT_GROSS] = gross_price
            self.data[EReceiptFields.AMOUNT_NET] = net_price
            if self.cb_pay_check.isChecked():
                self.data[EReceiptFields.PAYMENT_DATE] = self.de_payment_date.date().toString(DATE_FORMAT)
                self.data[EReceiptFields.BAR] = self.cb_bar_check.isChecked()
            else:
                self.data[EReceiptFields.PAYMENT_DATE] = ""
                self.data[EReceiptFields.BAR] = False
            self.data[EReceiptFields.COMMENT] = self.pte_comment.toPlainText()
            self.data[EReceiptFields.GROUP] = self.le_group.text()
            self.data[EReceiptFields.ATTACHMENT] = attachment
            valid = True
        else:
            self.pte_trade_partner.setStyleSheet("border: 2px solid red;")
            self.pte_description.setStyleSheet("border: 2px solid red;")
            self.ui.set_status("Weder Handelspartner noch Beschreibung vorhanden.", b_highlight=True)
        return valid


class GroupDialog(QDialog):
    """!
    @brief Get dialog with list of receipt group
    @param main_window_controller : the main window controller, needed to display status bar updates for example
    @param groups : possible group options
    @param line_edit : the QLineEdit from where this dialog was called
    """

    def __init__(self, main_window_controller: "MainWindow", groups: dict[str, str], line_edit: QLineEdit) -> None:
        super().__init__()
        self.setWindowTitle("Wähle eine Kategorie")
        layout = QVBoxLayout()
        self.controller = main_window_controller
        current_define = line_edit.text()

        # ComboBox with group options
        self.group_options = {}
        current_text = ""
        for name, _description in groups.items():
            display_text = name
            self.group_options[display_text] = name
            if name == current_define:
                current_text = display_text
        self.group_dropdown = QComboBox()
        self.group_dropdown.addItems(self.group_options.keys())
        self.group_dropdown.setCurrentText(current_text)
        layout.addWidget(self.group_dropdown)

        # select button
        copy_button = QPushButton("Auswählen")
        copy_button.clicked.connect(lambda: self.on_select_group(line_edit))
        layout.addWidget(copy_button)

        self.setLayout(layout)

    def on_select_group(self, line_edit: QLineEdit) -> None:
        """!
        @brief "Select" button callback to copy the dropdown define to the line edit
        @param line_edit : QLineEdit to copy the define name to
        """
        selected_value = self.group_dropdown.currentText()
        waiting_time_define = self.group_options[selected_value]
        line_edit.setText(waiting_time_define)
        self.close()
