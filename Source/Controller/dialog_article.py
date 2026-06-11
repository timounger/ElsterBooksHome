"""!
********************************************************************************
@file   dialog_article.py
@brief  Dialog for selecting, creating, editing, and deleting article templates.
********************************************************************************
"""

import copy
import logging
from typing import Any, TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, \
    QDoubleSpinBox, QPlainTextEdit, QComboBox, QGroupBox, QGridLayout, QMessageBox, \
    QTabWidget, QWidget

from Source.Util.app_data import read_beverage_mode
from Source.Model.article import EArticleFields, ARTICLE_TEMPLATE, read_articles, add_article, remove_article
from Source.Model.company import ECompanyFields, COMPANY_BOOKING_FIELD
from Source.Model.ZUGFeRD.drafthorse_data import UNIT, VAT_CODE
from Source.Model.ZUGFeRD.drafthorse_import import set_combo_box_items
from Source.Controller.table_filter import TableFilter, CellData

if TYPE_CHECKING:
    from Source.Controller.main_window import MainWindow

log = logging.getLogger(__name__)


ARTICLE_ROW_DESCRIPTION = ["Artikel-Nr.", "Name", "Netto-Preis", "Einheit", "USt.-%", "Gebinde", "Pfand", "ID"]
ARTICLE_NAME_IDX = 1


