"""
New Signature Dialog Module.

Facilitates the creation of a Signature object consisting of propositions and actions.
"""

from typing import Set, Tuple, Optional
from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QVBoxLayout, QWidget, QMessageBox
)

class NewSignatureDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Create New Signature")
        self.resize(400, 250)
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Unique Signature Name (e.g. Sig_1)")
        
        self.props_input = QLineEdit()
        self.props_input.setPlaceholderText("Comma-separated (e.g. p, q, r)")
        
        self.actions_input = QLineEdit()
        self.actions_input.setPlaceholderText("Comma-separated (e.g. a, b, knows)")
        
        form.addRow("Name:", self.name_input)
        form.addRow("Propositions:", self.props_input)
        form.addRow("Actions:", self.actions_input)
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def validate_and_accept(self) -> None:
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Error", "Signature name is required.")
            return
        self.accept()

    def get_data(self) -> Tuple[str, Set[str], Set[str]]:
        name = self.name_input.text().strip()
        props = {p.strip() for p in self.props_input.text().split(",") if p.strip()}
        actions = {a.strip() for a in self.actions_input.text().split(",") if a.strip()}
        return name, props, actions