# SPDX-License-Identifier: MIT
"""AEC Configuration, Engine Constants, and Scientific Status Taxonomy."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple

# -----------------------------------------------------------------------------
# 1. SCIENTIFIC EVIDENCE TAXONOMY (§37)
# -----------------------------------------------------------------------------
class ScientificStatus(str, Enum):
    """Scientific maturity rating for mechanisms and transformations."""
    VERIFIED_SOURCE = "VERIFIED_SOURCE"       # Proven from C++ sim.hpp or Kaggle engine 1.32.7
    REUSED_SAFETY = "REUSED_SAFETY"           # Validated safety predicate from ARCH-003
    IMPLEMENTATION_ONLY = "IMPLEMENTATION_ONLY" # Architectural glue / plumbing
    PLAUSIBLE_UNPROVEN = "PLAUSIBLE_UNPROVEN" # Analytically sound hypothesis; unproven in cohort
    EXPERIMENTAL = "EXPERIMENTAL"             # Active candidate under test
    QUARANTINED = "QUARANTINED"               # Scientifically unready / unvalidated
    FALSIFIED = "FALSIFIED"                   # Empirically falsified by prospective CRN trial

# -----------------------------------------------------------------------------
# 2. VERIFIED ENGINE CONSTANTS (C++ sim.hpp / kaggle_environments 1.32.7)
# -----------------------------------------------------------------------------
BOARD_SIZE: int = 10
EPISODE_STEPS: int = 720
TURNS_PER_DAY: int = 24
STARTING_MONEY: float = 3000.0
SHED_CAPACITY: int = 100
MAX_MARKET_ORDERS: int = 10
SHOP_UNLOCK_INTERVAL: int = 72
MAX_SHOP_INSTANCES: int = 8
FINAL_STEP: int = 718

PRODUCTS: Tuple[str, ...] = (
    "WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
    "EGG", "MILK", "WOOL", "FERTILIZER"
)
CROPS: Tuple[str, ...] = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")
ANIMALS: Tuple[str, ...] = ("GOOSE", "COW", "SHEEP")

CROP_SEED_PRICE: Dict[str, int] = {
    "WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80
}
CROP_GROWTH_DAYS: Dict[str, int] = {
    "WHEAT": 2, "CARROT": 2, "TOMATO": 8, "STRAWBERRY": 10, "MELON": 10
}
ANIMAL_COST: Dict[str, int] = {"GOOSE": 300, "COW": 400, "SHEEP": 500}
ANIMAL_STRUCTURE: Dict[str, str] = {"GOOSE": "COOP", "COW": "PASTURE", "SHEEP": "PASTURE"}

LAND_PRICES: Tuple[int, ...] = (1000, 2000, 4000)
MOVES: Dict[str, Tuple[int, int]] = {
    "NORTH": (0, -1), "SOUTH": (0, 1), "EAST": (1, 0), "WEST": (-1, 0)
}
SHED_TILES: Tuple[Tuple[int, int], ...] = ((4, 4), (5, 4), (4, 5), (5, 5))

# -----------------------------------------------------------------------------
# 3. MECHANISM GOVERNANCE & TAXONOMY (§36, §37)
# -----------------------------------------------------------------------------
MECHANISM_REGISTRY: Dict[str, Dict[str, Any]] = {
    "FRONTLOAD_ORDERS": {
        "status": ScientificStatus.FALSIFIED,
        "category": "MARKET",
        "role": "RETIRED",
        "rationale": "Falsified in EXP-AEC-002; order-blind sell-before-buy inverts intra-basket sequential price appreciation.",
    },
    "DEPENDENCY_AWARE_MARKET_TIMING": {
        "status": ScientificStatus.EXPERIMENTAL,
        "category": "MARKET",
        "role": "ACTIVE",
        "rationale": "Causal dependency-aware market order reordering certified via exact sequential simulator pricing and ActionBasketDependencyGraph.",
    },
    "TERMINAL_LIQUIDATION": {
        "status": ScientificStatus.VERIFIED_SOURCE,
        "category": "TERMINAL",
        "role": "DEFENSE_IN_DEPTH",
    },
    "PHASE_SHUTDOWN": {
        "status": ScientificStatus.VERIFIED_SOURCE,
        "category": "TERMINAL",
        "role": "DEFENSE_IN_DEPTH",
    },
    "LOCAL_WEED_DIG": {
        "status": ScientificStatus.QUARANTINED,
        "category": "ROUTE",
        "role": "QUARANTINED",
        "rationale": "Sunk-cost labor valuation and unverified 48-step downstream heuristic",
    },
    "RESOURCE_CONVERSION": {
        "status": ScientificStatus.QUARANTINED,
        "category": "RESOURCE",
        "role": "QUARANTINED",
        "rationale": "Dynamic inventory conversion and feed security DAG compiler pass; permanently quarantined per Phase 004B negative ITT.",
    },
    "EMERGENCY_FEED_PURCHASE": {
        "status": ScientificStatus.QUARANTINED,
        "category": "RESOURCE",
        "role": "QUARANTINED",
        "rationale": "Feed security rescue purchase; superseded by generalized emergency recovery.",
    },
    "DYNAMIC_SHADOW_HARVEST": {
        "status": ScientificStatus.EXPERIMENTAL,
        "category": "LABOR",
        "role": "ACTIVE",
        "rationale": "Coupled trajectory-preserving patch for mature crop salvage; candidate validated in Phase 006.",
    },
    "TERMINAL_HARVEST_SWEEP": {
        "status": ScientificStatus.EXPERIMENTAL,
        "category": "TERMINAL",
        "role": "ACTIVE",
        "rationale": "Coupled multi-worker terminal harvest salvage before step 718; candidate validated in Phase 006.",
    },
    "ROUTE_COMPRESSION": {
        "status": ScientificStatus.PLAUSIBLE_UNPROVEN,
        "category": "ROUTE",
        "role": "DEVELOPMENT",
        "rationale": "Task sequencing optimization to complete obligations in fewer movement steps.",
    },
    "CARGO_FERRY": {
        "status": ScientificStatus.PLAUSIBLE_UNPROVEN,
        "category": "LABOR",
        "role": "DEVELOPMENT",
        "rationale": "Auxiliary worker hauling to shed to unburden primary farmer field labor.",
    },
    "SHOP_ARBITRAGE": {
        "status": ScientificStatus.PLAUSIBLE_UNPROVEN,
        "category": "MARKET",
        "role": "DEVELOPMENT",
        "rationale": "Inter-turn price elasticity and town shop unlock interval arbitrage.",
    },
    "PRODUCTION_ARBITRAGE": {
        "status": ScientificStatus.PLAUSIBLE_UNPROVEN,
        "category": "RESOURCE",
        "role": "DEVELOPMENT",
        "rationale": "Cash -> input -> production -> output -> sale full lifecycle margin optimization.",
    },
    "TERMINAL_CONVERSION": {
        "status": ScientificStatus.PLAUSIBLE_UNPROVEN,
        "category": "TERMINAL",
        "role": "DEVELOPMENT",
        "rationale": "Endgame inventory liquidation conversion before step 718.",
    },
    "OPPONENT_PREEMPT_SELL": {
        "status": ScientificStatus.PLAUSIBLE_UNPROVEN,
        "category": "MARKET",
        "role": "DEVELOPMENT",
        "rationale": "Capture market clearing depth before anticipated rival supply dump.",
    },
    "EMERGENCY_RECOVERY": {
        "status": ScientificStatus.PLAUSIBLE_UNPROVEN,
        "category": "RESOURCE",
        "role": "DEVELOPMENT",
        "rationale": "Causal rescue for livestock starvation, wage default, or critical shed blockage.",
    },
    "TOWN_CYCLE": {
        "status": ScientificStatus.PLAUSIBLE_UNPROVEN,
        "category": "TIMING",
        "role": "DEVELOPMENT",
        "rationale": "Probabilistic signal tracking 72-step town demand refresh.",
    },
    "ASSET_HOLDING_VALUATION_TRIGGER": {
        "status": ScientificStatus.EXPERIMENTAL,
        "category": "MARKET",
        "role": "DEVELOPMENT",
        "rationale": "Phase 015 persistent asset-holding valuation trigger detecting uncommitted inventory windows without differential deltas",
    },
    "AUTONOMOUS_TRANCHE_ORDER_SYNTHESIZER": {
        "status": ScientificStatus.EXPERIMENTAL,
        "category": "MARKET",
        "role": "DEVELOPMENT",
        "rationale": "Phase 015 Autonomous Tranche Order Synthesizer with structural quantity anchors and exact counterfactual validation",
    },
}

ENABLED_FOUNDATION_MECHANISMS: Tuple[str, ...] = (
    "DEPENDENCY_AWARE_MARKET_TIMING",
    "TERMINAL_LIQUIDATION",
    "PHASE_SHUTDOWN",
)

QUARANTINED_MECHANISMS: Tuple[str, ...] = (
    "FRONTLOAD_ORDERS",
    "LOCAL_WEED_DIG",
    "DYNAMIC_SHADOW_HARVEST",
    "CARGO_FERRY_PRIORITY",
    "CARGO_FERRY",
    "OPPONENT_PREEMPT_SELL",
    "EMERGENCY_FEED_PURCHASE",
    "RESOURCE_CONVERSION",
    "TERMINAL_HARVEST_SWEEP",
    "TOWN_CYCLE",
    "SHOP_ARBITRAGE",
    "PRODUCTION_ARBITRAGE",
    "TERMINAL_CONVERSION",
    "EMERGENCY_RECOVERY",
    "ROUTE_COMPRESSION",
)


# -----------------------------------------------------------------------------
# 4. AEC CONFIGURATION PARAMETERS (§36)
# -----------------------------------------------------------------------------
@dataclass
class AECConfig:
    """Explicit parameters governing the AEC planning layer."""

    # Operational Mode (§33)
    operational_mode: str = "ROBUST_MODE"  # "ROBUST_MODE", "META_MODE", "RESEARCH_MODE"

    # Mechanism Boundaries & Governance
    enabled_mechanisms: Tuple[str, ...] = ENABLED_FOUNDATION_MECHANISMS
    quarantined_mechanisms: Tuple[str, ...] = QUARANTINED_MECHANISMS
    frozen_mode: bool = True         # EXP-AEC-001 frozen treatment isolation mode

    
    # Adaptive Horizons (§12, §22)
    short_horizon: int = 6           # Local / cheap events
    normal_horizon: int = 18         # Standard economic patches (12-24)
    extended_horizon: int = 36       # Long dependency or terminal consequence (24-48)
    
    # Bounded Search Budgets (§13, §21)
    max_opportunities: int = 16      # Maximum opportunities proposed per turn
    max_candidates: int = 8          # Maximum candidates after static pruning
    max_simulations: int = 8         # Maximum forward simulations executed
    
    # Event Sensitivity Thresholds (§6, §7)
    cash_deviation_threshold: float = 200.0  # Trigger E2 on material cash deviation
    shed_alarm_threshold: int = 95          # Trigger E3 when shed stock exceeds 95
    price_shock_relative: float = 0.25       # Trigger E4 when price shifts > 25%
    opponent_supply_shock_qty: int = 4       # Trigger E5 on sudden supply increase
    
    # Phase 015 Capabilities (§4, §11)
    enable_asset_holding_trigger: bool = False
    enable_tranche_synthesizer: bool = False

    # Phase 018 Repair A: candidate-funnel reservation (default OFF; isolated arm only)
    enable_funnel_reservation: bool = False
    funnel_reserved_fraction: float = 0.25

    # Phase 018 Repair B: boundary-safe quantity construction (default OFF; isolated arm only)
    enable_boundary_safe_quantities: bool = False

    # Phase 018 Repair A2: S7/S9 market-patch discrimination (default OFF; isolated arm only)
    enable_market_patch_discrimination: bool = False

    # Performance & Safety
    per_step_latency_limit_ms: float = 100.0
    fail_closed: bool = True
    
    # Backbone Specifications
    backbone_type: str = "v3"
    v3_tarball_path: str = "submission_Vj_kc_v3.tar.gz"
    v3_tarball_sha256: str = "845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943"

    def is_mechanism_enabled(self, mechanism: str) -> bool:
        """Check if a mechanism family is explicitly authorized."""
        return mechanism in self.enabled_mechanisms

    def is_family_live_eligible(self, family: str) -> bool:
        """Check if a family is cleared for live execution (enabled and not quarantined)."""
        return family in self.enabled_mechanisms and family not in self.quarantined_mechanisms

    @property
    def resource_conversion_enabled(self) -> bool:
        """Direct check enforcing that RESOURCE_CONVERSION remains strictly quarantined."""
        return self.is_family_live_eligible("RESOURCE_CONVERSION")


# -----------------------------------------------------------------------------
# 5. INTEGRATED BUILDS (Phase 010 Part XXIII & XXIV, Phase 015)
# -----------------------------------------------------------------------------
def build_robust_qualified_config() -> AECConfig:
    """Canonical AEC_ROBUST_QUALIFIED build containing only verified qualified mechanisms."""
    return AECConfig(
        operational_mode="ROBUST_MODE",
        enabled_mechanisms=ENABLED_FOUNDATION_MECHANISMS,
        quarantined_mechanisms=QUARANTINED_MECHANISMS,
        frozen_mode=True,
        enable_asset_holding_trigger=False,
        enable_tranche_synthesizer=False,
    )


def build_research_full_config() -> AECConfig:
    """Diagnostic AEC_RESEARCH_FULL build containing completed mechanisms with active gates."""
    return AECConfig(
        operational_mode="RESEARCH_MODE",
        enabled_mechanisms=ENABLED_FOUNDATION_MECHANISMS,
        quarantined_mechanisms=QUARANTINED_MECHANISMS,
        frozen_mode=False,
        enable_asset_holding_trigger=False,
        enable_tranche_synthesizer=False,
    )


def build_phase015_treatment_config(
    enable_trigger: bool = True,
    enable_synthesizer: bool = True,
) -> AECConfig:
    """Canonical Phase 015 treatment configuration with isolated capability switches."""
    enabled = list(ENABLED_FOUNDATION_MECHANISMS)
    if enable_trigger:
        enabled.append("ASSET_HOLDING_VALUATION_TRIGGER")
    if enable_synthesizer:
        enabled.append("AUTONOMOUS_TRANCHE_ORDER_SYNTHESIZER")
    return AECConfig(
        operational_mode="RESEARCH_MODE",
        enabled_mechanisms=tuple(enabled),
        quarantined_mechanisms=QUARANTINED_MECHANISMS,
        frozen_mode=False,
        enable_asset_holding_trigger=enable_trigger,
        enable_tranche_synthesizer=enable_synthesizer,
    )


def build_phase018_arm_a2_config() -> AECConfig:
    """Phase 018 Arm A2: Phase 015 treatment + funnel reservation ONLY.

    Isolation: differs from build_phase015_treatment_config() solely by
    enable_funnel_reservation=True. No quantity, trigger, representation, or
    evaluator change.
    """
    cfg = build_phase015_treatment_config()
    cfg.enable_funnel_reservation = True
    return cfg


def build_phase018_arm_b1_config() -> AECConfig:
    """Phase 018 Arm B1: Phase 015 treatment + boundary-safe quantities ONLY.

    Isolation: differs from build_phase015_treatment_config() solely by
    enable_boundary_safe_quantities=True. Reservation OFF, trigger unmodified,
    evaluator unchanged.
    """
    cfg = build_phase015_treatment_config()
    cfg.enable_boundary_safe_quantities = True
    return cfg


def build_phase018_arm_b2_s1_config() -> AECConfig:
    """Phase 018 Arm B2 leg S1: treatment + market-patch discrimination ONLY."""
    cfg = build_phase015_treatment_config()
    cfg.enable_market_patch_discrimination = True
    return cfg


def build_phase018_arm_b2_s1b_config() -> AECConfig:
    """Phase 018 Arm B2 leg S1B: treatment + discrimination + boundary menu."""
    cfg = build_phase015_treatment_config()
    cfg.enable_market_patch_discrimination = True
    cfg.enable_boundary_safe_quantities = True
    return cfg


def build_phase018_arm_b2_control_config() -> AECConfig:
    """Phase 018 Arm B2 control: foundation + discrimination (no tranche)."""
    cfg = build_robust_qualified_config()
    cfg.enable_market_patch_discrimination = True
    return cfg

