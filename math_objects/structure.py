"""
Structure Module.

This module defines the World, KripkeFrame and Model classes. A Kripke Frame consists of a 
set of worlds, a family of accessibility relations indexed by the actions of a Signature, and an initial world.
"""

import math
from typing import Set, Dict, Optional, Tuple
from collections import defaultdict
from matplotlib.path import Path
from matplotlib.patches import PathPatch
from math_objects.lattice import Lattice, FilteredLattice, ManyLattice
from math_objects.signature import Signature
import logging

try:
    import networkx as nx
    import matplotlib.pyplot as plt
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False

def _get_logger():
    return logging.getLogger("Structure")

class World:
    """Represents a state/world in a Kripke frame."""
    def __init__(self, name_long: str, name_short: str):
        self.name_long = name_long
        self.name_short = name_short

    def __hash__(self) -> int:
        return hash((self.name_long, self.name_short))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, World):
            return False
        return self.name_long == other.name_long and self.name_short == other.name_short

    def __repr__(self) -> str:
        return f"{self.name_short}"


class KripkeFrame:
    """
    Represents a Kripke Frame consisting of a set of worlds and a family of 
    accessibility relations dependent on a Signature's actions.
    """
    def __init__(
        self,
        name: str,
        signature: Signature,
        worlds: Set[World],
        initial_world: World,
        accessibility_relation: Optional[Dict[str, Dict[World, Set[World]]]] = None
    ):
        if not isinstance(signature, Signature):
            raise TypeError("The 'signature' argument must be an instance of Signature.")

        self.name = name
        self.signature = signature
        self.worlds = set(worlds)
        self.initial_world = initial_world
        self.actions = signature.actions
        
        if accessibility_relation is not None:
            self.accessibility_relation = accessibility_relation
        else:
            self.accessibility_relation = {act: defaultdict(set) for act in self.actions}

        for act in self.actions:
            if act not in self.accessibility_relation:
                self.accessibility_relation[act] = defaultdict(set)
            for world in self.worlds:
                if world not in self.accessibility_relation[act]:
                    self.accessibility_relation[act][world] = set()
                    
        _get_logger().info(f"KripkeFrame '{self.name}' initialized ({len(self.worlds)} worlds, {len(self.actions)} actions).")

    def add_world(self, world: World) -> None:
        if not isinstance(world, World):
            raise TypeError("The 'world' argument must be an instance of World.")
        
        if self.get_world(world.name_short):
            raise ValueError(f"A world with the name '{world.name_short}' already exists.")
        
        self.worlds.add(world)
        
        for act in self.actions:
            if world not in self.accessibility_relation[act]:
                self.accessibility_relation[act][world] = set()

    def delete_world(self, world: World) -> None:
        if not isinstance(world, World):
            raise TypeError("The 'world' argument must be an instance of World.")
        
        for act in self.actions:
            if self.accessibility_relation[act].get(world):
                raise ValueError(f"World '{world.name_short}' has outgoing relations in action '{act}'.")
            
            for other_world, targets in self.accessibility_relation[act].items():
                if world in targets:
                    raise ValueError(f"World '{other_world.name_short}' points to '{world.name_short}' in action '{act}'.")
        
        for act in self.actions:
            if world in self.accessibility_relation[act]:
                del self.accessibility_relation[act][world]
            
        self.worlds.remove(world)

    def get_world(self, name_short: str) -> Optional[World]:
        for world in self.worlds:
            if world.name_short == name_short:
                return world
        return None

    def add_relation(self, world1_name: str, world2_name: str, action: str) -> None:
        world1 = self.get_world(world1_name)
        world2 = self.get_world(world2_name)
        
        if not world1 or not world2:
            _get_logger().error(f"Cannot add relation: World '{world1_name}' or '{world2_name}' missing in frame '{self.name}'.")
            raise ValueError("Both worlds must exist in the frame.")
        
        if action not in self.actions:
            _get_logger().error(f"Cannot add relation: Action '{action}' not defined in signature '{self.signature.name}'.")
            raise ValueError(f"Action '{action}' is not defined in the frame's signature.")
        
        self.accessibility_relation[action][world1].add(world2)
        _get_logger().debug(f"Relation added in '{self.name}': ({world1.name_short}, {world2.name_short}) for action '{action}'.")
        
        self.accessibility_relation[action][world1].add(world2)

    def delete_relation(self, world1_name: str, world2_name: str, action: str) -> None:
        world1 = self.get_world(world1_name)
        world2 = self.get_world(world2_name)

        if not world1 or not world2:
            raise ValueError("Both worlds must exist in the frame.")
            
        if action not in self.actions:
            raise ValueError(f"Action '{action}' is not defined in the frame's signature.")
        
        if world2 not in self.accessibility_relation[action][world1]:
            raise ValueError(f"No relation exists from {world1_name} to {world2_name} for action '{action}'.")
        
        self.accessibility_relation[action][world1].remove(world2)

    def get_accessible_worlds(self, world_name: str, action: str) -> Set[World]:
        world = self.get_world(world_name)
        if not world:
            raise ValueError(f"World '{world_name}' does not exist.")
        
        if action not in self.accessibility_relation:
            return set()

        return self.accessibility_relation[action].get(world, set())

    def draw_graph(self, action: Optional[str] = None) -> None:
            if not VISUALIZATION_AVAILABLE:
                _get_logger().warning("Visualization libraries not installed. Cannot draw graph.")
                return
            if not self.actions:
                _get_logger().warning(f"Frame/Model '{self.name}' has no actions defined for graph visualization.")
                return
    
            G = nx.DiGraph()
            for world in self.worlds:
                G.add_node(world.name_short)
    
            if action:
                if action not in self.actions:
                    _get_logger().error(f"Action '{action}' requested but not found in frame/model.")
                    return
                actions_to_draw = [action]
                title = f"Graph: {self.name} (Action: {action})"
            else:
                actions_to_draw = sorted(list(self.actions))
                title = f"Graph: {self.name}"
    
            try:
                edge_data = defaultdict(list)
    
                for act in actions_to_draw:
                    if act in self.accessibility_relation:
                        for src, targets in self.accessibility_relation[act].items():
                            for tgt in targets:
                                u, v = src.name_short, tgt.name_short
                                edge_data[(u, v)].append(act)
    
                plt.figure(figsize=(12, 10))
                pos = nx.spring_layout(G, k=3.0, seed=42) 
                
                NODE_SIZE = 2500
                
                node_colors = []
                for node in G.nodes():
                    if node == self.initial_world.name_short:
                        node_colors.append("red")
                    else:
                        node_colors.append("lightblue")
    
                nx.draw_networkx_nodes(G, pos, node_size=NODE_SIZE, node_color=node_colors, edgecolors="black", linewidths=1.5)
                nx.draw_networkx_labels(G, pos, font_size=10, font_weight="bold")
    
                for (u, v), text_list in edge_data.items():
                    full_text = ", ".join(text_list)
                    
                    is_bidirectional = (v, u) in edge_data and u != v
                    is_self_loop = (u == v)
    
                    if is_self_loop:
                        x, y = pos[u]
    
                        loop_size = 0.30
                        dx = loop_size
                        dy = loop_size * 0.9
    
                        verts = [
                            (x, y),               
                            (x + dx, y + dy),    
                            (x - dx, y + dy),    
                            (x, y),             
                        ]
                        codes = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4]
    
                        path = Path(verts, codes)
                        patch = PathPatch(
                            path,
                            edgecolor="#555555",
                            linewidth=1.4,
                            facecolor="none",
                            zorder=1.5,
                        )
                        plt.gca().add_patch(patch)
    
                        label_y_offset = dy * 0.55
                        plt.text(
                            x,
                            y + label_y_offset,
                            full_text,
                            ha="center",
                            va="center",
                            fontsize=8,
                            color="darkblue",
                            zorder=3,
                            bbox=dict(
                                facecolor="white",
                                edgecolor="lightgray",
                                alpha=0.9,
                                pad=0.25,
                                boxstyle="round,pad=0.15",
                            ),
                        )
                        continue
    
                    x1, y1 = pos[u]
                    x2, y2 = pos[v]
                    
                    if is_bidirectional:
                        rad = 0.2
                        nx.draw_networkx_edges(
                            G, pos, edgelist=[(u,v)], 
                            connectionstyle=f"arc3,rad={rad}", 
                            arrowstyle="-|>", arrowsize=25, edge_color="#555555", width=1.5,
                            node_size=NODE_SIZE
                        )
                        
                        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                        vx, vy = x2 - x1, y2 - y1
                        dist = math.sqrt(vx**2 + vy**2)
                        if dist == 0: dist = 1 
                        
                        nx_vec, ny_vec = vy/dist, -vx/dist
                        offset = rad * dist * 0.6 
                        lx = mx + nx_vec * offset
                        ly = my + ny_vec * offset
                        
                        plt.text(lx, ly, full_text, horizontalalignment='center', verticalalignment='center', fontsize=8, color='darkblue', 
                                bbox=dict(facecolor='white', edgecolor='lightgray', alpha=0.9, pad=0.3, boxstyle='round,pad=0.2'))
    
                    else:
                        nx.draw_networkx_edges(
                            G, pos, edgelist=[(u,v)], 
                            arrowstyle="-|>", arrowsize=25, edge_color="#555555", width=1.5,
                            node_size=NODE_SIZE
                        )
                        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                        plt.text(mx, my, full_text, horizontalalignment='center', verticalalignment='center', fontsize=8, color='darkblue', 
                                bbox=dict(facecolor='white', edgecolor='lightgray', alpha=0.9, pad=0.3, boxstyle='round,pad=0.2'))
    
                plt.title(title, fontsize=14, fontweight='bold')
                plt.axis("off")
                plt.tight_layout()
                plt.show()
            except Exception as e:
                _get_logger().error(f"Failed to draw model graph: {e}")

    def __repr__(self) -> str:
        return f"KripkeFrame({self.name})"

