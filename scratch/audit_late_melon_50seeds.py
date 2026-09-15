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
from scratch.audit_late_melon_deep import CLLateMelonCutoff

def run_match_50seeds(args):
    arm, seed = args
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg, debug=False)
    
    agent_inst = ClosedLoopEconomicV1() if arm == "BASELINE" else CLLateMelonCutoff(cutoff_day=18)
    env.run([agent_inst, "starter"])
    steps = env.steps
    total_steps = len(steps)
    
    harvest_counts = Counter()
    total_harvs = 0
    total_plants = 0
    melon_plants = 0
    
    for s_idx in range(1, total_steps):
        prev_f = steps[s_idx - 1][0]["observation"]["farms"][0]
        act = steps[s_idx][0].get("action") or {}
        all_acts = [act.get("farmer") or ["PASS"]] + (act.get("hands") or [])
        workers = [tuple(prev_f["farmer"])] + [tuple(h) for h in prev_f["hands"]]
        
        for w_idx, a in enumerate(all_acts):
            if not a: continue
            op = a[0]
            if op == "HARVEST":
                total_harvs += 1
                pos = workers[w_idx] if w_idx < len(workers) else (0, 0)
                t = prev_f["tiles"][pos[1]][pos[0]] if 0 <= pos[1] < 10 and 0 <= pos[0] < 10 else None
                if isinstance(t, dict):
                    yu = int(t.get("yield_units", 0) or 0)
                    if t.get("kind") == "PLANT": harvest_counts[t.get("crop")] += yu
                    elif t.get("kind") == "PASTURE": harvest_counts[t.get("animal")] += yu
            elif op == "PLANT":
                total_plants += 1
                if len(a) > 1 and a[1] == "MELON": melon_plants += 1
                
    reward = float(steps[-1][0].get("reward") or 0.0)
    terminal_cash = float(steps[-1][0]["observation"]["farms"][0].get("money") or 0.0)
    
    return {
        "arm": arm,
        "seed": seed,
        "reward": reward,
        "terminal_cash": terminal_cash,
        "harvests": total_harvs,
        "plants": total_plants,
        "melon_plants": melon_plants,
        "straw": harvest_counts.get("STRAWBERRY", 0),
        "wool": harvest_counts.get("SHEEP", 0),
        "wheat": harvest_counts.get("WHEAT", 0),
        "melon": harvest_counts.get("MELON", 0),
        "milk": harvest_counts.get("COW", 0)
    }

if __name__ == "__main__":
    seeds = list(range(1000, 1050))
    tasks = [(arm, s) for arm in ("BASELINE", "CUTOFF_D18") for s in seeds]
    
    print(f"Running 50-Seed Validation for Late-Melon Cutoff D18 ({len(tasks)} matches)...")
    results = defaultdict(list)
    with ProcessPoolExecutor(max_workers=10) as ex:
        futs = [ex.submit(run_match_50seeds, t) for t in tasks]
        for f in as_completed(futs):
            res = f.result()
            results[res["arm"]].append(res)
            
    with open("scratch/audit_late_melon_50seeds_results.json", "w") as f:
        json.dump({k: v for k, v in results.items()}, f, indent=2)
        
    base_lst = sorted(results["BASELINE"], key=lambda x: x["seed"])
    cut_lst = sorted(results["CUTOFF_D18"], key=lambda x: x["seed"])
    
    b_rews = np.array([x["reward"] for x in base_lst])
    c_rews = np.array([x["reward"] for x in cut_lst])
    deltas = c_rews - b_rews
    
    print("\n" + "="*80)
    print(f"50-SEED MATCHED VALIDATION RESULTS (Seeds 1000–1049, N=50)")
    print("="*80)
    print(f"Baseline Mean Reward:   ${np.mean(b_rews):10.2f} ± ${np.std(b_rews):.2f} (Median: ${np.median(b_rews):.2f})")
    print(f"Cutoff D18 Mean Reward: ${np.mean(c_rews):10.2f} ± ${np.std(c_rews):.2f} (Median: ${np.median(c_rews):.2f})")
    print(f"Mean Paired Delta:      ${np.mean(deltas):+10.2f} ± ${np.std(deltas):.2f}")
    print(f"95% CI on Mean Delta:   [${np.mean(deltas) - 1.96*np.std(deltas)/np.sqrt(50):.2f}, ${np.mean(deltas) + 1.96*np.std(deltas)/np.sqrt(50):.2f}]")
    print(f"Win Rate (Cutoff > Base): {np.mean(deltas > 0)*100:.1f}%")
    print(f"Melon Plantings: Baseline {np.mean([x['melon_plants'] for x in base_lst]):.1f} vs Cutoff {np.mean([x['melon_plants'] for x in cut_lst]):.1f}")
    print(f"Melon Harvested Yield: Baseline {np.mean([x['melon'] for x in base_lst]):.1f}u vs Cutoff {np.mean([x['melon'] for x in cut_lst]):.1f}u")
    print(f"Strawberry Yield: Baseline {np.mean([x['straw'] for x in base_lst]):.1f}u vs Cutoff {np.mean([x['straw'] for x in cut_lst]):.1f}u")
