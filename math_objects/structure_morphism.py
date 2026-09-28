"""
Structure Morphism Module.

This module defines classes for morphisms between Kripke Frames and Models:
- KripkeFrameMorphism: Preserves initial world and transition relations under the same signature.
- ModelMorphism: Extends KripkeFrameMorphism to also preserve the local complete sublattice at each world.
"""

from collections import defaultdict
from typing import Dict, Tuple, List, Optional
import logging
from math_objects.structure import World, KripkeFrame, Model

try:
    import networkx as nx
    import matplotlib.pyplot as plt
    from matplotlib.path import Path
    from matplotlib.patches import PathPatch
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False

def _get_logger():
    return logging.getLogger("StructureMorphism")


class KripkeFrameMorphism:
    """
    Represents a morphism between two Kripke Frames over the same Signature.
    Preserves:
      1. Initial world: h(w_0) = w_0'
      2. Relations: If w1 -a-> w2, then h(w1) -a-> h(w2).
    """

    def __init__(
        self,
        name: str,
        source_frame: KripkeFrame,
        target_frame: KripkeFrame,
        world_map: Dict[World, World]
    ):
        if not isinstance(source_frame, KripkeFrame) or not isinstance(target_frame, KripkeFrame):
            raise TypeError("Source and target must be instances of KripkeFrame.")

        self.name = name
        self.source_frame = source_frame
        self.target_frame = target_frame
        self.world_map = world_map

        _get_logger().info(f"KripkeFrameMorphism '{self.name}' initialized: {source_frame.name} -> {target_frame.name}")

    def verify_morphism(self) -> Tuple[bool, List[str]]:
        """
        Validates whether the mapping satisfies all conditions for a Kripke frame morphism.
        """
        errors = []

        src_sig = self.source_frame.signature
        tgt_sig = self.target_frame.signature
        if src_sig.actions != tgt_sig.actions or src_sig.propositions != tgt_sig.propositions:
            errors.append(
                f"Frames must share the same signature. Source actions: {src_sig.actions}, "
                f"Target actions: {tgt_sig.actions}."
            )

        for w in self.source_frame.worlds:
            if w not in self.world_map or self.world_map[w] is None:
                errors.append(f"World '{w.name_short}' has no assigned target world.")
            elif self.world_map[w] not in self.target_frame.worlds:
                errors.append(
                    f"Image of world '{w.name_short}' ('{self.world_map[w].name_short}') "
                    f"is not a valid world in target frame '{self.target_frame.name}'."
                )

        if errors:
            return False, errors

        mapped_init = self.world_map.get(self.source_frame.initial_world)
        if mapped_init != self.target_frame.initial_world:
            errors.append(
                f"Initial world not preserved: Source initial '{self.source_frame.initial_world.name_short}' "
                f"maps to '{mapped_init.name_short if mapped_init else 'None'}', but target initial is "
                f"'{self.target_frame.initial_world.name_short}'."
            )


        for act in self.source_frame.actions:
            act_rel = self.source_frame.accessibility_relation.get(act, {})
            tgt_act_rel = self.target_frame.accessibility_relation.get(act, {})

            for src_w, target_set in act_rel.items():
                mapped_src = self.world_map.get(src_w)
                tgt_accessible = tgt_act_rel.get(mapped_src, set())

                for tgt_w in target_set:
                    mapped_tgt = self.world_map.get(tgt_w)
                    if mapped_tgt not in tgt_accessible:
                        errors.append(
                            f"Relation not preserved under action '{act}': "
                            f"({src_w.name_short} -> {tgt_w.name_short}) exists in source, but "
                            f"({mapped_src.name_short} -> {mapped_tgt.name_short}) does not exist in target."
                        )

        is_valid = len(errors) == 0
        if not is_valid:
            for err in errors:
                _get_logger().warning(f"Frame morphism '{self.name}' verification issue: {err}")
        else:
            _get_logger().info(f"Frame morphism '{self.name}' verified successfully.")

        return is_valid, errors

    def draw_graph(self) -> None:

        if not VISUALIZATION_AVAILABLE:
            _get_logger().warning("Visualization libraries not installed. Cannot draw graph.")
            return

        plt.figure(figsize=(14, 8))
        plt.title(f"Morphism Visualization: {self.name}\n({self.source_frame.name} ──> {self.target_frame.name})", fontsize=14, fontweight="bold")

        Gs = nx.DiGraph()
        for w in self.source_frame.worlds:
            Gs.add_node(w.name_short)
            
        Gt = nx.DiGraph()
        for w in self.target_frame.worlds:
            Gt.add_node(w.name_short)

        pos_s_raw = nx.spring_layout(Gs, k=2.0, seed=42)
        pos_t_raw = nx.spring_layout(Gt, k=2.0, seed=42)

        pos = {}
        for node, (x, y) in pos_s_raw.items():
            pos[f"src_{node}"] = (x - 3.0, y)
        for node, (x, y) in pos_t_raw.items():
            pos[f"tgt_{node}"] = (x + 3.0, y)

        G_master = nx.DiGraph()
        for w in self.source_frame.worlds:
            G_master.add_node(f"src_{w.name_short}", color="darkblue", label=w.name_short)
        for w in self.target_frame.worlds:
            G_master.add_node(f"tgt_{w.name_short}", color="darkorange", label=w.name_short)

        NODE_SIZE = 2500

        src_edge_data = defaultdict(list)
        for act, rel_map in self.source_frame.accessibility_relation.items():
            for src, targets in rel_map.items():
                for tgt in targets:
                    u, v = f"src_{src.name_short}", f"src_{tgt.name_short}"
                    src_edge_data[(u, v)].append(act)

        for (u, v), text_list in src_edge_data.items():
            full_text = "\n".join(text_list)
            x1, y1 = pos[u]
            x2, y2 = pos[v]
            if u == v:
                x, y = x1, y1
                dx, dy = 0.25, 0.22
                verts = [(x, y), (x + dx, y + dy), (x - dx, y + dy), (x, y)]
                path = Path(verts, [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4])
                plt.gca().add_patch(PathPatch(path, edgecolor="darkblue", linewidth=1.2, facecolor="none", zorder=1.5))
                plt.text(x, y + dy * 0.55, full_text, ha="center", va="center", fontsize=7, color="darkblue",
                        bbox=dict(facecolor="white", edgecolor="lightgray", alpha=0.9, boxstyle="round,pad=0.15"))
            else:
                nx.draw_networkx_edges(G_master, pos, edgelist=[(u, v)], arrowstyle="-|>", arrowsize=20, edge_color="darkblue", width=1.5, node_size=NODE_SIZE)
                plt.text((x1 + x2) / 2, (y1 + y2) / 2, full_text, ha='center', va='center', fontsize=7, color='darkblue',
                        bbox=dict(facecolor='white', edgecolor='lightgray', alpha=0.9, boxstyle='round,pad=0.2'))

        tgt_edge_data = defaultdict(list)
        for act, rel_map in self.target_frame.accessibility_relation.items():
            for src, targets in rel_map.items():
                for tgt in targets:
                    u, v = f"tgt_{src.name_short}", f"tgt_{tgt.name_short}"
                    tgt_edge_data[(u, v)].append(act)

        for (u, v), text_list in tgt_edge_data.items():
            full_text = "\n".join(text_list)
            x1, y1 = pos[u]
            x2, y2 = pos[v]
            if u == v:
                x, y = x1, y1
                dx, dy = 0.25, 0.22
                verts = [(x, y), (x + dx, y + dy), (x - dx, y + dy), (x, y)]
                path = Path(verts, [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4])
                plt.gca().add_patch(PathPatch(path, edgecolor="darkorange", linewidth=1.2, facecolor="none", zorder=1.5))
                plt.text(x, y + dy * 0.55, full_text, ha="center", va="center", fontsize=7, color="darkorange",
                        bbox=dict(facecolor="white", edgecolor="lightgray", alpha=0.9, boxstyle="round,pad=0.15"))
            else:
                nx.draw_networkx_edges(G_master, pos, edgelist=[(u, v)], arrowstyle="-|>", arrowsize=20, edge_color="darkorange", width=1.5, node_size=NODE_SIZE)
                plt.text((x1 + x2) / 2, (y1 + y2) / 2, full_text, ha='center', va='center', fontsize=7, color='darkorange',
                        bbox=dict(facecolor='white', edgecolor='lightgray', alpha=0.9, boxstyle='round,pad=0.2'))

        mapping_edges = []
        for sw, tw in self.world_map.items():
            if tw:
                mapping_edges.append((f"src_{sw.name_short}", f"tgt_{tw.name_short}"))

        nx.draw_networkx_edges(G_master, pos, edgelist=mapping_edges, edge_color="gray", style="dotted", width=2.0, arrowstyle="-|>", arrowsize=18, node_size=NODE_SIZE)

        src_nodes = [n for n, d in G_master.nodes(data=True) if n.startswith("src_")]
        tgt_nodes = [n for n, d in G_master.nodes(data=True) if n.startswith("tgt_")]
        
        nx.draw_networkx_nodes(G_master, pos, nodelist=src_nodes, node_size=NODE_SIZE, node_color="#99ccff", edgecolors="darkblue", linewidths=2.0)
        nx.draw_networkx_nodes(G_master, pos, nodelist=tgt_nodes, node_size=NODE_SIZE, node_color="#ffcc99", edgecolors="darkorange", linewidths=2.0)
        
        node_labels = {n: d["label"] for n, d in G_master.nodes(data=True)}
        nx.draw_networkx_labels(G_master, pos, labels=node_labels, font_size=9, font_weight="bold")

        max_y = max(y for _, y in pos.values())
        header_y = max_y + 0.8

        plt.text(-3.0, header_y, f"Source: {self.source_frame.name}", ha="center", fontsize=11, fontweight="bold", color="darkblue")
        plt.text(3.0, header_y, f"Target: {self.target_frame.name}", ha="center", fontsize=11, fontweight="bold", color="darkorange")

        plt.axis("off")
        plt.tight_layout()
        plt.show()

    def __repr__(self) -> str:
        return f"KripkeFrameMorphism('{self.name}': {self.source_frame.name} -> {self.target_frame.name})"


