"""
Factorial Economic Interaction Matrix (100 Matched Seeds 1000-1099)
Tests isolated economic mechanisms and their multi-factor interaction combinations:
Isolated:
1. Baseline (ARM A)
2. Worker Cap (11 Hands) [ARM B]
3. Fertilizer Rationalization (No Wheat Fert) [ARM C]
4. Strawberry Harvest Batching (>= 2) [ARM D]
5. Cow Priority & Day-5 Unlock [ARM E]
6. JIT Feed Buffering [ARM F]
7. Terminal Pocket Flush [ARM G]

Interactions:
8.  Fertilizer + Cow Priority (C + E)
9.  Fertilizer + Worker Cap (C + B)
10. Cow Priority + Worker Cap (E + B)
11. Fertilizer + Cow Priority + Worker Cap (C + E + B)
12. Full Synthesized (ARM I)
"""

import sys
import os
import json
import time
from collections import defaultdict
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import kaggle_environments
from scratch.build_economic_arms import (
    ArmABaseline, ArmBWorkerCap, ArmCFertilizerRational,
    ArmDStrawberryBatch, ArmELivestockPriority, ArmFFeedBuffering,
    ArmGTerminalFlush, ArmISynthesized
)
from candidates.candidate_cl_coordinated_v1 import (
    ClosedLoopCoordinatedV1, _fib, _dist, _quad, _bfs_step,
    BOARD, TPD, SHED_ACCESS, WELL_ACCESS, CROPS_DEF,
    PASTURE_SLOTS, PASTURE_SPECIES, MELON_TILES_D0,
    MELON_DESIGNATED_TILES, WHEAT_TILES_D0, SELLABLE,
    PRODUCE_TO_DROP, BASE_PRICES
)

# ---------------------------------------------------------------------------
# Interaction Classes
# ---------------------------------------------------------------------------

