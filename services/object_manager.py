"""
Object Manager Module.

This module provides the ObjectManager class, responsible for maintaining 
the in-memory state and registry of active project components (Signatures, 
Signature Morphisms, Lattices, Filtered Lattices, Many Lattices, Worlds, Models).
"""

from typing import Dict, Any

from math_objects.lattice import Lattice, FilteredLattice, ManyLattice
from math_objects.structure import World, KripkeFrame, Model
from math_objects.signature import Signature
from math_objects.signature_morphism import SignatureMorphism
from math_objects.structure_morphism import KripkeFrameMorphism, ModelMorphism
from services.logging_service import get_logger

logger = get_logger("ObjectManager")

class ObjectManager:
    def __init__(self):
        self.signatures: Dict[str, Signature] = {}
        self.signature_morphisms: Dict[str, SignatureMorphism] = {}
        self.lattices: Dict[str, Lattice] = {}
        self.filtered_lattices: Dict[str, FilteredLattice] = {}
        self.many_lattices: Dict[str, ManyLattice] = {}
        self.worlds: Dict[str, World] = {}
        self.kripke_frames: Dict[str, KripkeFrame] = {}
        self.models: Dict[str, Model] = {}
        self.kripke_frame_morphisms: Dict[str, KripkeFrameMorphism] = {}
        self.model_morphisms: Dict[str, ModelMorphism] = {}

    @property
    def _category_map(self) -> Dict[str, Dict[str, Any]]:
        return {
            "Signature": self.signatures,
            "Signature Morphism": self.signature_morphisms,
            "Lattice": self.lattices,
            "Filtered Lattice": self.filtered_lattices,
            "Many Lattice": self.many_lattices,
            "World": self.worlds,
            "Kripke Frame": self.kripke_frames,
            "Model": self.models,
            "Kripke Frame Morphism": self.kripke_frame_morphisms,
            "Model Morphism": self.model_morphisms
        }

    def register_object(self, name: str, obj: Any, type_str: str):
        target_dict = self._category_map.get(type_str)
        if target_dict is not None:
            target_dict[name] = obj
            logger.info(f"Registered {type_str}: {name}")
        else:
            logger.warning(f"Attempted to register unknown type: {type_str}")

    def is_object_loaded(self, category: str, name: str) -> bool:
        return name in self._category_map.get(category, {})

    def get_object(self, category: str, name: str):
        target_dict = self._category_map.get(category, {})
        obj = target_dict.get(name)
        if not obj:
            logger.debug(f"Object '{name}' not found in category '{category}'")
        return obj

    def delete_object(self, ui_category: str, name: str):
        target_dict = self._category_map.get(ui_category)
        if target_dict is not None:
            if name in target_dict:
                del target_dict[name]
                logger.info(f"Deleted {ui_category}: {name}")
                return
            else:
                logger.debug(f"Object '{name}' was already absent from memory dictionary for '{ui_category}'.")
                return

        logger.warning(f"Attempted to delete non-existent object category: {ui_category} - {name}")