class Model(KripkeFrame):

    """
    Represents a Model extending a KripkeFrame, combining a ManyLattice, 
    world-specific complete sublattices, and propositional valuations.
    """
    def __init__(
        self,
        name: str,
        signature: Signature,
        worlds: Set[World],
        initial_world: World,
        many_lattice: ManyLattice,
        world_lattices: Dict[World, Lattice],
        accessibility_relation: Optional[Dict[str, Dict[World, Set[World]]]] = None,
        description: str = "",
        valuations: Optional[Dict[World, Dict[str, str]]] = None,
    ):
        super().__init__(name, signature, worlds, initial_world, accessibility_relation)

        if not isinstance(many_lattice, ManyLattice):
            _get_logger().error(f"Model '{self.name}' initialization failed: 'many_lattice' is not a ManyLattice instance.")
            raise TypeError("The 'many_lattice' argument must be an instance of ManyLattice.")

        self.many_lattice = many_lattice
        self.description = description
        
        self.world_lattices = {}
        valid_sublattice_names = {lat.name: lat for lat in self.many_lattice.comp_sub_lat}
        
        for world in self.worlds:
            if world not in world_lattices:
                raise ValueError(f"World '{world.name_short}' must have a complete sublattice attributed in 'world_lattices'.")
            
            lat = world_lattices[world]
            if lat.name not in valid_sublattice_names:
                raise ValueError(f"Lattice '{lat.name}' for world '{world.name_short}' is not a registered complete sublattice.")
            
            self.world_lattices[world] = lat

        self.valuations = valuations if valuations is not None else {}
        for world in self.worlds:
            if world not in self.valuations:
                self.valuations[world] = {}

        _get_logger().info(f"Model '{self.name}' initialized with ManyLattice '{self.many_lattice.name_many_lattice}'.")

    def get_world_lattice(self, world: World) -> Lattice:
        if world not in self.world_lattices:
            raise ValueError(f"World '{world.name_short}' has no lattice attributed in this model.")
        return self.world_lattices[world]

    def get_assignment(self, world: World, variable: str) -> Optional[str]:
        return self.valuations.get(world, {}).get(variable)

    def assign_value(self, world: World, variable: str, value: str) -> None:
        if world not in self.worlds:
            raise ValueError("World is not part of the model's frame.")
            
        world_lat = self.get_world_lattice(world)
        if value not in world_lat.elements:
            raise ValueError(f"Value '{value}' is not in the lattice attributed to world '{world.name_long}' in this model.")
            
        if world not in self.valuations:
            self.valuations[world] = {}
        self.valuations[world][variable] = value

    def add_world(self, world: World, lattice: Lattice) -> None:
        super().add_world(world)
        
        valid_sublattice_names = {lat.name: lat for lat in self.many_lattice.comp_sub_lat}
        if lattice.name not in valid_sublattice_names:
            raise ValueError(f"Lattice '{lattice.name}' is not a registered complete sublattice.")
        
        self.world_lattices[world] = lattice
        if world not in self.valuations:
            self.valuations[world] = {}

    def delete_world(self, world: World) -> None:
        super().delete_world(world)
        if world in self.world_lattices:
            del self.world_lattices[world]
        if world in self.valuations:
            del self.valuations[world]

    def __repr__(self) -> str:
        return f"{self.name}"