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

# Mechanism B: M1 + Quota 50 + Prevent Wheat-Liquidity Cow Acceleration (Cap Day 6 cow buy at 1)
class MechanismBAgent(ParameterizedQuotaAgent):
    def __init__(self, quota=50):
        super().__init__(quota)

    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        orders = super()._macro_market(step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs)
        if day == 6:
            new_orders = []
            for o in orders:
                if isinstance(o, list) and len(o) >= 3 and o[0] == "BUY_ANIMAL" and o[1] == "COW":
                    new_orders.append(["BUY_ANIMAL", "COW", min(1, int(o[2]))])
                else:
                    new_orders.append(o)
            return new_orders
        return orders

# Mechanism A: M1 + Quota 50 + Preserve Sheep-Compatible Pasture Capacity
# (Do not buy a cow if it would exceed available cow slots in unlocked quadrants, reserving sheep slots)
class MechanismAAgent(ParameterizedQuotaAgent):
    def __init__(self, quota=50):
        super().__init__(quota)

    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        orders = super()._macro_market(step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs)
        
        # In single quadrant (NW), maximum cow slots = 4: (4,4), (4,3), (3,4), (3,3).
        # (4,2) and (2,4) must be strictly reserved for sheep!
        if len(quads) == 1:
            cows_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "COW")
            cows_inv = sum(int(inv.get("COW", 0) or 0) for inv in invs)
            cows_shed = int(shed.get("COW", 0) or 0)
            total_c = cows_f + cows_inv + cows_shed
            
            new_orders = []
            for o in orders:
                if isinstance(o, list) and len(o) >= 3 and o[0] == "BUY_ANIMAL" and o[1] == "COW":
                    allowed_cows = max(0, 4 - total_c)
                    can_buy = min(int(o[2]), allowed_cows)
                    if can_buy > 0:
                        new_orders.append(["BUY_ANIMAL", "COW", can_buy])
                else:
                    new_orders.append(o)
            return new_orders
        return orders

def run_seed_eval(seed):
    cfg = {"episodeSteps": 720, "seed": seed}

    def eval_agent(agent):
        env = kaggle_environments.make("kaggriculture", configuration=cfg)
        steps = env.run([agent, "starter"])
        
        sold = {"WHEAT": 0, "WOOL": 0, "STRAWBERRY": 0, "MILK": 0, "FERTILIZER": 0}
        moves = 0
        sheep_shed_days = 0
        sheep_escapes = 0

        for step_idx, st in enumerate(steps):
            obs = st[0].get("observation") or {}
            act = st[0].get("action") or {}
            priv = obs.get("private") or {}
            shed = priv.get("shed") or {}
            
            # Count sheep shed days (step % 24 == 23)
            if step_idx % 24 == 23:
                sheep_shed_days += int(shed.get("SHEEP", 0) or 0)
            
            w_acts = [act.get("farmer", ["PASS"])] + act.get("hands", [])
            for wa in w_acts:
                if isinstance(wa, list) and len(wa) > 0 and wa[0] in ("NORTH", "SOUTH", "EAST", "WEST"):
                    moves += 1

            for o in act.get("market", []):
                if isinstance(o, list) and len(o) >= 3 and o[0] == "SELL":
                    if o[1] in sold: sold[o[1]] += int(o[2])

        # Check final sheep count vs placed sheep to detect escapes
        farm = (steps[-1][0]["observation"].get("farms") or [{}])[0]
        final_sheep = sum(1 for r in farm.get("tiles", []) for t in r if isinstance(t, dict) and t.get("animal") == "SHEEP")

        return {
            "reward": steps[-1][0]["reward"],
            "sold": sold,
            "moves": moves,
            "sheep_shed_days": sheep_shed_days,
            "final_sheep": final_sheep
        }

    res_m1 = eval_agent(m1_module.ClosedLoopEconomicV1())
    res_q50 = eval_agent(ParameterizedQuotaAgent(50))
    res_b = eval_agent(MechanismBAgent(50))
    res_a = eval_agent(MechanismAAgent(50))

    return {
        "seed": seed,
        "m1": res_m1,
        "q50": res_q50,
        "mech_b": res_b,
        "mech_a": res_a
    }

