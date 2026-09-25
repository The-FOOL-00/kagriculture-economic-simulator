# SPDX-License-Identifier: MIT
"""Kagriculture V32 P10 Configuration & Constants.

Defines P10 runtime parameters, regime thresholds, counterfactual settings,
and risk budgets.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

PRODUCTS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER")
SEED_PRICES = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80}
ANIMAL_COSTS = {"GOOSE": 300, "COW": 400, "SHEEP": 500}
ANIMAL_STRUCTURES = {"GOOSE": "COOP", "COW": "PASTURE", "SHEEP": "PASTURE"}
LAND_PRICES = (1000, 2000, 4000)
MOVES = {"NORTH": (0, -1), "SOUTH": (0, 1), "EAST": (1, 0), "WEST": (-1, 0)}

# Seed governance
DEV_SEEDS_HISTORICAL = list(range(249675, 249685))  # Seeds 249675-249684 (P9 regression panel)
DEV_SEEDS_FRESH = list(range(249685, 249695))       # Seeds 249685-249694 (P10 fresh validation)
ALL_DEV_SEEDS = DEV_SEEDS_HISTORICAL + DEV_SEEDS_FRESH


@dataclass
class P10Config:
    # Residual Master Toggle
    residual_enabled: bool = False  # Default: False (Strict A7 Incumbent Parity)
    
    # Active Residual IDs to evaluate (empty when disabled)
    active_residual_ids: List[str] = field(default_factory=list)
    
    # Counterfactual Evaluation Settings
    enable_online_counterfactual: bool = False
    counterfactual_horizon_short: int = 4
    counterfactual_horizon_medium: int = 24
    counterfactual_horizon_long: int = 72
    
    # Acceptance Gating Thresholds
    min_paired_delta: float = 100.0        # Minimum expected value gain ($)
    max_worst_case_loss: float = 50.0      # Maximum allowed worst-case tested regression ($)
    min_confidence: float = 0.90
    
    # Board & Simulator constants
    board_size: int = 10
    episode_steps: int = 720
    turns_per_day: int = 24
    max_market_orders: int = 10
    shed_capacity: int = 100
