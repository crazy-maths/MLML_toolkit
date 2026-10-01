"""
Workspace Module.

This module defines the WorkspaceWidget class, which handles the display of object 
details and action buttons for visualization (such as Hasse diagrams and Model graphs).
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QFrame, QLabel, QSizePolicy
from PyQt6.QtCore import pyqtSignal, Qt

class WorkspaceWidget(QWidget):
    hasse_requested = pyqtSignal()
    model_requested = pyqtSignal()
    structure_morphism_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setSpacing(5)

        label_details = QLabel("Object Details:")
        label_details.setStyleSheet("font-weight: bold;")
        layout.addWidget(label_details)

        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setPlaceholderText("Select an object in the tree to view details.")
        self.details_text.setMaximumHeight(250)
        self.details_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.details_text)

        btn_layout = QHBoxLayout()
        self.btn_hasse = QPushButton("Show Hasse Diagram")
        self.btn_hasse.setEnabled(False)
        self.btn_hasse.clicked.connect(self.hasse_requested.emit)
        
        self.btn_model = QPushButton("Show Frame")
        self.btn_model.setEnabled(False)
        self.btn_model.clicked.connect(self.model_requested.emit)

        self.btn_structure_morphism = QPushButton("Show Structure Morphism")
        self.btn_structure_morphism.setEnabled(False)
        self.btn_structure_morphism.clicked.connect(self.structure_morphism_requested.emit)
        
        btn_layout.addWidget(self.btn_hasse)
        btn_layout.addWidget(self.btn_model)
        btn_layout.addWidget(self.btn_structure_morphism)
        layout.addLayout(btn_layout)
        
        layout.addWidget(QFrame(frameShape=QFrame.Shape.HLine))