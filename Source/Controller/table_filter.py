"""!
********************************************************************************
@file   table_filter.py
@brief  Table filter controller
********************************************************************************
"""

import os
import logging
from typing import NamedTuple, Callable, Optional, TYPE_CHECKING, Any
from enum import Enum

from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt, QDate, QPoint, QObject, QEvent, QModelIndex
from PyQt6.QtWidgets import QHeaderView, QAbstractItemView, QTabWidget, QMenu, QLabel
from PyQt6.QtGui import QIcon, QMouseEvent, QShortcut, QKeySequence, QAction, QStandardItemModel, QStandardItem

from Source.version import __title__
from Source.Util.app_data import ICON_ATTACH_LIGHT, ICON_ATTACH_DARK, ICON_PDF_LIGHT, ICON_PDF_DARK, ICON_XML_LIGHT, ICON_XML_DARK, \
    ICON_DELETE_LIGHT, ICON_DELETE_DARK, IMG_DROP_FILE, write_table_column, read_table_column, ICON_CONFIG_LIGHT, ICON_CONFIG_DARK, \
    open_explorer, ICON_OPEN_FOLDER_LIGHT, ICON_OPEN_FOLDER_DARK
from Source.Model.data_handler import DATE_FORMAT, PDF_TYPE, XML_TYPE
from Source.Views.tabs.tab_table_filter_ui import Ui_TableFilter
if TYPE_CHECKING:
    from Source.Controller.main_window import MainWindow

ATTACH = "Anhang"
DESCRIPTION = "Beschreibung"
DATE = "Datum"
INVOICE_NUMBER = "Re-Nr."
L_RECEIPT_ROW_DESCRIPTION = ["Status", "Zahldatum", DATE, INVOICE_NUMBER, "Lieferdatum", "Gruppe", ATTACH, "Handelspartner", DESCRIPTION, "Kommentar", "Netto", "Brutto", "ID"]
I_ATTACH_IDX = L_RECEIPT_ROW_DESCRIPTION.index(ATTACH)
I_DESCRIPTION_IDX = L_RECEIPT_ROW_DESCRIPTION.index(DESCRIPTION)
I_DATE_IDX = L_RECEIPT_ROW_DESCRIPTION.index(DATE)
I_INVOICE_NUMBER_IDX = L_RECEIPT_ROW_DESCRIPTION.index(INVOICE_NUMBER)

