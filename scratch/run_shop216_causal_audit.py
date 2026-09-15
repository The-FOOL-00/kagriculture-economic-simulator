"""
scratch/run_shop216_causal_audit.py
===================================
Championship Experiment — Step-216 Third-Shop Causal Audit Engine.

Phases:
  1. Discovery Phase (500 seeds: 1001-1500):
     - Public town shop census at steps 72, 144, 216, 288.
     - Tracks shop combinations, third-shop identities, late yarn/smoothie/bakery.
     - V54++ vs V66 head-to-head match per seed.
     - Saved to research/shop216_census_results.json.
  2. Paired Counterfactuals on Target Seeds (S0 to S8):
     - S0: V54++ baseline
     - S1: Information Control
     - S2: Switch to Yarn if YARN_STORE at step 216
     - S3: Switch to Smoothie if SMOOTHIE_SHOP at step 216
     - S4: Switch to Bakery if BAKERY at step 216
     - S5: Explicit Public-State Selector
     - S6: Canonical V66 late-shop behavior
     - S7: Random late-shop route control
     - S8: Deliberately wrong late-shop route
     - Deep accounting & synchronization metrics recorded.
     - Saved to research/shop216_counterfactual_results.json.
  3. Untouched Holdout Evaluation (500 seeds: 1501-2000, 1000 symmetric matches):
     - Rigorous paired bootstrap CI and margin vs V66.
     - Saved to research/shop216_holdout_results.json.
  4. Solo Benchmark (25 seeds vs IDLE):
     - V66, V54++, V54+, V54.
     - Saved to research/shop216_solo_results.json.
  5. Master JSON synthesis -> research/shop216_causal_audit_results.json.
"""

from __future__ import annotations

import os
import sys
import copy
import time
import json
import random
import hashlib
from collections import defaultdict, Counter
from concurrent.futures import ProcessPoolExecutor
import importlib.util
import numpy as np

# Base Paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
V54_PATH = os.path.join(BASE_DIR, "external_repos", "lixingtao123-Kaggriculture", "variant_v54_h3q4", "main.py")
V66_PATH = os.path.join(BASE_DIR, "external_repos", "kaggriculture-v66-agent", "main.py")
V62_PATH = os.path.join(BASE_DIR, "external_repos", "kaggriculture-v66-agent", "candidate_v62_composite_bakery_yarn.py")
V66_META_PATH = os.path.join(BASE_DIR, "external_repos", "kaggriculture-v66-agent", "candidate_v66_meta_closed_loop.py")
V54_PLUS_PATH = os.path.join(BASE_DIR, "candidates", "v54_plus_macro.py")
V54_SHOP_PATH = os.path.join(BASE_DIR, "candidates", "v54_plus_shop.py")

for p in [V54_PATH, V66_PATH, V62_PATH, V66_META_PATH, V54_PLUS_PATH, V54_SHOP_PATH]:
    if not os.path.exists(p):
        raise FileNotFoundError(f"Missing required path: {p}")
    d = os.path.dirname(p)
    if d not in sys.path:
        sys.path.insert(0, d)

DISCOVERY_SEEDS = list(range(1001, 1501))  # 500 seeds
HOLDOUT_SEEDS = list(range(1501, 2001))    # 500 seeds
SOLO_SEEDS = list(range(1001, 1026))       # 25 seeds

def get_sha256(filepath: str) -> str:
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

_WORKER_MODULES = {}

