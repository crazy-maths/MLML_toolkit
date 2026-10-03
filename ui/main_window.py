"""
Main Application Module.

This module defines the MainWindow class, which serves as the primary user interface
for the Many-Logic Modal Structure Editor.
"""

import sys
from collections import defaultdict
from typing import Dict, Set, Any
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
    QMenu, QMessageBox, QInputDialog, QLabel, QSplitter, QLineEdit, QComboBox, 
    QTreeWidget, QTreeWidgetItem, QFrame, QPushButton, QListWidget, 
    QAbstractItemView, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QAction

from math_objects.lattice import Lattice, FilteredLattice, ManyLattice
from math_objects.structure import World, KripkeFrame, Model
from math_objects.signature import Signature
from math_objects.signature_morphism import SignatureMorphism
from math_objects.structure_morphism import KripkeFrameMorphism, ModelMorphism

from services.object_manager import ObjectManager
from services.theme_service import ThemeService
from services.json_handler import JSONHandler
from services.html_renderer import HTMLRenderer
from services.evaluation_service import EvaluationService
from services.logging_service import get_logger

from parser.formula_parser import FormulaParser
from utils.decorators import handle_ui_errors
from ui.error_dialogs import ErrorHandler
from ui.sidebar import SidebarWidget
from ui.workspace import WorkspaceWidget
from ui.interpreter import InterpreterWidget
from ui.view_logs_dialog import ViewLogsDialog

from app_object_creation import (
    NewLatticeDialog, NewFilteredLatticeDialog, NewManyLatticeDialog,
    NewKripkeFrameDialog, NewModelDialog, NewSignatureDialog, NewSignatureMorphismDialog,
    NewKripkeFrameMorphismDialog, NewModelMorphismDialog, NewReductDialog
)
from app_object_loading import MultiSelectDialog
from config.config import PATHS