D_DEFAULT_COLUMN_STATUS = {
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
    @brief Drop filter for import
    @param label : label object
    @param callback : callback function
    """

    def __init__(self, label: QLabel, callback: Callable[[str], None]) -> None:
        super().__init__()
        self.label = label
        self.callback = callback
        self.label.setAcceptDrops(True)

    def eventFilter(self, obj: Any, event: Any) -> bool:
        """!
        @brief Drop filter for import
        @param obj : label object
        @param event : event
        @return drop status
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
    @brief properties of printed article
    """
    text: str = ""
    icon: str | None = None
    right_align: bool = False
    is_date: bool = False


class TableFilter(QtWidgets.QWidget, Ui_TableFilter):
    """!
    @brief General Filter Tab.
    @param ui : main window
    @param tab_widget : tab widget
    @param tab_idx : tab index
    @param s_title : tab name
    @param title_folder_link : create folder link on title lable
    @param btn_1_name : name of button 1
    @param btn_1_cb : callback function for button 1
    @param btn_2_name : name of button 2
    @param btn_2_cb : callback function for button 2
    @param btn_3_name : name of button 3
    @param btn_3_cb : callback function for button 3
    @param table_double_click_fnc : callback for double click
    @param l_table_header : table header
    @param sort_idx : row index to sort table
    @param pre_sort_idx : row index to previous sort table
    @param inverse_sort : table sort direction
    @param row_fill_idx : row index to fill after auto width
    @param delete_fnc : function to delete entry
    @param update_table_func : update table data function
    @param drag_fnc : drag function to import file
    @param column_setting_key : column setting key [S_KEY_CONTACTS_COLUMN, S_KEY_DOCUMENT_COLUMN, S_KEY_INCOME_COLUMN, S_KEY_EXPENDITURE_COLUMN]
    """

    def __init__(self, ui: "MainWindow", tab_widget: QTabWidget, tab_idx: int, s_title: str, title_folder_link: str = "",  # pylint: disable=keyword-arg-before-vararg
                 btn_1_name: str = "", btn_1_cb: Optional[Callable[[], None]] = None,
                 btn_2_name: str = "", btn_2_cb: Optional[Callable[[], None]] = None,
                 btn_3_name: str = "", btn_3_cb: Optional[Callable[[], None]] = None,
                 table_double_click_fnc: Optional[Callable[[int, int, str], None]] = None, l_table_header: Optional[list[str]] = None,
                 sort_idx: int = 0, pre_sort_idx: Optional[int] = None, inverse_sort: bool = False, row_fill_idx: int = 0,
                 delete_fnc: Optional[Callable[[str], None]] = None, update_table_func: Optional[Callable[[], None]] = None,
                 drag_fnc: Optional[Callable[[str], None]] = None,
                 column_setting_key: Optional[str] = None,
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
        self.l_table_header = l_table_header if (l_table_header is not None) else []
        self.sort_idx = sort_idx
        self.pre_sort_idx = pre_sort_idx
        self.inverse_sort = inverse_sort
        self.row_fill_idx = row_fill_idx
        self.delete_fnc = delete_fnc
        self.update_table_func = update_table_func
        self.drag_fnc = drag_fnc
        self.column_setting_key = column_setting_key
        self.active_filter: str | None = None
        self.l_data: list[list[CellData]] = []

        self.lbl_title.setText(s_title)
        self.btn_1.setText(btn_1_name)
        self.btn_1.setVisible(bool(btn_1_name))
        self.btn_2.setText(btn_2_name)
        self.btn_2.setVisible(bool(btn_2_name))
        self.btn_3.setText(btn_3_name)
        self.btn_3.setVisible(bool(btn_3_name))

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
        self.d_column = {}
        if self.column_setting_key is not None:
            d_column_setting = read_table_column(self.column_setting_key)
            for column_name, status in D_DEFAULT_COLUMN_STATUS.items():
                self.d_column[column_name] = d_column_setting.get(column_name, status)

        # table column config button
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(self.l_table_header)  # set before create menu -> is override later
        if self.column_setting_key is not None:
            self.btn_column.setMenu(self.create_column_menu())
            self.btn_column.setText("")
        else:
            self.btn_column.hide()
        self.b_column_initial_set = False

    def create_column_menu(self) -> QMenu:
        """!
        @brief Create column menu for button
        @return menu
        """
        menu = QMenu(self.ui)
        self.column_actions = []
        for col in range(self.model.columnCount()):
            header = self.model.headerData(col, Qt.Orientation.Horizontal)
            if header in self.d_column:
                action = QAction(str(header), self)
                action.setCheckable(True)
                action.setChecked(self.d_column[header])
                action.toggled.connect(lambda checked, c=col: self.column_menu_callback(c, checked))
                menu.addAction(action)
                self.column_actions.append(action)
        return menu

    def column_menu_callback(self, col: int, checked: bool) -> None:
        """!
        @brief Handles right click to pop up context menu
        @param col : column number
        @param checked : last check status
        """
        self.table.setColumnHidden(col, not checked)  # invert state
        self.d_column[self.l_table_header[col]] = checked
        write_table_column(self.column_setting_key, self.d_column)  # store setting persistent after change

    def show_context_menu(self, point: QPoint) -> None:
        """!
        @brief Handles right click to pop up context menu
        @param point : The position of the context menu event that the widget receives.
        """
        class ContextActions(str, Enum):
            """!
            @brief Possible context menu actions
            """
            ACTION_DELETE_ENTRY = "Eintrag löschen"

        index = self.table.indexAt(point)
        if index.isValid():
            menu = QMenu(self.ui)
            icon = QIcon(ICON_DELETE_LIGHT if self.ui.model.c_monitor.is_light_theme() else ICON_DELETE_DARK)
            menu.addAction(icon, ContextActions.ACTION_DELETE_ENTRY.value)
            selected_action = menu.exec(self.table.viewport().mapToGlobal(point))
            if selected_action:
                row = index.row()
                model = self.table.model()
                uid_index = model.index(row, len(self.l_table_header) - 1)
                uid = model.data(uid_index, Qt.ItemDataRole.DisplayRole)
                match selected_action.text():
                    case ContextActions.ACTION_DELETE_ENTRY:
                        if (self.delete_fnc is not None) and (self.update_table_func is not None):
                            self.delete_fnc(self.ui.model.data_path, uid)
                            self.update_table_func()
                            self.ui.set_status("Eintrag gelöscht")
                    case _:
                        log.warning("Unknown header context menu action selected: %s", selected_action.text())

    def get_attach_icon(self, attachment_file: str) -> str:
        """!
        @brief Get attachment icon depend on file type.
        @param attachment_file : attachment name
        @return attachment icon
        """
        file_name = attachment_file.lower()
        if file_name.lower().endswith(PDF_TYPE.lower()):
            attach_icon = ICON_PDF_LIGHT if self.ui.model.c_monitor.is_light_theme() else ICON_PDF_DARK
        elif file_name.lower().endswith(XML_TYPE.lower()):
            attach_icon = ICON_XML_LIGHT if self.ui.model.c_monitor.is_light_theme() else ICON_XML_DARK
        else:
            attach_icon = ICON_ATTACH_LIGHT if self.ui.model.c_monitor.is_light_theme() else ICON_ATTACH_DARK
        return attach_icon

    def check_entry_relevant(self, data: list[CellData]) -> bool:
        """!
        @brief Check if table item is in filter option.
        @param data : data to check for relevant at search
        @return status if entry is relevant for search
        """
        if self.active_filter:
            filter_text = self.active_filter.lower()
            l_filter_data = []
            for item in data[:-1]:  # do not use lase element it is UID
                l_filter_data.append(item.text)
            relevant = False
            for text in l_filter_data:
                if filter_text in str(text).lower():
                    relevant = True
                    break
            else:
                relevant = False
        else:
            relevant = True
        return relevant

    def update_table(self, l_data: Optional[list[list[CellData]]] = None) -> None:
        """!
        @brief Update table view.
        @param l_data : optional to update with new table data
        """
        if l_data is not None:  # optional update data
            self.l_data = l_data

        # config header
        table = self.table
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)  # only one line can select

        # set model
        model = QStandardItemModel()  # set again to delete old entries before set new
        self.model = model
        model.setColumnCount(len(self.l_table_header))
        table.setModel(model)

        table.setAlternatingRowColors(True)

        # insert items
        idx = 0
        for data in self.l_data:
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
            elif len(self.l_data) == idx:
                color = "green"
            else:
                color = "orange"
        else:
            color = None
        self.set_search_boarder(color)

        # set auto width
        table.resizeColumnsToContents()  # auto column width
        header = table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(self.row_fill_idx, QHeaderView.ResizeMode.Stretch)
            header.setVisible(True)

        # set header after auto size
        attach_icon = ICON_ATTACH_LIGHT if self.ui.model.c_monitor.is_light_theme() else ICON_ATTACH_DARK
        for i, value in enumerate(self.l_table_header):
            if value == ATTACH:
                model.setHeaderData(i, Qt.Orientation.Horizontal, QIcon(attach_icon), Qt.ItemDataRole.DecorationRole)
            else:
                model.setHeaderData(i, Qt.Orientation.Horizontal, value)

        # sort table
        sort_dir = Qt.SortOrder.AscendingOrder if self.inverse_sort else Qt.SortOrder.DescendingOrder
        if self.pre_sort_idx is not None:
            table.sortByColumn(self.pre_sort_idx, sort_dir)
        table.sortByColumn(self.sort_idx, sort_dir)
        table.setSortingEnabled(True)

        # update icon here for light/dark mode
        self.btn_column.setIcon(QIcon(ICON_CONFIG_LIGHT if self.ui.model.c_monitor.is_light_theme() else ICON_CONFIG_DARK))
        self.btn_open_folder.setIcon(QIcon(ICON_OPEN_FOLDER_LIGHT if self.ui.model.c_monitor.is_light_theme() else ICON_OPEN_FOLDER_DARK))

        # set column status initial after update data
        if not self.b_column_initial_set:  # TODO warum erst nach Aufruf von update_table
            self.b_column_initial_set = True
            for col in range(self.model.columnCount()):
                header = self.model.headerData(col, Qt.Orientation.Horizontal)
                if header is None:
                    header = ATTACH  # map None to ATTACH
                if header in self.d_column:
                    visible = self.d_column[header]
                    self.table.setColumnHidden(col, not visible)

    def on_item_double_clicked(self, index: QModelIndex) -> None:
        """!
        @brief Double click callback for QTableView.
        @param index : QModelIndex of the clicked cell
        """
        row = index.row()
        col = index.column()
        value = index.data(Qt.ItemDataRole.DisplayRole)

        if self.table_double_click_fnc is not None:
            self.table_double_click_fnc(row, col, value)

    def enter_pressed(self) -> None:
        """!
        @brief Enter pressed to filter table.
        """
        text = self.input_filter.text()
        self.set_filter(text)

    def reset_filter_clicked(self, _event: QMouseEvent) -> None:
        """!
        @brief Reset filter clicked.
        @param _event : call event
        """
        self.set_filter(None)

    def set_search_boarder(self, color: Optional[str]) -> None:
        """!
        @brief Set border of search widget.
        @param color : color to set
        """
        if color is None:
            self.input_filter.setStyleSheet("")
        else:
            self.input_filter.setStyleSheet(f"border: 2px solid {color};")

    def set_filter(self, filter_text: Optional[str]) -> None:
        """!
        @brief Set filter.
        @param filter_text : filter text
        """
        if filter_text:
            self.active_filter = filter_text
            self.lbl_reset_filter.setEnabled(True)
        else:
            self.active_filter = None
            self.input_filter.clear()
            self.lbl_reset_filter.setEnabled(False)
        self.update_table()
