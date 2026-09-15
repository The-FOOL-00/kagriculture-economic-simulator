"""
Comprehensive 10-Seed Comparative Forensics: Backbone vs IDLE, V54, V66
Extracts exact economic metrics for all 10 seeds across all three match types.
"""
import sys, os, json, time, statistics
sys.path.insert(0, ".")
sys.path.insert(0, "candidates/declarative_backbone")

from kaggle_environments import make
from candidates.declarative_backbone.params import V54_PRIOR
from candidates.declarative_backbone.compiler import DeclarativeBackboneCompiler
from scratch.run_exp_a import load_file_agent

SEEDS = list(range(2000, 2010))

v54_agent = load_file_agent("external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py")
v66_agent = load_file_agent("external_repos/kaggriculture-v66-agent/main.py")

def idle_agent(obs, cfg=None):
    return {"market": [], "farmer": ["PASS"], "hands": []}

def run_match_detailed(seed, opp_name, opp_fn):
    comp = DeclarativeBackboneCompiler(V54_PRIOR)
    cfg = {"episodeSteps": 720, "seed": seed}
    env = make("kaggriculture", configuration=cfg, debug=False)
    
    obs = env.reset()
    
    # Telemetry
    data = {
        "seed": seed,
        "opp_name": opp_name,
        "r0": 0.0,
        "r1": 0.0,
        "sales_qty": {},
        "sales_rev": {},
        "feed_bought": 0,
        "feed_spent": 0,
        "animals_placed": {"COW": 0, "SHEEP": 0},
        "land_unlocked": 1,
        "day10_cash": 0,
        "day15_cash": 0,
        "day20_cash": 0,
        "avg_prices": {},
    }
    
    price_samples = {"MILK": [], "WOOL": [], "FERTILIZER": [], "CARROT": [], "MELON": []}
    market_inv_samples = {"MILK": [], "WOOL": [], "FERTILIZER": [], "WHEAT": []}
    
    prev_money = obs[0].observation.farms[0]["money"]
    
    for step_idx in range(720):
        # Sample prices
        m_prices = obs[0].observation.market.get("prices", {})
        m_inv = obs[0].observation.market.get("inventory", {})
        for k in price_samples:
            if k in m_prices: price_samples[k].append(m_prices[k])
        for k in market_inv_samples:
            if k in m_inv: market_inv_samples[k].append(m_inv[k])
            
        action0 = comp(obs[0].observation)
        action1 = opp_fn(obs[1].observation)
        
        # Track animal placement
        all_actions = [action0.get("farmer", ["PASS"])] + action0.get("hands", [])
        for act in all_actions:
            if act and act[0] == "PLACE":
                an = act[1]
                data["animals_placed"][an] = data["animals_placed"].get(an, 0) + 1
        
        obs = env.step([action0, action1])
        if env.done:
            break
            
        farm0 = obs[0].observation.farms[0]
        day = obs[0].observation.day
        hour = obs[0].observation.hour
        
        if day == 10 and hour == 0: data["day10_cash"] = farm0["money"]
        if day == 15 and hour == 0: data["day15_cash"] = farm0["money"]
        if day == 20 and hour == 0: data["day20_cash"] = farm0["money"]
        data["land_unlocked"] = len(farm0["unlocked_quadrants"])

    data["r0"] = float(obs[0].reward or 0.0)
    data["r1"] = float(obs[1].reward or 0.0)
    
    for k in price_samples:
        data["avg_prices"][k] = statistics.mean(price_samples[k]) if price_samples[k] else 0.0
    for k in market_inv_samples:
        data[f"avg_inv_{k}"] = statistics.mean(market_inv_samples[k]) if market_inv_samples[k] else 0.0
        
    return data

results = {"IDLE": [], "V54": [], "V66": []}

print("Running 10-seed audit...")
for seed in SEEDS:
    print(f"Seed {seed}:")
    d_idle = run_match_detailed(seed, "IDLE", idle_agent)
    d_v54  = run_match_detailed(seed, "V54", v54_agent)
    d_v66  = run_match_detailed(seed, "V66", v66_agent)
    
    results["IDLE"].append(d_idle)
    results["V54"].append(d_v54)
    results["V66"].append(d_v66)
    
    print(f"  IDLE: r0={d_idle['r0']:.0f} | V54: r0={d_v54['r0']:.0f}, r1={d_v54['r1']:.0f} | V66: r0={d_v66['r0']:.0f}, r1={d_v66['r1']:.0f}")

output_path = "scratch/audit_10seed_results.json"
json.dump(results, open(output_path, "w"), indent=2)
print(f"Saved to {output_path}")
