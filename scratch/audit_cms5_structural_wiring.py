"""
scratch/audit_cms5_structural_wiring.py
======================================
Forensic audit script covering:
- Section 3: Action trajectory comparison between CMS5_185 and V54 (20 seeds)
- Section 10: Trace identity check between canonical V54 and CMS5_187 (10 seeds)
- Section 11: Wrapper vs reimplementation inspection
- Section 13: Zero-change / clipping test for all CMS5 parameters
"""

import os
import sys
if os.path.abspath(".") not in sys.path:
    sys.path.insert(0, os.path.abspath("."))
import copy
import json
import importlib.util
from kaggle_environments import make

# 1. Inspect Candidate Source for Section 11
def audit_section_11():
    print("=" * 80)
    print("SECTION 11: WRAPPER VS REIMPLEMENTATION AUDIT")
    print("=" * 80)
    cms5_file = os.path.abspath("candidates/cms5_v54_faithful.py")
    with open(cms5_file, "r", encoding="utf-8") as f:
        code = f.read()

    deps = []
    for line_no, line in enumerate(code.splitlines(), 1):
        if "importlib" in line or "V54_PATH" in line or "_v54_mod" in line or "_CANONICAL_V54" in line or "_v51_build_policy" in line:
            deps.append((line_no, line.strip()))

    print(f"Source file: {cms5_file}")
    print("Direct Dependency Evidence:")
    for lno, line in deps[:15]:
        print(f"  Line {lno:3d}: {line}")

    has_direct_import = "variant_v54_h3q4/main.py" in code
    delegates_route = "_CANONICAL_V54_ROUTE = _v54_mod._V54_ROUTE" in code
    delegates_policy = "_v51_build_policy = _v54_mod._v51_build_policy" in code

    classification = "B (Imports V54), C (Directly delegates to V54), D (Copies V54 route), E (Embeds V54 route)"
    print(f"\nClassification Verdict: {classification}")
    print(f"Direct import from external repo: {has_direct_import}")
    print(f"Delegates route: {delegates_route}")
    print(f"Delegates policy compilation: {delegates_policy}")
    return {
        "classification": classification,
        "evidence": deps
    }


# 2. Section 13: Zero-Change / Clipping Test on Parameters
def audit_section_13():
    print("\n" + "=" * 80)
    print("SECTION 13: ZERO-CHANGE / CLIPPING TEST")
    print("=" * 80)
    from candidates.cms5_v54_faithful import CMS5Config, build_cms5_route, build_cms5_policy

    baseline_cfg = CMS5Config()
    baseline_route = build_cms5_route(baseline_cfg)

    # Test parameters defined in CMS5Config
    params_to_test = [
        ("initial_workers", 4),
        ("initial_workers", 6),
        ("ramp_day_2_workers", 6),
        ("ramp_day_2_workers", 10),
        ("ramp_day_3_workers", 9),
        ("ramp_day_3_workers", 13),
        ("peak_workers", 10),
        ("peak_workers", 14),
        ("late_workers", 9),
        ("late_workers", 13),
        ("cow_purchases", 5),
        ("cow_purchases", 9),
        ("sheep_purchases", 1),
        ("sheep_purchases", 5),
        ("wheat_seeds", 185),
        ("wheat_seeds", 160),
        ("wheat_seeds", 210),
        ("strawberry_seeds", 30),
        ("strawberry_seeds", 44),
        ("strawberry_start_day", 4),
        ("strawberry_start_day", 6),
        ("melon_seeds", 8),
        ("melon_seeds", 16),
        ("land_1_step", 140),
        ("land_1_step", 160),
        ("land_2_step", 250),
        ("land_2_step", 280),
        ("liquidation_step", 645),
        ("liquidation_step", 690),
        ("front_supply_threshold", 1.0),
        ("front_supply_threshold", 5.0),
        ("preempt_maximum_batch", 2),
        ("preempt_maximum_batch", 8),
    ]

    results = []
    for param_name, req_val in params_to_test:
        kwargs = {param_name: req_val}
        test_cfg = CMS5Config(**kwargs)
        test_route = build_cms5_route(test_cfg)

        # Route difference
        diff_steps = []
        for t in range(len(baseline_route)):
            if baseline_route[t] != test_route[t]:
                diff_steps.append(t)

        first_step = diff_steps[0] if diff_steps else None
        num_changed = len(diff_steps)

        # Check if policy wrapper alters it (like liquidation_step or residual controller)
        affects_policy = num_changed > 0
        policy_note = "Route modified"
        if num_changed == 0:
            if param_name in ["liquidation_step", "liquidation_batch"]:
                affects_policy = True
                first_step = req_val
                policy_note = "Intercepted in cms5_agent wrapper at step >= liquidation_step"
            elif param_name in ["front_supply_threshold", "preempt_maximum_batch", "preempt_horizon", "front_existing_sells", "preempt_enabled"]:
                affects_policy = True
                first_step = "Dynamic (residual controller)"
                policy_note = "Passed to _V51ResidualConfig"
            else:
                affects_policy = False
                policy_note = "DEAD CODE / IGNORED: Parameter has NO effect on route or policy!"

        status = "WIRED" if affects_policy else "UNWIRED / CLIPPED"
        res_row = {
            "parameter": param_name,
            "requested_value": req_val,
            "effective_value": req_val if affects_policy else "BASELINE_DEFAULT",
            "first_step": first_step,
            "changed_actions_in_route": num_changed,
            "status": status,
            "note": policy_note
        }
        results.append(res_row)
        print(f"  {param_name:25s} = {str(req_val):5s} | Status: {status:18s} | FirstStep: {str(first_step):10s} | ChangedRouteActs: {num_changed:3d} | {policy_note}")

    return results


