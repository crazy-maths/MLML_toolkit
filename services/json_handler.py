"""
JSON Handler Module.

This module provides the JSONHandler class, a static utility for reading, writing and deleting
the project's data structures (Lattices, Filtered Lattices, Many Lattices, Worlds, Models) to JSON files.
It handles serialization, error checking, and referential integrity reconstruction.
"""

import json
import re
import os
from ast import literal_eval
from typing import Optional, List, Dict, Any, Set
from collections import defaultdict

from config.config import PATHS
from services.logging_service import get_logger

from math_objects.lattice import Lattice, FilteredLattice, ManyLattice
from math_objects.structure import World, KripkeFrame, Model
from math_objects.signature import Signature
from math_objects.signature_morphism import SignatureMorphism
from math_objects.structure_morphism import KripkeFrameMorphism, ModelMorphism

logger = get_logger("JSONHandler")


class JSONHandler:

    @staticmethod
    def _load_safe(filename: str) -> Dict[str, Any]:
        """Safely loads JSON data with explicit encoding and existence checks."""
        if not os.path.exists(filename) or os.path.getsize(filename) == 0:
            return {}
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load {filename}: {str(e)}")
            return {}

    @staticmethod
    def _compact_json(data: Dict[str, Any]) -> str:
        """Formats JSON to keep lists and relation tuples on one line for readability."""
        json_str = json.dumps(data, indent=4)
        # Compact simple lists [ "a", "b" ]
        json_str = re.sub(r'\[\s+("[^"]+",?)\s+\]', r'[\1]', json_str)
        # Compact tuples [ "a", "b" ]
        json_str = re.sub(r'\[\s+("[^"]+",)\s+("[^"]+")\s+\]', r'[\1 \2]', json_str)
        # Compact nested lists often used in relations
        json_str = re.sub(r'\[\s+((?:\["[^"]+",\s*"[^"]+"\](?:,\s*)?)+)\s+\]', lambda m: f"[{m.group(1)}]", json_str)
        return json_str

    @staticmethod
    def load_config(filename: str) -> Dict[str, Any]:
        return JSONHandler._load_safe(filename)

    @staticmethod
    def save_config(filename: str, config: Dict[str, Any]) -> bool:
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error saving config to {filename}: {str(e)}")
            return False

    # ==========================================
    #                 SIGNATURE
    # ==========================================

    @staticmethod
    def save_signature_to_json(filename: str, sig: Signature) -> bool:
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            data = JSONHandler._load_safe(filename)
            if 'signatures' not in data: data['signatures'] = []
            
            sig_list = [s for s in data['signatures'] if s.get('name') != sig.name]
            sig_list.append({
                "name": sig.name,
                "propositions": list(sig.propositions),
                "actions": list(sig.actions)
            })
            data['signatures'] = sig_list
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(JSONHandler._compact_json(data))
            return True
        except Exception as e:
            logger.error(f"Error saving signature '{sig.name}': {e}")
            return False

    @staticmethod
    def load_signature_from_json(filename: str, name: str) -> Optional[Signature]:
        data = JSONHandler._load_safe(filename)
        for s_data in data.get('signatures', []):
            if s_data.get('name') == name:
                return Signature(
                    name=name,
                    propositions=set(s_data.get('propositions', [])),
                    actions=set(s_data.get('actions', []))
                )
        return None

    @staticmethod
    def delete_signature_from_json(filename: str, name: str) -> bool:
        try:
            data = JSONHandler._load_safe(filename)
            data['signatures'] = [s for s in data.get('signatures', []) if s.get('name') != name]
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(JSONHandler._compact_json(data))
            return True
        except Exception as e:
            logger.error(f"Error deleting signature '{name}': {e}")
            return False

    # ==========================================
    #            SIGNATURE MORPHISM
    # ==========================================

    @staticmethod
    def save_signature_morphism_to_json(filename: str, sm: SignatureMorphism) -> bool:
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            data = JSONHandler._load_safe(filename)
            if 'signature_morphisms' not in data: data['signature_morphisms'] = []
            
            sm_list = [item for item in data['signature_morphisms'] if item.get('name') != sm.name]
            sm_list.append({
                "name": sm.name,
                "source_sig": sm.source_sig.name,
                "target_sig": sm.target_sig.name,
                "prop_map": sm.prop_map,
                "act_map": sm.act_map
            })
            data['signature_morphisms'] = sm_list
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(JSONHandler._compact_json(data))
            return True
        except Exception as e:
            logger.error(f"Error saving signature morphism '{sm.name}': {e}")
            return False

    @staticmethod
    def load_signature_morphism_from_json(filename: str, name: str, signatures_file: str = PATHS["signatures"]) -> Optional[SignatureMorphism]:
        data = JSONHandler._load_safe(filename)
        for item in data.get('signature_morphisms', []):
            if item.get('name') == name:
                try:
                    src_name = item.get('source_sig')
                    tgt_name = item.get('target_sig')
                    src_sig = JSONHandler.load_signature_from_json(signatures_file, src_name)
                    tgt_sig = JSONHandler.load_signature_from_json(signatures_file, tgt_name)
                    if not src_sig or not tgt_sig:
                        logger.error(f"Failed to load underlying signatures for morphism '{name}'")
                        return None
                    return SignatureMorphism(
                        name=name,
                        source_sig=src_sig,
                        target_sig=tgt_sig,
                        prop_map=item.get('prop_map', {}),
                        act_map=item.get('act_map', {})
                    )
                except Exception as e:
                    logger.error(f"Error loading signature morphism '{name}': {e}")
                    return None
        return None

    @staticmethod
    def delete_signature_morphism_from_json(filename: str, name: str) -> bool:
        try:
            data = JSONHandler._load_safe(filename)
            data['signature_morphisms'] = [item for item in data.get('signature_morphisms', []) if item.get('name') != name]
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(JSONHandler._compact_json(data))
            return True
        except Exception as e:
            logger.error(f"Error deleting signature morphism '{name}': {e}")
            return False

    # ==========================================
    #                 LATTICE
    # ==========================================

    @staticmethod
    def load_lattice_from_json(filename: str, lattice_name: str) -> Optional[Lattice]:
        data = JSONHandler._load_safe(filename)
            
        if 'lattices' in data and isinstance(data['lattices'], list):
            for lattice_data in data['lattices']:
                name = lattice_data.get('name')

                if name == lattice_name:
                    try:
                        elements = set(lattice_data.get('elements', []))
                        relations = set(tuple(rel) for rel in lattice_data.get('relations', []))
                        negation_map = lattice_data.get('negation_map', {})

                        # Robustly load implication map (converting string keys back to tuples)
                        implication_map_raw = lattice_data.get('implication_map', {})
                        implication_map = {}
                        for pair_str, value in implication_map_raw.items():
                            try:
                                key = literal_eval(pair_str)
                                if isinstance(key, (list, tuple)):
                                    implication_map[tuple(key)] = value
                            except (ValueError, SyntaxError) as e:
                                logger.warning(f"Failed to parse implication map key '{pair_str}' for lattice '{lattice_name}': {e}")

                        if elements and relations:
                            return Lattice(name, elements, relations, negation_map, implication_map)
                    except Exception as e:
                        logger.error(f"Error creating Lattice object for '{name}': {e}")
                        return None
        
        logger.warning(f"Lattice '{lattice_name}' not found in {filename}.")
        return None

    @staticmethod
    def save_lattice_to_json(filename: str, new_lattice: Lattice) -> bool:
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            data = JSONHandler._load_safe(filename)
            if 'lattices' not in data: data['lattices'] = []

            l_list = [l for l in data['lattices'] if l.get('name') != new_lattice.name]
            
            imp_map_str = {str(k): v for k, v in new_lattice.implication_map.items()}
            
            l_dict = {
                "name": new_lattice.name,
                "elements": list(new_lattice.elements),
                "relations": [list(r) for r in new_lattice.relations],
                "negation_map": new_lattice.negation_map,
                "implication_map": imp_map_str
            }
            l_list.append(l_dict)
            data['lattices'] = l_list
            
            with open(filename, 'w', encoding='utf-8') as f: 
                f.write(JSONHandler._compact_json(data))
            return True
        except Exception as e:
            logger.error(f"Error saving lattice '{new_lattice.name}' to {filename}: {str(e)}")
            return False
    
    @staticmethod
    def delete_lattice_from_json(filename: str, lattice_name: str) -> None:
        data = JSONHandler._load_safe(filename)
        if 'lattices' not in data: return

        data['lattices'] = [l for l in data['lattices'] if l.get('name') != lattice_name]

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(JSONHandler._compact_json(data))
            logger.info(f"Lattice '{lattice_name}' deleted.")
        except Exception as e:
            logger.error(f"Delete Error for lattice '{lattice_name}': {e}")

    # ==========================================
    #             FILTERED LATTICE
    # ==========================================

    @staticmethod
    def load_filtered_lattice_from_json(filename: str, filtered_lattice_name: str, lattices_file: str = PATHS["lattices"]) -> Optional[FilteredLattice]:
        data = JSONHandler._load_safe(filename)
            
        if 'filtered_lattices' in data:
            for fl_data in data['filtered_lattices']:
                if fl_data.get('filtered_lattice_name') == filtered_lattice_name:
                    try:
                        name_lattice = fl_data.get('lattice_name')
                        base = JSONHandler.load_lattice_from_json(lattices_file, name_lattice)
                        if not base: 
                            logger.error(f"Failed to load base lattice '{name_lattice}' for filtered lattice '{filtered_lattice_name}'")
                            return None

                        filter_set = set(fl_data.get('filter', []))
                        
                        return FilteredLattice(
                            filtered_lattice_name, name_lattice, 
                            base.elements, base.relations, 
                            base.negation_map, base.implication_map, filter_set
                        )
                    except Exception as e:
                        logger.error(f"Error loading Filtered Lattice '{filtered_lattice_name}': {e}")
                        return None
        return None

    @staticmethod
    def save_filtered_lattice_to_json(filename: str, new_fl: FilteredLattice) -> bool:
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            data = JSONHandler._load_safe(filename)
            if 'filtered_lattices' not in data: data['filtered_lattices'] = []
            
            fl_list = [fl for fl in data['filtered_lattices'] if fl.get('filtered_lattice_name') != new_fl.name_filtered_lattice]
            
            fl_dict = {
                "filtered_lattice_name": new_fl.name_filtered_lattice,
                "lattice_name": new_fl.name,
                "filter": list(new_fl.filter)
            }
            
            fl_list.append(fl_dict)
            data['filtered_lattices'] = fl_list
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(JSONHandler._compact_json(data))
            
            logger.info(f"Filtered Lattice '{new_fl.name_filtered_lattice}' saved successfully.")
            return True
        except Exception as e:
            logger.error(f"Save Error for filtered lattice '{new_fl.name_filtered_lattice}': {e}")
            return False

    @staticmethod
    def delete_filtered_lattice_from_json(filename: str, fl_name: str) -> None:
        data = JSONHandler._load_safe(filename)
        if 'filtered_lattices' not in data: return

        data['filtered_lattices'] = [l for l in data['filtered_lattices'] if l.get('filtered_lattice_name') != fl_name]
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(JSONHandler._compact_json(data))
            logger.info(f"Filtered Lattice '{fl_name}' deleted.")
        except Exception as e:
            logger.error(f"Delete Error for filtered lattice '{fl_name}': {e}")

    # ==========================================
    #              MANY LATTICE
    # ==========================================

    @staticmethod
    def load_many_lattice_from_json(filename: str, many_lattice_name: str, filtered_lattices_file: str = PATHS["filtered_lattices"], lattices_file: str = PATHS["lattices"]) -> Optional[ManyLattice]:
        data = JSONHandler._load_safe(filename)
            
        if 'many_lattices' in data:
            for ml_data in data['many_lattices']:
                if ml_data.get('many_lattice_name') == many_lattice_name:
                    try:
                        fl_name = ml_data.get('filtered_lattice_name')
                        
                        fl = JSONHandler.load_filtered_lattice_from_json(filtered_lattices_file, fl_name, lattices_file)
                        if not fl:
                            base_lat = JSONHandler.load_lattice_from_json(lattices_file, fl_name)
                            if base_lat:
                                fl_raw_data = JSONHandler._load_safe(filtered_lattices_file)
                                filter_set = set()
                                for f_item in fl_raw_data.get('filtered_lattices', []):
                                    if f_item.get('filtered_lattice_name') == fl_name:
                                        filter_set = set(f_item.get('filter', []))
                                        break

                                fl = FilteredLattice(
                                    fl_name,
                                    base_lat.name,
                                    base_lat.elements,
                                    base_lat.relations,
                                    base_lat.negation_map,
                                    base_lat.implication_map,
                                    filter_set
                                )
                            else:
                                logger.error(f"Failed to load base filtered lattice or lattice '{fl_name}' for many lattice '{many_lattice_name}'")
                                return None

                        comp_sub_lat_list = []
                        for sub_name in ml_data.get("comp_sub_lat", []):
                            sub_lat = JSONHandler.load_lattice_from_json(lattices_file, sub_name)
                            if sub_lat: 
                                comp_sub_lat_list.append(sub_lat)

                        return ManyLattice(
                            many_lattice_name, fl.name_filtered_lattice, fl.name,
                            fl.elements, fl.relations, comp_sub_lat_list,
                            fl.negation_map, fl.implication_map, fl.filter
                        )
                    except Exception as e:
                        logger.error(f"Error loading Many Lattice '{many_lattice_name}': {e}")
                        return None
        return None

    @staticmethod
    def save_many_lattice_to_json(filename: str, new_ml: ManyLattice) -> bool:
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            data = JSONHandler._load_safe(filename)
            if 'many_lattices' not in data: data['many_lattices'] = []
            
            ml_list = [ml for ml in data['many_lattices'] if ml.get('many_lattice_name') != new_ml.name_many_lattice]
            
            ml_dict = {
                "many_lattice_name": new_ml.name_many_lattice,
                "filtered_lattice_name": new_ml.name_filtered_lattice,
                "comp_sub_lat": [lat.name for lat in new_ml.comp_sub_lat]
            }
            
            ml_list.append(ml_dict)
            data['many_lattices'] = ml_list
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(JSONHandler._compact_json(data))
            return True
        except Exception as e:
            logger.error(f"Save Error for many lattice '{new_ml.name_many_lattice}': {e}")
            return False

    @staticmethod
    def delete_many_lattice_from_json(filename: str, ml_name: str) -> None:
        data = JSONHandler._load_safe(filename)
        if 'many_lattices' not in data: return

        data['many_lattices'] = [l for l in data['many_lattices'] if l.get('many_lattice_name') != ml_name]
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(JSONHandler._compact_json(data))
            logger.info(f"Many Lattice '{ml_name}' deleted.")
        except Exception as e:
            logger.error(f"Delete Error for many lattice '{ml_name}': {e}")

    # ==========================================
    #              KRIPKE FRAME
    # ==========================================

    @staticmethod
    def save_kripke_frame_to_json(filename: str, frame: KripkeFrame) -> bool:
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            data = JSONHandler._load_safe(filename)
            if 'kripke_frames' not in data: data['kripke_frames'] = []

            frame_list = [kf for kf in data['kripke_frames'] if kf.get('name') != frame.name]

            serialized_accessibility = {}
            for act, relation_map in frame.accessibility_relation.items():
                serialized_accessibility[act] = {
                    src.name_short: [tgt.name_short for tgt in targets]
                    for src, targets in relation_map.items()
                }

            serialized_worlds = [
                {"name_long": w.name_long, "name_short": w.name_short}
                for w in frame.worlds
            ]

            frame_list.append({
                "name": frame.name,
                "signature_name": frame.signature.name,
                "worlds": serialized_worlds,
                "initial_world": frame.initial_world.name_short if frame.initial_world else None,
                "accessibility_relation": serialized_accessibility
            })
            data['kripke_frames'] = frame_list
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(JSONHandler._compact_json(data))
            return True
        except Exception as e:
            logger.error(f"Error saving Kripke frame '{frame.name}': {e}")
            return False

    @staticmethod
    def load_kripke_frame_from_json(
        filename: str,
        name: str,
        signatures_file: str = PATHS["signatures"]
    ) -> Optional[KripkeFrame]:
        data = JSONHandler._load_safe(filename)
        for kf_data in data.get('kripke_frames', []):
            if kf_data.get('name') == name:
                try:
                    sig_name = kf_data.get('signature_name')
                    signature = JSONHandler.load_signature_from_json(signatures_file, sig_name)
                    if not signature:
                        logger.error(f"Signature '{sig_name}' not found for frame '{name}'")
                        return None

                    world_objects = set()
                    lookup: Dict[str, World] = {}

                    for w_entry in kf_data.get('worlds', []):
                        if isinstance(w_entry, dict):
                            w_long = w_entry.get("name_long", "").strip()
                            w_short = w_entry.get("name_short", "").strip()
                            w_obj = World(name_long=w_long, name_short=w_short)
                        else:
                            raw_name = str(w_entry).strip()
                            w_obj = World(name_long=raw_name, name_short=raw_name)

                        world_objects.add(w_obj)
                        if w_obj.name_short:
                            lookup[w_obj.name_short] = w_obj
                        if w_obj.name_long:
                            lookup[w_obj.name_long] = w_obj

                    init_key = str(kf_data.get('initial_world', '')).strip()
                    initial_world = lookup.get(init_key)
                    if not initial_world and world_objects:
                        initial_world = next(iter(world_objects))

                    raw_access = kf_data.get('accessibility_relation', {})
                    accessibility_relation: Dict[str, Dict[World, Set[World]]] = {
                        act: defaultdict(set) for act in signature.actions
                    }

                    for act in signature.actions:
                        act_map = raw_access.get(act, {})
                        for src_key, tgt_keys in act_map.items():
                            src_key = str(src_key).strip()
                            src_world = lookup.get(src_key)

                            if src_world:
                                for tgt_key in tgt_keys:
                                    tgt_key = str(tgt_key).strip()
                                    tgt_world = lookup.get(tgt_key)
                                    if tgt_world:
                                        accessibility_relation[act][src_world].add(tgt_world)
                                    else:
                                        logger.warning(
                                            f"Target world '{tgt_key}' in action '{act}' not recognized in frame '{name}'."
                                        )
                            else:
                                logger.warning(
                                    f"Source world '{src_key}' in action '{act}' not recognized in frame '{name}'."
                                )

                    return KripkeFrame(
                        name=name,
                        signature=signature,
                        worlds=world_objects,
                        initial_world=initial_world,
                        accessibility_relation=accessibility_relation
                    )
                except Exception as e:
                    logger.error(f"Error loading Kripke frame '{name}': {e}")
                    return None
        return None

    @staticmethod
    def delete_kripke_frame_from_json(filename: str, frame_name: str) -> None:
        data = JSONHandler._load_safe(filename)
        if 'kripke_frames' not in data: return

        data['kripke_frames'] = [kf for kf in data['kripke_frames'] if kf.get('name') != frame_name]
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(JSONHandler._compact_json(data))
            logger.info(f"Kripke Frame '{frame_name}' deleted.")
        except Exception as e:
            logger.error(f"Delete Error for Kripke frame '{frame_name}': {e}")

    # ==========================================
    #                 MODEL
    # ==========================================

    @staticmethod
    def save_model_to_json(filename: str, model: Model) -> bool:
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            data = JSONHandler._load_safe(filename)
            if 'models' not in data: data['models'] = []

            model_list = [m for m in data['models'] if m.get('name') != model.name]

            serialized_accessibility = {}
            for act, relation_map in model.accessibility_relation.items():
                serialized_accessibility[act] = {
                    src.name_short: [tgt.name_short for tgt in targets]
                    for src, targets in relation_map.items()
                }

            serialized_world_lattices = {
                w.name_short: lat.name for w, lat in model.world_lattices.items()
            }
            serialized_valuations = {
                w.name_short: vals for w, vals in model.valuations.items()
            }

            serialized_worlds = [
                {"name_long": w.name_long, "name_short": w.name_short}
                for w in model.worlds
            ]

            kf_name = getattr(model, "kripke_frame_name", model.name)

            model_list.append({
                "name": model.name,
                "kripke_frame_name": kf_name,
                "many_lattice_name": model.many_lattice.name_many_lattice,
                "signature_name": model.signature.name,
                "worlds": serialized_worlds,
                "initial_world": model.initial_world.name_short if model.initial_world else None,
                "world_lattices": serialized_world_lattices,
                "valuations": serialized_valuations,
                "description": model.description,
                "accessibility_relation": serialized_accessibility
            })
            data['models'] = model_list
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(JSONHandler._compact_json(data))
            return True
        except Exception as e:
            logger.error(f"Error saving model '{model.name}': {e}")
            return False


    @staticmethod
    def load_model_from_json(
        filename: str,
        name: str,
        kripke_frames_file: str = PATHS["kripke_frames"],
        many_lattices_file: str = PATHS["many_lattices"],
        lattices_file: str = PATHS["lattices"],
        signatures_file: str = PATHS["signatures"]
    ) -> Optional[Model]:
        data = JSONHandler._load_safe(filename)
        for m_data in data.get('models', []):
            if m_data.get('name') == name:
                try:
                    ml_name = m_data.get('many_lattice_name')
                    many_lat = JSONHandler.load_many_lattice_from_json(
                        many_lattices_file, ml_name, PATHS["filtered_lattices"], lattices_file
                    )
                    if not many_lat: return None

                    kf_name = m_data.get('kripke_frame_name')
                    frame = JSONHandler.load_kripke_frame_from_json(kripke_frames_file, kf_name, signatures_file)

                    if not frame:
                        logger.error(f"Cannot load model '{name}': underlying frame '{kf_name}' not found.")
                        return None

                    world_objects = frame.worlds
                    world_by_short = {w.name_short: w for w in world_objects}

                    world_lattices = {}
                    raw_wl = m_data.get('world_lattices', {})
                    sublat_cache = {lat.name: lat for lat in many_lat.comp_sub_lat}
                    for w_short, lat_name in raw_wl.items():
                        w = world_by_short.get(w_short)
                        if w and lat_name in sublat_cache:
                            world_lattices[w] = sublat_cache[lat_name]

                    valuations = {}
                    raw_vals = m_data.get('valuations', {})
                    for w_short, val_dict in raw_vals.items():
                        w = world_by_short.get(w_short)
                        if w:
                            valuations[w] = val_dict

                    model = Model(
                        name=name,
                        signature=frame.signature,
                        worlds=world_objects,
                        initial_world=frame.initial_world,
                        many_lattice=many_lat,
                        world_lattices=world_lattices,
                        accessibility_relation=frame.accessibility_relation,
                        description=m_data.get('description', ""),
                        valuations=valuations
                    )
                    model.kripke_frame_name = kf_name
                    return model

                except Exception as e:
                    logger.error(f"Error loading model '{name}': {e}")
                    return None
        return None

    @staticmethod
    def delete_model_from_json(filename: str, model_name: str) -> None:
        data = JSONHandler._load_safe(filename)
        if 'models' not in data: return

        data['models'] = [m for m in data['models'] if m.get('name') != model_name]
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(JSONHandler._compact_json(data))
            logger.info(f"Model '{model_name}' deleted.")
        except Exception as e:
            logger.error(f"Delete Error for model '{model_name}': {e}")

    # ==========================================
    #         KRIPKE FRAME MORPHISM
    # ==========================================

    @staticmethod
    def save_kripke_frame_morphism_to_json(filename: str, kfm: KripkeFrameMorphism) -> bool:
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            data = JSONHandler._load_safe(filename)
            if 'kripke_frame_morphisms' not in data: data['kripke_frame_morphisms'] = []
            
            # Map source world short name to target world short name
            world_mapping = {
                src.name_short: tgt.name_short
                for src, tgt in kfm.world_map.items()
                if src is not None and tgt is not None
            }

            m_list = [m for m in data['kripke_frame_morphisms'] if m.get('name') != kfm.name]
            m_list.append({
                "name": kfm.name,
                "source_frame": kfm.source_frame.name,
                "target_frame": kfm.target_frame.name,
                "world_map": world_mapping
            })
            data['kripke_frame_morphisms'] = m_list
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(JSONHandler._compact_json(data))
            return True
        except Exception as e:
            logger.error(f"Error saving Kripke frame morphism '{kfm.name}': {e}")
            return False

    @staticmethod
    def load_kripke_frame_morphism_from_json(
        filename: str,
        name: str,
        kripke_frames_file: str = PATHS["kripke_frames"]
    ) -> Optional[KripkeFrameMorphism]:
        data = JSONHandler._load_safe(filename)
        for m_data in data.get('kripke_frame_morphisms', []):
            if m_data.get('name') == name:
                try:
                    src_name = m_data.get('source_frame')
                    tgt_name = m_data.get('target_frame')
                    src_frame = JSONHandler.load_kripke_frame_from_json(kripke_frames_file, src_name)
                    tgt_frame = JSONHandler.load_kripke_frame_from_json(kripke_frames_file, tgt_name)

                    if not src_frame or not tgt_frame:
                        logger.error(f"Failed to load underlying frames for morphism '{name}'.")
                        return None

                    src_lookup = {w.name_short: w for w in src_frame.worlds}
                    tgt_lookup = {w.name_short: w for w in tgt_frame.worlds}

                    world_map: Dict[World, World] = {}
                    for src_short, tgt_short in m_data.get('world_map', {}).items():
                        src_w = src_lookup.get(src_short)
                        tgt_w = tgt_lookup.get(tgt_short)
                        if src_w and tgt_w:
                            world_map[src_w] = tgt_w

                    return KripkeFrameMorphism(
                        name=name,
                        source_frame=src_frame,
                        target_frame=tgt_frame,
                        world_map=world_map
                    )
                except Exception as e:
                    logger.error(f"Error loading Kripke frame morphism '{name}': {e}")
                    return None
        return None

    @staticmethod
    def delete_kripke_frame_morphism_from_json(filename: str, name: str) -> bool:
        try:
            data = JSONHandler._load_safe(filename)
            data['kripke_frame_morphisms'] = [
                m for m in data.get('kripke_frame_morphisms', []) if m.get('name') != name
            ]
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(JSONHandler._compact_json(data))
            return True
        except Exception as e:
            logger.error(f"Error deleting Kripke frame morphism '{name}': {e}")
            return False

    # ==========================================
    #              MODEL MORPHISM
    # ==========================================

    @staticmethod
    def save_model_morphism_to_json(filename: str, mm: ModelMorphism) -> bool:
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            data = JSONHandler._load_safe(filename)
            if 'model_morphisms' not in data: data['model_morphisms'] = []
            
            world_mapping = {
                src.name_short: tgt.name_short
                for src, tgt in mm.world_map.items()
                if src is not None and tgt is not None
            }

            m_list = [m for m in data['model_morphisms'] if m.get('name') != mm.name]
            m_list.append({
                "name": mm.name,
                "kripke_frame_morphism_name": getattr(mm, "kripke_frame_morphism_name", None),
                "source_model": mm.source_model.name,
                "target_model": mm.target_model.name,
                "world_map": world_mapping
            })
            data['model_morphisms'] = m_list
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(JSONHandler._compact_json(data))
            return True
        except Exception as e:
            logger.error(f"Error saving model morphism '{mm.name}': {e}")
            return False

    @staticmethod
    def load_model_morphism_from_json(
        filename: str,
        name: str,
        models_file: str = PATHS["models"]
    ) -> Optional[ModelMorphism]:
        data = JSONHandler._load_safe(filename)
        for m_data in data.get('model_morphisms', []):
            if m_data.get('name') == name:
                try:
                    src_name = m_data.get('source_model')
                    tgt_name = m_data.get('target_model')
                    src_model = JSONHandler.load_model_from_json(models_file, src_name)
                    tgt_model = JSONHandler.load_model_from_json(models_file, tgt_name)

                    if not src_model or not tgt_model:
                        logger.error(f"Failed to load underlying models for morphism '{name}'.")
                        return None

                    src_lookup = {w.name_short: w for w in src_model.worlds}
                    tgt_lookup = {w.name_short: w for w in tgt_model.worlds}

                    world_map: Dict[World, World] = {}
                    for src_short, tgt_short in m_data.get('world_map', {}).items():
                        src_w = src_lookup.get(src_short)
                        tgt_w = tgt_lookup.get(tgt_short)
                        if src_w and tgt_w:
                            world_map[src_w] = tgt_w

                    model_morphism = ModelMorphism(
                        name=name,
                        source_model=src_model,
                        target_model=tgt_model,
                        world_map=world_map
                    )
                    model_morphism.kripke_frame_morphism_name = m_data.get("kripke_frame_morphism_name")
                    return model_morphism
                except Exception as e:
                    logger.error(f"Error loading model morphism '{name}': {e}")
                    return None
        return None

    @staticmethod
    def delete_model_morphism_from_json(filename: str, name: str) -> bool:
        try:
            data = JSONHandler._load_safe(filename)
            data['model_morphisms'] = [
                m for m in data.get('model_morphisms', []) if m.get('name') != name
            ]
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(JSONHandler._compact_json(data))
            return True
        except Exception as e:
            logger.error(f"Error deleting model morphism '{name}': {e}")
            return False

    @staticmethod
    def get_names_from_json(filename: str, json_key: str, name_key: str) -> List[str]:
        """One-liner retrieval of object names for selection dialogs."""
        data = JSONHandler._load_safe(filename)
        return [i[name_key] for i in data.get(json_key, []) if name_key in i]