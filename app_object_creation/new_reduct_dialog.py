"""
New Reduct Dialog Module.

Facilitates the construction of a Reduct Model given a Signature Morphism
sigma: Sigma_1 -> Sigma_2 and a Model over Sigma_2.
"""

from typing import Dict, Tuple, Optional
from collections import defaultdict
from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QVBoxLayout, 
    QWidget, QMessageBox, QComboBox, QLabel, QTextEdit
)
from math_objects.structure import KripkeFrame, Model
from math_objects.signature_morphism import SignatureMorphism


class NewReductDialog(QDialog):
    def __init__(
        self,
        sig_morphism_dict: Dict[str, SignatureMorphism],
        model_dict: Dict[str, Model],
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.setWindowTitle("Create Reduct Model")
        self.resize(600, 480)

        self.sig_morphism_dict = sig_morphism_dict
        self.model_dict = model_dict

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter Reduct Model name (e.g. Model_Reduct_1)")

        self.combo_morph = QComboBox()
        self.combo_morph.addItems(sorted(list(self.sig_morphism_dict.keys())))
        self.combo_morph.currentTextChanged.connect(self.update_available_models)

        self.combo_model = QComboBox()
        self.combo_model.currentTextChanged.connect(self.update_preview)

        form.addRow("Reduct Model Name:", self.name_input)
        form.addRow("Signature Morphism (\u03c3: \u03a3\u2081 \u2192 \u03a3\u2082):", self.combo_morph)
        form.addRow("Base Model (over \u03a3\u2082):", self.combo_model)
        layout.addLayout(form)

        layout.addWidget(QLabel("<b>Construction Details:</b>"))
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        layout.addWidget(self.preview_text)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if self.combo_morph.count() > 0:
            self.update_available_models()

    def update_available_models(self) -> None:
        morph_name = self.combo_morph.currentText()
        self.combo_model.blockSignals(True)
        self.combo_model.clear()

        if morph_name in self.sig_morphism_dict:
            morph = self.sig_morphism_dict[morph_name]
            target_sig = morph.target_sig

            matching_models = [
                m_name for m_name, m_obj in self.model_dict.items()
                if (m_obj.signature.name == target_sig.name or
                    (m_obj.signature.propositions == target_sig.propositions and
                     m_obj.signature.actions == target_sig.actions))
            ]
            self.combo_model.addItems(sorted(matching_models))

        self.combo_model.blockSignals(False)
        self.update_preview()

    def update_preview(self) -> None:
        morph_name = self.combo_morph.currentText()
        model_name = self.combo_model.currentText()

        if not (morph_name in self.sig_morphism_dict and model_name in self.model_dict):
            self.preview_text.setPlainText("Select a valid Signature Morphism and Base Model.")
            return

        morph = self.sig_morphism_dict[morph_name]
        base_model = self.model_dict[model_name]
        source_sig = morph.source_sig

        details = [
            f"Source Signature (\u03a3\u2081): {source_sig.name}",
            f"Target Signature (\u03a3\u2082): {morph.target_sig.name}",
            f"Base Model: {base_model.name} (over \u03a3\u2082)",
            f"States: {len(base_model.worlds)} states preserved",
            f"Initial State: {base_model.initial_world.name_short if base_model.initial_world else 'None'}",
            "",
            "Action Mapping (x -a-> y in Reduct \u21d4 x -\u03c3(a)-> y in Base):"
        ]
        for a in sorted(source_sig.actions):
            details.append(f"  {a} \u21a6 {morph.act_map.get(a, 'None')}")

        details.append("")
        details.append("Proposition Valuation Mapping (V(w, p) = V_base(w, \u03c3(p))):")
        for p in sorted(source_sig.propositions):
            details.append(f"  {p} \u21a6 {morph.prop_map.get(p, 'None')}")

        self.preview_text.setPlainText("\n".join(details))

    def validate_and_accept(self) -> None:
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Reduct Model name is required.")
            return

        if not self.combo_model.currentText():
            QMessageBox.warning(
                self, 
                "Validation Error", 
                "No model over the target signature \u03a3\u2082 is available."
            )
            return

        self.accept()

    def get_data(self) -> Tuple[str, SignatureMorphism, Model]:
        name = self.name_input.text().strip()
        morph = self.sig_morphism_dict[self.combo_morph.currentText()]
        base_model = self.model_dict[self.combo_model.currentText()]
        return name, morph, base_model