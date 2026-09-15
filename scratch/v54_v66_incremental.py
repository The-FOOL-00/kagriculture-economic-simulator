"""
Step 7: Full Incremental Reconstruction Engine
==============================================
Evaluates sequential incremental stages from V54 to V66:
  R0: Canonical V54 Baseline
  R1: R0 + V56 Backbone Route (e103819410-islet-full)
  R2: R1 + V66 Active Residual Config (front_on_near=True, deficit thresholds 4.5k/4k, batch=8)
  R3: R2 + V60 Overlays (_v60_seed_trim + _v60_shed_guard)
  R4: R3 + V66 Terminal Realization (_route_loaded_units + terminal market) -> Complete V66

Evaluates across 20 common seeds (101-120) with symmetric seats (40 matches per stage):
  - Solo Reward (vs IDLE)
  - Competitive Margin vs V54 (with 95% CI and Win Rate)
  - Competitive Margin vs V66 (with 95% CI and Win Rate)

Outputs:
  research/v54_v66_incremental_reconstruction.csv
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
    spec54 = importlib.util.spec_from_file_location("v54_inc", V54_PATH)
    mod54 = importlib.util.module_from_spec(spec54)
    spec54.loader.exec_module(mod54)

    d = os.path.dirname(V62_PATH)
    if d not in sys.path: sys.path.insert(0, d)
    spec62 = importlib.util.spec_from_file_location("v62_inc", V62_PATH)
    mod62 = importlib.util.module_from_spec(spec62)
    spec62.loader.exec_module(mod62)

    spec66 = importlib.util.spec_from_file_location("v66_inc", V66_PATH)
    mod66 = importlib.util.module_from_spec(spec66)
    spec66.loader.exec_module(mod66)

    return mod54, mod62, mod66

def idle_agent(obs, configuration=None):
    return {"farmer": ["PASS"], "hands": [], "market": []}

def build_stage_agent(stage_id, mod54, mod62, mod66):
    if stage_id == "R0":
        return mod54.agent

    r54 = copy.deepcopy(mod54._V54_ROUTE)
    r66 = copy.deepcopy(mod62._V56_BACKBONE_ROUTE)
    cfg54 = copy.deepcopy(mod54._V54_CONFIG)
    cfg66 = copy.deepcopy(mod62._V54_CONFIG)

    v60_seed_trim = mod62._v60_seed_trim
    v60_shed_guard = mod62._v60_shed_guard
    route_loaded_units = mod66._route_loaded_units
    terminal_market = mod66._TERMINAL_MARKET

    # Select route
    # R1, R2, R3, R4 use r66 (V56 Backbone Route)
    route = r66

    # Select config
    # R1 uses cfg54 (passive deficit 1M)
    # R2, R3, R4 use cfg66 (active deficit 4.5k/4k)
    config = cfg54 if stage_id == "R1" else cfg66

    raw_policy = mod54._v51_build_policy(route, config)

    def agent(obs, configuration=None):
        step = int((obs or {}).get("step", 0) or 0)
        action = raw_policy(obs, configuration)

        if stage_id in ["R3", "R4"]:
            # R3/R4 apply seed trim and shed guard
            action = v60_seed_trim(obs, action, step)
            cap = int((configuration or {}).get("shedCapacity", 100)) or 100
            action = v60_shed_guard(obs, action, cap)

        if stage_id == "R4":
            # R4 applies terminal loaded return & terminal market
            if 713 <= step <= 716:
                action = route_loaded_units(obs, action, step)
            if step in (717, 718):
                action = mod66._TERMINAL_UNITS(obs, action, step)
            if step == 718:
                action = terminal_market(obs, action, rule="collision", replace=True)

        return action

    return agent

def run_stage_match_pair(task):
    seed, stage_id, opp_id = task
    mod54, mod62, mod66 = load_base_modules()

    agent_var = build_stage_agent(stage_id, mod54, mod62, mod66)
    
    if opp_id == "IDLE":
        agent_opp = idle_agent
    elif opp_id == "V54":
        agent_opp = mod54.agent
    elif opp_id == "V66":
        agent_opp = mod66.agent

    rewards_var = []
    rewards_opp = []

    # Seat 0
    env0 = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env0.reset()
    for s in range(719):
        o0, o1 = env0.state[0].observation, env0.state[1].observation
        o0["step"], o1["step"] = s, s
        a0 = agent_var(o0, env0.configuration)
        a1 = agent_opp(o1, env0.configuration)
        env0.step([a0, a1])
    rewards_var.append(float(env0.steps[-1][0].reward or 0.0))
    rewards_opp.append(float(env0.steps[-1][1].reward or 0.0))

    # Seat 1
    env1 = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env1.reset()
    for s in range(719):
        o0, o1 = env1.state[0].observation, env1.state[1].observation
        o0["step"], o1["step"] = s, s
        a0 = agent_opp(o0, env1.configuration)
        a1 = agent_var(o1, env1.configuration)
        env1.step([a0, a1])
    rewards_opp.append(float(env1.steps[-1][0].reward or 0.0))
    rewards_var.append(float(env1.steps[-1][1].reward or 0.0))

    return {
        "seed": seed,
        "stage_id": stage_id,
        "opp_id": opp_id,
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
    print("STEP 7: FULL INCREMENTAL RECONSTRUCTION (R0 -> R4)")
    print("Evaluating R0 to R4 across 20 Common Seeds (101-120) with symmetric seats")
    print("=" * 80, flush=True)

    stages = ["R0", "R1", "R2", "R3", "R4"]
    opps = ["IDLE", "V54", "V66"]

    tasks = []
    for st in stages:
        for opp in opps:
            for s in SEEDS:
                tasks.append((s, st, opp))

    t0 = time.time()
    results = defaultdict(list)
    with ProcessPoolExecutor(max_workers=8) as pool:
        for res in pool.map(run_stage_match_pair, tasks):
            key = (res["stage_id"], res["opp_id"])
            results[key].append(res)
            print(f"[{res['stage_id']} vs {res['opp_id']}] Seed {res['seed']} | Var: ${res['mean_var_reward']:,.0f} | Opp: ${res['mean_opp_reward']:,.0f} | Margin: {res['margin']:+,.0f}", flush=True)

    elapsed = time.time() - t0
    print(f"\nAll incremental simulations completed in {elapsed:.1f}s.")

    summary_records = []
    stage_names = {
        "R0": "R0: Canonical V54 Baseline",
        "R1": "R1: R0 + V56 Backbone Route (e103819410)",
        "R2": "R2: R1 + V66 Active Residual Config (4.5k/4k deficit)",
        "R3": "R3: R2 + V60 Overlays (Seed Trim + Shed Guard)",
        "R4": "R4: R3 + V66 Terminal Realization (Loaded Return + Final Market)"
    }

    for st in stages:
        solo_res = results[(st, "IDLE")]
        v54_res = results[(st, "V54")]
        v66_res = results[(st, "V66")]

        solo_mean = float(np.mean([r["mean_var_reward"] for r in solo_res]))

        # vs V54
        v54_margins = [r["margin"] for r in v54_res]
        ci_v54_low, ci_v54_high = bootstrap_ci(v54_margins)
        wr_v54 = sum(1 for m in v54_margins if m > 0) / len(v54_margins)

        # vs V66
        v66_margins = [r["margin"] for r in v66_res]
        ci_v66_low, ci_v66_high = bootstrap_ci(v66_margins)
        wr_v66 = sum(1 for m in v66_margins if m > 0) / len(v66_margins)

        summary_records.append({
            "STAGE": st,
            "DESCRIPTION": stage_names[st],
            "SOLO_REWARD": solo_mean,
            "MARGIN_VS_V54": float(np.mean(v54_margins)),
            "CI_V54_95": f"[${ci_v54_low:+,.0f}, ${ci_v54_high:+,.0f}]",
            "WR_VS_V54": f"{wr_v54*100:.1f}%",
            "MARGIN_VS_V66": float(np.mean(v66_margins)),
            "CI_V66_95": f"[${ci_v66_low:+,.0f}, ${ci_v66_high:+,.0f}]",
            "WR_VS_V66": f"{wr_v66*100:.1f}%"
        })

    print("\n" + "=" * 115)
    print("INCREMENTAL RECONSTRUCTION PROGRESSION (20 COMMON SEEDS, SYMMETRIC SEATS)")
    print("=" * 115)
    print(f"{'Stage':<6} | {'Description':<40} | {'Solo Rew':<10} | {'vs V54 Margin':<14} | {'95% CI vs V54':<20} | {'vs V66 Margin':<14} | {'95% CI vs V66'}")
    print("-" * 135)
    for r in summary_records:
        print(f"{r['STAGE']:<6} | {r['DESCRIPTION']:<40} | ${r['SOLO_REWARD']:<9,.0f} | ${r['MARGIN_VS_V54']:>+12,.0f} | {r['CI_V54_95']:<20} | ${r['MARGIN_VS_V66']:>+12,.0f} | {r['CI_V66_95']}")

    os.makedirs("research", exist_ok=True)
    with open("research/v54_v66_incremental_reconstruction.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_records[0].keys()))
        writer.writeheader()
        writer.writerows(summary_records)
    print("\nSaved research/v54_v66_incremental_reconstruction.csv")

if __name__ == "__main__":
    main()
