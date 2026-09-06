import os
import sys
import time
import json
import numpy as np
import pandas as pd
from concurrent.futures import ProcessPoolExecutor
from kaggle_environments import make

# 1. Test behavioral equivalence across Candidates A, B, C, D, E, F, G, H
def run_single_equivalence_check(seed, cand_name, cand_path, opp_path="main.py"):
    cfg = {"episodeSteps": 720, "seed": seed}
    env = make("kaggriculture", configuration=cfg, debug=False)
    env.run([cand_path, opp_path])
    
    # Extract trajectory info
    steps = env.steps
    actions = [s[0].action for s in steps]
    r_cand = float(steps[-1][0].reward or 0)
    r_opp = float(steps[-1][1].reward or 0)
    
    # State snapshots at Days 1 (24), 5 (120), 10 (240), 15 (360), 30 (719)
    def snap(step_idx):
        obs = steps[step_idx][0].observation
        farms = obs.get("farms", [{}, {}])
        f = farms[0]
        money = f.get("money", 0)
        hands = len(f.get("hands", []))
        tiles = f.get("tiles", [])
        cows = sum(1 for row in tiles for t in row if isinstance(t, dict) and t.get("animal") == "COW")
        sheep = sum(1 for row in tiles for t in row if isinstance(t, dict) and t.get("animal") == "SHEEP")
        geese = sum(1 for row in tiles for t in row if isinstance(t, dict) and t.get("animal") == "GOOSE")
        quads = len(f.get("unlocked_quadrants", []))
        return {
            'money': money,
            'hands': hands,
            'cows': cows,
            'sheep': sheep,
            'geese': geese,
            'quads': quads
        }
        
    snaps = {
        'd1': snap(24),
        'd5': snap(120),
        'd10': snap(240),
        'd15': snap(360),
        'd30': snap(719)
    }
    
    # Inventory at end
    final_obs = steps[-1][0].observation
    final_shed = (final_obs.get("private") or {}).get("shed") or {}
    
    # Market order stats
    market_orders = []
    for s in steps:
        act = s[0].action or {}
        for o in act.get("market", []) or []:
            if isinstance(o, list) and len(o) >= 2:
                market_orders.append(o)
                
    return {
        'cand': cand_name,
        'seed': seed,
        'reward': r_cand,
        'opp_reward': r_opp,
        'margin': r_cand - r_opp,
        'actions_hash': hash(str(actions)),
        'actions': actions,
        'snaps': snaps,
        'final_shed': final_shed,
        'market_orders_count': len(market_orders)
    }

if __name__ == "__main__":
    cands = {
        "A": "candidates/counterstrategy_ablation/candidate_A.py",
        "B": "candidates/counterstrategy_ablation/candidate_B.py",
        "C": "candidates/counterstrategy_ablation/candidate_C.py",
        "D": "candidates/counterstrategy_ablation/candidate_D.py",
        "E": "candidates/counterstrategy_ablation/candidate_E.py",
        "F": "candidates/counterstrategy_ablation/candidate_F.py",
        "G": "candidates/counterstrategy_ablation/candidate_G.py",
        "H": "candidates/counterstrategy_ablation/candidate_H.py"
    }
    
    test_seeds = [42, 100, 2026, 777, 999, 1234, 5555, 8888, 10101, 20202]
    tasks = []
    for c_name, c_path in cands.items():
        for s in test_seeds:
            tasks.append((s, c_name, c_path))
            
    print(f"Running {len(tasks)} equivalence evaluation runs with 6 workers...")
    t0 = time.time()
    results = {}
    with ProcessPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(run_single_equivalence_check, s, c_name, c_path) for s, c_name, c_path in tasks]
        for f in futures:
            res = f.result()
            c = res['cand']
            s = res['seed']
            results.setdefault(c, {})[s] = res
            
    print(f"Completed in {time.time() - t0:.1f}s")
    
    # Compare pairs
    pairs_to_check = [("A", "C"), ("B", "E"), ("D", "G"), ("F", "H")]
    print("\n" + "=" * 80)
    print("EXACT PAIRWISE BIT-FOR-BIT EQUIVALENCE VERIFICATION")
    print("=" * 80)
    
    for c1, c2 in pairs_to_check:
        print(f"\n--- Checking Candidate {c1} vs Candidate {c2} across {len(test_seeds)} seeds ---")
        identical_actions = True
        identical_rewards = True
        for s in test_seeds:
            r1 = results[c1][s]
            r2 = results[c2][s]
            
            act_match = (r1['actions'] == r2['actions'])
            rew_match = (r1['reward'] == r2['reward'])
            
            if not act_match:
                identical_actions = False
            if not rew_match:
                identical_rewards = False
                
            print(f"Seed {s:5d}: Reward {c1}=${r1['reward']:,.1f} vs {c2}=${r2['reward']:,.1f} | Action Exact Match: {act_match}")
            if not act_match:
                # find first diff step
                for step_i in range(len(r1['actions'])):
                    if r1['actions'][step_i] != r2['actions'][step_i]:
                        print(f"  First diff at step {step_i}: {c1}={r1['actions'][step_i]} vs {c2}={r2['actions'][step_i]}")
                        break
                        
        print(f"RESULT FOR {c1} vs {c2}: Actions Identical = {identical_actions} | Rewards Identical = {identical_rewards}")
        print(f"Status: {'100% INERT IMPLEMENTATION (BIT-IDENTICAL)' if identical_actions else 'BEHAVIORALLY DIVERGENT'}")

    # Output day snapshots for A vs C
    print("\n" + "=" * 80)
    print("DETAILED DAY-BY-DAY TRAJECTORY METRICS (Candidate A vs C on Seed 42)")
    print("=" * 80)
    s42_a = results["A"][42]
    s42_c = results["C"][42]
    for d_key in ['d1', 'd5', 'd10', 'd15', 'd30']:
        print(f"{d_key.upper()}:")
        print(f"  A: Money=${s42_a['snaps'][d_key]['money']:.1f}, Hands={s42_a['snaps'][d_key]['hands']}, Cows={s42_a['snaps'][d_key]['cows']}, Sheep={s42_a['snaps'][d_key]['sheep']}, Quads={s42_a['snaps'][d_key]['quads']}")
        print(f"  C: Money=${s42_c['snaps'][d_key]['money']:.1f}, Hands={s42_c['snaps'][d_key]['hands']}, Cows={s42_c['snaps'][d_key]['cows']}, Sheep={s42_c['snaps'][d_key]['sheep']}, Quads={s42_c['snaps'][d_key]['quads']}")

    with open("scratch/equivalence_audit_summary.json", "w") as f:
        # Save summary without full action lists for brevity
        clean_res = {}
        for c in results:
            clean_res[c] = {}
            for s in results[c]:
                item = dict(results[c][s])
                del item['actions']
                clean_res[c][s] = item
        json.dump(clean_res, f, indent=2)
