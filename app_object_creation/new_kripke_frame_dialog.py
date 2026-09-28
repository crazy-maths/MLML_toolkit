"""
New Kripke Frame Dialog Module.

Facilitates the creation of a KripkeFrame consisting of a Signature, a set of Worlds,
an initial World, and action-indexed accessibility relations.
"""

from collections import defaultdict
from typing import Dict, Set, Tuple, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDialogButtonBox, 
    QComboBox, QListWidget, QListWidgetItem, QTabWidget, QWidget, 
    QTableWidget, QLabel, QMessageBox, QHBoxLayout, QPushButton,
    QAbstractItemView, QHeaderView
)
from PyQt6.QtCore import Qt

from math_objects.signature import Signature
from math_objects.structure import World, KripkeFrame


class CheckableCell(QWidget):
    """Square checkable cell used for relation matrix toggles."""
    def __init__(self, is_checked: bool, active_bg: str, is_dark: bool, parent=None):
        super().__init__(parent)
        self.is_checked = is_checked
        self.active_bg = active_bg
        self.is_dark = is_dark
        self.setup_ui()

    def setup_ui(self):
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel("")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = self.label.font()
        font.setPointSize(14)
        font.setBold(True)
        self.label.setFont(font)
        self.layout.addWidget(self.label)
        self.update_style()

    def update_style(self):
        v_color = "#ffffff" if self.is_dark else "#000000"
        border_color = "#555555" if self.is_dark else "#cccccc"
        if self.is_checked:
            self.label.setText("✓")
            bg = self.active_bg
            self.label.setStyleSheet(f"color: {v_color}; border: none; background: transparent;")
        else:
            self.label.setText("")
            bg = "transparent"

        self.setStyleSheet(f"""
            CheckableCell {{
                background-color: {bg};
                border: 1px solid {border_color};
            }}
        """)

    def mousePressEvent(self, event):
        self.is_checked = not self.is_checked
        self.update_style()
        dialog = self.window()
        if hasattr(dialog, 'on_cell_clicked'):
            dialog.on_cell_clicked(self)


