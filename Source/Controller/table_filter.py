"""!
********************************************************************************
@file   table_filter.py
@brief  Table filter controller: Manages tabular data display, filtering, and context menus
********************************************************************************
"""

import os
import logging
from typing import NamedTuple, Callable, TYPE_CHECKING, Any
from enum import Enum

from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt, QDate, QPoint, QObject, QEvent, QModelIndex
from PyQt6.QtWidgets import QHeaderView, QAbstractItemView, QTabWidget, QMenu, QLabel
from PyQt6.QtGui import QIcon, QMouseEvent, QShortcut, QKeySequence, QAction, QStandardItemModel, QStandardItem

from Source.version import __title__
from Source.Util.app_data import ICON_ATTACH_LIGHT, ICON_ATTACH_DARK, ICON_PDF_LIGHT, ICON_PDF_DARK, ICON_XML_LIGHT, ICON_XML_DARK, \
    ICON_DELETE_LIGHT, ICON_DELETE_DARK, IMG_DROP_FILE, write_table_column, read_table_column, ICON_CONFIG_LIGHT, ICON_CONFIG_DARK, \
    open_explorer, ICON_OPEN_FOLDER_LIGHT, ICON_OPEN_FOLDER_DARK, ICON_INVOICE_LIGHT, ICON_INVOICE_DARK
from Source.Model.data_handler import DATE_FORMAT, PDF_TYPE, XML_TYPE
from Source.Views.tabs.tab_table_filter_ui import Ui_TableFilter
if TYPE_CHECKING:
    from Source.Controller.main_window import MainWindow

ATTACH = "Anhang"
DESCRIPTION = "Beschreibung"
DATE = "Datum"
INVOICE_NUMBER = "Re-Nr."
RECEIPT_ROW_DESCRIPTION = ["Status", "Zahldatum", DATE, INVOICE_NUMBER, "Lieferdatum", "Gruppe", ATTACH, "Handelspartner", DESCRIPTION, "Kommentar", "Netto", "Brutto", "ID"]
ATTACH_IDX = RECEIPT_ROW_DESCRIPTION.index(ATTACH)
DESCRIPTION_IDX = RECEIPT_ROW_DESCRIPTION.index(DESCRIPTION)
DATE_IDX = RECEIPT_ROW_DESCRIPTION.index(DATE)
INVOICE_NUMBER_IDX = RECEIPT_ROW_DESCRIPTION.index(INVOICE_NUMBER)

DEFAULT_COLUMN_STATUS = {
    # receipt
    "Zahldatum": False,
    INVOICE_NUMBER: True,
    "Lieferdatum": False,
    "Gruppe": False,
    "Kommentar": False,
    ATTACH: True,
    "Netto": False,
    "Brutto": True,
    # contacts
    "Kontaktperson": True,
    "E-Mail": True
}

log = logging.getLogger(__title__)


class DropFilter(QObject):
    """!
    @brief Drop filter for drag-and-drop imports.
    @param label : QLabel to accept drops.
    @param callback : Callback function to handle dropped file path.
    """

    def __init__(self, label: QLabel, callback: Callable[[str], None]) -> None:
        super().__init__()
        self.label = label
        self.callback = callback
        self.label.setAcceptDrops(True)

    def eventFilter(self, obj: Any, event: Any) -> bool:
        """!
        @brief Filter drag-and-drop events for file import.
        @param obj : Label object.
        @param event : Event to filter.
        @return Whether the event was handled.
        """
        if obj is self.label:
            if event.type() == QEvent.Type.DragEnter:
                if event.mimeData().hasUrls():
                    event.acceptProposedAction()
                    return True
            elif event.type() == QEvent.Type.Drop:
                for url in event.mimeData().urls():
                    file_path = url.toLocalFile()
                    self.callback(file_path)
                event.acceptProposedAction()
                return True
        return False


class CellData(NamedTuple):
    """!
    @brief Container for table cell data.
    """
    text: str = ""
    icon: str | None = None
    right_align: bool = False
    is_date: bool = False


