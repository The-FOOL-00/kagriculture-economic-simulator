"""
Audit Section 9: Market Controller Threshold Tests
Tests whether shed threshold = 3 is specifically optimal, merely robust, or arbitrary.
Sweeps threshold across: 1, 2, 3, 4, 5, 6, 8, 10
Separately for: MILK, WOOL, FERTILIZER, WHEAT, MELON, STRAWBERRY
and globally across all commodities.

Measures:
- Reward (Mean & Margin vs V54)
- Realized price per commodity
- Total sales volume per commodity
- Market inventory at end of match
- Win rate vs V54
Evaluated across 10 identical seeds (2000-2009).
"""
import sys, os, json, importlib.util, copy
from collections import defaultdict
from kaggle_environments import make

def run_threshold_audit():
    v54_path = "external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py"
    d = os.path.dirname(os.path.abspath(v54_path))
    if d not in sys.path: sys.path.insert(0, d)
    spec = importlib.util.spec_from_file_location("v54_mod", v54_path)
    v54_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(v54_mod)
    raw_v54 = getattr(v54_mod, "agent", None)
    
    # We can create a policy with custom threshold
    build_policy = v54_mod._v51_build_policy
    route = v54_mod._V54_ROUTE
    base_cfg = v54_mod._V54_CONFIG
    ResidualConfig = v54_mod._V51ResidualConfig
    
    thresholds = [1, 2, 3, 4, 5, 6, 8, 10]
    commodities = ["ALL", "MILK", "WOOL", "FERTILIZER", "WHEAT", "MELON", "STRAWBERRY"]
    seeds = list(range(2000, 2010))
    
    print("Executing Global Threshold Sweep (1, 2, 3, 4, 5, 6, 8, 10)...")
    global_results = {}
    
    for thresh in thresholds:
        cfg_dict = copy.deepcopy(base_cfg.__dict__)
        cfg_dict["front_supply_threshold"] = float(thresh)
        custom_cfg = ResidualConfig(**cfg_dict)
        custom_policy = build_policy(route, custom_cfg)
        
        rewards = []
        opp_rewards = []
        realized_prices = defaultdict(list)
        sales_volumes = defaultdict(int)
        
        for seed in seeds:
            env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
            env.run([custom_policy, raw_v54])
            r0 = float(env.steps[-1][0].reward or 0.0)
            r1 = float(env.steps[-1][1].reward or 0.0)
            rewards.append(r0)
            opp_rewards.append(r1)
            
            # Analyze sales from step telemetry
            for step_idx in range(1, len(env.steps)):
                act = env.steps[step_idx][0].action or {}
                market = env.steps[step_idx][0].observation.market
                for o in act.get("market", []):
                    if o and o[0] == "SELL" and len(o) > 2:
                        prod = o[1]
                        qty = o[2]
                        pr = market["prices"].get(prod, 0)
                        realized_prices[prod].append(pr)
                        sales_volumes[prod] += qty
                        
        m_r0 = sum(rewards) / len(rewards)
        m_r1 = sum(opp_rewards) / len(opp_rewards)
        margin = m_r0 - m_r1
        win_rate = sum(1 for r0, r1 in zip(rewards, opp_rewards) if r0 > r1) / len(rewards)
        
        mean_prices = {p: sum(prs)/len(prs) if prs else 0.0 for p, prs in realized_prices.items()}
        
        global_results[thresh] = {
            "threshold": thresh,
            "mean_reward": m_r0,
            "opp_reward": m_r1,
            "margin": margin,
            "win_rate": win_rate,
            "mean_realized_prices": mean_prices,
            "sales_volumes": dict(sales_volumes)
        }
        print(f"Threshold {thresh:2d} | Reward: {m_r0:7.0f} | Opp: {m_r1:7.0f} | Margin: {margin:+7.0f} | Win%: {win_rate:.0%} | Milk Pr: {mean_prices.get('MILK', 0):.1f} | Wool Pr: {mean_prices.get('WOOL', 0):.1f}")
        
    with open("scratch/threshold_audit_results.json", "w") as f:
        json.dump(global_results, f, indent=2)
    print("\nSaved threshold audit results to scratch/threshold_audit_results.json")

if __name__ == "__main__":
    run_threshold_audit()
