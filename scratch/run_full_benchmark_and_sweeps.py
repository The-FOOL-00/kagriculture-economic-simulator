"""
=============================================================================
COMPREHENSIVE BENCHMARK TOURNAMENT & PARAMETER SWEEP SUITE
=============================================================================
Executes:
1. 50+ Paired-match benchmark of Champion vs Titan, Golden v1, Synthetic opponents.
2. Full Parameter Sweeps (Melons, Cows, Sheep, Geese, Combinations).
3. Statistical confidence intervals and Pareto rankings.
=============================================================================
"""

import sys
import os
import time
import math
import numpy as np

project_root = r"c:\Users\Sundareswaran\Kagriculture"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from run_championship_benchmark import run_tournament


def run_benchmark_suite():
    champion = "candidates/slot2_hybrid_6c3s_10m.py"
    opponents = [
        ("Titan_Baseline", "candidates/slot1_titan_control.py"),
        ("Golden_Control_v1", "agents/golden_v1.py"),
    ]

    print("=" * 105)
    print("PART 19: 50+ MATCH BENCHMARK SUITE (Paired Seeds & Side Swapped)")
    print("=" * 105)

    bench_results = {}
    for name, opp_path in opponents:
        # 25 pairs = 50 matches
        res = run_tournament(champion, opp_path, num_pairs=25, start_seed=20001, max_workers=8)
        bench_results[name] = res
        w_low, w_high = res['ci_95']
        print(f"vs {name:<20s} | Matches: {res['games']:2d} | WinRate: {res['win_rate']:5.1f}% ({res['wins']}W-{res['losses']}L-{res['ties']}T) [95% CI: {w_low:.1f}%-{w_high:.1f}%] | Mean Cash: ${res['mean_us']:,.0f} | Median: ${res['median_us']:,.0f} | Opp: ${res['mean_opp']:,.0f} | Margin: {res['margin']:+,.0f}")

    return bench_results


def run_parameter_sweeps():
    print("\n" + "=" * 105)
    print("PART 21-23: PARAMETER SWEEPS & INTERACTION ANALYSIS (Seeds 30001-30020)")
    print("=" * 105)

    with open("agents/hybrid_6c3s_10m.py", "r", encoding="utf-8") as f:
        base_code = f.read()

    os.makedirs("sweep_agents", exist_ok=True)
    opp_path = "agents/golden_v1.py"

    # 1. Melons Sweep: 0, 5, 8, 10, 12, 15, 18, 20
    melon_configs = [0, 5, 8, 10, 12, 15, 18, 20]
    print("\n--- 1. MELON TARGET SWEEP (Fixed 6 Cows / 3 Sheep) ---")
    melon_results = []
    for m in melon_configs:
        code_m = base_code.replace("target_cows=6, target_sheep=3, target_geese=0, target_melons=10",
                                   f"target_cows=6, target_sheep=3, target_geese=0, target_melons={m}")
        p_m = f"sweep_agents/sweep_m_{m}.py"
        with open(p_m, "w", encoding="utf-8") as f:
            f.write(code_m)
        res = run_tournament(p_m, opp_path, num_pairs=10, start_seed=30001, max_workers=8)
        melon_results.append((m, res))
        print(f"  * Melons = {m:2d} | WinRate: {res['win_rate']:5.1f}% ({res['wins']}W-{res['losses']}L) | Mean Cash: ${res['mean_us']:8,.0f} | Median: ${res['median_us']:8,.0f} | Margin: {res['margin']:+8,.0f}")

    # 2. Cows Sweep: 0, 2, 4, 6, 8 (Fixed 3 Sheep / 10 Melons)
    cow_configs = [0, 2, 4, 6, 8]
    print("\n--- 2. COW TARGET SWEEP (Fixed 3 Sheep / 10 Melons) ---")
    cow_results = []
    for c in cow_configs:
        code_c = base_code.replace("target_cows=6, target_sheep=3, target_geese=0, target_melons=10",
                                   f"target_cows={c}, target_sheep=3, target_geese=0, target_melons=10")
        p_c = f"sweep_agents/sweep_c_{c}.py"
        with open(p_c, "w", encoding="utf-8") as f:
            f.write(code_c)
        res = run_tournament(p_c, opp_path, num_pairs=10, start_seed=30001, max_workers=8)
        cow_results.append((c, res))
        print(f"  * Cows = {c:2d}   | WinRate: {res['win_rate']:5.1f}% ({res['wins']}W-{res['losses']}L) | Mean Cash: ${res['mean_us']:8,.0f} | Median: ${res['median_us']:8,.0f} | Margin: {res['margin']:+8,.0f}")

    # 3. Sheep Sweep: 0, 1, 2, 3, 4, 5 (Fixed 6 Cows / 10 Melons)
    sheep_configs = [0, 1, 2, 3, 4, 5]
    print("\n--- 3. SHEEP TARGET SWEEP (Fixed 6 Cows / 10 Melons) ---")
    sheep_results = []
    for s in sheep_configs:
        code_s = base_code.replace("target_cows=6, target_sheep=3, target_geese=0, target_melons=10",
                                   f"target_cows=6, target_sheep={s}, target_geese=0, target_melons=10")
        p_s = f"sweep_agents/sweep_s_{s}.py"
        with open(p_s, "w", encoding="utf-8") as f:
            f.write(code_s)
        res = run_tournament(p_s, opp_path, num_pairs=10, start_seed=30001, max_workers=8)
        sheep_results.append((s, res))
        print(f"  * Sheep = {s:2d}  | WinRate: {res['win_rate']:5.1f}% ({res['wins']}W-{res['losses']}L) | Mean Cash: ${res['mean_us']:8,.0f} | Median: ${res['median_us']:8,.0f} | Margin: {res['margin']:+8,.0f}")

    # 4. Herd x Melon Combinations & Pareto Analysis
    combo_configs = [
        ("4C / 2S / 10M", 4, 2, 0, 10),
        ("4C / 2S / 15M", 4, 2, 0, 15),
        ("6C / 2S / 10M", 6, 2, 0, 10),
        ("6C / 2S / 15M", 6, 2, 0, 15),
        ("6C / 3S / 10M (Champion)", 6, 3, 0, 10),
        ("6C / 3S / 15M", 6, 3, 0, 15),
        ("8C / 4S / 10M", 8, 4, 0, 10),
        ("8C / 4S / 15M", 8, 4, 0, 15),
    ]
    print("\n--- 4. COMBINATION INTERACTION & PARETO ANALYSIS ---")
    combo_results = []
    for label, c, s, g, m in combo_configs:
        code_combo = base_code.replace("target_cows=6, target_sheep=3, target_geese=0, target_melons=10",
                                       f"target_cows={c}, target_sheep={s}, target_geese={g}, target_melons={m}")
        p_combo = f"sweep_agents/sweep_combo_{c}c_{s}s_{m}m.py"
        with open(p_combo, "w", encoding="utf-8") as f:
            f.write(code_combo)
        res = run_tournament(p_combo, opp_path, num_pairs=15, start_seed=30001, max_workers=8)
        combo_results.append((label, res))
        print(f"  * {label:26s} | WinRate: {res['win_rate']:5.1f}% ({res['wins']}W-{res['losses']}L) | Mean Cash: ${res['mean_us']:8,.0f} | Median: ${res['median_us']:8,.0f} | Margin: {res['margin']:+8,.0f}")

    print("=" * 105)


if __name__ == "__main__":
    run_benchmark_suite()
    run_parameter_sweeps()
