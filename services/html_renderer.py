"""
HTML Renderer Module.

This service handles all HTML string generation for UI displays, object detail cards, 
symbol legends, and mathematical definition popups.
"""

class HTMLRenderer:
    """Service to handle all HTML string generation for UI displays."""

    @staticmethod
    def _clean_str(obj) -> str:
        return str(obj).replace("'", "")

    @staticmethod
    def render_lattice(l, colors: dict) -> str:
        c_head, c_acc, c_sub = colors["header"], colors["accent"], colors["subtle"]
        html = f"<h3 style='color:{c_head};'>LATTICE: {l.name}</h3>"
        html += f"<b>Elements ({len(l.elements)}):</b><br>"
        clean_elems = [HTMLRenderer._clean_str(e) for e in sorted(list(l.elements))]
        html += f"<span style='font-family:monospace; color:{c_acc};'>{{{', '.join(clean_elems)}}}</span><br><br>"
        
        html += "<b>Relations (≤):</b><br>"
        rels_fmt = [f"({HTMLRenderer._clean_str(a)},{HTMLRenderer._clean_str(b)})" for a, b in sorted(list(l.relations))]
        html += f"<span style='font-family:monospace; color:{c_sub};'>{', '.join(rels_fmt)}</span><br><br>"
        
        if hasattr(l, 'negation_map') and l.negation_map:
            html += "<b>Negation (~):</b><br>"
            html += "<table border='0' cellspacing='2' cellpadding='2' style='font-family:monospace;'>"
            for a, res in sorted(l.negation_map.items()):
                html += f"<tr><td>~{HTMLRenderer._clean_str(a)}</td><td>= <b>{HTMLRenderer._clean_str(res)}</b></td></tr>"
            html += "</table><br>"

        html += "<b>Implication (→):</b><br>"
        if hasattr(l, 'implication_map') and l.implication_map:
            html += "<table border='0' cellspacing='2' cellpadding='2' style='font-family:monospace;'>"
            for (a, b), res in sorted(l.implication_map.items(), key=lambda x: str(x[0])):
                html += f"<tr><td>{HTMLRenderer._clean_str(a)} → {HTMLRenderer._clean_str(b)}</td><td>= <b>{HTMLRenderer._clean_str(res)}</b></td></tr>"
            html += "</table>"
        else:
            html += f"<i style='color:{c_sub};'>(Not defined)</i>"
        return html

    @staticmethod
    def render_filtered_lattice(fl, colors: dict) -> str:
        c_info, c_warn, c_sub = colors["info"], colors["warn"], colors["subtle"]
        html = f"<h3 style='color:{c_info};'>FILTERED LATTICE: {fl.name_filtered_lattice}</h3>"
        html += f"<b>Base Lattice:</b> {fl.name}<br>"
        
        filter_elems = sorted(list(fl.filter)) if hasattr(fl, 'filter') and fl.filter else []
        clean_filter = [HTMLRenderer._clean_str(e) for e in filter_elems]
        html += f"<b>Filter Set:</b> <span style='color:{c_warn};'>{{{', '.join(clean_filter)}}}</span><br>"
        return html

    @staticmethod
    def render_many_lattice(ml, colors: dict) -> str:
        c_acc, c_info, c_sub = colors["accent"], colors["info"], colors["subtle"]
        html = f"<h3 style='color:{c_acc};'>MANY LATTICE: {ml.name_many_lattice}</h3>"
        html += f"<b>Base Filtered Lattice:</b> {ml.name_filtered_lattice}<br>"
        html += f"<b>Base Lattice Name:</b> {ml.name}<br><br>"
        
        filter_elems = sorted(list(ml.filter)) if hasattr(ml, 'filter') and ml.filter else []
        html += f"<b>Global Filter:</b> <span style='color:{colors.get('warn', '#d35400')};'>{{{', '.join([HTMLRenderer._clean_str(e) for e in filter_elems])}}}</span><br><br>"

        html += "<b>Complete Sublattices (Logics):</b><br>"
        if hasattr(ml, 'comp_sub_lat') and ml.comp_sub_lat:
            for sub in ml.comp_sub_lat:
                sub_elems = sorted(list(sub.elements), key=str)
                html += f"&bull; <b style='color:{c_info};'>{sub.name}</b>: {{{', '.join([HTMLRenderer._clean_str(e) for e in sub_elems])}}}<br>"
        else:
            html += f"<i style='color:{c_sub};'>(No sublattices defined)</i>"
        return html

    @staticmethod
    def render_world(w, colors: dict, is_dark: bool = False) -> str:
        c_info, c_sub = colors["info"], colors["subtle"]
        html = f"<h3 style='color:{c_info};'>STATE: {w.name_long}</h3>"
        html += f"<b>Short Identifier:</b> <span style='font-family:monospace;'>{w.name_short}</span><br>"
        return html

    @staticmethod
    def render_kripke_frame(kf, colors: dict) -> str:
        c_info, c_text, c_sub = colors["info"], colors["text"], colors["subtle"]
        html = f"<h3 style='color:{c_info};'>KRIPKE FRAME: {kf.name}</h3>"
        
        if hasattr(kf, 'signature') and kf.signature:
            html += f"<b>Signature:</b> {kf.signature.name}<br>"

        init_name = kf.initial_world.name_short if kf.initial_world else "None"
        html += f"<b>Initial State:</b> {init_name}<br>"
        
        worlds_str = ', '.join(sorted([w.name_short for w in kf.worlds])) if kf.worlds else "None"
        html += f"<b>States ({len(kf.worlds)}):</b> {worlds_str}<br>"
        
        actions_str = ', '.join(sorted(list(kf.actions))) if kf.actions else "None"
        html += f"<b>Actions ({len(kf.actions)}):</b> {actions_str}<br><br>"

        html += "<b>Accessibility Relations (R):</b><br>"
        if not kf.actions:
            html += f"<i style='color:{c_sub};'>(No actions defined)</i>"
        else:
            for action in sorted(list(kf.actions)):
                html += f"<div style='margin-top:5px; font-weight:bold; color:{c_text};'>Action [{action}]:</div>"
                action_map = kf.accessibility_relation.get(action, {})
                sorted_src = sorted(action_map.keys(), key=lambda w: w.name_short)
                has_edges = False
                for src in sorted_src:
                    targets = action_map[src]
                    if targets:
                        has_edges = True
                        target_names = sorted([t.name_short for t in targets if t is not None])
                        html += f"<div style='margin-left:15px; font-family:monospace; color:{c_text};'>{src.name_short} &#8594; {{ {', '.join(target_names)} }}</div>"
                if not has_edges:
                    html += f"<div style='margin-left:15px; font-style:italic; color:{c_sub};'>No relations defined</div>"
        return html

    @staticmethod
    def render_model(m, colors: dict, is_dark: bool = False) -> str:
        c_err, c_text, c_sub, c_info = colors["error"], colors["text"], colors["subtle"], colors["info"]
        border_c = "#555" if is_dark else "#ddd"
        bg_c = "#333" if is_dark else "#f2f2f2"

        html = f"<h3 style='color:{c_err};'>MODEL: {m.name}</h3>"
        
        if getattr(m, 'description', None):
            html += f"<b>Description:</b> {m.description}<br><br>"
            
        html += f"<b>Many-Lattice:</b> {m.many_lattice.name_many_lattice}<br>"
        
        if hasattr(m, 'signature') and m.signature:
            html += f"<b>Signature:</b> {m.signature.name}<br>"
            
        init_name = m.initial_world.name_short if m.initial_world else "None"
        html += f"<b>Initial State:</b> {init_name}<br>"
        html += f"<b>States:</b> {', '.join(sorted([w.name_short for w in m.worlds]))}<br>"
        html += f"<b>Actions:</b> {', '.join(sorted(list(m.actions)))}<br><br>"

        # World Sublattices
        html += "<b>State Complete Sublattices:</b><br>"
        html += f"<table border='1' cellspacing='0' cellpadding='4' style='border-collapse:collapse; border-color:{border_c}; font-family:monospace; margin-bottom:10px;'>"
        html += f"<tr style='background-color:{bg_c};'><th>World</th><th>Sublattice</th><th>Elements</th></tr>"
        for w in sorted(list(m.worlds), key=lambda x: x.name_short):
            sub_lat = m.world_lattices.get(w)
            sub_name = sub_lat.name if sub_lat else "Unassigned"
            elems = f"{{{', '.join(sorted([HTMLRenderer._clean_str(e) for e in sub_lat.elements]))}}}" if sub_lat else "{}"
            html += f"<tr><td>{w.name_short} ({w.name_long})</td><td style='color:{c_info};'><b>{sub_name}</b></td><td>{elems}</td></tr>"
        html += "</table><br>"

        html += "<b>Proposition Valuations:</b><br>"
        props = sorted(list(m.signature.propositions)) if hasattr(m, 'signature') and m.signature else []
        if props and m.worlds:
            html += f"<table border='1' cellspacing='0' cellpadding='4' style='border-collapse:collapse; border-color:{border_c}; font-family:monospace; margin-bottom:10px;'>"
            html += f"<tr style='background-color:{bg_c};'><th>State</th>"
            for p in props:
                html += f"<th>{p}</th>"
            html += "</tr>"

            for w in sorted(list(m.worlds), key=lambda x: x.name_short):
                html += f"<tr><td>{w.name_short}</td>"
                for p in props:
                    val = m.get_assignment(w, p)
                    val_str = HTMLRenderer._clean_str(val) if val is not None else "-"
                    html += f"<td style='color:{c_info}; text-align:center;'>{val_str}</td>"
                html += "</tr>"
            html += "</table><br>"
        else:
            html += f"<i style='color:{c_sub};'>(No valuations defined)</i><br><br>"

        html += "<b>Accessibility Relations (R):</b><br>"
        if not m.actions:
            html += f"<i style='color:{c_sub};'>(No actions defined)</i>"
        else:
            for action in sorted(list(m.actions)):
                html += f"<div style='margin-top:5px; font-weight:bold; color:{c_text};'>Action [{action}]:</div>"
                action_map = m.accessibility_relation.get(action, {})
                sorted_src = sorted(action_map.keys(), key=lambda w: w.name_short)
                has_edges = False
                for src in sorted_src:
                    targets = action_map[src]
                    if targets:
                        has_edges = True
                        target_names = sorted([t.name_short for t in targets if t is not None])
                        html += f"<div style='margin-left:15px; font-family:monospace; color:{c_text};'>{src.name_short} &#8594; {{ {', '.join(target_names)} }}</div>"
                if not has_edges:
                    html += f"<div style='margin-left:15px; font-style:italic; color:{c_sub};'>No relations defined</div>"
        return html

    @staticmethod
    def render_symbol_legend(is_dark: bool, info_color: str) -> str:
        text_col, bg_col = ("white", "#333") if is_dark else ("black", "#f0f0f0")
        return f"""
        <h3 style='color:{info_color};'>Symbol Legend</h3>
        <table border="1" cellpadding="4" cellspacing="0" style='border-collapse: collapse; color:{text_col};'>
            <tr style='background-color:{bg_col};'><td><b>Button</b></td><td><b>Input Syntax</b></td><td><b>Description</b></td></tr>
            <tr><td>□</td><td>[]A</td><td>Necessity (Box)</td></tr>
            <tr><td>◇</td><td>&lt;&gt;A</td><td>Possibility (Diamond)</td></tr>
            <tr><td>¬</td><td>~A</td><td>Negation</td></tr>
            <tr><td>∧</td><td>A & B</td><td>Conjunction (Meet)</td></tr>
            <tr><td>∨</td><td>A | B</td><td>Disjunction (Join)</td></tr>
            <tr><td>→</td><td>A -> B</td><td>Implication</td></tr>
            <tr><td>↔</td><td>A &lt;-&gt; B</td><td>Bi-implication</td></tr>
        </table>"""

    @staticmethod
    def render_mathematical_definitions(is_dark: bool = False, info_color: str = "#2A7BDE") -> str:
        text_color = "#E0E0E0" if is_dark else "#222222"
        box_bg = "#2D3139" if is_dark else "#F5F7FA"
        border_col = "#444A57" if is_dark else "#D0D7DE"
        header_col = info_color

        return f"""
        <div style="font-family: Arial, sans-serif; color: {text_color}; line-height: 1.5; padding: 6px;">
            <h2 style="color: {header_col}; margin-bottom: 8px;">Mathematical Definitions Reference</h2>

            <div style="background-color: {box_bg}; border: 1px solid {border_col}; border-radius: 6px; padding: 10px; margin-bottom: 12px;">
                <b style="color: {header_col};">1. Signature & Signature Morphism</b><br>
                A <b>Signature</b> &Sigma; = (Prop, Act) defines propositional variables and actions.<br>
                A <b>Signature Morphism</b> &sigma;: &Sigma;<sub>1</sub> &rarr; &Sigma;<sub>2</sub> consists of mappings 
                <i>f: Prop<sub>1</sub> &rarr; Prop<sub>2</sub></i> and <i>g: Act<sub>1</sub> &rarr; Act<sub>2</sub></i>.
            </div>

            <div style="background-color: {box_bg}; border: 1px solid {border_col}; border-radius: 6px; padding: 10px; margin-bottom: 12px;">
                <b style="color: {header_col};">2. Lattices, Filtered Lattices & Many-Lattices</b><br>
                A <b>Lattice</b> L = (A, &le;) is a poset where every pair of elements has meet (&and;) and join (&or;).<br>
                A <b>Filtered Lattice</b> (L, D) pairs a base lattice with and a filter D &sube; A.<br>
                A <b>Many-Lattice</b> associates a filtered lattice with a family of complete sublattices.
            </div>

            <div style="background-color: {box_bg}; border: 1px solid {border_col}; border-radius: 6px; padding: 10px; margin-bottom: 12px;">
                <b style="color: {header_col};">3. Kripke Frame & Kripke Frame Morphism</b><br>
                A <b>Kripke Frame</b> over &Sigma; is a tuple &lang;W, w<sub>0</sub>, (R<sub>a</sub> )<sub>a &isin; Act</sub>&rang; where 
                W is a set of states, w<sub>0</sub> &isin; W is the initial state, and R<sub>a</sub> &sube; W &times; W.<br>
                A <b>Kripke Frame Morphism</b> h: F &rarr; F' between frames over the same signature preserves:
                <ul style="margin: 4px 0 4px 18px; padding: 0;">
                    <li>Initial state: h(w<sub>0</sub>) = w'<sub>0</sub></li>
                    <li>Transitions: If w<sub>1</sub> R<sub>a</sub> w<sub>2</sub>, then h(w<sub>1</sub>) R'<sub>a</sub> h(w<sub>2</sub>)</li>
                </ul>
            </div>

            <div style="background-color: {box_bg}; border: 1px solid {border_col}; border-radius: 6px; padding: 10px; margin-bottom: 12px;">
                <b style="color: {header_col};">4. Model & Model Morphism</b><br>
                A <b>Model</b> extends a Kripke frame by attributing a complete sublattice I(w) to each state w &isin; W, 
                plus local valuations v(w, p): W &times; Prop &rarr; I(w).<br>
                A <b>Model Morphism</b> is a frame morphism h that additionally preserves local sublattices: 
                I(w) = I'(h(w)) for all w &isin; W.
            </div>

            <div style="background-color: {box_bg}; border: 1px solid {border_col}; border-radius: 6px; padding: 10px; margin-bottom: 6px;">
                <b style="color: {header_col};">5. Reduct Model</b><br>
                Given &sigma;: &Sigma;<sub>1</sub> &rarr; &Sigma;<sub>2</sub> and a model M<sub>2</sub> over &Sigma;<sub>2</sub>, the <b>Reduct Model</b> M<sub>1</sub> = M<sub>2</sub>|<sub>&sigma;</sub> over &Sigma;<sub>1</sub> preserves the states, initial state, and world sublattices, while pulling back transitions and valuations:
                <ul style="margin: 4px 0 4px 18px; padding: 0;">
                    <li>x R<sub>a</sub> y iff x R<sub>&sigma;(a)</sub> y</li>
                    <li>v<sub>1</sub>(w, p) = v<sub>2</sub>(w, &sigma;(p))</li>
                </ul>
            </div>
        </div>
        """


    @staticmethod
    def render_signature(sig, colors: dict) -> str:
        c_head, c_acc, c_sub = colors["header"], colors["accent"], colors["subtle"]
        html = f"<h3 style='color:{c_head};'>SIGNATURE: {sig.name}</h3>"
        
        props = sorted(list(sig.propositions))
        html += f"<b>Propositions ({len(props)}):</b><br>"
        html += f"<span style='font-family:monospace; color:{c_acc};'>{{{', '.join(props)}}}</span><br><br>"
        
        acts = sorted(list(sig.actions))
        html += f"<b>Actions ({len(acts)}):</b><br>"
        html += f"<span style='font-family:monospace; color:{c_sub};'>{{{', '.join(acts)}}}</span><br>"
        return html

    @staticmethod
    def render_signature_morphism(sm, colors: dict) -> str:
        c_info, c_sub = colors["info"], colors["subtle"]
        html = f"<h3 style='color:{c_info};'>SIGNATURE MORPHISM: {sm.name}</h3>"
        html += f"<b>Source Signature:</b> {sm.source_sig.name}<br>"
        html += f"<b>Target Signature:</b> {sm.target_sig.name}<br><br>"
        
        html += "<b>Proposition Mapping (f):</b><br>"
        html += "<table border='0' cellspacing='2' cellpadding='2' style='font-family:monospace;'>"
        for k, v in sorted(sm.prop_map.items()):
            html += f"<tr><td>{k}</td><td>&rarr; <b>{v}</b></td></tr>"
        html += "</table><br>"
        
        html += "<b>Action Mapping (g):</b><br>"
        html += "<table border='0' cellspacing='2' cellpadding='2' style='font-family:monospace;'>"
        for k, v in sorted(sm.act_map.items()):
            html += f"<tr><td>{k}</td><td>&rarr; <b>{v}</b></td></tr>"
        html += "</table>"
        return html

    @staticmethod
    def render_structure_morphism(sm, colors: dict) -> str:
        c_info, c_sub, c_acc = colors["info"], colors["subtle"], colors["accent"]
        is_model_morph = hasattr(sm, 'source_model')
        title = "MODEL MORPHISM" if is_model_morph else "KRIPKE FRAME MORPHISM"
        src_name = sm.source_model.name if is_model_morph else sm.source_frame.name
        tgt_name = sm.target_model.name if is_model_morph else sm.target_frame.name

        html = f"<h3 style='color:{c_info};'>{title}: {sm.name}</h3>"
        html += f"<b>Source:</b> {src_name}<br>"
        html += f"<b>Target:</b> {tgt_name}<br><br>"

        html += "<b>World Mapping (h):</b><br>"
        html += "<table border='1' cellspacing='0' cellpadding='4' style='border-collapse:collapse; font-family:monospace;'>"
        html += "<tr><th>Source World</th><th>Target World</th>"
        if is_model_morph:
            html += "<th>Sublattice</th>"
        html += "</tr>"

        for src_w, tgt_w in sorted(sm.world_map.items(), key=lambda pair: pair[0].name_short):
            tgt_repr = f"{tgt_w.name_short} ({tgt_w.name_long})" if tgt_w else "-"
            html += f"<tr><td>{src_w.name_short} ({src_w.name_long})</td><td style='color:{c_acc};'>&rarr; <b>{tgt_repr}</b></td>"
            if is_model_morph:
                lat = sm.source_model.world_lattices.get(src_w)
                html += f"<td>{lat.name if lat else '-'}</td>"
            html += "</tr>"
        html += "</table>"
        return html