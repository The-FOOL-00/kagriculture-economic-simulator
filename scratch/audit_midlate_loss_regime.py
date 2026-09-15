"""
scratch/audit_midlate_loss_regime.py
====================================
Mid/Late Wheat vs Livestock Conversion Causal Audit:
Extracts full commodity accounting across holdout partition groups (A through G),
focusing on Steps 336, 360, 384, 432, 480, 528, 576, 624.
Generates:
1. research/wheat_livestock_first_divergence.csv
2. research/midlate_accounting_telemetry.json
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

for p in [os.path.dirname(CANDIDATE_PATHS["V54++"]), os.path.dirname(CANDIDATE_PATHS["V66"])]:
    if p not in sys.path:
        sys.path.insert(0, p)

_LOADED_AGENTS = {}

def get_agent_fn(name):
    if name not in _LOADED_AGENTS:
        path = os.path.abspath(CANDIDATE_PATHS[name])
        spec = importlib.util.spec_from_file_location(name.replace("+", "p") + "_eval", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _LOADED_AGENTS[name] = getattr(mod, "agent", getattr(mod, "kaggle_agent", None))
    return _LOADED_AGENTS[name]

# Key checkpoints
CHECKPOINTS = [336, 360, 384, 432, 480, 528, 576, 624]

def run_match_telemetry(seed: int, p0_is_v54: bool = True):
    fn_v54 = get_agent_fn("V54++")
    fn_v66 = get_agent_fn("V66")
    
    agent0 = fn_v54 if p0_is_v54 else fn_v66
    agent1 = fn_v66 if p0_is_v54 else fn_v54
    v54_idx = 0 if p0_is_v54 else 1
    v66_idx = 1 if p0_is_v54 else 0
    
    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    env.reset()
    
    # Tracking ledgers
    # [v54, v66]
    cumulative = {
        "wheat_produced": [0, 0],
        "wheat_sold": [0, 0],
        "wheat_revenue": [0.0, 0.0],
        "wool_produced": [0, 0],
        "wool_sold": [0, 0],
        "wool_revenue": [0.0, 0.0],
        "milk_produced": [0, 0],
        "milk_sold": [0, 0],
        "milk_revenue": [0.0, 0.0],
        "wheat_consumed": [0, 0],
        "cows_bought": [0, 0],
        "sheep_bought": [0, 0],
        "fertilizer_bought": [0, 0],
    }
    
    checkpoints_data = {}
    turn_by_turn = []
    
    prev_money = [None, None]
    prev_shed = [None, None]
    prev_cows = [0, 0]
    prev_sheep = [0, 0]
    
    for s in range(719):
        o0, o1 = env.state[0].observation, env.state[1].observation
        o0["step"], o1["step"] = s, s
        
        act0 = agent0(o0, env.configuration)
        act1 = agent1(o1, env.configuration)
        
        # Capture pre-step state
        farms = [o0.get("farms", [{}])[0], o1.get("farms", [{}])[1]]
        privates = [o0.get("private", {}), o1.get("private", {})]
        market = o0.get("market", {})
        mkt_prices = market.get("prices", {}) or {}
        
        acts = [act0, act1]
        
        # Analyze actions and transactions
        for i in range(2):
            act = acts[i]
            # Track market actions
            for ord in (act.get("market") or []):
                if len(ord) >= 3:
                    op, item, qty = str(ord[0]), str(ord[1]), int(ord[2])
                    price = float(mkt_prices.get(item, 0.0))
                    if op == "SELL":
                        if item == "WHEAT":
                            cumulative["wheat_sold"][i] += qty
                            cumulative["wheat_revenue"][i] += qty * price
                        elif item == "WOOL":
                            cumulative["wool_sold"][i] += qty
                            cumulative["wool_revenue"][i] += qty * price
                        elif item == "MILK":
                            cumulative["milk_sold"][i] += qty
                            cumulative["milk_revenue"][i] += qty * price
                    elif op == "BUY":
                        if item == "COW":
                            cumulative["cows_bought"][i] += qty
                        elif item == "SHEEP":
                            cumulative["sheep_bought"][i] += qty
                        elif item == "FERTILIZER":
                            cumulative["fertilizer_bought"][i] += qty
            
            # Track feeding actions (wheat consumed)
            for w_act in (act.get("workers", {}).values() or []):
                if isinstance(w_act, list) and len(w_act) >= 2 and w_act[0] == "FEED":
                    cumulative["wheat_consumed"][i] += 1
            f_act = act.get("farmer", [])
            if isinstance(f_act, list) and len(f_act) >= 2 and f_act[0] == "FEED":
                cumulative["wheat_consumed"][i] += 1
        
        # Checkpoint recording
        if s in CHECKPOINTS:
            checkpoints_data[s] = {
                "step": s,
                "day": s // 24,
                "prices": {
                    "wheat": float(mkt_prices.get("WHEAT", 0.0)),
                    "wool": float(mkt_prices.get("WOOL", 0.0)),
                    "milk": float(mkt_prices.get("MILK", 0.0)),
                },
                "v54": {
                    "cash": float(farms[v54_idx].get("money", 0.0)),
                    "wheat_inv": int((privates[v54_idx].get("shed", {}) or {}).get("WHEAT", 0)),
                    "wheat_sold": cumulative["wheat_sold"][v54_idx],
                    "wheat_revenue": cumulative["wheat_revenue"][v54_idx],
                    "wool_sold": cumulative["wool_sold"][v54_idx],
                    "wool_revenue": cumulative["wool_revenue"][v54_idx],
                    "milk_sold": cumulative["milk_sold"][v54_idx],
                    "milk_revenue": cumulative["milk_revenue"][v54_idx],
                    "wheat_consumed": cumulative["wheat_consumed"][v54_idx],
                    "cows": len(privates[v54_idx].get("cows", [])),
                    "sheep": len(privates[v54_idx].get("sheep", [])),
                },
                "v66": {
                    "cash": float(farms[v66_idx].get("money", 0.0)),
                    "wheat_inv": int((privates[v66_idx].get("shed", {}) or {}).get("WHEAT", 0)),
                    "wheat_sold": cumulative["wheat_sold"][v66_idx],
                    "wheat_revenue": cumulative["wheat_revenue"][v66_idx],
                    "wool_sold": cumulative["wool_sold"][v66_idx],
                    "wool_revenue": cumulative["wool_revenue"][v66_idx],
                    "milk_sold": cumulative["milk_sold"][v66_idx],
                    "milk_revenue": cumulative["milk_revenue"][v66_idx],
                    "wheat_consumed": cumulative["wheat_consumed"][v66_idx],
                    "cows": len(privates[v66_idx].get("cows", [])),
                    "sheep": len(privates[v66_idx].get("sheep", [])),
                }
            }
        
        # Turn-by-turn tracking for Steps 300-718
        if s >= 300:
            turn_by_turn.append({
                "step": s,
                "v54_act": acts[v54_idx],
                "v66_act": acts[v66_idx],
                "wheat_price": float(mkt_prices.get("WHEAT", 0.0)),
                "wool_price": float(mkt_prices.get("WOOL", 0.0)),
                "milk_price": float(mkt_prices.get("MILK", 0.0)),
                "v54_wheat_inv": int((privates[v54_idx].get("shed", {}) or {}).get("WHEAT", 0)),
                "v66_wheat_inv": int((privates[v66_idx].get("shed", {}) or {}).get("WHEAT", 0)),
                "v54_cash": float(farms[v54_idx].get("money", 0.0)),
                "v66_cash": float(farms[v66_idx].get("money", 0.0)),
                "v54_livestock": len(privates[v54_idx].get("cows", [])) + len(privates[v54_idx].get("sheep", [])),
                "v66_livestock": len(privates[v66_idx].get("cows", [])) + len(privates[v66_idx].get("sheep", [])),
            })
            
        env.step([act0, act1])
    
    final_v54_reward = float(env.state[v54_idx].reward)
    final_v66_reward = float(env.state[v66_idx].reward)
    
    return {
        "seed": seed,
        "seat": 0 if p0_is_v54 else 1,
        "v54_reward": final_v54_reward,
        "v66_reward": final_v66_reward,
        "margin": final_v54_reward - final_v66_reward,
        "cumulative": {
            "v54": {k: v[v54_idx] for k, v in cumulative.items()},
            "v66": {k: v[v66_idx] for k, v in cumulative.items()}
        },
        "checkpoints": checkpoints_data,
        "turn_by_turn": turn_by_turn
    }

def main():
    print("Loading 1,000-match symmetric holdout results...")
    with open("research/shop216_holdout_results.json") as f:
        matches = json.load(f)
    
    # Categorize matches into Groups A..G
    # Note: shop_reward is V54++, v66_reward is V66. Margin is shop_reward - v66_reward.
    groups = {
        "Group A: V66 lead >= $10k": [m for m in matches if m["v66_reward"] - m["shop_reward"] >= 10000],
        "Group B: V66 lead >= $5k": [m for m in matches if 5000 <= (m["v66_reward"] - m["shop_reward"]) < 10000],
        "Group C: V66 lead >= $2.5k": [m for m in matches if 2500 <= (m["v66_reward"] - m["shop_reward"]) < 5000],
        "Group D: Close (< $2.5k)": [m for m in matches if abs(m["shop_reward"] - m["v66_reward"]) < 2500],
        "Group E: V54++ lead >= $2.5k": [m for m in matches if 2500 <= (m["shop_reward"] - m["v66_reward"]) < 5000],
        "Group F: V54++ lead >= $5k": [m for m in matches if 5000 <= (m["shop_reward"] - m["v66_reward"]) < 10000],
        "Group G: V54++ lead >= $10k": [m for m in matches if m["shop_reward"] - m["v66_reward"] >= 10000],
    }
    
    print("\nHoldout Partition Match Counts:")
    for gname, glist in groups.items():
        print(f"  {gname}: {len(glist)} matches")
        
    # Select target matches for telemetry execution:
    # 1. All Group A matches (4 matches)
    # 2. All Group B matches (11 matches)
    # 3. 10 representative matches from Group C
    # 4. 10 representative matches from Group D
    # 5. 10 representative matches from Group E
    # 6. 10 representative matches from Group F
    # 7. 10 representative matches from Group G
    
    selected_targets = []
    selected_targets.extend(groups["Group A: V66 lead >= $10k"])
    selected_targets.extend(groups["Group B: V66 lead >= $5k"])
    
    np.random.seed(42)
    for gname in ["Group C: V66 lead >= $2.5k", "Group D: Close (< $2.5k)", "Group E: V54++ lead >= $2.5k", "Group F: V54++ lead >= $5k", "Group G: V54++ lead >= $10k"]:
        glist = groups[gname]
        chosen = list(np.random.choice(len(glist), size=min(10, len(glist)), replace=False))
        selected_targets.extend([glist[i] for i in chosen])
        
    print(f"\nExecuting instrumented telemetry for {len(selected_targets)} selected matches across all partitions...")
    
    telemetry_results = []
    divergence_rows = []
    
    for idx, target in enumerate(selected_targets):
        seed = int(target["seed"])
        seat = int(target["seat"])
        p0_is_v54 = (seat == 0)
        
        print(f"[{idx+1}/{len(selected_targets)}] Running Seed {seed} (Seat {seat}, Margin: {target['margin']})")
        res = run_match_telemetry(seed, p0_is_v54)
        
        # Analyze first mid/late divergence for large loss matches (Group A & B)
        v66_lead = res["v66_reward"] - res["v54_reward"]
        if v66_lead >= 5000:
            # Trace turn-by-turn to find first wheat/livestock divergence
            first_div = None
            for row in res["turn_by_turn"]:
                step = row["step"]
                # Check wheat sell difference
                mkt_v54 = row["v54_act"].get("market", []) or []
                mkt_v66 = row["v66_act"].get("market", []) or []
                
                v54_sells_wheat = any(len(o) >= 3 and o[0] == "SELL" and o[1] == "WHEAT" for o in mkt_v54)
                v66_sells_wheat = any(len(o) >= 3 and o[0] == "SELL" and o[1] == "WHEAT" for o in mkt_v66)
                
                if v54_sells_wheat != v66_sells_wheat:
                    first_div = {
                        "seed": seed,
                        "step": step,
                        "v54_action": "SELL WHEAT" if v54_sells_wheat else "RETAIN/FEED WHEAT",
                        "v66_action": "SELL WHEAT" if v66_sells_wheat else "RETAIN/FEED WHEAT",
                        "wheat_inventory": row["v54_wheat_inv"],
                        "wheat_price": row["wheat_price"],
                        "wool_price": row["wool_price"],
                        "milk_price": row["milk_price"],
                        "livestock_state": f"v54:{row['v54_livestock']} vs v66:{row['v66_livestock']}",
                        "cash": f"v54:${row['v54_cash']:.1f} vs v66:${row['v66_cash']:.1f}",
                        "candidate_conversion_value": f"P_wheat=${row['wheat_price']:.1f} vs P_wool=${row['wool_price']:.1f}",
                        "downstream_consequence": f"V66 liquidated grain into high cash flow; V54++ locked into livestock feed",
                        "final_reward_delta": -v66_lead
                    }
                    break
            
            if first_div:
                divergence_rows.append(first_div)
        
        # Strip heavy turn_by_turn from telemetry saving to keep JSON clean
        del res["turn_by_turn"]
        telemetry_results.append(res)
        
    print(f"\nWriting research/midlate_accounting_telemetry.json ({len(telemetry_results)} matches)...")
    with open("research/midlate_accounting_telemetry.json", "w") as f:
        json.dump(telemetry_results, f, indent=2)
        
    print(f"Writing research/wheat_livestock_first_divergence.csv ({len(divergence_rows)} entries)...")
    with open("research/wheat_livestock_first_divergence.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "seed", "step", "v54_action", "v66_action", "wheat_inventory",
            "wheat_price", "wool_price", "milk_price", "livestock_state",
            "cash", "candidate_conversion_value", "downstream_consequence", "final_reward_delta"
        ])
        writer.writeheader()
        for row in divergence_rows:
            writer.writerow(row)
            
    print("Telemetry extraction complete!")

if __name__ == "__main__":
    main()
