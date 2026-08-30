import os, sys, json, multiprocessing
sys.path.insert(0, r'c:\Users\Sundareswaran\Kagriculture')

from scratch.master_tournament_runner import run_paired_tournament
from agents.apex_grandmaster_v4 import ApexGrandmasterV4

# Load holdout seeds
def load_seeds(filepath, limit=50):
    with open(filepath, 'r') as f:
        seeds = [int(line.strip()) for line in f if line.strip().isdigit()]
    return seeds[:limit]

holdout_seeds = load_seeds(r'benchmarks/seeds/holdout.txt', 50)
apex_path = r'c:\Users\Sundareswaran\Kagriculture\agents\apex_grandmaster_v4.py'

# 7 Concrete Meta Opponent Archetypes
# Meta A: Fast Livestock + Melons (The dominant high-elo archetype) -> opponents/o12_top_meta.py
# Meta B: Fast Pure Crop Rusher (25 Melons + Rapid Carrots) -> opponents/o3_melon_specialist.py
# Meta C: Heavy Sheep + Cow Engine (Wool/Milk maximization) -> opponents/o6_sheep_specialist.py
# Meta D: High Labor 8 Workers + Land Scaler -> opponents/o5_cow_specialist.py
# Meta E: Economic Optimizer / Dynamic Allocator -> opponents/o8_economic_optimizer.py
# Meta F: Fast Fast Crop / Carrot-Tomato Rusher -> opponents/o4_fast_crop.py
# Meta G: Adversarial Champion Killer / Preemptor -> opponents/adversarial_champion_killer.py

meta_opponents = {
    "Meta_A_Fast_Livestock_Melons": r"c:\Users\Sundareswaran\Kagriculture\opponents\o12_top_meta.py",
    "Meta_B_Pure_Crop_Rusher": r"c:\Users\Sundareswaran\Kagriculture\opponents\o3_melon_specialist.py",
    "Meta_C_Heavy_Sheep_Engine": r"c:\Users\Sundareswaran\Kagriculture\opponents\o6_sheep_specialist.py",
    "Meta_D_Cow_Specialist_Scaler": r"c:\Users\Sundareswaran\Kagriculture\opponents\o5_cow_specialist.py",
    "Meta_E_Economic_Optimizer": r"c:\Users\Sundareswaran\Kagriculture\opponents\o8_economic_optimizer.py",
    "Meta_F_Fast_Crop_Rusher": r"c:\Users\Sundareswaran\Kagriculture\opponents\o4_fast_crop.py",
    "Meta_G_Adversarial_Preemptor": r"c:\Users\Sundareswaran\Kagriculture\opponents\adversarial_champion_killer.py"
}

if __name__ == '__main__':
    print("="*70)
    print("RUNNING APEX V4 VS 7 TOP-META OPPONENT ARCHETYPES")
    print("="*70)
    meta_results = {}
    for name, opp_p in meta_opponents.items():
        if not os.path.exists(opp_p):
            print(f"Opponent {opp_p} not found, skipping...")
            continue
        res = run_paired_tournament(apex_path, opp_p, holdout_seeds)
        meta_results[name] = res
        print(f"  {name:30s}: WR {res['pooled_wr']*100:5.1f}% [{res['ci_95'][0]*100:4.1f}%, {res['ci_95'][1]*100:4.1f}%] | Cand Cash: ${res['mean_cand_cash']:,.0f} | Opp Cash: ${res['mean_opp_cash']:,.0f} | Margin: +${res['mean_margin']:,.0f}")

    out_file = r'c:\Users\Sundareswaran\Kagriculture\scratch\meta_opponents_results.json'
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(meta_results, f, indent=2)
    print(f"\nSaved meta tournament results to {out_file}")
