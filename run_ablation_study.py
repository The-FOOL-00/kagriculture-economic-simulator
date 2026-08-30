"""
=============================================================================
KAGGRICULTURE STRATEGY ABLATION SUITE (CLEAN & UNCONFOUNDED)
=============================================================================
Measures exact marginal performance contribution of each strategic component:
1. Full Champion Strategy (Hybrid 6C / 3S / 10M)
2. Ablation 1: Minus Livestock (Pure Crop)
3. Ablation 2: Minus Melons (0 Melons, Pure Carrot/Wheat)
4. Ablation 3: Minus Animal Care (Feeding active, Care disabled)
5. Ablation 4: Minus Town Synchronization (No modulo-4 dump trigger)
6. Ablation 5: Plus Crop Fertilizer (Active fertilizer spreading)
7. Ablation 6: Dynamic Economic Allocation
=============================================================================
"""

import sys
import os
import shutil
from run_championship_benchmark import run_tournament

project_root = r"c:\Users\Sundareswaran\Kagriculture"
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def generate_ablation_files():
    with open("agents/hybrid_6c3s_10m.py", "r", encoding="utf-8") as f:
        base_code = f.read()

    os.makedirs("ablation_agents", exist_ok=True)

    # 1. Full Strategy
    p_full = "ablation_agents/ablation_full.py"
    with open(p_full, "w", encoding="utf-8") as f:
        f.write(base_code)

    # 2. Minus Livestock (0 cows, 0 sheep, 0 geese)
    p_no_livestock = "ablation_agents/ablation_no_livestock.py"
    code_no_live = base_code.replace("target_cows=6, target_sheep=3, target_geese=0, target_melons=10",
                                     "target_cows=0, target_sheep=0, target_geese=0, target_melons=10")
    with open(p_no_livestock, "w", encoding="utf-8") as f:
        f.write(code_no_live)

    # 3. Minus Melons (0 melons)
    p_no_melon = "ablation_agents/ablation_no_melon.py"
    code_no_m = base_code.replace("target_cows=6, target_sheep=3, target_geese=0, target_melons=10",
                                  "target_cows=6, target_sheep=3, target_geese=0, target_melons=0")
    with open(p_no_melon, "w", encoding="utf-8") as f:
        f.write(code_no_m)

    # 4. Minus Animal Care (care_animals = False)
    p_no_care = "ablation_agents/ablation_no_care.py"
    code_no_care = base_code.replace("care_animals=True", "care_animals=False")
    with open(p_no_care, "w", encoding="utf-8") as f:
        f.write(code_no_care)

    # 5. Minus Town Sync (town_sync = False)
    p_no_sync = "ablation_agents/ablation_no_sync.py"
    code_no_sync = base_code.replace("town_sync=True", "town_sync=False")
    with open(p_no_sync, "w", encoding="utf-8") as f:
        f.write(code_no_sync)

    # 6. Plus Crop Fertilizer (use_fert = True)
    p_fert = "ablation_agents/ablation_plus_fertilizer.py"
    code_fert = base_code.replace("use_fert=False", "use_fert=True")
    with open(p_fert, "w", encoding="utf-8") as f:
        f.write(code_fert)

    return [
        ("1_Full_Champion", p_full),
        ("2_Minus_Livestock", p_no_livestock),
        ("3_Minus_Melons", p_no_melon),
        ("4_Minus_Animal_Care", p_no_care),
        ("5_Minus_Town_Sync", p_no_sync),
        ("6_Plus_Crop_Fertilizer", p_fert),
    ]


if __name__ == "__main__":
    print("=" * 95)
    print("KAGGRICULTURE STRATEGY ABLATION SUITE (Seeds 50001-50010 vs Golden Control v1)")
    print("=" * 95)

    ablations = generate_ablation_files()
    opp_path = "agents/golden_v1.py"
    ablation_results = []

    for name, file_path in ablations:
        res = run_tournament(file_path, opp_path, num_pairs=5, start_seed=50001, max_workers=6)
        ablation_results.append((name, res))
        print(f"{name:25s} | WinRate: {res['win_rate']:5.1f}% ({res['wins']}W-{res['losses']}L) | Cash: ${res['mean_us']:8,.0f} | Margin: {res['margin']:+8,.0f}")

    print("\n" + "=" * 95)
    print("SUMMARY OF MARGINAL COMPONENT CONTRIBUTIONS")
    print("=" * 95)
    base_cash = ablation_results[0][1]['mean_us']
    for name, res in ablation_results:
        delta = res['mean_us'] - base_cash
        print(f"  * {name:25s}: Mean Cash = ${res['mean_us']:8,.0f} (Delta vs Full: {delta:+8,.0f})")
    print("=" * 95)
