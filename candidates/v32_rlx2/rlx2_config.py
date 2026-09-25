# SPDX-License-Identifier: MIT
"""Kagriculture V32 RL-X2 Configuration and Constants.

Frozen dependencies, simulation parameters, economic constants, and cohort ranges.
"""

from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Simulation parameters
ENGINE_VERSION = "1.32.7"
EPISODE_STEPS = 720
LAST_ACT_STEP = 718
BOARD_SIZE = 10
SHED_CAPACITY = 100
TURNS_PER_DAY = 24
MACRO_STEP_INTERVAL = 4  # Aligned with town consumption ticks (step % 4 == 0)

# Economic constants
PRODUCTS: Tuple[str, ...] = (
    "WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
    "EGG", "MILK", "WOOL", "FERTILIZER"
)

CROPS: Tuple[str, ...] = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")
ANIMALS: Tuple[str, ...] = ("GOOSE", "COW", "SHEEP")

SEED_PRICES: Dict[str, int] = {
    "WHEAT": 10,
    "CARROT": 20,
    "TOMATO": 50,
    "STRAWBERRY": 100,
    "MELON": 80,
}

ANIMAL_COSTS: Dict[str, int] = {
    "GOOSE": 300,
    "COW": 600,
    "SHEEP": 500,
}

ANIMAL_STRUCTURES: Dict[str, str] = {
    "GOOSE": "COOP",
    "COW": "PASTURE",
    "SHEEP": "PASTURE",
}

ANIMAL_PRODUCTS: Dict[str, str] = {
    "GOOSE": "EGG",
    "COW": "MILK",
    "SHEEP": "WOOL",
}

LAND_PRICES: Tuple[int, ...] = (1000, 2000, 4000)

MOVES: Dict[str, Tuple[int, int]] = {
    "NORTH": (0, -1),
    "SOUTH": (0, 1),
    "EAST": (1, 0),
    "WEST": (-1, 0),
}

# Fibonacci hiring schedule cost: cost = fib(hires_today)
def fib_hire_cost(hires_today: int) -> int:
    a, b = 1, 1
    for _ in range(hires_today):
        a, b = b, a + b
    return a

# Seed Cohorts
V32_TRAIN: Tuple[int, int] = (249635, 249674)       # 40 seeds (249635..249674)
V32_DEV_HIST: Tuple[int, int] = (249675, 249684)    # 10 seeds (249675..249684)
V32_DEV_FRESH: Tuple[int, int] = (249685, 249694)   # 10 seeds (249685..249694)
V32_DEV: Tuple[int, int] = (249675, 249694)         # 20 seeds total

# Absolute protected holdouts — NEVER TOUCH
REFUSED_HOLDOUTS: List[Tuple[int, int]] = [
    (214200, 214249),       # GATE0 virgin holdout
    (340000, 340049),       # EXP-AEC-001 consumed
    (340050, 340050 + 39),  # V29 consumed
    (340090, 340199),       # Protected remainder
    (340200, 340249),       # EXP-AEC-002 consumed
    (340250, 340299),       # EXP-AEC-003 consumed
    (340300, 340349),       # EXP-AEC-004 retired
    (249695, 249734),       # V32-CONFIRM virgin holdout
]

# Protected incumbent specification
A7_PATH = os.path.join(REPO_ROOT, "candidates", "v30_a7_standalone", "main.py")
A7_EXPECTED_SHA256 = "51c1d25245f68dd8de66b355f2ad6ca1d79de8af02efed521a5a82f7be69ce3f"

@dataclass
class RLX2Config:
    """Runtime configuration for RL-X2 agent and experiments."""
    macro_interval: int = MACRO_STEP_INTERVAL
    state_tier: str = "S2"  # "S0", "S1", "S2", "S3"
    reward_mode: str = "R1"  # "R0": terminal cash, "R1": A7 delta, "R3": potential
    min_cash_buffer: float = 30.0
    wage_runway_stress_threshold: float = 2.0  # days
    spot_price_min_sell: float = 2.0
    action_space_size: int = 10
    lr: float = 3e-4
    gamma: float = 0.99
    gae_lambda: float = 0.95
    clip_epsilon: float = 0.2
    vf_coef: float = 0.5
    ent_coef: float = 0.01
    max_grad_norm: float = 0.5
    device: str = "cpu"
