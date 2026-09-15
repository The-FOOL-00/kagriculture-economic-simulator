"""
Step 6: Macro Intervention Ablations Engine (Fixed & Complete)
==============================================================
Constructs V54-derived variants isolating each macro difference:
  A1: V54 + V66 Batch Seed Schedule (batches seed buys instead of trickle buys)
  A2: V54 + V66 Wheat Schedule (Step 0 front-run buy 5 wheat, adjusted sales)
  A3: V54 + V66 Strawberry Seed Trim (_v60_seed_trim)
  A4: V54 + V66 Livestock Timing (Day 2 cow buy step 65 vs 66)
  A7: V54 + V66 Shed Guard (_v60_shed_guard)
  A8: V54 + V66 Terminal Schedule (_route_loaded_units + terminal market)
  A_BACKBONE: V54 with full V56 Backbone Route (e103819410-islet-full)

Evaluates all variants across 20 common seeds (101-120) under symmetric seats:
  - Solo (vs IDLE)
  - Competitive (vs Canonical V54)

Outputs:
  research/v54_v66_causal_ablations.csv
  research/v54_v66_causal_ablations.md
"""

import os
import sys
import copy
import time
import json
import csv
import numpy as np
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from kaggle_environments import make

V54_PATH = os.path.abspath("external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py")
V62_PATH = os.path.abspath("external_repos/kaggriculture-v66-agent/candidate_v62_composite_bakery_yarn.py")
V66_PATH = os.path.abspath("external_repos/kaggriculture-v66-agent/candidate_v66_meta_closed_loop.py")

SEEDS = list(range(101, 121))  # 20 common seeds

import importlib.util
def load_base_modules():
    spec54 = importlib.util.spec_from_file_location("v54_ab", V54_PATH)
    mod54 = importlib.util.module_from_spec(spec54)
    spec54.loader.exec_module(mod54)

    d = os.path.dirname(V62_PATH)
    if d not in sys.path: sys.path.insert(0, d)
    spec62 = importlib.util.spec_from_file_location("v62_ab", V62_PATH)
    mod62 = importlib.util.module_from_spec(spec62)
    spec62.loader.exec_module(mod62)

    spec66 = importlib.util.spec_from_file_location("v66_ab", V66_PATH)
    mod66 = importlib.util.module_from_spec(spec66)
    spec66.loader.exec_module(mod66)

    return mod54, mod62, mod66

def idle_agent(obs, configuration=None):
    return {"farmer": ["PASS"], "hands": [], "market": []}

def build_variant_policy(variant_id, mod54, mod62, mod66):
    r54 = copy.deepcopy(mod54._V54_ROUTE)
    cfg54 = copy.deepcopy(mod54._V54_CONFIG)

    v60_seed_trim = mod62._v60_seed_trim
    v60_shed_guard = mod62._v60_shed_guard
    route_loaded_units = mod66._route_loaded_units
    terminal_market = mod66._TERMINAL_MARKET

    r66 = mod62._V56_BACKBONE_ROUTE

    if variant_id == "A1":
        # A1: Batch seed schedule - replace V54 trickle seed buys with V66 batched seed buys
        for s in range(719):
            v66_seeds = [o for o in r66[s].get("market", []) if o and o[0] == "BUY_SEED"]
            mkt_non_seeds = [o for o in r54[s].get("market", []) if not (o and o[0] == "BUY_SEED")]
            r54[s]["market"] = mkt_non_seeds + v66_seeds

    elif variant_id == "A2":
        # A2: Wheat schedule - Step 0 wheat buy + remove step 1 wheat buy
        r54[0]["market"] = [["BUY_PRODUCT", "WHEAT", 5]]
        r54[1]["market"] = [o for o in r54[1].get("market", []) if not (o and o[0] == "BUY_PRODUCT" and o[1] == "WHEAT")]
        # Also adopt V66 wheat selling sequence in opening
        for s in range(2, 20):
            v66_wheat_sells = [o for o in r66[s].get("market", []) if o and o[0] == "SELL" and o[1] == "WHEAT"]
            v54_non_wheat_sells = [o for o in r54[s].get("market", []) if not (o and o[0] == "SELL" and o[1] == "WHEAT")]
            r54[s]["market"] = v54_non_wheat_sells + v66_wheat_sells

    elif variant_id == "A3":
        # A3: Strawberry seed trim (runtime wrapper)
        pass

    elif variant_id == "A4":
        # A4: Livestock schedule - Day 2 cow purchase step 65 vs 66
        # Move step 66 cow buy to step 65
        c_66 = [o for o in r54[66].get("market", []) if o and o[0] == "BUY_ANIMAL"]
        r54[66]["market"] = [o for o in r54[66].get("market", []) if not (o and o[0] == "BUY_ANIMAL")]
        r54[65]["market"] = r54[65].get("market", []) + c_66

    elif variant_id == "A7":
        # A7: Shed guard (runtime wrapper)
        pass

    elif variant_id == "A8":
        # A8: Terminal schedule (runtime wrapper)
        pass

    elif variant_id == "A_BACKBONE":
        # Full V56 Backbone route under V54 controller
        r54 = copy.deepcopy(r66)

    # Build underlying policy
    raw_policy = mod54._v51_build_policy(r54, cfg54)

    def agent(obs, configuration=None):
        step = int((obs or {}).get("step", 0) or 0)
        action = raw_policy(obs, configuration)

        if variant_id == "A3":
            action = v60_seed_trim(obs, action, step)

        if variant_id == "A7":
            cap = int((configuration or {}).get("shedCapacity", 100)) or 100
            action = v60_shed_guard(obs, action, cap)

        if variant_id == "A8":
            if 713 <= step <= 716:
                action = route_loaded_units(obs, action, step)
            if step in (717, 718):
                action = mod66._TERMINAL_UNITS(obs, action, step)
            if step == 718:
                action = terminal_market(obs, action, rule="collision", replace=True)

        return action

    return agent

