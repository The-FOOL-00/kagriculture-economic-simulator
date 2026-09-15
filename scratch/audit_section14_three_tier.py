"""
Audit Section 14: Three-Tier Architecture Audit
Evaluates the marginal contribution of each tier:
Level 1: Macro Schedule
Level 2: Tactical Chore Execution
Level 3: Market Controller

Tests five progressive combinations across 10 identical seeds (2000-2009) vs IDLE and vs V54:
Arm A: Macro Only (Raw 719-step open-loop route, market controller disabled)
Arm B: Macro + Tactical (Open-loop route + local chore drift repair / EXP-A state adaptation)
Arm C: Macro + Market (Open-loop route + residual market controller: V54)
Arm D: Tactical + Market (Closed-loop chore executor + market controller without macro 719 route: M1/B1)
Arm E: Macro + Tactical + Market (Full three-tier integrated controller: V66)
"""
import sys, os, json, importlib.util, copy
from kaggle_environments import make

def load_agent_from_file(path, class_fallback=None):
    d = os.path.dirname(os.path.abspath(path))
    if d not in sys.path: sys.path.insert(0, d)
    name = os.path.splitext(os.path.basename(path))[0]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fn = getattr(mod, "agent", None) or getattr(mod, "_kaggle_submission_entrypoint", None)
    if fn is None and class_fallback and hasattr(mod, class_fallback):
        inst = getattr(mod, class_fallback)()
        fn = lambda obs, cfg=None: inst(obs, cfg)
    return fn

def run_three_tier_audit():
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
    
    seeds = list(range(2000, 2010))
    
    # Arm A: Macro Only (Direct replay of _V54_ROUTE without market controller)
    def policy_macro_only(obs, cfg=None):
        step = obs.get("step", obs.get("day", 0)*24 + obs.get("hour", 0))
        if step < len(route):
            return route[step]
        return {"market": [], "farmer": ["PASS"], "hands": []}
        
    # Arm B: Macro + Tactical (EXP-A / Declarative Backbone)
    policy_macro_tactical = load_agent_from_file("candidates/declarative_backbone/agent.py")
    
    # Arm C: Macro + Market (Full V54)
    policy_macro_market = raw_v54
    
    # Arm D: Tactical + Market (M1_FertGate / B1_Modular)
    policy_tactical_market = load_agent_from_file("candidates/candidate_cl_fert_gated.py")
    
    # Arm E: Macro + Tactical + Market (V66)
    policy_all_three = load_agent_from_file("external_repos/kaggriculture-v66-agent/main.py")
    
    arms = {
        "A_Macro_Only": policy_macro_only,
        "B_Macro_Plus_Tactical": policy_macro_tactical,
        "C_Macro_Plus_Market": policy_macro_market,
        "D_Tactical_Plus_Market": policy_tactical_market,
        "E_Macro_Tactical_Market": policy_all_three,
    }
    
    print("Evaluating Three-Tier Architecture Combinations across 10 seeds...")
    results = {}
    
    for arm_name, fn in arms.items():
        solo_r = []
        comp_r = []
        for seed in seeds:
            # Solo
            env_s = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
            env_s.run([fn, lambda obs, cfg=None: {"market": [], "farmer": ["PASS"], "hands": []}])
            solo_r.append(float(env_s.steps[-1][0].reward or 0.0))
            
            # Comp vs V54
            env_c = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
            env_c.run([fn, raw_v54])
            comp_r.append(float(env_c.steps[-1][0].reward or 0.0))
            
        m_s = sum(solo_r) / len(solo_r)
        m_c = sum(comp_r) / len(comp_r)
        
        results[arm_name] = {
            "arm": arm_name,
            "solo_mean": m_s,
            "comp_mean": m_c,
            "margin_vs_v54": m_c - 80264.0, # vs baseline V54
        }
        print(f"{arm_name:24s} | Solo: {m_s:7.0f} | vs V54: {m_c:7.0f} | Margin: {m_c - 80264.0:+7.0f}")
        
    with open("scratch/three_tier_audit_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nSaved three-tier audit to scratch/three_tier_audit_results.json")

if __name__ == "__main__":
    run_three_tier_audit()