class MainWindow(QMainWindow):
    """
    The main application window containing the workspace, sidebar, and tools.
    """

    def __init__(self, manager: ObjectManager, theme_service: ThemeService):
        """Initializes the main window and internal storage structures."""
        super().__init__()
        self.setWindowTitle("Many-Logic Modal Structure Editor")
        self.resize(1100, 750)
        
        self.manager = manager
        self.theme_service = theme_service
        self.config_file = PATHS["config"]

        self.setup_ui()
        self.create_menu()
        
        self.load_user_config()
        self.apply_theme()
        get_logger("MainWindow").info("MainWindow initialized successfully.")

    def load_user_config(self) -> None:
        try:
            config = JSONHandler.load_config(self.config_file)
            self.theme_service.is_dark_mode = config.get("dark_mode", False)
        except Exception as e:
            ErrorHandler.show_warning("Config Warning", "Could not load user preferences. Using defaults.", self)
            self.theme_service.is_dark_mode = False

    def save_user_config(self) -> None:
        try:
            config = {"dark_mode": self.theme_service.is_dark_mode}
            JSONHandler.save_config(self.config_file, config)
        except Exception as e:
            ErrorHandler.show_error("Save Error", f"Could not save user preferences: {str(e)}", self)

    def apply_theme(self) -> None:
        try:
            app = QApplication.instance()
            app.setStyle("Fusion")
            app.setStyleSheet(self.theme_service.get_stylesheet())
            
            legend_btn = self.interpreter.btn_legend 
            color = self.get_theme_color("accent")
            legend_btn.setStyleSheet(f"font-weight: bold; color: {color};")
            
            if hasattr(self, 'action_dark_mode'):
                self.action_dark_mode.setText("Toggle Light Mode" if self.theme_service.is_dark_mode else "Toggle Dark Mode")
        except Exception as e:
            get_logger("MainWindow").error(f"Theme application failed: {str(e)}")

    def get_theme_color(self, role: str) -> str:
        return self.theme_service.get_color(role)

    def toggle_dark_mode(self) -> None:
        try:
            self.theme_service.toggle()
            self.apply_theme()
            self.save_user_config()
            item = self.sidebar.tree.currentItem()
            if item: self.on_tree_item_clicked(item)
        except Exception as e:
            ErrorHandler.show_error("Theme Error", f"Could not toggle theme: {str(e)}", self)

    def setup_ui(self) -> None:
        """Main entry for UI assembly."""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.splitter)

        self._setup_sidebar()
        self._setup_workspace_and_interpreter()
        
        self.splitter.setSizes([300, 700])

    def _setup_sidebar(self):
        """Assembles the sidebar widget and connects its signals."""
        self.sidebar = SidebarWidget()
        self.sidebar.layout().setContentsMargins(5, 5, 5, 5)
        self.sidebar.init_tree_categories([
            "Signatures", "Signature Morphisms", "Lattices", 
            "Filtered Lattices", "Many Lattices", "Kripke Frames", "Models",
            "Kripke Frame Morphisms", "Model Morphisms"
        ])
        
        self.sidebar.item_clicked.connect(self.on_tree_item_clicked)
        self.sidebar.context_menu_requested.connect(self.open_tree_context_menu)
        
        self.splitter.addWidget(self.sidebar)

    def _setup_workspace_and_interpreter(self):
        """Assembles the workspace and interpreter into the right-hand panel."""
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(5, 5, 5, 5)
        right_layout.setSpacing(5)
        
        self.workspace = WorkspaceWidget()
        self.workspace.hasse_requested.connect(self.show_current_hasse)
        self.workspace.model_requested.connect(self.visualize_current_model)
        self.workspace.structure_morphism_requested.connect(self.visualize_current_structure_morphism)
        
        self.interpreter = InterpreterWidget()
        self.interpreter.evaluate_requested.connect(self.evaluate_formula)
        self.interpreter.validity_requested.connect(self.check_model_validity)
        self.interpreter.symbol_inserted.connect(self.insert_symbol)
        self.interpreter.btn_legend.clicked.connect(self.show_symbol_legend)
        self.interpreter.combo_models.currentIndexChanged.connect(self.update_world_combo)
        
        right_layout.addWidget(self.workspace)
        right_layout.addWidget(self.interpreter)
        right_layout.addStretch(1)
        
        self.splitter.addWidget(right_container)
    
    def insert_symbol(self, text: str) -> None:
        self.interpreter.formula_input.insert(text)
        self.interpreter.formula_input.setFocus()

    def show_symbol_legend(self) -> None:
        html = HTMLRenderer.render_symbol_legend(
            is_dark=self.theme_service.is_dark_mode,
            info_color=self.get_theme_color('info')
        )
        ErrorHandler.show_info("Symbol Legend", html, self)

    def show_math_definitions(self) -> None:
        html = HTMLRenderer.render_mathematical_definitions(
            is_dark=self.theme_service.is_dark_mode,
            info_color=self.get_theme_color('info')
        )
        ErrorHandler.show_info("Mathematical Definitions", html, self)

    def create_menu(self) -> None:
        """Initializes the application menu bar using a data-driven approach."""
        menu_bar = self.menuBar()

        menus = [
            ("New", [
                ("Signature", self.create_new_signature),
                ("Signature Morphism", self.create_new_signature_morphism),
                ("Lattice", self.create_new_lattice),
                ("Filtered Lattice", self.create_new_filtered_lattice),
                ("Many Lattice", self.create_new_many_lattice),
                ("Kripke Frame", self.create_new_kripke_frame),
                ("Model", self.create_new_model),
                ("Reduct Model", self.create_new_reduct_model),
                ("Kripke Frame Morphism", self.create_new_kripke_frame_morphism),
                ("Model Morphism", self.create_new_model_morphism)
            ]),
            ("Load", [
                ("Signature", lambda: self.load_specific_object("Signature", "signatures", "name")),
                ("Signature Morphism", lambda: self.load_specific_object("Signature Morphism", "signature_morphisms", "name")),
                ("Lattice", lambda: self.load_specific_object("Lattice", "lattices", "name")),
                ("Filtered Lattice", lambda: self.load_specific_object("Filtered Lattice", "filtered_lattices", "filtered_lattice_name")),
                ("Many Lattice", lambda: self.load_specific_object("Many Lattice", "many_lattices", "many_lattice_name")),
                ("Kripke Frame", lambda: self.load_specific_object("Kripke Frame", "kripke_frames", "name")),
                ("Model", lambda: self.load_specific_object("Model", "models", "name")),
                ("Kripke Frame Morphism", lambda: self.load_specific_object("Kripke Frame Morphism", "kripke_frame_morphisms", "name")),
                ("Model Morphism", lambda: self.load_specific_object("Model Morphism", "model_morphisms", "name"))
            ]),
            ("Delete", [
                ("Signature", lambda: self.delete_specific_object("Signature", "signatures", "name")),
                ("Signature Morphism", lambda: self.delete_specific_object("Signature Morphism", "signature_morphisms", "name")),
                ("Lattice", lambda: self.delete_specific_object("Lattice", "lattices", "name")),
                ("Filtered Lattice", lambda: self.delete_specific_object("Filtered Lattice", "filtered_lattices", "filtered_lattice_name")),
                ("Many Lattice", lambda: self.delete_specific_object("Many Lattice", "many_lattices", "many_lattice_name")),
                ("Kripke Frame", lambda: self.delete_specific_object("Kripke Frame", "kripke_frames", "name")),
                ("Model", lambda: self.delete_specific_object("Model", "models", "name")),
                ("Kripke Frame Morphism", lambda: self.delete_specific_object("Kripke Frame Morphism", "kripke_frame_morphisms", "name")),
                ("Model Morphism", lambda: self.delete_specific_object("Model Morphism", "model_morphisms", "name"))
            ]),
            ("See", [
                ("Signatures in File", lambda: self.see_objects_in_file("signatures", "name")),
                ("Signature Morphisms in File", lambda: self.see_objects_in_file("signature_morphisms", "name")),
                ("Lattices in File", lambda: self.see_objects_in_file("lattices", "name")),
                ("Filtered Lattices in File", lambda: self.see_objects_in_file("filtered_lattices", "filtered_lattice_name")),
                ("Many Lattices in File", lambda: self.see_objects_in_file("many_lattices", "many_lattice_name")),
                ("Kripke Frames in File", lambda: self.see_objects_in_file("kripke_frames", "name")),
                ("Models in File", lambda: self.see_objects_in_file("models", "name")),
                ("Kripke Frame Morphisms in File", lambda: self.see_objects_in_file("kripke_frame_morphisms", "name")),
                ("Model Morphisms in File", lambda: self.see_objects_in_file("model_morphisms", "name"))
            ])
        ]

        for menu_name, actions in menus:
            menu = menu_bar.addMenu(menu_name)
            for action_name, trigger in actions:
                menu.addAction(action_name).triggered.connect(trigger)

        view_menu = menu_bar.addMenu("View")
        self.action_dark_mode = QAction("Toggle Dark Mode", self)
        self.action_dark_mode.triggered.connect(self.toggle_dark_mode)
        view_menu.addAction(self.action_dark_mode)

        help_menu = menu_bar.addMenu("Help")
        help_menu.addAction("Symbol Legend").triggered.connect(self.show_symbol_legend)
        help_menu.addAction("Mathematical Definitions").triggered.connect(self.show_math_definitions)
        help_menu.addAction("View Logs").triggered.connect(self.open_view_logs_dialog)

    def refresh_model_combo(self) -> None:
        try:
            self.interpreter.set_model_list(list(self.manager.models.keys()))
            self.update_world_combo()
        except Exception as e:
            ErrorHandler.show_error("UI Update Error", f"Failed to refresh model list: {str(e)}", self)

    def update_world_combo(self) -> None:
        try:
            model_name = self.interpreter.get_selected_model()
            if model_name in self.manager.models:
                model = self.manager.models[model_name]
                world_names = sorted([w.name_long for w in model.worlds])
                self.interpreter.set_world_list(world_names)
        except Exception as e:
            ErrorHandler.show_error("UI Update Error", f"Failed to refresh worlds list: {str(e)}", self)
    
    def open_view_logs_dialog(self) -> None:
        try:
            log_path = Path("logs/app.log")
            dialog = ViewLogsDialog(log_path, parent=self)
            dialog.exec()
        except Exception as e:
            get_logger("MainWindow").error(f"Failed to open log dialog: {str(e)}")
            ErrorHandler.show_error("UI Error", "Could not open log viewer.", self)

    def is_object_loaded(self, category: str, name: str) -> bool:
        return self.manager.is_object_loaded(category, name)

    def register_object(self, name: str, obj: Any, type_str: str) -> None:
        self.manager.register_object(name, obj, type_str)
        
        cat_map = {
            "Signature": "Signatures",
            "Signature Morphism": "Signature Morphisms",
            "Lattice": "Lattices", 
            "Filtered Lattice": "Filtered Lattices",
            "Many Lattice": "Many Lattices", 
            "Kripke Frame": "Kripke Frames", 
            "Model": "Models",
            "Kripke Frame Morphism": "Kripke Frame Morphisms",
            "Model Morphism": "Model Morphisms"
        }
        cat = cat_map.get(type_str)
        
        if hasattr(self.sidebar, 'tree_categories') and cat in self.sidebar.tree_categories:
            parent = self.sidebar.tree_categories[cat]
            for i in range(parent.childCount()):
                if parent.child(i).text(0) == name:
                    return
            item = QTreeWidgetItem(parent)
            item.setText(0, name)
            
        if type_str == "Model": 
            self.refresh_model_combo()

    def remove_from_tree(self, category_label: str, object_name: str) -> None:
        root_item = self.sidebar.tree_categories.get(category_label)
        if not root_item: return
        for i in range(root_item.childCount()):
            child = root_item.child(i)
            if child.text(0) == object_name:
                root_item.removeChild(child)
                break

    def remove_object_from_memory(self, ui_category: str, tree_category_label: str, object_name: str) -> None:
        self.manager.delete_object(ui_category, object_name)
        self.remove_from_tree(tree_category_label, object_name)
        self.workspace.details_text.clear()
        self.statusBar().showMessage(f"Removed '{object_name}' from workspace.", 2000)
        
        if ui_category == "Model": 
            self.refresh_model_combo()

    def see_objects_in_file(self, json_key: str, name_key: str) -> None:
        filename_map = {
            "signatures": PATHS["signatures"],
            "signature_morphisms": PATHS["signature_morphisms"],
            "lattices": PATHS["lattices"],
            "filtered_lattices": PATHS["filtered_lattices"],
            "many_lattices": PATHS["many_lattices"],
            "kripke_frames": PATHS["kripke_frames"],
            "models": PATHS["models"],
            "kripke_frame_morphisms": PATHS["kripke_frame_morphisms"],
            "model_morphisms": PATHS["model_morphisms"]
        }
        fname = filename_map.get(json_key)
        if not fname:
            ErrorHandler.show_error("File Error", f"Invalid storage category key: '{json_key}'", self)
            return

        names = JSONHandler.get_names_from_json(fname, json_key, name_key)
        display_text = "\n".join(names) if names else "No items found."
        ErrorHandler.show_info(f"File Content: {fname}", display_text, self)

    def _recursive_register(self, obj: Any) -> None:
        """Recursively registers dependencies of an object to ensure they appear in the UI sidebar."""
        if isinstance(obj, ModelMorphism):
            if obj.source_model:
                if not self.is_object_loaded("Model", obj.source_model.name):
                    self.register_object(obj.source_model.name, obj.source_model, "Model")
                self._recursive_register(obj.source_model)

            if obj.target_model:
                if not self.is_object_loaded("Model", obj.target_model.name):
                    self.register_object(obj.target_model.name, obj.target_model, "Model")
                self._recursive_register(obj.target_model)

            kfm_name = getattr(obj, "kripke_frame_morphism_name", None)
            if kfm_name:
                if not self.is_object_loaded("Kripke Frame Morphism", kfm_name):
                    kfm_file = PATHS["kripke_frame_morphisms"]
                    kfm_obj = JSONHandler.load_kripke_frame_morphism_from_json(kfm_file, kfm_name)
                    if kfm_obj:
                        self.register_object(kfm_name, kfm_obj, "Kripke Frame Morphism")
                        self._recursive_register(kfm_obj)
                    else:
                        get_logger("recursive_register").warning(
                            f"Base Kripke Frame Morphism '{kfm_name}' not found on disk."
                        )
                else:
                    existing_kfm = self.manager.kripke_frame_morphisms.get(kfm_name)
                    if existing_kfm:
                        self._recursive_register(existing_kfm)

        elif isinstance(obj, KripkeFrameMorphism):
            if obj.source_frame:
                src_name = obj.source_frame.name
                if not self.is_object_loaded("Kripke Frame", src_name):
                    self.register_object(src_name, obj.source_frame, "Kripke Frame")
                self._recursive_register(obj.source_frame)

            if obj.target_frame:
                tgt_name = obj.target_frame.name
                if not self.is_object_loaded("Kripke Frame", tgt_name):
                    self.register_object(tgt_name, obj.target_frame, "Kripke Frame")
                self._recursive_register(obj.target_frame)

        elif isinstance(obj, Model):
            if not self.is_object_loaded("Model", obj.name):
                self.register_object(obj.name, obj, "Model")

            kf_name = getattr(obj, "kripke_frame_name", None)
            if kf_name:
                if not self.is_object_loaded("Kripke Frame", kf_name):
                    kf_file = PATHS["kripke_frames"]
                    kf_obj = JSONHandler.load_kripke_frame_from_json(kf_file, kf_name)
                    if kf_obj:
                        self.register_object(kf_name, kf_obj, "Kripke Frame")
                        self._recursive_register(kf_obj)
                    else:
                        get_logger("recursive_register").error(
                            f"Failed to cascade load frame '{kf_name}' for model '{obj.name}'."
                        )
                else:
                    existing_kf = self.manager.kripke_frames.get(kf_name)
                    if existing_kf:
                        self._recursive_register(existing_kf)

            if obj.many_lattice:
                ml_name = obj.many_lattice.name_many_lattice
                if not self.is_object_loaded("Many Lattice", ml_name):
                    self.register_object(ml_name, obj.many_lattice, "Many Lattice")
                self._recursive_register(obj.many_lattice)

            if hasattr(obj, 'world_lattices') and obj.world_lattices:
                for sub_lat in obj.world_lattices.values():
                    if sub_lat and not self.is_object_loaded("Lattice", sub_lat.name):
                        self.register_object(sub_lat.name, sub_lat, "Lattice")
                        self._recursive_register(sub_lat)

        elif isinstance(obj, KripkeFrame):
            if not self.is_object_loaded("Kripke Frame", obj.name):
                self.register_object(obj.name, obj, "Kripke Frame")
            if obj.signature:
                sig_name = obj.signature.name
                if not self.is_object_loaded("Signature", sig_name):
                    self.register_object(sig_name, obj.signature, "Signature")
                self._recursive_register(obj.signature)

        elif isinstance(obj, ManyLattice):
            if not self.is_object_loaded("Many Lattice", obj.name_many_lattice):
                self.register_object(obj.name_many_lattice, obj, "Many Lattice")
            
            base_fl_name = getattr(obj, 'name_filtered_lattice', None)
            if base_fl_name and not self.is_object_loaded("Filtered Lattice", base_fl_name):
                fl_obj = JSONHandler.load_filtered_lattice_from_json(PATHS["filtered_lattices"], base_fl_name)
                if not fl_obj:
                    fl_obj = FilteredLattice(
                        base_fl_name, obj.name, obj.elements, obj.relations,
                        obj.negation_map, obj.implication_map, obj.filter
                    )
                self.register_object(base_fl_name, fl_obj, "Filtered Lattice")
                self._recursive_register(fl_obj)

            for sub_lat in getattr(obj, 'comp_sub_lat', []):
                if not self.is_object_loaded("Lattice", sub_lat.name):
                    self.register_object(sub_lat.name, sub_lat, "Lattice")
                    self._recursive_register(sub_lat)

        elif isinstance(obj, FilteredLattice):
            if not self.is_object_loaded("Filtered Lattice", obj.name_filtered_lattice):
                self.register_object(obj.name_filtered_lattice, obj, "Filtered Lattice")

            base_lat_name = getattr(obj, 'name', None)
            if base_lat_name and not self.is_object_loaded("Lattice", base_lat_name):
                base_lat = JSONHandler.load_lattice_from_json(PATHS["lattices"], base_lat_name)
                if not base_lat:
                    base_lat = Lattice(
                        base_lat_name, obj.elements, obj.relations,
                        obj.negation_map, obj.implication_map
                    )
                self.register_object(base_lat_name, base_lat, "Lattice")
                self._recursive_register(base_lat)

        elif isinstance(obj, Lattice):
            if not self.is_object_loaded("Lattice", obj.name):
                self.register_object(obj.name, obj, "Lattice")

        elif isinstance(obj, SignatureMorphism):
            if obj.source_sig and not self.is_object_loaded("Signature", obj.source_sig.name):
                self.register_object(obj.source_sig.name, obj.source_sig, "Signature")
                self._recursive_register(obj.source_sig)
            if obj.target_sig and not self.is_object_loaded("Signature", obj.target_sig.name):
                self.register_object(obj.target_sig.name, obj.target_sig, "Signature")
                self._recursive_register(obj.target_sig)
            if not self.is_object_loaded("Signature Morphism", obj.name):
                self.register_object(obj.name, obj, "Signature Morphism")

        # 9. SIGNATURE
        elif isinstance(obj, Signature):
            if not self.is_object_loaded("Signature", obj.name):
                self.register_object(obj.name, obj, "Signature")

    def load_specific_object(self, ui_category: str, json_key: str, name_key: str) -> None:
        filename_map = {
            "Signature": PATHS["signatures"],
            "Signature Morphism": PATHS["signature_morphisms"],
            "Lattice": PATHS["lattices"],
            "Filtered Lattice": PATHS["filtered_lattices"],
            "Many Lattice": PATHS["many_lattices"],
            "Kripke Frame": PATHS["kripke_frames"],
            "Model": PATHS["models"],
            "Kripke Frame Morphism": PATHS["kripke_frame_morphisms"],
            "Model Morphism": PATHS["model_morphisms"]
        }
        fname = filename_map.get(ui_category)
        if not fname: return

        names = JSONHandler.get_names_from_json(fname, json_key, name_key)
        if not names:
            ErrorHandler.show_info(f"Load {ui_category}", f"No objects found in {fname}.", self)
            return

        dialog = MultiSelectDialog(f"Load {ui_category}", names, self)
        if dialog.exec():
            for selected_name in dialog.get_selected_items():
                if self.is_object_loaded(ui_category, selected_name): continue
                try:
                    obj = None
                    if ui_category == "Signature":
                        obj = JSONHandler.load_signature_from_json(fname, selected_name)
                    elif ui_category == "Signature Morphism":
                        obj = JSONHandler.load_signature_morphism_from_json(fname, selected_name)
                    elif ui_category == "Lattice":
                        obj = JSONHandler.load_lattice_from_json(fname, selected_name)
                    elif ui_category == "Filtered Lattice":
                        obj = JSONHandler.load_filtered_lattice_from_json(fname, selected_name)
                    elif ui_category == "Many Lattice":
                        obj = JSONHandler.load_many_lattice_from_json(fname, selected_name)
                    elif ui_category == "Kripke Frame":
                        obj = JSONHandler.load_kripke_frame_from_json(fname, selected_name)
                    elif ui_category == "Model":
                        obj = JSONHandler.load_model_from_json(fname, selected_name)
                    elif ui_category == "Kripke Frame Morphism":
                        obj = JSONHandler.load_kripke_frame_morphism_from_json(fname, selected_name)
                    elif ui_category == "Model Morphism":
                        obj = JSONHandler.load_model_morphism_from_json(fname, selected_name)

                    if obj:
                        self.register_object(selected_name, obj, ui_category)
                        self._recursive_register(obj)
                        self.statusBar().showMessage(f"Loaded {selected_name} and dependencies.", 3000)
                    else:
                        ErrorHandler.show_error("Load Failed", f"Could not load '{selected_name}'. Check logs for missing dependencies.", self)
                except Exception as e:
                    ErrorHandler.show_error("Load Failed", f"Failed to load {selected_name}: {str(e)}", self)

    def delete_specific_object(self, ui_category: str, json_key: str, name_key: str) -> None:
        filename_map = {
            "Signature": PATHS["signatures"],
            "Signature Morphism": PATHS["signature_morphisms"],
            "Lattice": PATHS["lattices"], 
            "Filtered Lattice": PATHS["filtered_lattices"],
            "Many Lattice": PATHS["many_lattices"], 
            "Kripke Frame": PATHS["kripke_frames"], 
            "Model": PATHS["models"],
            "Kripke Frame Morphism": PATHS["kripke_frame_morphisms"],
            "Model Morphism": PATHS["model_morphisms"]
        }
        fname = filename_map.get(ui_category)
        if not fname: return

        names = JSONHandler.get_names_from_json(fname, json_key, name_key)
        dialog = MultiSelectDialog(f"Delete {ui_category}", names, self)
        if dialog.exec():
            to_delete = dialog.get_selected_items()
            if not to_delete: return
            if ErrorHandler.ask_confirmation("Confirm Deletion", f"Delete {len(to_delete)} item(s)?", self):
                handler_map = {
                    "Signature": JSONHandler.delete_signature_from_json,
                    "Signature Morphism": JSONHandler.delete_signature_morphism_from_json,
                    "Lattice": JSONHandler.delete_lattice_from_json,
                    "Filtered Lattice": JSONHandler.delete_filtered_lattice_from_json,
                    "Many Lattice": JSONHandler.delete_many_lattice_from_json,
                    "Kripke Frame": JSONHandler.delete_kripke_frame_from_json,
                    "Model": JSONHandler.delete_model_from_json,
                    "Kripke Frame Morphism": JSONHandler.delete_kripke_frame_morphism_from_json,
                    "Model Morphism": JSONHandler.delete_model_morphism_from_json
                }
                cat_map = {
                    "Signature": "Signatures",
                    "Signature Morphism": "Signature Morphisms",
                    "Lattice": "Lattices", 
                    "Filtered Lattice": "Filtered Lattices",
                    "Many Lattice": "Many Lattices", 
                    "Kripke Frame": "Kripke Frames", 
                    "Model": "Models",
                    "Kripke Frame Morphism": "Kripke Frame Morphisms",
                    "Model Morphism": "Model Morphisms"
                }
                handler = handler_map[ui_category]
                tree_cat = cat_map[ui_category]
                
                for name in to_delete:
                    handler(fname, name)
                    self.remove_object_from_memory(ui_category, tree_cat, name)
    
    @handle_ui_errors
    def create_new_signature(self, checked=False) -> None:
        dialog = NewSignatureDialog(self)
        if dialog.exec():
            name, props, actions = dialog.get_data()
            sig = Signature(name, props, actions)
            if JSONHandler.save_signature_to_json(PATHS["signatures"], sig):
                self.register_object(name, sig, "Signature")
                self.statusBar().showMessage(f"Success: Signature '{name}' created.", 5000)

    @handle_ui_errors
    def create_new_signature_morphism(self, checked=False) -> None:
        sig_names = JSONHandler.get_names_from_json(PATHS["signatures"], "signatures", "name")
        if not sig_names:
            raise ValueError("No signatures found. Create a Signature first.")
        sig_map = {name: JSONHandler.load_signature_from_json(PATHS["signatures"], name) for name in sig_names}
        
        dialog = NewSignatureMorphismDialog(sig_map, self)
        if dialog.exec():
            name, src_sig, tgt_sig, prop_map, act_map = dialog.get_data()
            sm = SignatureMorphism(name, src_sig, tgt_sig, prop_map, act_map)
            
            valid, errors = sm.verify_morphism()
            if not valid:
                raise ValueError("\n".join(errors))
                
            if JSONHandler.save_signature_morphism_to_json(PATHS["signature_morphisms"], sm):
                self.register_object(name, sm, "Signature Morphism")
                self.statusBar().showMessage(f"Success: Signature Morphism '{name}' created.", 5000)
    
    @handle_ui_errors
    def create_new_lattice(self, checked=False) -> None:
        dialog = NewLatticeDialog(self)
        if dialog.exec():
            name, elements, relations, negation, implication = dialog.get_data()
            lat = Lattice(name, elements, relations, negation, implication)
            if JSONHandler.save_lattice_to_json(PATHS["lattices"], lat):
                self.register_object(name, lat, "Lattice")
                self._recursive_register(lat)
                self.statusBar().showMessage(f"Success: Lattice '{name}' created.", 5000)

    @handle_ui_errors
    def create_new_filtered_lattice(self, checked=False) -> None:
        lattice_names = JSONHandler.get_names_from_json(PATHS["lattices"], "lattices", "name")
        if not lattice_names: raise ValueError("No lattices found. Create a Lattice first.")
        lattices_map = {name: JSONHandler.load_lattice_from_json(PATHS["lattices"], name) for name in lattice_names}
        
        dialog = NewFilteredLatticeDialog(lattices_map, self)
        if dialog.exec():
            new_name, base_lat_name, filter_set = dialog.get_data()
            base_lat = lattices_map[base_lat_name]
            fl = FilteredLattice(new_name, base_lat_name, base_lat.elements, base_lat.relations, 
                                 base_lat.negation_map, base_lat.implication_map, filter_set)
            if JSONHandler.save_filtered_lattice_to_json(PATHS["filtered_lattices"], fl):
                self.register_object(new_name, fl, "Filtered Lattice")
                self._recursive_register(fl)
                self.statusBar().showMessage(f"Success: Filtered Lattice '{new_name}' created.", 5000)

    @handle_ui_errors
    def create_new_many_lattice(self, checked=False) -> None:
        fl_names = JSONHandler.get_names_from_json(PATHS["filtered_lattices"], "filtered_lattices", "filtered_lattice_name")
        if not fl_names: raise ValueError("Filtered Lattices must exist first.")
        fl_map = {name: JSONHandler.load_filtered_lattice_from_json(PATHS["filtered_lattices"], name) for name in fl_names}
        lat_names = JSONHandler.get_names_from_json(PATHS["lattices"], "lattices", "name")
        lat_map = {name: JSONHandler.load_lattice_from_json(PATHS["lattices"], name) for name in lat_names}

        dialog = NewManyLatticeDialog(fl_map, lat_map, self)
        if dialog.exec():
            new_name, base_fl_name, selected_generated, existing_names, interp_mode = dialog.get_data()
            base_fl = fl_map[base_fl_name]
            base_lat = lat_map[base_fl.name]
            
            comp_sub_lat_objects = [lat_map[n] for n in existing_names if n in lat_map]

            temp_ml = ManyLattice(
                new_name, base_fl.name_filtered_lattice, base_fl.name,
                base_fl.elements, base_fl.relations, [],
                base_fl.negation_map, base_fl.implication_map, base_fl.filter
            )

            for sub_name, subset in selected_generated:
                subset_str = {str(e).strip() for e in subset}
                
                sub_relations = {
                    (str(a).strip(), str(b).strip()) 
                    for a, b in base_lat.relations 
                    if str(a).strip() in subset_str and str(b).strip() in subset_str
                }
                
                temp_sub_lat = Lattice(sub_name, subset_str, sub_relations, {}, {})
                temp_ml.comp_sub_lat = [temp_sub_lat]

                sub_negation = {}
                for a in subset_str:
                    raw_neg = base_lat.negation_map.get(a)
                    if raw_neg:
                        if raw_neg in subset_str:
                            sub_negation[a] = raw_neg
                        else:
                            projected = temp_ml.down_interpretation(temp_sub_lat, raw_neg) if interp_mode == "down" else temp_ml.up_interpretation(temp_sub_lat, raw_neg)
                            sub_negation[a] = projected

                sub_implication = {}
                for a in subset_str:
                    for b in subset_str:
                        raw_imp = base_lat.implication_map.get((a, b))
                        if raw_imp:
                            if raw_imp in subset_str:
                                sub_implication[(a, b)] = raw_imp
                            else:
                                projected = temp_ml.down_interpretation(temp_sub_lat, raw_imp) if interp_mode == "down" else temp_ml.up_interpretation(temp_sub_lat, raw_imp)
                                sub_implication[(a, b)] = projected

                sub_lat = Lattice(sub_name, subset_str, sub_relations, sub_negation, sub_implication)
                
                if JSONHandler.save_lattice_to_json(PATHS["lattices"], sub_lat):
                    self.register_object(sub_name, sub_lat, "Lattice")
                    self._recursive_register(sub_lat)
                
                comp_sub_lat_objects.append(sub_lat)

            ml = ManyLattice(new_name, base_fl.name_filtered_lattice, base_fl.name,
                             base_fl.elements, base_fl.relations, comp_sub_lat_objects,
                             base_fl.negation_map, base_fl.implication_map, base_fl.filter)
            
            if JSONHandler.save_many_lattice_to_json(PATHS["many_lattices"], ml):
                self.register_object(new_name, ml, "Many Lattice")
                self._recursive_register(ml)
                self.statusBar().showMessage(f"Success: Many Lattice '{new_name}' created.", 5000)

    @handle_ui_errors
    def create_new_kripke_frame(self, checked=False) -> None:
        sig_names = JSONHandler.get_names_from_json(PATHS["signatures"], "signatures", "name")
        if not sig_names:
            raise ValueError("No signatures found. Create a Signature first.")
            
        sig_dict = {name: JSONHandler.load_signature_from_json(PATHS["signatures"], name) for name in sig_names}
        
        dialog = NewKripkeFrameDialog(sig_dict, is_dark_mode=self.theme_service.is_dark_mode, parent=self)
        if dialog.exec():
            name, signature, worlds, initial_world, accessibility_relation = dialog.get_data()
            kf = KripkeFrame(
                name=name,
                signature=signature,
                worlds=worlds,
                initial_world=initial_world,
                accessibility_relation=accessibility_relation
            )
            
            kf_file = PATHS["kripke_frames"]
            if JSONHandler.save_kripke_frame_to_json(kf_file, kf):
                self.register_object(name, kf, "Kripke Frame")
                self._recursive_register(kf)
                self.statusBar().showMessage(f"Success: Kripke Frame '{name}' created.", 5000)

    @handle_ui_errors
    def create_new_model(self, checked=False) -> None:
        kf_file = PATHS["kripke_frames"]
        frame_names = JSONHandler.get_names_from_json(kf_file, "kripke_frames", "name")
        ml_names = JSONHandler.get_names_from_json(PATHS["many_lattices"], "many_lattices", "many_lattice_name")

        if not frame_names:
            raise ValueError("No Kripke Frames found. Create a Kripke Frame first.")
        if not ml_names:
            raise ValueError("No Many-Lattices found. Create a Many-Lattice first.")

        frames_dict = {name: JSONHandler.load_kripke_frame_from_json(kf_file, name) for name in frame_names}
        many_lattices_dict = {
            name: JSONHandler.load_many_lattice_from_json(PATHS["many_lattices"], name) 
            for name in ml_names
        }

        dialog = NewModelDialog(frames_dict, many_lattices_dict, is_dark_mode=self.theme_service.is_dark_mode, parent=self)
        if dialog.exec():
            name, frame, many_lat, world_lattices, valuations, description = dialog.get_data()
            
            model = Model(
                name=name,
                signature=frame.signature,
                worlds=frame.worlds,
                initial_world=frame.initial_world,
                many_lattice=many_lat,
                world_lattices=world_lattices,
                accessibility_relation=frame.accessibility_relation,
                description=description,
                valuations=valuations
            )
            model.kripke_frame_name = frame.name
            
            if JSONHandler.save_model_to_json(PATHS["models"], model):
                self.register_object(name, model, "Model")
                self._recursive_register(model)
                self.statusBar().showMessage(f"Success: Model '{name}' created.", 5000)

    @handle_ui_errors
    def create_new_reduct_model(self, checked=False) -> None:
        sm_file = PATHS["signature_morphisms"]
        model_file = PATHS["models"]

        sm_names = JSONHandler.get_names_from_json(sm_file, "signature_morphisms", "name")
        model_names = JSONHandler.get_names_from_json(model_file, "models", "name")

        if not sm_names:
            raise ValueError("No Signature Morphisms found. Create a Signature Morphism first.")
        if not model_names:
            raise ValueError("No Models found. Create a Model first.")

        sm_dict = {
            name: JSONHandler.load_signature_morphism_from_json(sm_file, name)
            for name in sm_names
        }
        models_dict = {
            name: JSONHandler.load_model_from_json(model_file, name)
            for name in model_names
        }

        dialog = NewReductDialog(sm_dict, models_dict, parent=self)
        if dialog.exec():
            reduct_name, morph, base_model = dialog.get_data()
            src_sig = morph.source_sig

            reduct_relations = {act: defaultdict(set) for act in src_sig.actions}
            for act_src in src_sig.actions:
                act_tgt = morph.act_map.get(act_src)
                if act_tgt and act_tgt in base_model.accessibility_relation:
                    for src_w, targets in base_model.accessibility_relation[act_tgt].items():
                        reduct_relations[act_src][src_w] = set(targets)

            reduct_valuations = {}
            for w in base_model.worlds:
                reduct_valuations[w] = {}
                base_w_vals = base_model.valuations.get(w, {})
                for prop_src in src_sig.propositions:
                    prop_tgt = morph.prop_map.get(prop_src)
                    if prop_tgt and prop_tgt in base_w_vals:
                        reduct_valuations[w][prop_src] = base_w_vals[prop_tgt]

            reduct_frame_name = f"Frame_{reduct_name}"
            reduct_frame = KripkeFrame(
                name=reduct_frame_name,
                signature=src_sig,
                worlds=base_model.worlds,
                initial_world=base_model.initial_world,
                accessibility_relation=reduct_relations
            )

            kf_file = PATHS["kripke_frames"]
            JSONHandler.save_kripke_frame_to_json(kf_file, reduct_frame)
            self.register_object(reduct_frame_name, reduct_frame, "Kripke Frame")
            self._recursive_register(reduct_frame)

            reduct_model = Model(
                name=reduct_name,
                signature=src_sig,
                worlds=base_model.worlds,
                initial_world=base_model.initial_world,
                many_lattice=base_model.many_lattice,
                world_lattices=dict(base_model.world_lattices),
                accessibility_relation=reduct_relations,
                description=f"Reduct of {base_model.name} via {morph.name}",
                valuations=reduct_valuations
            )
            reduct_model.kripke_frame_name = reduct_frame_name

            if JSONHandler.save_model_to_json(model_file, reduct_model):
                self.register_object(reduct_name, reduct_model, "Model")
                self._recursive_register(reduct_model)
                self.statusBar().showMessage(
                    f"Success: Reduct Model '{reduct_name}' created.", 5000
                )

    @handle_ui_errors
    def create_new_kripke_frame_morphism(self, checked=False) -> None:
        kf_file = PATHS["kripke_frames"]
        frame_names = JSONHandler.get_names_from_json(kf_file, "kripke_frames", "name")
        if not frame_names or len(frame_names) < 1:
            raise ValueError("At least one Kripke Frame must exist. Create a Kripke Frame first.")

        frames_dict = {
            name: JSONHandler.load_kripke_frame_from_json(kf_file, name) 
            for name in frame_names
        }

        dialog = NewKripkeFrameMorphismDialog(frames_dict, parent=self)
        if dialog.exec():
            name, src_frame, tgt_frame, world_map = dialog.get_data()
            kfm = KripkeFrameMorphism(name, src_frame, tgt_frame, world_map)

            valid, errors = kfm.verify_morphism()
            if not valid:
                raise ValueError("\n".join(errors))

            kfm_file = PATHS["kripke_frame_morphisms"]
            if JSONHandler.save_kripke_frame_morphism_to_json(kfm_file, kfm):
                self.register_object(name, kfm, "Kripke Frame Morphism")
                self._recursive_register(kfm)
                self.statusBar().showMessage(f"Success: Kripke Frame Morphism '{name}' created.", 5000)

    @handle_ui_errors
    def create_new_model_morphism(self, checked=False) -> None:
        model_file = PATHS["models"]
        kfm_file = PATHS["kripke_frame_morphisms"]

        model_names = JSONHandler.get_names_from_json(model_file, "models", "name")
        kfm_names = JSONHandler.get_names_from_json(kfm_file, "kripke_frame_morphisms", "name")

        if not model_names or len(model_names) < 1:
            raise ValueError("At least one Model must exist. Create a Model first.")
        if not kfm_names or len(kfm_names) < 1:
            raise ValueError("At least one Kripke Frame Morphism must exist. Create a Kripke Frame Morphism first.")

        models_dict = {
            name: JSONHandler.load_model_from_json(model_file, name) 
            for name in model_names
        }
        kfm_dict = {
            name: JSONHandler.load_kripke_frame_morphism_from_json(kfm_file, name)
            for name in kfm_names
        }

        dialog = NewModelMorphismDialog(models_dict, kfm_dict, parent=self)
        if dialog.exec():
            name, src_model, tgt_model, kfm_name, world_map = dialog.get_data()
            mm = ModelMorphism(name, src_model, tgt_model, world_map)
            mm.kripke_frame_morphism_name = kfm_name

            valid, errors = mm.verify_morphism()
            if not valid:
                raise ValueError("\n".join(errors))

            mm_file = PATHS["model_morphisms"]
            if JSONHandler.save_model_morphism_to_json(mm_file, mm):
                self.register_object(name, mm, "Model Morphism")
                
                if not self.is_object_loaded("Model", src_model.name):
                    self.register_object(src_model.name, src_model, "Model")
                if not self.is_object_loaded("Model", tgt_model.name):
                    self.register_object(tgt_model.name, tgt_model, "Model")

                self._recursive_register(mm)
                self.statusBar().showMessage(f"Success: Model Morphism '{name}' created.", 5000)

    @handle_ui_errors
    def on_tree_item_clicked(self, item: QTreeWidgetItem) -> None:
        parent = item.parent()
        if not parent: return
        cat, name = parent.text(0), item.text(0)

        self.workspace.btn_hasse.setEnabled(cat in ["Lattices", "Filtered Lattices", "Many Lattices"])
        self.workspace.btn_model.setEnabled(cat in ["Kripke Frames", "Models"])
        self.workspace.btn_structure_morphism.setEnabled(cat in ["Kripke Frame Morphisms", "Model Morphisms"])

        colors = {
            "header": self.get_theme_color("header"), "accent": self.get_theme_color("accent"),
            "warn": self.get_theme_color("warn"), "info": self.get_theme_color("info"),
            "error": self.get_theme_color("error"), "text": self.get_theme_color("text"),
            "subtle": self.get_theme_color("subtle")
        }

        html = ""
        if cat == "Signatures":
            html = HTMLRenderer.render_signature(self.manager.signatures.get(name), colors)
        elif cat == "Signature Morphisms":
            html = HTMLRenderer.render_signature_morphism(self.manager.signature_morphisms.get(name), colors)
        elif cat == "Lattices":
            html = HTMLRenderer.render_lattice(self.manager.lattices.get(name), colors)
        elif cat == "Filtered Lattices":
            html = HTMLRenderer.render_filtered_lattice(self.manager.filtered_lattices.get(name), colors)
        elif cat == "Many Lattices":
            html = HTMLRenderer.render_many_lattice(self.manager.many_lattices.get(name), colors)
        elif cat == "Kripke Frames":
            kf = self.manager.kripke_frames.get(name)
            html = HTMLRenderer.render_kripke_frame(kf, colors) if kf else ""
        elif cat == "Models":
            m = self.manager.models.get(name)
            html = HTMLRenderer.render_model(m, colors, is_dark=self.theme_service.is_dark_mode) if m else ""
        elif cat == "Kripke Frame Morphisms":
            kfm = self.manager.kripke_frame_morphisms.get(name)
            html = HTMLRenderer.render_structure_morphism(kfm, colors) if kfm else ""
        elif cat == "Model Morphisms":
            mm = self.manager.model_morphisms.get(name)
            html = HTMLRenderer.render_structure_morphism(mm, colors) if mm else ""

        self.workspace.details_text.setHtml(html)

    @handle_ui_errors
    def visualize_current_model(self) -> None:
        item = self.sidebar.tree.currentItem()
        if not item or not item.parent():
            raise ValueError("Please select a Kripke Frame or Model in the Project Explorer tree to visualize.")
        cat, name = item.parent().text(0), item.text(0)
        
        target = None
        if cat == "Kripke Frames":
            target = self.manager.kripke_frames.get(name)
        elif cat == "Models":
            target = self.manager.models.get(name)
            
        if target:
            target.draw_graph()

    @handle_ui_errors
    def show_current_hasse(self) -> None:
        item = self.sidebar.tree.currentItem()
        if item and item.parent():
            cat, name = item.parent().text(0), item.text(0)
            obj = None
            if cat == "Lattices": obj = self.manager.lattices.get(name)
            elif cat == "Filtered Lattices": obj = self.manager.filtered_lattices.get(name)
            elif cat == "Many Lattices": obj = self.manager.many_lattices.get(name)
            if obj: obj.draw_hasse()

    @handle_ui_errors
    def visualize_current_structure_morphism(self) -> None:
        item = self.sidebar.tree.currentItem()
        if not item or not item.parent():
            raise ValueError("Please select a Kripke Frame Morphism or Model Morphism in the Project Explorer tree to visualize.")
        cat, name = item.parent().text(0), item.text(0)
        
        target = None
        if cat == "Kripke Frame Morphisms":
            target = self.manager.kripke_frame_morphisms.get(name)
        elif cat == "Model Morphisms":
            target = self.manager.model_morphisms.get(name)
            
        if target:
            target.draw_graph()
        else:
            raise ValueError(f"Morphism '{name}' is not loaded in memory.")

    def open_tree_context_menu(self, pos: QPoint) -> None:
        item = self.sidebar.tree.itemAt(pos)
        if item and item.parent():
            name = item.text(0)
            cat = item.parent().text(0)
            menu = QMenu()
            action = menu.addAction(f"Remove {name}")
            
            if menu.exec(self.sidebar.tree.viewport().mapToGlobal(pos)) == action:
                cat_map = {
                    "Signatures": "Signature", 
                    "Signature Morphisms": "Signature Morphism",
                    "Lattices": "Lattice", 
                    "Filtered Lattices": "Filtered Lattice", 
                    "Many Lattices": "Many Lattice", 
                    "Kripke Frames": "Kripke Frame", 
                    "Models": "Model",
                    "Kripke Frame Morphisms": "Kripke Frame Morphism",
                    "Model Morphisms": "Model Morphism"
                }
                if cat in cat_map:
                    try:
                        self.remove_object_from_memory(cat_map[cat], cat, name)
                    except Exception as e:
                        ErrorHandler.show_error("Deletion Failed", f"Could not remove '{name}': {str(e)}", self)

    @handle_ui_errors
    def evaluate_formula(self) -> None:
        f_str = self.interpreter.formula_input.text().strip()
        m_name = self.interpreter.get_selected_model()
        w_name = self.interpreter.get_selected_world()
        if not f_str or not m_name or not w_name:
            raise ValueError("Select Model, World, and enter formula.")
        
        target_model = self.manager.models[m_name]
        target_world = next((w for w in target_model.worlds if w.name_long == w_name), None)
        if not target_world:
            raise ValueError(f"World '{w_name}' not found in model '{m_name}'.")
        
        mode = self.interpreter.get_interpretation_mode()
        res_str = EvaluationService.evaluate(f_str, target_model, target_world, interpretation=mode)
        
        self.interpreter.validity_label.clear()
        self.interpreter.result_label.setText(f"<b>Result</b>: {res_str}")
        self.statusBar().showMessage(f"Evaluated ({mode}): {res_str}", 5000)

    @handle_ui_errors
    def check_model_validity(self) -> None:
        f_str = self.interpreter.formula_input.text().strip()
        m_name = self.interpreter.get_selected_model()
        if not f_str or not m_name: raise ValueError("Select Model and enter formula.")
        
        target_model = self.manager.models[m_name]
        mode = self.interpreter.get_interpretation_mode()
        
        results, global_satisfaction = EvaluationService.check_validity(f_str, target_model, interpretation=mode)
        msg_results = "<br>".join([f"{p[0]}: {p[1]}" for p in results])

        self.interpreter.result_label.clear()
        self.interpreter.validity_label.setText(f"<div><b>Global Satisfaction:</b> {global_satisfaction}</div><br>{msg_results}")
        self.statusBar().showMessage(f"Checked model '{m_name}'.", 5000)