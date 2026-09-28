"""
New Model Morphism Dialog Module.

Creates a ModelMorphism from an existing KripkeFrameMorphism between two Models.
Checks that for every world w in the source model, Lat(w) == Lat(h(w)).
"""

from typing import Dict, Tuple, Optional
from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QVBoxLayout, 
    QWidget, QMessageBox, QComboBox, QLabel, QTableWidget, QTableWidgetItem, QHeaderView
)
from math_objects.structure import World, Model
from math_objects.structure_morphism import KripkeFrameMorphism, ModelMorphism


class NewModelMorphismDialog(QDialog):
    def __init__(
        self, 
        model_dict: Dict[str, Model], 
        kfm_dict: Dict[str, KripkeFrameMorphism], 
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.setWindowTitle("Create New Model Morphism")
        self.resize(720, 520)
        
        self.model_dict = model_dict
        self.kfm_dict = kfm_dict
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Model Morphism Name (e.g. MM_1)")
        
        self.combo_source = QComboBox()
        self.combo_source.addItems(sorted(list(self.model_dict.keys())))
        self.combo_source.currentTextChanged.connect(self.update_available_frame_morphisms)
        
        self.combo_target = QComboBox()
        self.combo_target.addItems(sorted(list(self.model_dict.keys())))
        self.combo_target.currentTextChanged.connect(self.update_available_frame_morphisms)
        
        self.combo_kfm = QComboBox()
        self.combo_kfm.currentTextChanged.connect(self.update_preview_table)

        form.addRow("Morphism Name:", self.name_input)
        form.addRow("Source Model:", self.combo_source)
        form.addRow("Target Model:", self.combo_target)
        form.addRow("Base Frame Morphism:", self.combo_kfm)
        layout.addLayout(form)
        
        layout.addWidget(QLabel("<b>State Mapping & Sublattice Consistency Preview:</b>"))
        self.table_preview = QTableWidget()
        self.table_preview.setColumnCount(4)
        self.table_preview.setHorizontalHeaderLabels([
            "Source State", "Source Lattice", "Target State", "Target Lattice"
        ])
        self.table_preview.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table_preview)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if self.combo_source.count() > 0 and self.combo_target.count() > 0:
            self.update_available_frame_morphisms()

    def update_available_frame_morphisms(self) -> None:
        src_name = self.combo_source.currentText()
        tgt_name = self.combo_target.currentText()
        
        self.combo_kfm.blockSignals(True)
        self.combo_kfm.clear()

        if src_name in self.model_dict and tgt_name in self.model_dict:
            src_m = self.model_dict[src_name]
            tgt_m = self.model_dict[tgt_name]

            src_kf = getattr(src_m, "kripke_frame_name", src_m.name)
            tgt_kf = getattr(tgt_m, "kripke_frame_name", tgt_m.name)

            compatible_kfm = [
                kfm_name for kfm_name, kfm in self.kfm_dict.items()
                if (kfm.source_frame.name in (src_kf, src_m.name) and 
                    kfm.target_frame.name in (tgt_kf, tgt_m.name))
            ]
            self.combo_kfm.addItems(sorted(compatible_kfm))

        self.combo_kfm.blockSignals(False)
        self.update_preview_table()

    def update_preview_table(self) -> None:
        self.table_preview.setRowCount(0)
        src_name = self.combo_source.currentText()
        tgt_name = self.combo_target.currentText()
        kfm_name = self.combo_kfm.currentText()

        if not (src_name in self.model_dict and tgt_name in self.model_dict and kfm_name in self.kfm_dict):
            return

        src_model = self.model_dict[src_name]
        tgt_model = self.model_dict[tgt_name]
        kfm = self.kfm_dict[kfm_name]

        src_model_worlds = {w.name_short: w for w in src_model.worlds}
        tgt_model_worlds = {w.name_short: w for w in tgt_model.worlds}

        sorted_src = sorted(list(kfm.world_map.keys()), key=lambda w: w.name_short)
        self.table_preview.setRowCount(len(sorted_src))

        for row, src_kfm_w in enumerate(sorted_src):
            tgt_kfm_w = kfm.world_map.get(src_kfm_w)

            src_m_w = src_model_worlds.get(src_kfm_w.name_short)
            tgt_m_w = tgt_model_worlds.get(tgt_kfm_w.name_short) if tgt_kfm_w else None

            src_lat_name = src_model.world_lattices.get(src_m_w).name if (src_m_w and src_m_w in src_model.world_lattices) else "-"
            tgt_lat_name = tgt_model.world_lattices.get(tgt_m_w).name if (tgt_m_w and tgt_m_w in tgt_model.world_lattices) else "-"

            self.table_preview.setItem(row, 0, QTableWidgetItem(f"{src_kfm_w.name_short}"))
            self.table_preview.setItem(row, 1, QTableWidgetItem(src_lat_name))
            self.table_preview.setItem(row, 2, QTableWidgetItem(f"{tgt_kfm_w.name_short}" if tgt_kfm_w else "-"))
            
            tgt_lat_item = QTableWidgetItem(tgt_lat_name)

            if src_lat_name != tgt_lat_name or src_lat_name == "-":
                tgt_lat_item.setToolTip("Lattice mismatch!")
            self.table_preview.setItem(row, 3, tgt_lat_item)

    def validate_and_accept(self) -> None:
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Morphism name is required.")
            return

        kfm_name = self.combo_kfm.currentText()
        if not kfm_name:
            QMessageBox.warning(
                self, 
                "Validation Error", 
                "No compatible Kripke Frame Morphism exists. Create one first."
            )
            return

        src_model = self.model_dict[self.combo_source.currentText()]
        tgt_model = self.model_dict[self.combo_target.currentText()]
        kfm = self.kfm_dict[kfm_name]

        src_model_worlds = {w.name_short: w for w in src_model.worlds}
        tgt_model_worlds = {w.name_short: w for w in tgt_model.worlds}

        world_map = {}
        for src_kf_w, tgt_kf_w in kfm.world_map.items():
            m_src_w = src_model_worlds.get(src_kf_w.name_short)
            m_tgt_w = tgt_model_worlds.get(tgt_kf_w.name_short) if tgt_kf_w else None
            
            if not m_src_w or (tgt_kf_w and not m_tgt_w):
                 QMessageBox.critical(self, "Referential Integrity Error", 
                    f"State mismatch between models and base frame morphism. Check logs.")
                 return
            world_map[m_src_w] = m_tgt_w

        temp_morphism = ModelMorphism(name, src_model, tgt_model, world_map)
        valid, errors = temp_morphism.verify_morphism()
        if not valid:
            QMessageBox.critical(self, "Model Morphism Invalid", "\n".join(errors))
            return

        self.accept()

    def get_data(self) -> Tuple[str, Model, Model, str, Dict[World, World]]:
        name = self.name_input.text().strip()
        src_model = self.model_dict[self.combo_source.currentText()]
        tgt_model = self.model_dict[self.combo_target.currentText()]
        kfm_name = self.combo_kfm.currentText()
        kfm = self.kfm_dict[kfm_name]

        src_model_worlds = {w.name_short: w for w in src_model.worlds}
        tgt_model_worlds = {w.name_short: w for w in tgt_model.worlds}

        world_map = {}
        for src_kf_w, tgt_kf_w in kfm.world_map.items():
            world_map[src_model_worlds[src_kf_w.name_short]] = \
                tgt_model_worlds[tgt_kf_w.name_short]

        return name, src_model, tgt_model, kfm_name, world_map