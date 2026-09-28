"""
New Signature Morphism Dialog Module.

Facilitates the creation of a SignatureMorphism mapping between two signatures.
"""

from typing import Dict, Tuple, Optional
from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QVBoxLayout, 
    QWidget, QMessageBox, QComboBox, QLabel, QTableWidget, QTableWidgetItem, QHeaderView
)
from math_objects.signature import Signature

class NewSignatureMorphismDialog(QDialog):
    def __init__(self, sig_dict: Dict[str, Signature], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Create New Signature Morphism")
        self.resize(600, 500)
        
        self.sig_dict = sig_dict
        self.prop_widgets: Dict[str, QComboBox] = {}
        self.act_widgets: Dict[str, QComboBox] = {}
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Unique Morphism Name (e.g. SM_1)")
        
        self.combo_source = QComboBox()
        self.combo_source.addItems(sorted(list(self.sig_dict.keys())))
        self.combo_source.currentTextChanged.connect(self.update_mapping_tables)
        
        self.combo_target = QComboBox()
        self.combo_target.addItems(sorted(list(self.sig_dict.keys())))
        self.combo_target.currentTextChanged.connect(self.update_mapping_tables)
        
        form.addRow("Morphism Name:", self.name_input)
        form.addRow("Source Signature:", self.combo_source)
        form.addRow("Target Signature:", self.combo_target)
        layout.addLayout(form)
        
        layout.addWidget(QLabel("<b>Proposition Mappings (Source → Target):</b>"))
        self.table_props = QTableWidget()
        self.table_props.setColumnCount(2)
        self.table_props.setHorizontalHeaderLabels(["Source Proposition", "Target Proposition"])
        self.table_props.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table_props)
        
        layout.addWidget(QLabel("<b>Action Mappings (Source → Target):</b>"))
        self.table_acts = QTableWidget()
        self.table_acts.setColumnCount(2)
        self.table_acts.setHorizontalHeaderLabels(["Source Action", "Target Action"])
        self.table_acts.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table_acts)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if self.combo_source.count() > 0 and self.combo_target.count() > 0:
            self.update_mapping_tables()

    def update_mapping_tables(self) -> None:
        src_name = self.combo_source.currentText()
        tgt_name = self.combo_target.currentText()
        
        if src_name not in self.sig_dict or tgt_name not in self.sig_dict:
            return
            
        src_sig = self.sig_dict[src_name]
        tgt_sig = self.sig_dict[tgt_name]
        
        target_prop_items = sorted(list(tgt_sig.propositions))
        target_act_items = sorted(list(tgt_sig.actions))
        
        self.prop_widgets.clear()
        props = sorted(list(src_sig.propositions))
        self.table_props.setRowCount(len(props))
        for r, p in enumerate(props):
            self.table_props.setItem(r, 0, QTableWidgetItem(p))
            combo = QComboBox()
            combo.addItems(target_prop_items)
            self.prop_widgets[p] = combo
            self.table_props.setCellWidget(r, 1, combo)
            
        self.act_widgets.clear()
        acts = sorted(list(src_sig.actions))
        self.table_acts.setRowCount(len(acts))
        for r, a in enumerate(acts):
            self.table_acts.setItem(r, 0, QTableWidgetItem(a))
            combo = QComboBox()
            combo.addItems(target_act_items)
            self.act_widgets[a] = combo
            self.table_acts.setCellWidget(r, 1, combo)

    def validate_and_accept(self) -> None:
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Error", "Morphism name is required.")
            return
        self.accept()

    def get_data(self) -> Tuple[str, Signature, Signature, Dict[str, str], Dict[str, str]]:
        name = self.name_input.text().strip()
        src_sig = self.sig_dict[self.combo_source.currentText()]
        tgt_sig = self.sig_dict[self.combo_target.currentText()]
        
        prop_map = {p: combo.currentText() for p, combo in self.prop_widgets.items()}
        act_map = {a: combo.currentText() for a, combo in self.act_widgets.items()}
        
        return name, src_sig, tgt_sig, prop_map, act_map