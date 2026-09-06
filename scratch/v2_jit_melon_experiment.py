"""
V2 Day-0 Just-In-Time Melon Pipeline Causal Study
=================================================
A strict, isolated, reproducible experimental harness evaluating:
- Frozen V2 (Treatment A)
- Factorial treatments (Treatments B through G)
- Full Canonical Day-0 JIT Melon Pipeline (Treatment H)

Preserves Slot 1 and Slot 2 live candidate files unaltered.
"""

import sys
import os
import time
import json
import math
import copy
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
from kaggle_environments import make

# Ensure project root in sys.path
PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import candidates.slot2_aethel_refined_v2 as v2
import opponents.live_flooder_v1 as lf

# ---------------------------------------------------------------------------
# 1. Load Canonical Ground-Truth Opening Trace from Gayathri / Yuyajk Replays
# ---------------------------------------------------------------------------
REPLAY_FILE = os.path.join(PROJECT_ROOT, "scratch", "replays", "V2_Loss_vs_GAYATHRI SALINI_104796498.json")

with open(REPLAY_FILE, "r", encoding="utf-8") as f:
    _replay_data = json.load(f)

# Note: In Kaggle Environment replays, steps[s+1][p]['action'] is the action executed at step s.
_raw_steps = _replay_data["steps"]
CANONICAL_JIT_TRACE = []
for s in range(len(_raw_steps) - 1):
    CANONICAL_JIT_TRACE.append(copy.deepcopy(_raw_steps[s + 1][0].get("action", {})))

while len(CANONICAL_JIT_TRACE) < 720:
    CANONICAL_JIT_TRACE.append({"farmer": ["PASS"], "hands": [], "market": []})

V2_TRACE = copy.deepcopy(v2._TRACE)

# ---------------------------------------------------------------------------
# 2. Build Factorial Agents (Treatments A through H)
# ---------------------------------------------------------------------------

def agent_A_frozen_v2(obs, config=None):
    """Treatment A: Frozen Aethel-Refined V2 baseline."""
    return v2.agent(obs, config)


def agent_B_workers_only(obs, config=None):
    """Treatment B: V2 + Extra Workers Only.
    Hires 5 hands immediately on Step 0 instead of staggered hiring; keeps 7 melons, 10 wheat, reduced feed.
    """
    step = int(obs.get("step", 0) or 0)
    if step >= v2._TERMINAL_START_STEP:
        return v2._terminal_action(obs)
    action = copy.deepcopy(V2_TRACE[min(step, len(V2_TRACE) - 1)])
    if step == 0:
        action["market"] = [
            ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"],
            ["BUY_ANIMAL", "COW", 3], ["BUY_ANIMAL", "SHEEP", 1],
            ["BUY_SEED", "MELON", 7], ["BUY_SEED", "WHEAT", 10],
            ["BUY_PRODUCT", "WHEAT", 16]
        ]
    elif step in (1, 2, 6):
        action["market"] = [o for o in action.get("market", []) if o != ["HIRE"]]
    return action


def agent_C_melons_only(obs, config=None):
    """Treatment C: V2 + Extra Melons Only.
    Buys 12 melons instead of 7; keeps 2 hires, 10 wheat, reduced feed buffer.
    """
    step = int(obs.get("step", 0) or 0)
    if step >= v2._TERMINAL_START_STEP:
        return v2._terminal_action(obs)
    action = copy.deepcopy(V2_TRACE[min(step, len(V2_TRACE) - 1)])
    if step == 0:
        action["market"] = [
            ["BUY_ANIMAL", "COW", 3], ["BUY_ANIMAL", "SHEEP", 1],
            ["BUY_SEED", "MELON", 12], ["BUY_SEED", "WHEAT", 10],
            ["BUY_PRODUCT", "WHEAT", 8],
            ["HIRE"], ["HIRE"]
        ]
    return action


