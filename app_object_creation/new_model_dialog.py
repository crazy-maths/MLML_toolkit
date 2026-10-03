"""
New Model Dialog Module.

Facilitates the creation of a Model based on a selected KripkeFrame and ManyLattice.
Allows assigning complete sublattices from the ManyLattice to each world,
and assigning valuations to propositions according to each world's sublattice.
"""

from typing import Dict, Tuple, Optional, Any
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDialogButtonBox, 
    QComboBox, QTabWidget, QWidget, QLabel, QMessageBox, QTextEdit, 
    QScrollArea, QGroupBox
)
from PyQt6.QtCore import Qt

from math_objects.lattice import Lattice, ManyLattice
from math_objects.structure import World, KripkeFrame, Model


class NewModelDialog(QDialog):
    def __init__(
        self,
        frames_dict: Dict[str, KripkeFrame],
        many_lattices_dict: Dict[str, ManyLattice],
        is_dark_mode: bool = False,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.setWindowTitle("Create New Model")
        self.resize(750, 700)

        self.frames_dict = frames_dict
        self.many_lattices_dict = many_lattices_dict
        self.is_dark_mode = is_dark_mode

        self.world_sublattice_combos: Dict[World, QComboBox] = {}
        self.valuation_combos: Dict[World, Dict[str, QComboBox]] = {}

        self.main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)

        self.tab_base = QWidget()
        self.setup_base_tab()
        self.tabs.addTab(self.tab_base, "1. Structure Selection")

        self.tab_worlds = QWidget()
        self.setup_worlds_tab()
        self.tabs.addTab(self.tab_worlds, "2. Sublattices and Valuations")

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        self.main_layout.addWidget(buttons)

        if self.combo_frame.count() > 0 and self.combo_ml.count() > 0:
            self.refresh_worlds_and_valuations()

    def setup_base_tab(self):
        layout = QVBoxLayout(self.tab_base)
        form = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., Model_1")

        self.combo_frame = QComboBox()
        self.combo_frame.addItems(sorted(list(self.frames_dict.keys())))
        self.combo_frame.currentTextChanged.connect(self.on_frame_or_ml_changed)

        self.combo_ml = QComboBox()
        self.combo_ml.addItems(sorted(list(self.many_lattices_dict.keys())))
        self.combo_ml.currentTextChanged.connect(self.on_frame_or_ml_changed)

        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(80)
        self.desc_input.setPlaceholderText("Optional description...")

        form.addRow("Model Name:", self.name_input)
        form.addRow("Kripke Frame:", self.combo_frame)
        form.addRow("Many-Lattice:", self.combo_ml)
        form.addRow("Description:", self.desc_input)
        layout.addLayout(form)
        layout.addStretch()

    def setup_worlds_tab(self):
        layout = QVBoxLayout(self.tab_worlds)
        layout.addWidget(QLabel("<b>Assign complete sublattices and valuations for each state:</b>"))

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.worlds_container = QWidget()
        self.worlds_layout = QVBoxLayout(self.worlds_container)
        self.scroll_area.setWidget(self.worlds_container)

        layout.addWidget(self.scroll_area)

    def on_frame_or_ml_changed(self):
        self.refresh_worlds_and_valuations()

    def refresh_worlds_and_valuations(self):
        while self.worlds_layout.count() > 0:
            item = self.worlds_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        self.world_sublattice_combos.clear()
        self.valuation_combos.clear()

        frame_name = self.combo_frame.currentText()
        ml_name = self.combo_ml.currentText()

        if frame_name not in self.frames_dict or ml_name not in self.many_lattices_dict:
            return

        frame = self.frames_dict[frame_name]
        many_lat = self.many_lattices_dict[ml_name]

        sublattices = many_lat.comp_sub_lat
        if not sublattices:
            self.worlds_layout.addWidget(QLabel("Selected Many-Lattice has no registered complete sublattices."))
            return

        sublat_names = [lat.name for lat in sublattices]
        props = sorted(list(frame.signature.propositions))

        for world in sorted(list(frame.worlds), key=lambda w: w.name_short):
            box = QGroupBox(f"State: {world.name_long} ({world.name_short})")
            box_layout = QFormLayout(box)

            combo_sublat = QComboBox()
            combo_sublat.addItems(sublat_names)
            box_layout.addRow("Complete Sublattice:", combo_sublat)
            self.world_sublattice_combos[world] = combo_sublat

            self.valuation_combos[world] = {}

            val_group = QWidget()
            val_form = QFormLayout(val_group)

            for prop in props:
                val_combo = QComboBox()
                val_form.addRow(f"Prop '{prop}':", val_combo)
                self.valuation_combos[world][prop] = val_combo

            box_layout.addRow(QLabel("<b>Valuations:</b>"), val_group)
            self.worlds_layout.addWidget(box)

            def make_handler(w, sub_cb):
                return lambda: self.update_world_valuation_options(w, sub_cb.currentText(), many_lat)

            combo_sublat.currentTextChanged.connect(make_handler(world, combo_sublat))
            self.update_world_valuation_options(world, combo_sublat.currentText(), many_lat)

        self.worlds_layout.addStretch()

    def update_world_valuation_options(self, world: World, sublat_name: str, many_lat: ManyLattice):
        sub_lat = many_lat.get_comp_sub_lattice(sublat_name)
        if not sub_lat:
            return

        elements = sorted(list(sub_lat.elements), key=str)
        for prop, combo in self.valuation_combos.get(world, {}).items():
            curr_val = combo.currentText()
            combo.blockSignals(True)
            combo.clear()
            combo.addItems([str(e) for e in elements])
            if curr_val in elements:
                combo.setCurrentText(curr_val)
            combo.blockSignals(False)

    def validate_and_accept(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Model name is required.")
            return

        frame_name = self.combo_frame.currentText()
        ml_name = self.combo_ml.currentText()

        if frame_name not in self.frames_dict:
            QMessageBox.warning(self, "Error", "Please select a valid Kripke Frame.")
            return
        if ml_name not in self.many_lattices_dict:
            QMessageBox.warning(self, "Error", "Please select a valid Many-Lattice.")
            return

        frame = self.frames_dict[frame_name]
        for w in frame.worlds:
            if w not in self.world_sublattice_combos or not self.world_sublattice_combos[w].currentText():
                QMessageBox.warning(self, "Error", f"State '{w.name_short}' must have a sublattice assigned.")
                return

        self.accept()

    def get_data(self) -> Tuple[str, KripkeFrame, ManyLattice, Dict[World, Lattice], Dict[World, Dict[str, str]], str]:
        name = self.name_input.text().strip()
        frame = self.frames_dict[self.combo_frame.currentText()]
        many_lat = self.many_lattices_dict[self.combo_ml.currentText()]
        description = self.desc_input.toPlainText().strip()

        world_lattices: Dict[World, Lattice] = {}
        valuations: Dict[World, Dict[str, str]] = {}

        for world in frame.worlds:
            sublat_name = self.world_sublattice_combos[world].currentText()
            world_lattices[world] = many_lat.get_comp_sub_lattice(sublat_name)

            valuations[world] = {}
            for prop, combo in self.valuation_combos.get(world, {}).items():
                valuations[world][prop] = combo.currentText()

        return name, frame, many_lat, world_lattices, valuations, description