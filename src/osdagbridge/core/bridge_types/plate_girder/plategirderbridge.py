from __future__ import annotations
import sqlite3
import types
from pathlib import Path
from .ui_fields import FrontendData
from .dto import (
    ConcreteProperties,
    DeckLayoutProperties,
    GrillageGeometry,
    SectionProperties,
    SteelProperties,
    MaterialProperties,
    BridgeParametersDTO,
    SectionDimsDTO,
    ISectionDimsDTO,
    ShearStudParamsDTO,
    GirderSegmentDTO,
)
from .defaults import (
    BASIC_INPUT_DICT,
)
from .initial_sizing import DEFAULT_FOOTPATH_WIDTH
from .analyser import BridgeGrillageModel
from osdagbridge.core.utils.memory_guard import OpsMemoryGuard, log_memory, tracemalloc_mark_start
from .analysis_results import PlateGirderAnalysisResults
from .designer import run_design_check
from . import deckdesign
from .plot_generator import (
    build_figure_sfd,
    build_figure_bmd,
    # build_figure_bmd_contour,  # commented out
    build_figure_deflection,
    build_figure_grillage,
    build_nodes_members,
    figure_to_bytes,
)
from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017
from osdagbridge.core.utils.common import (
    KEY_STRUCTURE_TYPE,
    KEY_PROJECT_LOCATION,
    KEY_SPAN,
    KEY_CARRIAGEWAY_WIDTH,
    KEY_INCLUDE_MEDIAN,
    KEY_FOOTPATH,
    KEY_TS_FOOTPATH_WIDTH,
    KEY_RAILING_WIDTH,
    KEY_SKEW_ANGLE,
    KEY_DESIGN_MODE,
    KEY_GIRDER,
    KEY_CROSS_BRACING,
    KEY_END_DIAPHRAGM,
    KEY_DECK_CONCRETE_GRADE_BASIC,
    KEY_DS_REINF_MATERIAL,
    KEY_MATERIAL_GIRDER_E, KEY_MATERIAL_GIRDER_G, KEY_MATERIAL_GIRDER_POISSON,
    KEY_MATERIAL_GIRDER_FY, KEY_MATERIAL_GIRDER_FU, KEY_MATERIAL_GIRDER_THERMAL,
    KEY_MATERIAL_DECK_FCK, KEY_MATERIAL_DECK_FCTM, KEY_MATERIAL_DECK_ECM,
    DEFAULT_CRASH_BARRIER_WIDTH,
    DEFAULT_RAILING_WIDTH,
    DEFAULT_GIRDER_SPACING,
    DEFAULT_CROSS_BRACING_SPACING,
    MPa,
    GPa,
    N,
    m,
    KEY_UTIL_FLEXURE,
    KEY_UTIL_SHEAR,
    KEY_UTIL_INTERACTION,
    KEY_UTIL_LTB,
    KEY_UTIL_DEFLECTION_CRACK,
    KEY_UTIL_FATIGUE,
    KEY_UTIL_LONG_TRANS_SHEAR,
    KEY_UTIL_STRESS_LIMITATION,
    KEY_SL_IMPORTANCE_FACTOR, KEY_SL_SOIL_TYPE, KEY_SL_TIME_PERIOD,
    KEY_SL_DAMPING, KEY_SL_RESPONSE_REDUCTION,
    KEY_SL_DEAD_LOAD_MODE, KEY_SL_DEAD_LOAD_VALUE,
    KEY_SL_LIVE_LOAD_MODE, KEY_SL_LIVE_LOAD_VALUE,
    KEY_SL_HORIZONTAL_COEFF, KEY_SL_VERTICAL_COEFF,
    KEY_MD_WIDTH,
    KEY_RL_WIDTH,
    KEY_TS_DECK_OVERHANG,
    KEY_TS_DECK_THICKNESS,
    KEY_TS_NO_OF_GIRDERS,
    KEY_TS_GIRDER_SPACING,
    KEY_TS_OVERALL_WIDTH,
    KEY_TS_FOOTPATH_WIDTH,
    KEY_TS_NO_OF_FOOTPATHS,
    KEY_WC_THICKNESS,
    KEY_WC_DENSITY,
    KEY_MP_GIRDER_SYMMETRY, KEY_MP_GIRDER_DEPTH, KEY_MP_GIRDER_WEB_DEPTH, KEY_MP_GIRDER_WEB_THICKNESS,
    KEY_MP_GIRDER_TOP_FLANGE_WIDTH, KEY_MP_GIRDER_TOP_FLANGE_THICKNESS,
    KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH, KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS,
    KEY_MP_GIRDER_SECTIONAL_AREA, KEY_MP_GIRDER_MASS,
    KEY_MP_GIRDER_SECTIONAL_IZ, KEY_MP_GIRDER_SECTIONAL_IY,
    KEY_MP_GIRDER_RADIUS_GYRATION_Z, KEY_MP_GIRDER_RADIUS_GYRATION_Y,
    KEY_MP_GIRDER_ELASTIC_MODULUS_ZZ, KEY_MP_GIRDER_ELASTIC_MODULUS_ZY,
    KEY_MP_GIRDER_PLASTIC_MODULUS_ZUZ, KEY_MP_GIRDER_PLASTIC_MODULUS_ZUY,
    KEY_MP_GIRDER_TORSION_CONSTANT_IT, KEY_MP_GIRDER_WARPING_CONSTANT_IW,
    KEY_METALLIC_CRASH_BARRIER_TYPE,
    KEY_RIGID_CRASH_BARRIER_TYPE,
    KEY_CRASH_BARRIER_TYPE,
    KEY_CB_TYPE,
    KEY_RL_TYPE,
    KEY_RAILING_TYPE,
    KEY_MD_TYPE,
    KEY_MEDIAN_TYPE,
    KEY_DS_STUD_DIAMETER,
    KEY_DS_STUD_HEIGHT,
    KEY_DS_STUD_COUNT,
    KEY_DS_STUD_TRANSVERSE_SPACING,
    KEY_DS_STUD_HEAD_DIAMETER,
    KEY_DS_STUD_HEAD_HEIGHT,
    KEY_MP_GIRDER_TORSIONAL_RESTRAINT,
    KEY_MP_GIRDER_WARPING_RESTRAINT,
    KEY_MP_GIRDER_WEB_TYPE,

    # Dimensional card
    KEY_SD_GRADE_OF_MATERIAL,
    KEY_SD_SECTION_TYPE,
    KEY_SD_SECTION_DESIGNATION,
    KEY_SD_SECTION_CLASS,
    KEY_SD_TOTAL_DEPTH,
    KEY_SD_WEB_THICKNESS,
    KEY_SD_TOP_FLANGE_WIDTH,
    KEY_SD_TOP_FLANGE_THICKNESS,
    KEY_SD_BOTTOM_FLANGE_WIDTH,
    KEY_SD_BOTTOM_FLANGE_THICKNESS,
    KEY_SD_TORSIONAL_RESTRAINT,
    KEY_SD_WARPING_RESTRAINT,
    KEY_SD_WEB_TYPE,
    KEY_SD_EFFECTIVE_SLAB_WIDTH,
    # Shear connector card
    KEY_SD_SHEAR_YIELD_STRENGTH,
    KEY_SD_SHEAR_ULTIMATE_STRENGTH,
    KEY_SD_SHEAR_DIAMETER,
    KEY_SD_SHEAR_HEIGHT,
    KEY_SD_SHEAR_TRANSVERSE_SPACING,
    KEY_SD_SHEAR_STUDS_PER_SECTION,
    KEY_SD_SHEAR_LONGITUDINAL_SPACING,
    # Section properties card
    KEY_MP_GIRDER_MASS,
    KEY_MP_GIRDER_SECTIONAL_AREA,
    KEY_MP_GIRDER_SECTIONAL_IZ,
    KEY_MP_GIRDER_SECTIONAL_IY,
    KEY_MP_GIRDER_RADIUS_GYRATION_Z,
    KEY_MP_GIRDER_RADIUS_GYRATION_Y,
    KEY_MP_GIRDER_ELASTIC_MODULUS_ZZ,
    KEY_MP_GIRDER_ELASTIC_MODULUS_ZY,
    KEY_MP_GIRDER_PLASTIC_MODULUS_ZUZ,
    KEY_MP_GIRDER_PLASTIC_MODULUS_ZUY,
    KEY_MP_GIRDER_TORSION_CONSTANT_IT,
    KEY_MP_GIRDER_WARPING_CONSTANT_IW,
    KEY_SD_SECTION_PROP_MASS,
    KEY_SD_SECTION_PROP_AREA,
    KEY_SD_SECTION_PROP_IZ,
    KEY_SD_SECTION_PROP_IV,
    KEY_SD_SECTION_PROP_RZ,
    KEY_SD_SECTION_PROP_RV,
    KEY_SD_SECTION_PROP_ZZ,
    KEY_SD_SECTION_PROP_ZV,
    KEY_SD_SECTION_PROP_ZUZ,
    KEY_SD_SECTION_PROP_ZUV,
    KEY_SD_SECTION_PROP_IT,
    KEY_SD_SECTION_PROP_IW,
    KEY_SD_COMPOSITE_IZ,
    KEY_SD_PNA_DEPTH,
    KEY_SD_MU_APPLIED,
    KEY_SD_MD_CAPACITY,
    KEY_SD_FLANGE_SLENDERNESS,
    KEY_SD_WEB_SLENDERNESS,
    KEY_SD_WEB_CLASS_LIMIT,
    KEY_SD_FLANGE_CLASS_LIMIT,
    KEY_SD_CLASS_FLANGE,
    KEY_SD_CLASS_WEB,
    KEY_SD_SHEAR_VU,
    KEY_SD_SHEAR_AV,
    KEY_SD_PANEL_CD,
    KEY_SD_SHEAR_KV,
    KEY_SD_SHEAR_LAMBDA_W,
    KEY_SD_SHEAR_TAU_B,
    KEY_SD_SHEAR_VCR,
    KEY_SD_HIGH_SHEAR,
    KEY_SD_MDV,
    KEY_SD_MN_AXIAL,
    KEY_SD_MN_MOMENT,
    KEY_SD_MN_RATIO,
    KEY_SD_LTB_MCR,
    KEY_SD_LTB_LAMBDA,
    KEY_SD_LTB_CHI,
    KEY_SD_LTB_MB,
    KEY_SD_STIFF_METHOD,
    KEY_SD_STIFF_INT_THICK,
    KEY_SD_STIFF_INT_SPACING,
    KEY_SD_STIFF_END_THICK,
    KEY_SD_STIFF_END_COUNT,
    KEY_SD_STIFF_LONG,
    KEY_SD_IS_IYS_MIN,
    KEY_SD_IS_IYS_PROV,
    KEY_SD_IS_FQ,
    KEY_SD_IS_FQD,
    KEY_SD_BS_R,
    KEY_SD_BS_FCDW_WB,
    KEY_SD_BS_FCDW_LC,
    KEY_SD_BS_FPSD,
    KEY_SD_BS_FCD,
    # Deflection check keys (Table 5.10)
    KEY_SD_DEFL_LIVE,
    KEY_SD_DEFL_TOTAL,
    KEY_SD_DEFL_ALLOW_LIVE,
    KEY_SD_DEFL_ALLOW_TOTAL,
    # Stiffener table
    KEY_SD_STIFFENER_ROW_INTERMEDIATE,
    KEY_SD_STIFFENER_ROW_LONGITUDINAL,
    KEY_SD_STIFFENER_ROW_BEARING,
    KEY_SD_STIFFENER_COL_GRADE,
    KEY_SD_STIFFENER_COL_THICKNESS,
    KEY_SD_STIFFENER_COL_WIDTH,
    KEY_SD_STIFFENER_COL_SPACING,
    # Design options — shear stud transverse spacing input key
    KEY_DS_STUD_TRANSVERSE_SPACING,
    KEY_MP_STIFFENER_LONGITUDINAL_THICKNESS,
    KEY_MP_STIFFENER_BEARING_OUTSTAND,
    KEY_MP_STIFFENER_BEARING_THICKNESS,
    KEY_MP_STIFFENER_SPACING,
    KEY_MP_STIFFENER_NO_BEARING_STIFFENERS,
    KEY_MP_STIFFENER_INTERMEDIATE,
    KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS,
    KEY_MP_STIFFENER_INTERMEDIATE_OUTSTAND,
    KEY_MP_STIFFENER_INTERMEDIATE_SPACING,
    KEY_MP_STIFFENER_LONGITUDINAL,

    # Cross Bracing Details
    KEY_MP_CB_BRACING_SECTION_TYPE,
    KEY_MP_CB_TOP_CHORD_SECTION_DESIG,
    KEY_MP_CB_BOTTOM_CHORD_SECTION_DESIG,

    # Transverse member properties
    KEY_TD_CB_PROP_L, KEY_TD_CB_PROP_H, KEY_TD_CB_PROP_B, KEY_TD_CB_PROP_TW, KEY_TD_CB_PROP_TF,
    KEY_TD_CB_PROP_RZ, KEY_TD_CB_PROP_M, KEY_TD_CB_PROP_A, KEY_TD_CB_PROP_IZ, KEY_TD_CB_PROP_IV,
    KEY_TD_CB_PROP_RV, KEY_TD_CB_PROP_ZZ, KEY_TD_CB_PROP_ZV, KEY_TD_CB_PROP_ZUZ, KEY_TD_CB_PROP_ZUV,
            
    KEY_TD_CB_TOP_CHORD_PROP_L, KEY_TD_CB_TOP_CHORD_PROP_H, KEY_TD_CB_TOP_CHORD_PROP_B, KEY_TD_CB_TOP_CHORD_PROP_TW, KEY_TD_CB_TOP_CHORD_PROP_TF,
    KEY_TD_CB_TOP_CHORD_PROP_RZ, KEY_TD_CB_TOP_CHORD_PROP_M, KEY_TD_CB_TOP_CHORD_PROP_A, KEY_TD_CB_TOP_CHORD_PROP_IZ, KEY_TD_CB_TOP_CHORD_PROP_IV,
    KEY_TD_CB_TOP_CHORD_PROP_RV, KEY_TD_CB_TOP_CHORD_PROP_ZZ, KEY_TD_CB_TOP_CHORD_PROP_ZV, KEY_TD_CB_TOP_CHORD_PROP_ZUZ, KEY_TD_CB_TOP_CHORD_PROP_ZUV,
    
    KEY_TD_CB_BOTTOM_CHORD_PROP_L, KEY_TD_CB_BOTTOM_CHORD_PROP_H, KEY_TD_CB_BOTTOM_CHORD_PROP_B, KEY_TD_CB_BOTTOM_CHORD_PROP_TW, KEY_TD_CB_BOTTOM_CHORD_PROP_TF,
    KEY_TD_CB_BOTTOM_CHORD_PROP_RZ, KEY_TD_CB_BOTTOM_CHORD_PROP_M, KEY_TD_CB_BOTTOM_CHORD_PROP_A, KEY_TD_CB_BOTTOM_CHORD_PROP_IZ, KEY_TD_CB_BOTTOM_CHORD_PROP_IV,
    KEY_TD_CB_BOTTOM_CHORD_PROP_RV, KEY_TD_CB_BOTTOM_CHORD_PROP_ZZ, KEY_TD_CB_BOTTOM_CHORD_PROP_ZV, KEY_TD_CB_BOTTOM_CHORD_PROP_ZUZ, KEY_TD_CB_BOTTOM_CHORD_PROP_ZUV,

    KEY_TD_ED_PROP_L, KEY_TD_ED_PROP_H, KEY_TD_ED_PROP_B, KEY_TD_ED_PROP_TW, KEY_TD_ED_PROP_TF,
    KEY_TD_ED_PROP_RZ, KEY_TD_ED_PROP_M, KEY_TD_ED_PROP_A, KEY_TD_ED_PROP_IZ, KEY_TD_ED_PROP_IV,
    KEY_TD_ED_PROP_RV, KEY_TD_ED_PROP_ZZ, KEY_TD_ED_PROP_ZV, KEY_TD_ED_PROP_ZUZ, KEY_TD_ED_PROP_ZUV,

    KEY_TD_ED_TOP_CHORD_PROP_L, KEY_TD_ED_TOP_CHORD_PROP_H, KEY_TD_ED_TOP_CHORD_PROP_B, KEY_TD_ED_TOP_CHORD_PROP_TW, KEY_TD_ED_TOP_CHORD_PROP_TF,
    KEY_TD_ED_TOP_CHORD_PROP_RZ, KEY_TD_ED_TOP_CHORD_PROP_M, KEY_TD_ED_TOP_CHORD_PROP_A, KEY_TD_ED_TOP_CHORD_PROP_IZ, KEY_TD_ED_TOP_CHORD_PROP_IV,
    KEY_TD_ED_TOP_CHORD_PROP_RV, KEY_TD_ED_TOP_CHORD_PROP_ZZ, KEY_TD_ED_TOP_CHORD_PROP_ZV, KEY_TD_ED_TOP_CHORD_PROP_ZUZ, KEY_TD_ED_TOP_CHORD_PROP_ZUV,

    KEY_TD_ED_BOTTOM_CHORD_PROP_L, KEY_TD_ED_BOTTOM_CHORD_PROP_H, KEY_TD_ED_BOTTOM_CHORD_PROP_B, KEY_TD_ED_BOTTOM_CHORD_PROP_TW, KEY_TD_ED_BOTTOM_CHORD_PROP_TF,
    KEY_TD_ED_BOTTOM_CHORD_PROP_RZ, KEY_TD_ED_BOTTOM_CHORD_PROP_M, KEY_TD_ED_BOTTOM_CHORD_PROP_A, KEY_TD_ED_BOTTOM_CHORD_PROP_IZ, KEY_TD_ED_BOTTOM_CHORD_PROP_IV,
    KEY_TD_ED_BOTTOM_CHORD_PROP_RV, KEY_TD_ED_BOTTOM_CHORD_PROP_ZZ, KEY_TD_ED_BOTTOM_CHORD_PROP_ZV, KEY_TD_ED_BOTTOM_CHORD_PROP_ZUZ, KEY_TD_ED_BOTTOM_CHORD_PROP_ZUV,
)