def agent_D_reduced_feed_only(obs, config=None):
    """Treatment D: V2 + Reduced Initial Feed Only.
    Keeps 2 hires, 7 melons, 10 wheat, 3C/1S.
    Buys only 2 feed upfront ($58) instead of 17 ($472); holds freed $414 liquid cash.
    Buys feed just-in-time when shed buffer <= 2.
    """
    step = int(obs.get("step", 0) or 0)
    if step >= v2._TERMINAL_START_STEP:
        return v2._terminal_action(obs)
    action = copy.deepcopy(V2_TRACE[min(step, len(V2_TRACE) - 1)])
    if step == 0:
        action["market"] = [
            ["BUY_ANIMAL", "COW", 3], ["BUY_ANIMAL", "SHEEP", 1],
            ["BUY_SEED", "MELON", 7], ["BUY_SEED", "WHEAT", 10],
            ["BUY_PRODUCT", "WHEAT", 2],
            ["HIRE"], ["HIRE"]
        ]
    else:
        private = obs.get("private", {}) or {}
        shed = private.get("shed", {}) or {}
        wheat = shed.get("WHEAT", 0)
        farm = (obs.get("farms", [{}]))[int(obs.get("player", 0) or 0)]
        money = float(farm.get("money", 0) or 0)
        orders = action.get("market", [])
        has_feed_buy = any(isinstance(o, list) and len(o) >= 3 and o[0] == "BUY_PRODUCT" and o[1] == "WHEAT" for o in orders)
        if wheat <= 2 and not has_feed_buy and money >= 60 and len(orders) < 10:
            orders.append(["BUY_PRODUCT", "WHEAT", 2])
    return action


def agent_E_workers_and_melons(obs, config=None):
    """Treatment E: V2 + Extra Workers + Extra Melons.
    5 hires, 12 melons, 10 wheat, 3C/1S, reduced feed to fit budget.
    """
    step = int(obs.get("step", 0) or 0)
    if step >= v2._TERMINAL_START_STEP:
        return v2._terminal_action(obs)
    action = copy.deepcopy(V2_TRACE[min(step, len(V2_TRACE) - 1)])
    if step == 0:
        action["market"] = [
            ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"],
            ["BUY_ANIMAL", "COW", 3], ["BUY_ANIMAL", "SHEEP", 1],
            ["BUY_SEED", "MELON", 12], ["BUY_SEED", "WHEAT", 10],
            ["BUY_PRODUCT", "WHEAT", 8]
        ]
    elif step in (1, 2, 6):
        action["market"] = [o for o in action.get("market", []) if o != ["HIRE"]]
    return action


def agent_F_workers_and_feed(obs, config=None):
    """Treatment F: V2 + Extra Workers + Reduced Feed.
    5 hires, 7 melons, 10 wheat, 3C/1S, 2 feed upfront, liquid cash held.
    """
    step = int(obs.get("step", 0) or 0)
    if step >= v2._TERMINAL_START_STEP:
        return v2._terminal_action(obs)
    action = copy.deepcopy(V2_TRACE[min(step, len(V2_TRACE) - 1)])
    if step == 0:
        action["market"] = [
            ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"],
            ["BUY_ANIMAL", "COW", 3], ["BUY_ANIMAL", "SHEEP", 1],
            ["BUY_SEED", "MELON", 7], ["BUY_SEED", "WHEAT", 10],
            ["BUY_PRODUCT", "WHEAT", 2]
        ]
    elif step in (1, 2, 6):
        action["market"] = [o for o in action.get("market", []) if o != ["HIRE"]]
    return action


def agent_G_melons_and_feed(obs, config=None):
    """Treatment G: V2 + Extra Melons + Reduced Feed.
    2 hires, 12 melons, 10 wheat, 3C/1S, 2 feed upfront.
    """
    step = int(obs.get("step", 0) or 0)
    if step >= v2._TERMINAL_START_STEP:
        return v2._terminal_action(obs)
    action = copy.deepcopy(V2_TRACE[min(step, len(V2_TRACE) - 1)])
    if step == 0:
        action["market"] = [
            ["BUY_ANIMAL", "COW", 3], ["BUY_ANIMAL", "SHEEP", 1],
            ["BUY_SEED", "MELON", 12], ["BUY_SEED", "WHEAT", 10],
            ["BUY_PRODUCT", "WHEAT", 2],
            ["HIRE"], ["HIRE"]
        ]
    return action


