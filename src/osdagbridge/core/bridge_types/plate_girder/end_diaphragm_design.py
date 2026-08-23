import copy
import math
from typing import Optional
import pandas as pd

from osdagbridge.core.bridge_types.plate_girder.cross_bracing_design import CrossBracingDesign
from osdagbridge.core.utils.common import (
    KEY_MP_ED_TYPE,
    KEY_MP_ED_BRACING_TYPE,
    KEY_MP_ED_TOP_CHORD,
    KEY_MP_ED_BOTTOM_CHORD,
    KEY_TS_NO_OF_GIRDERS,
    KEY_TS_GIRDER_SPACING,
    KEY_MP_GIRDER_DEPTH,
)

class EndDiaphragmDesign:
    def __init__(self, bridge):
        self.bridge = bridge
        self.cb_design = CrossBracingDesign(bridge=bridge, include_edge_beams=False)

    def get_end_diaphragm_count(self) -> int:
        return 2 # Usually start and end

    def get_forces_and_design(self) -> dict:
        """
        Runs design for all end diaphragms based on user type selection.
        Returns a dict of pair designs.
        """
        if not self.bridge.result_data:
            return {}

        model = self.bridge.grillage_model.model
        if not model:
            return {}

        start_elements = [str(e) for e in model.get_element(member="start_edge", options="elements")]
        end_elements = [str(e) for e in model.get_element(member="end_edge", options="elements")]
        all_edge_elements = start_elements + end_elements

        girders = self.bridge.result_data.get("girders", {})
        girder_node_sets = {
            g_name: set(g_data.get("nodes", []))
            for g_name, g_data in girders.items()
        }

        def _find_girder(node) -> Optional[str]:
            for g_name, node_set in girder_node_sets.items():
                if node in node_set:
                    return g_name
            return None

        pair_to_elements = {}
        for m in all_edge_elements:
            if m not in self.bridge.result_data.get("members", {}):
                continue
            n1, n2 = self.bridge.result_data["members"][m]
            g1 = _find_girder(n1)
            g2 = _find_girder(n2)
            if g1 and g2 and g1 != g2:
                idx1 = girders[g1].get("index", 0)
                idx2 = girders[g2].get("index", 0)
                pair = f"{g1}-{g2}" if idx1 <= idx2 else f"{g2}-{g1}"
                pair_to_elements.setdefault(pair, []).append(m)

        n_girders = int(self.bridge.input_dict[KEY_TS_NO_OF_GIRDERS])
        pairs = [f"G{i}-G{i+1}" for i in range(1, n_girders)]

        D = float(self.bridge.input_dict.get(KEY_MP_GIRDER_DEPTH, 1.0))
        h = D * 0.85
        s = float(self.bridge.input_dict.get(KEY_TS_GIRDER_SPACING, 3.0))

        pair_designs = {}
        forces_dict = {"pairs": {}}
        
        # Populate for all pairs
        for i, pair in enumerate(pairs, start=1):
            pair_id = pair.replace("-", "")
            _m1 = f".{pair_id}.E{i}M1"
            _m2 = f".{pair_id}.E{i}M2"
            
            # Find the type
            member_suffix = _m1 if self.bridge.input_dict.get(f"{KEY_MP_ED_TYPE}{_m1}") else _m2
            ed_type = self.bridge.input_dict.get(f"{KEY_MP_ED_TYPE}{member_suffix}") or ""
            
            pair_designs[pair] = {"ed_type": ed_type}

            elements = pair_to_elements.get(pair, [])
            
            if ed_type == "Cross Bracing":
                bracing_type = self.bridge.input_dict.get(f"{KEY_MP_ED_BRACING_TYPE}{member_suffix}")
                horiz_proj = s if bracing_type in ("X", "X-Bracing") else s / 2.0
                L_d = math.sqrt(horiz_proj ** 2 + h ** 2)
                cos_alpha = math.cos(math.atan2(h, horiz_proj))
                
                diag_tens_max, diag_comp_max = 0.0, 0.0
                chord_tens_max, chord_comp_max = 0.0, 0.0

                for lc in self.bridge.result_data["loadcases"]:
                    lc_str = str(lc)
                    if lc_str.startswith("Envelope"): continue
                    
                    for m in elements:
                        if lc_str not in self.bridge.result_data["forces"] or m not in self.bridge.result_data["forces"][lc_str]:
                            continue
                        vz_i = self.bridge.result_data["forces"][lc_str][m].get("Vz_i")
                        if vz_i is None: continue
                        
                        vz_kn = vz_i / 1000.0
                        f_diag = vz_kn / cos_alpha
                        f_chord = vz_kn
                        
                        if f_diag > diag_tens_max: diag_tens_max = f_diag
                        if f_diag < diag_comp_max: diag_comp_max = f_diag
                        if f_chord > chord_tens_max: chord_tens_max = f_chord
                        if f_chord < chord_comp_max: chord_comp_max = f_chord

                forces_dict["pairs"][pair] = {
                    "diag_tension_kN": round(diag_tens_max, 3) if diag_tens_max > 0.005 else None,
                    "diag_compression_kN": round(abs(diag_comp_max), 3) if diag_comp_max < -0.005 else None,
                    "chord_tension_kN": round(chord_tens_max, 3) if chord_tens_max > 0.005 else None,
                    "chord_compression_kN": round(abs(chord_comp_max), 3) if chord_comp_max < -0.005 else None,
                }
                
                # Copy geometry
                forces_dict["geometry"] = {
                    "diagonal_length_m": L_d,
                    "horiz_proj_m": horiz_proj
                }

            elif ed_type in ("Rolled Beam", "Welded Beam"):
                # Extract Vy and Mz
                vy_max, mz_max = 0.0, 0.0
                for lc in self.bridge.result_data["loadcases"]:
                    lc_str = str(lc)
                    if lc_str.startswith("Envelope"): continue
                    
                    for m in elements:
                        if lc_str not in self.bridge.result_data["forces"] or m not in self.bridge.result_data["forces"][lc_str]:
                            continue
                        vy_i = self.bridge.result_data["forces"][lc_str][m].get("Vy_i", 0.0)
                        vy_j = self.bridge.result_data["forces"][lc_str][m].get("Vy_j", 0.0)
                        mz_i = self.bridge.result_data["forces"][lc_str][m].get("Mz_i", 0.0)
                        mz_j = self.bridge.result_data["forces"][lc_str][m].get("Mz_j", 0.0)
                        
                        vy_kn = max(abs(vy_i / 1000.0), abs(vy_j / 1000.0))
                        mz_knm = max(abs(mz_i / 1000.0), abs(mz_j / 1000.0))
                        
                        if vy_kn > vy_max: vy_max = vy_kn
                        if mz_knm > mz_max: mz_max = mz_knm
                
                forces_dict["pairs"][pair] = {
                    "vy_kN": round(vy_max, 3),
                    "mz_kNm": round(mz_max, 3)
                }
                
        # Now design members
        cb_forces_for_design = {"pairs": {}, "geometry": forces_dict.get("geometry", {})}
        for p, d in forces_dict["pairs"].items():
            if "diag_tension_kN" in d:
                cb_forces_for_design["pairs"][p] = d

        cb_designs = self.cb_design.run_member_designs(cb_forces_for_design)
        
        for p, designs in cb_designs.items():
            if p in pair_designs:
                pair_designs[p].update(designs)
                
        self.forces_dict = forces_dict
        return pair_designs
