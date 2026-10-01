"""
Lattice and Algebraic Structures Module.

This module defines classes for representing Lattices, Filtered Lattices and Many-Lattices.
It provides methods for algebraic operations (meet, join, implication, negation) and visualization.
"""

from typing import Set, Dict, Tuple, Optional, List
from collections import defaultdict
import logging

try:
    import networkx as nx
    import matplotlib.pyplot as plt
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False


def _get_logger():
    return logging.getLogger("MathObjects")


def _compute_hasse_layout(G):
    """
    Computes a layout for a Hasse Diagram to minimize crossings.
    Uses the Barycenter Heuristic: nodes are placed horizontally based on 
    the average position of their predecessors (children in the lattice).
    """
    if not G.nodes: return {}

    layers = {}
    try:
        sorted_nodes = list(nx.topological_sort(G))
    except:
        return nx.spring_layout(G)

    for n in sorted_nodes:
        preds = list(G.predecessors(n))
        if preds:
            layers[n] = max(layers[p] for p in preds) + 1
        else:
            layers[n] = 0

    layer_nodes = defaultdict(list)
    for n, l in layers.items():
        layer_nodes[l].append(n)
        
    max_layer = max(layers.values())
    pos = {}
    
    layer_nodes[0].sort(key=lambda x: str(x))
    width = len(layer_nodes[0])
    for i, node in enumerate(layer_nodes[0]):
        pos[node] = (i - width / 2.0) * 1.5

    for l in range(1, max_layer + 1):
        node_order = []
        for node in layer_nodes[l]:
            preds = list(G.predecessors(node))
            if preds:
                avg_x = sum(pos[p] for p in preds) / len(preds)
            else:
                avg_x = 0 
            node_order.append((node, avg_x))
        
        node_order.sort(key=lambda x: x[1])
        
        current_nodes = [n for n, x in node_order]
        width = len(current_nodes)
        for i, node in enumerate(current_nodes):
            pos[node] = (i - width / 2.0) * 1.5

    final_pos = {}
    for node, x in pos.items():
        final_pos[node] = (x, layers[node])
        
    return final_pos

def _to_node_repr(element):
    if isinstance(element, tuple):
        return ",".join(str(e).strip("' ") for e in element)
    return str(element).replace("'", "").replace(" ", "")

