import sys
import os
import json
from collections import defaultdict, Counter
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
import kaggle_environments

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from candidates.candidate_cl_economic_v1 import ClosedLoopEconomicV1
import candidates.slot2_aethel_refined_v2 as v2_mod

def run_baseline_match(args):
    seed, p0_type, p1_type = args
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg, debug=False)
    
    agent0 = ClosedLoopEconomicV1() if p0_type == "CL" else v2_mod.agent
    agent1 = ClosedLoopEconomicV1() if p1_type == "CL" else v2_mod.agent
    
    env.run([agent0, agent1])
    steps = env.steps
    total_steps = len(steps)
    
    def extract_full_telemetry(p_idx):
        harvested_units = Counter()
        fertilizer_collected = 0
        feed_consumed = 0
        
        for s_idx in range(1, total_steps):
            prev_f = steps[s_idx - 1][0]["observation"]["farms"][p_idx]
            act = steps[s_idx][p_idx].get("action") or {}
            all_acts = [act.get("farmer") or ["PASS"]] + (act.get("hands") or [])
            workers = [tuple(prev_f["farmer"])] + [tuple(h) for h in prev_f["hands"]]
            
            for w_idx, a in enumerate(all_acts):
                if not a: continue
                op = a[0]
                pos = workers[w_idx] if w_idx < len(workers) else (0, 0)
                t = prev_f["tiles"][pos[1]][pos[0]] if 0 <= pos[1] < 10 and 0 <= pos[0] < 10 else None
                if op == "HARVEST" and isinstance(t, dict):
                    k = t.get("kind")
                    yu = int(t.get("yield_units", 0) or 0)
                    if k == "PLANT":
                        harvested_units[t.get("crop", "UNKNOWN")] += yu
                    elif k == "PASTURE":
                        harvested_units[t.get("animal", "UNKNOWN")] += yu
                elif op == "COLLECT_FERTILIZER":
                    fertilizer_collected += 1
                elif op == "FEED":
                    feed_consumed += 1

        final_farm = steps[-1][0]["observation"]["farms"][p_idx]
        final_priv = steps[-1][p_idx]["observation"].get("private") or {}
        shed = final_priv.get("shed") or {}
        invs = final_priv.get("inventories") or []
        
        total_inv = Counter()
        for it, qty in shed.items():
            total_inv[it] += int(qty or 0)
        for inv in invs:
            for it, qty in inv.items():
                total_inv[it] += int(qty or 0)

        terminal_money = float(final_farm.get("money") or 0.0)
        terminal_reward = float(steps[-1][p_idx].get("reward") or 0.0)
        
        return {
            "reward": terminal_reward,
            "money": terminal_money,
            "harvested_units": dict(harvested_units),
            "fertilizer_collected": fertilizer_collected,
            "feed_consumed": feed_consumed,
            "terminal_inventory": dict(total_inv),
            "shed_inventory": dict(shed)
        }

    p0_data = extract_full_telemetry(0)
    p1_data = extract_full_telemetry(1)
    
    cl_seat = 0 if p0_type == "CL" else 1
    v2_seat = 1 if p0_type == "CL" else 0
    cl_data = p0_data if cl_seat == 0 else p1_data
    v2_data = p1_data if cl_seat == 0 else p0_data
    
    return {
        "seed": seed,
        "cl_seat": cl_seat,
        "v2_seat": v2_seat,
        "cl_reward": cl_data["reward"],
        "v2_reward": v2_data["reward"],
        "margin": cl_data["reward"] - v2_data["reward"],
        "cl_telemetry": cl_data,
        "v2_telemetry": v2_data
    }

if __name__ == "__main__":
    seeds = list(range(1000, 1010))
    tasks = []
    # 10 matches: CL Seat 0 vs V2 Seat 1
    for s in seeds:
        tasks.append((s, "CL", "V2"))
    # 10 matches: V2 Seat 0 vs CL Seat 1
    for s in seeds:
        tasks.append((s, "V2", "CL"))
        
    print(f"Generating Exact Raw H2H Baseline ({len(tasks)} matches across Seeds 1000-1009)...")
    results = []
    with ProcessPoolExecutor(max_workers=10) as ex:
        futs = [ex.submit(run_baseline_match, t) for t in tasks]
        for f in as_completed(futs):
            results.append(f.result())
            
    results.sort(key=lambda x: (x["seed"], x["cl_seat"]))
    
    with open("scratch/exact_raw_h2h_baseline.json", "w") as f:
        json.dump(results, f, indent=2)
        
    print(f"\nSaved {len(results)} exact H2H match baseline records to scratch/exact_raw_h2h_baseline.json")
    
    # Summary statistics
    cl_rews = [r["cl_reward"] for r in results]
    v2_rews = [r["v2_reward"] for r in results]
    margins = [r["margin"] for r in results]
    
    print("\n" + "="*90)
    print(f"{'Seed':<6} | {'CL Seat':<7} | {'CL Reward ($)':<14} | {'V2 Reward ($)':<14} | {'Margin (CL - V2)':<16} | {'Straw (CL/V2)':<14} | {'Wool (CL/V2)':<14}")
    print("-" * 90)
    for r in results:
        cl_s = r["cl_telemetry"]["harvested_units"].get("STRAWBERRY", 0)
        v2_s = r["v2_telemetry"]["harvested_units"].get("STRAWBERRY", 0)
        cl_w = r["cl_telemetry"]["harvested_units"].get("SHEEP", 0)
        v2_w = r["v2_telemetry"]["harvested_units"].get("SHEEP", 0)
        print(f"{r['seed']:<6} | {r['cl_seat']:<7} | ${r['cl_reward']:12.2f} | ${r['v2_reward']:12.2f} | ${r['margin']:14.2f} | {cl_s:5.0f} / {v2_s:<5.0f} | {cl_w:5.0f} / {v2_w:<5.0f}")
        
    print("-" * 90)
    print(f"CL Mean: ${np.mean(cl_rews):.2f} ± ${np.std(cl_rews):.2f} (Median: ${np.median(cl_rews):.2f}, 95% CI: ±${1.96*np.std(cl_rews)/np.sqrt(len(cl_rews)):.2f})")
    print(f"V2 Mean: ${np.mean(v2_rews):.2f} ± ${np.std(v2_rews):.2f} (Median: ${np.median(v2_rews):.2f}, 95% CI: ±${1.96*np.std(v2_rews)/np.sqrt(len(v2_rews)):.2f})")
    print(f"Mean Margin: ${np.mean(margins):.2f} ± ${np.std(margins):.2f} (Win Rate: {np.mean([1 if m > 0 else 0 for m in margins])*100:.1f}%)")
