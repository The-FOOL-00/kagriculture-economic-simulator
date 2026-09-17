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
        "rationale": "Dynamic inventory conversion and feed security DAG compiler pass; architecturally unblocked, pending micro-validation.",
    },
    "EMERGENCY_FEED_PURCHASE": {
        "status": ScientificStatus.QUARANTINED,
        "category": "RESOURCE",
        "role": "QUARANTINED",
        "rationale": "Feed security rescue purchase; architecturally unblocked, pending micro-validation.",
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
    "OPPONENT_PREEMPT_SELL",
    "EMERGENCY_FEED_PURCHASE",
    "RESOURCE_CONVERSION",
    "TERMINAL_HARVEST_SWEEP",
    "TOWN_CYCLE",
)


# -----------------------------------------------------------------------------
# 4. AEC CONFIGURATION PARAMETERS (§36)
# -----------------------------------------------------------------------------
@dataclass
class AECConfig:
    """Explicit parameters governing the AEC planning layer."""
    
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

