"""
Audit Section 13: Terminal Liquidation Timing Audit
Tests terminal liquidation trigger step: 620, 640, 650, 660, 670, 680, 690, 700
Measures:
- Remaining inventory at step 720 (unrealized value)
- Stranded seeds / late unharvested production
- Liquidation revenue captured
- Final reward (Solo and vs V54)
Evaluated across 10 identical seeds (2000-2009).
"""
import sys, os, json, importlib.util, copy
from kaggle_environments import make

def run_terminal_audit():
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
    steps_to_test = [620, 640, 650, 660, 670, 680, 690, 700]
    
    print("Executing Terminal Liquidation Timing Sweep across 10 seeds...")
    results = {}
    
    for liq_step in steps_to_test:
        # We can implement a wrapper that intercepts the terminal liquidation dump:
        # In V54, the terminal dump happens starting around step 670.
        # If we shift the liquidation dump:
        base_policy = build_policy(route, base_cfg)
        
        def make_shifted_terminal_agent(target_liq_step):
            # In V54, route has sales scheduled at 670-719.
            # If target_liq_step != 670:
            # If step >= target_liq_step, dump any shed goods!
            def agent_fn(obs, cfg=None):
                step = obs.get("step", obs.get("day", 0)*24 + obs.get("hour", 0))
                act = base_policy(obs, cfg)
                if not isinstance(act, dict): return act
                
                # If step is before target_liq_step, block late terminal dumps
                if step < target_liq_step and step >= 650:
                    market = act.get("market", [])
                    # filter out massive terminal dumps
                    act["market"] = [o for o in market if not (o and o[0] == "SELL" and o[2] > 10)]
                elif step >= target_liq_step:
                    # Force liquidation of all available shed inventory
                    farm = obs.farms[obs.player]
                    shed = farm.get("shed", {})
                    market = list(act.get("market", []))
                    existing_sells = {o[1] for o in market if o and o[0] == "SELL"}
                    for item, qty in shed.items():
                        if qty > 0 and item not in existing_sells and len(market) < 10:
                            market.append(["SELL", item, min(qty, 30)])
                    act["market"] = market[:10]
                return act
            return agent_fn
            
        policy = make_shifted_terminal_agent(liq_step)
        
        solo_rewards = []
        comp_rewards = []
        rem_inv_list = []
        
        for seed in seeds:
            # Solo
            env_solo = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
            env_solo.run([policy, lambda obs, cfg=None: {"market": [], "farmer": ["PASS"], "hands": []}])
            r_solo = float(env_solo.steps[-1][0].reward or 0.0)
            solo_rewards.append(r_solo)
            
            # Check remaining inventory in shed
            final_farm = env_solo.steps[-1][0].observation.farms[0]
            rem_inv = sum(final_farm.get("shed", {}).values())
            rem_inv_list.append(rem_inv)
            
            # Comp
            env_comp = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
            env_comp.run([policy, raw_v54])
            r_comp = float(env_comp.steps[-1][0].reward or 0.0)
            comp_rewards.append(r_comp)
            
        m_solo = sum(solo_rewards) / len(solo_rewards)
        m_comp = sum(comp_rewards) / len(comp_rewards)
        m_inv = sum(rem_inv_list) / len(rem_inv_list)
        
        results[liq_step] = {
            "liquidation_step": liq_step,
            "solo_reward": m_solo,
            "comp_reward": m_comp,
            "rem_inventory": m_inv,
            "delta_solo_vs_670": m_solo - (results[670]["solo_reward"] if 670 in results else m_solo),
            "delta_comp_vs_670": m_comp - (results[670]["comp_reward"] if 670 in results else m_comp),
        }
        print(f"Step {liq_step:3d} | Solo: {m_solo:7.0f} | Comp: {m_comp:7.0f} | Remaining Inv: {m_inv:4.1f} | DeltaComp: {results[liq_step]['delta_comp_vs_670']:+7.0f}")
        
    with open("scratch/terminal_liquidation_audit_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nSaved terminal liquidation audit to scratch/terminal_liquidation_audit_results.json")

if __name__ == "__main__":
    run_terminal_audit()