def agent_H_full_jit_pipeline(obs, config=None):
    """Treatment H: Full Canonical Day-0 JIT Melon Pipeline.
    5 hires, 12 melons, 7 wheat, 2 cows, 2 sheep, 0 upfront feed, 2 feed JIT on Step 1.
    Integrates the canonical top-agent opening through Step 711 with V2 terminal net at Step 712+.
    """
    step = int(obs.get("step", 0) or 0)
    if step >= 712:
        return v2._terminal_action(obs)
    if step < len(CANONICAL_JIT_TRACE):
        action = copy.deepcopy(CANONICAL_JIT_TRACE[step])
    else:
        action = {"farmer": ["PASS"], "hands": [], "market": []}
    return action


TREATMENT_MAP = {
    "A": {"name": "Treatment A: Frozen V2", "fn": agent_A_frozen_v2, "desc": "Frozen V2 control"},
    "B": {"name": "Treatment B: Extra Workers Only", "fn": agent_B_workers_only, "desc": "5 hires, 7 melons, 16 feed"},
    "C": {"name": "Treatment C: Extra Melons Only", "fn": agent_C_melons_only, "desc": "2 hires, 12 melons, 8 feed"},
    "D": {"name": "Treatment D: Reduced Feed Only", "fn": agent_D_reduced_feed_only, "desc": "2 hires, 7 melons, 2 feed + liquid cash"},
    "E": {"name": "Treatment E: Workers + Melons", "fn": agent_E_workers_and_melons, "desc": "5 hires, 12 melons, 8 feed"},
    "F": {"name": "Treatment F: Workers + Reduced Feed", "fn": agent_F_workers_and_feed, "desc": "5 hires, 7 melons, 2 feed"},
    "G": {"name": "Treatment G: Melons + Reduced Feed", "fn": agent_G_melons_and_feed, "desc": "2 hires, 12 melons, 2 feed"},
    "H": {"name": "Treatment H: Full JIT Pipeline", "fn": agent_H_full_jit_pipeline, "desc": "5 hires, 12 melons, 2 feed, full JIT"}
}

# ---------------------------------------------------------------------------
# 3. Simulation Runner
# ---------------------------------------------------------------------------

