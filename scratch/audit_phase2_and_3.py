import sys
import os
import json
import numpy as np
from collections import defaultdict
from scipy import stats
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.abspath('.'))

from scratch.run_phase2_to_5_study import run_predecision_telemetry

def main():
    with open("scratch/exact_accounting_200seeds_results.json") as f:
        acc_data = json.load(f)

    # ITE = Reward(A) - Reward(Q50)
    ite_by_seed = {d["seed"]: d["mech_a"]["reward"] - d["q50"]["reward"] for d in acc_data}
    
    seeds = list(range(1250, 1450))
    print(f"Extracting 20 pre-decision state variables across {len(seeds)} seeds at Day 6 Hour 0...", flush=True)
    with ProcessPoolExecutor(max_workers=10) as pool:
        telemetry = list(pool.map(run_predecision_telemetry, seeds))

    with open("scratch/phase2_telemetry_200seeds.json", "w") as f:
        json.dump(telemetry, f, indent=2)

    # Correlate and classify
    labels = {}
    beneficial = []
    neutral = []
    harmful = []
    for s in seeds:
        ite = ite_by_seed[s]
        if ite > 5000:
            lbl = "STRONGLY_BENEFICIAL"
            beneficial.append(s)
        elif ite < -5000:
            lbl = "STRONGLY_HARMFUL"
            harmful.append(s)
        else:
            lbl = "NEUTRAL"
            neutral.append(s)
        labels[s] = lbl

    print(f"\n=== ITE DISTRIBUTION (N=200) ===")
    print(f"Strongly Beneficial (ITE > +$5,000): {len(beneficial)} ({len(beneficial)/len(seeds)*100:.1f}%) | Mean ITE: ${np.mean([ite_by_seed[s] for s in beneficial]):,.2f}")
    print(f"Neutral (-$5,000 <= ITE <= +$5,000): {len(neutral)} ({len(neutral)/len(seeds)*100:.1f}%) | Mean ITE: ${np.mean([ite_by_seed[s] for s in neutral]):,.2f}")
    print(f"Strongly Harmful (ITE < -$5,000): {len(harmful)} ({len(harmful)/len(seeds)*100:.1f}%) | Mean ITE: ${np.mean([ite_by_seed[s] for s in harmful]):,.2f}")

    # Build feature table
    telem_by_seed = {t["seed"]: t for t in telemetry}
    
    print("\n=== PRE-DECISION STATE VARIABLE CORRELATIONS WITH ITE ===")
    var_names = [
        "cash", "cows_shed", "cows_field", "sheep_shed", "sheep_field",
        "free_pasture_tiles", "free_sheep_coords", "sheep_purchased_unplaced",
        "cow_placed_consumes_sheep_tile", "is_single_quadrant",
        "wheat_sold_d6", "wheat_harvests_pending", "strawberry_bushes"
    ]

    for v in var_names:
        vals = np.array([float(telem_by_seed[s][v]) for s in seeds])
        ites = np.array([ite_by_seed[s] for s in seeds])
        if np.std(vals) > 1e-6:
            r, p = stats.pearsonr(vals, ites)
            rho, p_rho = stats.spearmanr(vals, ites)
            print(f"{v:<32} | Pearson r={r:+.4f} (p={p:.4f}) | Spearman rho={rho:+.4f} (p={p_rho:.4f})")
        else:
            print(f"{v:<32} | Constant value = {vals[0]}")

    # Test Rule Candidates
    print("\n=== CANDIDATE INTERPRETABLE TRIGGER RULES ===")
    rules = {
        "R1: Single Quadrant Only": lambda t: t["is_single_quadrant"],
        "R2: Cow Consumes Sheep Slot (2,4)": lambda t: t["cow_placed_consumes_sheep_tile"],
        "R3: Free Sheep Coords < 4": lambda t: t["free_sheep_coords"] < 4,
        "R4: Cow Consumes Slot AND Wheat Sold >= 25": lambda t: t["cow_placed_consumes_sheep_tile"] and t["wheat_sold_d6"] >= 25,
        "R5: Single Quad AND Cash >= 400": lambda t: t["is_single_quadrant"] and t["cash"] >= 400,
        "R6: Free Pasture Tiles <= 1": lambda t: t["free_pasture_tiles"] <= 1,
    }

    print(f"{'Rule':<45} | {'Cov':>5} | {'Prec':>6} | {'Recall':>6} | {'Mean ITE In':>12} | {'Mean ITE Out':>12} | {'Net Gain':>10}")
    print("-" * 105)
    for rname, rfn in rules.items():
        triggered = [s for s in seeds if rfn(telem_by_seed[s])]
        not_triggered = [s for s in seeds if not rfn(telem_by_seed[s])]
        
        coverage = len(triggered) / len(seeds)
        # Precision: fraction of triggered seeds where ITE > 0
        prec = np.mean([ite_by_seed[s] > 0 for s in triggered]) if triggered else 0.0
        # Recall: fraction of strongly beneficial seeds triggered
        rec = sum(1 for s in beneficial if s in triggered) / len(beneficial) if beneficial else 0.0
        
        mean_in = np.mean([ite_by_seed[s] for s in triggered]) if triggered else 0.0
        mean_out = np.mean([ite_by_seed[s] for s in not_triggered]) if not_triggered else 0.0
        
        # Net gain over Q50 by applying intervention ONLY when triggered:
        # If triggered -> get Reward(A), if not triggered -> get Reward(Q50)
        # Gain over Q50 = sum_{s in triggered} ITE(s) / len(seeds)
        net_gain = sum(ite_by_seed[s] for s in triggered) / len(seeds) if triggered else 0.0
        
        print(f"{rname:<45} | {coverage*100:>4.1f}% | {prec*100:>5.1f}% | {rec*100:>5.1f}% | ${mean_in:>+11,.2f} | ${mean_out:>+11,.2f} | ${net_gain:>+9,.2f}")

if __name__ == "__main__":
    main()