# 8. Fertilizer + Cow Priority (C + E)
class ArmInter_Fert_Cow(ArmCFertilizerRational):
    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        orders = super()._macro_market(step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs)
        cows_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "COW")
        sheep_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "SHEEP")
        cows_inv = sum(int(inv.get("COW", 0) or 0) for inv in invs)
        sheep_inv = sum(int(inv.get("SHEEP", 0) or 0) for inv in invs)
        cows_tot = cows_f + int(shed.get("COW", 0) or 0) + cows_inv
        sheep_tot = sheep_f + int(shed.get("SHEEP", 0) or 0) + sheep_inv
        n_animals = cows_tot + sheep_tot
        
        filtered = [o for o in orders if not (o and o[0] == "BUY_ANIMAL")]
        shed_anim_count = int(shed.get("COW", 0) or 0) + int(shed.get("SHEEP", 0) or 0) + cows_inv + sheep_inv
        
        if shed_anim_count == 0 and hour == 0 and n_animals < 14:
            if ("NE" in quads or (len(quads) == 1 and day >= 5)) and 5 <= day <= 22 and len(filtered) < 8:
                target_cows = 8
                target_sheep = 6
                cows_needed = max(0, target_cows - cows_tot)
                sheep_needed = max(0, target_sheep - sheep_tot)
                
                m_rem = money
                if cows_needed > 0 and m_rem >= 650:
                    can_buy_c = min(cows_needed, min(2, int((m_rem - 250) // 400)))
                    if can_buy_c > 0:
                        filtered.append(["BUY_ANIMAL", "COW", can_buy_c])
                        m_rem -= can_buy_c * 400
                        cows_tot += can_buy_c
                if sheep_needed > 0 and m_rem >= 750 and len(filtered) < 8:
                    can_buy_s = min(sheep_needed, min(3, int((m_rem - 250) // 500)))
                    if can_buy_s > 0:
                        filtered.append(["BUY_ANIMAL", "SHEEP", can_buy_s])
                        m_rem -= can_buy_s * 500
                        sheep_tot += can_buy_s
                        
        return filtered[:10]


# 9. Fertilizer + Worker Cap (C + B)
class ArmInter_Fert_Cap(ArmCFertilizerRational):
    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        orders = super()._macro_market(step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs)
        filtered_orders = []
        cur_h = hired
        for order in orders:
            if order and order[0] == "HIRE":
                if cur_h < 11:
                    filtered_orders.append(order)
                    cur_h += 1
            else:
                filtered_orders.append(order)
        return filtered_orders[:10]


# 10. Cow Priority + Worker Cap (E + B)
class ArmInter_Cow_Cap(ArmELivestockPriority):
    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        orders = super()._macro_market(step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs)
        filtered_orders = []
        cur_h = hired
        for order in orders:
            if order and order[0] == "HIRE":
                if cur_h < 11:
                    filtered_orders.append(order)
                    cur_h += 1
            else:
                filtered_orders.append(order)
        return filtered_orders[:10]


# 11. Fertilizer + Cow Priority + Worker Cap (C + E + B)
class ArmInter_Fert_Cow_Cap(ArmInter_Fert_Cow):
    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        orders = super()._macro_market(step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs)
        filtered_orders = []
        cur_h = hired
        for order in orders:
            if order and order[0] == "HIRE":
                if cur_h < 11:
                    filtered_orders.append(order)
                    cur_h += 1
            else:
                filtered_orders.append(order)
        return filtered_orders[:10]


ARM_CONFIGS = {
    "ARM_A (Baseline)": ArmABaseline,
    "ARM_B (Worker Cap 11)": ArmBWorkerCap,
    "ARM_C (Fertilizer Rational)": ArmCFertilizerRational,
    "ARM_D (Strawberry >= 2)": ArmDStrawberryBatch,
    "ARM_E (Cow Priority Day 5)": ArmELivestockPriority,
    "ARM_F (JIT Feed 1.2x)": ArmFFeedBuffering,
    "ARM_G (Terminal Flush)": ArmGTerminalFlush,
    "INTER_Fert_Cow (C + E)": ArmInter_Fert_Cow,
    "INTER_Fert_Cap (C + B)": ArmInter_Fert_Cap,
    "INTER_Cow_Cap (E + B)": ArmInter_Cow_Cap,
    "INTER_Fert_Cow_Cap (C + E + B)": ArmInter_Fert_Cow_Cap,
    "ARM_I (Synthesized)": ArmISynthesized
}

def _run_single_match(arm_name, seed, seat=0):
    cls = ARM_CONFIGS[arm_name]
    agent_inst = cls()
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    agents = [agent_inst, "starter"] if seat == 0 else ["starter", agent_inst]
    
    try:
        env.run(agents)
        steps = env.steps
        p = seat
        reward = float(steps[-1][p].get("reward") or 0.0)
        
        prod_count = 0
        move_count = 0
        idle_count = 0
        
        for s_idx in range(1, len(steps)):
            act = steps[s_idx][p].get("action") or {}
            f_act = act.get("farmer") or ["PASS"]
            h_acts = act.get("hands") or []
            for w_act in [f_act] + h_acts:
                cmd = w_act[0] if isinstance(w_act, list) and len(w_act) > 0 else (w_act if isinstance(w_act, str) else "PASS")
                if cmd in ("NORTH", "SOUTH", "EAST", "WEST"):
                    move_count += 1
                elif cmd == "PASS":
                    idle_count += 1
                else:
                    prod_count += 1
                    
        return {
            "arm": arm_name,
            "seed": seed,
            "reward": reward,
            "prod": prod_count,
            "move": move_count,
            "idle": idle_count,
            "error": None
        }
    except Exception as e:
        return {
            "arm": arm_name,
            "seed": seed,
            "reward": 0.0,
            "prod": 0,
            "move": 0,
            "idle": 0,
            "error": str(e)
        }

def run_factorial_matrix(seeds=range(1000, 1100), max_workers=10):
    tasks = []
    for arm_name in ARM_CONFIGS:
        for i, s in enumerate(seeds):
            tasks.append((arm_name, s, i % 2))
            
    print(f"\nRunning Factorial Interaction Study ({len(ARM_CONFIGS)} Arms x {len(seeds)} Seeds = {len(tasks)} Matches)...")
    t0 = time.time()
    results_by_arm = defaultdict(list)
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_run_single_match, arm, s, seat): (arm, s) for arm, s, seat in tasks}
        for f in as_completed(futures):
            res = f.result()
            results_by_arm[res["arm"]].append(res)
            done = sum(len(v) for v in results_by_arm.values())
            if done % 100 == 0 or done == len(tasks):
                print(f"  Completed {done}/{len(tasks)} matches in {time.time()-t0:.1f}s...")
                
    elapsed = time.time() - t0
    
    # Calculate baseline
    base_rews = np.array([r["reward"] for r in results_by_arm["ARM_A (Baseline)"]])
    base_mean = float(np.mean(base_rews))
    
    summary = []
    for arm_name in ARM_CONFIGS:
        res_list = results_by_arm[arm_name]
        rews = np.array([r["reward"] for r in res_list])
        prods = np.array([r["prod"] for r in res_list])
        moves = np.array([r["move"] for r in res_list])
        idles = np.array([r["idle"] for r in res_list])
        
        m_rew = float(np.mean(rews))
        lift = m_rew - base_mean
        
        row = {
            "arm": arm_name,
            "mean_reward": m_rew,
            "std_reward": float(np.std(rews)),
            "median_reward": float(np.median(rews)),
            "prod": float(np.mean(prods)),
            "move": float(np.mean(moves)),
            "idle": float(np.mean(idles)),
            "lift_vs_baseline": lift
        }
        summary.append(row)
        
    out_path = os.path.join(PROJECT_ROOT, "scratch", "factorial_economic_interactions_results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
        
    print("\n" + "=" * 105)
    print("FACTORIAL ECONOMIC INTERACTION MATRIX (N = 100 Matched Seeds 1000-1099)")
    print("=" * 105)
    print(f"{'ARM / CONFIGURATION':<32} | {'REWARD (MEAN  STD)':<24} | {'MEDIAN ($)':<11} | {'PROD':<7} | {'MOVES':<7} | {'IDLE':<6} | {'CAUSAL LIFT':<13}")
    print("-" * 105)
    for r in summary:
        print(f"{r['arm']:<32} | ${r['mean_reward']:10,.1f}  ${r['std_reward']:8,.1f} | ${r['median_reward']:9,.1f} | {r['prod']:7.1f} | {r['move']:7.1f} | {r['idle']:6.1f} | {r['lift_vs_baseline']:+10,.1f}")
    print("=" * 105)
    
    return summary

if __name__ == "__main__":
    run_factorial_matrix()