def run_single_game(args):
    """Runs a single 720-turn game between candidate and opponent."""
    agent_key, opp_key, seed, swapped = args
    cand_fn = TREATMENT_MAP[agent_key]["fn"]
    
    if opp_key == "v2":
        opp_fn = v2.agent
    elif opp_key == "live_flooder":
        opp_fn = lf.agent
    elif opp_key == "starter":
        opp_fn = "starter"
    else:
        opp_fn = v2.agent

    agent0 = opp_fn if swapped else cand_fn
    agent1 = cand_fn if swapped else opp_fn
    our_player = 1 if swapped else 0
    opp_player = 0 if swapped else 1

    cfg = {"episodeSteps": 720, "seed": seed}
    env = make("kaggriculture", configuration=cfg, debug=False)
    
    checkpoints = (24, 48, 72, 100, 120, 144, 168, 192, 216, 240, 255, 264, 265, 266, 288, 336, 360, 432, 504, 600, 650, 719)
    cp_telemetry = {}
    
    starvation_events = 0
    min_feed_seen = 999
    
    t0 = time.time()
    env.run([agent0, agent1])
    elapsed = time.time() - t0

    # Extract micro-telemetry
    for s_idx in checkpoints:
        if s_idx < len(env.steps):
            f_us = env.steps[s_idx][our_player]["observation"]["farms"][our_player]
            priv_us = env.steps[s_idx][our_player]["observation"]["private"]
            
            melons_planted = 0
            wheat_planted = 0
            cows_placed = 0
            sheep_placed = 0
            for row in f_us.get("tiles", []):
                for t in row:
                    if isinstance(t, dict):
                        if t.get("crop") == "MELON": melons_planted += 1
                        elif t.get("crop") == "WHEAT": wheat_planted += 1
                        if t.get("animal") == "COW": cows_placed += 1
                        elif t.get("animal") == "SHEEP": sheep_placed += 1
            
            cp_telemetry[f"step_{s_idx}"] = {
                "money": float(f_us.get("money", 0)),
                "shed_melon": int(priv_us.get("shed", {}).get("MELON", 0)),
                "shed_wheat": int(priv_us.get("shed", {}).get("WHEAT", 0)),
                "shed_fertilizer": int(priv_us.get("shed", {}).get("FERTILIZER", 0)),
                "hands": len(f_us.get("hands", [])),
                "cows": cows_placed,
                "sheep": sheep_placed,
                "melons_planted": melons_planted,
                "wheat_planted": wheat_planted
            }

    # Verify starvation across all steps
    for s_idx, st in enumerate(env.steps):
        f_us = st[our_player]["observation"]["farms"][our_player]
        priv_us = st[our_player]["observation"]["private"]
        current_wheat = int(priv_us.get("shed", {}).get("WHEAT", 0))
        if current_wheat < min_feed_seen:
            min_feed_seen = current_wheat
        for row in f_us.get("tiles", []):
            for t in row:
                if isinstance(t, dict) and t.get("consecutive_unfed", 0) >= 2:
                    starvation_events += 1

    r_us = float(env.steps[-1][our_player]["reward"] or 0)
    r_opp = float(env.steps[-1][opp_player]["reward"] or 0)
    margin = r_us - r_opp
    win = 1.0 if r_us > r_opp else (0.5 if r_us == r_opp else 0.0)

    market_prices = env.steps[264][0]["observation"].get("market", {}).get("prices", {})
    melon_price_264 = float(market_prices.get("MELON", 250))
    wheat_price_264 = float(market_prices.get("WHEAT", 25))

    return {
        "treatment": agent_key,
        "opponent": opp_key,
        "seed": seed,
        "swapped": swapped,
        "reward_us": r_us,
        "reward_opp": r_opp,
        "margin": margin,
        "win": win,
        "elapsed": elapsed,
        "starvation_events": starvation_events,
        "min_feed_seen": min_feed_seen,
        "melon_price_264": melon_price_264,
        "wheat_price_264": wheat_price_264,
        "telemetry": cp_telemetry
    }

# ---------------------------------------------------------------------------
# 4. Detailed Telemetry Extractor (Phase 5 & 6)
# ---------------------------------------------------------------------------
def run_detailed_telemetry(seed=42):
    """Extracts step-by-step telemetry for Treatment A vs Treatment H."""
    print(f"Extracting turn-by-turn Day 1-11 micro-telemetry on seed {seed}...")
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env.run([agent_H_full_jit_pipeline, v2.agent])
    
    # Player 0 = H, Player 1 = V2 (A)
    steps_data = []
    for s in range(0, 271):
        step_entry = env.steps[s]
        
        # H (P0)
        f_h = step_entry[0]["observation"]["farms"][0]
        priv_h = step_entry[0]["observation"]["private"]
        act_h = step_entry[0].get("action", {})
        mkt_h = act_h.get("market", []) if isinstance(act_h, dict) else []
        
        # V2 (P1)
        f_v2 = step_entry[1]["observation"]["farms"][1]
        priv_v2 = step_entry[1]["observation"]["private"]
        act_v2 = step_entry[1].get("action", {})
        mkt_v2 = act_v2.get("market", []) if isinstance(act_v2, dict) else []
        
        # Count crops
        h_melons_field = sum(1 for row in f_h.get("tiles", []) for t in row if isinstance(t, dict) and t.get("crop") == "MELON")
        v2_melons_field = sum(1 for row in f_v2.get("tiles", []) for t in row if isinstance(t, dict) and t.get("crop") == "MELON")
        
        steps_data.append({
            "step": s,
            "day": s // 24,
            "hour": s % 24,
            "h_cash": float(f_h.get("money", 0)),
            "v2_cash": float(f_v2.get("money", 0)),
            "h_melon_shed": int(priv_h.get("shed", {}).get("MELON", 0)),
            "v2_melon_shed": int(priv_v2.get("shed", {}).get("MELON", 0)),
            "h_wheat_shed": int(priv_h.get("shed", {}).get("WHEAT", 0)),
            "v2_wheat_shed": int(priv_v2.get("shed", {}).get("WHEAT", 0)),
            "h_melons_field": h_melons_field,
            "v2_melons_field": v2_melons_field,
            "h_mkt": mkt_h,
            "v2_mkt": mkt_v2
        })
    return steps_data

