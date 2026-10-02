# SPDX-License-Identifier: MIT
"""V46 Phase 13: Synthetic Adversarial Strategy Population Generator.

Generates a broad, stress-testing population of synthetic opponents across 5 difficulty tiers:
1. Elite (Ultra-high compounding, tight multi-crop and livestock optimization)
2. Strong (Fast land expansion, aggressive livestock or melon specialization)
3. Moderate (Standard balanced farming, steady growth)
4. Weird (Atypical allocations: 0 land expansion, pure goose swarm, extreme carrot focus)
5. Adversarial (Hostile early price depressors, aggressive front-runners, liquidity bleeders)
"""

from __future__ import annotations
import copy
import json
import os
import sys
from typing import Any, Callable, Dict, List, Optional
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v46.optimizer.macro_route import MacroRouteConfig, MacroRouteExecutor


def generate_adversarial_population() -> Dict[str, MacroRouteConfig]:
    """Generates synthetic adversarial opponent profiles across all tiers."""
    adversaries: Dict[str, MacroRouteConfig] = {}

    # Tier 1: Elite Adversaries
    adversaries["ADV_ELITE_DUAL_SCALE"] = MacroRouteConfig(
        route_id="ADV_ELITE_DUAL_SCALE",
        name="Elite Dual Scale Compounding",
        description="Elite rapid expansion: 4 quadrants by day 8, 28 hands, 8 cows, 4 sheep, aggressive wheat & strawberry.",
        opening_wash=(25, 25),
        land_purchase_days=[0, 4, 8],
        max_land_quadrants=4,
        max_hands=28,
        target_cows=8,
        target_sheep=4,
        cow_buy_day=2,
        sheep_buy_day=3,
        primary_crop="WHEAT",
        primary_crop_count=24,
        secondary_crop="STRAWBERRY",
        secondary_crop_count=12,
        payback_cutoff_step=520,
        liquidation_schedule={692: 0.5, 703: 0.5, 715: 1.0}
    )

    # Tier 2: Strong Adversaries
    adversaries["ADV_STRONG_MELON_CRUSH"] = MacroRouteConfig(
        route_id="ADV_STRONG_MELON_CRUSH",
        name="Strong Melon Crusher",
        description="Massive melon farm (28 plots), 2 cows, sells 100% of melons at step 691 crashing market prices.",
        opening_wash=(20, 20),
        land_purchase_days=[0, 4, 10],
        max_land_quadrants=4,
        max_hands=24,
        target_cows=2,
        target_sheep=0,
        cow_buy_day=3,
        sheep_buy_day=99,
        primary_crop="MELON",
        primary_crop_count=28,
        secondary_crop="WHEAT",
        secondary_crop_count=8,
        payback_cutoff_step=540,
        liquidation_schedule={691: 0.8, 714: 1.0}
    )

    adversaries["ADV_STRONG_DAIRY_FLOOD"] = MacroRouteConfig(
        route_id="ADV_STRONG_DAIRY_FLOOD",
        name="Strong Dairy Flooder",
        description="12 cows, high wheat feed, sells milk every 24 steps suppressing milk prices permanently.",
        opening_wash=(25, 25),
        land_purchase_days=[0, 6, 12],
        max_land_quadrants=4,
        max_hands=26,
        target_cows=12,
        target_sheep=0,
        cow_buy_day=1,
        sheep_buy_day=99,
        primary_crop="WHEAT",
        primary_crop_count=26,
        secondary_crop="CARROT",
        secondary_crop_count=4,
        payback_cutoff_step=500,
        liquidation_schedule={480: 0.3, 552: 0.3, 624: 0.3, 693: 0.5, 716: 1.0}
    )

    # Tier 3: Moderate Adversaries
    adversaries["ADV_MOD_BALANCED_GRAZIER"] = MacroRouteConfig(
        route_id="ADV_MOD_BALANCED_GRAZIER",
        name="Moderate Balanced Grazier",
        description="Moderate paced farming: 5 cows, 2 sheep, standard land expansion, step 716 single dump.",
        opening_wash=(25, 25),
        land_purchase_days=[0, 10, 20],
        max_land_quadrants=3,
        max_hands=18,
        target_cows=5,
        target_sheep=2,
        cow_buy_day=4,
        sheep_buy_day=6,
        primary_crop="WHEAT",
        primary_crop_count=14,
        secondary_crop="CARROT",
        secondary_crop_count=6,
        payback_cutoff_step=520,
        liquidation_schedule={716: 1.0}
    )

    # Tier 4: Weird Adversaries
    adversaries["ADV_WEIRD_GOOSE_SWARM"] = MacroRouteConfig(
        route_id="ADV_WEIRD_GOOSE_SWARM",
        name="Weird Goose Swarm",
        description="Atypical goose focus: 10 coops, geese egg production from day 4, low capital requirements.",
        opening_wash=(10, 10),
        land_purchase_days=[0],
        max_land_quadrants=2,
        max_hands=14,
        target_cows=0,
        target_sheep=0,
        target_geese=10,
        cow_buy_day=99,
        sheep_buy_day=99,
        primary_crop="WHEAT",
        primary_crop_count=16,
        secondary_crop="CARROT",
        secondary_crop_count=4,
        payback_cutoff_step=450,
        liquidation_schedule={693: 0.5, 716: 1.0}
    )

    # Tier 5: Hostile Adversarial
    adversaries["ADV_HOSTILE_EARLY_PREEMPTOR"] = MacroRouteConfig(
        route_id="ADV_HOSTILE_EARLY_PREEMPTOR",
        name="Hostile Early Pre-emptor",
        description="Pre-empts market at step 685 (8 steps before standard V44 step 693), dumping all strawberry and milk stock.",
        opening_wash=(25, 25),
        land_purchase_days=[0, 8, 16],
        max_land_quadrants=4,
        max_hands=20,
        target_cows=6,
        target_sheep=3,
        cow_buy_day=2,
        sheep_buy_day=4,
        primary_crop="WHEAT",
        primary_crop_count=16,
        secondary_crop="STRAWBERRY",
        secondary_crop_count=8,
        payback_cutoff_step=520,
        liquidation_schedule={685: 0.7, 700: 0.7, 714: 1.0}
    )

    return adversaries


if __name__ == "__main__":
    advs = generate_adversarial_population()
    print(f"Generated {len(advs)} synthetic adversarial profiles across 5 tiers:")
    for aid, a in advs.items():
        print(f"  {aid:<30}: {a.name} ({a.description[:60]}...)")
    out_dir = os.path.dirname(__file__)
    out_file = os.path.join(out_dir, "synthetic_adversaries.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({aid: a.__dict__ for aid, a in advs.items()}, f, indent=2)
    print(f"Saved synthetic adversary configs to: {out_file}")
