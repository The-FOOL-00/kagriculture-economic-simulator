"""
Audit Section 4 & Section 5: Hierarchical Reconstruction, Leave-One-Out & Priority Rankings
Tests whether the 'Six Mechanisms' (Labor, Livestock, Wheat, Strawberry, Market Controller, Terminal Liquidation)
are genuinely minimal and sufficient.

1. Hierarchical Construction:
B0: Minimal valid executor (Pass/basic chore loop, baseline cash)
B1: B0 + Dynamic Labor Ramp
B2: B1 + Early Livestock Fleet
B3: B2 + Self-Sufficient Wheat Engine
B4: B3 + Recurring Strawberry Wave
B5: B4 + Market Controller (Front-running threshold 3)
B6: B5 + Terminal Liquidation (Step 670 dump)

2. Leave-One-Out (LOO) on B6:
- LOO_Labor: B6 without Labor Ramp
- LOO_Livestock: B6 without Livestock
- LOO_Wheat: B6 without Wheat
- LOO_Strawberry: B6 without Strawberry
- LOO_Market: B6 without Market Controller
- LOO_Terminal: B6 without Terminal Liquidation

3. Priority Rankings:
Ranking A: Pure causal effect in isolation
Ranking B: Marginal effect after prior mechanisms are established
"""
import sys, os, json, importlib.util, copy
from kaggle_environments import make

