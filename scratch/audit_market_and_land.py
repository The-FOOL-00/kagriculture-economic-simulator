import sys
import os
import json
import numpy as np
from scipy import stats
from concurrent.futures import ProcessPoolExecutor
import kaggle_environments

sys.path.insert(0, os.path.abspath('.'))
from scratch.run_wheat_quota_sweep_50seeds import ParameterizedQuotaAgent

def get_market_telemetry(seed):
    agent = ParameterizedQuotaAgent(50)
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    env.reset()
    
    prices_d6 = {}
    land_day = 30
    for t in range(720):
        obs0 = env.steps[-1][0]["observation"]
        f0 = obs0["farms"][0]
        
        if t == 144: # Day 6 Hour 0
            mkt = obs0.get("market", {}) or {}
            inv = mkt.get("inventory", {})
            prices_d6 = {
                "wheat_inv": inv.get("WHEAT", 0),
                "carrot_inv": inv.get("CARROT", 0),
                "melon_inv": inv.get("MELON", 0),
                "fert_inv": inv.get("FERTILIZER", 0),
                "cash": f0["money"]
            }
        
        if len(f0["unlocked_quadrants"]) > 1 and land_day == 30:
            land_day = t / 24.0

        if t >= 144 and land_day < 30:
            break
            
        action = agent(obs0)
        env.step([action, "starter"])
        
    prices_d6["land_day"] = land_day
    prices_d6["seed"] = seed
    return prices_d6

def main():
    with open("scratch/exact_accounting_200seeds_results.json") as f:
        acc = json.load(f)
    ite_by_seed = {d["seed"]: d["mech_a"]["reward"] - d["q50"]["reward"] for d in acc}
    
    seeds = list(range(1250, 1450))
    print("Extracting Day 6 market prices and land purchase day across 200 seeds...", flush=True)
    with ProcessPoolExecutor(max_workers=10) as pool:
        res = list(pool.map(get_market_telemetry, seeds))
        
    for r in res:
        r["ite"] = ite_by_seed[r["seed"]]
        
    print("\n=== CORRELATIONS WITH ITE ===")
    for k in ["cash", "wheat_inv", "carrot_inv", "melon_inv", "fert_inv", "land_day"]:
        vals = np.array([r[k] for r in res])
        ites = np.array([r["ite"] for r in res])
        if np.std(vals) > 1e-6:
            r_p, p_p = stats.pearsonr(vals, ites)
            r_s, p_s = stats.spearmanr(vals, ites)
            print(f"{k:<15} | Pearson r={r_p:+.4f} (p={p_p:.4f}) | Spearman rho={r_s:+.4f} (p={p_s:.4f})")
        else:
            print(f"{k:<15} | Constant")

    # Land day distribution
    land_days = [r["land_day"] for r in res]
    print(f"\nLand purchase day: Mean={np.mean(land_days):.2f}, Median={np.median(land_days):.2f}, Min={np.min(land_days):.2f}, Max={np.max(land_days):.2f}")
    
    # Check ITE by Land Day (Before Day 9 vs Day 9+)
    early_land = [r["ite"] for r in res if r["land_day"] < 9.0]
    late_land = [r["ite"] for r in res if r["land_day"] >= 9.0]
    print(f"Seeds with Land < Day 9: N={len(early_land)} | Mean ITE = ${np.mean(early_land):,.2f} | Win Rate = {np.mean(np.array(early_land) > 0)*100:.1f}%")
    print(f"Seeds with Land >= Day 9: N={len(late_land)} | Mean ITE = ${np.mean(late_land):,.2f} | Win Rate = {np.mean(np.array(late_land) > 0)*100:.1f}%")

if __name__ == "__main__":
    main()