from osdagbridge.core.bridge_types.plate_girder.initial_sizing import (
    DEFAULT_DECK_THICKNESS as _DEFAULT_DECK_THICKNESS_MM,
)
from osdagbridge.core.bridge_components.super_structure.deck.geometry import (
    deck_thickness_from_inputs,
)
from osdagbridge.core.bridge_components.super_structure.crash_barrier.geometry import (
    crash_barrier_load_from_inputs,
)
from osdagbridge.core.bridge_components.super_structure.railing.geometry import (
    railing_load_from_inputs,
)
from osdagbridge.core.bridge_components.super_structure.shear_studs.geometry import (
    min_stud_head_diameter,
    min_stud_head_height,
)
from osdagbridge.core.utils.logger import bridge_logger
from osdagbridge.core.bridge_types.plate_girder.designer import (BridgeConfig, IRC22CapacityCalculator, DCREngine, DemandEnvelope, design_envelope_engine,)

_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "ResourceFiles" / "Intg_osdag.sqlite"

# Steel constants (same values used in analyser.py __main__)
_STEEL_E0       = 200 * GPa    # Initial elastic modulus (Pa)
_STEEL_B        = 0.01         # Strain-hardening ratio
_STEEL_FY_DEFAULT = 250 * MPa  # Fallback Fy if material not found in DB (Pa)


def resolve_girder_value(source: dict, base_key: str, i: int | None = None):
    """
    Resolve a girder property from an input/output dict, tolerating both the
    per-girder dynamic key scheme and the legacy scalar key.

    Per-girder values are stored under ``<base_key>.G{i+1}.M1`` (see
    ``defaults.solve_extend_basic_input_dict``). Resolution order:

      1. ``<base_key>.G{i+1}.M1`` — the requested girder (only when ``i`` given),
      2. ``<base_key>``           — the legacy scalar key, if still populated,
      3. ``<base_key>.G1.M1``     — first girder, the representative fallback used
                                    for edge beams / transverse members and any
                                    consumer that does not care about a specific
                                    girder.

    Raises ``KeyError(base_key)`` if none of the candidates are present.
    """
    candidates = []
    if i is not None:
        candidates.append(f"{base_key}.G{i + 1}.M1")
    candidates.append(base_key)
    candidates.append(f"{base_key}.G1.M1")
    for key in candidates:
        if key in source:
            return source[key]
    raise KeyError(base_key)


