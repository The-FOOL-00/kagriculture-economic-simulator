"""
Extract complete ground-truth telemetry from env.steps for:
Backbone vs IDLE
Backbone vs V54
Backbone vs V66
across seeds 2000-2009.
"""
import sys, os, json, importlib.util, statistics
from kaggle_environments import make

def load_agent(path):
    d = os.path.dirname(os.path.abspath(path))
    if d not in sys.path:
        sys.path.insert(0, d)
    name = os.path.splitext(os.path.basename(path))[0]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, "agent", None) or getattr(mod, "_kaggle_submission_entrypoint", None)

backbone_path = "candidates/declarative_backbone/agent.py"
v54_path = "external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py"
v66_path = "external_repos/kaggriculture-v66-agent/main.py"

def idle_agent(obs, cfg=None):
    return {"market": [], "farmer": ["PASS"], "hands": []}

def analyze_match(env):
    # env.steps has length 721
    # step 0 is initial obs, step 1 to 720 are transitions
    prices_history = {"MILK": [], "WOOL": [], "FERTILIZER": [], "CARROT": [], "MELON": [], "WHEAT": []}
    inv_history = {"MILK": [], "WOOL": [], "FERTILIZER": [], "CARROT": [], "MELON": [], "WHEAT": []}
    
    p0_money_history = []
    p1_money_history = []
    
    p0_sales_qty = {"MILK": 0, "WOOL": 0, "FERTILIZER": 0, "CARROT": 0, "MELON": 0}
    p1_sales_qty = {"MILK": 0, "WOOL": 0, "FERTILIZER": 0, "CARROT": 0, "MELON": 0, "WHEAT": 0, "STRAWBERRY": 0}
    
    p0_land_unlocks = []
    p1_land_unlocks = []
    
    p0_cows = 0
    p0_sheep = 0
    p1_cows = 0
    p1_sheep = 0
    
    for t in range(1, len(env.steps)):
        s = env.steps[t]
        obs = s[0].observation
        market = obs.market
        m_prices = market.get("prices", {})
        m_inv = market.get("inventory", {})
        for k in prices_history:
            if k in m_prices: prices_history[k].append(m_prices[k])
            if k in m_inv: inv_history[k].append(m_inv[k])
            
        farm0 = obs.farms[0]
        farm1 = obs.farms[1]
        p0_money_history.append(farm0["money"])
        p1_money_history.append(farm1["money"])
        
        # Land unlocks
        if len(farm0["unlocked_quadrants"]) > len(p0_land_unlocks) + 1:
            p0_land_unlocks.append((t, len(farm0["unlocked_quadrants"])))
        if len(farm1["unlocked_quadrants"]) > len(p1_land_unlocks) + 1:
            p1_land_unlocks.append((t, len(farm1["unlocked_quadrants"])))
            
        # Sales in action
        act0 = s[0].action or {}
        for order in act0.get("market", []):
            if order and order[0] == "SELL":
                prod = order[1]
                qty = order[2] if len(order) > 2 else 1
                if prod in p0_sales_qty: p0_sales_qty[prod] += qty
                
        act1 = s[1].action or {}
        for order in act1.get("market", []):
            if order and order[0] == "SELL":
                prod = order[1]
                qty = order[2] if len(order) > 2 else 1
                if prod in p1_sales_qty: p1_sales_qty[prod] += qty
                
    # Final count of animals on farm
    for row in farm0["tiles"]:
        for t in row:
            if isinstance(t, dict) and "animal" in t:
                if t["animal"] == "COW": p0_cows += 1
                elif t["animal"] == "SHEEP": p0_sheep += 1
    for row in farm1["tiles"]:
        for t in row:
            if isinstance(t, dict) and "animal" in t:
                if t["animal"] == "COW": p1_cows += 1
                elif t["animal"] == "SHEEP": p1_sheep += 1
                
    return {
        "r0": float(env.steps[-1][0].reward or 0.0),
        "r1": float(env.steps[-1][1].reward or 0.0),
        "mean_prices": {k: statistics.mean(v) if v else 0.0 for k, v in prices_history.items()},
        "mean_inv": {k: statistics.mean(v) if v else 0.0 for k, v in inv_history.items()},
        "p0_sales_qty": p0_sales_qty,
        "p1_sales_qty": p1_sales_qty,
        "p0_cows": p0_cows,
        "p0_sheep": p0_sheep,
        "p1_cows": p1_cows,
        "p1_sheep": p1_sheep,
        "p0_land_unlocks": p0_land_unlocks,
        "p1_land_unlocks": p1_land_unlocks,
        "p0_day10_money": p0_money_history[240] if len(p0_money_history) > 240 else 0,
        "p0_day15_money": p0_money_history[360] if len(p0_money_history) > 360 else 0,
        "p0_day20_money": p0_money_history[480] if len(p0_money_history) > 480 else 0,
        "p1_day10_money": p1_money_history[240] if len(p1_money_history) > 240 else 0,
        "p1_day15_money": p1_money_history[360] if len(p1_money_history) > 360 else 0,
        "p1_day20_money": p1_money_history[480] if len(p1_money_history) > 480 else 0,
    }

SEEDS = list(range(2000, 2010))
results = {"IDLE": [], "V54": [], "V66": []}

for seed in SEEDS:
    print(f"Running Seed {seed}...")
    # 1. vs IDLE
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env.run([load_agent(backbone_path), idle_agent])
    d_idle = analyze_match(env)
    results["IDLE"].append(d_idle)
    
    # 2. vs V54
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env.run([load_agent(backbone_path), load_agent(v54_path)])
    d_v54 = analyze_match(env)
    results["V54"].append(d_v54)
    
    # 3. vs V66
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env.run([load_agent(backbone_path), load_agent(v66_path)])
    d_v66 = analyze_match(env)
    results["V66"].append(d_v66)
    
    print(f"  Seed {seed} -> IDLE: r0={d_idle['r0']:.0f} | V54: r0={d_v54['r0']:.0f} (v54={d_v54['r1']:.0f}) | V66: r0={d_v66['r0']:.0f} (v66={d_v66['r1']:.0f})")

json.dump(results, open("scratch/telemetry_10seeds.json", "w"), indent=2)
print("Saved to scratch/telemetry_10seeds.json")