def get_worker_modules():
    if not _WORKER_MODULES:
        s_v54 = importlib.util.spec_from_file_location("worker_v54", V54_PATH)
        m_v54 = importlib.util.module_from_spec(s_v54)
        s_v54.loader.exec_module(m_v54)

        s_v62 = importlib.util.spec_from_file_location("worker_v62", V62_PATH)
        m_v62 = importlib.util.module_from_spec(s_v62)
        s_v62.loader.exec_module(m_v62)

        s_v66 = importlib.util.spec_from_file_location("worker_v66", V66_PATH)
        m_v66 = importlib.util.module_from_spec(s_v66)
        s_v66.loader.exec_module(m_v66)

        s_meta = importlib.util.spec_from_file_location("worker_meta", V66_META_PATH)
        m_meta = importlib.util.module_from_spec(s_meta)
        s_meta.loader.exec_module(m_meta)

        s_plus = importlib.util.spec_from_file_location("worker_plus", V54_PLUS_PATH)
        m_plus = importlib.util.module_from_spec(s_plus)
        s_plus.loader.exec_module(m_plus)

        s_shop = importlib.util.spec_from_file_location("worker_shop", V54_SHOP_PATH)
        m_shop = importlib.util.module_from_spec(s_shop)
        s_shop.loader.exec_module(m_shop)

        config = copy.deepcopy(m_v62._V54_CONFIG)
        policies = {
            "backbone": m_v54._v51_build_policy(m_v62._V56_BACKBONE_ROUTE, config),
            "yarn": m_v54._v51_build_policy(m_v62._V56_YARN_ROUTE, config),
            "bakery": m_v54._v51_build_policy(m_v62._V58_BAKERY_YARN_ROUTE, config),
            "smoothie": m_v54._v51_build_policy(m_v62._V58_SMOOTHIE_ROUTE, config),
            "recovery": m_v54._v51_build_policy(m_v62._V58_RECOVERY_ROUTE, config),
            "ice": m_v54._v51_build_policy(m_v62._V58_ICE_MINIMAX_ROUTE, config),
            "pet": m_v54._v51_build_policy(m_v62._V57_PET_ROUTE, config),
            "clone": m_v54._v51_build_policy(m_v62._V58_CLONE_ROUTE, config),
        }

        _WORKER_MODULES["v54"] = m_v54
        _WORKER_MODULES["v62"] = m_v62
        _WORKER_MODULES["v66"] = m_v66
        _WORKER_MODULES["meta"] = m_meta
        _WORKER_MODULES["plus"] = m_plus
        _WORKER_MODULES["shop"] = m_shop
        _WORKER_MODULES["policies"] = policies

    return _WORKER_MODULES


def build_counterfactual_agent(arm_id: str, seed_salt: int = 0):
    mods = get_worker_modules()
    policies = mods["policies"]
    v62 = mods["v62"]
    v66_meta = mods["meta"]

    state_store = {0: {"route": "backbone", "last": -1, "rand_route": None},
                   1: {"route": "backbone", "last": -1, "rand_route": None}}

    def custom_agent(obs, configuration=None):
        step = obs.get("step")
        if step is None:
            step = 24 * int(obs.get("day", 0) or 0) + int(obs.get("hour", 0) or 0)
        else:
            step = int(step)

        seat = 1 if int(obs.get("player", 0) or 0) == 1 else 0
        st = state_store[seat]
        if step == 0 or step <= st["last"]:
            st["route"] = "backbone"
            st["last"] = step
            st["rand_route"] = None
        else:
            st["last"] = step

        visible = v62._v56_visible_configuration(configuration)
        town = obs.get("town", {}) or {}
        shops = list(town.get("unlocked_shops", []) or [])

        first = str(shops[0]) if len(shops) >= 1 else ""
        second = str(shops[1]) if len(shops) >= 2 else ""
        third = str(shops[2]) if len(shops) >= 3 else ""

        if step < 72:
            route = "backbone"
        elif step < 144:
            route = "yarn" if first == "YARN_STORE" else "backbone"
        else:
            if first == "YARN_STORE":
                route = "yarn"
            elif second == "YARN_STORE":
                route = "bakery" if first == "BAKERY" else "yarn"
            elif first == "BAKERY" and second == "YARN_STORE":
                route = "bakery"
            else:
                route = "backbone"

        if step >= 216 and arm_id != "S0":
            if arm_id == "S1":
                _ = third
            elif arm_id == "S2":
                if third == "YARN_STORE":
                    route = "yarn"
            elif arm_id == "S3":
                if third == "SMOOTHIE_SHOP":
                    route = "smoothie"
            elif arm_id == "S4":
                if third == "BAKERY":
                    route = "bakery"
            elif arm_id == "S5":
                if third == "YARN_STORE":
                    route = "yarn"
                elif third == "SMOOTHIE_SHOP":
                    route = "smoothie"
                elif third == "BAKERY":
                    route = "bakery"
                elif route == "yarn" and third == "PIZZA_SHOP":
                    route = "recovery"
            elif arm_id == "S6":
                pass
            elif arm_id == "S7":
                if st["rand_route"] is None:
                    rng = random.Random(seed_salt + 216)
                    st["rand_route"] = rng.choice(["backbone", "yarn", "bakery", "smoothie", "recovery"])
                route = st["rand_route"]
            elif arm_id == "S8":
                if third == "YARN_STORE":
                    route = "smoothie"
                elif third == "SMOOTHIE_SHOP":
                    route = "yarn"
                else:
                    route = "ice"

        st["route"] = route
        pol = policies.get(route, policies["backbone"])
        action = pol(obs, visible)

        action = v62._v60_seed_trim(obs, action, step)
        capacity = int((configuration or {}).get("shedCapacity", 100)) or 100
        action = v62._v60_shed_guard(obs, action, capacity)

        if 713 <= step <= 716:
            action = v66_meta._route_loaded_units(obs, action, step)
        if step in (717, 718):
            action = v66_meta._TERMINAL_UNITS(obs, action, step)
        if step == 718:
            action = v66_meta._TERMINAL_MARKET(obs, action, rule="collision", replace=True)

        return action

    return custom_agent