def run_match_pair(task):
    seed, variant_id, opp_type = task
    mod54, mod62, mod66 = load_base_modules()

    var_agent = build_variant_policy(variant_id, mod54, mod62, mod66)
    opp_agent = idle_agent if opp_type == "IDLE" else mod54.agent

    rewards_var = []
    rewards_opp = []

    # Seat 0
    env0 = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env0.reset()
    for s in range(719):
        o0, o1 = env0.state[0].observation, env0.state[1].observation
        o0["step"], o1["step"] = s, s
        a0 = var_agent(o0, env0.configuration)
        a1 = opp_agent(o1, env0.configuration)
        env0.step([a0, a1])
    rewards_var.append(float(env0.steps[-1][0].reward or 0.0))
    rewards_opp.append(float(env0.steps[-1][1].reward or 0.0))

    # Seat 1
    env1 = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env1.reset()
    for s in range(719):
        o0, o1 = env1.state[0].observation, env1.state[1].observation
        o0["step"], o1["step"] = s, s
        a0 = opp_agent(o0, env1.configuration)
        a1 = var_agent(o1, env1.configuration)
        env1.step([a0, a1])
    rewards_opp.append(float(env1.steps[-1][0].reward or 0.0))
    rewards_var.append(float(env1.steps[-1][1].reward or 0.0))

    return {
        "seed": seed,
        "variant_id": variant_id,
        "opp_type": opp_type,
        "var_rewards": rewards_var,
        "opp_rewards": rewards_opp,
        "mean_var_reward": float(np.mean(rewards_var)),
        "mean_opp_reward": float(np.mean(rewards_opp)),
        "margin": float(np.mean(rewards_var)) - float(np.mean(rewards_opp))
    }

def bootstrap_ci(deltas, num_samples=10000, alpha=0.05):
    arr = np.array(deltas)
    n = len(arr)
    boot_means = []
    np.random.seed(42)
    for _ in range(num_samples):
        s = np.random.choice(arr, size=n, replace=True)
        boot_means.append(np.mean(s))
    return float(np.percentile(boot_means, 100 * (alpha / 2))), float(np.percentile(boot_means, 100 * (1 - alpha / 2)))