def main():
    seeds = list(range(1000, 1050)) # 50 matched seeds
    print(f"Running 50-seed causal ablations for Mechanism A & B vs M1 (Seeds 1000-1049)...")
    
    with ProcessPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(run_seed_eval, seeds))

    def analyze_diff(name, key):
        diff_rew = np.array([r[key]["reward"] - r["m1"]["reward"] for r in results])
        diff_wool = np.array([r[key]["sold"]["WOOL"] - r["m1"]["sold"]["WOOL"] for r in results])
        diff_wheat = np.array([r[key]["sold"]["WHEAT"] - r["m1"]["sold"]["WHEAT"] for r in results])
        diff_straw = np.array([r[key]["sold"]["STRAWBERRY"] - r["m1"]["sold"]["STRAWBERRY"] for r in results])
        diff_milk = np.array([r[key]["sold"]["MILK"] - r["m1"]["sold"]["MILK"] for r in results])
        diff_shed_days = np.array([r[key]["sheep_shed_days"] - r["m1"]["sheep_shed_days"] for r in results])
        
        n = len(results)
        mean_r = float(np.mean(diff_rew))
        med_r = float(np.median(diff_rew))
        std_r = float(np.std(diff_rew, ddof=1))
        sem_r = std_r / np.sqrt(n)
        ci95 = [mean_r - 1.96 * sem_r, mean_r + 1.96 * sem_r]
        win_rate = float(np.mean(diff_rew > 0) * 100)
        t_stat, p_val = stats.ttest_1samp(diff_rew, 0.0)

        print(f"\n==================================================")
        print(f"RESULTS FOR {name} (N={n})")
        print(f"==================================================")
        print(f"Mean Reward Delta:   ${mean_r:+,.2f}")
        print(f"Median Reward Delta: ${med_r:+,.2f}")
        print(f"Standard Deviation:  ${std_r:,.2f}")
        print(f"95% CI:              [${ci95[0]:+,.2f}, ${ci95[1]:+,.2f}]")
        print(f"Win Rate:            {win_rate:.1f}%")
        print(f"p-value:             {p_val:.4f}")
        print(f"Wool Delta:          {np.mean(diff_wool):+.2f} units")
        print(f"Wheat Delta:         {np.mean(diff_wheat):+.2f} units")
        print(f"Strawberry Delta:    {np.mean(diff_straw):+.2f} units")
        print(f"Milk Delta:          {np.mean(diff_milk):+.2f} units")
        print(f"Sheep Shed Days Diff:{np.mean(diff_shed_days):+.2f} days")

        return {
            "name": name,
            "mean_delta": mean_r,
            "median_delta": med_r,
            "ci95": ci95,
            "win_rate": win_rate,
            "p_val": p_val,
            "wool_delta": float(np.mean(diff_wool)),
            "wheat_delta": float(np.mean(diff_wheat)),
            "straw_delta": float(np.mean(diff_straw)),
            "milk_delta": float(np.mean(diff_milk)),
            "shed_days_delta": float(np.mean(diff_shed_days))
        }

    q50_summary = analyze_diff("Raw Quota 50", "q50")
    mech_b_summary = analyze_diff("Mechanism B (Prevent Wheat Liquidity Cow Acceleration)", "mech_b")
    mech_a_summary = analyze_diff("Mechanism A (Preserve Sheep-Compatible Pasture Capacity)", "mech_a")

    with open("scratch/ablation_pasture_mechanisms_50seeds.json", "w") as f:
        json.dump({
            "raw_q50": q50_summary,
            "mech_b": mech_b_summary,
            "mech_a": mech_a_summary,
            "results": results
        }, f, indent=2)

if __name__ == "__main__":
    main()
