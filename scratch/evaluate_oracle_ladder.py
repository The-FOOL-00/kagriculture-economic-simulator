"""
scratch/evaluate_oracle_ladder.py
=================================
Runs the Economic Oracle Ladder and prints the theoretical frontier vs current architectures.
"""

import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from engine.economic_oracle import EconomicOracle


def main():
    oracle = EconomicOracle()
    
    l0 = oracle.level_0_pure_relaxed_bound()
    l1 = oracle.level_1_temporal_maturation_bound()
    l2 = oracle.level_2_labor_constrained_bound()
    l3 = oracle.level_3_spatial_movement_bound()
    l4 = oracle.level_4_competitive_market_frontier()
    
    print("\n" + "=" * 75)
    print("           KAGGRICULTURE ECONOMIC FRONTIER ORACLE LADDER")
    print("=" * 75)
    print(f"{'Oracle Layer':<45} | {'Final Realized Cash':>20}")
    print("-" * 75)
    print(f"{l0['name']:<45} | ${l0['final_cash']:>19,.2f}")
    print(f"{l1['name']:<45} | ${l1['final_cash']:>19,.2f}")
    print(f"{l2['name']:<45} | ${l2['final_cash']:>19,.2f}")
    print(f"{l3['name']:<45} | ${l3['final_cash']:>19,.2f}")
    print(f"{l4['name']:<45} | ${l4['final_cash']:>19,.2f}")
    print("-" * 75)
    print(f"{'Current Best V54++ (Solo / Idle Opponent)':<45} | ${156127:>19,.2f}")
    print(f"{'Current Best V54++ (Head-to-Head Self-Play)':<45} | ${80264:>19,.2f}")
    print(f"{'Actual Top-1 Kaggle Match (Tetsuya in 104060611)':<45} | ${138411:>19,.2f}")
    print(f"{'Actual Top-8 Kaggle Match (Zhyphirus in 104060611)':<45} | ${124189:>19,.2f}")
    print("=" * 75)
    print("\nLevel 0 Detailed Revenue Breakdown:")
    for item, d in sorted(l0["sales_summary"].items(), key=lambda t: -t[1]["revenue"]):
        print(f"  {item:<12}: {d['units']:>4d} units sold -> ${d['revenue']:>8,d}")
    print(f"  Fixed Costs : ${l0['fixed_costs']:,d}")
    print(f"  Net Bound   : ${l0['final_cash']:,d}")


if __name__ == "__main__":
    main()
