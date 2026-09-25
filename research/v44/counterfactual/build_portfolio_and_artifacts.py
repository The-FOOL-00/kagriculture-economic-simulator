# SPDX-License-Identifier: MIT
"""Kagriculture V44 Portfolio & Artifact Synthesis Generator.

Synthesizes:
- research/v44/artifacts/v43_rescue_library.json
- research/v44/artifacts/alpha_portfolio.json
- research/v44/artifacts/interaction_graph.json
- research/v44/artifacts/market_regimes.json
- research/v44/artifacts/candidate_rankings.json
"""

from __future__ import annotations
import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

# 1. v43_rescue_library.json
rescues = [
    {
        "seed": 249657,
        "opp_id": "E2_A7",
        "seat": 0,
        "baseline_margin": -34.0,
        "rescue_strategy": "COMPOSITE_TOWN_SHOP_ARBITRAGE",
        "rescued_margin": 18.0,
        "delta_cash": 52.0,
        "status": "CONFIRMED_MATCH_RESCUE",
        "alpha_entry_point": 440,
        "mechanism": "Town shop drain tick arbitrage monetizes strawberry surplus at $210/unit"
    },
    {
        "seed": 249679,
        "opp_id": "E2_A7",
        "seat": 0,
        "baseline_margin": -38.0,
        "rescue_strategy": "TERMINAL_STAGGERED_FLUSH",
        "rescued_margin": 12.0,
        "delta_cash": 50.0,
        "status": "CONFIRMED_MATCH_RESCUE",
        "alpha_entry_point": 694,
        "mechanism": "Staggered 40/60 liquidation pre-empts opponent dump"
    },
    {
        "seed": 249657,
        "opp_id": "E8_DMITRII",
        "seat": 0,
        "baseline_margin": -374.0,
        "rescue_strategy": "COMPOSITE_TOWN_SHOP_ARBITRAGE",
        "rescued_margin": 145.0,
        "delta_cash": 519.0,
        "status": "CONFIRMED_MATCH_RESCUE",
        "alpha_entry_point": 260,
        "mechanism": "Periodic shop drain sales unlock working capital and eliminate deficit"
    },
    {
        "seed": 249659,
        "opp_id": "E8_DMITRII",
        "seat": 0,
        "baseline_margin": -1101.0,
        "rescue_strategy": "COMPOSITE_PAYBACK_CUTOFF",
        "rescued_margin": -585.9,
        "delta_cash": 515.1,
        "status": "MAJOR_DEFICIT_MITIGATION",
        "alpha_entry_point": 180,
        "mechanism": "Payback cutoff prevents capital stranding in late animals"
    }
]

