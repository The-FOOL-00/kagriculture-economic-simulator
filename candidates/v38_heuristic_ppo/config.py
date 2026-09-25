# SPDX-License-Identifier: MIT
"""Kagriculture V38 Configuration and Governance Constants."""

from __future__ import annotations
import os
import sys

# Directory Paths
V38_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(V38_DIR, "..", ".."))
SCRATCH_DIR = os.path.join(REPO_ROOT, "scratch", "v38")

# Quarantine Enforcement: These ranges must NEVER be used.
QUARANTINED_SEEDS = [
    (214200, 214249),  # Virgin Holdout
    (340090, 340199),  # Protected Remainder
    (249695, 249734),  # V32 Confirmation Holdout
]

# Explicit Safe Seed Allowlists
SAFE_TRAIN_SEEDS = list(range(249635, 249650))  # 15 seeds (V32_TRAIN sub-range)
SAFE_DEV_SEEDS = list(range(249675, 249685))    # 10 seeds (V36 Independent Validation cohort)
SAFE_FRESH_SEEDS = list(range(249685, 249695))  # 10 seeds (Strictly held-out fresh cohort < 249695)

def assert_seed_safe(seed: int) -> None:
    """Raises ValueError if seed belongs to any quarantined range."""
    for lo, hi in QUARANTINED_SEEDS:
        if lo <= seed <= hi:
            raise ValueError(f"CRITICAL GOVERNANCE VIOLATION: Seed {seed} is strictly quarantined ({lo}..{hi})!")

# Verify allowlists at import time
for s in SAFE_TRAIN_SEEDS + SAFE_DEV_SEEDS + SAFE_FRESH_SEEDS:
    assert_seed_safe(s)

# Economic Constants
PRODUCTS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER")
SEED_PRICES = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80}
ANIMAL_COSTS = {"GOOSE": 300, "COW": 400, "SHEEP": 500}
ANIMAL_STRUCTURES = {"GOOSE": "COOP", "COW": "PASTURE", "SHEEP": "PASTURE"}
LAND_PRICES = (1000, 2000, 4000)

EPISODE_STEPS = 720
DAYS_PER_EPISODE = 30
HOURS_PER_DAY = 24
TOWN_CYCLE = 4
SHOP_UNLOCK_CYCLE = 72

# Macro Action Vocabulary
MACRO_ACTIONS = {
    0: "TRUST_HEURISTIC",
    1: "EXPAND_LAND",
    2: "HIRE_WORKER",
    3: "ANIMAL_EXPANSION",
    4: "CROP_EXPANSION",
    5: "SHOP_SUPPLY",
    6: "SELL_INVENTORY",
    7: "HOLD_INVENTORY",
    8: "MARKET_OPPORTUNITY",
    9: "LIQUIDITY_PROTECT",
    10: "RECOVERY",
}
NUM_MACRO_ACTIONS = len(MACRO_ACTIONS)

# Liquidity Safety Floor
MIN_LIQUID_CASH_BUFFER = 150.0  # Cash reserve that must never be breached by non-emergency interventions
WAGE_PER_HAND_PER_DAY = 10.0

# Intervention Control
DEFAULT_MACRO_HORIZON = 4  # Default H-step duration for bounded macro interventions
MAX_CONSECUTIVE_INTERVENTIONS = 3  # Cooldown limit to prevent open-loop drift
