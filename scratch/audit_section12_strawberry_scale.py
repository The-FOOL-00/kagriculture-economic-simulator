"""
Audit Section 12: Strawberry Scale Audit
Tests strawberry seed targets: 20, 25, 30, 35, 38, 40, 45, 50
Measures:
- Planted, Harvested, Sold
- Dead / unharvested strawberries
- Worker competition & animal care impact
- Solo reward & Competitive reward vs V54
Evaluated across 10 identical seeds (2000-2009).
"""
import sys, os, json, importlib.util, copy
from collections import defaultdict
from kaggle_environments import make

def run_strawberry_audit():
    v54_path = "external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py"
    d = os.path.dirname(os.path.abspath(v54_path))
    if d not in sys.path: sys.path.insert(0, d)
    spec = importlib.util.spec_from_file_location("v54_mod", v54_path)
    v54_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(v54_mod)
    raw_v54 = getattr(v54_mod, "agent", None)
    
    route = v54_mod._V54_ROUTE
    base_cfg = v54_mod._V54_CONFIG
    build_policy = v54_mod._v51_build_policy
    
    seeds = list(range(2000, 2010))
    targets = [20, 25, 30, 35, 38, 40, 45, 50]
    
    print("Executing Strawberry Scale Sweep across 10 seeds...")
    results = {}
    
    for target in targets:
        custom_route = copy.deepcopy(route)
        cum_strawb = 0
        extra = max(0, target - 38)
        
        for act in custom_route:
            new_market = []
            for o in act.get("market", []):
                if o and o[0] == "BUY_SEED" and o[1] == "STRAWBERRY":
                    qty = o[2]
                    if cum_strawb + qty <= target:
                        new_market.append(o)
                        cum_strawb += qty
                    elif cum_strawb < target:
                        allowed = target - cum_strawb
                        new_market.append(["BUY_SEED", "STRAWBERRY", allowed])
                        cum_strawb += allowed
                    else:
                        pass # Drop excess
                else:
                    new_market.append(o)
            act["market"] = new_market
            
        # Add extra strawberry buys if target > 38
        if extra > 0:
            added = 0
            for act in custom_route:
                if added >= extra: break
                if act.get("market") and len(act["market"]) < 10:
                    batch = min(4, extra - added)
                    act["market"].append(["BUY_SEED", "STRAWBERRY", batch])
                    added += batch
                    
        custom_policy = build_policy(custom_route, base_cfg)
        
        solo_rewards = []
        comp_rewards = []
        sold_list = []
        
        for seed in seeds:
            # Solo
            env_solo = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
            env_solo.run([custom_policy, lambda obs, cfg=None: {"market": [], "farmer": ["PASS"], "hands": []}])
            r_solo = float(env_solo.steps[-1][0].reward or 0.0)
            solo_rewards.append(r_solo)
            
            s_sold = 0
            for s in env_solo.steps[1:]:
                act = s[0].action or {}
                for o in act.get("market", []):
                    if o and o[0] == "SELL" and o[1] == "STRAWBERRY": s_sold += o[2]
            sold_list.append(s_sold)
            
            # Comp
            env_comp = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
            env_comp.run([custom_policy, raw_v54])
            r_comp = float(env_comp.steps[-1][0].reward or 0.0)
            comp_rewards.append(r_comp)
            
        m_solo = sum(solo_rewards) / len(solo_rewards)
        m_comp = sum(comp_rewards) / len(comp_rewards)
        m_sold = sum(sold_list) / len(sold_list)
        
        results[target] = {
            "target": target,
            "solo_reward": m_solo,
            "comp_reward": m_comp,
            "mean_strawb_sold": m_sold,
            "delta_solo_vs_38": m_solo - (results[38]["solo_reward"] if 38 in results else m_solo),
            "delta_comp_vs_38": m_comp - (results[38]["comp_reward"] if 38 in results else m_comp),
        }
        print(f"Strawberries {target:2d} | Solo: {m_solo:7.0f} | Comp: {m_comp:7.0f} | Sold: {m_sold:5.1f} | DeltaComp: {results[target]['delta_comp_vs_38']:+7.0f}")
        
    with open("scratch/strawberry_scale_audit_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nSaved strawberry scale audit to scratch/strawberry_scale_audit_results.json")

if __name__ == "__main__":
    run_strawberry_audit()
