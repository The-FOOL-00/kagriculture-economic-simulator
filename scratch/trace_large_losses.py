import os
import sys
import copy
import json
import csv
from collections import defaultdict
import importlib.util
from kaggle_environments import make

CANDIDATE_PATHS = {
    "V66": "external_repos/kaggriculture-v66-agent/main.py",
    "V54++": "candidates/v54_plus_shop.py",
}

_LOADED_AGENTS = {}

def get_agent_fn(name):
    if name not in _LOADED_AGENTS:
        path = os.path.abspath(CANDIDATE_PATHS[name])
        d = os.path.dirname(path)
        if d not in sys.path:
            sys.path.insert(0, d)
        spec = importlib.util.spec_from_file_location(name.replace("+", "p") + "_eval", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _LOADED_AGENTS[name] = getattr(mod, "agent", getattr(mod, "kaggle_agent", None))
    return _LOADED_AGENTS[name]

large_loss_seeds = [1542, 1609, 1773, 1871, 1948, 1949, 1969]

fn_v54 = get_agent_fn("V54++")
fn_v66 = get_agent_fn("V66")

summary_records = []
divergence_csv_rows = []

for seed in large_loss_seeds:
    print(f"\n==========================================")
    print(f"TRACING LARGE LOSS SEED {seed}")
    print(f"==========================================")
    
    # Run Match 0: P0=V54++, P1=V66
    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    env.reset()
    
    first_market_diff = None
    first_money_diff = None
    first_hand_diff = None
    first_shed_diff = None
    first_phys_diff = None
    first_action_diff = None
    
    divergence_log = []
    
    # Track early phase accounting (Steps 0-143)
    early_straw_planted = [0, 0]
    early_straw_harvested = [0, 0]
    early_straw_sold = [0, 0]
    early_cows_bought = [0, 0]
    early_sheep_bought = [0, 0]
    early_cow_step = [None, None]
    early_sheep_step = [None, None]
    
    sales_total = [defaultdict(float), defaultdict(float)]
    revenue_total = [defaultdict(float), defaultdict(float)]
    
    prev_tiles = [None, None]
    
    for s in range(719):
        o0, o1 = env.state[0].observation, env.state[1].observation
        o0["step"], o1["step"] = s, s
        
        act0 = fn_v54(o0, env.configuration)
        act1 = fn_v66(o1, env.configuration)
        
        f0 = o0.get("farms", [{}])[0]
        f1 = o1.get("farms", [{}])[1]
        
        priv0 = o0.get("private", {})
        priv1 = o1.get("private", {})
        
        m0, m1 = f0.get("money", 0.0), f1.get("money", 0.0)
        h0, h1 = len(f0.get("hands", [])), len(f1.get("hands", []))
        shed0, shed1 = len(priv0.get("shed", [])), len(priv1.get("shed", []))
        
        # Track early plant/harvest
        if s <= 143:
            # Check market sales
            for ord in (act0.get("market") or []):
                if len(ord) >= 3 and ord[0] == "SELL" and ord[1] == "STRAWBERRY":
                    early_straw_sold[0] += int(ord[2])
            for ord in (act1.get("market") or []):
                if len(ord) >= 3 and ord[0] == "SELL" and ord[1] == "STRAWBERRY":
                    early_straw_sold[1] += int(ord[2])
            
            # Check livestock purchases
            for ord in (act0.get("market") or []):
                if len(ord) >= 3 and ord[0] == "BUY":
                    if ord[1] == "COW":
                        early_cows_bought[0] += int(ord[2])
                        if early_cow_step[0] is None: early_cow_step[0] = s
                    elif ord[1] == "SHEEP":
                        early_sheep_bought[0] += int(ord[2])
                        if early_sheep_step[0] is None: early_sheep_step[0] = s
            for ord in (act1.get("market") or []):
                if len(ord) >= 3 and ord[0] == "BUY":
                    if ord[1] == "COW":
                        early_cows_bought[1] += int(ord[2])
                        if early_cow_step[1] is None: early_cow_step[1] = s
                    elif ord[1] == "SHEEP":
                        early_sheep_bought[1] += int(ord[2])
                        if early_sheep_step[1] is None: early_sheep_step[1] = s

        # Track total sales
        for ord in (act0.get("market") or []):
            if len(ord) >= 3 and ord[0] == "SELL":
                sales_total[0][ord[1]] += int(ord[2])
        for ord in (act1.get("market") or []):
            if len(ord) >= 3 and ord[0] == "SELL":
                sales_total[1][ord[1]] += int(ord[2])
                
        # First physical difference detection
        if first_phys_diff is None:
            diffs = []
            if abs(m0 - m1) > 0.01:
                diffs.append(f"money: {m0} vs {m1}")
            if h0 != h1:
                diffs.append(f"hands: {h0} vs {h1}")
            if shed0 != shed1:
                diffs.append(f"shed: {shed0} vs {shed1}")
            if priv0.get("seeds") != priv1.get("seeds"):
                diffs.append(f"seeds: {priv0.get('seeds')} vs {priv1.get('seeds')}")
            if priv0.get("inventories") != priv1.get("inventories"):
                diffs.append(f"inv: {priv0.get('inventories')} vs {priv1.get('inventories')}")
            if diffs:
                first_phys_diff = (s, diffs)
                print(f"--> FIRST TRUE PHYSICAL STATE DIVERGENCE at Step {s}: {', '.join(diffs)}")
        
        env.step([act0, act1])
        
        if (s + 1) % 24 == 0:
            day = (s + 1) // 24
            post_o0, post_o1 = env.state[0].observation, env.state[1].observation
            pm0 = post_o0.get("farms", [{}])[0].get("money", 0)
            pm1 = post_o1.get("farms", [{}])[1].get("money", 0)
            ph0 = len(post_o0.get("farms", [{}])[0].get("hands", []))
            ph1 = len(post_o1.get("farms", [{}])[1].get("hands", []))
            if day in [3, 6, 9, 12, 15, 20, 25, 30]:
                print(f"Day {day:2d} (Step {s+1:3d}): V54++ $={pm0:8.1f} (h={ph0}) | V66 $={pm1:8.1f} (h={ph1}) | Margin={pm0-pm1:8.1f}")

    r0 = float(env.steps[-1][0].reward or 0.0)
    r1 = float(env.steps[-1][1].reward or 0.0)
    print(f"FINAL REWARD: V54++={r0:.1f}, V66={r1:.1f}, Margin={r0-r1:.1f}")
    
    post_o0, post_o1 = env.state[0].observation, env.state[1].observation
    shed_final_0 = defaultdict(int)
    for a in post_o0.get("private", {}).get("shed", []):
        shed_final_0[a if isinstance(a, str) else a.get("type")] += 1
    shed_final_1 = defaultdict(int)
    for a in post_o1.get("private", {}).get("shed", []):
        shed_final_1[a if isinstance(a, str) else a.get("type")] += 1
    print(f"Final Animals: V54++={dict(shed_final_0)} | V66={dict(shed_final_1)}")
    print(f"Commodity Sales V54++: {dict(sales_total[0])}")
    print(f"Commodity Sales V66:   {dict(sales_total[1])}")
    
    first_step = first_phys_diff[0] if first_phys_diff else 720
    first_desc = "; ".join(first_phys_diff[1]) if first_phys_diff else "None"
    
    divergence_csv_rows.append({
        "seed": seed,
        "first_divergence_step": first_step,
        "divergence_category": "Hand Hiring / Liquidity Allocation",
        "v54_action_state": f"Step {first_step}: V54++ money={env.state[0].observation['farms'][0]['money']}",
        "v66_action_state": f"Step {first_step}: V66 money={env.state[1].observation['farms'][1]['money']}",
        "downstream_consequence": f"V66 final lead: +${r1-r0:.1f}; Wheat sales {sales_total[1].get('WHEAT', 0)} vs {sales_total[0].get('WHEAT', 0)}; Sheep {shed_final_1.get('SHEEP', 0)} vs {shed_final_0.get('SHEEP', 0)}"
    })

# Write CSV
with open("research/early_loss_divergence.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["seed", "first_divergence_step", "divergence_category", "v54_action_state", "v66_action_state", "downstream_consequence"])
    writer.writeheader()
    for row in divergence_csv_rows:
        writer.writerow(row)
print("\nWrote research/early_loss_divergence.csv successfully.")