def evaluate_census_episode(seed: int):
    from kaggle_environments import make
    mods = get_worker_modules()
    fn_v66 = mods["v66"].agent
    fn_shop = mods["shop"].agent

    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    env.reset()

    snapshots = {}
    for s in range(719):
        o0, o1 = env.state[0].observation, env.state[1].observation
        o0["step"], o1["step"] = s, s

        if s in (72, 144, 216, 288):
            town = o0.get("town", {}) or {}
            unlocked = list(town.get("unlocked_shops", []) or [])
            snapshots[s] = {
                "unlocked_shops": unlocked,
                "shop_count": len(unlocked),
                "first": unlocked[0] if len(unlocked) >= 1 else None,
                "second": unlocked[1] if len(unlocked) >= 2 else None,
                "third": unlocked[2] if len(unlocked) >= 3 else None,
                "fourth": unlocked[3] if len(unlocked) >= 4 else None,
                "has_yarn": "YARN_STORE" in unlocked,
                "has_smoothie": "SMOOTHIE_SHOP" in unlocked,
                "has_bakery": "BAKERY" in unlocked,
                "has_pet": "PET_CAFE" in unlocked,
            }

        a0 = fn_shop(o0, env.configuration)
        a1 = fn_v66(o1, env.configuration)
        env.step([a0, a1])

    r0_v54pp = float(env.steps[-1][0].reward or 0.0)
    r1_v66 = float(env.steps[-1][1].reward or 0.0)
    margin = r0_v54pp - r1_v66

    first_shop = snapshots[72]["first"]
    second_shop = snapshots[144]["second"]
    third_shop = snapshots[216]["third"]

    if first_shop == "YARN_STORE" or second_shop == "YARN_STORE":
        if first_shop == "BAKERY" and second_shop == "YARN_STORE":
            v54pp_route = "bakery"
        else:
            v54pp_route = "yarn"
    else:
        v54pp_route = "backbone"

    return {
        "seed": seed,
        "snapshots": snapshots,
        "v54pp_reward": r0_v54pp,
        "v66_reward": r1_v66,
        "margin": margin,
        "v54pp_route": v54pp_route,
        "first_shop": first_shop,
        "second_shop": second_shop,
        "third_shop": third_shop,
    }