class PlateGirderBridge:
    """Core backend for Plate Girder Bridge."""

    # Keys that originate from the basic input dock.
    # Everything else in input_dict is treated as an additional input.
    _BASIC_INPUT_KEYS = frozenset({
        KEY_STRUCTURE_TYPE,
        KEY_PROJECT_LOCATION,
        KEY_SPAN,
        KEY_CARRIAGEWAY_WIDTH,
        KEY_INCLUDE_MEDIAN,
        KEY_FOOTPATH,
        KEY_SKEW_ANGLE,
        KEY_DESIGN_MODE,
        KEY_GIRDER,
        KEY_CROSS_BRACING,
        KEY_END_DIAPHRAGM,
        KEY_DECK_CONCRETE_GRADE_BASIC,
        KEY_MD_WIDTH,
    })

    def __init__(self) -> None:
        self.input_dict: dict = {}
        self.basic_inputs: dict = {}
        self.additional_inputs: dict = {}
        self._frontend = FrontendData()
        # Immutable snapshot of input_dict captured at the start of design().
        # All 3D CAD / IFC methods read from this instead of the live input_dict.
        self.output_dict: types.MappingProxyType = types.MappingProxyType({})

        # Results populated by design()
        self.grillage_geometry: GrillageGeometry | None = None
        self.deck_layout: DeckLayoutProperties | None = None
        self.result_data: dict = {}         # flat restructured dataset, set after analysis

        # Analyser — populated by setup_grillage()
        self.grillage_model: BridgeGrillageModel = BridgeGrillageModel()

        # Central ospgrillage / OpenSeesPy memory-release policy (see OpsMemoryGuard).
        self.memory = OpsMemoryGuard(self)

        # When True, design() writes tools/bridge_full_data.json. Off by default.
        self.dump_json: bool = False

    def input_values(self) -> list:
        """Return UI field definitions for the InputDock (delegated to FrontendData)."""
        return self._frontend.input_values()
    
    def output_values(self) -> list:
        """Return UI field definitions for the OutputDock (delegated to FrontendData)."""
        return self._frontend.output_values()

    def set_input(self, input_dict: dict) -> None:
        """
        Receive and store the input dictionary from the UI.

        Stores the full dict in ``self.input_dict`` and splits it into:
        - ``self.basic_inputs``  — keys from the main input dock
        - ``self.additional_inputs`` — all remaining keys (additional-input dialog, etc.)

        All values are normalised so that numeric strings are coerced to
        ``int`` / ``float`` before any downstream consumer touches them.

        Parameters
        ----------
        input_dict : dict
            The flat dictionary built and maintained by ``CustomWindow``.
        """
        self.input_dict = self._normalize_input_dict(input_dict)
        self.basic_inputs = {
            k: v for k, v in self.input_dict.items()
            if k in self._BASIC_INPUT_KEYS
        }
        self.additional_inputs = {
            k: v for k, v in self.input_dict.items()
            if k not in self._BASIC_INPUT_KEYS
        }

    # ------------------------------------------------------------------
    # Input normalisation
    # ------------------------------------------------------------------

    @staticmethod
    def _coerce(value):
        """Convert a value to its natural Python type, recursively.

        * Numeric strings → ``int`` (if no decimal point) or ``float``.
        * ``bool``, ``int``, ``float`` pass through as-is.
        * ``list`` → each element is coerced recursively.
        * ``dict`` → each value is coerced recursively.
        * Everything else (non-numeric strings) is returned unchanged.
        """
        # --- scalars already in the right type ---
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value

        # --- lists: recurse into each element ---
        if isinstance(value, list):
            return [PlateGirderBridge._coerce(item) for item in value]

        # --- dicts: coerce each value, keep keys as-is ---
        if isinstance(value, dict):
            return {k: PlateGirderBridge._coerce(v) for k, v in value.items()}

        # --- strings: try numeric conversion ---
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return value
            # int check first — ``"400"`` should stay int, not float
            try:
                int_val = int(text)
                if str(int_val) == text:
                    return int_val
            except (ValueError, TypeError):
                pass
            try:
                return float(text)
            except (ValueError, TypeError):
                pass
        return value

    @classmethod
    def _normalize_input_dict(cls, raw: dict) -> dict:
        """Return a copy of *raw* with all values coerced to native types."""
        return {k: cls._coerce(v) for k, v in raw.items()}

    # ─────────────────────────────────────────────────────────────────────────
    # Design pipeline
    # ─────────────────────────────────────────────────────────────────────────

    def _resolve_optimized_bounds_to_mm(self) -> None:
        """
        For Optimised design, per-girder dimensional keys may hold list values
        (user-supplied optimisation bounds in mm) or the string "All".
        This method collapses each such key to a single float **stored in metres**
        so that designer and analyser remain in SI units.

        Resolution rule (applied only to list / string values):
          * list  → floor(min(min(list), max(list), initial_sizing_default_mm)) / 1000
          * "All" → snap the initial-sizing default UP to the next SAIL-approved
                    thickness (smallest SAIL value >= initial_sizing_mm), / 1000.
                    "All" is only ever stored for the three thickness keys.
          * float (mm) → left for _convert_girder_dims_mm_to_m to divide by 1000.

        ``initial_sizing_default_mm`` is BridgeConfigurationSolver
        .compute_section_properties() value × 1000.

        Keys resolved (per girder, suffix ``.G{n}.M1``):
            KEY_MP_GIRDER_DEPTH, KEY_MP_GIRDER_WEB_DEPTH,
            KEY_MP_GIRDER_TOP_FLANGE_WIDTH, KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH,
            KEY_MP_GIRDER_TOP_FLANGE_THICKNESS, KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS,
            KEY_MP_GIRDER_WEB_THICKNESS
        """
        import math
        from .initial_sizing import BridgeConfigurationSolver
        from osdagbridge.core.utils.common import SAIL_APPROVED_THICKNESS_VALUES

        inp = self.input_dict
        if str(inp.get(KEY_DESIGN_MODE, '')).strip() != 'Optimized':
            return

        sail_mm = sorted(float(s) for s in SAIL_APPROVED_THICKNESS_VALUES)

        def _snap_up_to_sail(value_mm: float) -> float:
            """Smallest SAIL-approved thickness >= value_mm.

            If value_mm exceeds the largest SAIL value, use value_mm itself
            (no clamping to the SAIL maximum).
            """
            for s in sail_mm:
                if s >= value_mm:
                    return s
            return value_mm

        span  = float(inp[KEY_SPAN])
        count = self._girder_count()

        _DIM_KEYS = [
            (KEY_MP_GIRDER_DEPTH,                   'D'),
            (KEY_MP_GIRDER_WEB_DEPTH,               'd_web'),
            (KEY_MP_GIRDER_TOP_FLANGE_WIDTH,        'B_top'),
            (KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH,     'B_bot'),
            (KEY_MP_GIRDER_TOP_FLANGE_THICKNESS,    't_f_top'),
            (KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS, 't_f_bot'),
            (KEY_MP_GIRDER_WEB_THICKNESS,           't_w'),
        ]

        solver = BridgeConfigurationSolver(
            carriageway_width=float(inp.get(KEY_CARRIAGEWAY_WIDTH))
        )

        def _resolve_one(full_key: str, initial_sizing_mm: float) -> None:
            raw = inp.get(full_key)
            if isinstance(raw, list) and raw:
                list_min = min(float(v) for v in raw)
                list_max = max(float(v) for v in raw)
                resolved_mm = min(list_min, list_max, initial_sizing_mm)
                inp[full_key] = math.floor(resolved_mm) / 1000.0  # floor in mm, store as m
            elif isinstance(raw, str):
                # "All" → snap initial sizing up to the next SAIL-approved thickness.
                inp[full_key] = _snap_up_to_sail(initial_sizing_mm) / 1000.0
            # float mm value — left for _convert_girder_dims_mm_to_m to divide by 1000

        for gi in range(count):
            suffix   = f".G{gi + 1}.M1"
            symmetry = inp.get(f"{KEY_MP_GIRDER_SYMMETRY}{suffix}")
            props    = solver.compute_section_properties(span=span, symmetry=symmetry)

            for base_key, prop_key in _DIM_KEYS:
                initial_sizing_mm = props[prop_key] * 1e3  # m → mm
                _resolve_one(f"{base_key}{suffix}", initial_sizing_mm)
                # Legacy scalar (un-suffixed) key, resolved first by no-index
                # consumers (e.g. SteelSection); use the first girder's sizing.
                if gi == 0:
                    _resolve_one(base_key, initial_sizing_mm)

    def _convert_girder_dims_mm_to_m(self) -> None:
        """
        Convert per-girder dimensional keys from mm back to SI metres in
        input_dict before the design pipeline consumes them.

        defaults.py stores these keys in mm for UI display. The analyser,
        designer, and all section-property helpers expect SI metres.

        Keys converted for ALL design modes (always numeric mm):
            KEY_MP_GIRDER_DEPTH, KEY_MP_GIRDER_WEB_DEPTH,
            KEY_MP_GIRDER_TOP_FLANGE_WIDTH, KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH

        Keys converted only for non-Optimized mode (numeric mm). Optimized mode
        stores "All" for these and _resolve_optimized_bounds_to_mm handles them:
            KEY_MP_GIRDER_TOP_FLANGE_THICKNESS,
            KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS,
            KEY_MP_GIRDER_WEB_THICKNESS
        """
        _DIM_KEYS_ALL_MODES = [
            KEY_MP_GIRDER_DEPTH,
            KEY_MP_GIRDER_WEB_DEPTH,
            KEY_MP_GIRDER_TOP_FLANGE_WIDTH,
            KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH,
        ]
        _DIM_KEYS_NON_OPTIMIZED = [
            KEY_MP_GIRDER_TOP_FLANGE_THICKNESS,
            KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS,
            KEY_MP_GIRDER_WEB_THICKNESS,
        ]

        inp = self.input_dict
        is_optimized = str(inp.get(KEY_DESIGN_MODE, '')).strip() == 'Optimized'
        count = self._girder_count()

        keys_to_convert = list(_DIM_KEYS_ALL_MODES)
        if not is_optimized:
            keys_to_convert.extend(_DIM_KEYS_NON_OPTIMIZED)

        def _to_m(full_key: str) -> None:
            val = inp.get(full_key)
            if val is None:
                return
            try:
                inp[full_key] = float(val) / 1000.0
            except (ValueError, TypeError):
                pass  # leave non-numeric strings ("All") for _resolve_optimized_bounds_to_mm

        for base_key in keys_to_convert:
            # The legacy scalar (un-suffixed) key must be converted too: SteelSection
            # and other no-index consumers resolve it FIRST via resolve_girder_value,
            # so leaving it in mm yields a mm×1000 unit blow-up (negative web depth).
            _to_m(base_key)
            for gi in range(count):
                _to_m(f"{base_key}.G{gi + 1}.M1")

    def _run_stage(self, stage_num: str, func, *args, **kwargs):
        # Check for user cancel before entering each stage, then emit start/complete markers
        bridge_logger.check_cancel()
        bridge_logger.stage_start(stage_num)
        result = func(*args, **kwargs)
        bridge_logger.stage_complete(stage_num)
        return result

    def _validate_inputs(self):
        """Perform strict validation on essential input dictionary keys."""
        inp = self.input_dict
        required_keys = [
            KEY_SPAN,
            KEY_TS_OVERALL_WIDTH,
            KEY_TS_NO_OF_GIRDERS,
            KEY_TS_GIRDER_SPACING,
        ]
        missing = [k for k in required_keys if k not in inp or inp[k] is None or str(inp[k]).strip() == ""]
        if missing:
            raise ValueError(f"Missing required input parameters: {', '.join(missing)}")

        span = float(inp[KEY_SPAN])
        if span <= 0:
            raise ValueError(f"Span must be strictly positive, got {span}.")
        n_girders = int(inp[KEY_TS_NO_OF_GIRDERS])
        if n_girders < 2:
            raise ValueError(f"Minimum 2 girders required, got {n_girders}.")
        spacing = float(inp[KEY_TS_GIRDER_SPACING])
        if spacing <= 0:
            raise ValueError(f"Girder spacing must be positive, got {spacing}.")

    def _solve_bridge_layout(self):
        """Snapshot input_dict into mutable output_dict for the pipeline."""
        self.output_dict = dict(self.input_dict)
        
    def _stage_grillage_setup(self):
        self._build_dtos()
        self.setup_grillage()

    def _stage_load_combinations(self):
        bridge_logger.sub_step("Running initial analysis for live load envelope...")
        dataset_initial = self.analyze()
        
        bridge_logger.sub_step("Creating governing LL load case...")
        self.create_governing_ll_load_case(dataset_initial, partial_safety_factor=1.0)
        
        bridge_logger.sub_step("Creating DL+LL combination...")
        self.create_dl_ll_combination(dl_factor=1.0, ll_factor=1.0)
        
        bridge_logger.check_cancel()
        bridge_logger.sub_step("Creating ULS and SLS combinations...")
        self.create_uls_combinations()
        
        self.create_sls_combinations()

    def _stage_cad_generation(self):
        # Validate that the CAD parameter DTO can be assembled, but do NOT build
        # the OCC solid model here: the desktop 3D viewer regenerates its own
        # copy from these parameters at render time (cad_3d.render_3d_cad), and
        # the copy previously stored on self.cad_components had no consumers —
        # it just kept a second full solid model resident until release().
        self.get_3d_cad_parameters()
        bridge_logger.sub_step("CAD parameters prepared; geometry is built by the viewer at render time.")

    def _stage_transverse_design(self):
        self.crossbracing_design_results = self._design_cross_bracing_members()
        self.output_dict["crossbracing_design_results"] = self.crossbracing_design_results
        self.end_diaphragm_design_results = self._design_end_diaphragm_members()
        self.output_dict["end_diaphragm_design_results"] = self.end_diaphragm_design_results
        return self.crossbracing_design_results

    def design(self) -> None:
        """
        Run the full analysis/design pipeline.
        Orchestrates the 14 linear stages mapping exactly to the revised architecture.
        """
        bridge_logger.analysis_start()

        # Log memory at the start of every design so per-iteration growth is visible.
        log_memory("design: START")
        # Mark the Python-allocation baseline (opt-in via OSDAGBRIDGE_MEM_TRACE=1) so release()
        # can name the top Python growers per cycle — the decisive Python-vs-native leak test.
        tracemalloc_mark_start()

        # Release the previous run's OpenSeesPy domain + cached datasets before rebuilding,
        # so a redesign (even while the input dock is still locked) starts clean.
        # set_input() has already run, so input_dict is untouched by this.
        self.memory.release()

        try:
            # Pre-stage: Unit conversions (must run before validation)
            self._resolve_optimized_bounds_to_mm()
            self._convert_girder_dims_mm_to_m()
            
            # Stage 1: Input Validation
            self._run_stage("1", self._validate_inputs)
            
            # Stage 2: Bridge Layout Solving
            self._run_stage("2", self._solve_bridge_layout)
            
            # Stage 3: Grillage Setup
            self._run_stage("3", self._stage_grillage_setup)
            
            # Stage 4A: Dead Load Application
            self._run_stage("4A", self.add_dead_loads)
            
            # Stage 4B: Live Load Application
            self._run_stage("4B", self.add_live_loads)
            
            # Stage 4C: Wind Load Application
            self._run_stage("4C", self.add_wind_loads)
            
            # Stage 4D: Temperature Load Application
            self._run_stage("4D", self.add_temperature_load)
            
            # Stage 4E: Seismic Load Application
            self._run_stage("4E", self.add_seismic_loads)
            
            # Stage 4F: Load Combination Envelope
            self._run_stage("4F", self._stage_load_combinations)
            
            # Stage 4G: Structural Analysis
            dataset = self._run_stage("4G", self._reanalyze_with_dedup)
            dataset = self.create_envelope_load_case(dataset)
            dataset = self._drop_moving_increment_cases(dataset)

            # Drop the raw ospgrillage per-load-case records as soon as the
            # deduplicated dataset is cached: everything downstream (design checks,
            # get_result_data, plots, output dock) reads that cached dataset, so
            # holding the records through stages 5-8 only inflates the peak RSS.
            self.memory.clear_intermediate_results()
            
            # Print Summary
            inp = self.input_dict
            print(
                f"\n{'-'*60}\n"
                f"  PLATE GIRDER BRIDGE - DESIGN SUMMARY\n"
                f"{'-'*60}\n"
                f"  Span                  : {float(inp[KEY_SPAN]):.1f} m\n"
                f"  Overall width         : {inp[KEY_TS_OVERALL_WIDTH]:.3f} m\n"
                f"  No. of girders        : {inp[KEY_TS_NO_OF_GIRDERS]}\n"
                f"  Girder spacing        : {inp[KEY_TS_GIRDER_SPACING] * 1e3:.1f} mm\n"
                f"  Deck overhang         : {inp[KEY_TS_DECK_OVERHANG] * 1e3:.1f} mm\n"
            )
            # Per-girder cross-section block (each girder may differ).
            for gi in range(self._girder_count()):
                v = lambda key: self._girder_value(key, gi)
                print(
                    f"{'-'*60}\n"
                    f"  GIRDER G{gi + 1} CROSS-SECTION (mm) / PROPERTIES (SI)\n"
                    f"{'-'*60}\n"
                    f"  Total depth      D    : {v(KEY_MP_GIRDER_DEPTH)                   * 1e3:.1f}\n"
                    f"  Web depth        d_w  : {v(KEY_MP_GIRDER_WEB_DEPTH)               * 1e3:.1f}\n"
                    f"  Web thickness    t_w  : {v(KEY_MP_GIRDER_WEB_THICKNESS)           * 1e3:.1f}\n"
                    f"  Top flange width B_ft : {v(KEY_MP_GIRDER_TOP_FLANGE_WIDTH)        * 1e3:.1f}\n"
                    f"  Top flange thk   T_ft : {v(KEY_MP_GIRDER_TOP_FLANGE_THICKNESS)    * 1e3:.1f}\n"
                    f"  Bot flange width B_fb : {v(KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH)     * 1e3:.1f}\n"
                    f"  Bot flange thk   T_fb : {v(KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS) * 1e3:.1f}\n"
                    f"  Area   A  : {v(KEY_MP_GIRDER_SECTIONAL_AREA):.6f} m^2\n"
                    f"  I_z       : {v(KEY_MP_GIRDER_SECTIONAL_IZ):.6f} m^4\n"
                    f"  I_y       : {v(KEY_MP_GIRDER_SECTIONAL_IY):.6f} m^4\n"
                    f"  I_t (J)   : {v(KEY_MP_GIRDER_TORSION_CONSTANT_IT):.6f} m^3\n"
                    f"{'-'*60}"
                )

            # Stage 5: Girder Design Checks
            self._run_stage("5", self._run_dcr_checks, dataset)
            self.result_data = self.grillage_model.get_result_data()

            if self.dump_json:
                from osdagbridge.core.bridge_types.plate_girder.results_data import dump_full_data
                dump_full_data(
                    self.grillage_model.model,
                    edge_dist=self.grillage_model.edge_dist or 0.0,
                    # Use the envelope-augmented dataset so the Envelope ULS / Envelope
                    # SLS pseudo load cases appear in the dump; falls back to
                    # model.get_results() if absent.
                    dataset=getattr(self.grillage_model, "_deduplicated_results", None),
                )

            # Stage 6: Deck Slab Design
            # self.deck_design_results = self._run_stage("6", self.design_deck_slab)
            
            # Stage 7: Transverse Member Design
            self.crossbracing_design_results = self._run_stage("7", self._stage_transverse_design)
            
            self.bridge_component_solver()
            self.compute_load_effects_cache()
            for _gi, _vals in (self._deflections_cache or {}).items():
                _live = _vals.get("live_mm")
                _total = _vals.get("total_mm")
                if _live is not None:
                    self.output_dict[f"{KEY_SD_DEFL_LIVE}.{_gi}"] = round(float(_live), 3)
                if _total is not None:
                    self.output_dict[f"{KEY_SD_DEFL_TOTAL}.{_gi}"] = round(float(_total), 3)
            
            # Stage 8: 3D CAD & Drawing Generation
            self._run_stage("8", self._stage_cad_generation)

            # Freeze output_dict — no further writes allowed after this point
            self.output_dict = types.MappingProxyType(self.output_dict)
            # Log memory after the design completes so growth per iteration is visible.
            log_memory("design: COMPLETE")
            bridge_logger.analysis_complete()

        except Exception as e:
            bridge_logger.analysis_failed(str(e))
            raise

    def reset(self) -> None:
        # Release all heavy analysis memory (unlock / app-close entry point).
        self.memory.release()

    def _export_cad_figures(self, cad_generator) -> dict:
        """
        Export 4 CAD views to the fixed internal Images folder.
        Returns { ReportFigures_attr: absolute_path } for each view.
        Returns {} on any failure. Never raises.
        """
        import os
        import logging
        _log = logging.getLogger(__name__)

        # ── Resolve save path: core/data/ResourceFiles/Images/ ───────
        resource_files_dir = os.path.normpath(os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '..', '..', '..', 'core', 'data', 'ResourceFiles'
        ))
        figures_dir = os.path.join(resource_files_dir, 'Images')
        if not os.path.exists(figures_dir):
            os.makedirs(figures_dir)

        if not cad_generator:
            return {}

        core = cad_generator

        # ── Verify model has been generated ───────────────────────────
        if not getattr(core, 'model_data', None):
            _log.warning(
                "_export_cad_figures: model_data is empty — "
                "run design first")
            return {}

        # ── Create headless Viewer3d — no window, no auto-export ─────
        try:
            from OCC.Display.OCCViewer import Viewer3d
            off_display = Viewer3d()
            off_display.Create()          # NO arguments — avoids TypeError
            off_display.SetModeShaded()
        except Exception as exc:
            _log.warning(
                "_export_cad_figures: Viewer3d init failed: "
                "%s — export skipped", exc)
            return {}

        if not hasattr(off_display, 'ExportToImage'):
            _log.warning(
                "_export_cad_figures: off_display has no ExportToImage "
                "— export skipped")
            return {}

        # ── Stub cad_widget for off-screen rendering ─────────────────
        # osdag_display_shape() calls canvas.model_ais_objects — provide it.
        class _OffscreenCanvas:
            def __init__(self):
                self.model_ais_objects = {}
        off_canvas = _OffscreenCanvas()

        # ── Save originals BEFORE touching anything ──────────────────
        original_display    = getattr(core, 'display', None)
        original_cad_widget = getattr(core, 'cad_widget', None)
        original_component  = getattr(core, 'component', None)

        figure_paths = {}

        # Freeze GC around this guard-less headless viewer's render/teardown (Shiboken-GC segfault guard).
        import gc
        _gc_was_enabled = gc.isenabled()
        gc.disable()

        try:
            # ── Substitute + render all components onto off-screen display
            core.display    = off_display
            core.cad_widget = off_canvas

            for component in ["Girder", "Stiffener", "Cross Bracing",
                              "Deck", "Crash Barrier", "Railing", "Median"]:
                try:
                    if hasattr(core, 'display_3dModel'):
                        core.display_3dModel(component)
                except Exception as exc:
                    _log.debug("component %s skipped: %s", component, exc)

            off_display.FitAll()

            # View 1 — Isometric / 3D
            try:
                off_display.set_bg_gradient_color(
                    [235, 235, 235], [195, 195, 195])
                p = os.path.join(figures_dir, 'girder_3d.png')
                off_display.ExportToImage(p)
                if os.path.exists(p):
                    figure_paths['girder_3d'] = os.path.abspath(p)
            except Exception as exc:
                _log.warning("3D view export failed: %s", exc)

            # View 2 — Front
            try:
                off_display.View_Front()
                off_display.FitAll()
                off_display.set_bg_gradient_color(
                    [235, 235, 235], [195, 195, 195])
                p = os.path.join(figures_dir, 'girder_front.png')
                off_display.ExportToImage(p)
                if os.path.exists(p):
                    figure_paths['girder_front'] = os.path.abspath(p)
            except Exception as exc:
                _log.warning("Front view export failed: %s", exc)

            # View 3 — Top
            try:
                off_display.View_Top()
                off_display.FitAll()
                off_display.set_bg_gradient_color(
                    [235, 235, 235], [195, 195, 195])
                p = os.path.join(figures_dir, 'girder_top.png')
                off_display.ExportToImage(p)
                if os.path.exists(p):
                    figure_paths['girder_top'] = os.path.abspath(p)
            except Exception as exc:
                _log.warning("Top view export failed: %s", exc)

            # View 4 — Side (Right)
            try:
                off_display.View_Right()
                off_display.FitAll()
                off_display.set_bg_gradient_color(
                    [235, 235, 235], [195, 195, 195])
                p = os.path.join(figures_dir, 'girder_end.png')
                off_display.ExportToImage(p)
                if os.path.exists(p):
                    figure_paths['girder_end'] = os.path.abspath(p)
            except Exception as exc:
                _log.warning("Side view export failed: %s", exc)

        finally:
            # ── CRITICAL: isolation cleanup — ALWAYS runs ────────────
            # Ordered teardown: Remove each AIS's C++ ref before EraseAll, then restore GC.
            try:
                ctx = off_display.Context
                for ais_list in off_canvas.model_ais_objects.values():
                    items = ais_list if isinstance(ais_list, (list, tuple)) else [ais_list]
                    for ais in items:
                        try:
                            if ctx.IsDisplayed(ais):
                                ctx.Remove(ais, False)
                        except Exception:
                            pass
                off_canvas.model_ais_objects.clear()
            except Exception:
                pass
            try:
                off_display.EraseAll()
            except Exception:
                pass
            core.display    = original_display
            core.cad_widget = original_cad_widget
            core.component  = original_component
            if _gc_was_enabled:
                gc.enable()

        _log.info(
            "_export_cad_figures: exported %d view(s) to %s",
            len(figure_paths), figures_dir)
        return figure_paths


    def generate_design_report(self, request, cad_generator, is_preview=False):
        """Compile the final PDF design report."""
        from osdagbridge.core.reports.report_generator import build_report_payload, generate_report

        report_inputs = self.input_dict.copy()
        output_dict   = dict(self.output_dict)  # MappingProxyType → dict

        # ── Chapter 4: analysis summary for Tables ──────────────────
        lc_sum  = getattr(self, '_lc_summary',       None)
        rxn_sum = getattr(self, '_reaction_summary',  None)
        if lc_sum is not None or rxn_sum is not None:
            output_dict['analysis_summary'] = {
                'load_cases': lc_sum  or {},
                'reactions':  rxn_sum or {},
            }

        payload = build_report_payload(request, report_inputs, output_dict)

        # Collect figure bytes into payload.figure_data — no disk writes here
        figure_data = {}
        if isinstance(cad_generator, dict):
            figure_data.update(cad_generator.get('figure_data', {}))

        payload.figure_data = figure_data  # handed off; generate_report clears it after writing

        return generate_report(payload, request)

    def _build_dtos(self) -> None:
        """Construct GrillageGeometry and DeckLayoutProperties DTOs from solved results."""
        inp = self.input_dict
        span = float(inp[KEY_SPAN])
        # n_t: transverse grid lines — span divided by cross-bracing spacing, rounded to nearest odd integer with minimum of 3 (1 at each end + at least 1 internal for bracing)
        n_t = max(3, (int(round(span / (DEFAULT_CROSS_BRACING_SPACING)*2) + 1)))

        deck_overhang = float(inp[KEY_TS_DECK_OVERHANG])
        # When there is an overhang, the two edge beams add 2 extra longitudinal
        # grid lines on top of the structural girder count.
        n_l = int(inp[KEY_TS_NO_OF_GIRDERS]) + (2 if deck_overhang > 0 else 0)

        self.grillage_geometry = GrillageGeometry(
            L=span,
            n_l=n_l,
            n_t=n_t,
            edge_dist=deck_overhang,
            ext_to_int_dist=float(inp[KEY_TS_GIRDER_SPACING]),
            angle=float(self.input_dict.get(KEY_SKEW_ANGLE) or 0.0),
        )

        self.deck_layout = DeckLayoutProperties(
            carriageway_width=float(inp[KEY_CARRIAGEWAY_WIDTH]),
            crash_barrier_width=float(DEFAULT_CRASH_BARRIER_WIDTH),
            footpath_width=float(inp[KEY_TS_FOOTPATH_WIDTH]),
            railing_width=float(inp[KEY_RL_WIDTH]),
            median_width=float(inp[KEY_MD_WIDTH]),
            n_footpaths=int(inp[KEY_TS_NO_OF_FOOTPATHS]),
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Bridge component solver
    # ─────────────────────────────────────────────────────────────────────────

    def bridge_component_solver(self) -> None:
        """
        Single entry-point that computes all derived bridge-component
        geometry values and writes them into ``self.output_dict``.

        **How to add a new component in the future**

        1. Create a private ``_solve_<component>(self)`` method below.
        2. Add **one line** calling it here.

        ``bridge_component_solver()`` is called only **once** from the
        design pipeline; each private sub-method owns its own slice of
        ``output_dict`` and can be developed and tested independently.

        Current components
        ------------------
        * Shear studs  --> ``_solve_shear_studs()``
        """
        self._solve_shear_studs()

        # ── Future components: add one line per component here ────────────────
        # self._solve_deck()
        # self._solve_bearings()
        # self._solve_stiffeners()
        # self._solve_cross_bracing()

    def _solve_shear_studs(self) -> None:
        """
        Compute derived shear-stud geometry values and update ``output_dict``.

        Keys written
        ------------
        KEY_DS_STUD_HEAD_DIAMETER
            Minimum stud head diameter = 1.5 x d_stud
            [IRC 22:2015 - Cl. 606.6 - Detailing of Shear Connectors]

        KEY_DS_STUD_HEAD_HEIGHT
            Minimum stud head height = 0.667 x d_stud
            [IS 3935:1966 - Composite Construction]

        Raises
        ------
        ValueError
            If ``KEY_DS_STUD_DIAMETER`` is missing or cannot be parsed as float.
        """
        # KEY_DS_STUD_DIAMETER is always populated by _update_design_options_defaults()
        d_stud_mm = float(self.output_dict[KEY_DS_STUD_DIAMETER])

        # ── Compute geometry values ───────────────────────────────────────────
        # Minimum head diameter  [IRC 22:2015 - Cl. 606.6]
        head_d_mm = min_stud_head_diameter(d_stud_mm)

        # Minimum head height    [IS 3935:1966]
        head_h_mm = min_stud_head_height(d_stud_mm)

        # ── Write results into output_dict ────────────────────────────────────
        self.output_dict.update({
            KEY_DS_STUD_HEAD_DIAMETER: head_d_mm,
            KEY_DS_STUD_HEAD_HEIGHT:   head_h_mm,
        })

    # ─────────────────────────────────────────────────────────────────────────
    # Grillage model setup
    # ─────────────────────────────────────────────────────────────────────────

    def setup_grillage(self) -> None:
        """
        Initialise and build the BridgeGrillageModel in order:
          1. set_geometry   — grillage dimensions and cross-section layout
          2. create_sections — section properties for all member types
          3. create_material — steel material from the DB-backed girder selection
          4. assign_members  — pair sections with material to create member objects
          5. create_model    — build and run the OpenSees grillage model

        Must be called after design() has populated grillage_geometry,
        deck_layout, and section_props.
        """
        self.grillage_model.set_geometry(self.grillage_geometry, self.deck_layout)
        # Build one SectionProperties per main girder. When the input dict carries
        # per-girder dynamic keys (``<base>.G{i}.M1``) the girders may differ;
        # otherwise every girder falls back to the shared scalar section.
        n_girders = self._girder_count()
        girder_sections = [self._girder_section(i) for i in range(n_girders)]
        self.grillage_model.create_sections(
            girder_sections=girder_sections,
            edge_longitudinal=self._girder_section(),
            transverse=self._transverse_section(),
            end_transverse=self._end_transverse_section(),
        )
        self.material_props = self._build_material_props()
        self.grillage_model.create_material(self.material_props)
        self.grillage_model.assign_members()
        self.grillage_model.create_model()

    def _lookup_material(self, material_name: str, property: str) -> float:
        """
        Query the Osdag SQLite database for the specified property of the given
        material name.  Returns the property value in its respective units.  Falls back to the default value
        if the DB is missing or the material is not found.
        """
        if not _DB_PATH.exists():
            raise LookupError(f"Material database not found at {_DB_PATH} in PlateGirderBridge._lookup_material")

        # Choose the table: rebar (Fe-grades), structural steel (E-grades), or concrete
        if material_name.startswith('Fe'):
            table = 'Rebar_Grade_Properties'
        elif material_name[0] == 'E':
            table = 'Steel_Grade_Properties'
        else:
            table = 'Concrete_Grade_Properties'

        try:
            con = sqlite3.connect(_DB_PATH)
            cur = con.cursor()
            cur.execute(
                f'SELECT "{property}" FROM {table} WHERE "Grade" = ?',
                (material_name,),
            )
            row = cur.fetchone()
            con.close()
            if row:
                if property == "Modulus of Elasticity":     # Elastic modulus (Pa)
                    return float(row[0]) * GPa
                elif property == "Poisson's Ratio":         # Poisson's ratio (unitless)
                    return float(row[0])
                elif property == "Density":                 # Unit weight (N/m³)
                    return float(row[0]) * N / m ** 3
                elif property == "Yield Strength":          # Yield strength (Pa)
                    return float(row[0]) * MPa              # DB stores MPa as integer → convert to Pa
                elif property == "Ultimate Tensile Strength":
                    return float(row[0]) * MPa
                elif property in ("fck", "fctm", "Ecm", "fy", "fu", "Es"):  # Concrete (MPa/GPa) and rebar (MPa) properties — returned as plain numbers
                    return float(row[0])
                else:
                    raise SyntaxError(f"Unknown property '{property}' requested in table '{table}' in PlateGirderBridge._lookup_material")

        except sqlite3.Error:
            raise LookupError(f"Error querying material database in PlateGirderBridge._lookup_material: {sqlite3.Error}")

    def _build_material_props(self) -> MaterialProperties:
        """Build a MaterialProperties from the selected girder material in input_dict.
        
        For DB grades (e.g. 'E 250A') properties are looked up from the SQLite database.
        For custom grades (those not found in the DB) the sub-values already stored in
        input_dict (material.girder.e, .fy, .fu, .poisson, .g) are used directly.
        This prevents a NoneType crash when the user has entered a custom material.
        """
        _DEFAULT_DENSITY = 78500.0  # N/m³ — fallback when not available in DB

        # ── Steel (Girder) ────────────────────────────────────────────────────
        steel_grade = str(self.input_dict.get(KEY_GIRDER, "")).strip()
        e = self._lookup_material(steel_grade, "Modulus of Elasticity")
        if e is None:
            # Custom grade — read from the material sub-keys populated by the UI
            raw_e = self.input_dict.get(KEY_MATERIAL_GIRDER_E)
            e = float(raw_e) * GPa if raw_e not in (None, "") else _STEEL_E0

        v = self._lookup_material(steel_grade, "Poisson's Ratio")
        if v is None:
            raw_v = self.input_dict.get(KEY_MATERIAL_GIRDER_POISSON)
            v = float(raw_v) if raw_v not in (None, "") else 0.3

        rho = self._lookup_material(steel_grade, "Density")
        if rho is None:
            rho = _DEFAULT_DENSITY

        fy = self._lookup_material(steel_grade, "Yield Strength")
        if fy is None:
            raw_fy = self.input_dict.get(KEY_MATERIAL_GIRDER_FY)
            fy = float(raw_fy) * MPa if raw_fy not in (None, "") else _STEEL_FY_DEFAULT

        fu = self._lookup_material(steel_grade, "Ultimate Tensile Strength")
        if fu is None:
            raw_fu = self.input_dict.get(KEY_MATERIAL_GIRDER_FU)
            fu = float(raw_fu) * MPa if raw_fu not in (None, "") else fy * 1.25

        steel_prop = SteelProperties(
            grade=steel_grade,
            E=e,
            v=v,
            rho=rho,
            Fy=fy,
            Fu=fu,
            E0=_STEEL_E0,
            b=_STEEL_B,
        )

        # ── Concrete (Deck) ───────────────────────────────────────────────────
        concrete_grade = str(self.input_dict.get(KEY_DECK_CONCRETE_GRADE_BASIC, "")).strip()
        fck = self._lookup_material(concrete_grade, "fck")
        if fck is None:
            raw_fck = self.input_dict.get(KEY_MATERIAL_DECK_FCK)
            fck = float(raw_fck) if raw_fck not in (None, "") else 25.0

        fctm = self._lookup_material(concrete_grade, "fctm")
        if fctm is None:
            raw_fctm = self.input_dict.get(KEY_MATERIAL_DECK_FCTM)
            fctm = float(raw_fctm) if raw_fctm not in (None, "") else 2.2

        Ecm = self._lookup_material(concrete_grade, "Ecm")
        if Ecm is None:
            raw_ecm = self.input_dict.get(KEY_MATERIAL_DECK_ECM)
            Ecm = float(raw_ecm) if raw_ecm not in (None, "") else 30.0

        concrete_prop = ConcreteProperties(
            grade=concrete_grade,
            fck=fck,
            fctm=fctm,
            Ecm=Ecm,
        )

        return MaterialProperties(
            steel_prop=steel_prop,
            concrete_prop=concrete_prop,
        )

    def _girder_count(self) -> int:
        """Number of structural main girders (excludes overhang edge beams)."""
        try:
            return max(1, int(self.input_dict[KEY_TS_NO_OF_GIRDERS]))
        except (KeyError, TypeError, ValueError):
            return 1

    def _girder_value(self, base_key: str, i: int | None = None):
        """
        Read a girder property from ``input_dict`` (see ``resolve_girder_value``
        for the per-girder/scalar resolution order).
        """
        return resolve_girder_value(self.input_dict, base_key, i)

    def _girder_section(self, i: int | None = None) -> SectionProperties:
        """
        Build a SectionProperties for main girder ``i`` (0-based).

        ``i=None`` builds from the representative (first) girder — used for edge
        beams and as the uniform fallback.
        """
        g = lambda key: self._girder_value(key, i)
        Az = g(KEY_MP_GIRDER_WEB_DEPTH) * g(KEY_MP_GIRDER_WEB_THICKNESS)
        Ay = 2 * g(KEY_MP_GIRDER_TOP_FLANGE_WIDTH) * g(KEY_MP_GIRDER_TOP_FLANGE_THICKNESS)
        return SectionProperties(
            A=g(KEY_MP_GIRDER_SECTIONAL_AREA),
            J=g(KEY_MP_GIRDER_TORSION_CONSTANT_IT),
            Iz=g(KEY_MP_GIRDER_SECTIONAL_IZ),
            Iy=g(KEY_MP_GIRDER_SECTIONAL_IY),
            Az=Az,
            Ay=Ay,
        )

    def _transverse_section(self) -> SectionProperties:
        """Build a SectionProperties for the transverse deck slab (half-depth, unit width)."""
        g = lambda key: self._girder_value(key)  # representative (first) girder
        t  = g(KEY_MP_GIRDER_DEPTH) / 2
        Az = t * g(KEY_MP_GIRDER_WEB_THICKNESS)
        return SectionProperties(
            A=g(KEY_MP_GIRDER_SECTIONAL_AREA) / 2,
            J=g(KEY_MP_GIRDER_TORSION_CONSTANT_IT) / 2,
            Iz=g(KEY_MP_GIRDER_SECTIONAL_IZ) / 2,
            Iy=g(KEY_MP_GIRDER_SECTIONAL_IY) / 2,
            Az=Az,
            Ay=Az,
        )

    def _end_transverse_section(self) -> SectionProperties:
        """Build a SectionProperties for the end transverse slab (quarter-depth)."""
        g = lambda key: self._girder_value(key)  # representative (first) girder
        Az = g(KEY_MP_GIRDER_WEB_DEPTH) / 2 * g(KEY_MP_GIRDER_WEB_THICKNESS)
        Ay = g(KEY_MP_GIRDER_TOP_FLANGE_WIDTH) * g(KEY_MP_GIRDER_TOP_FLANGE_THICKNESS)
        return SectionProperties(
            A=g(KEY_MP_GIRDER_SECTIONAL_AREA) / 4,
            J=g(KEY_MP_GIRDER_TORSION_CONSTANT_IT) / 4,
            Iz=g(KEY_MP_GIRDER_SECTIONAL_IZ) / 4,
            Iy=g(KEY_MP_GIRDER_SECTIONAL_IY) / 4,
            Az=Az,
            Ay=Ay,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Dead loads — permanent loads applied after the grillage model is built
    # ─────────────────────────────────────────────────────────────────────────

    def add_dead_loads(self) -> None:
        """
        Apply all permanent dead loads to the grillage model in order:
          1. Girder self weight     — line load along each longitudinal member
          2. Deck slab              — patch load over the full deck area
          3. Wearing course         — patch load over the carriageway area
          4. Footpath               — patch load on footpath strips (skipped if none)
          5. Crash barrier          — line load at each barrier centreline (skipped if none)
          6. Railing                — line load at each railing centreline (skipped if none)
          7. Median                 — line load at median centreline (skipped if none)
          8. DL combination         — combines all above into a single "DL" load case

        Must be called after setup_grillage() has built and registered the model.
        """
        deck_t_m = deck_thickness_from_inputs(self.input_dict, _DEFAULT_DECK_THICKNESS_MM)
        wc_t_m = float(self.input_dict[KEY_WC_THICKNESS]) / 1000.0
        wc_rho  = float(self.input_dict[KEY_WC_DENSITY])
        barrier_load_kN_m = crash_barrier_load_from_inputs(self.input_dict)
        railing_load_kN_m = railing_load_from_inputs(self.input_dict)

        model = self.grillage_model
        model.create_self_weight_load()
        model.create_deck_load(slab_thickness_m=deck_t_m)
        model.create_wearing_course_load(thickness_m=wc_t_m, density_kN_m3=wc_rho, partial_safety_factor=1.0)
        model.create_footpath_load()
        model.create_crash_barrier_load(barrier_load_kN_per_m=barrier_load_kN_m)
        model.create_railing_load(railing_load_kN_per_m=railing_load_kN_m)
        model.create_median_load()
        model.create_dead_load_combination(partial_safety_factor=1.0)

    # ─────────────────────────────────────────────────────────────────────────
    # Live loads — vehicle and moving loads applied after the grillage model
    # ─────────────────────────────────────────────────────────────────────────

    def add_live_loads(self) -> None:
        """
        Apply all live loads to the grillage model in order:
          1. Vehicle load cases — static placements per IRC:6 Table 6A
          2. Moving vehicle load cases — moving paths for each vehicle

        Must be called after setup_grillage() has built and registered the model.
        """
        model = self.grillage_model
        model.add_vehicle_load_cases_from_combinations()
        bridge_logger.check_cancel()
        
        model.create_moving_vehicle_load_cases()

    # ─────────────────────────────────────────────────────────────────────────
    # Wind loads — applied after dead and live loads, before analysis
    # ─────────────────────────────────────────────────────────────────────────

    def add_wind_loads(self) -> None:
        """
        Apply wind loads to the grillage model per IRC:6-2017 Cl.209.3.3–209.3.5.

        Wind parameters are read from ``self.input_dict`` (the
        Additional Inputs dialog).  Any parameter not yet supplied falls back
        to a sensible default so the method is always safe to call.

        Load cases created (delegated to BridgeGrillageModel.create_wind_load):
          - ``"WL Transverse"``   — FT line load on the two exterior girders
          - ``"WL Longitudinal"`` — FL = 0.25 FT patch load over the full deck
          - ``"WL Uplift"``       — Pz × G × CL patch load (upward) on the deck
          - ``"1.0 WL"``          — combined load case with partial_safety_factor = 1.0
        """
        ai  = self.additional_inputs
        inp = self.input_dict

        # ── Wind speed / terrain ─────────────────────────────────────────
        basic_wind_speed = float(ai.get("basic_wind_speed") or 33.0)
        if basic_wind_speed == 0.0:
            bridge_logger.info("Wind load absent (speed=0); skipping.")
            return

        height_for_pz = float(ai.get("avg_exposed_height") or 10.0)
        terrain_raw   = str(ai.get("terrain_type") or "Plain Terrain")
        terrain       = "plain" if "plain" in terrain_raw.lower() else "obstructed"

        # ── Exposed height components ────────────────────────────────────
        railing_height       = float(ai.get("railing_height")       or 0.0)
        crash_barrier_height = float(ai.get("crash_barrier_height") or 0.0)
        deck_t_m             = deck_thickness_from_inputs(ai, _DEFAULT_DECK_THICKNESS_MM)

        # ── Girder geometry for CD ───────────────────────────────────────
        # Use the governing (deepest) girder for the windward drag depth so a
        # mix of per-girder depths still yields a conservative transverse force.
        n_girders = inp[KEY_TS_NO_OF_GIRDERS]
        d_depth   = max(
            self._girder_value(KEY_MP_GIRDER_DEPTH, i) for i in range(self._girder_count())
        )
        c_spacing = inp[KEY_TS_GIRDER_SPACING]

        self.grillage_model.create_wind_load(
            railing_height=railing_height,
            crash_barrier_height=crash_barrier_height,
            deck_thickness=deck_t_m,
            height_for_pz=height_for_pz,
            terrain=terrain,
            basic_wind_speed=basic_wind_speed,
            girder_section="plate",
            number_of_girders=n_girders,
            c_spacing=c_spacing,
            d_depth=d_depth,
            partial_safety_factor=1.0,
        )

    # ============================================================
    #   Temperature Load Analysis  IRC:6-2017 Cl.215
    # ============================================================

    def analyse_uniform_temperature(
        self,
        max_shade_temp: float,
        min_shade_temp: float,
        girders: list[dict],
        structural_type: str = 'metallic',
        snowbound: bool = False,
        k_fixed: float = 1_000_000.0,
        k_free: float = 100.0,
        s_girder: float | None = None,
        h_diaphragm: float | None = None,
    ) -> list[dict]:
        """
        Restrained axial force, bearing movement and end-diaphragm shear under
        uniform temperature change per IRC:6-2017 Cl.215.2.

        Analysis is performed per girder; girders may have different E_s and A_s.

        Parameters
        ----------
        max_shade_temp : float
            Maximum shade air temperature (°C) from IRC:6-2017 Annexure F / Table 15.
        min_shade_temp : float
            Minimum shade air temperature (°C).
        girders : list of dict
            One entry per girder, each containing:
              'E_s' (float, MPa) — steel elastic modulus
              'A_s' (float, m²)  — steel girder cross-section area
        structural_type : str
            'metallic' (default) or 'other' — controls effective temperature
            derivation per IRC:6-2017 Cl.215.2.
        snowbound : bool
            True if the location is snowbound (metallic structures only).
        k_fixed : float
            Longitudinal stiffness of the fixed bearing (kN/m).
            Default: 1 000 000 kN/m (virtually rigid pot bearing).
        k_free : float
            Longitudinal stiffness of the expansion bearing (kN/m).
            Default: 100 kN/m.
        s_girder : float, optional
            Centre-to-centre girder spacing (m) — for end-diaphragm shear (Step 5).
        h_diaphragm : float, optional
            Height of the end diaphragm (m) — for end-diaphragm shear (Step 5).

        Returns
        -------
        list of dict
            One result dict per girder.  Key output quantities:

            delta_free_rise_m   (m)    free thermal expansion
            delta_free_fall_m   (m)    free thermal contraction
            k_girder_kN_m       (kN/m) girder axial stiffness
            N_temp_rise_kN      (kN)   restrained axial force (rise)
            N_temp_fall_kN      (kN)   restrained axial force (fall)
            bearing_movement_m  (m)    governing bearing design movement
            V_diaphragm_rise_kN (kN)   end-diaphragm transverse shear (rise)
            V_diaphragm_fall_kN (kN)   end-diaphragm transverse shear (fall)
        """
        L = self.L   # span length (m)

        # ── IRC:6-2017 Cl.215.2 — effective bridge temperature range ──────────
        temp_range = IRC6_2017.cl_215_2_effective_bridge_temperature(
            max_temp=max_shade_temp,
            min_temp=min_shade_temp,
            structural_type=structural_type,
            snowbound=snowbound,
        )
        T_max  = temp_range['T_max']            # effective max bridge temperature (°C)
        T_min  = temp_range['T_min']            # effective min bridge temperature (°C)
        T_mean = (T_max + T_min) / 2.0          # mean construction temperature (°C)

        # ── IRC:6-2017 Cl.215.2 — thermal expansion coefficient ──────────────
        alpha = IRC6_2017.cl_215_4_material_properties()['alpha']   # /°C

        # Temperature differentials from mean construction temperature
        delta_T_rise = T_max - T_mean   # °C  rise above mean
        delta_T_fall = T_mean - T_min   # °C  fall below mean

        print(
            f"Uniform temperature (IRC:6-2017 Cl.215.2): "
            f"T_max={T_max:.1f}°C  T_min={T_min:.1f}°C  T_mean={T_mean:.1f}°C  "
            f"alpha={alpha:.2e}/°C  "
            f"delta_T_rise={delta_T_rise:.1f}°C  delta_T_fall={delta_T_fall:.1f}°C"
        )

        results = []

        for idx, girder in enumerate(girders):
            E_s = girder['E_s']   # steel modulus (MPa)
            A_s = girder['A_s']   # steel girder cross-section area (m²)

            # Step 1 — Free thermal expansion / contraction  [m]  — IRC:6-2017 Cl.215.2
            #   delta = alpha × delta_T × L
            delta_free_rise = alpha * delta_T_rise * L   # m
            delta_free_fall = alpha * delta_T_fall * L   # m

            # Step 2 — Girder axial stiffness  [kN/m]
            #   E_s [MPa] × 1000 → [kN/m²];  × A_s [m²] / L [m]  →  kN/m
            k_girder = (E_s * 1000.0 * A_s) / L   # kN/m

            # Step 3 — Restrained axial force via spring compatibility  [kN]
            #   Girder (k_g) + fixed bearing (k_f) + expansion bearing (k_e) in series
            #   k_eff = k_g × k_f × k_e / (k_g×k_f + k_g×k_e + k_f×k_e)
            denom       = (k_girder * k_fixed
                           + k_girder * k_free
                           + k_fixed  * k_free)
            k_eff       = (k_girder * k_fixed * k_free) / denom   # kN/m
            N_temp_rise = k_eff * delta_free_rise   # kN  axial compression on rise
            N_temp_fall = k_eff * delta_free_fall   # kN  axial tension on fall

            # Step 4 — Bearing design movement  [m]
            #   Expansion-end displacement u = N / k_free
            u_free_end_rise  = N_temp_rise / k_free                     # m
            u_free_end_fall  = N_temp_fall / k_free                     # m
            bearing_movement = max(u_free_end_rise, u_free_end_fall)    # m  governing

            # Step 5 — End-diaphragm transverse racking shear  [kN]  (approximate)
            #   V ≈ N_temp × (s_girder / h_diaphragm)
            #   NOTE: approximate 2D frame analogy; use 3D FEM for exact value.
            V_rise = V_fall = None
            if s_girder is not None and h_diaphragm is not None:
                V_rise = N_temp_rise * (s_girder / h_diaphragm)   # kN
                V_fall = N_temp_fall * (s_girder / h_diaphragm)   # kN

            print(
                f"  Girder {idx}: k_girder={k_girder:.0f} kN/m  "
                f"N_rise={N_temp_rise:.2f} kN  N_fall={N_temp_fall:.2f} kN  "
                f"bearing_mov={bearing_movement * 1000:.2f} mm"
            )

            results.append({
                # Identification
                'girder_index':        idx,
                'E_s_MPa':             E_s,
                'A_s_m2':              A_s,
                'clause':              temp_range['clause'],
                # Effective temperatures (°C)
                'T_max':               T_max,
                'T_min':               T_min,
                'T_mean':              T_mean,
                'delta_T_rise':        delta_T_rise,
                'delta_T_fall':        delta_T_fall,
                # Step 1 — free movement (m)
                'delta_free_rise_m':   delta_free_rise,
                'delta_free_fall_m':   delta_free_fall,
                # Step 2 — stiffnesses (kN/m)
                'k_girder_kN_m':       k_girder,
                'k_fixed_kN_m':        k_fixed,
                'k_free_kN_m':         k_free,
                # Step 3 — axial forces (kN)
                'N_temp_rise_kN':      N_temp_rise,
                'N_temp_fall_kN':      N_temp_fall,
                # Step 4 — bearing movement (m)
                'u_free_end_rise_m':   u_free_end_rise,
                'u_free_end_fall_m':   u_free_end_fall,
                'bearing_movement_m':  bearing_movement,
                # Step 5 — end-diaphragm shear (kN); None if geometry not supplied
                'V_diaphragm_rise_kN': V_rise,
                'V_diaphragm_fall_kN': V_fall,
                'diaphragm_note': (
                    'Approximate (3D FEM for exact). '
                    'V = N_temp × (s_girder / h_diaphragm).'
                ) if V_rise is not None else (
                    'Not computed: s_girder or h_diaphragm not provided.'
                ),
            })

        self.temp_uniform_results = results
        return results

    def analyse_temperature_gradient(
        self,
        parts: list[dict],
        h_slab: float,
        E_s: float,
        T_profile_rise: list[tuple] | None = None,
        T_profile_fall: list[tuple] | None = None,
        dy: float = 0.001,
    ) -> dict:
        """
        Eigen stresses in the composite cross-section under the IRC:6-2017 Cl.215.4
        non-uniform temperature gradient.

        Stresses are self-equilibrating and exist even in a simply supported beam.
        For a simply supported span, secondary (hyperstatic) reactions are zero;
        the gradient causes free curvature only.

        Parameters
        ----------
        parts : list of dict
            Rectangular section components from top to bottom, each containing:
              'label'  (str)   : e.g. 'slab', 'top_flange', 'web', 'bot_flange'
              'b'      (float) : width (m)
              'h'      (float) : height / thickness (m)
              'E'      (float) : elastic modulus (MPa) — E_c for slab, E_s for steel
              'y_top'  (float) : depth of top face from top of composite section (m)
        h_slab : float
            Slab thickness (m) — controls the extent of the Cl.215.4 gradient.
        E_s : float
            Steel modulus (MPa) — reference for transformed-section properties.
        T_profile_rise : list of (y, T), optional
            Signed temperature (°C) at each depth y (m) for positive gradient
            (top heating).  If None, derived from IRC:6-2017 Cl.215.4 'heating'.
        T_profile_fall : list of (y, T), optional
            Signed temperature (°C) for negative gradient (top cooling).
            If None, derived from IRC:6-2017 Cl.215.4 'cooling' with negated values
            so cooling → negative F_N (contraction) and correct bending sign.
        dy : float
            Integration strip height (m).  Default: 0.001 m.

        Returns
        -------
        dict with keys:
            y_NA_m, A_eq_m2, I_eq_m4,
            F_N_rise_kN, M_N_rise_kNm, F_N_fall_kN, M_N_fall_kNm,
            sigma_eigen_rise_MPa, sigma_eigen_fall_MPa,
            kappa_rise_per_m, kappa_fall_per_m,
            delta_mid_rise_m, delta_mid_fall_m,
            clause, note_secondary
        """
        L = self.L

        # ── IRC:6-2017 Cl.215.2 — thermal expansion coefficient ──────────────
        alpha = IRC6_2017.cl_215_4_material_properties()['alpha']   # /°C

        D_total = max(p['y_top'] + p['h'] for p in parts)   # total composite depth (m)

        # ── Build IRC:6-2017 Cl.215.4 profiles when not supplied ─────────────
        if T_profile_rise is None:
            gr    = IRC6_2017.cl_215_4_temperature_gradient(h_slab, gradient_type='heating')
            T_fn  = gr['T_at_y']
            n_pts = max(int(D_total / 0.001) + 2, 3)
            # T_fn returns 0 for y > h_slab; profile covers full composite depth
            T_profile_rise = [(i * 0.001, T_fn(i * 0.001)) for i in range(n_pts)]
            print(f"Gradient profile (heating): T1={gr['T1']:.1f}°C  h1={gr['h1']:.3f} m  [{gr['clause']}]")

        if T_profile_fall is None:
            gr    = IRC6_2017.cl_215_4_temperature_gradient(h_slab, gradient_type='cooling')
            T_fn  = gr['T_at_y']
            n_pts = max(int(D_total / 0.001) + 2, 3)
            # Negate magnitudes: cooling → negative F_N and correct bending sign
            T_profile_fall = [(i * 0.001, -T_fn(i * 0.001)) for i in range(n_pts)]
            print(f"Gradient profile (cooling): T1={gr['T1']:.1f}°C  h1={gr['h1']:.3f} m  [{gr['clause']}]")

        # ── Step 1 — Transformed section properties (reference modulus = E_s) ─
        # Modular ratio n_i = E_i / E_s  (< 1 for concrete, = 1 for steel)
        A_eq   = 0.0   # m²   total transformed area
        Ay_sum = 0.0   # m³   first moment of transformed area from top face

        for part in parts:
            n_i    = part['E'] / E_s
            y_c_i  = part['y_top'] + part['h'] / 2.0   # part centroid depth (m)
            A_eq  += n_i * part['b'] * part['h']
            Ay_sum += n_i * part['b'] * part['h'] * y_c_i

        y_NA = Ay_sum / A_eq   # neutral axis depth from top (m)

        # Transformed second moment of area about NA  (parallel-axis theorem)
        I_eq = 0.0   # m⁴
        for part in parts:
            n_i   = part['E'] / E_s
            b_i   = part['b']
            h_i   = part['h']
            y_c_i = part['y_top'] + h_i / 2.0
            I_eq += n_i * (b_i * h_i**3 / 12.0
                           + b_i * h_i * (y_c_i - y_NA)**2)

        print(
            f"Transformed section (IRC:6-2017 Cl.215.4): "
            f"y_NA={y_NA:.4f} m  A_eq={A_eq:.5f} m²  I_eq={I_eq:.6f} m⁴"
        )

        # ── Helper: piecewise linear interpolation of (y, T) profile ─────────
        def interp_profile(T_profile: list[tuple], y: float) -> float:
            """Linearly interpolate; returns boundary value outside defined range."""
            if not T_profile:
                return 0.0
            if y <= T_profile[0][0]:
                return T_profile[0][1]
            if y >= T_profile[-1][0]:
                return T_profile[-1][1]
            for i in range(len(T_profile) - 1):
                y0, T0 = T_profile[i]
                y1, T1 = T_profile[i + 1]
                if y0 <= y <= y1:
                    return T0 + (y - y0) / (y1 - y0) * (T1 - T0)
            return 0.0

        # ── Helper: fine-strip numerical integration of F_N and M_N ──────────
        def integrate_profile(T_profile: list[tuple]) -> tuple[float, float]:
            """
            Axial (F_N, kN) and moment (M_N, kN·m) thermal resultants.

            Unit path:
              E_i [MPa] × 1000 → [kN/m²]
              × alpha [/°C] × T(y) [°C] × b [m] × dy [m]  →  kN
              × (y − y_NA) [m]                              →  kN·m

            Each part uses its own E_i, so the concrete-to-steel interface at
            the slab soffit is handled correctly.  Parts with T = 0 throughout
            contribute zero without special-casing.
            """
            F_N = 0.0
            M_N = 0.0
            for part in parts:
                y_top    = part['y_top']
                b        = part['b']      # m
                E_i      = part['E']      # MPa
                n_strips = max(1, int(round(part['h'] / dy)))
                dy_i     = part['h'] / n_strips
                for k in range(n_strips):
                    y_mid = y_top + (k + 0.5) * dy_i
                    T_y   = interp_profile(T_profile, y_mid)
                    dF    = E_i * 1000.0 * alpha * T_y * b * dy_i   # kN
                    F_N  += dF
                    M_N  += dF * (y_mid - y_NA)                      # kN·m
            return F_N, M_N

        # ── Step 2 — Piecewise integration of thermal resultants ──────────────
        F_N_rise, M_N_rise = integrate_profile(T_profile_rise)
        F_N_fall, M_N_fall = integrate_profile(T_profile_fall)

        # ── Step 3 — Eigen stresses at key fibre locations ────────────────────
        def E_at_y(y_check: float) -> float:
            """E (MPa) of the part whose depth range contains y_check."""
            for p in parts:
                if p['y_top'] <= y_check <= p['y_top'] + p['h']:
                    return p['E']
            return E_s   # gap between parts — fall back to steel

        def sigma_eigen(
            y_f: float,
            F_N: float,
            M_N: float,
            T_profile: list[tuple],
        ) -> float:
            """
            Eigen stress (MPa) at fibre depth y_f from top of section.

            sigma = E_f × alpha × T_f
                    − F_N / (A_eq × 1000)
                    − M_N × (y_f − y_NA) / (I_eq × 1000)

            Unit check (all terms → MPa):
              E_f [MPa] × alpha [/°C] × T_f [°C]             = MPa ✓
              F_N [kN] / (A_eq [m²] × 1000)                  = MPa ✓
              M_N [kN·m] × Δy [m] / (I_eq [m⁴] × 1000)      = MPa ✓
            """
            E_f = E_at_y(y_f)
            T_f = interp_profile(T_profile, y_f)
            return (
                E_f * alpha * T_f
                - F_N / (A_eq * 1000.0)
                - M_N * (y_f - y_NA) / (I_eq * 1000.0)
            )

        # Standard fibre check depths — identified from parts labels
        web_part = next(
            (p for p in parts if 'web' in p.get('label', '').lower()), None
        )
        bot_fl = next(
            (p for p in parts
             if 'bot' in p.get('label', '').lower()
             and 'flange' in p.get('label', '').lower()),
            None,
        )

        fibre_locs: list[tuple[str, float]] = [
            ('top_of_slab',         0.0),
            ('bottom_of_slab',      h_slab),
            ('top_of_steel_flange', h_slab),   # coincides with slab soffit
        ]
        if web_part:
            fibre_locs.append(('top_of_web',    web_part['y_top']))
            fibre_locs.append(('mid_depth_web', web_part['y_top'] + web_part['h'] / 2.0))
        if bot_fl:
            fibre_locs.append(('bottom_flange_top', bot_fl['y_top']))
        fibre_locs.append(('bottom_fibre', D_total))

        sigma_rise = {
            lbl: sigma_eigen(y_f, F_N_rise, M_N_rise, T_profile_rise)
            for lbl, y_f in fibre_locs
        }
        sigma_fall = {
            lbl: sigma_eigen(y_f, F_N_fall, M_N_fall, T_profile_fall)
            for lbl, y_f in fibre_locs
        }

        # ── Step 4 — Midspan deflection from gradient  (simply supported) ─────
        # No secondary reactions — IRC:6-2017 Cl.215.4
        # kappa = M_N / (E_s [kN/m²] × I_eq [m⁴])
        # delta_mid = kappa × L² / 8
        kappa_rise     = M_N_rise / (E_s * 1000.0 * I_eq)   # 1/m
        kappa_fall     = M_N_fall / (E_s * 1000.0 * I_eq)   # 1/m
        delta_mid_rise = kappa_rise * L**2 / 8.0             # m
        delta_mid_fall = kappa_fall * L**2 / 8.0             # m

        print(
            f"Thermal resultants: "
            f"F_N_rise={F_N_rise:.2f} kN  M_N_rise={M_N_rise:.2f} kN·m  "
            f"delta_mid_rise={delta_mid_rise * 1000:.2f} mm"
        )

        result = {
            # Transformed section properties
            'y_NA_m':               y_NA,
            'A_eq_m2':              A_eq,
            'I_eq_m4':              I_eq,
            # Thermal resultants
            'F_N_rise_kN':          F_N_rise,
            'M_N_rise_kNm':         M_N_rise,
            'F_N_fall_kN':          F_N_fall,
            'M_N_fall_kNm':         M_N_fall,
            # Eigen stresses at standard fibre locations (MPa)
            'sigma_eigen_rise_MPa': sigma_rise,
            'sigma_eigen_fall_MPa': sigma_fall,
            # Curvature and midspan deflection from gradient
            'kappa_rise_per_m':     kappa_rise,
            'kappa_fall_per_m':     kappa_fall,
            'delta_mid_rise_m':     delta_mid_rise,
            'delta_mid_fall_m':     delta_mid_fall,
            # Metadata
            'clause':               'IRC 6:2017 Cl.215.4',
            'note_secondary': (
                'Simply supported span: secondary (hyperstatic) reactions = 0. '
                'Gradient causes free curvature only.'
            ),
        }

        self.temp_gradient_results = result
        return result

    # ─────────────────────────────────────────────────────────────────────────
    # Temperature and seismic loads
    # ─────────────────────────────────────────────────────────────────────────

    def add_temperature_load(self) -> None:
        """
        Apply temperature load to the grillage model as a patch load over the
        full deck footprint per IRC:6-2017 Cl.215.

        The load intensity is read from ``self.additional_inputs`` using the key
        ``"temperature_load_kN_m2"``.  If the key is absent or zero the load is
        silently skipped (temperature load is optional).

        Delegates to BridgeGrillageModel.create_temperature_load().
        """
        tl_raw = self.input_dict.get("temperature_load_kN_m2")
        if not tl_raw or float(tl_raw) == 0.0:
            bridge_logger.info("Temperature load absent; skipping.")
            return
        tl_kN_m2 = float(tl_raw)
        self.grillage_model.create_temperature_load(
            temperature_load_kN_m2=tl_kN_m2,
            partial_safety_factor=1.0,
        )

    def add_seismic_loads(self) -> None:
        """
        Apply seismic load cases to the grillage model per IRC:6-2017 Cl. 218.

        Must be called AFTER ``create_governing_ll_load_case()`` so that:
          - the dead-load cases exist on the grillage model (total DL is
            integrated from them on demand), and
          - ``governing_ll_name`` is set so the governing vehicle weight can
            be computed for the IRC 218.5.2 live-load fraction.

        Input sources
        -------------
        ``KEY_PROJECT_LOCATION`` : zone factor Z from ``weather_data['z_value']``.
        ``KEY_SL_*``             : importance factor, soil type, time period,
                                   damping, response reduction factor and the
                                   UI-computed Ah / Av coefficients.
        DL / LL                  : derived from model state, unless the seismic
                                   tab's Custom mode supplies explicit values.

        Load cases created (delegated to
        BridgeGrillageModel.create_seismic_load_cases):
          - ``"EQ_X"``            → Longitudinal seismic (0% LL)
          - ``"EQ_Z"``            → Transverse seismic (20% LL)
          - ``"EQ_Y"``            → Vertical seismic, Av = (2/3)×Ah (20% LL)
          - ``"1.5 EQ (a/b/c)"``  → IRC 218.3 design combinations with γ = 1.5
        """
        inp = self.input_dict

        # ── Zone factor Z: from project-location weather_data ──
        location = inp.get(KEY_PROJECT_LOCATION) or {}
        if isinstance(location, str) and '{' in location:
            import ast
            try:
                location = ast.literal_eval(location)
            except (ValueError, SyntaxError):
                location = {}
        z_value = 0.10  # Zone II default (lowest hazard)
        if isinstance(location, dict):
            weather = location.get('weather_data') or {}
            z_val = weather.get('z_value')
            if z_val is not None:
                z_value = float(z_val)

        # ── Soil type from the seismic tab ──
        soil_str = str(inp.get(KEY_SL_SOIL_TYPE) or "")
        soil_type = 3 if "III" in soil_str else (2 if "II" in soil_str else 1)

        # ── IRC 218 parameters from the seismic tab ──
        def _to_float(key: str, default: float) -> float:
            try:
                return float(inp.get(key))
            except (TypeError, ValueError):
                return default

        importance_factor = _to_float(KEY_SL_IMPORTANCE_FACTOR, 1.0)
        damping_pct       = _to_float(KEY_SL_DAMPING, 2.0)
        R                 = _to_float(KEY_SL_RESPONSE_REDUCTION, 1.0)
        time_period       = _to_float(KEY_SL_TIME_PERIOD, 0.5)

        # ── Ah and Av: use UI-computed values if present; else computed in
        # the analyser from z_value / soil / T / damping ──
        def _to_coeff(key: str) -> float | None:
            try:
                v = float(inp.get(key))
                return v if v > 0 else None
            except (TypeError, ValueError):
                return None

        Ah = _to_coeff(KEY_SL_HORIZONTAL_COEFF)
        Av = _to_coeff(KEY_SL_VERTICAL_COEFF)

        # ── DL / LL: Custom mode overrides; Automatic (default) derives them
        # from model state inside create_seismic_load_cases() ──
        def _custom_load(mode_key: str, value_key: str) -> float | None:
            if str(inp.get(mode_key) or "Automatic") != "Custom":
                return None
            try:
                return float(inp.get(value_key))
            except (TypeError, ValueError):
                return None

        dead_load_kN = _custom_load(KEY_SL_DEAD_LOAD_MODE, KEY_SL_DEAD_LOAD_VALUE)
        live_load_kN = _custom_load(KEY_SL_LIVE_LOAD_MODE, KEY_SL_LIVE_LOAD_VALUE)

        self.grillage_model.create_seismic_load_cases(
            z_value=z_value,
            soil_type=soil_type,
            importance_factor=importance_factor,
            damping_percent=damping_pct,
            response_reduction_factor=R,
            time_period=time_period,
            Ah=Ah,
            Av=Av,
            dead_load_kN=dead_load_kN,
            live_load_kN=live_load_kN,
            partial_safety_factor=1.5,  # IRC:6-2017 Table B.2 seismic ULS
        )

    def vehicle_lane_coordinates(self) -> list:
        """
        Return vehicle-to-coordinate mappings for all IRC:6-2017 Table 6A
        combinations.

        Delegates to BridgeGrillageModel.vehicle_lane_coordinates().

        Returns
        -------
        list of dict
            Each dict has 'case_num' and 'combinations' keys.
        """
        return self.grillage_model.vehicle_lane_coordinates()

    def create_vehicle_load_cases(self) -> list:
        """
        Create static vehicle load cases based on IRC:6-2017 lane combinations.

        Delegates to BridgeGrillageModel.create_vehicle_load_cases().

        Returns
        -------
        list
            All created load case objects.
        """
        return self.grillage_model.create_vehicle_load_cases()

    def add_vehicle_load_cases_from_combinations(self) -> list:
        """
        Create vehicle load cases with lane factors (alf) and dynamic load
        allowance (dla) applied, using IRC:6-2017 combinations.

        Delegates to BridgeGrillageModel.add_vehicle_load_cases_from_combinations().

        Returns
        -------
        list
            All created load case objects.
        """
        return self.grillage_model.add_vehicle_load_cases_from_combinations()

    def create_moving_vehicle_load_cases(
        self,
        span: float | None = None,
    ) -> list:
        """
        Create moving load cases for all vehicles previously created by
        add_vehicle_load_cases_from_combinations().

        The traversal path extents are derived from each vehicle's IRC:6
        length: start = -vehicle_length, end = span + vehicle_length.

        Delegates to BridgeGrillageModel.create_moving_vehicle_load_cases().

        Parameters
        ----------
        span : float, optional
            Override the bridge span (m); defaults to the analysed span.

        Returns
        -------
        list
            All created moving load case objects.
        """
        return self.grillage_model.create_moving_vehicle_load_cases(
            span=span,
        )

    def analyze(self):
        """
        Run the OpenSees grillage analysis for all registered load cases.

        Delegates to BridgeGrillageModel.analyze(), which executes the model,
        retrieves results for every load case, and stores them in
        ``self.grillage_model.dataset``.

        Must be called after add_dead_loads() and add_live_loads() have
        registered all load cases on the model.

        Returns
        -------
        xarray.Dataset
            Results dataset containing displacements and forces for all load
            cases, indexed by Loadcase, Node/Element, and Component.
        """
        bridge_logger.check_cancel()
        result = self.grillage_model.analyze()
        return result

    def create_governing_ll_load_case(self, dataset, partial_safety_factor: float = 1.0):
        """
        Identify the governing static vehicle load case, create a
        ``"{partial_safety_factor} LL"`` load case from it, and solve just that case.

        Must be called after analyze().

        Parameters
        ----------
        dataset : xarray.Dataset
            Results from the initial analysis.
        partial_safety_factor : float
            ULS partial safety factor for the governing LL case (default 1.0).

        Returns
        -------
        None
            The combined dataset is built once by _reanalyze_with_dedup().
        """
        return self.grillage_model.create_governing_ll_load_case(
            dataset=dataset,
            partial_safety_factor=partial_safety_factor,
        )

    def _reanalyze_with_dedup(self):
        """
        Solve the load cases added since the initial analysis (the DL+LL case and
        the ULS/SLS combinations), build the combined results dataset once, cache
        it on the grillage model, and return it.

        A bare analyze() would re-solve EVERY registered case — including all
        ~50 increments of each moving load — and ospgrillage's record store
        (extract_analysis -> dict.setdefault) would then discard the repeated
        results, so only the new cases are passed to analyze().

        Called by design() after load combinations have been registered so that
        combination results are included in the final results dataset.
        """
        g = self.grillage_model
        m = g.model

        new_cases = [
            lc.name
            for lc in (
                [getattr(g, "dl_ll_combination", None)]
                + list(getattr(g, "uls_combinations", None) or [])
                + list(getattr(g, "sls_combinations", None) or [])
            )
            if lc is not None
        ]
        if new_cases:
            m.analyze(load_case=new_cases)

        ds = m.get_results()

        # Safety net only: with the installed ospgrillage the records are keyed by
        # load-case name, so no duplicate Loadcase labels occur; keep the axis
        # unique anyway in case a future ospgrillage version changes behaviour.
        lc_vals = ds.coords["Loadcase"].values
        seen: set = set()
        unique_idx = []
        for i, val in enumerate(lc_vals):
            if val not in seen:
                seen.add(val)
                unique_idx.append(i)
        if len(unique_idx) < len(lc_vals):
            ds = ds.isel(Loadcase=unique_idx)

        self.grillage_model._deduplicated_results = ds
        return ds

    def _drop_moving_increment_cases(self, ds):
        """
        Drop the per-position "Moving CaseN at global position ..." rows from the
        cached results dataset once the envelopes exist.

        These ~50-increments-per-vehicle rows dominate the Loadcase axis (about
        two thirds of it) but have no post-design consumer: governing-LL
        detection uses the static vehicle cases during stage 4F, envelopes cover
        the combinations, the plots dropdown deliberately hides them
        (mpl_plot_widget.link_output_dock), and the load-effects table excludes
        them. Keeping them just multiplies the resident dataset (and everything
        derived from it, e.g. result_data) roughly 3x.
        """
        lcs = ds.coords["Loadcase"].values
        keep = [lc for lc in lcs if not str(lc).startswith("Moving ")]
        if len(keep) == len(lcs):
            return ds
        ds = ds.sel(Loadcase=keep)
        self.grillage_model._deduplicated_results = ds
        log_memory(
            f"design: dropped {len(lcs) - len(keep)} moving-increment load cases "
            f"from cached dataset ({len(lcs)} -> {len(keep)})"
        )
        return ds

    def create_envelope_load_case(self, dataset=None):
        """
        Build two worst-signed-magnitude force/displacement envelopes — one over
        the ULS combinations and one over the SLS combinations — and inject them
        into the results dataset as the pseudo load cases ``Envelope ULS`` and
        ``Envelope SLS``.

        Delegates to BridgeGrillageModel.create_envelope_load_case(), which
        caches the augmented dataset on the grillage model's
        ``_deduplicated_results`` and the standalone enveloped DataArrays on its
        ``result_envelopes`` (``{label: {"forces", "displacements"}}``). Both are
        mirrored onto this object.

        Parameters
        ----------
        dataset : xarray.Dataset, optional
            Results dataset to envelope. Defaults to the deduplicated results
            cached on the grillage model.

        Returns
        -------
        xarray.Dataset
            The augmented dataset with the ``Envelope ULS`` / ``Envelope SLS`` rows.
        """
        augmented = self.grillage_model.create_envelope_load_case(dataset=dataset)
        self.result_envelopes = self.grillage_model.result_envelopes
        self._results_with_envelope = augmented
        return augmented

    # ─────────────────────────────────────────────────────────────────────────
    # Load combinations
    # ─────────────────────────────────────────────────────────────────────────

    #: Input-dict key holding the per-combination include/exclude selection
    #: persisted by the load-combination checkbox widget (LoadCombinationWidget).
    _LC_SELECTION_KEY = "irc6_default_combinations"

    def _combination_keys(self, namespace_filter):
        """
        Return the set of selected (included) combination keys, or ``None``.

        Reads the per-combination selection saved by the load-combination UI
        (a list of ``{"key", "included", ...}`` dicts). ``namespace_filter`` is
        a predicate on the key string used to keep only ULS or only SLS keys.

        Returns ``None`` when no selection exists (dialog never opened) so the
        analyser falls back to generating every combination. Returns a (possibly
        empty) ``set`` otherwise — an empty set means the user de-selected every
        combination in that limit state, so none should be generated.
        """
        sel = self.input_dict.get(self._LC_SELECTION_KEY)
        if not sel:
            return None
        return {
            e["key"] for e in sel
            if e.get("included") and e.get("key") and namespace_filter(e["key"])
        }

    def create_uls_combinations(self) -> list:
        """
        Create the user-selected ULS load combinations per IRC:6-2017 Table B.2.

        When all are selected, produces 13 combinations:
          BASIC_1 … BASIC_6        — 2 permanent directions × 3 variable leaders
          ACCIDENTAL_1 … ACCIDENTAL_3 — 3 events × 1 valid leader
          SEISMIC_1 … SEISMIC_4    — 2 directions × 2 seismic conditions

        The combinations the user de-selected in the load-combination UI are
        skipped; with no saved selection every combination is generated.

        Must be called after create_governing_ll_load_case() so that the LL
        load case (``ll_load_case``) is available for combination.

        Delegates to BridgeGrillageModel.create_uls_combinations().

        Returns
        -------
        list — ospgrillage load-case objects registered with the model.
        """
        included = self._combination_keys(lambda k: ".sls." not in k)
        return self.grillage_model.create_uls_combinations(included_keys=included)

    def create_sls_combinations(self) -> list:
        """
        Create the user-selected SLS load combinations per IRC:6-2017 Table B.3.

        When all are selected, produces 14 combinations:
          SLS_RARE_1 … SLS_RARE_6          — 2 surfacing directions × 3 variable leaders
          SLS_FREQUENT_1 … SLS_FREQUENT_6  — same structure, frequent-column factors
          SLS_QP_1, SLS_QP_2               — quasi-permanent; only TL (0.5) contributes

        The combinations the user de-selected in the load-combination UI are
        skipped; with no saved selection every combination is generated.

        Must be called after create_governing_ll_load_case() so that the LL
        load case is available for combination.

        Delegates to BridgeGrillageModel.create_sls_combinations().

        Returns
        -------
        list — ospgrillage load-case objects registered with the model.
        """
        included = self._combination_keys(lambda k: ".sls." in k)
        return self.grillage_model.create_sls_combinations(included_keys=included)

    def create_dl_ll_combination(self, dl_factor: float = 1.0, ll_factor: float = 1.0):
        """
        Create the ``"{dl_factor} DL + {ll_factor} LL"`` load case combining the
        dead-load combination with the governing live-load case.

        With the defaults this registers a ``"1.0 DL + 1.0 LL"`` case carrying
        the unfactored sum of dead and live loads.

        Must be called after create_dead_load_combination() (via add_dead_loads())
        and create_governing_ll_load_case() so both sub-cases are available.

        Delegates to BridgeGrillageModel.create_dl_ll_combination().

        Returns
        -------
        The ospgrillage load-case object registered with the model, or ``None``
        if neither sub-case was available.
        """
        return self.grillage_model.create_dl_ll_combination(
            dl_factor=dl_factor, ll_factor=ll_factor
        )

    # ─────────────────────────────────────────────────────────────────────────
    # DCR checks
    # ─────────────────────────────────────────────────────────────────────────

    def _run_dcr_checks(self, dataset) -> None:
        """Run structural capacity checks and push DCR percentages to the output dock."""
        results = PlateGirderAnalysisResults(dataset=dataset, bridge=self.grillage_model)
        _, engine, design_results = run_design_check(
            plate_girder_bridge=self,
            analysis_results=results,
            print_report=True,
        )
        self._dcr_engine = engine
        bridge_logger.check_cancel()
        self.design_results = design_results

        # Write every output into output_dict while it is still mutable.
        # store_design_results also sets the KEY_UTIL_* values so the block
        # below is redundant — but kept for the _frontend.set_output_value calls.
        # self.store_design_results(design_results)

    def _design_cross_bracing_members(self) -> dict:
        """
        Run Osdag member designs for cross-bracing diagonals and chords.

        Returns
        -------
        dict — nested by pair → member → force_type → Osdag result.
        """
        from osdagbridge.core.bridge_types.plate_girder.cross_bracing_design import CrossBracingDesign
        from osdagbridge.core.bridge_types.plate_girder.results_data import enrich_crossbracing_dump

        if not self.result_data:
            print("[CrossBracing] No analysis results available — skipping.")
            return {}

        cb = CrossBracingDesign(bridge=self)
        if not cb.get_crossbracing_count():
            print("[CrossBracing] No cross-bracing panels found — skipping.")
            return {}

        forces_dict = cb.get_design_forces_dict()
        if not forces_dict or not forces_dict.get("pairs"):
            return {}
        
        # Store configuration in output_dict
        self.output_dict["member_properties.cross_bracing_details.type"] = forces_dict.get("brace_type", "X")
        self.output_dict["member_properties.cross_bracing_details.top_chord"] = forces_dict.get("top_chord", True)
        self.output_dict["member_properties.cross_bracing_details.bottom_chord"] = forces_dict.get("bottom_chord", True)
        
        cb.print_critical_forces(forces_dict)

        bridge_logger.check_cancel()
        pair_designs = cb.run_member_designs(forces_dict)
        self.output_dict["crossbracing_forces_dict"] = forces_dict

        enrich_crossbracing_dump(pair_designs)
        # self._print_crossbracing_design_results(forces_dict, pair_designs)

        # Resolve all possible intermediate girder pairs
        n_girders = int(self.input_dict[KEY_TS_NO_OF_GIRDERS])
        pairs = [f"G{i}-G{i+1}" for i in range(1, n_girders)]

        # Key mapping function
        def make_pair_key(key: str, pair_id: str) -> str:
            for pfx in (
                "transverse_member_design.cb.section_properties.bracing",
                "transverse_member_design.cb.section_properties.top_chord",
                "transverse_member_design.cb.section_properties.bottom_chord",
            ):
                if key.startswith(pfx):
                    suffix = key[len(pfx):].lstrip(".")
                    return f"{pfx}.{pair_id}.{suffix}"
            pfx = "member_properties.cross_bracing_details"
            if key.startswith(pfx):
                suffix = key[len(pfx):].lstrip(".")
                return f"{pfx}.{pair_id}.{suffix}"
            return f"{key}.{pair_id}"

        # Initialize keys to None for all pairs (both brace & chords)
        for pair in pairs:
            pair_id = pair.replace("-", "")
            
            # Diagonal/bracing
            for k in (
                KEY_TD_CB_PROP_L, KEY_TD_CB_PROP_H, KEY_TD_CB_PROP_B, KEY_TD_CB_PROP_TW, KEY_TD_CB_PROP_TF,
                KEY_TD_CB_PROP_RZ, KEY_TD_CB_PROP_M, KEY_TD_CB_PROP_A, KEY_TD_CB_PROP_IZ, KEY_TD_CB_PROP_IV,
                KEY_TD_CB_PROP_RV, KEY_TD_CB_PROP_ZZ, KEY_TD_CB_PROP_ZV, KEY_TD_CB_PROP_ZUZ, KEY_TD_CB_PROP_ZUV,
            ):
                self.output_dict[make_pair_key(k, pair_id)] = None

            # Top chord
            for k in (
                KEY_TD_CB_TOP_CHORD_PROP_L, KEY_TD_CB_TOP_CHORD_PROP_H, KEY_TD_CB_TOP_CHORD_PROP_B, KEY_TD_CB_TOP_CHORD_PROP_TW, KEY_TD_CB_TOP_CHORD_PROP_TF,
                KEY_TD_CB_TOP_CHORD_PROP_RZ, KEY_TD_CB_TOP_CHORD_PROP_M, KEY_TD_CB_TOP_CHORD_PROP_A, KEY_TD_CB_TOP_CHORD_PROP_IZ, KEY_TD_CB_TOP_CHORD_PROP_IV,
                KEY_TD_CB_TOP_CHORD_PROP_RV, KEY_TD_CB_TOP_CHORD_PROP_ZZ, KEY_TD_CB_TOP_CHORD_PROP_ZV, KEY_TD_CB_TOP_CHORD_PROP_ZUZ, KEY_TD_CB_TOP_CHORD_PROP_ZUV,
            ):
                self.output_dict[make_pair_key(k, pair_id)] = None

            # Bottom chord
            for k in (
                KEY_TD_CB_BOTTOM_CHORD_PROP_L, KEY_TD_CB_BOTTOM_CHORD_PROP_H, KEY_TD_CB_BOTTOM_CHORD_PROP_B, KEY_TD_CB_BOTTOM_CHORD_PROP_TW, KEY_TD_CB_BOTTOM_CHORD_PROP_TF,
                KEY_TD_CB_BOTTOM_CHORD_PROP_RZ, KEY_TD_CB_BOTTOM_CHORD_PROP_M, KEY_TD_CB_BOTTOM_CHORD_PROP_A, KEY_TD_CB_BOTTOM_CHORD_PROP_IZ, KEY_TD_CB_BOTTOM_CHORD_PROP_IV,
                KEY_TD_CB_BOTTOM_CHORD_PROP_RV, KEY_TD_CB_BOTTOM_CHORD_PROP_ZZ, KEY_TD_CB_BOTTOM_CHORD_PROP_ZV, KEY_TD_CB_BOTTOM_CHORD_PROP_ZUZ, KEY_TD_CB_BOTTOM_CHORD_PROP_ZUV,
            ):
                self.output_dict[make_pair_key(k, pair_id)] = None

        # Process design results and query database per pair
        from osdagbridge.core.bridge_types.plate_girder.results_data import _extract_osdag_summary

        top_chord_enabled = self.output_dict.get("member_properties.cross_bracing_details.top_chord", True)
        bottom_chord_enabled = self.output_dict.get("member_properties.cross_bracing_details.bottom_chord", True)

        for pair in pairs:
            pair_id = pair.replace("-", "")
            member_designs = pair_designs.get(pair, {}) if pair_designs else {}

            # Diagonal section designation for this pair
            diag_des = ""
            diag_data = member_designs.get("diagonal", {})
            for force_type in ("tension", "compression"):
                res = _extract_osdag_summary(diag_data.get(force_type) or {})
                sec = res.get("section")
                if sec:
                    diag_des = str(sec)
                    break

            # Chord section designation for this pair
            chord_des = ""
            chord_data = member_designs.get("chord", {})
            for force_type in ("tension", "compression"):
                res = _extract_osdag_summary(chord_data.get(force_type) or {})
                sec = res.get("section")
                if sec:
                    chord_des = str(sec)
                    break

            # Query database and populate diagonal section properties
            if diag_des:
                self.output_dict[make_pair_key(KEY_MP_CB_BRACING_SECTION_TYPE, pair_id)] = diag_des
                diag_details = self._query_crossbracing_section(diag_des)
                if diag_details:
                    self.output_dict[make_pair_key("member_properties.cross_bracing_details.diagonal.section_type", pair_id)] = diag_details["type"]
                    
                    # Set diagonal dimensions
                    leg_h_key = make_pair_key("member_properties.cross_bracing_details.diagonal.leg_h", pair_id)
                    leg_w_key = make_pair_key("member_properties.cross_bracing_details.diagonal.leg_w", pair_id)
                    thick_key = make_pair_key("member_properties.cross_bracing_details.diagonal.thickness", pair_id)
                    if diag_details["type"] == "ANGLE":
                        self.output_dict[leg_h_key] = diag_details["H"] * 1000.0
                        self.output_dict[leg_w_key] = diag_details["B"] * 1000.0
                        self.output_dict[thick_key] = diag_details["tw"] * 1000.0
                    elif diag_details["type"] == "CHANNEL":
                        self.output_dict[leg_h_key] = diag_details["L"] * 1000.0
                        self.output_dict[leg_w_key] = diag_details["B"] * 1000.0
                        self.output_dict[thick_key] = diag_details["tw"] * 1000.0

                    self.output_dict[make_pair_key(KEY_TD_CB_PROP_L, pair_id)] = diag_details["L"]
                    self.output_dict[make_pair_key(KEY_TD_CB_PROP_H, pair_id)] = diag_details["H"]
                    self.output_dict[make_pair_key(KEY_TD_CB_PROP_B, pair_id)] = diag_details["B"]
                    self.output_dict[make_pair_key(KEY_TD_CB_PROP_TW, pair_id)] = diag_details["tw"]
                    self.output_dict[make_pair_key(KEY_TD_CB_PROP_TF, pair_id)] = diag_details["tF"]
                    self.output_dict[make_pair_key(KEY_TD_CB_PROP_RZ, pair_id)] = diag_details["rz"]
                    self.output_dict[make_pair_key(KEY_TD_CB_PROP_M, pair_id)] = diag_details["M"]
                    self.output_dict[make_pair_key(KEY_TD_CB_PROP_A, pair_id)] = diag_details["A"]
                    self.output_dict[make_pair_key(KEY_TD_CB_PROP_IZ, pair_id)] = diag_details["Iz"]
                    self.output_dict[make_pair_key(KEY_TD_CB_PROP_IV, pair_id)] = diag_details["Iv"]
                    self.output_dict[make_pair_key(KEY_TD_CB_PROP_RV, pair_id)] = diag_details["rv"]
                    self.output_dict[make_pair_key(KEY_TD_CB_PROP_ZZ, pair_id)] = diag_details["Zz"]
                    self.output_dict[make_pair_key(KEY_TD_CB_PROP_ZV, pair_id)] = diag_details["Zv"]
                    self.output_dict[make_pair_key(KEY_TD_CB_PROP_ZUZ, pair_id)] = diag_details["Zuz"]
                    self.output_dict[make_pair_key(KEY_TD_CB_PROP_ZUV, pair_id)] = diag_details["Zuv"]

            # Query database and populate top/bottom chords section properties
            if chord_des:
                self.output_dict[make_pair_key(KEY_MP_CB_TOP_CHORD_SECTION_DESIG, pair_id)] = chord_des
                self.output_dict[make_pair_key(KEY_MP_CB_BOTTOM_CHORD_SECTION_DESIG, pair_id)] = chord_des
                chord_details = self._query_crossbracing_section(chord_des)
                if chord_details:
                    if top_chord_enabled:
                        self.output_dict[make_pair_key("member_properties.cross_bracing_details.top_chord.section_type", pair_id)] = chord_details["type"]
                        tc_h_key = make_pair_key("member_properties.cross_bracing_details.top_chord.leg_h", pair_id)
                        tc_w_key = make_pair_key("member_properties.cross_bracing_details.top_chord.leg_w", pair_id)
                        tc_t_key = make_pair_key("member_properties.cross_bracing_details.top_chord.thickness", pair_id)
                        if chord_details["type"] == "ANGLE":
                            self.output_dict[tc_h_key] = chord_details["H"] * 1000.0
                            self.output_dict[tc_w_key] = chord_details["B"] * 1000.0
                            self.output_dict[tc_t_key] = chord_details["tw"] * 1000.0
                        elif chord_details["type"] == "CHANNEL":
                            self.output_dict[tc_h_key] = chord_details["L"] * 1000.0
                            self.output_dict[tc_w_key] = chord_details["B"] * 1000.0
                            self.output_dict[tc_t_key] = chord_details["tw"] * 1000.0

                        self.output_dict[make_pair_key(KEY_TD_CB_TOP_CHORD_PROP_L, pair_id)] = chord_details["L"]
                        self.output_dict[make_pair_key(KEY_TD_CB_TOP_CHORD_PROP_H, pair_id)] = chord_details["H"]
                        self.output_dict[make_pair_key(KEY_TD_CB_TOP_CHORD_PROP_B, pair_id)] = chord_details["B"]
                        self.output_dict[make_pair_key(KEY_TD_CB_TOP_CHORD_PROP_TW, pair_id)] = chord_details["tw"]
                        self.output_dict[make_pair_key(KEY_TD_CB_TOP_CHORD_PROP_TF, pair_id)] = chord_details["tF"]
                        self.output_dict[make_pair_key(KEY_TD_CB_TOP_CHORD_PROP_RZ, pair_id)] = chord_details["rz"]
                        self.output_dict[make_pair_key(KEY_TD_CB_TOP_CHORD_PROP_M, pair_id)] = chord_details["M"]
                        self.output_dict[make_pair_key(KEY_TD_CB_TOP_CHORD_PROP_A, pair_id)] = chord_details["A"]
                        self.output_dict[make_pair_key(KEY_TD_CB_TOP_CHORD_PROP_IZ, pair_id)] = chord_details["Iz"]
                        self.output_dict[make_pair_key(KEY_TD_CB_TOP_CHORD_PROP_IV, pair_id)] = chord_details["Iv"]
                        self.output_dict[make_pair_key(KEY_TD_CB_TOP_CHORD_PROP_RV, pair_id)] = chord_details["rv"]
                        self.output_dict[make_pair_key(KEY_TD_CB_TOP_CHORD_PROP_ZZ, pair_id)] = chord_details["Zz"]
                        self.output_dict[make_pair_key(KEY_TD_CB_TOP_CHORD_PROP_ZV, pair_id)] = chord_details["Zv"]
                        self.output_dict[make_pair_key(KEY_TD_CB_TOP_CHORD_PROP_ZUZ, pair_id)] = chord_details["Zuz"]
                        self.output_dict[make_pair_key(KEY_TD_CB_TOP_CHORD_PROP_ZUV, pair_id)] = chord_details["Zuv"]

                    if bottom_chord_enabled:
                        self.output_dict[make_pair_key("member_properties.cross_bracing_details.bottom_chord.section_type", pair_id)] = chord_details["type"]
                        bc_h_key = make_pair_key("member_properties.cross_bracing_details.bottom_chord.leg_h", pair_id)
                        bc_w_key = make_pair_key("member_properties.cross_bracing_details.bottom_chord.leg_w", pair_id)
                        bc_t_key = make_pair_key("member_properties.cross_bracing_details.bottom_chord.thickness", pair_id)
                        if chord_details["type"] == "ANGLE":
                            self.output_dict[bc_h_key] = chord_details["H"] * 1000.0
                            self.output_dict[bc_w_key] = chord_details["B"] * 1000.0
                            self.output_dict[bc_t_key] = chord_details["tw"] * 1000.0
                        elif chord_details["type"] == "CHANNEL":
                            self.output_dict[bc_h_key] = chord_details["L"] * 1000.0
                            self.output_dict[bc_w_key] = chord_details["B"] * 1000.0
                            self.output_dict[bc_t_key] = chord_details["tw"] * 1000.0

                        self.output_dict[make_pair_key(KEY_TD_CB_BOTTOM_CHORD_PROP_L, pair_id)] = chord_details["L"]
                        self.output_dict[make_pair_key(KEY_TD_CB_BOTTOM_CHORD_PROP_H, pair_id)] = chord_details["H"]
                        self.output_dict[make_pair_key(KEY_TD_CB_BOTTOM_CHORD_PROP_B, pair_id)] = chord_details["B"]
                        self.output_dict[make_pair_key(KEY_TD_CB_BOTTOM_CHORD_PROP_TW, pair_id)] = chord_details["tw"]
                        self.output_dict[make_pair_key(KEY_TD_CB_BOTTOM_CHORD_PROP_TF, pair_id)] = chord_details["tF"]
                        self.output_dict[make_pair_key(KEY_TD_CB_BOTTOM_CHORD_PROP_RZ, pair_id)] = chord_details["rz"]
                        self.output_dict[make_pair_key(KEY_TD_CB_BOTTOM_CHORD_PROP_M, pair_id)] = chord_details["M"]
                        self.output_dict[make_pair_key(KEY_TD_CB_BOTTOM_CHORD_PROP_A, pair_id)] = chord_details["A"]
                        self.output_dict[make_pair_key(KEY_TD_CB_BOTTOM_CHORD_PROP_IZ, pair_id)] = chord_details["Iz"]
                        self.output_dict[make_pair_key(KEY_TD_CB_BOTTOM_CHORD_PROP_IV, pair_id)] = chord_details["Iv"]
                        self.output_dict[make_pair_key(KEY_TD_CB_BOTTOM_CHORD_PROP_RV, pair_id)] = chord_details["rv"]
                        self.output_dict[make_pair_key(KEY_TD_CB_BOTTOM_CHORD_PROP_ZZ, pair_id)] = chord_details["Zz"]
                        self.output_dict[make_pair_key(KEY_TD_CB_BOTTOM_CHORD_PROP_ZV, pair_id)] = chord_details["Zv"]
                        self.output_dict[make_pair_key(KEY_TD_CB_BOTTOM_CHORD_PROP_ZUZ, pair_id)] = chord_details["Zuz"]
                        self.output_dict[make_pair_key(KEY_TD_CB_BOTTOM_CHORD_PROP_ZUV, pair_id)] = chord_details["Zuv"]
        
        self.crossbracing_design_results = pair_designs
        return pair_designs
    
    def _design_end_diaphragm_members(self) -> dict:
        """
        Run Osdag member designs for end-diaphragm bracing members (diagonals/chords)
        if type is "Cross Bracing", or calculate and populate section properties if
        type is "Rolled Beam" or "Welded Beam".

        Returns
        -------
        dict - nested by pair -> member -> force_type -> Osdag result.
        """
        from osdagbridge.core.bridge_types.plate_girder.end_diaphragm_design import EndDiaphragmDesign
        ed_design = EndDiaphragmDesign(bridge=self)
        pair_designs = ed_design.get_forces_and_design()
        
        # Populate forces_dict for reports
        self.output_dict["end_diaphragm_forces_dict"] = getattr(ed_design, "forces_dict", {})
        self.end_diaphragm_design_results = pair_designs
        return pair_designs


