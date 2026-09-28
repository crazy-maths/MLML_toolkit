"""
Sidebar Module.

Defines the SidebarWidget containing the Project Explorer tree for managing 
all math objects (Signatures, Morphisms, Lattices, Worlds, Models, etc.).
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem
from PyQt6.QtCore import Qt, pyqtSignal

class SidebarWidget(QWidget):
    item_clicked = pyqtSignal(object)
    context_menu_requested = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        layout.addWidget(QLabel("<b>Project Explorer:</b>"))
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(lambda pos: self.context_menu_requested.emit(pos))
        self.tree.itemClicked.connect(lambda item: self.item_clicked.emit(item))
        layout.addWidget(self.tree)

    def init_tree_categories(self, categories):
        """Initializes the tree root categories in the sidebar."""
        self.tree_categories = {}
        for cat in categories:
            item = QTreeWidgetItem(self.tree)
            item.setText(0, cat)
            item.setExpanded(True)
            self.tree_categories[cat] = item
        return self.tree_categories