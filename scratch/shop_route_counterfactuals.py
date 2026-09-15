"""
scratch/shop_route_counterfactuals.py
=====================================
Sections 5, 6, 7, 8, 9, 10, 11:
Causal Route Ablations, Exact Seed Counterfactuals, and Micro-Forensics.

1. Build pure shop route variants on top of V54+ baseline:
   - Arm A: Always Backbone (V54+)
   - Arm B: Always Yarn Route
   - Arm C: Always Bakery/Yarn Route
   - Arm D: Shop-State Selected Route (Public state only)
   - Arm E: Canonical V66 Shop-Route Selection
   - Arm F: Random Shop Route (Causal Control)
2. Run Key Causal Ablation across 50 fresh symmetric seeds (601–650 x 2 seats = 100 matches)
   against V54 and V66.
3. Run Exact Counterfactual Replays on the >$10k seeds (204, 206, 208, 405, 479, etc.)
4. Isolate the $26k–$27k examples (Seeds 204 and 208) with full commodity/accounting bridge.
5. Instrument downstream state divergence and shop stability.
6. Saves: research/shop_route_counterfactuals.csv
"""

import os
import sys
import copy
import time
import json
import csv
import random
import numpy as np
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
import importlib.util
from pathlib import Path
from kaggle_environments import make

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
V54_PATH = os.path.join(BASE_DIR, "external_repos", "lixingtao123-Kaggriculture", "variant_v54_h3q4", "main.py")
V62_PATH = os.path.join(BASE_DIR, "external_repos", "kaggriculture-v66-agent", "candidate_v62_composite_bakery_yarn.py")
V66_PATH = os.path.join(BASE_DIR, "external_repos", "kaggriculture-v66-agent", "main.py")
V66_META_PATH = os.path.join(BASE_DIR, "external_repos", "kaggriculture-v66-agent", "candidate_v66_meta_closed_loop.py")
V54PLUS_PATH = os.path.join(BASE_DIR, "candidates", "v54_plus_macro.py")

for p in [V54_PATH, V62_PATH, V66_PATH, V66_META_PATH, V54PLUS_PATH]:
    d = os.path.dirname(p)
    if d not in sys.path:
        sys.path.insert(0, d)

# Lazy agent module loading helper
_MODULES = {}

def get_modules():
    if "loaded" not in _MODULES:
        spec_v54 = importlib.util.spec_from_file_location("v54_m", V54_PATH)
        mod_v54 = importlib.util.module_from_spec(spec_v54)
        spec_v54.loader.exec_module(mod_v54)

        spec_v62 = importlib.util.spec_from_file_location("v62_m", V62_PATH)
        mod_v62 = importlib.util.module_from_spec(spec_v62)
        spec_v62.loader.exec_module(mod_v62)

        spec_v66 = importlib.util.spec_from_file_location("v66_m", V66_PATH)
        mod_v66 = importlib.util.module_from_spec(spec_v66)
        spec_v66.loader.exec_module(mod_v66)

        spec_v66_meta = importlib.util.spec_from_file_location("v66_meta_m", V66_META_PATH)
        mod_v66_meta = importlib.util.module_from_spec(spec_v66_meta)
        spec_v66_meta.loader.exec_module(mod_v66_meta)

        spec_v54plus = importlib.util.spec_from_file_location("v54plus_m", V54PLUS_PATH)
        mod_v54plus = importlib.util.module_from_spec(spec_v54plus)
        spec_v54plus.loader.exec_module(mod_v54plus)

        _MODULES["v54"] = getattr(mod_v54, "agent", getattr(mod_v54, "kaggle_agent", None))
        _MODULES["v62_mod"] = mod_v62
        _MODULES["v54_mod"] = mod_v54
        _MODULES["v66"] = getattr(mod_v66, "agent", getattr(mod_v66, "kaggle_agent", None))
        _MODULES["v66_meta"] = mod_v66_meta
        _MODULES["v54plus"] = getattr(mod_v54plus, "agent", getattr(mod_v54plus, "kaggle_agent", None))
        _MODULES["loaded"] = True
    return _MODULES

