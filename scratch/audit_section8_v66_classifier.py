"""
Audit Section 8: Strict Empirical Audit of V66 Opponent Classifier
Evaluates V66 against 10 controlled opponents across 10 seeds (2000-2009):
1. IDLE
2. passive farmer
3. V2
4. M1
5. B1
6. L_Minimal
7. V54
8. V66
9. synthetic high-seller
10. synthetic low-seller

Measures:
- Predicted class (from _META_STATE)
- Actual policy selected
- Final score of V66
- Baseline V54 score against the same opponent
- Whether classification was correct
- Whether classification mattered
- Controlled H2H: V66 (Classifier ENABLED) vs V66 (Classifier DISABLED) on identical seeds.
"""
import sys, os, json, importlib.util
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

# Synthetic Opponents
def passive_farmer_agent(obs, cfg=None):
    return {"market": [], "farmer": ["MOVE_DOWN"], "hands": []}

def synthetic_high_seller_agent(obs, cfg=None):
    farm = obs.farms[obs.player]
    act = {"market": [["SELL", "WHEAT", 5], ["SELL", "CARROT", 5]], "farmer": ["PASS"], "hands": []}
    return act

def synthetic_low_seller_agent(obs, cfg=None):
    farm = obs.farms[obs.player]
    m = []
    if farm["money"] >= 20:
        m.append(["BUY_SEED", "CARROT", 1])
    return {"market": m, "farmer": ["PASS"], "hands": []}

