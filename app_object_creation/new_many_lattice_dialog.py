import itertools
from typing import Dict, List, Set, Tuple, Optional, Any
from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QComboBox, 
    QListWidget, QListWidgetItem, QLabel, QTabWidget, QWidget, 
    QVBoxLayout, QRadioButton, QButtonGroup, QHBoxLayout, QPushButton,
    QCheckBox, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QBrush


class SublatticeRowWidget(QWidget):
    """Widget displaying a checkbox, subset display, and a custom name input field."""
    def __init__(self, subset_set: Set[str], default_name: str, is_base: bool = False, parent=None):
        super().__init__(parent)
        self.subset_set = subset_set
        self.is_base = is_base
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        
        self.checkbox = QCheckBox()
        self.label_elements = QLabel("{" + ", ".join(sorted(list(subset_set))) + "}")
        self.label_elements.setMinimumWidth(180)
        
        self.name_input = QLineEdit()
        self.name_input.setText(default_name)
        self.name_input.setEnabled(False)
        
        if self.is_base:
            self.name_input.setToolTip("Base lattice already exists; its name cannot be changed.")
        else:
            self.name_input.setPlaceholderText("Lattice name...")
            self.checkbox.toggled.connect(self.name_input.setEnabled)
        
        layout.addWidget(self.checkbox)
        layout.addWidget(self.label_elements)
        layout.addWidget(QLabel("Name:"))
        layout.addWidget(self.name_input, 1)

    def is_selected(self) -> bool:
        return self.checkbox.isChecked()

    def set_selected(self, checked: bool) -> None:
        self.checkbox.setChecked(checked)

    def get_custom_name(self) -> str:
        return self.name_input.text().strip()