def build_pure_variant_agent(mode="backbone", seed_rng=42):
    """
    Constructs a research variant on top of V54+ / V56-backbone that differs
    ONLY in the route selected after shop unlock.
    """
    mods = get_modules()
    mod_v54 = mods["v54_mod"]
    mod_v62 = mods["v62_mod"]
    mod_meta = mods["v66_meta"]

    config = copy.deepcopy(mod_v62._V54_CONFIG)
    
    # Pre-build base candidate policies
    policy_backbone = mod_v54._v51_build_policy(mod_v62._V56_BACKBONE_ROUTE, config)
    policy_yarn = mod_v54._v51_build_policy(mod_v62._V56_YARN_ROUTE, config)
    policy_bakery = mod_v54._v51_build_policy(mod_v62._V58_BAKERY_YARN_ROUTE, config)

    # Overlays identical to V54+
    _v60_seed_trim = mod_v62._v60_seed_trim
    _v60_shed_guard = mod_v62._v60_shed_guard
    _route_loaded_units = mod_meta._route_loaded_units
    _TERMINAL_UNITS = mod_meta._TERMINAL_UNITS
    _TERMINAL_MARKET = mod_meta._TERMINAL_MARKET

    state = {"route": "backbone", "history": []}
    rng = random.Random(seed_rng)

    def variant_agent(obs, configuration=None):
        step = obs.get("step")
        if step is None:
            step = 24 * int(obs.get("day", 0) or 0) + int(obs.get("hour", 0) or 0)
        else:
            step = int(step)

        if step == 0:
            state["route"] = "backbone"
            state["history"] = []

        visible = mod_v62._v56_visible_configuration(configuration)
        
        # Advance active policy
        shops = list((obs.get("town", {}) or {}).get("unlocked_shops", []) or [])

        # Route Selection Logic
        if mode == "always_backbone":
            chosen = "backbone"
        elif mode == "always_yarn":
            chosen = "yarn"
        elif mode == "always_bakery":
            chosen = "bakery"
        elif mode == "shop_only_reactive":
            # Pure public shop state controller
            first = shops[0] if len(shops) >= 1 else ""
            second = shops[1] if len(shops) >= 2 else ""
            if "YARN_STORE" in shops:
                if first == "BAKERY" and second == "YARN_STORE":
                    chosen = "bakery"
                else:
                    chosen = "yarn"
            elif first == "BAKERY":
                chosen = "bakery"
            else:
                chosen = "backbone"
        elif mode == "yarn_when_unlocked":
            chosen = "yarn" if "YARN_STORE" in shops else "backbone"
        elif mode == "bakery_when_unlocked":
            chosen = "bakery" if "BAKERY" in shops else "backbone"
        elif mode == "random_control":
            if step in (72, 144):
                chosen = rng.choice(["backbone", "yarn", "bakery"])
            else:
                chosen = state["route"]
        elif mode == "canonical_v66_route_selection":
            # Uses exact V66 route selection without opponent classifier
            # If step 72/144 has YARN_STORE or BAKERY/YARN
            first = shops[0] if len(shops) >= 1 else ""
            second = shops[1] if len(shops) >= 2 else ""
            if first == "YARN_STORE" or second == "YARN_STORE":
                chosen = "yarn"
            elif first == "BAKERY" and second == "YARN_STORE":
                chosen = "bakery"
            else:
                chosen = "backbone"
        else:
            chosen = "backbone"

        state["route"] = chosen

        # Execute chosen policy
        if chosen == "yarn":
            action = policy_yarn(obs, visible)
        elif chosen == "bakery":
            action = policy_bakery(obs, visible)
        else:
            action = policy_backbone(obs, visible)

        # Apply standard V54+ verified overlays
        action = _v60_seed_trim(obs, action, step)
        capacity = int((configuration or {}).get("shedCapacity", 100)) or 100
        action = _v60_shed_guard(obs, action, capacity)

        if 713 <= step <= 716:
            action = _route_loaded_units(obs, action, step)
        if step in (717, 718):
            action = _TERMINAL_UNITS(obs, action, step)
        if step == 718:
            action = _TERMINAL_MARKET(obs, action, rule="collision", replace=True)

        return action

    return variant_agent