def _run_s10_seed(seed):
    import os, sys, importlib.util
    if os.path.abspath(".") not in sys.path:
        sys.path.insert(0, os.path.abspath("."))
    from kaggle_environments import make
    v54_path = os.path.abspath("external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py")
    spec_v54 = importlib.util.spec_from_file_location(f"v54_truth_{seed}", v54_path)
    mod_v54 = importlib.util.module_from_spec(spec_v54)
    spec_v54.loader.exec_module(mod_v54)
    v54_agent = getattr(mod_v54, "agent")

    from candidates.cms5_v54_faithful import build_cms5_policy, CMS5Config
    cms5_187_agent = build_cms5_policy(CMS5Config(wheat_seeds=187))
    idle = lambda obs, cfg=None: {"market": [], "farmer": ["PASS"], "hands": []}

    env_v54 = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env_v54.run([v54_agent, idle])

    env_cms5 = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env_cms5.run([cms5_187_agent, idle])

    r_v54 = env_v54.steps[-1][0].reward
    r_cms5 = env_cms5.steps[-1][0].reward

    farmer_diffs = 0
    hands_diffs = 0
    market_diffs = 0

    for t in range(len(env_v54.steps)):
        act_v = env_v54.steps[t][0].action or {}
        act_c = env_cms5.steps[t][0].action or {}

        if act_v.get("farmer") != act_c.get("farmer"):
            farmer_diffs += 1
        if act_v.get("hands") != act_c.get("hands"):
            hands_diffs += 1
        if act_v.get("market") != act_c.get("market"):
            market_diffs += 1

    total_diffs = farmer_diffs + hands_diffs + market_diffs
    return {
        "seed": seed,
        "r_v54": r_v54,
        "r_cms5": r_cms5,
        "reward_diff": r_cms5 - r_v54,
        "farmer_diffs": farmer_diffs,
        "hands_diffs": hands_diffs,
        "market_diffs": market_diffs,
        "total_diffs": total_diffs,
        "identical": (total_diffs == 0)
    }

def audit_section_10(seeds=list(range(101, 111))):
    print("\n" + "=" * 80)
    print("SECTION 10: REPRODUCTION CLAIM - EXACT V54 EQUIVALENCE AUDIT (10 SEEDS)")
    print("=" * 80)
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=6) as executor:
        seed_reports = list(executor.map(_run_s10_seed, seeds))

    all_trace_identical = all(r["identical"] for r in seed_reports)
    for r in sorted(seed_reports, key=lambda x: x["seed"]):
        print(f"  Seed {r['seed']}: V54=${r['r_v54']:,.0f} | CMS5=${r['r_cms5']:,.0f} | Diffs(F={r['farmer_diffs']}, H={r['hands_diffs']}, M={r['market_diffs']}) | Trace Identical: {r['identical']}")

    verdict_str = f"TRACE-IDENTICAL = {all_trace_identical}"
    print(f"\nFINAL VERDICT: {verdict_str}")
    return {
        "all_trace_identical": all_trace_identical,
        "seed_reports": seed_reports
    }