class TableFilter(QtWidgets.QWidget, Ui_TableFilter):
    """!
    @brief General tab for table filtering and display.
    @param ui : main window
    @param tab_widget : QTabWidget containing this tab
    @param tab_idx : Index of this tab in the tab widget
    @param title : Tab display title
    @param title_folder_link : Create folder link on title label.
    @param btn_1_name : name of button 1
    @param btn_1_icon : icon paths of button 1 (light, dark)
    @param btn_1_cb : callback function for button 1
    @param btn_2_name : name of button 2
    @param btn_2_icon : icon paths of button 2 (light, dark)
    @param btn_2_cb : callback function for button 2
    @param btn_3_name : name of button 3
    @param btn_3_icon : icon paths of button 3 (light, dark)
    @param btn_3_cb : callback function for button 3
    @param table_double_click_fnc : callback for double click
    @param table_header : table header
    @param sort_idx : row index to sort table
    @param pre_sort_idx : row index to previous sort table
    @param inverse_sort : table sort direction
    @param row_fill_idx : row index to fill after auto width
    @param delete_fnc : function to delete entry
    @param update_table_func : update table data function
    @param drag_fnc : drag function to import file
    @param column_setting_key : column setting key [KEY_CONTACTS_COLUMN, KEY_DOCUMENT_COLUMN, KEY_INCOME_COLUMN, KEY_EXPENDITURE_COLUMN]
    @param create_invoice : Whether to show the create invoice context menu option.
    """

    def __init__(self, ui: "MainWindow", tab_widget: QTabWidget, tab_idx: int, title: str, title_folder_link: str = "",  # pylint: disable=keyword-arg-before-vararg
                 btn_1_name: str = "", btn_1_icon: tuple[str, str] | None = None, btn_1_cb: Callable[[], None] | None = None,
                 btn_2_name: str = "", btn_2_icon: tuple[str, str] | None = None, btn_2_cb: Callable[[], None] | None = None,
                 btn_3_name: str = "", btn_3_icon: tuple[str, str] | None = None, btn_3_cb: Callable[[], None] | None = None,
                 table_double_click_fnc: Callable[[int, int, str], None] | None = None, table_header: list[str] | None = None,
                 sort_idx: int = 0, pre_sort_idx: int | None = None, inverse_sort: bool = False, row_fill_idx: int = 0,
                 delete_fnc: Callable[[str, str], None] | None = None, update_table_func: Callable[[], None] | None = None,
                 drag_fnc: Callable[[str], None] | None = None,
                 column_setting_key: str | None = None,
                 create_invoice: bool = False,
                 *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.ui = ui
        tab = tab_widget.widget(tab_idx)
        self.setupUi(tab)

        # Shortcuts
        self.shortcut_finde = QShortcut(QKeySequence("Ctrl+F"), tab)
        self.shortcut_finde.activated.connect(self.input_filter.setFocus)
        self.shortcut_esc = QShortcut(QKeySequence("Esc"), tab)
        self.shortcut_esc.activated.connect(lambda: self.set_filter(None))
        if btn_1_cb is not None:
            self.shortcut_new = QShortcut(QKeySequence("Ctrl+N"), tab)
            self.shortcut_new.activated.connect(btn_1_cb)

        self.title_folder_link = title_folder_link
        self.table_double_click_fnc = table_double_click_fnc
        self.table_header = table_header if (table_header is not None) else []
        self.sort_idx = sort_idx
        self.pre_sort_idx = pre_sort_idx
        self.inverse_sort = inverse_sort
        self.row_fill_idx = row_fill_idx
        self.delete_fnc = delete_fnc
        self.update_table_func = update_table_func
        self.drag_fnc = drag_fnc
        self.column_setting_key = column_setting_key
        self.create_invoice = create_invoice
        self.active_filter: str | None = None
        self.table_data: list[list[CellData]] = []

        self.lbl_title.setText(title)
        is_light_theme = self.ui.model.monitor.is_light_theme()
        self.btn_1.setText(btn_1_name)
        self.btn_1.setVisible(bool(btn_1_name))
        self.btn_2.setText(btn_2_name)
        self.btn_2.setVisible(bool(btn_2_name))
        self.btn_3.setText(btn_3_name)
        self.btn_3.setVisible(bool(btn_3_name))
        if btn_1_icon is not None:
            self.btn_1.setIcon(QIcon(btn_1_icon[0] if is_light_theme else btn_1_icon[1]))
        if btn_2_icon is not None:
            self.btn_2.setIcon(QIcon(btn_2_icon[0] if is_light_theme else btn_2_icon[1]))
        if btn_3_icon is not None:
            self.btn_3.setIcon(QIcon(btn_3_icon[0] if is_light_theme else btn_3_icon[1]))

        if title_folder_link:
            self.btn_open_folder.setText("")
            link_path = os.path.join(self.ui.model.data_path, title_folder_link)
            self.btn_open_folder.clicked.connect(lambda: open_explorer(link_path, True))
        else:
            self.btn_open_folder.hide()

        self.table.doubleClicked.connect(self.on_item_double_clicked)
        if btn_1_cb is not None:
            self.btn_1.clicked.connect(btn_1_cb)
        if btn_2_cb is not None:
            self.btn_2.clicked.connect(btn_2_cb)
        if btn_3_cb is not None:
            self.btn_3.clicked.connect(btn_3_cb)

        # filter input dialog
        self.input_filter.setPlaceholderText('Suchtext eingeben (Strg+F)')
        self.input_filter.returnPressed.connect(self.enter_pressed)
        self.input_filter.setClearButtonEnabled(True)

        # clear filter label
        self.lbl_reset_filter.mousePressEvent = self.reset_filter_clicked  # type: ignore
        self.lbl_reset_filter.setEnabled(False)

        # set right click content menu
        if (self.delete_fnc is not None) and (self.update_table_func is not None):
            header = self.table.verticalHeader()
            if header is not None:
                header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
                header.customContextMenuRequested.connect(self.show_context_menu)

        # drag for import label
        if self.drag_fnc is not None:
            self.lbl_drag.setText(f'<img src="{IMG_DROP_FILE}" width="16" height="16"> Zu importierende Datei hierher ziehen')
            self.drop_filter = DropFilter(self.lbl_drag, self.drag_fnc)
            self.lbl_drag.installEventFilter(self.drop_filter)

        # table column_config
        self.column_visibility = {}
        if self.column_setting_key is not None:
            column_setting = read_table_column(self.column_setting_key)
            for column_name, status in DEFAULT_COLUMN_STATUS.items():
                self.column_visibility[column_name] = column_setting.get(column_name, status)

        # table column config button
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(self.table_header)  # set before create menu -> is override later
        if self.column_setting_key is not None:
            self.btn_column.setMenu(self.create_column_menu())
            self.btn_column.setText("")
        else:
            self.btn_column.hide()
        self.column_initial_set = False

    def create_column_menu(self) -> QMenu:
        """!
        @brief Creates the column visibility menu for the config button.
        @return Column visibility menu.
        """
        menu = QMenu(self.ui)
        self.column_actions = []
        for col in range(self.model.columnCount()):
            header = self.model.headerData(col, Qt.Orientation.Horizontal)
            if header in self.column_visibility:
                action = QAction(str(header), self)
                action.setCheckable(True)
                action.setChecked(self.column_visibility[header])
                action.toggled.connect(lambda checked, c=col: self.column_menu_callback(c, checked))
                menu.addAction(action)
                self.column_actions.append(action)
        return menu

    def column_menu_callback(self, col: int, checked: bool) -> None:
        """!
        @brief Handles column show/hide changes and saves them persistently.
        @param col : Column number.
        @param checked : New visibility state.
        """
        self.table.setColumnHidden(col, not checked)  # invert state
        self.column_visibility[self.table_header[col]] = checked
        if self.column_setting_key is not None:
            write_table_column(self.column_setting_key, self.column_visibility)  # store setting persistent after change

    def show_context_menu(self, point: QPoint) -> None:
        """!
        @brief Displays context menu on right-click of a table row.
        @param point : The position of the context menu event that the widget receives.
        """
        class ContextActions(str, Enum):
            """!
            @brief Possible context menu actions.
            """
            ACTION_CREATE_INVOICE = "Rechnung erstellen"
            ACTION_DELETE_ENTRY = "Eintrag löschen"
            ACTION_CUSTOM_FUNCTION = "Stundenliste erstellen"

        index = self.table.indexAt(point)
        if index.isValid():
            is_light_theme = self.ui.model.monitor.is_light_theme()
            menu = QMenu(self.ui)
            if self.create_invoice:
                icon = QIcon(ICON_INVOICE_LIGHT if is_light_theme else ICON_INVOICE_DARK)
                menu.addAction(icon, ContextActions.ACTION_CREATE_INVOICE.value)
            icon = QIcon(ICON_DELETE_LIGHT if is_light_theme else ICON_DELETE_DARK)
            menu.addAction(icon, ContextActions.ACTION_DELETE_ENTRY.value)
            viewport = self.table.viewport()
            assert viewport is not None
            selected_action = menu.exec(viewport.mapToGlobal(point))
            if selected_action:
                row = index.row()
                model = self.table.model()
                assert model is not None
                uid_index = model.index(row, len(self.table_header) - 1)
                uid = model.data(uid_index, Qt.ItemDataRole.DisplayRole)
                match selected_action.text():
                    case ContextActions.ACTION_CREATE_INVOICE:
                        self.ui.tab_income.create_invoice(uid)
                    case ContextActions.ACTION_DELETE_ENTRY:
                        if (self.delete_fnc is not None) and (self.update_table_func is not None):
                            self.delete_fnc(self.ui.model.data_path, uid)
                            self.update_table_func()
                            self.ui.set_status("Eintrag gelöscht")
                    case ContextActions.ACTION_CUSTOM_FUNCTION:
                        log.warning("Unknown header context menu action selected: %s", selected_action.text())
                    case _:
                        log.warning("Unknown header context menu action selected: %s", selected_action.text())

    def get_attach_icon(self, attachment_file: str) -> str:
        """!
        @brief Returns icon path depending on attachment type (PDF, XML, other).
        @param attachment_file : Attachment file name.
        @return Attachment icon path.
        """
        file_name = attachment_file.lower()
        if file_name.endswith(PDF_TYPE):
            attach_icon = ICON_PDF_LIGHT if self.ui.model.monitor.is_light_theme() else ICON_PDF_DARK
        elif file_name.endswith(XML_TYPE):
            attach_icon = ICON_XML_LIGHT if self.ui.model.monitor.is_light_theme() else ICON_XML_DARK
        else:
            attach_icon = ICON_ATTACH_LIGHT if self.ui.model.monitor.is_light_theme() else ICON_ATTACH_DARK
        return attach_icon

    def check_entry_relevant(self, data: list[CellData]) -> bool:
        """!
        @brief Returns True if the row matches the active filter.
        @param data : Row data to check against the active filter.
        @return Whether the entry matches the filter.
        """
        if self.active_filter:
            filter_text = self.active_filter.lower()
            return any(filter_text in str(item.text).lower() for item in data[:-1])  # exclude UID
        return True

    def update_table(self, table_data: list[list[CellData]] | None = None) -> None:
        """!
        @brief Updates the table model, applies filters, resizing, sorting, and column visibility.
        @param table_data : Optional new table data to display.
        """
        if table_data is not None:  # optional update data
            self.table_data = table_data

        # config header
        table = self.table
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)  # only one line can select

        # set model
        model = QStandardItemModel()  # set again to delete old entries before set new
        self.model = model
        model.setColumnCount(len(self.table_header))
        table.setModel(model)

        table.setAlternatingRowColors(True)

        # insert items
        idx = 0
        for data in self.table_data:
            if self.check_entry_relevant(data):
                items = []
                for i, cell_data in enumerate(data):
                    text = cell_data.text
                    if text is not None:
                        if len(text) < 50:
                            text = text.replace("\n", " ")
                    item = QStandardItem(text)
                    if cell_data.icon is not None:
                        item.setIcon(QIcon(cell_data.icon))
                    alignment = Qt.AlignmentFlag.AlignRight if cell_data.right_align else Qt.AlignmentFlag.AlignLeft
                    item.setTextAlignment(alignment | Qt.AlignmentFlag.AlignVCenter)
                    if cell_data.is_date:
                        item.setData(QDate.fromString(cell_data.text, DATE_FORMAT), Qt.ItemDataRole.DisplayRole)
                    items.append(item)
                model.appendRow(items)
                idx += 1

        if self.active_filter:
            if idx == 0:
                color = "red"
            elif len(self.table_data) == idx:
                color = "green"
            else:
                color = "orange"
        else:
            color = None
        self.set_search_border(color)

        # set header before auto size so resizeColumnsToContents includes header text width
        attach_icon = ICON_ATTACH_LIGHT if self.ui.model.monitor.is_light_theme() else ICON_ATTACH_DARK
        for i, value in enumerate(self.table_header):
            if value == ATTACH:
                model.setHeaderData(i, Qt.Orientation.Horizontal, QIcon(attach_icon), Qt.ItemDataRole.DecorationRole)
            else:
                model.setHeaderData(i, Qt.Orientation.Horizontal, value)

        # set auto width (disable sorting so sort indicator arrow does not affect column width)
        table.setSortingEnabled(False)
        table.resizeColumnsToContents()
        header = table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(self.row_fill_idx, QHeaderView.ResizeMode.Stretch)
            header.setVisible(True)

        # sort table
        sort_dir = Qt.SortOrder.AscendingOrder if self.inverse_sort else Qt.SortOrder.DescendingOrder
        if self.pre_sort_idx is not None:
            table.sortByColumn(self.pre_sort_idx, sort_dir)
        table.sortByColumn(self.sort_idx, sort_dir)
        table.setSortingEnabled(True)

        # update icon here for light/dark mode
        self.btn_column.setIcon(QIcon(ICON_CONFIG_LIGHT if self.ui.model.monitor.is_light_theme() else ICON_CONFIG_DARK))
        self.btn_open_folder.setIcon(QIcon(ICON_OPEN_FOLDER_LIGHT if self.ui.model.monitor.is_light_theme() else ICON_OPEN_FOLDER_DARK))

        # set column status initial after update data
        if not self.column_initial_set:  # TODO warum erst nach Aufruf von update_table
            self.column_initial_set = True
            for col in range(self.model.columnCount()):
                col_header = self.model.headerData(col, Qt.Orientation.Horizontal)
                if col_header is None:
                    col_header = ATTACH  # map None to ATTACH
                if col_header in self.column_visibility:
                    visible = self.column_visibility[col_header]
                    self.table.setColumnHidden(col, not visible)

    def on_item_double_clicked(self, index: QModelIndex) -> None:
        """!
        @brief Calls the double-click callback with row, column, and value.
        @param index : QModelIndex of the clicked cell.
        """
        row = index.row()
        col = index.column()
        value = index.data(Qt.ItemDataRole.DisplayRole)

        if self.table_double_click_fnc is not None:
            self.table_double_click_fnc(row, col, value)

    def enter_pressed(self) -> None:
        """!
        @brief Filters table on Enter pressed in search box.
        """
        text = self.input_filter.text()
        self.set_filter(text)

    def reset_filter_clicked(self, _event: QMouseEvent) -> None:
        """!
        @brief Reset the search filter and show all table rows.
        @param _event : Mouse click event.
        """
        self.set_filter(None)

    def set_search_border(self, color: str | None) -> None:
        """!
        @brief Sets the border color of the search input (green/orange/red).
        @param color : Border color to set.
        """
        if color is None:
            self.input_filter.setStyleSheet("border: 1px solid palette(dark);")  # "" or None do not work since new pyqt6 version
        else:
            self.input_filter.setStyleSheet(f"border: 2px solid {color};")

    def set_filter(self, filter_text: str | None) -> None:
        """!
        @brief Activates or clears the text filter and refreshes the table.
        @param filter_text : Filter text to apply.
        """
        if filter_text:
            self.active_filter = filter_text
            self.lbl_reset_filter.setEnabled(True)
        else:
            self.active_filter = None
            self.input_filter.clear()
            self.lbl_reset_filter.setEnabled(False)
        self.update_table()