def main():
    print("=" * 80)
    print("STEP 6: MACRO INTERVENTION ABLATIONS BENCHMARK")
    print("Variants A1-A8 & A_BACKBONE across 20 Common Seeds (101-120) vs IDLE & vs V54")
    print("=" * 80, flush=True)

    variants = ["A1", "A2", "A3", "A4", "A7", "A8", "A_BACKBONE"]
    tasks = []
    for var in variants:
        for opp in ["IDLE", "V54"]:
            for s in SEEDS:
                tasks.append((s, var, opp))

    t0 = time.time()
    results_by_var_opp = defaultdict(list)
    with ProcessPoolExecutor(max_workers=8) as pool:
        for res in pool.map(run_match_pair, tasks):
            key = (res["variant_id"], res["opp_type"])
            results_by_var_opp[key].append(res)
            print(f"[{res['variant_id']} vs {res['opp_type']}] Seed {res['seed']} | Var: ${res['mean_var_reward']:,.0f} | Opp: ${res['mean_opp_reward']:,.0f} | Margin: {res['margin']:+,.0f}", flush=True)

    elapsed = time.time() - t0
    print(f"\nAll ablation simulations completed in {elapsed:.1f}s.")

    # Calculate V54 solo baseline
    mod54, _, _ = load_base_modules()
    v54_solo_rews = []
    for s in SEEDS:
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": s})
        env.reset()
        for step in range(719):
            o0, o1 = env.state[0].observation, env.state[1].observation
            o0["step"], o1["step"] = step, step
            env.step([mod54.agent(o0, env.configuration), idle_agent(o1, env.configuration)])
        v54_solo_rews.append(float(env.steps[-1][0].reward or 0.0))
    v54_solo_mean = float(np.mean(v54_solo_rews))

    summary_rows = []
    labels = {
        "A1": "A1: Batch Seed Schedule",
        "A2": "A2: Step 0 Wheat Front-Run",
        "A3": "A3: Strawberry Seed Trim (_v60_seed_trim)",
        "A4": "A4: Day 2 Cow Buy Timing",
        "A7": "A7: Shed Guard (_v60_shed_guard)",
        "A8": "A8: Terminal Schedule (_route_loaded_units + market)",
        "A_BACKBONE": "A_BACKBONE: Full V56 Backbone Route (e103819410)"
    }

    for var in variants:
        solo_list = results_by_var_opp[(var, "IDLE")]
        comp_list = results_by_var_opp[(var, "V54")]

        solo_rews = [r["mean_var_reward"] for r in solo_list]
        comp_margins = [r["margin"] for r in comp_list]

        ci_low, ci_high = bootstrap_ci(comp_margins)

        summary_rows.append({
            "VARIANT": var,
            "MECHANISM": labels[var],
            "SOLO_REWARD_MEAN": float(np.mean(solo_rews)),
            "SOLO_DELTA_VS_V54": float(np.mean(solo_rews)) - v54_solo_mean,
            "COMP_MARGIN_MEAN": float(np.mean(comp_margins)),
            "COMP_MARGIN_MEDIAN": float(np.median(comp_margins)),
            "CI_95_LOW": ci_low,
            "CI_95_HIGH": ci_high,
            "WIN_RATE": sum(1 for m in comp_margins if m > 0) / len(comp_margins),
            "CLASSIFICATION": "CAUSAL IMPROVEMENT" if ci_low > 200 else ("NEUTRAL / MINOR" if ci_high >= 0 else "NEGATIVE")
        })

    print("\n" + "=" * 105)
    print("SECTION 6: MACRO INTERVENTION ABLATIONS SUMMARY (20 COMMON SEEDS)")
    print("=" * 105)
    print(f"{'Variant':<48} | {'Solo Delta':<12} | {'Comp Margin':<14} | {'95% CI':<24} | {'Classification'}")
    print("-" * 125)
    for r in summary_rows:
        print(f"{r['MECHANISM']:<48} | ${r['SOLO_DELTA_VS_V54']:>+10,.0f} | ${r['COMP_MARGIN_MEAN']:>+12,.0f} | [${r['CI_95_LOW']:>+8,.0f}, ${r['CI_95_HIGH']:>+8,.0f}] | {r['CLASSIFICATION']}")

    os.makedirs("research", exist_ok=True)
    with open("research/v54_v66_causal_ablations.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)
    print("\nSaved research/v54_v66_causal_ablations.csv")

    with open("research/v54_v66_causal_ablations.md", "w", encoding="utf-8") as f:
        f.write("# Macro Intervention Ablations Report (Section 6)\n\n")
        f.write("Evaluates V54-derived variants isolating each macro difference from V66.\n")
        f.write("Evaluated across 20 common seeds (101-120) with symmetric seats vs IDLE (solo) and vs canonical V54.\n\n")
        f.write("| Variant | Mechanism | Solo Delta vs V54 | Competitive Margin vs V54 | 95% Bootstrap CI | Win Rate | Classification |\n")
        f.write("| :--- | :--- | :---: | :---: | :---: | :---: | :--- |\n")
        for r in summary_rows:
            f.write(f"| **{r['VARIANT']}** | {r['MECHANISM']} | ${r['SOLO_DELTA_VS_V54']:+,.0f} | ${r['COMP_MARGIN_MEAN']:+,.0f} | [${r['CI_95_LOW']:+,.0f}, ${r['CI_95_HIGH']:+,.0f}] | {r['WIN_RATE']*100:.1f}% | **{r['CLASSIFICATION']}** |\n")

    print("Saved research/v54_v66_causal_ablations.md")

if __name__ == "__main__":
    main()