class ModelMorphism(KripkeFrameMorphism):
    """
    Represents a morphism between two Models over the same Signature.
    Extends KripkeFrameMorphism by requiring that each world's complete sublattice
    is preserved: Lat(w) == Lat(h(w)).
    """

    def __init__(
        self,
        name: str,
        source_model: Model,
        target_model: Model,
        world_map: Dict[World, World]
    ):
        if not isinstance(source_model, Model) or not isinstance(target_model, Model):
            raise TypeError("Source and target must be instances of Model.")

        super().__init__(name, source_model, target_model, world_map)
        self.source_model = source_model
        self.target_model = target_model

    def verify_morphism(self) -> Tuple[bool, List[str]]:
        """
        Validates frame preservation conditions plus local sublattice preservation.
        """
        is_frame_valid, errors = super().verify_morphism()

        for w in self.source_model.worlds:
            mapped_w = self.world_map.get(w)
            if not mapped_w:
                continue

            src_lat = self.source_model.world_lattices.get(w)
            tgt_lat = self.target_model.world_lattices.get(mapped_w)

            if src_lat is None:
                errors.append(f"Source world '{w.name_short}' has no assigned sublattice.")
            elif tgt_lat is None:
                errors.append(f"Target world '{mapped_w.name_short}' has no assigned sublattice.")
            elif src_lat.name != tgt_lat.name:
                errors.append(
                    f"Sublattice not preserved for world '{w.name_short}': "
                    f"Source uses '{src_lat.name}', but target '{mapped_w.name_short}' uses '{tgt_lat.name}'."
                )

        is_valid = len(errors) == 0
        if not is_valid:
            for err in errors:
                _get_logger().warning(f"Model morphism '{self.name}' verification issue: {err}")
        else:
            _get_logger().info(f"Model morphism '{self.name}' verified successfully.")

        return is_valid, errors

    def __repr__(self) -> str:
        return f"ModelMorphism('{self.name}': {self.source_model.name} -> {self.target_model.name})"