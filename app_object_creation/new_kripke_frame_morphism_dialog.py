"""
New Kripke Frame Morphism Dialog Module.

Facilitates the creation of a KripkeFrameMorphism mapping between two Kripke Frames.
Validates signature equality, initial state preservation, and accessibility relation preservation.
"""

from typing import Dict, Tuple, Optional
from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QVBoxLayout, 
    QWidget, QMessageBox, QComboBox, QLabel, QTableWidget, QTableWidgetItem, QHeaderView
)
from math_objects.structure import World, KripkeFrame
from math_objects.structure_morphism import KripkeFrameMorphism


class NewKripkeFrameMorphismDialog(QDialog):
    def __init__(self, frame_dict: Dict[str, KripkeFrame], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Create New Kripke Frame Morphism")
        self.resize(650, 520)
        
        self.frame_dict = frame_dict
        self.world_combos: Dict[World, QComboBox] = {}
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Morphism Name (e.g. KFM_1)")
        
        self.combo_source = QComboBox()
        self.combo_source.addItems(sorted(list(self.frame_dict.keys())))
        self.combo_source.currentTextChanged.connect(self.update_mapping_table)
        
        self.combo_target = QComboBox()
        self.combo_target.addItems(sorted(list(self.frame_dict.keys())))
        self.combo_target.currentTextChanged.connect(self.update_mapping_table)
        
        form.addRow("Morphism Name:", self.name_input)
        form.addRow("Source Frame:", self.combo_source)
        form.addRow("Target Frame:", self.combo_target)
        layout.addLayout(form)
        
        layout.addWidget(QLabel("<b>State Mapping (h: Source State &rarr; Target State):</b>"))
        self.table_map = QTableWidget()
        self.table_map.setColumnCount(2)
        self.table_map.setHorizontalHeaderLabels(["Source State", "Target State"])
        self.table_map.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table_map)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if self.combo_source.count() > 0 and self.combo_target.count() > 0:
            self.update_mapping_table()

    def update_mapping_table(self) -> None:
        src_name = self.combo_source.currentText()
        tgt_name = self.combo_target.currentText()
        
        if src_name not in self.frame_dict or tgt_name not in self.frame_dict:
            return
            
        src_frame = self.frame_dict[src_name]
        tgt_frame = self.frame_dict[tgt_name]
        
        self.world_combos.clear()
        src_worlds = sorted(list(src_frame.worlds), key=lambda w: w.name_short)
        tgt_worlds = sorted(list(tgt_frame.worlds), key=lambda w: w.name_short)
        tgt_display_names = [f"{w.name_short} ({w.name_long})" for w in tgt_worlds]
        
        self.table_map.setRowCount(len(src_worlds))
        for r, src_w in enumerate(src_worlds):
            self.table_map.setItem(r, 0, QTableWidgetItem(f"{src_w.name_short} ({src_w.name_long})"))
            combo = QComboBox()
            combo.addItems(tgt_display_names)
            
            if src_w == src_frame.initial_world and tgt_frame.initial_world:
                init_idx = tgt_worlds.index(tgt_frame.initial_world)
                combo.setCurrentIndex(init_idx)
                
            self.world_combos[src_w] = combo
            self.table_map.setCellWidget(r, 1, combo)

    def validate_and_accept(self) -> None:
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Morphism name is required.")
            return

        src_frame = self.frame_dict[self.combo_source.currentText()]
        tgt_frame = self.frame_dict[self.combo_target.currentText()]

        tgt_worlds = sorted(list(tgt_frame.worlds), key=lambda w: w.name_short)
        world_map = {}
        for src_w, combo in self.world_combos.items():
            chosen_idx = combo.currentIndex()
            world_map[src_w] = tgt_worlds[chosen_idx]

        temp_morphism = KripkeFrameMorphism(name, src_frame, tgt_frame, world_map)
        valid, errors = temp_morphism.verify_morphism()
        if not valid:
            QMessageBox.critical(self, "Morphism Verification Failed", "\n".join(errors))
            return

        self.accept()

    def get_data(self) -> Tuple[str, KripkeFrame, KripkeFrame, Dict[World, World]]:
        name = self.name_input.text().strip()
        src_frame = self.frame_dict[self.combo_source.currentText()]
        tgt_frame = self.frame_dict[self.combo_target.currentText()]
        tgt_worlds = sorted(list(tgt_frame.worlds), key=lambda w: w.name_short)

        world_map = {}
        for src_w, combo in self.world_combos.items():
            chosen_idx = combo.currentIndex()
            world_map[src_w] = tgt_worlds[chosen_idx]

        return name, src_frame, tgt_frame, world_map