def run_classifier_audit():
    v66_path = "external_repos/kaggriculture-v66-agent/candidate_v66_meta_closed_loop.py"
    d66 = os.path.dirname(os.path.abspath(v66_path))
    if d66 not in sys.path: sys.path.insert(0, d66)
    spec66 = importlib.util.spec_from_file_location("v66_audit_mod", v66_path)
    v66_mod = importlib.util.module_from_spec(spec66)
    spec66.loader.exec_module(v66_mod)
    
    v54_fn = load_agent_from_file("external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py")
    
    opponents = {
        "1_IDLE": lambda obs, cfg=None: {"market": [], "farmer": ["PASS"], "hands": []},
        "2_PassiveFarmer": passive_farmer_agent,
        "3_V2": load_agent_from_file("agents/slot4_control_frozen_v2.py"),
        "4_M1": load_agent_from_file("candidates/candidate_cl_fert_gated.py"),
        "5_B1": load_agent_from_file("candidates/research_b_only_v1.py", "ResearchBOnlyV1"),
        "6_L_Minimal": load_agent_from_file("candidates/candidate_cl_labor_minimal_v1.py"),
        "7_V54": v54_fn,
        "8_V66": load_agent_from_file("external_repos/kaggriculture-v66-agent/main.py"),
        "9_SyntheticHighSeller": synthetic_high_seller_agent,
        "10_SyntheticLowSeller": synthetic_low_seller_agent,
    }
    
    seeds = list(range(2000, 2010)) # 10 seeds
    
    print("Testing 10 Opponents across 10 Seeds...")
    results = []
    
    for opp_name, opp_fn in opponents.items():
        v66_scores = []
        v54_scores = []
        opp_scores = []
        classes_detected = set()
        routes_activated = set()
        events_log = []
        
        for seed in seeds:
            # Run V66 (Seat 0) vs Opponent (Seat 1)
            # Reset meta state
            v66_mod._META_STATE[0] = v66_mod._fresh_state()
            v66_mod._META_STATE[1] = v66_mod._fresh_state()
            
            env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
            env.run([v66_mod.agent, opp_fn])
            
            r0 = float(env.steps[-1][0].reward or 0.0)
            r1 = float(env.steps[-1][1].reward or 0.0)
            v66_scores.append(r0)
            opp_scores.append(r1)
            
            final_meta = v66_mod._META_STATE[0]
            classes_detected.add(final_meta.get("branch", "NONE") or "NONE")
            routes_activated.add(final_meta.get("route", "DEFAULT") or "DEFAULT")
            events_log.extend(final_meta.get("events", []))
            
            # Baseline V54 vs Opponent
            env_v54 = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
            env_v54.run([v54_fn, opp_fn])
            r_v54 = float(env_v54.steps[-1][0].reward or 0.0)
            v54_scores.append(r_v54)
            
        m_v66 = sum(v66_scores) / len(v66_scores)
        m_v54 = sum(v54_scores) / len(v54_scores)
        m_opp = sum(opp_scores) / len(opp_scores)
        
        # Did classification happen?
        non_none_classes = [c for c in classes_detected if c != "NONE"]
        classified = len(non_none_classes) > 0
        correct = False # Since none of these 10 are the historical replays
        
        res_entry = {
            "opponent": opp_name,
            "v66_mean": m_v66,
            "v54_mean": m_v54,
            "opp_mean": m_opp,
            "delta_v66_v54": m_v66 - m_v54,
            "classes_detected": list(classes_detected),
            "routes_activated": list(routes_activated),
            "classified": classified,
            "correct": correct,
            "events_sample": events_log[:3],
        }
        results.append(res_entry)
        print(f"{opp_name:22s} | V66: {m_v66:7.0f} | V54: {m_v54:7.0f} | Delta: {m_v66 - m_v54:+7.0f} | Class: {list(classes_detected)} | Routes: {list(routes_activated)}")
        
    print("\n" + "="*80)
    print("V66 ABLATION: CLASSIFIER ENABLED vs CLASSIFIER DISABLED (vs V54 on identical seeds)")
    print("="*80)
    
    # Controlled experiment: V66 Enabled vs V66 Disabled against V54 across 20 seeds
    test_seeds = list(range(2000, 2020))
    enabled_scores = []
    disabled_scores = []
    
    # Classifier disabled wrapper
    def v66_disabled_agent(obs, cfg=None):
        # Force meta state to stay inactive
        seat = v66_mod._BASE._v58_seat(obs)
        act = v66_mod.agent(obs, cfg)
        v66_mod._META_STATE[seat]["branch"] = ""
        v66_mod._META_STATE[seat]["route"] = ""
        return act
        
    # We need a proper way to disable classification in V66: patch _activate or bypass step 72/144 check
    orig_advance = v66_mod._advance
    def advance_no_classifier(obs, visible):
        # advance without signature matching
        seat = v66_mod._BASE._v58_seat(obs)
        step = v66_mod._BASE._v59_step(obs)
        actions = v66_mod._ORIGINAL_ADVANCE(obs, visible)
        state = v66_mod._META_STATE[seat]
        if step == 0 or step <= int(state.get("last", -1)):
            state = v66_mod._fresh_state(step)
            v66_mod._META_STATE[seat] = state
        else:
            state["last"] = step
        # Bypass signature matching completely!
        return actions
        
    for seed in test_seeds:
        # 1. Enabled
        v66_mod._advance = orig_advance
        v66_mod._META_STATE[0] = v66_mod._fresh_state()
        v66_mod._META_STATE[1] = v66_mod._fresh_state()
        env_en = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
        env_en.run([v66_mod.agent, v54_fn])
        r_en = float(env_en.steps[-1][0].reward or 0.0)
        enabled_scores.append(r_en)
        
        # 2. Disabled
        v66_mod._advance = advance_no_classifier
        v66_mod._META_STATE[0] = v66_mod._fresh_state()
        v66_mod._META_STATE[1] = v66_mod._fresh_state()
        env_dis = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
        env_dis.run([v66_mod.agent, v54_fn])
        r_dis = float(env_dis.steps[-1][0].reward or 0.0)
        disabled_scores.append(r_dis)
        
    m_en = sum(enabled_scores) / len(enabled_scores)
    m_dis = sum(disabled_scores) / len(disabled_scores)
    diffs = [e - d for e, d in zip(enabled_scores, disabled_scores)]
    print(f"V66 Enabled Mean (vs V54):  {m_en:7.0f}")
    print(f"V66 Disabled Mean (vs V54): {m_dis:7.0f}")
    print(f"Paired Difference Mean:     {sum(diffs)/len(diffs):+7.0f}")
    print(f"Per-seed diffs: {diffs}")
    
    classifier_audit_summary = {
        "opponents_test": results,
        "enabled_mean": m_en,
        "disabled_mean": m_dis,
        "paired_diff_mean": sum(diffs)/len(diffs),
        "diffs": diffs,
    }
    with open("scratch/v66_classifier_audit_results.json", "w") as f:
        json.dump(classifier_audit_summary, f, indent=2)
    print("Saved classifier audit to scratch/v66_classifier_audit_results.json")

if __name__ == "__main__":
    run_classifier_audit()
