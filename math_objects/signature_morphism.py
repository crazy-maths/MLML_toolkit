"""
Signature Morphism Module.

This module defines the SignatureMorphism class, representing a pair of mapping 
functions (f for propositions, g for actions) between a source and target signature.
"""

from typing import Dict, Tuple, List
from math_objects.signature import Signature
import logging

def _get_logger():
    return logging.getLogger("SignatureMorphism")

class SignatureMorphism:
    def __init__(
        self,
        name: str,
        source_sig: Signature,
        target_sig: Signature,
        prop_map: Dict[str, str],
        act_map: Dict[str, str]
    ):
        self.name = name
        self.source_sig = source_sig
        self.target_sig = target_sig
        self.prop_map = prop_map
        self.act_map = act_map
        _get_logger().info(f"SignatureMorphism '{self.name}' initialized: {source_sig.name} -> {target_sig.name}")

    def verify_morphism(self) -> Tuple[bool, List[str]]:
        errors = []
        
        for p in self.source_sig.propositions:
            if p not in self.prop_map or not self.prop_map[p]:
                errors.append(f"Proposition '{p}' has no mapped target.")
            elif self.prop_map[p] not in self.target_sig.propositions:
                errors.append(f"Mapped target proposition '{self.prop_map[p]}' for '{p}' is not in the target signature.")
                
        for a in self.source_sig.actions:
            if a not in self.act_map or not self.act_map[a]:
                errors.append(f"Action '{a}' has no mapped target.")
            elif self.act_map[a] not in self.target_sig.actions:
                errors.append(f"Mapped target action '{self.act_map[a]}' for '{a}' is not in the target signature.")
                
        if errors:
            for err in errors:
                _get_logger().warning(f"SignatureMorphism '{self.name}' validation issue: {err}")
        else:
            _get_logger().info(f"SignatureMorphism '{self.name}' verified successfully.")

        return len(errors) == 0, errors

    def __repr__(self) -> str:
        return f"SignatureMorphism('{self.name}': {self.source_sig.name} -> {self.target_sig.name})"