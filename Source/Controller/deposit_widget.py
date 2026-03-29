"""!
********************************************************************************
@file   deposit_widget.py
@brief  Widget for deposit (Pfand) tracking in invoices.
********************************************************************************
"""

import logging
from typing import Any, TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QGridLayout, \
    QLabel, QSpinBox, QPushButton, QDoubleSpinBox, QComboBox

from Source.version import __title__
from Source.Model.article import EArticleFields, read_articles

if TYPE_CHECKING:
    from Source.Controller.main_window import MainWindow
    from Source.Views.widgets.invoice_item_data_ui import Ui_InvoiceItemData

log = logging.getLogger(__title__)


class DepositRow:
    """!
    @brief Single row in the deposit tracking grid.
    """

    def __init__(self, article_name: str = "", container_type: str = "", deposit: float = 0.0,
                 is_editable: bool = False, article_names: list[str] | None = None,
                 container_suggestions: list[tuple[str, float]] | None = None) -> None:
        """!
        @brief Initialize deposit row.
        @param article_name : display name for the row.
        @param container_type : container type (Kasten/Flasche/etc.).
        @param deposit : deposit amount per unit.
        @param is_editable : True for manually added rows with editable fields.
        @param article_names : list of article names that map to this deposit row (for auto-calculate).
        @param container_suggestions : list of (container_type, deposit) tuples for auto-fill.
        """
        self.article_name = article_name
        self.article_names = article_names or []
        self.container_type = container_type
        self.deposit = deposit
        self.is_editable = is_editable
        self._suggestions: dict[str, float] = {s[0]: s[1] for s in (container_suggestions or [])}

        if is_editable:
            self.combo_container = QComboBox()
            self.combo_container.setEditable(True)
            self.combo_container.addItem("")
            for name, dep in self._suggestions.items():
                self.combo_container.addItem(f"{name} ({dep:.2f} €)", name)
            self.combo_container.setCurrentText(container_type)
            self.dsb_deposit = QDoubleSpinBox()
            self.dsb_deposit.setMaximum(999.99)
            self.dsb_deposit.setDecimals(2)
            self.dsb_deposit.setSuffix(" €")
            self.dsb_deposit.setValue(deposit)
            self.combo_container.currentIndexChanged.connect(self._on_suggestion_selected)
        else:
            self.lbl_name = QLabel(article_name)
            self.lbl_container = QLabel(container_type)
            self.lbl_deposit = QLabel(f"{deposit:.2f} €")
            self.lbl_deposit.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.sb_delivered = QSpinBox()
        self.sb_delivered.setMaximum(9999)

        self.sb_returned = QSpinBox()
        self.sb_returned.setMaximum(9999)

        self.lbl_saldo = QLabel("0,00 €")
        self.lbl_saldo.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.btn_remove: QPushButton | None = None
        if is_editable:
            self.btn_remove = QPushButton("×")
            self.btn_remove.setFixedWidth(25)

    def get_deposit_value(self) -> float:
        """!
        @brief Get current deposit value (from spinbox if editable, else from stored value).
        @return Deposit amount per unit.
        """
        if self.is_editable:
            return self.dsb_deposit.value()
        return self.deposit

    def _on_suggestion_selected(self, _index: int) -> None:
        """!
        @brief Auto-fill deposit value when a suggestion is selected from the combo box.
        @param index : selected combo box index.
        """
        data = self.combo_container.currentData()
        if data and data in self._suggestions:
            self.dsb_deposit.setValue(self._suggestions[data])

    def get_name(self) -> str:
        """!
        @brief Get current name.
        @return Article/deposit name.
        """
        return self.get_container_type()

    def get_container_type(self) -> str:
        """!
        @brief Get current container type.
        @return Container type string.
        """
        if self.is_editable:
            data = self.combo_container.currentData()
            return data if data else self.combo_container.currentText()
        return self.container_type

    def get_saldo(self) -> float:
        """!
        @brief Calculate net deposit for this row.
        @return (delivered - returned) * deposit.
        """
        return (self.sb_delivered.value() - self.sb_returned.value()) * self.get_deposit_value()

    def update_saldo_label(self) -> None:
        """!
        @brief Update the saldo display label.
        """
        self.lbl_saldo.setText(f"{self.get_saldo():.2f} €")

    def get_container_widget(self) -> QWidget:
        """!
        @brief Get the container type widget.
        @return Container type widget.
        """
        return self.combo_container if self.is_editable else self.lbl_container

    def get_deposit_widget(self) -> QWidget:
        """!
        @brief Get the deposit value widget.
        @return Deposit widget.
        """
        return self.dsb_deposit if self.is_editable else self.lbl_deposit


