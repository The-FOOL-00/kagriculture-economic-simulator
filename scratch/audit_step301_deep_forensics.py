"""
scratch/audit_step301_deep_forensics.py
=======================================
Deep Turn-Level Forensics around Step 301 (Steps 240 to 360):
1. Pairwise diff of all 7 ancestral route action tapes -> research/step301_route_diff.csv
2. Full turn tracing of Population A (V66 >= V54++ + $5k) and Population B (V54++ >= V66 + $5k)
3. Step 300 state vs Step 301 action analysis
4. Shop sequences at Steps 72, 144, 216, 288
5. Tile bonus verification
Outputs:
- research/step301_route_diff.csv
- research/step301_telemetry_deep.json
"""

import os
import sys
import copy
import json
import csv
from collections import defaultdict
import numpy as np
import importlib.util
from kaggle_environments import make

BASE_DIR = os.path.abspath(".")
CANDIDATE_PATHS = {
    "V54++": os.path.join(BASE_DIR, "candidates", "v54_plus_shop.py"),
    "V66": os.path.join(BASE_DIR, "external_repos", "kaggriculture-v66-agent", "main.py"),
}

for p in [BASE_DIR, os.path.dirname(CANDIDATE_PATHS["V54++"]), os.path.dirname(CANDIDATE_PATHS["V66"])]:
    if p not in sys.path:
        sys.path.insert(0, p)

from candidates.v54_plus_shop import mod_v62, agent as fn_v54

spec_v66 = importlib.util.spec_from_file_location("v66_eval", CANDIDATE_PATHS["V66"])
mod_v66 = importlib.util.module_from_spec(spec_v66)
spec_v66.loader.exec_module(mod_v66)
fn_v66 = mod_v66.agent

ROUTES = {
    "Backbone": mod_v62._V56_BACKBONE_ROUTE,
    "Yarn": mod_v62._V56_YARN_ROUTE,
    "Bakery_Yarn": mod_v62._V58_BAKERY_YARN_ROUTE,
    "Recovery": mod_v62._V58_RECOVERY_ROUTE,
    "Ice_Minimax": mod_v62._V58_ICE_MINIMAX_ROUTE,
    "Known_Yarn": mod_v62._V58_KNOWN_YARN_ROUTE,
    "Clone": mod_v62._V58_CLONE_ROUTE,
}

def diff_two_routes(name_a, r_a, name_b, r_b):
    first_diff = None
    diff_steps = []
    commodities = set()
    worker_affected = False
    market_affected = False
    livestock_affected = False
    
    for s in range(240, 361):
        item_a = r_a[s]
        item_b = r_b[s]
        
        f_a, f_b = item_a.get("farmer", []), item_b.get("farmer", [])
        h_a, h_b = item_a.get("hands", []), item_b.get("hands", [])
        m_a, m_b = item_a.get("market", []), item_b.get("market", [])
        
        diff = (f_a != f_b) or (h_a != h_b) or (m_a != m_b)
        if diff:
            if first_diff is None:
                first_diff = s
            diff_steps.append(s)
            
            if h_a != h_b:
                worker_affected = True
            if m_a != m_b:
                market_affected = True
                for ord in (m_a + m_b):
                    if len(ord) >= 2:
                        commodities.add(ord[1])
                        if any(k in str(ord[1]).upper() for k in ["COW", "SHEEP", "WOOL", "MILK"]):
                            livestock_affected = True
            if f_a != f_b:
                for act in [f_a, f_b]:
                    if len(act) >= 2:
                        commodities.add(act[1])
                        if any(k in str(act[1]).upper() for k in ["COW", "SHEEP", "FEED", "CARE"]):
                            livestock_affected = True
                            
    return {
        "route_a": name_a,
        "route_b": name_b,
        "first_diff_step": first_diff if first_diff is not None else -1,
        "all_material_diff_steps": len(diff_steps),
        "commodity_affected": ";".join(sorted(commodities)) if commodities else "NONE",
        "worker_affected": worker_affected,
        "market_affected": market_affected,
        "livestock_affected": livestock_affected,
    }