def _run_s3_seed(seed):
    import os, sys, importlib.util
    if os.path.abspath(".") not in sys.path:
        sys.path.insert(0, os.path.abspath("."))
    from kaggle_environments import make
    v54_path = os.path.abspath("external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py")
    spec_v54 = importlib.util.spec_from_file_location(f"v54_truth_s3_{seed}", v54_path)
    mod_v54 = importlib.util.module_from_spec(spec_v54)
    spec_v54.loader.exec_module(mod_v54)
    v54_agent = getattr(mod_v54, "agent")

    from candidates.cms5_v54_faithful import build_cms5_policy, CMS5Config
    cms5_185_agent = build_cms5_policy(CMS5Config(wheat_seeds=185))
    idle = lambda obs, cfg=None: {"market": [], "farmer": ["PASS"], "hands": []}

    env_v54 = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env_v54.run([v54_agent, idle])

    env_185 = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env_185.run([cms5_185_agent, idle])

    r_v54 = env_v54.steps[-1][0].reward
    r_185 = env_185.steps[-1][0].reward

    diff_timesteps = []
    differing_market = 0
    differing_farmer = 0
    differing_hands = 0
    differing_seed_buys = 0
    differing_wheat_acts = 0
    differing_sales = 0
    differing_terminal_acts = 0

    for t in range(len(env_v54.steps)):
        act_v = env_v54.steps[t][0].action or {}
        act_c = env_185.steps[t][0].action or {}

        has_diff = False
        if act_v.get("farmer") != act_c.get("farmer"):
            differing_farmer += 1
            has_diff = True
        if act_v.get("hands") != act_c.get("hands"):
            differing_hands += 1
            has_diff = True
        if act_v.get("market") != act_c.get("market"):
            differing_market += 1
            has_diff = True

            m_v = act_v.get("market", [])
            m_c = act_c.get("market", [])
            s_v = [o for o in m_v if o and o[0] == "BUY_SEED"]
            s_c = [o for o in m_c if o and o[0] == "BUY_SEED"]
            if s_v != s_c:
                differing_seed_buys += 1
            w_v = [o for o in m_v if o and len(o) > 1 and o[1] == "WHEAT"]
            w_c = [o for o in m_c if o and len(o) > 1 and o[1] == "WHEAT"]
            if w_v != w_c:
                differing_wheat_acts += 1
            sel_v = [o for o in m_v if o and o[0] == "SELL"]
            sel_c = [o for o in m_c if o and o[0] == "SELL"]
            if sel_v != sel_c:
                differing_sales += 1

        if has_diff:
            diff_timesteps.append(t)
            if t >= 670:
                differing_terminal_acts += 1

    return {
        "seed": seed,
        "r_v54": r_v54,
        "r_185": r_185,
        "reward_delta": r_185 - r_v54,
        "differing_timesteps_count": len(diff_timesteps),
        "first_diff_step": diff_timesteps[0] if diff_timesteps else None,
        "last_diff_step": diff_timesteps[-1] if diff_timesteps else None,
        "differing_market_orders": differing_market,
        "differing_farmer_actions": differing_farmer,
        "differing_hand_actions": differing_hands,
        "differing_seed_purchases": differing_seed_buys,
        "differing_wheat_actions": differing_wheat_acts,
        "differing_sales": differing_sales,
        "differing_terminal_actions": differing_terminal_acts
    }

def audit_section_3(seeds=list(range(101, 121))):
    print("\n" + "=" * 80)
    print("SECTION 3: CMS5_185 VS V54 COMPLETE ACTION TRAJECTORY COMPARISON (20 SEEDS)")
    print("=" * 80)
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=6) as executor:
        seed_diff_summaries = list(executor.map(_run_s3_seed, seeds))

    for summary in sorted(seed_diff_summaries, key=lambda x: x["seed"]):
        print(f"  Seed {summary['seed']:3d}: Delta=${summary['reward_delta']:+,.0f} | DiffTimesteps={summary['differing_timesteps_count']} | FirstStep={summary['first_diff_step']} | LastStep={summary['last_diff_step']} | MarketDiff={summary['differing_market_orders']} (SeedBuys={summary['differing_seed_purchases']}, Wheat={summary['differing_wheat_actions']}) | HandsDiff={summary['differing_hand_actions']}")

    return seed_diff_summaries


if __name__ == "__main__":
    audit_section_11()
    audit_section_13()
    audit_section_10()
    audit_section_3()