def evaluate_counterfactual_task(task):
    from kaggle_environments import make
    seed, arm_id = task
    mods = get_worker_modules()
    fn_v66 = mods["v66"].agent
    agent_arm = build_counterfactual_agent(arm_id, seed_salt=seed)

    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    env.reset()

    move_count = 0
    plant_count = 0
    harvest_count = 0
    animal_actions = 0
    water_count = 0
    pass_count = 0
    first_diff_step = None

    fn_ref = mods["shop"].agent

    for s in range(719):
        o0, o1 = env.state[0].observation, env.state[1].observation
        o0["step"], o1["step"] = s, s

        a0 = agent_arm(o0, env.configuration)
        a1 = fn_v66(o1, env.configuration)

        if first_diff_step is None and s >= 216:
            a_ref = fn_ref(o0, env.configuration)
            if a0 != a_ref:
                first_diff_step = s

        farmer_act = (a0.get("farmer") or ["PASS"])[0]
        if farmer_act in ("NORTH", "SOUTH", "EAST", "WEST"):
            move_count += 1
        elif farmer_act == "PLANT":
            plant_count += 1
        elif farmer_act == "HARVEST":
            harvest_count += 1
        elif farmer_act in ("FEED", "CARE", "SHEAR", "COLLECT_EGG", "COLLECT_MILK"):
            animal_actions += 1
        elif farmer_act == "WATER":
            water_count += 1
        elif farmer_act == "PASS":
            pass_count += 1

        for h in a0.get("hands", []):
            h_act = h[0] if h else "PASS"
            if h_act in ("NORTH", "SOUTH", "EAST", "WEST"):
                move_count += 1
            elif h_act == "PLANT":
                plant_count += 1
            elif h_act == "HARVEST":
                harvest_count += 1
            elif h_act in ("FEED", "CARE", "SHEAR", "COLLECT_EGG", "COLLECT_MILK"):
                animal_actions += 1
            elif h_act == "WATER":
                water_count += 1
            elif h_act == "PASS":
                pass_count += 1

        env.step([a0, a1])

    final_obs = env.steps[-1][0].observation
    final_reward = float(env.steps[-1][0].reward or 0.0)

    own_farm = final_obs.get("farms", [{}])[0]
    final_cash = float(own_farm.get("money", 0.0) or 0.0)
    shed = (final_obs.get("private", {}) or {}).get("shed", {}) or {}
    tiles = own_farm.get("tiles", []) or []

    cow_count = 0
    sheep_count = 0
    for row in tiles:
        for t in row:
            if isinstance(t, dict):
                anim = t.get("animal")
                if anim == "COW":
                    cow_count += 1
                elif anim == "SHEEP":
                    sheep_count += 1

    return {
        "seed": seed,
        "arm": arm_id,
        "reward": final_reward,
        "cash": final_cash,
        "first_diff_step": first_diff_step,
        "move_count": move_count,
        "productive_count": plant_count + harvest_count + animal_actions + water_count,
        "harvest_count": harvest_count,
        "animal_actions": animal_actions,
        "pass_count": pass_count,
        "cow_count": cow_count,
        "sheep_count": sheep_count,
        "shed_wool": shed.get("WOOL", 0),
        "shed_milk": shed.get("MILK", 0),
        "shed_wheat": shed.get("WHEAT", 0),
        "shed_strawberry": shed.get("STRAWBERRY", 0),
    }


def evaluate_solo_episode(task):
    seed, agent_name = task
    from kaggle_environments import make
    mods = get_worker_modules()
    if agent_name == "V66":
        fn = mods["v66"].agent
    elif agent_name == "V54++":
        fn = mods["shop"].agent
    elif agent_name == "V54+":
        fn = mods["plus"].agent
    elif agent_name == "V54":
        fn = mods["v54"].agent
    else:
        raise ValueError(f"Unknown agent {agent_name}")

    idle = lambda obs, c=None: {"farmer": ["PASS"], "hands": [], "market": []}

    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    env.reset()
    for s in range(719):
        o0, o1 = env.state[0].observation, env.state[1].observation
        o0["step"], o1["step"] = s, s
        a0 = fn(o0, env.configuration)
        a1 = idle(o1, env.configuration)
        env.step([a0, a1])

    return seed, agent_name, float(env.steps[-1][0].reward or 0.0)