# ---------------------------------------------------------------------------
# 5. Factorial ANOVA & Interaction Analysis
# ---------------------------------------------------------------------------
def compute_factorial_effects(factorial_results):
    """Decomposes the 2x2x2 factorial results into main effects and interactions."""
    # Group by treatment key
    scores = {}
    margins = {}
    for r in factorial_results:
        t = r["treatment"]
        scores.setdefault(t, []).append(r["reward_us"])
        margins.setdefault(t, []).append(r["margin"])
    
    means = {t: np.mean(scores[t]) for t in scores}
    mean_margins = {t: np.mean(margins[t]) for t in margins}
    
    # 2x2x2 design:
    # W: Workers (0 = V2 2-worker staggered, 1 = 5-worker Day 0)
    # M: Melons (0 = 7 melons, 1 = 12 melons)
    # F: Feed (0 = 17 feed hoard, 1 = 2 feed JIT)
    # A = (0, 0, 0)
    # B = (1, 0, 0)
    # C = (0, 1, 0)
    # D = (0, 0, 1)
    # E = (1, 1, 0)
    # F = (1, 0, 1)
    # G = (0, 1, 1)
    # H = (1, 1, 1)
    
    yA = means["A"]
    yB = means["B"]
    yC = means["C"]
    yD = means["D"]
    yE = means["E"]
    yF = means["F"]
    yG = means["G"]
    yH = means["H"]
    
    # Main effects
    w_main = ((yB + yE + yF + yH) - (yA + yC + yD + yG)) / 4.0
    m_main = ((yC + yE + yG + yH) - (yA + yB + yD + yF)) / 4.0
    f_main = ((yD + yF + yG + yH) - (yA + yB + yC + yE)) / 4.0
    
    # Two-way interactions
    wm_int = ((yH + yE + yA + yD) - (yB + yF + yC + yG)) / 4.0
    wf_int = ((yH + yF + yA + yC) - (yB + yE + yD + yG)) / 4.0
    mf_int = ((yH + yG + yA + yB) - (yC + yE + yD + yF)) / 4.0
    
    # Three-way interaction
    wmf_int = ((yH + yF + yC + yB) - (yE + yG + yD + yA)) / 4.0
    
    return {
        "treatment_means": means,
        "treatment_margins": mean_margins,
        "worker_main_effect": w_main,
        "melon_main_effect": m_main,
        "feed_main_effect": f_main,
        "worker_x_melon": wm_int,
        "worker_x_feed": wf_int,
        "melon_x_feed": mf_int,
        "three_way_interaction": wmf_int
    }