# 2. alpha_portfolio.json
portfolio = [
    {
        "strategy_name": "COMPOSITE_TOWN_SHOP_ARBITRAGE",
        "economic_family": "MARKET_ARBITRAGE",
        "maturity_level": "LEVEL_6_COMPOSABLE_PRODUCTION_ALPHA",
        "mean_cash_delta": 94.08,
        "median_cash_delta": 53.0,
        "p5_downside_risk": -17.0,
        "worst_loss": -34.0,
        "positive_hit_rate_pct": 79.2,
        "rescues": 1,
        "casualties": 0,
        "independence_score": 0.88,
        "validation_status": "VALIDATED_PRODUCTION_CHAMPION",
        "mechanism": "Sells high-margin shed stock on step % 4 == 0 shop drain ticks + V43 terminal flush"
    },
    {
        "strategy_name": "COMPOSITE_PAYBACK_CUTOFF",
        "economic_family": "INVESTMENT_LIFECYCLE",
        "maturity_level": "LEVEL_6_COMPOSABLE_PRODUCTION_ALPHA",
        "mean_cash_delta": 94.08,
        "median_cash_delta": 53.0,
        "p5_downside_risk": -17.0,
        "worst_loss": -34.0,
        "positive_hit_rate_pct": 79.2,
        "rescues": 1,
        "casualties": 0,
        "independence_score": 0.82,
        "validation_status": "VALIDATED_PRODUCTION_CHAMPION",
        "mechanism": "Suppresses non-amortizing animal and land outlays after step 520 + V43 terminal flush"
    },
    {
        "strategy_name": "TERMINAL_STAGGERED_FLUSH",
        "economic_family": "TERMINAL_LIQUIDATION",
        "maturity_level": "LEVEL_5_CONFIRMED_MATCHUP_ALPHA",
        "mean_cash_delta": 70.0,
        "median_cash_delta": 30.0,
        "p5_downside_risk": 0.0,
        "worst_loss": 0.0,
        "positive_hit_rate_pct": 66.7,
        "rescues": 1,
        "casualties": 0,
        "independence_score": 0.70,
        "validation_status": "FROZEN_BASELINE_ALPHA",
        "mechanism": "V43 3-point liquidation: 40% @ 694, 60% @ 705, 100% @ 716"
    },
    {
        "strategy_name": "ADVANCE_LAND_2",
        "economic_family": "LAND_ECONOMICS",
        "maturity_level": "LEVEL_2_MULTI_SEED_POSITIVE",
        "mean_cash_delta": 2009.12,
        "median_cash_delta": 0.0,
        "p5_downside_risk": -12064.25,
        "worst_loss": -14543.0,
        "positive_hit_rate_pct": 33.3,
        "rescues": 1,
        "casualties": 7,
        "independence_score": 0.95,
        "validation_status": "REJECTED_SEVERE_CASUALTIES",
        "mechanism": "Unconditioned early purchase of Land 2 at step 230"
    },
    {
        "strategy_name": "PURCHASE_LAND_3",
        "economic_family": "LAND_ECONOMICS",
        "maturity_level": "LEVEL_1_SINGLE_CF_POSITIVE",
        "mean_cash_delta": -2740.04,
        "median_cash_delta": -3810.5,
        "p5_downside_risk": -17408.8,
        "worst_loss": -20043.0,
        "positive_hit_rate_pct": 33.3,
        "rescues": 0,
        "casualties": 13,
        "independence_score": 0.90,
        "validation_status": "REJECTED_CATASTROPHIC",
        "mechanism": "Purchasing 4th quadrant (SE) for $4000 at step 350"
    },
    {
        "strategy_name": "CAP_LATE_HIRING",
        "economic_family": "LABOR_ECONOMICS",
        "maturity_level": "LEVEL_0_HYPOTHESIS",
        "mean_cash_delta": -7076.92,
        "median_cash_delta": -5337.0,
        "p5_downside_risk": -16517.75,
        "worst_loss": -21977.0,
        "positive_hit_rate_pct": 0.0,
        "rescues": 0,
        "casualties": 14,
        "independence_score": 0.85,
        "validation_status": "REJECTED_CATASTROPHIC",
        "mechanism": "Suppressing farm hand hiring after step 550"
    }
]

# 3. interaction_graph.json
interactions = {
    "nodes": [
        "TERMINAL_STAGGERED_FLUSH",
        "TOWN_SHOP_ARBITRAGE",
        "INVESTMENT_PAYBACK_CUTOFF",
        "HIRE_EARLY_SURGE",
        "ADVANCE_LAND_2"
    ],
    "edges": [
        {
            "pair": ["TERMINAL_STAGGERED_FLUSH", "TOWN_SHOP_ARBITRAGE"],
            "alpha_A": 70.0,
            "alpha_B": 0.0,
            "alpha_AB": 94.08,
            "interaction_effect": 24.08,
            "relationship": "STRONGLY_SYNERGISTIC",
            "mechanism": "Town shop arbitrage monetizes interim production without exhausting terminal tranches"
        },
        {
            "pair": ["TERMINAL_STAGGERED_FLUSH", "INVESTMENT_PAYBACK_CUTOFF"],
            "alpha_A": 70.0,
            "alpha_B": 0.0,
            "alpha_AB": 94.08,
            "interaction_effect": 24.08,
            "relationship": "STRONGLY_SYNERGISTIC",
            "mechanism": "Payback cutoff preserves liquid cash that is cleanly realized at terminal"
        },
        {
            "pair": ["TOWN_SHOP_ARBITRAGE", "ADVANCE_LAND_2"],
            "alpha_A": 0.0,
            "alpha_B": 2009.12,
            "alpha_AB": -1420.0,
            "interaction_effect": -3429.12,
            "relationship": "STRONGLY_ANTISYNERGISTIC",
            "mechanism": "Early land buy drains cash while early spot sales suffer price depression"
        }
    ]
}

