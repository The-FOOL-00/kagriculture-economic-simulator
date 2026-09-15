import sys
import os
import json
import numpy as np
import scipy.stats as stats
from concurrent.futures import ProcessPoolExecutor
import kaggle_environments

sys.path.insert(0, os.path.abspath('.'))

import candidates.candidate_cl_fert_gated as m1_module
from scratch.run_wheat_quota_sweep_50seeds import ParameterizedQuotaAgent
from scratch.test_wheat_deferral_pilot import Quota50WheatDeferralAgent

def run_seed_match(seed):
    cfg = {"episodeSteps": 720, "seed": seed}

    def evaluate_agent(agent):
        env = kaggle_environments.make("kaggriculture", configuration=cfg)
        steps = env.run([agent, "starter"])
        
        rew = steps[-1][0]["reward"]
        
        # Detailed actions count
        actions = {
            "MOVE": 0, "PASS": 0, "CARE": 0, "FEED": 0, "HARVEST": 0,
            "WATER": 0, "PLANT": 0, "FERTILIZE": 0, "DROP": 0, "PICKUP": 0
        }
        sold = {
            "WHEAT": 0, "WOOL": 0, "STRAWBERRY": 0, "MILK": 0, "FERTILIZER": 0
        }
        harvested = {
            "WHEAT": 0, "WOOL": 0, "STRAWBERRY": 0, "MILK": 0
        }

        for st in steps:
            p0 = st[0]
            act = p0.get("action") or {}
            w_acts = [act.get("farmer", ["PASS"])] + act.get("hands", [])
            for wa in w_acts:
                if isinstance(wa, list) and len(wa) > 0:
                    op = wa[0]
                    if op in ("NORTH", "SOUTH", "EAST", "WEST"):
                        actions["MOVE"] += 1
                    elif op in actions:
                        actions[op] += 1
                    else:
                        actions["PASS"] += 1

            for o in act.get("market", []):
                if isinstance(o, list) and len(o) >= 3 and o[0] == "SELL":
                    item, qty = o[1], o[2]
                    if item in sold:
                        sold[item] += qty

        return {
            "reward": rew,
            "actions": actions,
            "sold": sold
        }

    m1_res = evaluate_agent(m1_module.ClosedLoopEconomicV1())
    cand_res = evaluate_agent(Quota50WheatDeferralAgent(50))

    return {
        "seed": seed,
        "m1": m1_res,
        "cand": cand_res,
        "rew_diff": cand_res["reward"] - m1_res["reward"],
        "wool_diff": cand_res["sold"]["WOOL"] - m1_res["sold"]["WOOL"],
        "wheat_diff": cand_res["sold"]["WHEAT"] - m1_res["sold"]["WHEAT"],
        "straw_diff": cand_res["sold"]["STRAWBERRY"] - m1_res["sold"]["STRAWBERRY"],
        "milk_diff": cand_res["sold"]["MILK"] - m1_res["sold"]["MILK"],
        "fert_diff": cand_res["sold"]["FERTILIZER"] - m1_res["sold"]["FERTILIZER"],
        "care_diff": cand_res["actions"]["CARE"] - m1_res["actions"]["CARE"],
        "feed_diff": cand_res["actions"]["FEED"] - m1_res["actions"]["FEED"],
        "move_diff": cand_res["actions"]["MOVE"] - m1_res["actions"]["MOVE"],
        "pass_diff": cand_res["actions"]["PASS"] - m1_res["actions"]["PASS"],
        "harvest_diff": cand_res["actions"]["HARVEST"] - m1_res["actions"]["HARVEST"]
    }