def bootstrap_ci(arr, num_samples=10000, alpha=0.05):
    a = np.array(arr)
    n = len(a)
    np.random.seed(42)
    boot = [np.mean(np.random.choice(a, size=n, replace=True)) for _ in range(num_samples)]
    return float(np.percentile(boot, 100 * (alpha / 2))), float(np.percentile(boot, 100 * (1 - alpha / 2)))

def run_match(task):
    seed, agent_name_0, agent_name_1, mode0, mode1 = task
    mods = get_modules()

    def make_fn(name, mode, seed_val):
        if name == "V54":
            return mods["v54"]
        elif name == "V66":
            return mods["v66"]
        elif name == "V54+":
            return mods["v54plus"]
        elif name == "IDLE":
            return lambda obs, conf=None: {"farmer": ["PASS"], "hands": [], "market": []}
        elif name.startswith("VARIANT_"):
            return build_pure_variant_agent(mode, seed_val)
        else:
            return mods["v54plus"]

    fn0 = make_fn(agent_name_0, mode0, seed)
    fn1 = make_fn(agent_name_1, mode1, seed)

    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    env.reset()

    telemetry = {
        "step72_shops": [],
        "step144_shops": [],
        "sales": defaultdict(float),
        "production": defaultdict(float),
    }

    for s in range(719):
        o0, o1 = env.state[0].observation, env.state[1].observation
        o0["step"], o1["step"] = s, s

        if s == 72:
            telemetry["step72_shops"] = list((o0.get("town") or {}).get("unlocked_shops") or [])
        elif s == 144:
            telemetry["step144_shops"] = list((o0.get("town") or {}).get("unlocked_shops") or [])

        a0 = fn0(o0, env.configuration)
        a1 = fn1(o1, env.configuration)
        env.step([a0, a1])

    r0 = float(env.steps[-1][0].reward or 0.0)
    r1 = float(env.steps[-1][1].reward or 0.0)

    return {
        "seed": seed,
        "a0": agent_name_0,
        "a1": agent_name_1,
        "r0": r0,
        "r1": r1,
        "delta": r0 - r1,
        "telemetry": telemetry
    }

