# SPDX-License-Identifier: MIT
"""V45 Market Response & Price Impact Empirical Modeling.

Quantifies non-linear price impact, order slippage, market depth, and recovery dynamics
for selling quantities Q in [1, 2, 4, 8, 16, 32] across commodities and market regimes:
- THIN_MARKET vs CROWDED_MARKET
- DRAIN_TICK vs OFF_TICK
- MIDGAME vs TERMINAL_WINDOW

Outputs:
- research/v45/artifacts/market_regimes.json
- research/v45/artifacts/price_impact_model.json
"""

from __future__ import annotations
import json
import os
import sys
import time
from typing import Dict, List
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import kaggle_environments.envs.kaggriculture.kaggriculture as kg
from research.v45.governance import assert_protected_artifacts, assert_seed_safe
from research.v40.env.fast_sim import FastKagricultureSim

COMMODITIES = ["STRAWBERRY", "MILK", "WOOL", "MELON"]
QUANTITIES = [1, 2, 4, 8, 16, 25, 32]


def compute_market_price(item: str, inventory: int) -> int:
    return kg.market_price(item, inventory)


def analyze_price_impact():
    print("=" * 80)
    print("V45 PHASE 4: PRICE IMPACT & MARKET RESPONSE EMPIRICAL MODELING")
    print("=" * 80)
    
    assert_protected_artifacts()
    
    # 1. Exact mathematical impact for each commodity across inventory levels
    # Default I0 for STRAWBERRY=10000, MILK=10000, WOOL=10000, MELON=10000
    # In engine, market["inventory"][item] begins at 10000.
    
    impact_data = {}
    
    for c in COMMODITIES:
        impact_data[c] = {}
        # Test 3 inventory regimes:
        # Regime A: Depleted / Scarcity (I = 9980, e.g. after town drain)
        # Regime B: Equilibrium (I = 10000)
        # Regime C: Saturated (I = 10050, e.g. after opponent dump)
        inv_regimes = {
            "SCARCITY": 9980,
            "EQUILIBRIUM": 10000,
            "SATURATED": 10050,
        }
        for reg_name, base_inv in inv_regimes.items():
            impact_data[c][reg_name] = {}
            p_initial = compute_market_price(c, base_inv)
            for q in QUANTITIES:
                # In per-unit lockstep pricing:
                # unit 1 is quoted at base_inv, unit 2 at base_inv + 1, ..., unit q at base_inv + q - 1
                unit_prices = [compute_market_price(c, base_inv + k) for k in range(q)]
                total_cash = sum(unit_prices)
                avg_price = total_cash / q
                p_final = compute_market_price(c, base_inv + q)
                slippage_per_unit = p_initial - avg_price
                terminal_drop = p_initial - p_final
                
                impact_data[c][reg_name][str(q)] = {
                    "initial_price": p_initial,
                    "avg_realized_price": round(avg_price, 2),
                    "final_price": p_final,
                    "total_cash": total_cash,
                    "slippage_per_unit": round(slippage_per_unit, 2),
                    "slippage_pct": round(slippage_per_unit / max(1, p_initial) * 100, 2),
                    "post_sale_price_drop": terminal_drop,
                }
                
    # 2. Market Regimes Definition
    market_regimes = {
        "REGIME_1_PRE_COLLAPSE": {
            "description": "Pre-dump equilibrium: prices near or above base, low recent volume, rising opponent inventory.",
            "price_threshold": ">= 1.0 * base_price",
            "opponent_pressure": "HIGH (P(dump_8) >= 0.60)",
            "optimal_action": "PRE_EMPTIVE_TRANCHE",
        },
        "REGIME_2_ACTIVE_COLLAPSE": {
            "description": "Post-dump collapse: market inventory saturated (I > I0), price falling rapidly.",
            "price_threshold": "< 0.85 * base_price",
            "opponent_pressure": "RECENT_DUMP_DETECTED",
            "optimal_action": "HOLD_OR_DELAY",
        },
        "REGIME_3_SHOP_DRAIN_SPIKE": {
            "description": "Town shop drain tick (step % 4 == 0): town shops consume inventory, driving acute price spike.",
            "price_threshold": ">= 1.25 * base_price",
            "opponent_pressure": "LOW_OR_MODERATE",
            "optimal_action": "SCARCITY_ARBITRAGE_TRANCHE",
        },
        "REGIME_4_TERMINAL_PRE_EMPTION": {
            "description": "Steps 690-694 terminal window: immediately before structural Step 695 opponent liquidation wave.",
            "step_window": "690..694",
            "optimal_action": "PRIMARY_STAGGERED_PRE_EMPTION",
        },
        "REGIME_5_TERMINAL_RECOVERY": {
            "description": "Steps 704-706 and 716+: order book re-absorbs after first dump; secondary depth available.",
            "step_window": "704..718",
            "optimal_action": "SECONDARY_STAGGERED_FLUSH",
        }
    }
    
    # Save artifacts
    artifacts_dir = os.path.join(REPO_ROOT, "research", "v45", "artifacts")
    os.makedirs(artifacts_dir, exist_ok=True)
    
    impact_file = os.path.join(artifacts_dir, "price_impact_model.json")
    with open(impact_file, "w") as f:
        json.dump(impact_data, f, indent=2)
        
    regimes_file = os.path.join(artifacts_dir, "market_regimes.json")
    with open(regimes_file, "w") as f:
        json.dump(market_regimes, f, indent=2)
        
    print(f"Saved price impact model to {impact_file}")
    print(f"Saved market regimes to {regimes_file}")
    
    # Display representative impact table
    print("\n--- PRICE IMPACT TABLE FOR STRAWBERRY (Base Price: $120) ---")
    print(f"{'Qty':<5} | {'Equil Init':<10} | {'Equil Avg':<10} | {'Equil Slip':<10} | {'Scarcity Avg':<12} | {'Saturated Avg':<12}")
    for q in QUANTITIES:
        eq = impact_data["STRAWBERRY"]["EQUILIBRIUM"][str(q)]
        sc = impact_data["STRAWBERRY"]["SCARCITY"][str(q)]
        sat = impact_data["STRAWBERRY"]["SATURATED"][str(q)]
        print(f"{q:<5} | ${eq['initial_price']:<9} | ${eq['avg_realized_price']:<9} | -${eq['slippage_per_unit']:<9} | ${sc['avg_realized_price']:<11} | ${sat['avg_realized_price']:<11}")
        
    print("\n--- PRICE IMPACT TABLE FOR MELON (Base Price: $250) ---")
    print(f"{'Qty':<5} | {'Equil Init':<10} | {'Equil Avg':<10} | {'Equil Slip':<10} | {'Scarcity Avg':<12} | {'Saturated Avg':<12}")
    for q in QUANTITIES:
        eq = impact_data["MELON"]["EQUILIBRIUM"][str(q)]
        sc = impact_data["MELON"]["SCARCITY"][str(q)]
        sat = impact_data["MELON"]["SATURATED"][str(q)]
        print(f"{q:<5} | ${eq['initial_price']:<9} | ${eq['avg_realized_price']:<9} | -${eq['slippage_per_unit']:<9} | ${sc['avg_realized_price']:<11} | ${sat['avg_realized_price']:<11}")


if __name__ == "__main__":
    analyze_price_impact()
