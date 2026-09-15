"""
Audit Section 7: Reconcile V54 Source with the Reconstruction
Runs Original V54 vs Reconstructed / Declarative Backbone (EXP-A) across 20 seeds (2000-2019).
Measures exact per-seed differences on all 13 metrics:
1. Final reward
2. Worker count (total worker-days)
3. Wheat seeds bought & planted
4. Strawberries planted
5. Cows placed
6. Sheep placed
7. Milk sold (units)
8. Wool sold (units)
9. Fertilizer sold (units)
10. Wheat sold (units)
11. Market sell events (number of sell orders)
12. Terminal liquidation timing & revenue
13. Average realized market prices
"""
import sys, os, json, importlib.util
from collections import defaultdict
from kaggle_environments import make

def load_agent(path):
    d = os.path.dirname(os.path.abspath(path))
    if d not in sys.path: sys.path.insert(0, d)
    name = os.path.splitext(os.path.basename(path))[0]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, "agent", None) or getattr(mod, "_kaggle_submission_entrypoint", None)

def extract_detailed_run(agent_fn, seed):
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    opp_fn = lambda obs, cfg=None: {"market": [], "farmer": ["PASS"], "hands": []}
    env.run([agent_fn, opp_fn])
    
    metrics = {
        "seed": seed,
        "reward": float(env.steps[-1][0].reward or 0.0),
        "worker_days": 0,
        "wheat_seeds": 0,
        "strawberries_planted": 0,
        "cows": 0,
        "sheep": 0,
        "milk_sold": 0,
        "wool_sold": 0,
        "fert_sold": 0,
        "wheat_sold": 0,
        "market_sell_events": 0,
        "terminal_liq_rev": 0.0,
        "prices": defaultdict(list)
    }
    
    farm_final = env.steps[-1][0].observation.farms[0]
    for row in farm_final["tiles"]:
        for t in row:
            if isinstance(t, dict):
                if t.get("animal") == "COW": metrics["cows"] += 1
                elif t.get("animal") == "SHEEP": metrics["sheep"] += 1
                
    for step_idx in range(1, len(env.steps)):
        s = env.steps[step_idx]
        obs = s[0].observation
        act = s[0].action or {}
        market = obs.market
        farm = obs.farms[0]
        day = obs.day
        hour = obs.hour
        
        if hour == 23 or step_idx == 720:
            metrics["worker_days"] += farm.get("hires_today", 0)
            
        all_units = [act.get("farmer", ["PASS"])] + act.get("hands", [])
        for u in all_units:
            if u and u[0] == "PLANT" and len(u) > 1:
                if u[1] == "STRAWBERRY": metrics["strawberries_planted"] += 1
                
        for o in act.get("market", []):
            if not o: continue
            op = o[0]
            if op == "BUY_SEED" and len(o) > 2 and o[1] == "WHEAT":
                metrics["wheat_seeds"] += o[2]
            elif op == "SELL" and len(o) > 2:
                prod = o[1]
                qty = o[2]
                pr = market["prices"].get(prod, 0)
                metrics["market_sell_events"] += 1
                metrics["prices"][prod].append(pr)
                if prod == "MILK": metrics["milk_sold"] += qty
                elif prod == "WOOL": metrics["wool_sold"] += qty
                elif prod == "FERTILIZER": metrics["fert_sold"] += qty
                elif prod == "WHEAT": metrics["wheat_sold"] += qty
                if step_idx >= 670:
                    metrics["terminal_liq_rev"] += qty * pr
                    
    metrics["avg_price_milk"] = sum(metrics["prices"]["MILK"])/len(metrics["prices"]["MILK"]) if metrics["prices"]["MILK"] else 0.0
    metrics["avg_price_wool"] = sum(metrics["prices"]["WOOL"])/len(metrics["prices"]["WOOL"]) if metrics["prices"]["WOOL"] else 0.0
    metrics["avg_price_wheat"] = sum(metrics["prices"]["WHEAT"])/len(metrics["prices"]["WHEAT"]) if metrics["prices"]["WHEAT"] else 0.0
    del metrics["prices"]
    return metrics

def run_reconciliation_audit():
    v54_path = "external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py"
    expa_path = "candidates/declarative_backbone/agent.py"
    
    fn_v54 = load_agent(v54_path)
    fn_expa = load_agent(expa_path)
    
    seeds = list(range(2000, 2020)) # 20 seeds
    print(f"Executing 20-seed comparison: Original V54 vs EXP-A Reconstruction...")
    
    comparisons = []
    
    for seed in seeds:
        m_v54 = extract_detailed_run(fn_v54, seed)
        m_expa = extract_detailed_run(fn_expa, seed)
        
        diff = {
            "seed": seed,
            "reward_v54": m_v54["reward"],
            "reward_expa": m_expa["reward"],
            "reward_diff": m_expa["reward"] - m_v54["reward"],
            "workers_v54": m_v54["worker_days"],
            "workers_expa": m_expa["worker_days"],
            "workers_diff": m_expa["worker_days"] - m_v54["worker_days"],
            "wheat_seeds_v54": m_v54["wheat_seeds"],
            "wheat_seeds_expa": m_expa["wheat_seeds"],
            "strawb_planted_v54": m_v54["strawberries_planted"],
            "strawb_planted_expa": m_expa["strawberries_planted"],
            "cows_v54": m_v54["cows"],
            "cows_expa": m_expa["cows"],
            "sheep_v54": m_v54["sheep"],
            "sheep_expa": m_expa["sheep"],
            "milk_sold_v54": m_v54["milk_sold"],
            "milk_sold_expa": m_expa["milk_sold"],
            "wool_sold_v54": m_v54["wool_sold"],
            "wool_sold_expa": m_expa["wool_sold"],
            "fert_sold_v54": m_v54["fert_sold"],
            "fert_sold_expa": m_expa["fert_sold"],
            "wheat_sold_v54": m_v54["wheat_sold"],
            "wheat_sold_expa": m_expa["wheat_sold"],
            "sell_events_v54": m_v54["market_sell_events"],
            "sell_events_expa": m_expa["market_sell_events"],
            "terminal_rev_v54": m_v54["terminal_liq_rev"],
            "terminal_rev_expa": m_expa["terminal_liq_rev"],
        }
        comparisons.append(diff)
        print(f"Seed {seed:4d} | V54: {m_v54['reward']:7.0f} | EXP-A: {m_expa['reward']:7.0f} | Delta: {diff['reward_diff']:+8.0f} | Strawb Planted: {m_v54['strawberries_planted']} vs {m_expa['strawberries_planted']}")
        
    with open("scratch/v54_reconciliation_20seeds.json", "w") as f:
        json.dump(comparisons, f, indent=2)
    print("\nSaved 20-seed reconciliation to scratch/v54_reconciliation_20seeds.json")

if __name__ == "__main__":
    run_reconciliation_audit()