class DepositWidget:
    """!
    @brief Manages deposit tracking grid and updates the associated invoice item widget.
    """

    def __init__(self, ui: "MainWindow", item_dialog: "Ui_InvoiceItemData",
                 on_total_changed: Any = None) -> None:
        """!
        @brief Initialize deposit widget.
        @param ui : main window reference for data access.
        @param item_dialog : invoice item widget to update with totals.
        @param on_total_changed : callback when total deposit changes.
        """
        self.ui = ui
        self.item_dialog = item_dialog
        self.on_total_changed = on_total_changed
        self.rows: list[DepositRow] = []
        self._next_grid_row = 1  # row 0 is header
        self.widget = QWidget()
        self._setup_ui()

    def _setup_ui(self) -> None:
        """!
        @brief Build the deposit tracking grid inside the item widget.
        """
        layout = QVBoxLayout(self.widget)
        layout.setContentsMargins(0, 0, 0, 0)

        group = QGroupBox("Pfand-Positionen")
        self.group_layout = QVBoxLayout(group)

        # header + grid
        self.grid = QGridLayout()
        self.grid.addWidget(QLabel("<b>Gebinde</b>"), 0, 0)
        self.grid.addWidget(QLabel("<b>Pfand/Stk.</b>"), 0, 1)
        self.grid.addWidget(QLabel("<b>Geliefert</b>"), 0, 2)
        self.grid.addWidget(QLabel("<b>Zurück</b>"), 0, 3)
        self.grid.addWidget(QLabel("<b>Saldo</b>"), 0, 4)
        self.group_layout.addLayout(self.grid)

        # buttons
        btn_layout = QHBoxLayout()
        self.btn_auto_calc = QPushButton("Pfand aus Positionen berechnen")
        self.btn_auto_calc.clicked.connect(self.auto_calculate)
        btn_layout.addWidget(self.btn_auto_calc)

        self.btn_add_row = QPushButton("Gebinde hinzufügen")
        self.btn_add_row.clicked.connect(self._add_manual_row)
        btn_layout.addWidget(self.btn_add_row)

        btn_layout.addStretch()

        self.lbl_total = QLabel("<b>Pfand gesamt: 0,00 €</b>")
        self.lbl_total.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        btn_layout.addWidget(self.lbl_total)
        self.group_layout.addLayout(btn_layout)

        layout.addWidget(group)

    def _add_row_to_grid(self, row: DepositRow) -> None:
        """!
        @brief Add a deposit row's widgets to the grid.
        @param row : deposit row to add.
        """
        row_index = self._next_grid_row
        self._next_grid_row += 1
        self.rows.append(row)

        self.grid.addWidget(row.get_container_widget(), row_index, 0)
        self.grid.addWidget(row.get_deposit_widget(), row_index, 1)
        self.grid.addWidget(row.sb_delivered, row_index, 2)
        self.grid.addWidget(row.sb_returned, row_index, 3)
        self.grid.addWidget(row.lbl_saldo, row_index, 4)

        if row.btn_remove is not None:
            self.grid.addWidget(row.btn_remove, row_index, 5)
            row.btn_remove.clicked.connect(lambda: self._remove_row(row))

        row.sb_delivered.valueChanged.connect(self._on_quantity_changed)
        row.sb_returned.valueChanged.connect(self._on_quantity_changed)
        if row.is_editable:
            row.dsb_deposit.valueChanged.connect(self._on_quantity_changed)

    def _get_container_suggestions(self) -> list[tuple[str, float]]:
        """!
        @brief Collect all unique container types with deposit values from articles.
        @return List of (container_type, deposit) tuples.
        """
        articles = read_articles(self.ui.model.data_path)
        seen: dict[str, float] = {}
        for a in articles:
            deposit = float(a[EArticleFields.DEPOSIT])
            container = str(a[EArticleFields.CONTAINER_TYPE])
            if deposit > 0 and container and container not in seen:
                seen[container] = deposit
        return list(seen.items())

    def _add_manual_row(self) -> None:
        """!
        @brief Add an editable row for custom deposit entry with suggestions not already present.
        """
        existing_types = {row.get_container_type() for row in self.rows}
        suggestions = [(ct, dep) for ct, dep in self._get_container_suggestions() if ct not in existing_types]
        row = DepositRow(is_editable=True, container_suggestions=suggestions)
        self._add_row_to_grid(row)

    def _remove_row(self, row: DepositRow) -> None:
        """!
        @brief Remove a manual deposit row from the grid.
        @param row : row to remove.
        """
        if row not in self.rows:
            return
        # remove widgets from grid
        for widget in [row.get_container_widget(), row.get_deposit_widget(),
                       row.sb_delivered, row.sb_returned, row.lbl_saldo, row.btn_remove]:
            if widget is not None:
                self.grid.removeWidget(widget)
                widget.setParent(None)
        self.rows.remove(row)
        self._on_quantity_changed()

    def _on_quantity_changed(self) -> None:
        """!
        @brief Handle changes to delivered/returned quantities.
        """
        for row in self.rows:
            row.update_saldo_label()
        self._update_total()

    def _update_total(self) -> None:
        """!
        @brief Recalculate total deposit and update item widget.
        """
        total = sum(row.get_saldo() for row in self.rows)
        self.lbl_total.setText(f"<b>Pfand gesamt: {total:.2f} €</b>")

        # update item widget
        vat_rate = self.item_dialog.dsb_item_vat_rate.value()
        self.item_dialog.dsb_item_net_unit_price.setValue(total)
        self.item_dialog.dsb_item_gross_unit_price.setValue(round(total * (1 + vat_rate / 100), 2))

        # build description
        lines: list[str] = []
        for row in self.rows:
            delivered = row.sb_delivered.value()
            returned = row.sb_returned.value()
            if delivered > 0 or returned > 0:
                container = row.get_container_type() or row.get_name() or "Pfand"
                deposit_val = row.get_deposit_value()
                diff = delivered - returned
                line = f"{container}: {delivered} geliefert, {returned} zurück, diff {diff}  (x {deposit_val:.2f} €) = {row.get_saldo():.2f} €"
                lines.append(line)
        self.item_dialog.pte_item_description.setPlainText("\n".join(lines))

        if self.on_total_changed:
            self.on_total_changed()

    def auto_calculate(self, item_widgets: list["Ui_InvoiceItemData"] | None = None) -> None:
        """!
        @brief Create deposit rows from invoice positions that have deposit articles.
        @param item_widgets : list of invoice item widgets to scan.
        """
        if item_widgets is None:
            return

        # save manual rows and remove all rows
        manual_rows_data: list[tuple[str, float, int, int]] = []
        for row in [r for r in self.rows if r.is_editable]:
            manual_rows_data.append((
                row.get_container_type(),
                row.get_deposit_value(),
                row.sb_delivered.value(),
                row.sb_returned.value()
            ))
        for row in list(self.rows):
            self._remove_row(row)

        # build article lookup: name -> (container_type, deposit)
        articles = read_articles(self.ui.model.data_path)
        article_map: dict[str, tuple[str, float]] = {}
        for a in articles:
            deposit = float(a[EArticleFields.DEPOSIT])
            if deposit > 0:
                article_map[str(a[EArticleFields.NAME])] = (
                    str(a[EArticleFields.CONTAINER_TYPE]) or "Stück",
                    deposit
                )

        # collect quantities grouped by (container_type, deposit)
        groups: dict[tuple[str, float], tuple[list[str], float]] = {}
        for item_dialog in item_widgets:
            name = item_dialog.le_item_name.text()
            if name in article_map:
                key = article_map[name]
                if key not in groups:
                    groups[key] = ([], 0.0)
                names, qty = groups[key]
                if name not in names:
                    names.append(name)
                groups[key] = (names, qty + item_dialog.dsb_item_quantity.value())

        # create auto-generated rows
        for (container_type, deposit), (article_names, quantity) in groups.items():
            row = DepositRow(
                article_name=container_type,
                container_type=container_type,
                deposit=deposit,
                is_editable=False,
                article_names=article_names
            )
            self._add_row_to_grid(row)
            row.sb_delivered.setValue(int(quantity))

        # re-add manual rows at the bottom
        suggestions = self._get_container_suggestions()
        for container, deposit, delivered, returned in manual_rows_data:
            row = DepositRow(is_editable=True, container_suggestions=suggestions,
                             container_type=container, deposit=deposit)
            self._add_row_to_grid(row)
            row.sb_delivered.setValue(delivered)
            row.sb_returned.setValue(returned)