def main():
    print("1. Performing Pairwise Route Action Tape Diff (Steps 240-360)...")
    route_names = list(ROUTES.keys())
    route_diff_rows = []
    
    for i in range(len(route_names)):
        for j in range(i + 1, len(route_names)):
            na, nb = route_names[i], route_names[j]
            diff_res = diff_two_routes(na, ROUTES[na], nb, ROUTES[nb])
            route_diff_rows.append(diff_res)
            
    print(f"Writing research/step301_route_diff.csv ({len(route_diff_rows)} pairs)...")
    with open("research/step301_route_diff.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "route_a", "route_b", "first_diff_step", "all_material_diff_steps",
            "commodity_affected", "worker_affected", "market_affected", "livestock_affected"
        ])
        writer.writeheader()
        for r in route_diff_rows:
            writer.writerow(r)
            
    print("\n2. Loading 1,000-Match Holdout for Population A and Population B...")
    with open("research/shop216_holdout_results.json") as f:
        matches = json.load(f)
        
    pop_a = [m for m in matches if m["v66_reward"] - m["shop_reward"] >= 5000] # Large V66 wins
    pop_b = [m for m in matches if m["shop_reward"] - m["v66_reward"] >= 5000] # Large V54++ wins
    
    print(f"Population A (V66 >= V54++ + $5k): {len(pop_a)} matches")
    print(f"Population B (V54++ >= V66 + $5k): {len(pop_b)} matches")
    
    # Select all 15 matches from Pop A, and 15 representative matches from Pop B
    np.random.seed(42)
    sample_b_idx = np.random.choice(len(pop_b), size=min(15, len(pop_b)), replace=False)
    selected_matches = [("PopA", m) for m in pop_a] + [("PopB", pop_b[i]) for i in sample_b_idx]
    
    print(f"\n3. Running Full Turn Tracing (Steps 240-360) across {len(selected_matches)} matches...")
    
    telemetry_records = []
    step301_transitions = []
    shop_sequences = defaultdict(list)
    
    for idx, (pop_label, target) in enumerate(selected_matches):
        seed = int(target["seed"])
        seat = int(target["seat"])
        p0_is_v54 = (seat == 0)
        
        agent0 = fn_v54 if p0_is_v54 else fn_v66
        agent1 = fn_v66 if p0_is_v54 else fn_v54
        v54_idx = 0 if p0_is_v54 else 1
        v66_idx = 1 if p0_is_v54 else 0
        
        env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
        env.reset()
        
        step300_state = None
        step301_state = None
        
        shops_at = {}
        
        for s in range(361):
            o0, o1 = env.state[0].observation, env.state[1].observation
            o0["step"], o1["step"] = s, s
            
            # Record shops at milestones
            if s in [72, 144, 216, 288]:
                town = o0.get("town", {}) or {}
                shops_at[s] = list(town.get("unlocked_shops", []) or [])
                
            act0 = agent0(o0, env.configuration)
            act1 = agent1(o1, env.configuration)
            
            if s == 300:
                f0, f1 = o0.get("farms", [{}])[0], o1.get("farms", [{}])[1]
                p0_priv, p1_priv = o0.get("private", {}), o1.get("private", {})
                mkt = o0.get("market", {})
                step300_state = {
                    "v54_money": f0.get("money") if p0_is_v54 else f1.get("money"),
                    "v66_money": f1.get("money") if p0_is_v54 else f0.get("money"),
                    "v54_shed_wheat": (p0_priv if p0_is_v54 else p1_priv).get("shed", {}).get("WHEAT", 0),
                    "v66_shed_wheat": (p1_priv if p0_is_v54 else p0_priv).get("shed", {}).get("WHEAT", 0),
                    "v54_cows": len((p0_priv if p0_is_v54 else p1_priv).get("cows", [])),
                    "v66_cows": len((p1_priv if p0_is_v54 else p0_priv).get("cows", [])),
                    "v54_sheep": len((p0_priv if p0_is_v54 else p1_priv).get("sheep", [])),
                    "v66_sheep": len((p1_priv if p0_is_v54 else p0_priv).get("sheep", [])),
                    "wheat_price": mkt.get("prices", {}).get("WHEAT", 0.0),
                    "wool_price": mkt.get("prices", {}).get("WOOL", 0.0),
                    "milk_price": mkt.get("prices", {}).get("MILK", 0.0),
                }
                
            if s == 301:
                v54_act = act0 if p0_is_v54 else act1
                v66_act = act1 if p0_is_v54 else act0
                
                step301_transitions.append({
                    "pop": pop_label,
                    "seed": seed,
                    "seat": seat,
                    "step300_state": step300_state,
                    "v54_act_301": {
                        "farmer": v54_act.get("farmer"),
                        "market": v54_act.get("market"),
                        "hands_count": len(v54_act.get("hands", []) or [])
                    },
                    "v66_act_301": {
                        "farmer": v66_act.get("farmer"),
                        "market": v66_act.get("market"),
                        "hands_count": len(v66_act.get("hands", []) or [])
                    },
                    "shops": shops_at,
                    "margin": target["shop_reward"] - target["v66_reward"]
                })
                
            env.step([act0, act1])
            
        shop_sequences[pop_label].append({
            "seed": seed,
            "shops": shops_at,
            "margin": target["shop_reward"] - target["v66_reward"]
        })
        print(f"[{idx+1}/{len(selected_matches)}] {pop_label} Seed {seed} Seat {seat} Traced through Step 360")
        
    print("\nWriting research/step301_telemetry_deep.json...")
    with open("research/step301_telemetry_deep.json", "w") as f:
        json.dump({
            "step301_transitions": step301_transitions,
            "shop_sequences": shop_sequences
        }, f, indent=2)
        
    print("Step 301 deep forensics complete!")

if __name__ == "__main__":
    main()