def main():
    seeds = list(range(1000, 1050))
    print(f"Running 50-seed matched ablation: M1 vs Quota 50 + Wheat Deferral (Seeds 1000-1049)...")
    
    with ProcessPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(run_seed_match, seeds))

    rew_diffs = np.array([r["rew_diff"] for r in results])
    wool_diffs = np.array([r["wool_diff"] for r in results])
    wheat_diffs = np.array([r["wheat_diff"] for r in results])
    straw_diffs = np.array([r["straw_diff"] for r in results])
    milk_diffs = np.array([r["milk_diff"] for r in results])
    fert_diffs = np.array([r["fert_diff"] for r in results])
    care_diffs = np.array([r["care_diff"] for r in results])
    feed_diffs = np.array([r["feed_diff"] for r in results])
    move_diffs = np.array([r["move_diff"] for r in results])
    pass_diffs = np.array([r["pass_diff"] for r in results])
    harv_diffs = np.array([r["harvest_diff"] for r in results])

    n = len(results)
    mean_rew = float(np.mean(rew_diffs))
    median_rew = float(np.median(rew_diffs))
    std_rew = float(np.std(rew_diffs, ddof=1))
    sem_rew = std_rew / np.sqrt(n)
    ci95 = [float(mean_rew - 1.96 * sem_rew), float(mean_rew + 1.96 * sem_rew)]
    win_rate = float(np.mean(rew_diffs > 0) * 100)
    t_stat, p_val = stats.ttest_1samp(rew_diffs, 0.0)

    summary = {
        "candidate": "M1 + Quota 50 + Morning Wheat Deferral (Hour < 12)",
        "n_seeds": n,
        "mean_rew_delta": round(mean_rew, 2),
        "median_rew_delta": round(median_rew, 2),
        "std_rew": round(std_rew, 2),
        "ci95": [round(ci95[0], 2), round(ci95[1], 2)],
        "win_rate_pct": round(win_rate, 1),
        "t_stat": round(float(t_stat), 4),
        "p_val": round(float(p_val), 4),
        "secondary_deltas": {
            "wool_sold": round(float(np.mean(wool_diffs)), 2),
            "wheat_sold": round(float(np.mean(wheat_diffs)), 2),
            "straw_sold": round(float(np.mean(straw_diffs)), 2),
            "milk_sold": round(float(np.mean(milk_diffs)), 2),
            "fert_sold": round(float(np.mean(fert_diffs)), 2),
            "care_actions": round(float(np.mean(care_diffs)), 2),
            "feed_actions": round(float(np.mean(feed_diffs)), 2),
            "move_actions": round(float(np.mean(move_diffs)), 2),
            "pass_actions": round(float(np.mean(pass_diffs)), 2),
            "harvest_actions": round(float(np.mean(harv_diffs)), 2)
        }
    }

    with open("scratch/ablation_50seed_wheat_deferral.json", "w") as f:
        json.dump({"summary": summary, "results": results}, f, indent=2)

    print("\n=== 50-SEED ABLATION RESULTS ===")
    print(f"Mean Reward Delta:   ${summary['mean_rew_delta']:+,.2f}")
    print(f"Median Reward Delta: ${summary['median_rew_delta']:+,.2f}")
    print(f"95% CI:              [${summary['ci95'][0]:+,.2f}, ${summary['ci95'][1]:+,.2f}]")
    print(f"Win Rate:            {summary['win_rate_pct']:.1f}%")
    print(f"p-value:             {summary['p_val']:.4f}")
    print("\n--- Secondary Commodity Deltas ---")
    print(f"Wheat Sold:          {summary['secondary_deltas']['wheat_sold']:+.2f} units")
    print(f"Wool Sold:           {summary['secondary_deltas']['wool_sold']:+.2f} units")
    print(f"Strawberry Sold:     {summary['secondary_deltas']['straw_sold']:+.2f} units")
    print(f"Milk Sold:           {summary['secondary_deltas']['milk_sold']:+.2f} units")
    print(f"Fertilizer Sold:     {summary['secondary_deltas']['fert_sold']:+.2f} units")
    print("\n--- Action Deltas ---")
    print(f"CARE Actions:        {summary['secondary_deltas']['care_actions']:+.2f}")
    print(f"FEED Actions:        {summary['secondary_deltas']['feed_actions']:+.2f}")
    print(f"HARVEST Actions:     {summary['secondary_deltas']['harvest_actions']:+.2f}")
    print(f"MOVE Actions:        {summary['secondary_deltas']['move_actions']:+.2f}")
    print(f"PASS Actions:        {summary['secondary_deltas']['pass_actions']:+.2f}")

if __name__ == "__main__":
    main()