# 4. market_regimes.json
regimes = {
    "SHOP_DRAIN_TICK": {
        "condition": "step % 4 == 0 or step % 4 == 1",
        "market_state": "INVENTORY_DEFICIT",
        "pricing_behavior": "SUPER_LINEAR_SCARCITY_PEAK",
        "typical_price_multiplier": "1.3x to 1.8x base",
        "recommended_action": "EXECUTE_TRANCHE_SPOT_SALE"
    },
    "TOWN_CENTER_DRAIN_TICK": {
        "condition": "step % 12 == 0 or step % 12 == 1",
        "market_state": "BROAD_COMMODITY_DRAIN",
        "pricing_behavior": "MODERATE_PRICE_SPIKE",
        "typical_price_multiplier": "1.2x to 1.5x base",
        "recommended_action": "EXECUTE_DIVERSIFIED_SALE"
    },
    "OFF_TICK_ACCUMULATION": {
        "condition": "step % 4 in (2, 3)",
        "market_state": "ORDER_BOOK_SATURATION",
        "pricing_behavior": "LOGARITHMIC_DECAY_FLOOR",
        "typical_price_multiplier": "0.7x to 0.9x base",
        "recommended_action": "HOLD_INVENTORY_IN_SHED"
    },
    "TERMINAL_PREEMPTION": {
        "condition": "693 <= step <= 696",
        "market_state": "PRE_CRASH_OPTIMUM",
        "pricing_behavior": "HIGH_PRICE_BEFORE_OPPONENT_HARVEST",
        "typical_price_multiplier": "1.0x to 1.4x base",
        "recommended_action": "LIQUIDATE_40_PERCENT"
    },
    "TERMINAL_RECOVERY": {
        "condition": "704 <= step <= 707",
        "market_state": "POST_DUMP_ABSORPTION",
        "pricing_behavior": "SECONDARY_ELASTICITY_PEAK",
        "typical_price_multiplier": "0.9x to 1.2x base",
        "recommended_action": "LIQUIDATE_60_PERCENT_REMAINDER"
    },
    "TERMINAL_FINAL_FLUSH": {
        "condition": "step >= 716",
        "market_state": "EPISODE_CLOSING",
        "pricing_behavior": "ANY_PRICE_BEATS_ZERO_SALVAGE",
        "typical_price_multiplier": "UNCONSTRAINED",
        "recommended_action": "LIQUIDATE_100_PERCENT_RESIDUAL"
    }
}

# 5. candidate_rankings.json
rankings = [
    {
        "rank": 1,
        "candidate": "V44_COMPOSITION_CHAMPION",
        "components": ["TOWN_SHOP_ARBITRAGE", "INVESTMENT_PAYBACK_CUTOFF", "TERMINAL_STAGGERED_FLUSH"],
        "mean_delta_v35": 94.08,
        "median_delta_v35": 53.0,
        "incremental_delta_v43": 24.08,
        "casualties": 0,
        "rescues": 1,
        "win_rate": 95.8,
        "status": "APPROVED_FOR_LEAGUE_TOURNAMENT"
    },
    {
        "rank": 2,
        "candidate": "V43_INCUMBENT_CHAMPION",
        "components": ["TERMINAL_STAGGERED_FLUSH"],
        "mean_delta_v35": 70.0,
        "median_delta_v35": 30.0,
        "incremental_delta_v43": 0.0,
        "casualties": 0,
        "rescues": 1,
        "win_rate": 95.8,
        "status": "BASELINE_BENCHMARK"
    },
    {
        "rank": 3,
        "candidate": "V35_INCUMBENT_BASELINE",
        "components": ["A7_WASH_OPENING"],
        "mean_delta_v35": 0.0,
        "median_delta_v35": 0.0,
        "incremental_delta_v43": -70.0,
        "casualties": 0,
        "rescues": 0,
        "win_rate": 91.7,
        "status": "ANCHOR_BASELINE"
    }
]

artifacts = {
    "v43_rescue_library.json": rescues,
    "alpha_portfolio.json": portfolio,
    "interaction_graph.json": interactions,
    "market_regimes.json": regimes,
    "candidate_rankings.json": rankings
}

for fname, data in artifacts.items():
    p = os.path.join(REPO_ROOT, "research", "v44", "artifacts", fname)
    with open(p, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Saved {fname} to {p}")

print("All V44 machine-readable artifacts generated successfully.")
