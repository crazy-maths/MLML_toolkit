"""
Signature Module.

This module defines the Signature class, representing a pair of sets:
Propositions (Prop) and Actions (Act).
"""

from typing import Set
import logging

def _get_logger():
    return logging.getLogger("Signature")

class Signature:
    """
    Represents a signature consisting of a set of propositions and a set of actions.
    """
    def __init__(self, name: str, propositions: Set[str], actions: Set[str]):
        self.name = name
        self.propositions = set(propositions) if propositions is not None else set()
        self.actions = set(actions) if actions is not None else set()
        _get_logger().info(f"Signature '{self.name}' initialized ({len(self.propositions)} props, {len(self.actions)} acts).")

    def __repr__(self) -> str:
        return f"Signature('{self.name}', Props: {len(self.propositions)}, Acts: {len(self.actions)})"