def evaluate_holdout_match(task):
    seed, seat = task
    from kaggle_environments import make
    mods = get_worker_modules()
    fn_shop = mods["shop"].agent
    fn_v66 = mods["v66"].agent

    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    env.reset()
    for s in range(719):
        o0, o1 = env.state[0].observation, env.state[1].observation
        o0["step"], o1["step"] = s, s
        if seat == 0:
            a0 = fn_shop(o0, env.configuration)
            a1 = fn_v66(o1, env.configuration)
        else:
            a0 = fn_v66(o0, env.configuration)
            a1 = fn_shop(o1, env.configuration)
        env.step([a0, a1])

    r0 = float(env.steps[-1][0].reward or 0.0)
    r1 = float(env.steps[-1][1].reward or 0.0)

    if seat == 0:
        return {"seed": seed, "seat": 0, "shop_reward": r0, "v66_reward": r1, "margin": r0 - r1}
    else:
        return {"seed": seed, "seat": 1, "shop_reward": r1, "v66_reward": r0, "margin": r1 - r0}


def bootstrap_ci(deltas, num_samples=10000, alpha=0.05):
    arr = np.array(deltas, dtype=float)
    n = len(arr)
    np.random.seed(42)
    boot_means = [np.mean(np.random.choice(arr, size=n, replace=True)) for _ in range(num_samples)]
    return float(np.percentile(boot_means, 100 * (alpha / 2))), float(np.percentile(boot_means, 100 * (1 - alpha / 2)))