class Lattice:
    """
    Represents a lattice with elements, a partial order, and unary/binary operations.
    """

    def __init__(
        self,
        name: str,
        elements: Set[str],
        relations: Set[Tuple[str, str]],
        negation_map: Optional[Dict[str, str]] = None,
        implication_map: Optional[Dict[Tuple[str, str], str]] = None
    ):

        self.name = name
        self.elements = set(elements)
        self.relations = set(relations)
        self.negation_map = negation_map if negation_map is not None else {}
        self.implication_map = implication_map if implication_map is not None else {}

        if not self._check_is_lattice():
            _get_logger().error(f"Validation failed: '{name}' is not a valid lattice.")
            raise ValueError(f"The object '{name}' is not a valid lattice.")

        self.bottom = self.meet_set(self.elements)
        self.top = self.join_set(self.elements)
        _get_logger().info(f"Lattice '{self.name}' initialized ({len(self.elements)} elements).")

    def is_less_than_or_equal(self, a: str, b: str) -> bool:
        return (a, b) in self.relations

    def negation(self, variable: str) -> Optional[str]:
        try:
            return self.negation_map[variable]
        except KeyError:
            _get_logger().warning(f"Lattice '{self.name}': Variable '{variable}' has no negation assigned.")
            return None

    def implication(self, variable1: str, variable2: str) -> Optional[str]:
        try:
            return self.implication_map[(variable1, variable2)]
        except KeyError:
            _get_logger().warning(f"Lattice '{self.name}': Pair ('{variable1}', '{variable2}') has no implication assigned.")
            return None

    def join(self, a: str, b: str) -> str:
        if a not in self.elements or b not in self.elements:
            raise ValueError(f"Elements '{a}' or '{b}' not in the lattice.")

        upper_bounds = {
            x for x in self.elements 
            if self.is_less_than_or_equal(a, x) and self.is_less_than_or_equal(b, x)
        }

        if not upper_bounds:
            raise ValueError(f"No common upper bounds found for '{a}' and '{b}'.")

        for x in upper_bounds:
            if all(self.is_less_than_or_equal(x, y) for y in upper_bounds):
                return x

        raise ValueError(f"No unique Join found for '{a}' and '{b}'.")

    def meet(self, a: str, b: str) -> str:
        if a not in self.elements or b not in self.elements:
            raise ValueError(f"Elements '{a}' or '{b}' not in the lattice.")

        lower_bounds = {
            x for x in self.elements 
            if self.is_less_than_or_equal(x, a) and self.is_less_than_or_equal(x, b)
        }

        if not lower_bounds:
            raise ValueError(f"No common lower bounds found for '{a}' and '{b}'.")

        for x in lower_bounds:
            if all(self.is_less_than_or_equal(y, x) for y in lower_bounds):
                return x

        raise ValueError(f"No unique Meet found for '{a}' and '{b}'.")

    def meet_set(self, subset: Optional[Set[str]] = None) -> str:
        if subset is None:
            subset = set()
        
        subset_list = list(subset)
        if not subset_list:
            return self.top

        lower = subset_list[0]
        for element in subset_list:
            lower = self.meet(lower, element)
        return lower

    def join_set(self, subset: Optional[Set[str]] = None) -> str:
        if subset is None:
            subset = set()

        subset_list = list(subset)
        if not subset_list:
            return self.bottom

        greatest = subset_list[0]
        for element in subset_list:
            greatest = self.join(greatest, element)
        return greatest

    def _check_is_lattice(self) -> bool:
        try:
            for x in self.elements:
                for y in self.elements:
                    self.meet(x, y)
                    self.join(x, y)
            return True
        except ValueError as e:
            _get_logger().error(f"Lattice check failed for '{self.name}': {e}")
            return False

    def draw_hasse(self) -> None:
        if not VISUALIZATION_AVAILABLE: 
            _get_logger().warning("Visualization unavailable: networkx or matplotlib missing.")
            return
        if not self.elements: return
        
        G = nx.DiGraph()
        G.add_nodes_from([_to_node_repr(e) for e in self.elements])
        
        edges = (self.relations if hasattr(self, 'relations') else self.truth_relation)
        clean_edges = [(_to_node_repr(a), _to_node_repr(b)) for a, b in edges if a != b]
        
        G.add_edges_from(clean_edges)

        if list(nx.simple_cycles(G)):
            _get_logger().error(f"Hasse Diagram for {self.name} contains cycles.")
            return

        try:
            TR = nx.transitive_reduction(G)
        except Exception as e:
            _get_logger().warning(f"Transitive reduction failed for {self.name}, using raw graph: {e}")
            TR = G
        pos = _compute_hasse_layout(TR)

        plt.figure(figsize=(8, 10))
        plt.title(f"Hasse Diagram: {self.name}")

        labels = {node: node for node in TR.nodes()}
        max_len = max((len(l) for l in labels.values()), default=1)
        node_size = 1000 + (max_len * 300)

        nx.draw_networkx_nodes(TR, pos, node_size=node_size, node_color="#A0CBE2", edgecolors="black")
        nx.draw_networkx_labels(TR, pos, labels=labels, font_size=10, font_weight="bold")
        nx.draw_networkx_edges(TR, pos, arrows=False, width=1.5, edge_color="gray")
        
        plt.axis("off")
        plt.tight_layout()
        plt.show(block=False)

    def __repr__(self) -> str:
        return f"{self.name}"