def main():
    print("=" * 80)
    print("PHASE 4: CAUSAL ROUTE ABLATIONS & COUNTERFACTUAL ANALYSIS")
    print("=" * 80, flush=True)

    # 1. Section 8: Exact Route Counterfactual on High-Margin Seeds
    # Target seeds: 204, 206, 208, 405, 450, 471, 479, 485, 486, 515, 521, 539, 551
    HIGH_MARGIN_SEEDS = [204, 206, 208, 405, 450, 471, 479, 485, 486, 515, 521, 539, 551]
    counterfactual_tasks = []

    variant_modes = [
        ("CANONICAL_V66", "V66", ""),
        ("FORCED_BACKBONE", "VARIANT_BACKBONE", "always_backbone"),
        ("FORCED_YARN", "VARIANT_YARN", "always_yarn"),
        ("FORCED_BAKERY", "VARIANT_BAKERY", "always_bakery"),
        ("SHOP_STATE_SELECTED", "VARIANT_SHOP_STATE", "shop_only_reactive"),
    ]

    for seed in HIGH_MARGIN_SEEDS:
        for arm_name, agent_type, mode_str in variant_modes:
            counterfactual_tasks.append((seed, agent_type, "V54", mode_str, ""))

    print(f"\nRunning {len(counterfactual_tasks)} counterfactual replays on {len(HIGH_MARGIN_SEEDS)} large-delta seeds...")
    t0 = time.time()
    cf_results = []
    with ProcessPoolExecutor(max_workers=10) as pool:
        for res in pool.map(run_match, counterfactual_tasks):
            cf_results.append(res)

    print(f"Counterfactual runs finished in {time.time() - t0:.1f}s.")

    # Aggregate Counterfactual Results by Seed and Arm
    seed_arm_rewards = defaultdict(dict)
    for res in cf_results:
        seed = res["seed"]
        a0 = res["a0"]
        seed_arm_rewards[seed][a0] = res["r0"]
        seed_arm_rewards[seed]["V54_opp"] = res["r1"]
        seed_arm_rewards[seed]["shops"] = res["telemetry"]["step144_shops"]

    print("\n" + "=" * 105)
    print("EXACT ROUTE COUNTERFACTUAL MATRIX ON LARGE-DELTA SEEDS (vs V54)")
    print("=" * 105)
    print(f"{'Seed':<6} | {'Step 144 Shops':<32} | {'V54 Opp':<10} | {'V66 Canon':<11} | {'Backbone':<10} | {'Yarn':<10} | {'Bakery':<10} | {'Shop-State':<10}")
    print("-" * 105)
    for seed in HIGH_MARGIN_SEEDS:
        d = seed_arm_rewards[seed]
        shops_str = str(d.get("shops", []))
        v54_r = d.get("V54_opp", 0)
        v66_r = d.get("V66", 0)
        bb_r = d.get("VARIANT_BACKBONE", 0)
        yarn_r = d.get("VARIANT_YARN", 0)
        bakery_r = d.get("VARIANT_BAKERY", 0)
        shop_r = d.get("VARIANT_SHOP_STATE", 0)
        print(f"{seed:<6} | {shops_str:<32} | ${v54_r:<9,.0f} | ${v66_r:<10,.0f} | ${bb_r:<9,.0f} | ${yarn_r:<9,.0f} | ${bakery_r:<9,.0f} | ${shop_r:<9,.0f}")

    # 2. Section 6 & 7: The Key Causal Ablation across 50 Fresh Seeds (601–650)
    # 50 seeds x 2 seats = 100 matches per variant vs V54 and vs V66
    ABLATION_SEEDS = list(range(601, 651))
    ablation_arms = [
        ("Baseline (V54+)", "V54+", ""),
        ("Variant 1 (Yarn when YARN unlocked)", "VARIANT_V1", "yarn_when_unlocked"),
        ("Variant 2 (Bakery when BAKERY unlocked)", "VARIANT_V2", "bakery_when_unlocked"),
        ("Variant 3 (Shop-State Only Reactive)", "VARIANT_V3", "shop_only_reactive"),
        ("Variant 4 (Canonical V66 Route Selector)", "VARIANT_V4", "canonical_v66_route_selection"),
        ("Control (Random Shop Route Assignment)", "VARIANT_RND", "random_control"),
    ]

    print("\n" + "=" * 80)
    print("SECTION 6 & 7: 50-SEED CAUSAL ABLATION MATRIX (100 MATCHES PER ARM)")
    print("=" * 80, flush=True)

    ablation_results = []
    ablation_tasks = []
    for arm_label, agent_type, mode_str in ablation_arms:
        for opp in ["V54", "V66"]:
            for seed in ABLATION_SEEDS:
                ablation_tasks.append((seed, agent_type, opp, mode_str, ""))
                ablation_tasks.append((seed, opp, agent_type, "", mode_str))

    print(f"Executing {len(ablation_tasks)} symmetric evaluation matches...")
    t1 = time.time()
    with ProcessPoolExecutor(max_workers=10) as pool:
        for res in pool.map(run_match, ablation_tasks):
            ablation_results.append(res)
            if len(ablation_results) % 100 == 0 or len(ablation_results) == len(ablation_tasks):
                print(f"  {len(ablation_results)}/{len(ablation_tasks)} done ({time.time() - t1:.1f}s)", flush=True)

    # Analyze Section 6 & 7 Results
    ablation_summary = []
    for arm_label, agent_type, mode_str in ablation_arms:
        for opp in ["V54", "V66"]:
            deltas = []
            r0_list = []
            r1_list = []
            wins = ties = losses = 0

            for m in ablation_results:
                if m["a0"] == agent_type and m["a1"] == opp:
                    diff = m["r0"] - m["r1"]
                    deltas.append(diff)
                    r0_list.append(m["r0"])
                    r1_list.append(m["r1"])
                elif m["a1"] == agent_type and m["a0"] == opp:
                    diff = m["r1"] - m["r0"]
                    deltas.append(diff)
                    r0_list.append(m["r1"])
                    r1_list.append(m["r0"])
                else:
                    continue

                if diff > 0.01:
                    wins += 1
                elif diff < -0.01:
                    losses += 1
                else:
                    ties += 1

            mean_d = float(np.mean(deltas))
            med_d = float(np.median(deltas))
            std_d = float(np.std(deltas))
            ci_l, ci_h = bootstrap_ci(deltas)
            win_rate = (wins + 0.5 * ties) / len(deltas) * 100

            ablation_summary.append({
                "arm": arm_label,
                "opponent": opp,
                "agent_mean": float(np.mean(r0_list)),
                "opp_mean": float(np.mean(r1_list)),
                "mean_delta": mean_d,
                "median_delta": med_d,
                "std_delta": std_d,
                "ci_low": ci_l,
                "ci_high": ci_h,
                "wins": wins,
                "ties": ties,
                "losses": losses,
                "win_rate": win_rate,
                "n_games": len(deltas)
            })

    print("\n" + "=" * 125)
    print("CAUSAL ABLATION BENCHMARK RESULTS (50 FRESH SEEDS 601–650, SYMMETRIC SEATS)")
    print("=" * 125)
    print(f"{'Variant Arm':<40} | {'Opp':<5} | {'Agent Mean':<10} | {'Opp Mean':<10} | {'Margin':<12} | {'Median':<10} | {'95% CI':<20} | {'W/T/L':<10} | {'Win %'}")
    print("-" * 125)
    for row in ablation_summary:
        ci_str = f"[${row['ci_low']:+,.0f}, ${row['ci_high']:+,.0f}]"
        wtl = f"{row['wins']}/{row['ties']}/{row['losses']}"
        print(f"{row['arm']:<40} | {row['opponent']:<5} | ${row['agent_mean']:<9,.0f} | ${row['opp_mean']:<9,.0f} | ${row['mean_delta']:>+10,.0f} | ${row['median_delta']:>+8,.0f} | {ci_str:<20} | {wtl:<10} | {row['win_rate']:>5.1f}%")

    # 3. Section 11: Shop-Stability Test across Opponent Classes
    # Test Arm D (Shop-State Selected) vs IDLE, V54, V56-Backbone, V66
    print("\n" + "=" * 80)
    print("SECTION 11: SHOP-STABILITY TEST (SHOP-STATE SELECTED vs OPPONENT POOL)")
    print("=" * 80)
    stability_tasks = []
    test_opps = ["IDLE", "V54", "VARIANT_BACKBONE", "V66"]
    for opp in test_opps:
        for seed in ABLATION_SEEDS[:25]:  # 25 seeds x 2 seats = 50 matches
            stability_tasks.append((seed, "VARIANT_SHOP_STATE", opp, "shop_only_reactive", "always_backbone" if opp == "VARIANT_BACKBONE" else ""))
            stability_tasks.append((seed, opp, "VARIANT_SHOP_STATE", "always_backbone" if opp == "VARIANT_BACKBONE" else "", "shop_only_reactive"))

    stability_results = []
    with ProcessPoolExecutor(max_workers=10) as pool:
        for res in pool.map(run_match, stability_tasks):
            stability_results.append(res)

    for opp in test_opps:
        deltas = [m["r0"] - m["r1"] if m["a0"] == "VARIANT_SHOP_STATE" else m["r1"] - m["r0"] for m in stability_results if opp in (m["a0"], m["a1"])]
        r_agent = [m["r0"] if m["a0"] == "VARIANT_SHOP_STATE" else m["r1"] for m in stability_results if opp in (m["a0"], m["a1"])]
        ci_l, ci_h = bootstrap_ci(deltas)
        print(f"  Shop-State Selected vs {opp:<16}: Mean Margin ${np.mean(deltas):>+9,.0f} | 95% CI [${ci_l:+,.0f}, ${ci_h:+,.0f}] | Agent Score: ${np.mean(r_agent):,.0f}")

    # Save to research/shop_route_counterfactuals.csv
    csv_path = "research/shop_route_counterfactuals.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "arm", "opponent", "agent_mean", "opp_mean", "mean_delta",
            "median_delta", "std_delta", "ci_low", "ci_high",
            "wins", "ties", "losses", "win_rate", "n_games"
        ])
        writer.writeheader()
        writer.writerows(ablation_summary)
    print(f"\nSaved results to {csv_path}")

if __name__ == "__main__":
    main()