class ArticleSelectDialog(QDialog):
    """!
    @brief Dialog for selecting an article template to fill into an invoice item.
    """

    def __init__(self, ui: "MainWindow", select_mode: bool = False) -> None:
        """!
        @brief Initialize article selection dialog.
        @param ui : main window reference.
        @param select_mode : True for article selection (invoice), False for management only (settings).
        """
        super().__init__(parent=ui)
        self.ui = ui
        self.select_mode = select_mode
        self.selected_article: dict[EArticleFields, Any] | None = None
        self.articles: list[dict[EArticleFields, Any]] = []
        self._setup_ui()
        self._load_articles()

    def _setup_ui(self) -> None:
        """!
        @brief Build the dialog layout using TableFilter for consistent look and search.
        """
        self.setWindowTitle("Artikel auswählen" if self.select_mode else "Artikel verwalten")
        self.setMinimumSize(700, 400)
        layout = QVBoxLayout(self)

        # create a container tab widget for TableFilter
        self._tab_widget = QTabWidget()
        self._tab_widget.addTab(QWidget(), "")
        self._tab_widget.tabBar().hide()

        double_click_fn = self._on_double_click_select if self.select_mode else self._on_double_click_edit
        self.table_filter = TableFilter(
            self.ui, self._tab_widget, 0,
            title="Artikel auswählen" if self.select_mode else "Artikel verwalten",
            btn_1_name="Neu",
            btn_1_cb=self._new_article,
            btn_2_name="Bearbeiten",
            btn_2_cb=self._edit_article,
            btn_3_name="Löschen",
            btn_3_cb=self._delete_article,
            table_double_click_fnc=double_click_fn,
            table_header=ARTICLE_ROW_DESCRIPTION,
            sort_idx=ARTICLE_NAME_IDX,
            inverse_sort=True,
            row_fill_idx=ARTICLE_NAME_IDX,
            delete_fnc=self._delete_by_uid,
            update_table_func=self._load_articles,
        )
        self.table_filter.btn_open_folder.hide()
        self.table_filter.lbl_drag.hide()
        layout.addWidget(self._tab_widget)

        # bottom buttons
        if self.select_mode:
            btn_layout = QHBoxLayout()
            btn_layout.addStretch()
            self.btn_select = QPushButton("Übernehmen")
            self.btn_select.clicked.connect(self._accept_selection)
            btn_layout.addWidget(self.btn_select)
            btn_close = QPushButton("Schließen")
            btn_close.clicked.connect(self.reject)
            btn_layout.addWidget(btn_close)
            layout.addLayout(btn_layout)

    def _load_articles(self) -> None:
        """!
        @brief Load articles from disk and populate the table.
        """
        self.articles = read_articles(self.ui.model.data_path)
        is_beverage = read_beverage_mode()
        rows = []
        for article in self.articles:
            deposit = article[EArticleFields.DEPOSIT]
            row = [
                CellData(text=str(article[EArticleFields.ARTICLE_ID])),
                CellData(text=str(article[EArticleFields.NAME])),
                CellData(text=f"{article[EArticleFields.NET_UNIT_PRICE]:.2f}", right_align=True, sort_value=article[EArticleFields.NET_UNIT_PRICE]),
                CellData(text=str(UNIT.get(article[EArticleFields.QUANTITY_UNIT], article[EArticleFields.QUANTITY_UNIT]))),
                CellData(text=f"{article[EArticleFields.VAT_RATE]:.0f}%", right_align=True),
                CellData(text=str(article[EArticleFields.CONTAINER_TYPE])),
                CellData(text=f"{deposit:.2f}" if deposit else "", right_align=True),
                CellData(text=str(article[EArticleFields.ID])),
            ]
            rows.append(row)
        self.table_filter.update_table(rows)
        # hide columns
        self.table_filter.table.setColumnHidden(7, True)  # ID
        if not is_beverage:
            self.table_filter.table.setColumnHidden(5, True)  # Gebinde
            self.table_filter.table.setColumnHidden(6, True)  # Pfand

    def _get_selected_uid(self) -> str | None:
        """!
        @brief Get the UID of the currently selected row.
        @return UID string or None.
        """
        index = self.table_filter.table.currentIndex()
        if not index.isValid():
            return None
        model = self.table_filter.table.model()
        assert model is not None
        uid_index = model.index(index.row(), len(ARTICLE_ROW_DESCRIPTION) - 1)
        return model.data(uid_index, Qt.ItemDataRole.DisplayRole)

    def _get_selected_article(self) -> dict[EArticleFields, Any] | None:
        """!
        @brief Get the currently selected article from the table.
        @return Selected article data or None.
        """
        uid = self._get_selected_uid()
        if uid:
            return next((a for a in self.articles if str(a[EArticleFields.ID]) == uid), None)
        return None

    def _accept_selection(self) -> None:
        """!
        @brief Accept the selected article and close the dialog.
        """
        self.selected_article = self._get_selected_article()
        if self.selected_article is not None:
            self.accept()

    def _on_double_click_select(self, _row: int, _col: int, _value: str) -> None:
        """!
        @brief Handle double-click in select mode - accept the selection.
        @param _row : clicked row index.
        @param _col : clicked column index.
        @param _value : value of clicked cell.
        """
        self._accept_selection()

    def _on_double_click_edit(self, _row: int, _col: int, _value: str) -> None:
        """!
        @brief Handle double-click in manage mode - open edit dialog.
        @param _row : clicked row index.
        @param _col : clicked column index.
        @param _value : value of clicked cell.
        """
        self._edit_article()

    def _new_article(self) -> None:
        """!
        @brief Open article edit dialog for creating a new article.
        """
        dialog = ArticleEditDialog(self.ui, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_articles()

    def _edit_article(self) -> None:
        """!
        @brief Open article edit dialog for editing the selected article.
        """
        article = self._get_selected_article()
        if article is not None:
            dialog = ArticleEditDialog(self.ui, article=article, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self._load_articles()

    def _delete_article(self) -> None:
        """!
        @brief Delete the selected article.
        """
        article = self._get_selected_article()
        if article is not None:
            remove_article(self.ui.model.data_path, article[EArticleFields.ID])
            self._load_articles()

    def _delete_by_uid(self, _path: str, uid: str) -> None:
        """!
        @brief Delete article by UID (for context menu).
        @param _path : unused, provided by TableFilter interface.
        @param uid : article ID to delete.
        """
        remove_article(self.ui.model.data_path, uid)


class ArticleEditDialog(QDialog):
    """!
    @brief Dialog for creating or editing an article template.
    """

    def __init__(self, ui: "MainWindow", article: dict[EArticleFields, Any] | None = None,
                 parent: QWidget | None = None) -> None:
        """!
        @brief Initialize article edit dialog.
        @param ui : main window reference.
        @param article : existing article data for editing, or None for new article.
        @param parent : parent widget.
        """
        super().__init__(parent=parent)
        self.ui = ui
        self.article = article
        self.uid = article[EArticleFields.ID] if article else None
        self._setup_ui()
        if article is not None:
            self._load_data(article)

    def _setup_ui(self) -> None:
        """!
        @brief Build the edit form layout.
        """
        self.setWindowTitle("Artikel bearbeiten" if self.article else "Neuer Artikel")
        self.setMinimumWidth(450)
        layout = QVBoxLayout(self)

        group = QGroupBox("Artikeldaten")
        grid = QGridLayout(group)
        row = 0

        # Name (BT-153)
        grid.addWidget(QLabel("Name:"), row, 0)
        self.le_name = QLineEdit()
        grid.addWidget(self.le_name, row, 1)
        row += 1

        # Artikel-Nr. (BT-155)
        grid.addWidget(QLabel("Artikel-Nr.:"), row, 0)
        self.le_article_id = QLineEdit()
        grid.addWidget(self.le_article_id, row, 1)
        row += 1

        # Beschreibung (BT-154)
        grid.addWidget(QLabel("Beschreibung:"), row, 0)
        self.pte_description = QPlainTextEdit()
        self.pte_description.setMaximumHeight(60)
        grid.addWidget(self.pte_description, row, 1)
        row += 1

        # Netto-Einzelpreis (BT-146)
        grid.addWidget(QLabel("Netto-Einzelpreis:"), row, 0)
        self.dsb_net_price = QDoubleSpinBox()
        self.dsb_net_price.setMaximum(999999.99)
        self.dsb_net_price.setDecimals(2)
        self.dsb_net_price.setSuffix(" €")
        grid.addWidget(self.dsb_net_price, row, 1)
        row += 1

        # Brutto-Einzelpreis (berechnet)
        grid.addWidget(QLabel("Brutto-Einzelpreis:"), row, 0)
        self.dsb_gross_price = QDoubleSpinBox()
        self.dsb_gross_price.setMaximum(999999.99)
        self.dsb_gross_price.setDecimals(2)
        self.dsb_gross_price.setSuffix(" €")
        self.dsb_gross_price.setReadOnly(True)
        self.dsb_gross_price.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        grid.addWidget(self.dsb_gross_price, row, 1)
        row += 1

        # Einheit (BT-130)
        grid.addWidget(QLabel("Einheit:"), row, 0)
        self.combo_unit = QComboBox()
        set_combo_box_items(self.combo_unit, "H87", UNIT)
        grid.addWidget(self.combo_unit, row, 1)
        row += 1

        # Steuersatz (BT-152)
        grid.addWidget(QLabel("Steuersatz:"), row, 0)
        self.dsb_vat_rate = QDoubleSpinBox()
        self.dsb_vat_rate.setMaximum(100.0)
        self.dsb_vat_rate.setDecimals(2)
        self.dsb_vat_rate.setSuffix(" %")
        default_tax_rate = self.ui.tab_settings.company_data[COMPANY_BOOKING_FIELD][ECompanyFields.TAX_RATES][0]
        self.dsb_vat_rate.setValue(default_tax_rate)
        grid.addWidget(self.dsb_vat_rate, row, 1)
        row += 1

        # Steuerkategorie (BT-151)
        grid.addWidget(QLabel("Steuerkategorie:"), row, 0)
        self.combo_vat_code = QComboBox()
        set_combo_box_items(self.combo_vat_code, "S", VAT_CODE)
        grid.addWidget(self.combo_vat_code, row, 1)
        row += 1

        # Gebindeart (nur im Getränkehändler-Modus)
        is_beverage_mode = read_beverage_mode()

        self.lbl_container_type = QLabel("Gebindeart:")
        grid.addWidget(self.lbl_container_type, row, 0)
        self.combo_container_type = QComboBox()
        self.combo_container_type.setEditable(True)
        self.combo_container_type.addItem("")
        # add suggestions from existing articles with deposit values
        self._container_deposits: dict[str, float] = {}
        for a in read_articles(self.ui.model.data_path):
            ct = str(a[EArticleFields.CONTAINER_TYPE])
            deposit = float(a[EArticleFields.DEPOSIT])
            if ct and ct not in self._container_deposits:
                self._container_deposits[ct] = deposit
                self.combo_container_type.addItem(ct)
        self.combo_container_type.currentTextChanged.connect(self._on_container_type_changed)
        grid.addWidget(self.combo_container_type, row, 1)
        row += 1

        self.lbl_deposit = QLabel("Pfand pro Einheit:")
        grid.addWidget(self.lbl_deposit, row, 0)
        self.dsb_deposit = QDoubleSpinBox()
        self.dsb_deposit.setMaximum(999.99)
        self.dsb_deposit.setDecimals(2)
        self.dsb_deposit.setSuffix(" €")
        grid.addWidget(self.dsb_deposit, row, 1)

        if not is_beverage_mode:
            self.lbl_container_type.setVisible(False)
            self.combo_container_type.setVisible(False)
            self.lbl_deposit.setVisible(False)
            self.dsb_deposit.setVisible(False)

        # connect signals for auto gross calculation
        self.dsb_net_price.valueChanged.connect(self._update_gross_price)
        self.dsb_vat_rate.valueChanged.connect(self._update_gross_price)

        layout.addWidget(group)

        # buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_save = QPushButton("Speichern")
        self.btn_save.clicked.connect(self._save)
        btn_layout.addWidget(self.btn_save)
        self.btn_cancel = QPushButton("Abbrechen")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

    def _update_gross_price(self) -> None:
        """!
        @brief Recalculate gross price from net price and VAT rate.
        """
        net = self.dsb_net_price.value()
        vat_rate = self.dsb_vat_rate.value()
        gross = round(net * (1 + vat_rate / 100), 2)
        self.dsb_gross_price.setValue(gross)

    def _on_container_type_changed(self, text: str) -> None:
        """!
        @brief Auto-fill deposit value when a known container type is selected.
        @param text : selected container type.
        """
        if text in self._container_deposits:
            self.dsb_deposit.setValue(self._container_deposits[text])

    def _load_data(self, article: dict[EArticleFields, Any]) -> None:
        """!
        @brief Populate form fields from existing article data.
        @param article : article data dictionary.
        """
        self.le_name.setText(str(article[EArticleFields.NAME]))
        self.le_article_id.setText(str(article[EArticleFields.ARTICLE_ID]))
        self.pte_description.setPlainText(str(article[EArticleFields.DESCRIPTION]))
        vat_rate = float(article[EArticleFields.VAT_RATE])
        if vat_rate > 0:
            self.dsb_vat_rate.setValue(vat_rate)
        self.dsb_net_price.setValue(float(article[EArticleFields.NET_UNIT_PRICE]))
        set_combo_box_items(self.combo_unit, str(article[EArticleFields.QUANTITY_UNIT]), UNIT)
        set_combo_box_items(self.combo_vat_code, str(article[EArticleFields.VAT_CODE]), VAT_CODE)
        container_type = str(article[EArticleFields.CONTAINER_TYPE])
        self.combo_container_type.setCurrentText(container_type)
        self.dsb_deposit.setValue(float(article[EArticleFields.DEPOSIT]))

    def _save(self) -> None:
        """!
        @brief Validate and save the article data.
        """
        name = self.le_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Pflichtfeld", "Bitte einen Artikelnamen eingeben.")
            self.le_name.setFocus()
            return

        data: dict[EArticleFields, Any] = copy.deepcopy(ARTICLE_TEMPLATE)
        data[EArticleFields.NAME] = name
        data[EArticleFields.ARTICLE_ID] = self.le_article_id.text().strip()
        data[EArticleFields.DESCRIPTION] = self.pte_description.toPlainText().strip()
        data[EArticleFields.NET_UNIT_PRICE] = self.dsb_net_price.value()
        data[EArticleFields.QUANTITY_UNIT] = self.combo_unit.currentData()
        data[EArticleFields.VAT_RATE] = self.dsb_vat_rate.value()
        data[EArticleFields.VAT_CODE] = self.combo_vat_code.currentData()
        data[EArticleFields.CONTAINER_TYPE] = self.combo_container_type.currentText()
        data[EArticleFields.DEPOSIT] = self.dsb_deposit.value()

        is_update = self.uid is not None
        add_article(self.ui.model.data_path, self.ui.model.git_add, data, article_id=self.uid, rename=is_update)
        self.accept()
