"""
New Lattice Dialog Module.

Creates a Lattice with elements, order relations, and an Implication Map.
"""

import itertools
import logging
from typing import Tuple, Set, Dict
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDialogButtonBox, 
    QListWidget, QListWidgetItem, QPushButton, QLabel,
    QTableWidget, QHeaderView, QComboBox, QTabWidget, QWidget
)
from PyQt6.QtCore import Qt
from ui.error_dialogs import ErrorHandler

logger = logging.getLogger("NewLatticeDialog")


class NewLatticeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Lattice")
        self.resize(600, 700)
        
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.neg_combos: Dict[str, QComboBox] = {}
        self._last_elements: list[str] = []
        
        # TAB 1: Structure
        self.tab_struct = QWidget()
        self.setup_struct_tab()
        self.tabs.addTab(self.tab_struct, "1. Elements & Order")
        
        # TAB 2: Implication
        self.tab_imp = QWidget()
        self.setup_imp_tab()
        self.tabs.addTab(self.tab_imp, "2. Implication")

        # TAB 3: Negation
        self.tab_neg = QWidget()
        self.setup_neg_tab()
        self.tabs.addTab(self.tab_neg, "3. Negation")
        
        self.tabs.currentChanged.connect(self.on_tab_changed)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def setup_struct_tab(self):
        layout = QVBoxLayout(self.tab_struct)
        form = QFormLayout()
        self.name_input = QLineEdit()
        self.elements_input = QLineEdit()
        self.elements_input.setPlaceholderText("separated by comma, e.g., 0,1,a,b")
        self.elements_input.returnPressed.connect(self.populate_lists)
        form.addRow("Name:", self.name_input)
        form.addRow("Elements:", self.elements_input)
        layout.addLayout(form)

        self.gen_btn = QPushButton("Define an order")
        self.gen_btn.clicked.connect(self.populate_lists)
        layout.addWidget(self.gen_btn)
        
        layout.addWidget(QLabel("Relations (a ≤ b):"))
        self.rel_list = QListWidget()
        self.rel_list.itemChanged.connect(self.on_relation_changed)
        layout.addWidget(self.rel_list)

    def setup_imp_tab(self):
        layout = QVBoxLayout(self.tab_imp)
        layout.addWidget(QLabel("Define Implication (Row → Col):"))
        self.table_imp = QTableWidget()
        layout.addWidget(self.table_imp)

    def setup_neg_tab(self):
        layout = QVBoxLayout(self.tab_neg)
        layout.addWidget(QLabel("Define Negation (~a):"))
        
        self.neg_form_widget = QWidget()
        self.neg_form_layout = QFormLayout(self.neg_form_widget)
        layout.addWidget(self.neg_form_widget)
        layout.addStretch()

    def populate_imp_table(self):
        try:
            elements = sorted([e.strip() for e in self.elements_input.text().split(',') if e.strip()])
            if not elements:
                self.table_imp.setRowCount(0)
                self.table_imp.setColumnCount(0)
                return
            
            n = len(elements)
            self.table_imp.setRowCount(n)
            self.table_imp.setColumnCount(n)
            self.table_imp.setHorizontalHeaderLabels(elements)
            self.table_imp.setVerticalHeaderLabels(elements)
            self.table_imp.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            
            for r in range(n):
                for c in range(n):
                    combo = QComboBox()
                    combo.addItems(elements)
                    self.table_imp.setCellWidget(r, c, combo)
        except Exception as e:
            logger.error(f"Failed to populate implication table: {str(e)}")
            ErrorHandler.show_error("Display Error", "An error occurred while building the implication table.")

    def populate_neg_tab(self):
        try:
            while self.neg_form_layout.rowCount() > 0:
                self.neg_form_layout.removeRow(0)
                
            self.neg_combos = {}
            elements = sorted([e.strip() for e in self.elements_input.text().split(',') if e.strip()])
            if not elements:
                return
                
            for el in elements:
                combo = QComboBox()
                combo.addItems(elements)
                self.neg_form_layout.addRow(f"~{el}:", combo)
                self.neg_combos[el] = combo
        except Exception as e:
            logger.error(f"Failed to populate negation tab: {str(e)}")

    def populate_lists(self):
        try:
            elements = [e.strip() for e in self.elements_input.text().split(',') if e.strip()]
            if not elements:
                return

            self.rel_list.clear()
            for p in itertools.product(elements, repeat=2):
                item = QListWidgetItem(f"({p[0]}, {p[1]})")
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Checked if p[0] == p[1] else Qt.CheckState.Unchecked)
                self.rel_list.addItem(item)

            self._last_elements = sorted(list(elements))
            self.populate_imp_table()
            self.populate_neg_tab()

        except Exception as e:
            logger.error(f"Failed to populate relation list: {str(e)}")
            ErrorHandler.show_error("Generation Error", "An error occurred while generating the relations list.")

    def on_tab_changed(self, index):
        elements = sorted([e.strip() for e in self.elements_input.text().split(',') if e.strip()])
        if elements != self._last_elements:
            self._last_elements = list(elements)
            self.populate_imp_table()
            self.populate_neg_tab()
    
    def on_relation_changed(self, item: QListWidgetItem):
        try:
            clean = item.text().replace('(', '').replace(')', '').replace("'", "")
            parts = [x.strip() for x in clean.split(',')]
            
            if len(parts) != 2:
                return

            a, b = parts
            if a == b:
                return

            opposite = None
            for i in range(self.rel_list.count()):
                other = self.rel_list.item(i)
                clean_other = other.text().replace('(', '').replace(')', '').replace("'", "")
                other_parts = [v.strip() for v in clean_other.split(',')]
                
                if len(other_parts) == 2 and other_parts[0] == b and other_parts[1] == a:
                    opposite = other
                    break

            if opposite is None:
                return

            self.rel_list.blockSignals(True)

            if item.checkState() == Qt.CheckState.Checked:
                opposite.setCheckState(Qt.CheckState.Unchecked)
                opposite.setFlags(opposite.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)
            elif item.checkState() == Qt.CheckState.Unchecked:
                opposite.setFlags(opposite.flags() | Qt.ItemFlag.ItemIsUserCheckable)

            self.rel_list.blockSignals(False)

        except Exception as e:
            logger.error(f"Error processing relation change: {str(e)}")

        self.rel_list.blockSignals(True)

        if item.checkState() == Qt.CheckState.Checked:
            opposite.setCheckState(Qt.CheckState.Unchecked)
            opposite.setFlags(opposite.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)

        elif item.checkState() == Qt.CheckState.Unchecked:
            opposite.setFlags(opposite.flags() | Qt.ItemFlag.ItemIsUserCheckable)

        self.rel_list.blockSignals(False)

    def validate_and_accept(self):
        try:
            name = self.name_input.text().strip()
            if not name:
                ErrorHandler.show_warning("Validation Error", "Lattice name is required.")
                self.tabs.setCurrentIndex(0)
                return
            
            elements = [e.strip() for e in self.elements_input.text().split(',') if e.strip()]
            if not elements:
                ErrorHandler.show_warning("Validation Error", "Elements list cannot be empty.")
                self.tabs.setCurrentIndex(0)
                return

            if self.rel_list.count() == 0:
                ErrorHandler.show_warning("Validation Error", "Please click 'Define an order' to generate the order relations.")
                self.tabs.setCurrentIndex(0)
                return

            if elements != self._last_elements:
                self._last_elements = list(elements)
                self.populate_imp_table()
                self.populate_neg_tab()

            rows = self.table_imp.rowCount()
            cols = self.table_imp.columnCount()
            if rows == 0 or cols == 0 or rows != len(elements):
                ErrorHandler.show_warning("Validation Error", "Please review and complete the Implication table.")
                self.tabs.setCurrentIndex(1)
                return

            for r in range(rows):
                for c in range(cols):
                    widget = self.table_imp.cellWidget(r, c)
                    if not isinstance(widget, QComboBox) or not widget.currentText().strip():
                        row_el = self.table_imp.verticalHeaderItem(r).text()
                        col_el = self.table_imp.horizontalHeaderItem(c).text()
                        ErrorHandler.show_warning(
                            "Validation Error", 
                            f"Implication ({row_el} → {col_el}) must be specified."
                        )
                        self.tabs.setCurrentIndex(1)
                        return

            if not getattr(self, 'neg_combos', {}) or len(self.neg_combos) != len(elements):
                ErrorHandler.show_warning("Validation Error", "Please review and specify Negation for all elements.")
                self.tabs.setCurrentIndex(2)
                return

            for el in elements:
                combo = self.neg_combos.get(el)
                if not combo or not combo.currentText().strip():
                    ErrorHandler.show_warning("Validation Error", f"Negation for element '{el}' must be specified.")
                    self.tabs.setCurrentIndex(2)
                    return

            self.accept()
        except Exception as e:
            logger.error(f"Error during lattice validation: {str(e)}")
            ErrorHandler.show_error("Validation Error", "An unexpected error occurred while validating the lattice.")

    def get_data(self) -> Tuple[str, Set[str], Set[Tuple[str, str]], Dict[Tuple[str, str], str]]:
        try:
            name = self.name_input.text().strip()
            elements = {e.strip() for e in self.elements_input.text().split(',') if e.strip()}
            
            relations = set()
            for i in range(self.rel_list.count()):
                item = self.rel_list.item(i)
                if item.checkState() == Qt.CheckState.Checked:
                    clean = item.text().replace('(', '').replace(')', '').replace("'", "")
                    p = [x.strip() for x in clean.split(',')]
                    if len(p) == 2:
                        relations.add((p[0], p[1]))

            imp_map = {}
            rows = self.table_imp.rowCount()
            for r in range(rows):
                a = self.table_imp.verticalHeaderItem(r).text()
                for c in range(rows):
                    b = self.table_imp.horizontalHeaderItem(c).text()
                    widget = self.table_imp.cellWidget(r, c)
                    res = widget.currentText() if isinstance(widget, QComboBox) else ""
                    imp_map[(a, b)] = res
                    
            negation_map = {}
            for el, combo in getattr(self, 'neg_combos', {}).items():
                negation_map[el] = combo.currentText()
                
            return name, elements, relations, negation_map, imp_map
        except Exception as e:
            logger.error(f"Error retrieving lattice data: {str(e)}")
            ErrorHandler.show_error("Data Error", "An error occurred while retrieving lattice data.")
            raise