def run_minimality_audit():
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
    ResidualConfig = v54_mod._V51ResidualConfig
    
    seeds = list(range(2000, 2010)) # 10 seeds
    
    # Let's define the filtered routes for B0 -> B6:
    # B0: Strips all hires, animals, wheat, strawberries, market controller, terminal dump
    # To make B0 a valid executor: 2 baseline workers, passes, basic carrot/melon
    
    def build_hierarchical_policy(level):
        custom_route = copy.deepcopy(route)
        cfg_dict = copy.deepcopy(base_cfg.__dict__)
        
        # Determine mechanism inclusions:
        inc_labor = (level >= 1)
        inc_livestock = (level >= 2)
        inc_wheat = (level >= 3)
        inc_strawb = (level >= 4)
        inc_market = (level >= 5)
        inc_terminal = (level >= 6)
        
        for step_idx, act in enumerate(custom_route):
            day = step_idx // 24
            new_m = []
            hires_today = 0
            for o in act.get("market", []):
                if not o: continue
                op = o[0]
                if op == "HIRE":
                    if inc_labor:
                        new_m.append(o)
                    else:
                        if hires_today < 2:
                            new_m.append(o)
                            hires_today += 1
                elif op == "BUY_ANIMAL":
                    if inc_livestock: new_m.append(o)
                elif op == "BUY_SEED" and o[1] == "WHEAT":
                    if inc_wheat: new_m.append(o)
                elif op == "BUY_SEED" and o[1] == "STRAWBERRY":
                    if inc_strawb: new_m.append(o)
                elif op == "SELL":
                    if not inc_terminal and step_idx >= 670:
                        pass # Drop terminal liquidation
                    else:
                        new_m.append(o)
                else:
                    new_m.append(o)
            act["market"] = new_m
            
        if not inc_market:
            cfg_dict["preempt_enabled"] = False
            cfg_dict["front_supply_threshold"] = 99999.0
            
        return build_policy(custom_route, ResidualConfig(**cfg_dict))

    def build_loo_policy(dropped_mech):
        custom_route = copy.deepcopy(route)
        cfg_dict = copy.deepcopy(base_cfg.__dict__)
        
        for step_idx, act in enumerate(custom_route):
            new_m = []
            hires_today = 0
            for o in act.get("market", []):
                if not o: continue
                op = o[0]
                if op == "HIRE" and dropped_mech == "Labor":
                    if hires_today < 2:
                        new_m.append(o)
                        hires_today += 1
                elif op == "BUY_ANIMAL" and dropped_mech == "Livestock":
                    pass
                elif op == "BUY_SEED" and o[1] == "WHEAT" and dropped_mech == "Wheat":
                    pass
                elif op == "BUY_SEED" and o[1] == "STRAWBERRY" and dropped_mech == "Strawberry":
                    pass
                elif op == "SELL" and dropped_mech == "Terminal" and step_idx >= 670:
                    pass
                else:
                    new_m.append(o)
            act["market"] = new_m
            
        if dropped_mech == "Market":
            cfg_dict["preempt_enabled"] = False
            cfg_dict["front_supply_threshold"] = 99999.0
            
        return build_policy(custom_route, ResidualConfig(**cfg_dict))

    print("Evaluating Hierarchical Reconstruction (B0 -> B6)...")
    ladder_results = {}
    prev_solo = 0.0
    prev_comp = 0.0
    
    stages = [
        ("B0_MinimalBase", 0),
        ("B1_PlusLabor", 1),
        ("B2_PlusLivestock", 2),
        ("B3_PlusWheat", 3),
        ("B4_PlusStrawberry", 4),
        ("B5_PlusMarketController", 5),
        ("B6_PlusTerminalLiquidation", 6),
    ]
    
    for name, lvl in stages:
        policy = build_hierarchical_policy(lvl)
        solo_r = []
        comp_r = []
        for seed in seeds:
            env_s = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
            env_s.run([policy, lambda obs, cfg=None: {"market": [], "farmer": ["PASS"], "hands": []}])
            solo_r.append(float(env_s.steps[-1][0].reward or 0.0))
            
            env_c = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
            env_c.run([policy, raw_v54])
            comp_r.append(float(env_c.steps[-1][0].reward or 0.0))
            
        m_solo = sum(solo_r) / len(solo_r)
        m_comp = sum(comp_r) / len(comp_r)
        marg_solo = m_solo - prev_solo if lvl > 0 else m_solo
        marg_comp = m_comp - prev_comp if lvl > 0 else m_comp
        prev_solo = m_solo
        prev_comp = m_comp
        
        ladder_results[name] = {
            "level": lvl,
            "solo_reward": m_solo,
            "comp_reward": m_comp,
            "marginal_solo": marg_solo,
            "marginal_comp": marg_comp,
        }
        print(f"{name:26s} | Solo: {m_solo:7.0f} (Marg: {marg_solo:+7.0f}) | Comp: {m_comp:7.0f} (Marg: {marg_comp:+7.0f})")
        
    print("\nEvaluating Leave-One-Out Tests on B6...")
    b6_solo = ladder_results["B6_PlusTerminalLiquidation"]["solo_reward"]
    b6_comp = ladder_results["B6_PlusTerminalLiquidation"]["comp_reward"]
    
    loo_results = {}
    mechs = ["Labor", "Livestock", "Wheat", "Strawberry", "Market", "Terminal"]
    for m in mechs:
        policy = build_loo_policy(m)
        solo_r = []
        comp_r = []
        for seed in seeds:
            env_s = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
            env_s.run([policy, lambda obs, cfg=None: {"market": [], "farmer": ["PASS"], "hands": []}])
            solo_r.append(float(env_s.steps[-1][0].reward or 0.0))
            
            env_c = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
            env_c.run([policy, raw_v54])
            comp_r.append(float(env_c.steps[-1][0].reward or 0.0))
            
        m_s = sum(solo_r) / len(solo_r)
        m_c = sum(comp_r) / len(comp_r)
        deg_solo = m_s - b6_solo
        deg_comp = m_c - b6_comp
        
        loo_results[m] = {
            "dropped": m,
            "solo_reward": m_s,
            "comp_reward": m_c,
            "degradation_solo": deg_solo,
            "degradation_comp": deg_comp,
            "is_essential": abs(deg_comp) > 2000
        }
        print(f"Drop {m:12s} | Solo: {m_s:7.0f} (Delta {deg_solo:+7.0f}) | Comp: {m_c:7.0f} (Delta {deg_comp:+7.0f}) | Essential: {loo_results[m]['is_essential']}")
        
    full_minimality = {
        "ladder": ladder_results,
        "leave_one_out": loo_results
    }
    with open("scratch/minimality_audit_results.json", "w") as f:
        json.dump(full_minimality, f, indent=2)
    print("\nSaved minimality audit to scratch/minimality_audit_results.json")

if __name__ == "__main__":
    run_minimality_audit()
