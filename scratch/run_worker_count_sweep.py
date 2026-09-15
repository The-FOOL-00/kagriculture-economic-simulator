"""
Controlled Worker Count Sweep & Marginal Value of Labor
Runs 100 matched games (Seeds 1000-1099) across 5 worker-count caps:
- 9 hands (10 workers total)
- 10 hands (11 workers total)
- 11 hands (12 workers total)
- 12 hands (13 workers total)
- 13 hands (14 workers total, default baseline)
Measures:
- Reward, Revenue, Hiring Fees
- Movement turns, Productive turns, Idle turns, Shed visits
- Unsold terminal inventory value
- Marginal economic contribution per worker
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
from candidates.candidate_cl_coordinated_v1 import ClosedLoopCoordinatedV1, _fib

SEEDS = list(range(1000, 1100))
CAPS = [9, 10, 11, 12, 13]

class WorkerCappedAgent(ClosedLoopCoordinatedV1):
    def __init__(self, max_hands=11):
        super().__init__()
        self.max_hands = max_hands

    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        orders = super()._macro_market(step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs)
        filtered = []
        cur_h = hired
        for o in orders:
            if o and o[0] == "HIRE":
                if cur_h < self.max_hands:
                    filtered.append(o)
                    cur_h += 1
            else:
                filtered.append(o)
        return filtered[:10]

def _run_single_worker_game(cap, seed, seat=0):
    agent_inst = WorkerCappedAgent(max_hands=cap)
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    agents = [agent_inst, "starter"] if seat == 0 else ["starter", agent_inst]
    
    try:
        env.run(agents)
        steps = env.steps
        total_steps = len(steps)
        p = seat
        
        final_reward = float(steps[-1][p].get("reward") or 0.0)
        final_obs = steps[-1][p]["observation"]
        final_farm = final_obs["farms"][p]
        final_shed = (final_obs.get("private") or {}).get("shed") or {}
        final_invs = (final_obs.get("private") or {}).get("inventories") or []
        
        prod_count = 0
        move_count = 0
        idle_count = 0
        shed_count = 0
        
        # Action classification
        for s_idx in range(1, total_steps):
            act = steps[s_idx][p].get("action") or {}
            f_act = act.get("farmer") or ["PASS"]
            h_acts = act.get("hands") or []
            for w_act in [f_act] + h_acts:
                cmd = w_act[0] if isinstance(w_act, list) and len(w_act) > 0 else (w_act if isinstance(w_act, str) else "PASS")
                if cmd in ("NORTH", "SOUTH", "EAST", "WEST"):
                    move_count += 1
                elif cmd == "PASS":
                    idle_count += 1
                elif cmd in ("DROP", "PICKUP"):
                    shed_count += 1
                    prod_count += 1
                else:
                    prod_count += 1
                    
        # Hiring fees
        hired_hands = len(final_farm.get("hands", []))
        hiring_fees = sum(_fib(h) for h in range(hired_hands))
        
        # Terminal unsold value
        m_prices = final_obs.get("market", {}).get("prices", {})
        unsold_val = 0.0
        for it, q in final_shed.items():
            if int(q or 0) > 0:
                unsold_val += int(q) * float(m_prices.get(it, 50))
        for inv in final_invs:
            if isinstance(inv, dict):
                for it, q in inv.items():
                    if int(q or 0) > 0:
                        unsold_val += int(q) * float(m_prices.get(it, 50))
                        
        return {
            "cap": cap,
            "seed": seed,
            "reward": final_reward,
            "hired_hands": hired_hands,
            "hiring_fees": hiring_fees,
            "productive": prod_count,
            "movement": move_count,
            "idle": idle_count,
            "shed": shed_count,
            "unsold_val": unsold_val,
            "error": None
        }
    except Exception as e:
        return {
            "cap": cap,
            "seed": seed,
            "reward": 0.0,
            "hired_hands": 0,
            "hiring_fees": 0,
            "productive": 0,
            "movement": 0,
            "idle": 0,
            "shed": 0,
            "unsold_val": 0.0,
            "error": str(e)
        }

def run_worker_sweep(max_workers=10):
    all_results = {}
    print("=" * 80)
    print("PHASE 3: CONTROLLED WORKER COUNT SWEEP (9, 10, 11, 12, 13 Hands, Seeds 1000-1099)")
    print("=" * 80)
    
    tasks = []
    for cap in CAPS:
        for i, s in enumerate(SEEDS):
            tasks.append((cap, s, i % 2))
            
    t0 = time.time()
    results_by_cap = defaultdict(list)
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_run_single_worker_game, cap, s, seat): (cap, s) for cap, s, seat in tasks}
        for f in as_completed(futures):
            res = f.result()
            results_by_cap[res["cap"]].append(res)
            done = sum(len(v) for v in results_by_cap.values())
            if done % 50 == 0 or done == len(tasks):
                print(f"  Completed {done}/{len(tasks)} games in {time.time()-t0:.1f}s...")
                
    elapsed = time.time() - t0
    
    # Summarize per cap
    summary_table = []
    prev_reward = None
    for cap in sorted(CAPS):
        res_list = results_by_cap[cap]
        rews = np.array([r["reward"] for r in res_list])
        prods = np.array([r["productive"] for r in res_list])
        moves = np.array([r["movement"] for r in res_list])
        idles = np.array([r["idle"] for r in res_list])
        sheds = np.array([r["shed"] for r in res_list])
        fees = np.array([r["hiring_fees"] for r in res_list])
        unsold = np.array([r["unsold_val"] for r in res_list])
        
        mean_r = float(np.mean(rews))
        marginal_gain = (mean_r - prev_reward) if prev_reward is not None else 0.0
        prev_reward = mean_r
        
        row = {
            "cap": cap,
            "mean_reward": mean_r,
            "std_reward": float(np.std(rews)),
            "median_reward": float(np.median(rews)),
            "productive": float(np.mean(prods)),
            "movement": float(np.mean(moves)),
            "idle": float(np.mean(idles)),
            "shed": float(np.mean(sheds)),
            "hiring_fees": float(np.mean(fees)),
            "unsold_val": float(np.mean(unsold)),
            "prod_move_ratio": float(np.mean(prods) / np.mean(moves)),
            "marginal_reward_gain": marginal_gain
        }
        summary_table.append(row)
        
    out_path = os.path.join(PROJECT_ROOT, "scratch", "worker_count_sweep_results.json")
    with open(out_path, "w") as f:
        json.dump(summary_table, f, indent=2)
        
    print("\n" + "=" * 95)
    print("CONTROLLED WORKER COUNT EXPERIMENT RESULTS (N = 100 Seeds per Cap)")
    print("=" * 95)
    print(f"{'CAP':<8} | {'REWARD (MEAN ± STD)':<24} | {'MEDIAN ($)':<11} | {'PROD':<7} | {'MOVES':<7} | {'IDLE':<6} | {'PROD/MOV':<8} | {'FEES':<6} | {'MARGINAL GAIN':<13}")
    print("-" * 95)
    for r in summary_table:
        print(f"{r['cap']:<2} hands | ${r['mean_reward']:10,.1f} ± ${r['std_reward']:8,.1f} | ${r['median_reward']:9,.1f} | {r['productive']:7.1f} | {r['movement']:7.1f} | {r['idle']:6.1f} | {r['prod_move_ratio']:8.3f} | ${r['hiring_fees']:5.0f} | {r['marginal_reward_gain']:+10,.1f}")
    print("=" * 95)

if __name__ == "__main__":
    run_worker_sweep()