class NewKripkeFrameDialog(QDialog):
    def __init__(
        self,
        signature_dict: Dict[str, Signature],
        is_dark_mode: bool = False,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.setWindowTitle("Create New Kripke Frame")
        self.resize(750, 650)

        self.signature_dict = signature_dict
        self.is_dark_mode = is_dark_mode

        self.created_worlds: Dict[str, World] = {}
        self.relations_data: Dict[str, Dict[str, Set[str]]] = defaultdict(lambda: defaultdict(set))
        self.current_action_context: Optional[str] = None

        self.main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.main_layout.addWidget(self.tabs)

        self.tab_general = QWidget()
        self.setup_general_tab()
        self.tabs.addTab(self.tab_general, "1. Signature & States")

        self.tab_relations = QWidget()
        self.setup_relations_tab()
        self.tabs.addTab(self.tab_relations, "2. Accessibility Relations")

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        self.main_layout.addWidget(buttons)

    def setup_general_tab(self):
        layout = QVBoxLayout(self.tab_general)
        form = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., Frame_1")

        self.combo_signature = QComboBox()
        self.combo_signature.addItems(sorted(list(self.signature_dict.keys())))
        self.combo_signature.currentTextChanged.connect(self.on_signature_changed)

        self.combo_initial = QComboBox()

        form.addRow("Frame Name:", self.name_input)
        form.addRow("Signature:", self.combo_signature)
        form.addRow("Initial State:", self.combo_initial)
        layout.addLayout(form)

        # World creator box
        layout.addWidget(QLabel("<b>Create States:</b>"))
        world_create_layout = QHBoxLayout()
        self.world_long_input = QLineEdit()
        self.world_long_input.setPlaceholderText("Long Name (e.g. State_1)")
        self.world_short_input = QLineEdit()
        self.world_short_input.setPlaceholderText("Short Name (e.g. s1)")
        btn_add_world = QPushButton("Add State")
        btn_add_world.clicked.connect(self.add_world)
        btn_remove_world = QPushButton("Remove Selected")
        btn_remove_world.clicked.connect(self.remove_world)

        world_create_layout.addWidget(self.world_long_input)
        world_create_layout.addWidget(self.world_short_input)
        world_create_layout.addWidget(btn_add_world)
        world_create_layout.addWidget(btn_remove_world)
        layout.addLayout(world_create_layout)

        self.list_worlds = QListWidget()
        layout.addWidget(self.list_worlds)

    def on_signature_changed(self, sig_name: str):
        self.relations_data.clear()

    def add_world(self):
        long_name = self.world_long_input.text().strip()
        short_name = self.world_short_input.text().strip()

        if not long_name or not short_name:
            QMessageBox.warning(self, "Input Error", "Both long and short state names are required.")
            return

        if short_name in self.created_worlds:
            QMessageBox.warning(self, "Duplicate State", f"State with short name '{short_name}' already exists.")
            return

        for w in self.created_worlds.values():
            if w.name_long == long_name:
                QMessageBox.warning(self, "Duplicate State", f"State with long name '{long_name}' already exists.")
                return

        world = World(name_long=long_name, name_short=short_name)
        self.created_worlds[short_name] = world
        self.list_worlds.addItem(f"{long_name} ({short_name})")
        self.combo_initial.addItem(short_name)

        self.world_long_input.clear()
        self.world_short_input.clear()

    def remove_world(self):
        selected_row = self.list_worlds.currentRow()
        if selected_row < 0:
            return

        item_text = self.list_worlds.item(selected_row).text()
        short_name = item_text.split("(")[-1].replace(")", "").strip()

        if short_name in self.created_worlds:
            del self.created_worlds[short_name]

        self.list_worlds.takeItem(selected_row)
        idx = self.combo_initial.findText(short_name)
        if idx >= 0:
            self.combo_initial.removeItem(idx)

        for act in self.relations_data:
            if short_name in self.relations_data[act]:
                del self.relations_data[act][short_name]
            for src in self.relations_data[act]:
                self.relations_data[act][src].discard(short_name)

    def setup_relations_tab(self):
        layout = QVBoxLayout(self.tab_relations)
        nav_layout = QHBoxLayout()
        nav_layout.addWidget(QLabel("<b>Action Context:</b>"))
        self.combo_action_context = QComboBox()
        self.combo_action_context.currentTextChanged.connect(self.switch_action_context)
        nav_layout.addWidget(self.combo_action_context)
        layout.addLayout(nav_layout)

        layout.addWidget(QLabel("Check accessibility transitions (Row → Column):"))
        self.table_relations = QTableWidget()
        self.table_relations.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table_relations.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table_relations)

    def on_tab_changed(self, index: int):
        if index == 1:
            sig_name = self.combo_signature.currentText()
            if sig_name not in self.signature_dict:
                QMessageBox.warning(self, "Invalid Signature", "Please select a valid Signature.")
                self.tabs.setCurrentIndex(0)
                return

            if not self.created_worlds:
                QMessageBox.warning(self, "No States", "Please define at least one state first.")
                self.tabs.setCurrentIndex(0)
                return

            sig = self.signature_dict[sig_name]
            actions = sorted(list(sig.actions))
            if not actions:
                QMessageBox.warning(self, "No Actions", "The selected signature contains no actions.")
                self.tabs.setCurrentIndex(0)
                return

            self.combo_action_context.blockSignals(True)
            self.combo_action_context.clear()
            self.combo_action_context.addItems(actions)
            self.combo_action_context.blockSignals(False)

            world_shorts = sorted(list(self.created_worlds.keys()))
            n = len(world_shorts)
            self.table_relations.setRowCount(n)
            self.table_relations.setColumnCount(n)
            self.table_relations.setHorizontalHeaderLabels(world_shorts)
            self.table_relations.setVerticalHeaderLabels(world_shorts)

            self.switch_action_context(self.combo_action_context.currentText())

    def switch_action_context(self, action: str):
        if not action:
            return
        self.current_action_context = action
        self.load_data_to_matrix(action)

    def load_data_to_matrix(self, action: str):
        self.table_relations.setUpdatesEnabled(False)
        self.table_relations.clearContents()
        active_bg = "#2a82da" if self.is_dark_mode else "#3daee9"
        action_rel = self.relations_data[action]

        for r in range(self.table_relations.rowCount()):
            src = self.table_relations.verticalHeaderItem(r).text()
            targets = action_rel.get(src, set())
            for c in range(self.table_relations.columnCount()):
                tgt = self.table_relations.horizontalHeaderItem(c).text()
                was_checked = (tgt in targets)
                cell = CheckableCell(was_checked, active_bg, self.is_dark_mode, self.table_relations)
                cell.setProperty("src", src)
                cell.setProperty("tgt", tgt)
                self.table_relations.setCellWidget(r, c, cell)

        self.table_relations.setUpdatesEnabled(True)

    def on_cell_clicked(self, cell_widget: CheckableCell):
        action = self.current_action_context
        if not action:
            return
        src = cell_widget.property("src")
        tgt = cell_widget.property("tgt")
        if cell_widget.is_checked:
            self.relations_data[action][src].add(tgt)
        else:
            self.relations_data[action][src].discard(tgt)

    def validate_and_accept(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Error", "Frame Name is required.")
            return
        if not self.created_worlds:
            QMessageBox.warning(self, "Error", "Frame must contain at least one state.")
            return
        if not self.combo_initial.currentText():
            QMessageBox.warning(self, "Error", "Select an initial state.")
            return
        self.accept()

    def get_data(self) -> Tuple[str, Signature, Set[World], World, Dict[str, Dict[World, Set[World]]]]:
        name = self.name_input.text().strip()
        signature = self.signature_dict[self.combo_signature.currentText()]
        worlds_set = set(self.created_worlds.values())
        init_short = self.combo_initial.currentText()
        initial_world = self.created_worlds[init_short]

        accessibility_relation: Dict[str, Dict[World, Set[World]]] = {act: defaultdict(set) for act in signature.actions}
        for act in signature.actions:
            for src_short, tgt_shorts in self.relations_data[act].items():
                src_w = self.created_worlds.get(src_short)
                if src_w:
                    for tgt_short in tgt_shorts:
                        tgt_w = self.created_worlds.get(tgt_short)
                        if tgt_w:
                            accessibility_relation[act][src_w].add(tgt_w)

        return name, signature, worlds_set, initial_world, accessibility_relation