class NewManyLatticeDialog(QDialog):
    def __init__(self, filtered_lattice_dict: Dict[str, Any], lattice_dict: Dict[str, Any], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Create New Many Lattice")
        self.resize(780, 750)
        
        self.filtered_lattice_dict = filtered_lattice_dict
        self.lattice_dict = lattice_dict
        self.generated_row_widgets: List[SublatticeRowWidget] = []
        
        main_layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter unique name for the Many Lattice")
        self.name_input.textChanged.connect(self.update_default_names)
        
        self.combo_filtered_lat = QComboBox()
        self.combo_filtered_lat.addItems(list(filtered_lattice_dict.keys()))
        self.combo_filtered_lat.currentTextChanged.connect(self.on_base_changed)
        
        form_layout.addRow("Name:", self.name_input)
        form_layout.addRow("Base Filtered Lattice:", self.combo_filtered_lat)
        main_layout.addLayout(form_layout)

        interp_layout = QHBoxLayout()
        interp_layout.addWidget(QLabel("<b>Interpretation Mode:</b>"))
        self.radio_down = QRadioButton("Down")
        self.radio_up = QRadioButton("Up")
        self.radio_down.setChecked(True)
        self.btn_group = QButtonGroup()
        self.btn_group.addButton(self.radio_down)
        self.btn_group.addButton(self.radio_up)
        interp_layout.addWidget(self.radio_down)
        interp_layout.addWidget(self.radio_up)
        interp_layout.addStretch()
        main_layout.addLayout(interp_layout)

        self.tabs = QTabWidget()
        
        self.tab_gen = QWidget()
        gen_main_vbox = QVBoxLayout(self.tab_gen)
        
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: gray; font-style: italic;")
        gen_main_vbox.addWidget(self.status_label)

        self.list_generated = QListWidget()
        gen_main_vbox.addWidget(self.list_generated)

        gen_btn_layout = QHBoxLayout()
        btn_all_gen = QPushButton("Select All")
        btn_none_gen = QPushButton("Select None")
        btn_all_gen.clicked.connect(lambda: self.set_all_generated_checks(True))
        btn_none_gen.clicked.connect(lambda: self.set_all_generated_checks(False))
        gen_btn_layout.addWidget(btn_all_gen)
        gen_btn_layout.addWidget(btn_none_gen)
        gen_main_vbox.addLayout(gen_btn_layout)

        self.tab_existing = QWidget()
        exist_vbox = QVBoxLayout(self.tab_existing)
        
        self.exist_search = QLineEdit()
        self.exist_search.setPlaceholderText("Filter existing lattices...")
        self.exist_search.textChanged.connect(self.filter_existing)
        exist_vbox.addWidget(self.exist_search)

        self.list_existing = QListWidget()
        exist_vbox.addWidget(self.list_existing)

        exist_btn_layout = QHBoxLayout()
        btn_all_ex = QPushButton("Select All")
        btn_none_ex = QPushButton("Select None")
        btn_all_ex.clicked.connect(lambda: self.set_all_checks(self.list_existing, Qt.CheckState.Checked))
        btn_none_ex.clicked.connect(lambda: self.set_all_checks(self.list_existing, Qt.CheckState.Unchecked))
        exist_btn_layout.addWidget(btn_all_ex)
        exist_btn_layout.addWidget(btn_none_ex)
        exist_vbox.addLayout(exist_btn_layout)

        self.tabs.addTab(self.tab_gen, "Generate Sublattices")
        self.tabs.addTab(self.tab_existing, "Select Existing")
        main_layout.addWidget(self.tabs)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

        self.populate_existing_lattices()
        if filtered_lattice_dict:
            self.on_base_changed(self.combo_filtered_lat.currentText())

    def set_all_generated_checks(self, checked: bool):
        for widget in self.generated_row_widgets:
            widget.set_selected(checked)

    def set_all_checks(self, list_widget: QListWidget, state: Qt.CheckState):
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            if item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                item.setCheckState(state)

    def filter_existing(self, text):
        for i in range(self.list_existing.count()):
            item = self.list_existing.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def populate_existing_lattices(self) -> None:
        """Populates all existing lattices. Does not force or exclude anything automatically."""
        self.list_existing.clear()
        for name in sorted(self.lattice_dict.keys()):
            self.add_checkable_item(self.list_existing, name)

    def on_base_changed(self, fl_name: str) -> None:
        self.list_generated.clear()
        self.generated_row_widgets.clear()
        if not fl_name or fl_name not in self.filtered_lattice_dict: return

        fl_obj = self.filtered_lattice_dict[fl_name]
        base_name = getattr(fl_obj, 'name_lattice', getattr(fl_obj, 'name', None))

        if not base_name or base_name not in self.lattice_dict:
            self.add_header_item(self.list_generated, f"Error: Base '{base_name}' not found")
            return

        current_lattice = self.lattice_dict[base_name]
        elements = list(current_lattice.elements)

        if len(elements) > 10:
            self.add_header_item(self.list_generated, f"Lattice too large ({len(elements)} el.)")
            return

        self.status_label.setText("Calculating valid sublattices...")
        self.repaint() 

        valid_sublattices = []
        for r in range(1, len(elements) + 1):
            for subset in itertools.combinations(elements, r):
                subset_set = set(subset)
                if self.is_valid_sublattice(subset_set, current_lattice):
                    valid_sublattices.append(subset_set)

        valid_sublattices.sort(key=len)
        current_size = -1
        idx = 1
        prefix = self.name_input.text().strip() or "sublat"

        for sub in valid_sublattices:
            if len(sub) != current_size:
                current_size = len(sub)
                if current_size == len(elements):
                    self.add_header_item(self.list_generated, f"Size {current_size} (Full Base Lattice):")
                else:
                    self.add_header_item(self.list_generated, f"Size {current_size}:")

            item = QListWidgetItem(self.list_generated)
            is_full = (len(sub) == len(elements))
            
            default_name = base_name if is_full else f"{prefix}_{idx}"
            row_widget = SublatticeRowWidget(sub, default_name, is_base=is_full, parent=self)
            
            item.setSizeHint(row_widget.sizeHint())
            self.list_generated.addItem(item)
            self.list_generated.setItemWidget(item, row_widget)
            self.generated_row_widgets.append(row_widget)
            
            if not is_full:
                idx += 1

        self.status_label.setText(f"Found {len(valid_sublattices)} valid sublattices (including base lattice).")

    def update_default_names(self, text: str):
        """Updates placeholder and default names for unselected proper sublattices."""
        prefix = text.strip() or "sublat"
        idx = 1
        for widget in self.generated_row_widgets:
            if widget.is_base:
                continue
            if not widget.is_selected():
                widget.name_input.setText(f"{prefix}_{idx}")
            idx += 1

    def is_valid_sublattice(self, subset: Set[str], lattice: Any) -> bool:
        if len(subset) == 1: return True
        for a in subset:
            for b in subset:
                try:
                    if lattice.join(a, b) not in subset: return False
                    if lattice.meet(a, b) not in subset: return False
                except: return False
        return True

    def add_header_item(self, list_widget: QListWidget, text: str) -> None:
        item = QListWidgetItem(text)
        font = QFont()
        font.setBold(True)
        item.setFont(font)

        palette = list_widget.palette()
        base_color = palette.color(palette.ColorRole.Base)
        is_dark = base_color.lightness() < 128

        header_bg = base_color.lighter(150) if is_dark else base_color.darker(110)
        header_text = QColor("#ffffff") if is_dark else QColor("#000000")

        item.setBackground(QBrush(header_bg))
        item.setForeground(QBrush(header_text))
        item.setFlags(Qt.ItemFlag.NoItemFlags) 
        list_widget.addItem(item)

    def add_checkable_item(self, list_widget: QListWidget, text: str) -> None:
        item = QListWidgetItem(text)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(Qt.CheckState.Unchecked)
        list_widget.addItem(item)

    def validate_and_accept(self):
        ml_name = self.name_input.text().strip()
        if not ml_name:
            QMessageBox.warning(self, "Validation Error", "Many-Lattice name is required.")
            return

        selected_names = set()

        for widget in self.generated_row_widgets:
            if widget.is_selected():
                custom_name = widget.get_custom_name()
                if not custom_name:
                    QMessageBox.warning(self, "Validation Error", "All selected sublattices must have a non-empty name.")
                    return
                
                if custom_name in selected_names:
                    QMessageBox.warning(self, "Validation Error", f"Duplicate sublattice name in selection: '{custom_name}'.")
                    return
                
                if not widget.is_base and custom_name in self.lattice_dict:
                    QMessageBox.warning(self, "Duplicate Name", f"A lattice named '{custom_name}' is already saved. Choose a different name.")
                    return
                
                selected_names.add(custom_name)

        for i in range(self.list_existing.count()):
            item = self.list_existing.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                name = item.text()
                if name in selected_names:
                    QMessageBox.warning(self, "Validation Error", f"Duplicate sublattice name selected: '{name}'.")
                    return
                selected_names.add(name)

        if not selected_names:
            QMessageBox.warning(self, "Validation Error", "Please select at least one complete sublattice.")
            return

        self.accept()

    def get_data(self) -> Tuple[str, str, List[Tuple[str, Set[str]]], List[str], str]:
        name = self.name_input.text().strip()
        base_fl_name = self.combo_filtered_lat.currentText()
        interpretation_mode = "down" if self.radio_down.isChecked() else "up"

        generated_sublattices = []
        selected_existing_names = []

        for widget in self.generated_row_widgets:
            if widget.is_selected():
                if widget.is_base:
                    if widget.get_custom_name() not in selected_existing_names:
                        selected_existing_names.append(widget.get_custom_name())
                else:
                    generated_sublattices.append((widget.get_custom_name(), widget.subset_set))

        for i in range(self.list_existing.count()):
            item = self.list_existing.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                name = item.text()
                if name not in selected_existing_names:
                    selected_existing_names.append(name)

        return name, base_fl_name, generated_sublattices, selected_existing_names, interpretation_mode