class FilteredLattice(Lattice):
    def __init__(
        self,
        name_filtered_lattice: str,
        name_lattice: str,
        elements: Set[str],
        relations: Set[Tuple[str, str]],
        negation_map: Optional[Dict[str, str]] = None,
        implication_map: Optional[Dict[Tuple[str, str], str]] = None,
        filter: Optional[Set[str]] = None
    ):
        super().__init__(name_lattice, elements, relations, negation_map, implication_map)
        self.name_filtered_lattice = name_filtered_lattice
        self.filter = filter if filter is not None else set()

        is_valid, error_msg = self._check_filter()
        if not is_valid:
            _get_logger().error(f"Filter validation failed for '{self.name_filtered_lattice}': {error_msg}")
            raise ValueError(error_msg)

    def _check_filter(self) -> Tuple[bool, str]:
        if not self.filter.issubset(self.elements):
            return False, "The Filter must be a subset of the Lattice elements."

        for x in self.filter:
            for y in self.elements:
                if self.is_less_than_or_equal(x, y) and y not in self.filter:
                    return False, (
                        f"The Filter is not upward-closed: element '{x}' is in the filter "
                        f"and '{x}' <= '{y}', but '{y}' is not in the filter."
                    )

        return True, ""

    def __repr__(self) -> str:
        return f"{self.name_filtered_lattice}"


class ManyLattice(FilteredLattice):

    def __init__(
        self,
        name_many_lattice: str,
        name_filtered_lattice: str,
        name_lattice: str,
        elements: Set[str],
        relations: Set[Tuple[str, str]],
        comp_sub_lat: List[Lattice],
        negation_map: Optional[Dict[str, str]] = None,
        implication_map: Optional[Dict[Tuple[str, str], str]] = None,
        filter: Optional[Set[str]] = None
    ):
        super().__init__(
            name_filtered_lattice, name_lattice, elements, relations, 
            negation_map, implication_map, filter
        )
        
        for lat in comp_sub_lat:
            if not isinstance(lat, Lattice):
                raise TypeError("comp_sub_lat must contain Lattice instances.")

        self.comp_sub_lat = comp_sub_lat
        self.name_many_lattice = name_many_lattice
        _get_logger().info(f"ManyLattice '{self.name_many_lattice}' initialized with {len(self.comp_sub_lat)} sublattices.")

    def __repr__(self) -> str:
        return f"{self.name_many_lattice}"

    def add_comp_sub_lat(self, lattice: Lattice) -> None:
        if not isinstance(lattice, Lattice):
            raise TypeError("Argument must be a Lattice instance.")
        
        if self.get_comp_sub_lattice(lattice.name):
            raise ValueError(f"Lattice '{lattice.name}' already exists.")
        
        self.comp_sub_lat.append(lattice)

    def get_comp_sub_lattice(self, name: str) -> Optional[Lattice]:
        for lattice in self.comp_sub_lat:
            if lattice.name == name:
                return lattice
        return None

    def down_interpretation(self, lattice: Lattice, element_a: str) -> str:
        if not isinstance(lattice, Lattice):
            raise TypeError("Argument 'lattice' must be a Lattice instance.")
        
        if lattice.name not in [lat.name for lat in self.comp_sub_lat]:
            raise ValueError("Lattice must be a registered complete sublattice.")

        if element_a in lattice.elements:
            return element_a

        lower_set = {x for x in lattice.elements if self.is_less_than_or_equal(x, element_a)}

        if not lower_set:
            return lattice.bottom
        return lattice.join_set(lower_set)

    def up_interpretation(self, lattice: Lattice, element_a: str) -> str:
        if not isinstance(lattice, Lattice):
            raise TypeError("Argument 'lattice' must be a Lattice instance.")
        
        if lattice.name not in [lat.name for lat in self.comp_sub_lat]:
            raise ValueError("Lattice must be a registered complete sublattice.")

        if element_a in lattice.elements:
            return element_a

        upper_set = {x for x in lattice.elements if self.is_less_than_or_equal(element_a, x)}

        if not upper_set:
            return lattice.top
        return lattice.meet_set(upper_set)
