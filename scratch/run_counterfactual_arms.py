"""
scratch/run_counterfactual_arms.py
==================================
Runs paired counterfactuals A0..A6 against Canonical V66.
Evaluates across:
1. 7 Large V66 Loss Seeds
2. Full Partition Sample of 50 seeds (100 symmetric matches):
   - 7 Large V66 losses (>= $5k)
   - 10 Medium V66 losses ($2.5k - $5k)
   - 20 Close games (|margin| < $2.5k)
   - 13 V54++ Large wins (>= $5k)
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

BASE_DIR = os.path.abspath(".")
V54_PATH = os.path.join(BASE_DIR, "external_repos", "lixingtao123-Kaggriculture", "variant_v54_h3q4", "main.py")
V62_PATH = os.path.join(BASE_DIR, "external_repos", "kaggriculture-v66-agent", "candidate_v62_composite_bakery_yarn.py")
V66_PATH = os.path.join(BASE_DIR, "external_repos", "kaggriculture-v66-agent", "candidate_v66_meta_closed_loop.py")
V54PLUS_PATH = os.path.join(BASE_DIR, "candidates", "v54_plus_shop.py")

for p in [os.path.dirname(V54_PATH), os.path.dirname(V62_PATH)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Load base modules
spec_v54 = importlib.util.spec_from_file_location("v54_base_cf", V54_PATH)
mod_v54 = importlib.util.module_from_spec(spec_v54)
spec_v54.loader.exec_module(mod_v54)

spec_v62 = importlib.util.spec_from_file_location("v62_base_cf", V62_PATH)
mod_v62 = importlib.util.module_from_spec(spec_v62)
spec_v62.loader.exec_module(mod_v62)

spec_v66 = importlib.util.spec_from_file_location("v66_base_cf", V66_PATH)
mod_v66 = importlib.util.module_from_spec(spec_v66)
spec_v66.loader.exec_module(mod_v66)

spec_v54plus = importlib.util.spec_from_file_location("v54plus_cf", V54PLUS_PATH)
mod_v54plus = importlib.util.module_from_spec(spec_v54plus)
spec_v54plus.loader.exec_module(mod_v54plus)

# Base routes & overlays
_CONFIG_BASE = copy.deepcopy(mod_v62._V54_CONFIG)
_V60_SEED_TRIM = mod_v62._v60_seed_trim
_V60_SHED_GUARD = mod_v62._v60_shed_guard
_ROUTE_LOADED = mod_v66._route_loaded_units
_TERM_UNITS = mod_v66._TERMINAL_UNITS
_TERM_MKT = mod_v66._TERMINAL_MARKET
_VIS_CONF = mod_v62._v56_visible_configuration

# Build Arm Policies
# A0: Frozen V54++
# A1: Strawberry scheduling altered (no early strawberry buy/plant in steps 0-143, redirecting labor to wheat)
# A2: Cow timing altered (delay step 150 cow buy to step 174 to preserve early liquidity)
# A3: Sheep/cow timing altered (swap cow buy at step 150 with sheep buy)
# A4: Combined Strawberry + Cow timing altered (A1 + A2)
# A5: Early market-sales policy altered (liquidate all 20 wheat at step 72 to front Day 6 hiring)
# A6: Livestock-care priority altered (feed_days_reserve = 1.0 instead of 1.5)

def build_counterfactual_agent(arm_id: str):
    # Base routes
    r_backbone = copy.deepcopy(mod_v62._V56_BACKBONE_ROUTE)
    r_yarn = copy.deepcopy(mod_v62._V56_YARN_ROUTE)
    r_bakery = copy.deepcopy(mod_v62._V58_BAKERY_YARN_ROUTE)
    cfg = copy.deepcopy(_CONFIG_BASE)
    
    if arm_id == "A1" or arm_id == "A4":
        # A1: Suppress early strawberry planting (replace PLANT STRAWBERRY with PLANT WHEAT in early steps)
        for r in [r_backbone, r_yarn, r_bakery]:
            for s in range(144):
                item = r[s]
                f_act = item.get("farmer", [])
                if len(f_act) > 1 and f_act[0] == "PLANT" and f_act[1] == "STRAWBERRY":
                    item["farmer"] = ["PLANT", "WHEAT"]
                mkt = item.get("market", [])
                new_mkt = []
                for ord in mkt:
                    if len(ord) >= 3 and ord[0] == "BUY_SEED" and ord[1] == "STRAWBERRY" and s < 144:
                        new_mkt.append(["BUY_SEED", "WHEAT", ord[2]])
                    else:
                        new_mkt.append(ord)
                item["market"] = new_mkt

    if arm_id == "A2" or arm_id == "A4":
        # A2: Cow timing altered (delay step 150 cow purchase to step 174)
        for r in [r_backbone, r_yarn, r_bakery]:
            if len(r) > 150:
                mkt150 = r[150].get("market", [])
                delayed_orders = []
                rem_orders = []
                for ord in mkt150:
                    if len(ord) >= 3 and ord[0] == "BUY_ANIMAL" and ord[1] == "COW":
                        delayed_orders.append(ord)
                    else:
                        rem_orders.append(ord)
                r[150]["market"] = rem_orders
                if len(r) > 174:
                    r[174]["market"] = (r[174].get("market") or []) + delayed_orders

    if arm_id == "A3":
        # A3: Sheep/cow timing altered (at step 150, replace BUY_ANIMAL COW with BUY_ANIMAL SHEEP)
        for r in [r_backbone, r_yarn, r_bakery]:
            if len(r) > 150:
                for ord in (r[150].get("market") or []):
                    if len(ord) >= 3 and ord[0] == "BUY_ANIMAL" and ord[1] == "COW":
                        ord[1] = "SHEEP"

    if arm_id == "A5":
        # A5: Early market-sales policy altered (sell all wheat at step 72)
        for r in [r_backbone, r_yarn, r_bakery]:
            if len(r) > 72:
                r[72]["market"] = (r[72].get("market") or []) + [["SELL", "WHEAT", 20]]

    if arm_id == "A6":
        # A6: Livestock-care priority altered
        from dataclasses import replace
        cfg = replace(cfg, feed_days_reserve=1.0)

    pol_backbone = mod_v54._v51_build_policy(r_backbone, cfg)
    pol_yarn = mod_v54._v51_build_policy(r_yarn, cfg)
    pol_bakery = mod_v54._v51_build_policy(r_bakery, cfg)
    
    state = {0: {"route": "backbone", "last": -1}, 1: {"route": "backbone", "last": -1}}
    
    def agent_fn(obs, conf=None):
        step = obs.get("step")
        if step is None:
            step = 24 * int(obs.get("day", 0) or 0) + int(obs.get("hour", 0) or 0)
        else:
            step = int(step)
            
        seat = 1 if int(obs.get("player", 0) or 0) == 1 else 0
        s_state = state[seat]
        if step == 0 or step <= s_state["last"]:
            s_state["route"] = "backbone"
        s_state["last"] = step
        
        visible = _VIS_CONF(conf)
        town = obs.get("town", {}) or {}
        shops = list(town.get("unlocked_shops", []) or [])
        
        s_state["route"] = mod_v54plus._select_route(step, shops)
        route = s_state["route"]
        
        if route == "yarn":
            action = pol_yarn(obs, visible)
        elif route == "bakery":
            action = pol_bakery(obs, visible)
        else:
            action = pol_backbone(obs, visible)
            
        action = _V60_SEED_TRIM(obs, action, step)
        cap = int((conf or {}).get("shedCapacity", 100)) or 100
        action = _V60_SHED_GUARD(obs, action, cap)
        if 713 <= step <= 716:
            action = _ROUTE_LOADED(obs, action, step)
        if step in (717, 718):
            action = _TERM_UNITS(obs, action, step)
        if step == 718:
            action = _TERM_MKT(obs, action, rule="collision", replace=True)
            
        return action

    return agent_fn

_ARM_CACHE = {}

def get_arm_agent(arm_id: str):
    if arm_id not in _ARM_CACHE:
        _ARM_CACHE[arm_id] = build_counterfactual_agent(arm_id)
    return _ARM_CACHE[arm_id]

def run_single_match(seed, arm_id, seat):
    """Runs a single match: arm vs Canonical V66."""
    fn_arm = get_arm_agent(arm_id)
    fn_v66 = mod_v54plus.get_agent_fn("V66") if hasattr(mod_v54plus, "get_agent_fn") else None
    if fn_v66 is None:
        # Load V66
        spec_v66_main = importlib.util.spec_from_file_location("v66_main_eval", os.path.join(BASE_DIR, "external_repos", "kaggriculture-v66-agent", "main.py"))
        mod_v66_main = importlib.util.module_from_spec(spec_v66_main)
        spec_v66_main.loader.exec_module(mod_v66_main)
        fn_v66 = mod_v66_main.agent

    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    env.reset()
    
    for s in range(719):
        o0, o1 = env.state[0].observation, env.state[1].observation
        o0["step"], o1["step"] = s, s
        
        if seat == 0:
            act0 = fn_arm(o0, env.configuration)
            act1 = fn_v66(o1, env.configuration)
        else:
            act0 = fn_v66(o0, env.configuration)
            act1 = fn_arm(o1, env.configuration)
            
        env.step([act0, act1])
        
    r0 = float(env.steps[-1][0].reward or 0.0)
    r1 = float(env.steps[-1][1].reward or 0.0)
    
    arm_reward = r0 if seat == 0 else r1
    v66_reward = r1 if seat == 0 else r0
    margin = arm_reward - v66_reward
    
    return {
        "seed": seed,
        "arm": arm_id,
        "seat": seat,
        "arm_reward": arm_reward,
        "v66_reward": v66_reward,
        "margin": margin
    }

def worker_task(task):
    seed, arm_id, seat = task
    return run_single_match(seed, arm_id, seat)

if __name__ == "__main__":
    # Select seeds for testing:
    # 7 large V66 loss seeds
    large_loss_seeds = [1542, 1609, 1773, 1871, 1948, 1949, 1969]
    
    # 10 medium loss seeds ($2.5k - $5k lead for V66)
    # 20 close game seeds (|margin| < $2.5k)
    # 13 large V54++ win seeds (>= $5k lead for V54++)
    with open("research/shop216_holdout_results.json") as f:
        matches = json.load(f)
        
    seed_stats = defaultdict(dict)
    for m in matches:
        seed_stats[m["seed"]][m["seat"]] = m
        
    med_loss_seeds = []
    close_seeds = []
    large_win_seeds = []
    
    for s, seats in seed_stats.items():
        if s in large_loss_seeds:
            continue
        v54_avg = (seats[0]["shop_reward"] + seats[1]["shop_reward"]) / 2.0
        v66_avg = (seats[0]["v66_reward"] + seats[1]["v66_reward"]) / 2.0
        margin = v54_avg - v66_avg
        if -5000 <= margin < -2500 and len(med_loss_seeds) < 10:
            med_loss_seeds.append(s)
        elif abs(margin) < 2500 and len(close_seeds) < 20:
            close_seeds.append(s)
        elif margin >= 5000 and len(large_win_seeds) < 13:
            large_win_seeds.append(s)
            
    eval_seeds = large_loss_seeds + med_loss_seeds + close_seeds + large_win_seeds
    print(f"Total evaluation seeds: {len(eval_seeds)} (Large loss: {len(large_loss_seeds)}, Med loss: {len(med_loss_seeds)}, Close: {len(close_seeds)}, Win: {len(large_win_seeds)})")
    
    arms = ["A0", "A1", "A2", "A3", "A4", "A5", "A6"]
    
    results_by_arm = defaultdict(list)
    for arm in arms:
        arm_t0 = time.time()
        arm_tasks = [(seed, arm, seat) for seed in eval_seeds for seat in [0, 1]]
        print(f"\n>>> Running Arm {arm} ({len(arm_tasks)} matches) >>>")
        with ProcessPoolExecutor(max_workers=10) as executor:
            for res in executor.map(worker_task, arm_tasks):
                results_by_arm[arm].append(res)
        print(f">>> Finished Arm {arm} in {time.time()-arm_t0:.1f}s")
        with open("research/counterfactual_raw_results.json", "w") as f:
            json.dump(results_by_arm, f, indent=2)
        
    # Analyze by arm
    # Aggregate to seed level (paired symmetric average)
    summary_report = {}
    
    # Base A0 performance
    a0_seed_margins = {}
    for res in results_by_arm["A0"]:
        pass
        
    seed_groups = {
        "Large V66 Losses": large_loss_seeds,
        "Medium V66 Losses": med_loss_seeds,
        "Close Games": close_seeds,
        "Large V54++ Wins": large_win_seeds,
        "All 50 Seeds": eval_seeds
    }
    
    print("\n=======================================================")
    print("COUNTERFACTUAL AUDIT RESULTS (A0..A6)")
    print("=======================================================")
    
    for arm in arms:
        # Group by seed
        arm_seeds = defaultdict(dict)
        for r in results_by_arm[arm]:
            arm_seeds[r["seed"]][r["seat"]] = r
            
        seed_margins = {}
        seed_arm_rewards = {}
        for s, seats in arm_seeds.items():
            avg_arm = (seats[0]["arm_reward"] + seats[1]["arm_reward"]) / 2.0
            avg_v66 = (seats[0]["v66_reward"] + seats[1]["v66_reward"]) / 2.0
            seed_margins[s] = avg_arm - avg_v66
            seed_arm_rewards[s] = avg_arm
            
        if arm == "A0":
            a0_seed_rewards = seed_arm_rewards
            a0_seed_margins = seed_margins
            
        print(f"\n--- ARM {arm} ---")
        arm_summary = {}
        for group_name, g_seeds in seed_groups.items():
            g_margins = [seed_margins[s] for s in g_seeds]
            g_deltas = [seed_arm_rewards[s] - a0_seed_rewards[s] for s in g_seeds]
            
            mean_margin = np.mean(g_margins)
            mean_delta = np.mean(g_deltas)
            med_delta = np.median(g_deltas)
            
            # Bootstrap CI on delta
            if len(g_deltas) > 1 and arm != "A0":
                boot = [np.mean(np.random.choice(g_deltas, size=len(g_deltas), replace=True)) for _ in range(1000)]
                ci_low, ci_high = np.percentile(boot, [2.5, 97.5])
            else:
                ci_low, ci_high = 0.0, 0.0
                
            wins = sum(1 for d in g_deltas if d > 0)
            losses = sum(1 for d in g_deltas if d < 0)
            ties = sum(1 for d in g_deltas if abs(d) < 0.01)
            
            p_loss_500 = np.mean([1.0 if d < -500 else 0.0 for d in g_deltas])
            p_loss_1000 = np.mean([1.0 if d < -1000 else 0.0 for d in g_deltas])
            p_gain_2000 = np.mean([1.0 if d > 2000 else 0.0 for d in g_deltas])
            
            print(f"  {group_name:18s} (N={len(g_seeds):2d}): Mean Delta={mean_delta:+8.1f} | Med={med_delta:+8.1f} | 95% CI=[{ci_low:+8.1f}, {ci_high:+8.1f}] | W/T/L={wins}/{ties}/{losses} | P(<-1k)={p_loss_1000:.1%}")
            
            arm_summary[group_name] = {
                "n": len(g_seeds),
                "mean_delta": float(mean_delta),
                "med_delta": float(med_delta),
                "ci_low": float(ci_low),
                "ci_high": float(ci_high),
                "wins": wins,
                "losses": losses,
                "ties": ties,
                "p_loss_500": float(p_loss_500),
                "p_loss_1000": float(p_loss_1000),
                "p_gain_2000": float(p_gain_2000)
            }
        summary_report[arm] = arm_summary
        
    with open("research/counterfactual_summary_report.json", "w") as f:
        json.dump(summary_report, f, indent=2)
    print("\nSaved research/counterfactual_summary_report.json successfully.")