# ---------------------------------------------------------------------------
# 6. Main Execution Logic
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["smoke", "micro", "factorial", "dev_tournament", "holdout", "full"], default="full")
    parser.add_argument("--workers", type=int, default=10)
    args = parser.parse_args()

    out_dir = os.path.join(PROJECT_ROOT, "scratch", "jit_melon_results")
    os.makedirs(out_dir, exist_ok=True)

    print(f"============================================================")
    print(f"V2 DAY-0 JUST-IN-TIME MELON PIPELINE CAUSAL STUDY")
    print(f"Execution Mode: {args.mode} | Worker Threads: {args.workers}")
    print(f"============================================================")

    # 1. Micro-telemetry & Day 10-11 Liquidity Checkpoint
    if args.mode in ("micro", "full"):
        print("\n>>> PHASE 5 & 6: RUNNING DAY 1-11 MICRO-TELEMETRY...")
        telemetry_42 = run_detailed_telemetry(seed=42)
        telemetry_100 = run_detailed_telemetry(seed=100)
        with open(os.path.join(out_dir, "micro_telemetry_seed42.json"), "w") as f:
            json.dump(telemetry_42, f, indent=2)
        with open(os.path.join(out_dir, "micro_telemetry_seed100.json"), "w") as f:
            json.dump(telemetry_100, f, indent=2)
        print("Micro-telemetry exported successfully.")

    # 2. Factorial Experiment (A through H across 25 paired seeds = 50 games per treatment = 400 games)
    factorial_data = []
    if args.mode in ("factorial", "full"):
        print("\n>>> PHASE 2 & 9: RUNNING FACTORIAL TOURNAMENT (A through H across 25 paired seeds = 400 matches)...")
        tasks = []
        fact_seeds = list(range(1001, 1026)) # 25 seeds
        for t_key in TREATMENT_MAP.keys():
            for s in fact_seeds:
                tasks.append((t_key, "v2", s, False))
                tasks.append((t_key, "v2", s, True))
        
        print(f"Total factorial games to run: {len(tasks)}")
        t_start = time.time()
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            futures = {executor.submit(run_single_game, item): item for item in tasks}
            for fut in as_completed(futures):
                factorial_data.append(fut.result())
        
        print(f"Factorial completed in {time.time() - t_start:.1f}s.")
        with open(os.path.join(out_dir, "factorial_raw_results.json"), "w") as f:
            json.dump(factorial_data, f, indent=2)
            
        fact_effects = compute_factorial_effects(factorial_data)
        with open(os.path.join(out_dir, "factorial_effects.json"), "w") as f:
            json.dump(fact_effects, f, indent=2)
        print("Factorial effects computed and saved.")

    # 3. Matched Development Tournament (A vs H across 250 paired seeds = 500 games against V2, plus LiveFlooder & Starter)
    dev_results = []
    if args.mode in ("dev_tournament", "full"):
        print("\n>>> PHASE 8: RUNNING MATCHED-SEED DEVELOPMENT TOURNAMENT (500 Matched Games)...")
        tasks = []
        dev_seeds = list(range(2001, 2251)) # 250 seeds * 2 seats = 500 games vs V2
        for s in dev_seeds:
            # Treatment H vs V2 (Seat 0 & Seat 1)
            tasks.append(("H", "v2", s, False))
            tasks.append(("H", "v2", s, True))
            # Treatment A vs V2 (Control Seat 0 & Seat 1)
            tasks.append(("A", "v2", s, False))
            tasks.append(("A", "v2", s, True))
            
        print(f"Total development games to run: {len(tasks)}")
        t_start = time.time()
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            futures = {executor.submit(run_single_game, item): item for item in tasks}
            for fut in as_completed(futures):
                dev_results.append(fut.result())
                
        print(f"Dev tournament completed in {time.time() - t_start:.1f}s.")
        with open(os.path.join(out_dir, "dev_tournament_results.json"), "w") as f:
            json.dump(dev_results, f, indent=2)
        print("Development tournament results saved.")

    # 4. Unseen Holdout Suite (300 unseen games: Seeds 7000-7149 * 2 seats = 300 games vs V2)
    holdout_results = []
    if args.mode in ("holdout", "full"):
        print("\n>>> PHASE 13: RUNNING UNSEEN HOLDOUT VALIDATION (300 Unseen Games: Seeds 7000-7149)...")
        tasks = []
        holdout_seeds = list(range(7000, 7150)) # 150 seeds * 2 seats = 300 games
        for s in holdout_seeds:
            tasks.append(("H", "v2", s, False))
            tasks.append(("H", "v2", s, True))
            tasks.append(("A", "v2", s, False))
            tasks.append(("A", "v2", s, True))
            
        print(f"Total holdout games to run: {len(tasks)}")
        t_start = time.time()
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            futures = {executor.submit(run_single_game, item): item for item in tasks}
            for fut in as_completed(futures):
                holdout_results.append(fut.result())
                
        print(f"Holdout completed in {time.time() - t_start:.1f}s.")
        with open(os.path.join(out_dir, "holdout_results.json"), "w") as f:
            json.dump(holdout_results, f, indent=2)
        print("Holdout results saved.")

    print("\n============================================================")
    print("ALL CAUSAL EXPERIMENTAL SUITES FINISHED SUCCESSFULLY.")
    print("============================================================")
