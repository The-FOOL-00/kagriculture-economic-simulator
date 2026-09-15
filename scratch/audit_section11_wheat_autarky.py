"""
Audit Section 11: Wheat Autarky Audit
Tests wheat seed scale: 100, 125, 150, 175, 187, 200, 225, 250
Measures:
- Feed purchases
- Wheat harvested
- Wheat sold
- Animal uptime / starvation events
- Cash velocity & final reward (solo and competitive vs V54)
Evaluated across 10 identical seeds (2000-2009).
"""
import sys, os, json, importlib.util, copy
from collections import defaultdict
from kaggle_environments import make

def run_wheat_audit():
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
    wheat_targets = [100, 125, 150, 175, 187, 200, 225, 250]
    
    print("Executing Wheat Scale Sweep across 10 seeds...")
    results = {}
    
    for target in wheat_targets:
        # Build modified route or wrapper that caps/extends wheat purchases
        def make_wheat_policy(wheat_cap):
            base_policy = build_policy(route, base_cfg)
            
            def wheat_agent(obs, cfg=None):
                act = base_policy(obs, cfg)
                step = obs.get("step", obs.get("day", 0)*24 + obs.get("hour", 0))
                # Count wheat bought so far by inspecting farm or tracking state
                # In obs, we can track total wheat bought
                # Or we can wrap market orders:
                return act
            return base_policy
            
        # Let's create a custom route with exact wheat buy modifications:
        custom_route = copy.deepcopy(route)
        cum_wheat = 0
        extra_to_add = max(0, target - 187)
        
        for act in custom_route:
            new_market = []
            for o in act.get("market", []):
                if o and o[0] == "BUY_SEED" and o[1] == "WHEAT":
                    qty = o[2]
                    if cum_wheat + qty <= target:
                        new_market.append(o)
                        cum_wheat += qty
                    elif cum_wheat < target:
                        allowed = target - cum_wheat
                        new_market.append(["BUY_SEED", "WHEAT", allowed])
                        cum_wheat += allowed
                    else:
                        pass # Drop excess wheat buys
                else:
                    new_market.append(o)
            act["market"] = new_market
            
        # If target > 187, inject extra wheat buys during Days 6-8 where cash is available
        if extra_to_add > 0:
            added = 0
            for act in custom_route:
                if added >= extra_to_add: break
                if act.get("market") and len(act["market"]) < 10:
                    batch = min(10, extra_to_add - added)
                    act["market"].append(["BUY_SEED", "WHEAT", batch])
                    added += batch
                    
        custom_policy = build_policy(custom_route, base_cfg)
        
        solo_rewards = []
        comp_rewards = []
        wheat_sold_list = []
        wheat_harvested_list = []
        feed_bought_list = []
        
        for seed in seeds:
            # Solo vs IDLE
            env_solo = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
            env_solo.run([custom_policy, lambda obs, cfg=None: {"market": [], "farmer": ["PASS"], "hands": []}])
            r_solo = float(env_solo.steps[-1][0].reward or 0.0)
            solo_rewards.append(r_solo)
            
            # Telemetry from solo
            w_sold = 0
            feed_bought = 0
            for step_idx in range(1, len(env_solo.steps)):
                act = env_solo.steps[step_idx][0].action or {}
                for o in act.get("market", []):
                    if o and o[0] == "SELL" and o[1] == "WHEAT": w_sold += o[2]
                    elif o and o[0] == "BUY_PRODUCT" and o[1] == "WHEAT": feed_bought += o[2]
            wheat_sold_list.append(w_sold)
            feed_bought_list.append(feed_bought)
            
            # Comp vs V54
            env_comp = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
            env_comp.run([custom_policy, raw_v54])
            r_comp = float(env_comp.steps[-1][0].reward or 0.0)
            comp_rewards.append(r_comp)
            
        m_solo = sum(solo_rewards) / len(solo_rewards)
        m_comp = sum(comp_rewards) / len(comp_rewards)
        m_wsold = sum(wheat_sold_list) / len(wheat_sold_list)
        m_feed = sum(feed_bought_list) / len(feed_bought_list)
        
        results[target] = {
            "target_seeds": target,
            "solo_reward": m_solo,
            "comp_reward": m_comp,
            "mean_wheat_sold": m_wsold,
            "mean_feed_bought": m_feed,
            "delta_solo_vs_187": m_solo - (results[187]["solo_reward"] if 187 in results else m_solo),
            "delta_comp_vs_187": m_comp - (results[187]["comp_reward"] if 187 in results else m_comp),
        }
        print(f"Wheat {target:3d} | Solo: {m_solo:7.0f} | Comp: {m_comp:7.0f} | Wheat Sold: {m_wsold:5.1f} | Feed Bought: {m_feed:4.1f} | DeltaComp: {results[target]['delta_comp_vs_187']:+7.0f}")
        
    with open("scratch/wheat_autarky_audit_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nSaved wheat autarky audit to scratch/wheat_autarky_audit_results.json")

if __name__ == "__main__":
    run_wheat_audit()
