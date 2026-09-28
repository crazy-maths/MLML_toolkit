from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QComboBox, QListWidget, QAbstractItemView, QMessageBox
)
from PyQt6.QtCore import Qt

class NewFilteredLatticeDialog(QDialog):
    def __init__(self, lattices, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Filtered Lattice")
        self.setMinimumWidth(400)
        self.lattices = lattices
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Filtered Lattice Name:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., MyFilteredLattice_1")
        layout.addWidget(self.name_input)

        layout.addWidget(QLabel("Select Base Lattice:"))
        self.lattice_combo = QComboBox()
        self.lattice_combo.addItems(list(self.lattices.keys()))
        self.lattice_combo.currentIndexChanged.connect(self.update_element_list)
        layout.addWidget(self.lattice_combo)

        layout.addWidget(QLabel("Select Filter Elements (Hold Ctrl to select multiple):"))
        
        self.element_search = QLineEdit()
        self.element_search.setPlaceholderText("Search elements...")
        self.element_search.textChanged.connect(self.filter_elements)
        layout.addWidget(self.element_search)

        self.element_list = QListWidget()
        self.element_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        layout.addWidget(self.element_list)

        btn_layout = QHBoxLayout()
        self.btn_ok = QPushButton("Create")
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

        self.update_element_list()

    def update_element_list(self):
        """Populates the list widget based on the selected lattice."""
        self.element_list.clear()
        selected_lat_name = self.lattice_combo.currentText()
        if selected_lat_name in self.lattices:
            elements = sorted(list(self.lattices[selected_lat_name].elements))
            self.element_list.addItems([str(e) for e in elements])

    def filter_elements(self, text):
        """Filters the visibility of elements in the list based on search text."""
        for i in range(self.element_list.count()):
            item = self.element_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def get_data(self):
        """Returns the name, base lattice name, and the set of selected elements."""
        name = self.name_input.text().strip()
        base_lattice = self.lattice_combo.currentText()
        
        selected_items = self.element_list.selectedItems()
        filter_set = {item.text() for item in selected_items}
        
        return name, base_lattice, filter_set

    def accept(self):
        """Validation before closing."""
        name, base, filter_set = self.get_data()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Please enter a name.")
            return
        if not filter_set:
            QMessageBox.warning(self, "Validation Error", "Please select at least one element for the filter.")
            return
        super().accept()