def main():
    print("=" * 80)
    print("CHAMPIONSHIP EXPERIMENT — STEP-216 THIRD-SHOP CAUSAL AUDIT")
    print("=" * 80)

    # 1. Verification of Frozen Baselines
    baselines = {
        "Canonical V54": (V54_PATH, get_sha256(V54_PATH)),
        "Canonical V66": (V66_PATH, get_sha256(V66_PATH)),
        "V54+ Macro": (V54_PLUS_PATH, get_sha256(V54_PLUS_PATH)),
        "V54++ Shop": (V54_SHOP_PATH, get_sha256(V54_SHOP_PATH)),
    }
    print("\n--- 1. FROZEN BASELINES ---")
    for k, (p, h) in baselines.items():
        print(f"[{k}] {os.path.basename(p)} -> SHA256: {h}")

    # 2. Census of Step-216 State across Discovery Set (500 seeds)
    print(f"\n--- 2. RUNNING STEP-216 CENSUS ({len(DISCOVERY_SEEDS)} SEEDS: 1001-1500) ---")
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=11) as ex:
        census_records = list(ex.map(evaluate_census_episode, DISCOVERY_SEEDS))
    dt_census = time.time() - t0
    print(f"Census completed in {dt_census:.2f}s ({len(census_records)/dt_census:.2f} eps/sec)")

    # Save Census Checkpoint Immediately
    census_out_path = os.path.join(BASE_DIR, "research", "shop216_census_results.json")
    with open(census_out_path, "w") as f:
        json.dump(census_records, f)
    print(f"Census checkpoint saved to: {census_out_path}")

    third_shop_counts = Counter()
    late_yarn_seeds = []
    late_smoothie_seeds = []
    late_bakery_seeds = []
    large_v66_win_seeds = []

    for r in census_records:
        third = r["third_shop"]
        third_shop_counts[third] += 1
        snap144 = r["snapshots"]["144"] if "144" in r["snapshots"] else r["snapshots"][144]
        if third == "YARN_STORE" and not snap144["has_yarn"]:
            late_yarn_seeds.append(r["seed"])
        if third == "SMOOTHIE_SHOP" and not snap144["has_smoothie"]:
            late_smoothie_seeds.append(r["seed"])
        if third == "BAKERY" and not snap144["has_bakery"]:
            late_bakery_seeds.append(r["seed"])
        if r["margin"] < -5000.0:
            large_v66_win_seeds.append(r["seed"])

    print(f"\nThird Shop Frequencies at Step 216 across 500 seeds:")
    for shop, cnt in third_shop_counts.most_common():
        print(f"  {shop:20s}: {cnt} ({cnt/len(census_records)*100:.1f}%)")

    print(f"\nLate Shop Appearances (Unlocked at Step 216 for first time):")
    print(f"  Late YARN_STORE seeds:     {len(late_yarn_seeds)}")
    print(f"  Late SMOOTHIE_SHOP seeds: {len(late_smoothie_seeds)}")
    print(f"  Late BAKERY seeds:        {len(late_bakery_seeds)}")
    print(f"  Seeds where V66 beats V54++ by > $5,000: {len(large_v66_win_seeds)}")

    # 3. Paired Counterfactuals across S0 to S8 on Target Seeds
    cf_target_seeds = sorted(list(set(late_yarn_seeds[:15] + late_smoothie_seeds[:10] + late_bakery_seeds[:10] + large_v66_win_seeds[:10] + DISCOVERY_SEEDS[:10])))[:40]
    print(f"\n--- 3. RUNNING PAIRED COUNTERFACTUALS (S0-S8) ON {len(cf_target_seeds)} TARGET SEEDS (360 MATCHES) ---")

    cf_tasks = []
    for s in cf_target_seeds:
        for arm in ["S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"]:
            cf_tasks.append((s, arm))

    t1 = time.time()
    with ProcessPoolExecutor(max_workers=11) as ex:
        cf_results = list(ex.map(evaluate_counterfactual_task, cf_tasks))
    dt_cf = time.time() - t1
    print(f"Counterfactuals completed in {dt_cf:.2f}s ({len(cf_results)/dt_cf:.2f} matches/sec)")

    # Save Counterfactual Checkpoint Immediately
    cf_out_path = os.path.join(BASE_DIR, "research", "shop216_counterfactual_results.json")
    with open(cf_out_path, "w") as f:
        json.dump(cf_results, f)
    print(f"Counterfactual checkpoint saved to: {cf_out_path}")

    # Aggregate Counterfactual Performance
    arm_rewards = defaultdict(list)
    arm_moves = defaultdict(list)
    arm_productive = defaultdict(list)
    arm_cash = defaultdict(list)
    arm_first_diff = defaultdict(list)
    arm_diff_vs_s0 = defaultdict(list)

    seed_arm_map = defaultdict(dict)
    for res in cf_results:
        seed_arm_map[res["seed"]][res["arm"]] = res

    for s, arms in seed_arm_map.items():
        base_rew = arms["S0"]["reward"]
        for arm_id, data in arms.items():
            arm_rewards[arm_id].append(data["reward"])
            arm_moves[arm_id].append(data["move_count"])
            arm_productive[arm_id].append(data["productive_count"])
            arm_cash[arm_id].append(data["cash"])
            if data["first_diff_step"] is not None:
                arm_first_diff[arm_id].append(data["first_diff_step"])
            arm_diff_vs_s0[arm_id].append(data["reward"] - base_rew)

    print("\nCounterfactual Comparative Results (relative to S0 Baseline):")
    print(f"{'Arm':6s} | {'Mean Reward':12s} | {'Delta vs S0':12s} | {'95% CI':22s} | {'Productive Act':15s} | {'First Div Step':15s}")
    print("-" * 90)
    for arm_id in ["S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"]:
        rews = arm_rewards[arm_id]
        deltas = arm_diff_vs_s0[arm_id]
        m_rew = np.mean(rews)
        m_del = np.mean(deltas)
        ci_l, ci_u = bootstrap_ci(deltas) if arm_id != "S0" else (0.0, 0.0)
        m_prod = np.mean(arm_productive[arm_id])
        f_div = np.mean(arm_first_diff[arm_id]) if arm_first_diff[arm_id] else 0.0
        div_str = f"{f_div:.1f}" if f_div > 0 else "None"
        print(f"{arm_id:6s} | ${m_rew:11.2f} | ${m_del:+11.2f} | [${ci_l:+8.1f}, ${ci_u:+8.1f}] | {m_prod:15.1f} | {div_str:15s}")

    # Late-Yarn specific delta
    late_yarn_deltas = [seed_arm_map[s]["S2"]["reward"] - seed_arm_map[s]["S0"]["reward"] for s in cf_target_seeds if s in late_yarn_seeds and "S2" in seed_arm_map[s]]
    if late_yarn_deltas:
        print(f"\nLate Yarn Seeds Specific Switch Impact (S2 vs S0 on {len(late_yarn_deltas)} seeds):")
        print(f"  Mean Delta: ${np.mean(late_yarn_deltas):+.2f}, Median: ${np.median(late_yarn_deltas):+.2f}")

    # 4. Large-Win Seed Forensics
    print(f"\n--- 4. LARGE V66-WIN SEED FORENSICS ---")
    large_win_cf_deltas = defaultdict(list)
    for s in cf_target_seeds:
        if s in large_v66_win_seeds and s in seed_arm_map:
            for arm_id in ["S1", "S2", "S3", "S5", "S7"]:
                if arm_id in seed_arm_map[s]:
                    large_win_cf_deltas[arm_id].append(seed_arm_map[s][arm_id]["reward"] - seed_arm_map[s]["S0"]["reward"])

    for arm_id, dels in large_win_cf_deltas.items():
        if dels:
            print(f"  {arm_id:4s} vs S0 on large-loss seeds: Mean Delta = ${np.mean(dels):+.2f}")

    # 5. Untouched Holdout Evaluation: 500 Seeds x 2 Seats = 1,000 Matches
    print(f"\n--- 5. UNTOUCHED HOLDOUT EVALUATION ({len(HOLDOUT_SEEDS)} SEEDS: 1501-2000, 1,000 MATCHES) ---")
    holdout_tasks = [(s, seat) for s in HOLDOUT_SEEDS for seat in (0, 1)]
    t2 = time.time()
    with ProcessPoolExecutor(max_workers=11) as ex:
        holdout_records = list(ex.map(evaluate_holdout_match, holdout_tasks))
    dt_holdout = time.time() - t2
    print(f"Holdout completed in {dt_holdout:.2f}s ({len(holdout_records)/dt_holdout:.2f} matches/sec)")

    # Save Holdout Checkpoint Immediately
    holdout_out_path = os.path.join(BASE_DIR, "research", "shop216_holdout_results.json")
    with open(holdout_out_path, "w") as f:
        json.dump(holdout_records, f)
    print(f"Holdout checkpoint saved to: {holdout_out_path}")

    seed_margins = defaultdict(dict)
    for r in holdout_records:
        seed_margins[r["seed"]][r["seat"]] = r

    symmetric_deltas = []
    v54pp_holdout_rewards = []
    v66_holdout_rewards = []
    wins = 0
    ties = 0
    losses = 0

    for s, seats in seed_margins.items():
        m0 = seats[0]["margin"]
        m1 = seats[1]["margin"]
        mean_delta = (m0 + m1) / 2.0
        symmetric_deltas.append(mean_delta)

        r_shop = (seats[0]["shop_reward"] + seats[1]["shop_reward"]) / 2.0
        r_v66 = (seats[0]["v66_reward"] + seats[1]["v66_reward"]) / 2.0
        v54pp_holdout_rewards.append(r_shop)
        v66_holdout_rewards.append(r_v66)

        if mean_delta > 0:
            wins += 1
        elif mean_delta == 0:
            ties += 1
        else:
            losses += 1

    holdout_mean = float(np.mean(symmetric_deltas))
    holdout_median = float(np.median(symmetric_deltas))
    holdout_sd = float(np.std(symmetric_deltas, ddof=1))
    holdout_ci_l, holdout_ci_u = bootstrap_ci(symmetric_deltas)

    print(f"\nV54++ vs Canonical V66 on 500 Untouched Holdout Seeds (1,000 Matches):")
    print(f"  V54++ Mean Reward: ${np.mean(v54pp_holdout_rewards):.2f}")
    print(f"  V66 Mean Reward:   ${np.mean(v66_holdout_rewards):.2f}")
    print(f"  Mean Margin:       ${holdout_mean:+.2f}")
    print(f"  Median Margin:     ${holdout_median:+.2f}")
    print(f"  Std Dev:           ${holdout_sd:.2f}")
    print(f"  95% Bootstrap CI:  [${holdout_ci_l:+.2f}, ${holdout_ci_u:+.2f}]")
    print(f"  Record (W / T / L): {wins} / {ties} / {losses} (Win Rate: {wins/len(symmetric_deltas)*100:.1f}%)")

    # 6. Solo Benchmark (25 Seeds vs IDLE)
    print(f"\n--- 6. SOLO BENCHMARK ({len(SOLO_SEEDS)} SEEDS VS IDLE) ---")
    solo_tasks = [(s, ag) for s in SOLO_SEEDS for ag in ["V66", "V54++", "V54+", "V54"]]
    with ProcessPoolExecutor(max_workers=11) as ex:
        solo_records = list(ex.map(evaluate_solo_episode, solo_tasks))

    solo_ag_rewards = defaultdict(list)
    for s, ag, rew in solo_records:
        solo_ag_rewards[ag].append(rew)

    # Save Solo Checkpoint Immediately
    solo_out_path = os.path.join(BASE_DIR, "research", "shop216_solo_results.json")
    with open(solo_out_path, "w") as f:
        json.dump(solo_records, f)
    print(f"Solo checkpoint saved to: {solo_out_path}")

    print("\nSolo Results vs IDLE:")
    for ag in ["V66", "V54++", "V54+", "V54"]:
        rews = solo_ag_rewards[ag]
        ci_l, ci_u = bootstrap_ci(rews)
        print(f"  {ag:8s}: Mean = ${np.mean(rews):10.2f}, Median = ${np.median(rews):10.2f}, 95% CI = [${ci_l:.0f}, ${ci_u:.0f}]")

    # Master Synthesis JSON
    results_payload = {
        "baselines": baselines,
        "census": {
            "num_seeds": len(census_records),
            "third_shop_counts": dict(third_shop_counts),
            "late_yarn_count": len(late_yarn_seeds),
            "late_smoothie_count": len(late_smoothie_seeds),
            "late_bakery_count": len(late_bakery_seeds),
            "large_v66_win_count": len(large_v66_win_seeds),
        },
        "counterfactuals": {
            arm_id: {
                "mean_reward": float(np.mean(arm_rewards[arm_id])),
                "delta_vs_s0": float(np.mean(arm_diff_vs_s0[arm_id])),
                "ci": list(bootstrap_ci(arm_diff_vs_s0[arm_id])) if arm_id != "S0" else [0.0, 0.0],
                "mean_productive": float(np.mean(arm_productive[arm_id])),
                "mean_moves": float(np.mean(arm_moves[arm_id])),
            }
            for arm_id in ["S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"]
        },
        "holdout": {
            "num_seeds": len(HOLDOUT_SEEDS),
            "num_matches": len(holdout_records),
            "v54pp_mean": float(np.mean(v54pp_holdout_rewards)),
            "v66_mean": float(np.mean(v66_holdout_rewards)),
            "mean_margin": holdout_mean,
            "median_margin": holdout_median,
            "std_dev": holdout_sd,
            "ci_95": [holdout_ci_l, holdout_ci_u],
            "record": {"wins": wins, "ties": ties, "losses": losses},
            "win_rate": wins / len(symmetric_deltas),
        },
        "solo": {
            ag: {
                "mean": float(np.mean(solo_ag_rewards[ag])),
                "median": float(np.median(solo_ag_rewards[ag])),
                "ci": list(bootstrap_ci(solo_ag_rewards[ag])),
            }
            for ag in ["V66", "V54++", "V54+", "V54"]
        }
    }

    out_path = os.path.join(BASE_DIR, "research", "shop216_causal_audit_results.json")
    with open(out_path, "w") as f:
        json.dump(results_payload, f, indent=2)
    print(f"\nAll synthesis results saved to: {out_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
