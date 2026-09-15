"""
scratch/shop_controller_ablation.py
===================================
Sections 12 & 13: Minimum Sufficient Shop Controller & Public State Test.

Compares Models / Candidate Rule Sets:
S1 (Model A): shop-only (obs['town']['unlocked_shops'])
S2: shop + step/day
S3 (Model B): shop + own cash
S4: shop + market inventory (wheat/wool inventory)
S5 (Model C): shop + own cash + market inventory
S6 (Model D): full state predicate (Canonical V66 opponent fingerprint)

Measures:
1. Agreement % with Canonical V66 route selection across 100 seeds.
2. Paired performance margin vs V54 and vs V66 (mean, median, SD, 95% CI).
3. Code complexity / minimality (number of state variables required).
4. Saves to research/shop_controller_minimality.csv.
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
import importlib.util
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

_LOADED = {}

def load_environment_modules():
    if "done" not in _LOADED:
        spec_v54 = importlib.util.spec_from_file_location("v54_ctl", V54_PATH)
        mod_v54 = importlib.util.module_from_spec(spec_v54)
        spec_v54.loader.exec_module(mod_v54)

        spec_v62 = importlib.util.spec_from_file_location("v62_ctl", V62_PATH)
        mod_v62 = importlib.util.module_from_spec(spec_v62)
        spec_v62.loader.exec_module(mod_v62)

        spec_v66 = importlib.util.spec_from_file_location("v66_ctl", V66_PATH)
        mod_v66 = importlib.util.module_from_spec(spec_v66)
        spec_v66.loader.exec_module(mod_v66)

        spec_v66_meta = importlib.util.spec_from_file_location("v66_meta_ctl", V66_META_PATH)
        mod_v66_meta = importlib.util.module_from_spec(spec_v66_meta)
        spec_v66_meta.loader.exec_module(mod_v66_meta)

        spec_v54plus = importlib.util.spec_from_file_location("v54plus_ctl", V54PLUS_PATH)
        mod_v54plus = importlib.util.module_from_spec(spec_v54plus)
        spec_v54plus.loader.exec_module(mod_v54plus)

        _LOADED["v54"] = getattr(mod_v54, "agent", getattr(mod_v54, "kaggle_agent", None))
        _LOADED["v62_mod"] = mod_v62
        _LOADED["v54_mod"] = mod_v54
        _LOADED["v66"] = getattr(mod_v66, "agent", getattr(mod_v66, "kaggle_agent", None))
        _LOADED["v66_meta"] = mod_v66_meta
        _LOADED["v54plus"] = getattr(mod_v54plus, "agent", getattr(mod_v54plus, "kaggle_agent", None))
        _LOADED["done"] = True
    return _LOADED

def make_controller_agent(rule_model="S1"):
    mods = load_environment_modules()
    mod_v54 = mods["v54_mod"]
    mod_v62 = mods["v62_mod"]
    mod_meta = mods["v66_meta"]

    config = copy.deepcopy(mod_v62._V54_CONFIG)
    policy_backbone = mod_v54._v51_build_policy(mod_v62._V56_BACKBONE_ROUTE, config)
    policy_yarn = mod_v54._v51_build_policy(mod_v62._V56_YARN_ROUTE, config)
    policy_bakery = mod_v54._v51_build_policy(mod_v62._V58_BAKERY_YARN_ROUTE, config)
    policy_ice = mod_v54._v51_build_policy(mod_v62._V58_ICE_MINIMAX_ROUTE, config)

    # Overlays
    _v60_seed_trim = mod_v62._v60_seed_trim
    _v60_shed_guard = mod_v62._v60_shed_guard
    _route_loaded_units = mod_meta._route_loaded_units
    _TERMINAL_UNITS = mod_meta._TERMINAL_UNITS
    _TERMINAL_MARKET = mod_meta._TERMINAL_MARKET

    state = {"route": "backbone"}

    def controller_agent(obs, configuration=None):
        step = obs.get("step")
        if step is None:
            step = 24 * int(obs.get("day", 0) or 0) + int(obs.get("hour", 0) or 0)
        else:
            step = int(step)

        if step == 0:
            state["route"] = "backbone"

        visible = mod_v62._v56_visible_configuration(configuration)
        town = obs.get("town", {}) or {}
        shops = list(town.get("unlocked_shops", []) or [])
        player = int(obs.get("player", 0) or 0)
        farms = list(obs.get("farms", []) or [])
        my_farm = farms[player] if player < len(farms) else {}
        opp_farm = farms[1 - player] if len(farms) >= 2 else {}
        my_money = float(my_farm.get("money", 0.0) or 0.0)
        market = obs.get("market", {}) or {}
        inv = market.get("inventory", {}) or {}

        first = shops[0] if len(shops) >= 1 else ""
        second = shops[1] if len(shops) >= 2 else ""

        # Model Rule Implementations
        if rule_model == "S1":
            # Model A: Pure public shop-only
            if "YARN_STORE" in shops:
                if first == "BAKERY" and second == "YARN_STORE":
                    chosen = "bakery"
                else:
                    chosen = "yarn"
            elif first == "BAKERY" and second == "YARN_STORE":
                chosen = "bakery"
            else:
                chosen = "backbone"

        elif rule_model == "S2":
            # S2: shop + step timing gating
            if step >= 72 and first == "YARN_STORE":
                chosen = "yarn"
            elif step >= 144 and second == "YARN_STORE":
                chosen = "yarn"
            elif step >= 144 and first == "BAKERY" and second == "YARN_STORE":
                chosen = "bakery"
            else:
                chosen = "backbone"

        elif rule_model == "S3":
            # Model B: shop + own money gating (must have >= 140 cash to support yarn transition)
            if "YARN_STORE" in shops and my_money >= 140.0:
                chosen = "yarn"
            elif first == "BAKERY" and second == "YARN_STORE":
                chosen = "bakery"
            else:
                chosen = "backbone"

        elif rule_model == "S4":
            # S4: shop + market inventory check (wool inventory must not be flooded > 10050)
            wool_inv = float(inv.get("WOOL", 10000.0) or 10000.0)
            if "YARN_STORE" in shops and wool_inv <= 10050.0:
                chosen = "yarn"
            elif first == "BAKERY" and second == "YARN_STORE":
                chosen = "bakery"
            else:
                chosen = "backbone"

        elif rule_model == "S5":
            # Model C: shop + own cash + market inventory
            wool_inv = float(inv.get("WOOL", 10000.0) or 10000.0)
            if "YARN_STORE" in shops and my_money >= 140.0 and wool_inv <= 10050.0:
                chosen = "yarn"
            elif first == "BAKERY" and second == "YARN_STORE":
                chosen = "bakery"
            else:
                chosen = "backbone"

        elif rule_model == "S6":
            # Model D: full state predicate (V66 exact classifier reproduction)
            # Reconstruct exact step-72/144 conditions
            if step >= 72:
                if first == "YARN_STORE":
                    chosen = "yarn"
                elif first == "FARMERS_MARKET" and second == "YARN_STORE":
                    chosen = "yarn"
                elif first == "BAKERY" and second == "YARN_STORE":
                    chosen = "bakery"
                else:
                    chosen = "backbone"
            else:
                chosen = "backbone"

        else:
            chosen = "backbone"

        state["route"] = chosen

        if chosen == "yarn":
            action = policy_yarn(obs, visible)
        elif chosen == "bakery":
            action = policy_bakery(obs, visible)
        elif chosen == "ice":
            action = policy_ice(obs, visible)
        else:
            action = policy_backbone(obs, visible)

        # Overlays
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

    return controller_agent

def bootstrap_ci(arr, num_samples=10000, alpha=0.05):
    a = np.array(arr)
    n = len(a)
    np.random.seed(42)
    boot = [np.mean(np.random.choice(a, size=n, replace=True)) for _ in range(num_samples)]
    return float(np.percentile(boot, 100 * (alpha / 2))), float(np.percentile(boot, 100 * (1 - alpha / 2)))

def evaluate_controller_task(task):
    seed, model_name, opp_name = task
    mods = load_environment_modules()
    
    agent_fn = make_controller_agent(model_name)
    opp_fn = mods["v54"] if opp_name == "V54" else mods["v66"]

    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    env.reset()

    for s in range(719):
        o0, o1 = env.state[0].observation, env.state[1].observation
        o0["step"], o1["step"] = s, s
        a0 = agent_fn(o0, env.configuration)
        a1 = opp_fn(o1, env.configuration)
        env.step([a0, a1])

    r0 = float(env.steps[-1][0].reward or 0.0)
    r1 = float(env.steps[-1][1].reward or 0.0)

    return {
        "seed": seed,
        "model": model_name,
        "opp": opp_name,
        "r_agent": r0,
        "r_opp": r1,
        "delta": r0 - r1
    }

def main():
    print("=" * 80)
    print("SECTIONS 12 & 13: MINIMUM SUFFICIENT SHOP CONTROLLER ABLATION")
    print("=" * 80, flush=True)

    MODELS = ["S1", "S2", "S3", "S4", "S5", "S6"]
    MODEL_DESCRIPTIONS = {
        "S1": "Shop-Only (Model A: unlocked_shops only)",
        "S2": "Shop + Timing (unlocked_shops + step>=72/144)",
        "S3": "Shop + Own Cash (Model B: shops + cash>=140)",
        "S4": "Shop + Market Inv (shops + wool_inv<=10050)",
        "S5": "Shop + Cash + Inv (Model C: shops + cash + inv)",
        "S6": "Full State Predicate (Model D: V66 exact match)",
    }
    EVAL_SEEDS = list(range(601, 651))  # 50 seeds x 2 opponents = 100 matches per model

    tasks = []
    for m in MODELS:
        for opp in ["V54", "V66"]:
            for s in EVAL_SEEDS:
                tasks.append((s, m, opp))

    print(f"Running {len(tasks)} matches across {len(MODELS)} controller models...")
    t0 = time.time()
    results = []
    with ProcessPoolExecutor(max_workers=10) as pool:
        for res in pool.map(evaluate_controller_task, tasks):
            results.append(res)
            if len(results) % 100 == 0 or len(results) == len(tasks):
                print(f"  {len(results)}/{len(tasks)} matches complete ({time.time() - t0:.1f}s)", flush=True)

    # Process and summarize results
    summary_rows = []
    for m in MODELS:
        for opp in ["V54", "V66"]:
            subset = [r for r in results if r["model"] == m and r["opp"] == opp]
            deltas = [r["delta"] for r in subset]
            agent_rewards = [r["r_agent"] for r in subset]
            opp_rewards = [r["r_opp"] for r in subset]
            wins = sum(1 for d in deltas if d > 0.01)
            ties = sum(1 for d in deltas if abs(d) <= 0.01)
            losses = sum(1 for d in deltas if d < -0.01)
            win_rate = (wins + 0.5 * ties) / len(deltas) * 100
            ci_low, ci_high = bootstrap_ci(deltas)

            summary_rows.append({
                "model": m,
                "description": MODEL_DESCRIPTIONS[m],
                "opponent": opp,
                "agent_mean": float(np.mean(agent_rewards)),
                "opp_mean": float(np.mean(opp_rewards)),
                "mean_delta": float(np.mean(deltas)),
                "median_delta": float(np.median(deltas)),
                "std_delta": float(np.std(deltas)),
                "ci_low": ci_low,
                "ci_high": ci_high,
                "wins": wins,
                "ties": ties,
                "losses": losses,
                "win_rate": win_rate,
                "num_matches": len(deltas)
            })

    print("\n" + "=" * 125)
    print("CONTROLLER MINIMALITY EVALUATION RESULTS")
    print("=" * 125)
    print(f"{'Model':<6} | {'Description':<35} | {'Opp':<5} | {'Agent Mean':<10} | {'Margin':<12} | {'Median':<10} | {'95% CI':<20} | {'W/T/L':<10} | {'Win %'}")
    print("-" * 125)
    for row in summary_rows:
        ci_str = f"[${row['ci_low']:+,.0f}, ${row['ci_high']:+,.0f}]"
        wtl = f"{row['wins']}/{row['ties']}/{row['losses']}"
        print(f"{row['model']:<6} | {row['description']:<35} | {row['opponent']:<5} | ${row['agent_mean']:<9,.0f} | ${row['mean_delta']:>+10,.0f} | ${row['median_delta']:>+8,.0f} | {ci_str:<20} | {wtl:<10} | {row['win_rate']:>5.1f}%")

    # Save to research/shop_controller_minimality.csv
    csv_path = "research/shop_controller_minimality.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "model", "description", "opponent", "agent_mean", "opp_mean",
            "mean_delta", "median_delta", "std_delta", "ci_low", "ci_high",
            "wins", "ties", "losses", "win_rate", "num_matches"
        ])
        writer.writeheader()
        writer.writerows(summary_rows)

    print(f"\nSaved minimality evaluation to {csv_path}")

if __name__ == "__main__":
    main()
