# SPDX-License-Identifier: MIT
"""V46 Phase 4 & 5: Macro Route Synthesizer & Diverse Optima Search.

Generates and optimizes a diverse portfolio of structurally distinct macro strategies:
- Route A: Balanced Dual-Livestock (Cow + Sheep + Strawberry)
- Route B: Dairy Intensive (10 Cows, High Milk Continuous Compounding)
- Route C: Textile / Wool Intensive (8 Sheep, Low Care, High Fiber Yield)
- Route D: Melon Horticulture (High-Yield Batch Crop, Day 24-28 Peak Realization)
- Route E: Strawberry Perennial (Continuous Picking Cycles, High Value Density)
- Route F: Rapid Land Expansion (Fast 4-Quadrant Unlocking, Scale Labor)
- Route G: Capital-Lean Labor Minimalist (High Margin, Zero Idle Wage Waste)
- Route H: Dual-Livestock Early Amortization (Day 4 Pastures, Aggressive Compounding)
- Plus mutated parameter configurations for high-throughput screening.
"""

from __future__ import annotations
import copy
import json
import os
import sys
from typing import Any, Dict, List, Tuple
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v46.optimizer.macro_route import MacroRouteConfig, MacroRouteExecutor


def generate_candidate_route_library() -> Dict[str, MacroRouteConfig]:
    """Generates a structured library of diverse macro routes across all economic dimensions."""
    routes: Dict[str, MacroRouteConfig] = {}

    # 1. Route A: Balanced Compound (V44 Economic Dual-Livestock Archetype)
    routes["ROUTE_A_BALANCED_COMPOUND"] = MacroRouteConfig(
        route_id="ROUTE_A_BALANCED_COMPOUND",
        name="Balanced Dual-Livestock Compound",
        description="Standard V44 economic baseline: 6 cows, 3 sheep, wheat/strawberry, step 520 cutoff, staggered 693/704/716 liquidation.",
        opening_wash=(25, 25),
        land_purchase_days=[0, 8, 16],
        max_land_quadrants=4,
        max_hands=20,
        daily_hire_ceiling=2,
        target_cows=6,
        target_sheep=3,
        target_geese=0,
        cow_buy_day=2,
        sheep_buy_day=4,
        primary_crop="WHEAT",
        primary_crop_count=16,
        secondary_crop="STRAWBERRY",
        secondary_crop_count=8,
        payback_cutoff_step=520,
        liquidation_schedule={693: 0.5, 704: 0.5, 716: 1.0}
    )

    # 2. Route B: Dairy Intensive (Cow Heavy)
    routes["ROUTE_B_DAIRY_INTENSIVE"] = MacroRouteConfig(
        route_id="ROUTE_B_DAIRY_INTENSIVE",
        name="Dairy Capital Intensive",
        description="Pure dairy specialization: 10 cows, 0 sheep, heavy wheat feeding, maximizes high-value milk flow.",
        opening_wash=(25, 25),
        land_purchase_days=[0, 6, 14],
        max_land_quadrants=4,
        max_hands=24,
        daily_hire_ceiling=2,
        target_cows=10,
        target_sheep=0,
        target_geese=0,
        cow_buy_day=1,
        sheep_buy_day=99,
        primary_crop="WHEAT",
        primary_crop_count=22,
        secondary_crop="CARROT",
        secondary_crop_count=4,
        payback_cutoff_step=500,
        liquidation_schedule={693: 0.5, 704: 0.5, 716: 1.0}
    )

    # 3. Route C: Textile / Wool Intensive (Sheep Heavy)
    routes["ROUTE_C_TEXTILE_SHEEP"] = MacroRouteConfig(
        route_id="ROUTE_C_TEXTILE_SHEEP",
        name="Textile Wool Specialist",
        description="Wool specialization: 8 sheep, 2 cows, low feed requirement, high margin wool yield.",
        opening_wash=(25, 25),
        land_purchase_days=[0, 8, 16],
        max_land_quadrants=4,
        max_hands=18,
        daily_hire_ceiling=2,
        target_cows=2,
        target_sheep=8,
        target_geese=0,
        cow_buy_day=6,
        sheep_buy_day=2,
        primary_crop="WHEAT",
        primary_crop_count=14,
        secondary_crop="STRAWBERRY",
        secondary_crop_count=6,
        payback_cutoff_step=520,
        liquidation_schedule={693: 0.5, 704: 0.5, 716: 1.0}
    )

    # 4. Route D: Melon Horticulture (Crop Heavy)
    routes["ROUTE_D_MELON_HORTICULTURE"] = MacroRouteConfig(
        route_id="ROUTE_D_MELON_HORTICULTURE",
        name="High-Yield Melon Horticulture",
        description="Cash crop specialization: 24 melon tiles, 2 cows for organic manure, massive day 24-28 batch liquidation.",
        opening_wash=(25, 25),
        land_purchase_days=[0, 4, 10],
        max_land_quadrants=4,
        max_hands=22,
        daily_hire_ceiling=3,
        target_cows=2,
        target_sheep=0,
        target_geese=0,
        cow_buy_day=4,
        sheep_buy_day=99,
        primary_crop="MELON",
        primary_crop_count=24,
        secondary_crop="CARROT",
        secondary_crop_count=6,
        payback_cutoff_step=540,
        liquidation_schedule={690: 0.6, 705: 0.6, 716: 1.0}
    )

    # 5. Route E: Strawberry Perennial (Perennial Picking)
    routes["ROUTE_E_STRAWBERRY_PERENNIAL"] = MacroRouteConfig(
        route_id="ROUTE_E_STRAWBERRY_PERENNIAL",
        name="Perennial Strawberry Focus",
        description="Perennial fruit specialization: 20 strawberry plots, day 10 harvest unlock with recurring picking cycles.",
        opening_wash=(25, 25),
        land_purchase_days=[0, 6, 12],
        max_land_quadrants=4,
        max_hands=22,
        daily_hire_ceiling=2,
        target_cows=3,
        target_sheep=2,
        target_geese=0,
        cow_buy_day=3,
        sheep_buy_day=5,
        primary_crop="STRAWBERRY",
        primary_crop_count=20,
        secondary_crop="WHEAT",
        secondary_crop_count=10,
        payback_cutoff_step=520,
        liquidation_schedule={693: 0.5, 704: 0.5, 716: 1.0}
    )

    # 6. Route F: Fast Land Scale Expansion
    routes["ROUTE_F_FAST_LAND_SCALE"] = MacroRouteConfig(
        route_id="ROUTE_F_FAST_LAND_SCALE",
        name="Rapid 4-Quadrant Scale Expansion",
        description="Early land acquisition on days 0, 4, 8, max labor ceiling (28 hands), large diversified farm footprint.",
        opening_wash=(25, 25),
        land_purchase_days=[0, 4, 8],
        max_land_quadrants=4,
        max_hands=28,
        daily_hire_ceiling=3,
        target_cows=6,
        target_sheep=4,
        target_geese=0,
        cow_buy_day=2,
        sheep_buy_day=4,
        primary_crop="WHEAT",
        primary_crop_count=20,
        secondary_crop="STRAWBERRY",
        secondary_crop_count=12,
        payback_cutoff_step=520,
        liquidation_schedule={693: 0.5, 704: 0.5, 716: 1.0}
    )

    # 7. Route G: Capital-Lean Labor Minimalist
    routes["ROUTE_G_LEAN_LABOR_DEFENSE"] = MacroRouteConfig(
        route_id="ROUTE_G_LEAN_LABOR_DEFENSE",
        name="Capital-Lean Labor Minimalist",
        description="Low overhead: 12 hands max, compact 2-quadrant operation, zero wage bleed, high net liquidity retention.",
        opening_wash=(25, 25),
        land_purchase_days=[0],
        max_land_quadrants=2,
        max_hands=12,
        daily_hire_ceiling=1,
        target_cows=4,
        target_sheep=2,
        target_geese=0,
        cow_buy_day=2,
        sheep_buy_day=4,
        primary_crop="WHEAT",
        primary_crop_count=12,
        secondary_crop="STRAWBERRY",
        secondary_crop_count=4,
        payback_cutoff_step=480,
        liquidation_schedule={693: 0.5, 704: 0.5, 716: 1.0}
    )

    # 8. Route H: Early Amortization Sprint (High Compounding)
    routes["ROUTE_H_EARLY_AMORTIZATION"] = MacroRouteConfig(
        route_id="ROUTE_H_EARLY_AMORTIZATION",
        name="Early Amortization Livestock Sprint",
        description="Aggressive day 1-2 cow and sheep stocking to maximize yield compounding across days 8..28.",
        opening_wash=(30, 30),
        land_purchase_days=[0, 6, 14],
        max_land_quadrants=4,
        max_hands=22,
        daily_hire_ceiling=2,
        target_cows=7,
        target_sheep=3,
        target_geese=0,
        cow_buy_day=1,
        sheep_buy_day=2,
        primary_crop="WHEAT",
        primary_crop_count=18,
        secondary_crop="STRAWBERRY",
        secondary_crop_count=6,
        payback_cutoff_step=500,
        liquidation_schedule={693: 0.5, 704: 0.5, 716: 1.0}
    )

    # Generate perturbed variants to reach 16 distinct candidate routes
    base_keys = list(routes.keys())
    for k in base_keys:
        base_cfg = routes[k]
        # Mutation 1: Earlier liquidation variant (pre-empt aggressive dumpers)
        var1 = copy.deepcopy(base_cfg)
        var1.route_id = f"{base_cfg.route_id}_EARLY_LIQ"
        var1.name = f"{base_cfg.name} (Early Liquidation)"
        var1.liquidation_schedule = {688: 0.4, 698: 0.5, 714: 1.0}
        routes[var1.route_id] = var1

    return routes


if __name__ == "__main__":
    routes = generate_candidate_route_library()
    print(f"Generated {len(routes)} structurally distinct candidate macro routes:")
    for rid, r in routes.items():
        print(f"  {rid:<35}: {r.name}")

    out_file = os.path.join(os.path.dirname(__file__), "strategy_portfolio.json")
    routes_dict = {rid: r.__dict__ for rid, r in routes.items()}
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(routes_dict, f, indent=2)
    print(f"Saved candidate route library to: {out_file}")
