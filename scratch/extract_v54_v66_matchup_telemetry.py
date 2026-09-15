"""
Step 4 & 5: Matchup Telemetry & Causal Divergence Engine
======================================================
Runs 80 symmetric matches:
  - 20 common seeds (101-120) x 2 seats
  - 20 fresh seeds (201-220) x 2 seats
Between canonical V54 and canonical V66.

Extracts:
  - V54 reward, V66 reward, delta
  - Commodity quantities: wheat, strawberry, milk, wool, fertilizer, melon, carrot
  - Cash milestones: Day 5 (step 120), Day 10 (step 240), Day 15 (step 360),
                    Day 20 (step 480), Day 25 (step 600), terminal cash (step 719)
  - First action divergence, first state divergence, first economic divergence
  - Saves full telemetry and causal divergence trace to:
    research/v54_v66_matchup_telemetry.json
    research/v54_v66_first_causal_divergence.json
"""

import os
import sys
import time
import json
import numpy as np
from concurrent.futures import ProcessPoolExecutor
from kaggle_environments import make

V54_PATH = os.path.abspath("external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py")
V66_PATH = os.path.abspath("external_repos/kaggriculture-v66-agent/main.py")

SEEDS = list(range(101, 121)) + list(range(201, 221))  # 40 seeds

import importlib.util
def load_agent(agent_name):
    path = V54_PATH if agent_name == "V54" else V66_PATH
    d = os.path.dirname(path)
    if d not in sys.path:
        sys.path.insert(0, d)
    spec = importlib.util.spec_from_file_location(f"mod_{agent_name}_{os.getpid()}_{time.time_ns()}", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod.agent

def run_telemetry_match(task):
    seed, p0_name, p1_name = task
    agent0 = load_agent(p0_name)
    agent1 = load_agent(p1_name)

    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.reset()

    # Trackers
    cash_milestones = {
        0: {}, 1: {}
    }
    commodities_sold = {
        0: {"WHEAT": 0, "STRAWBERRY": 0, "MILK": 0, "WOOL": 0, "FERTILIZER": 0, "MELON": 0, "CARROT": 0},
        1: {"WHEAT": 0, "STRAWBERRY": 0, "MILK": 0, "WOOL": 0, "FERTILIZER": 0, "MELON": 0, "CARROT": 0}
    }

    first_action_div = None
    first_state_div = None
    first_econ_div = None

    milestone_steps = [120, 240, 360, 480, 600, 718]

    for step in range(719):
        obs0 = env.state[0].observation
        obs1 = env.state[1].observation

        # Inject step as done by Kaggle env.run harness
        obs0["step"] = step
        obs1["step"] = step

        farm0 = obs0.farms[0]
        farm1 = obs1.farms[1]

        # Record cash milestones
        if step in milestone_steps:
            day_label = f"Day_{step // 24}"
            cash_milestones[0][day_label] = float(farm0.get("money", 0))
            cash_milestones[1][day_label] = float(farm1.get("money", 0))

        # Check state divergence between farm0 and farm1
        if first_state_div is None and step > 0:
            money_diff = abs(float(farm0.get("money", 0)) - float(farm1.get("money", 0)))
            hands_diff = len(farm0.get("hands", [])) != len(farm1.get("hands", []))
            if money_diff > 5 or hands_diff:
                first_state_div = {
                    "step": step,
                    "day": step // 24,
                    "hour": step % 24,
                    "farm0_money": float(farm0.get("money", 0)),
                    "farm1_money": float(farm1.get("money", 0)),
                    "farm0_hands": len(farm0.get("hands", [])),
                    "farm1_hands": len(farm1.get("hands", [])),
                    "reason": f"Money diff: ${money_diff:.0f}, Hands diff: {hands_diff}"
                }

        if first_econ_div is None and step > 0:
            money_diff = abs(float(farm0.get("money", 0)) - float(farm1.get("money", 0)))
            if money_diff >= 100:
                first_econ_div = {
                    "step": step,
                    "day": step // 24,
                    "hour": step % 24,
                    "farm0_money": float(farm0.get("money", 0)),
                    "farm1_money": float(farm1.get("money", 0)),
                    "delta": money_diff
                }

        act0 = agent0(obs0, env.configuration)
        act1 = agent1(obs1, env.configuration)

        # Check action divergence
        if first_action_div is None:
            m0 = act0.get("market", [])
            m1 = act1.get("market", [])
            f0 = act0.get("farmer", ["PASS"])
            f1 = act1.get("farmer", ["PASS"])
            if m0 != m1 or f0 != f1:
                first_action_div = {
                    "step": step,
                    "day": step // 24,
                    "hour": step % 24,
                    "p0_market": m0,
                    "p1_market": m1,
                    "p0_farmer": f0,
                    "p1_farmer": f1
                }

        # Track sales
        for player_idx, act in [(0, act0), (1, act1)]:
            for m in act.get("market", []):
                if m and m[0] == "SELL" and len(m) > 2:
                    item, qty = m[1], m[2]
                    if item in commodities_sold[player_idx]:
                        commodities_sold[player_idx][item] += qty

        env.step([act0, act1])

    final_r0 = float(env.steps[-1][0].reward or 0.0)
    final_r1 = float(env.steps[-1][1].reward or 0.0)
    cash_milestones[0]["Terminal"] = final_r0
    cash_milestones[1]["Terminal"] = final_r1

    if p0_name == "V54":
        v54_seat = 0
        v66_seat = 1
        v54_rew = final_r0
        v66_rew = final_r1
    else:
        v54_seat = 1
        v66_seat = 0
        v54_rew = final_r1
        v66_rew = final_r0

    return {
        "seed": seed,
        "v54_seat": v54_seat,
        "v66_seat": v66_seat,
        "v54_reward": v54_rew,
        "v66_reward": v66_rew,
        "delta": v66_rew - v54_rew,
        "v54_cash": cash_milestones[v54_seat],
        "v66_cash": cash_milestones[v66_seat],
        "v54_commodities": commodities_sold[v54_seat],
        "v66_commodities": commodities_sold[v66_seat],
        "first_action_divergence": first_action_div,
        "first_state_divergence": first_state_div,
        "first_economic_divergence": first_econ_div
    }

def main():
    print("Running 80 symmetric telemetry matches between V54 and V66...")
    tasks = []
    for s in SEEDS:
        tasks.append((s, "V54", "V66"))
        tasks.append((s, "V66", "V54"))

    t0 = time.time()
    results = []
    with ProcessPoolExecutor(max_workers=8) as pool:
        for res in pool.map(run_telemetry_match, tasks):
            results.append(res)
            print(f"Seed {res['seed']:3d} | Seat {res['v66_seat']} | V54: ${res['v54_reward']:>9,.0f} | V66: ${res['v66_reward']:>9,.0f} | Margin: {res['delta']:>+8,.0f}", flush=True)

    elapsed = time.time() - t0
    print(f"\nAll 80 telemetry matches completed in {elapsed:.1f}s.")

    # Aggregate Cash Milestones
    milestone_keys = ["Day_5", "Day_10", "Day_15", "Day_20", "Day_25", "Terminal"]
    cash_means_v54 = {k: np.mean([r["v54_cash"].get(k, 0) for r in results]) for k in milestone_keys}
    cash_means_v66 = {k: np.mean([r["v66_cash"].get(k, 0) for r in results]) for k in milestone_keys}
    cash_deltas = {k: cash_means_v66[k] - cash_means_v54[k] for k in milestone_keys}

    # Aggregate Commodity Sales
    comm_keys = ["WHEAT", "STRAWBERRY", "MILK", "WOOL", "FERTILIZER", "MELON", "CARROT"]
    comm_means_v54 = {c: np.mean([r["v54_commodities"].get(c, 0) for r in results]) for c in comm_keys}
    comm_means_v66 = {c: np.mean([r["v66_commodities"].get(c, 0) for r in results]) for c in comm_keys}
    comm_deltas = {c: comm_means_v66[c] - comm_means_v54[c] for c in comm_keys}

    print("\n" + "=" * 70)
    print("MATCHUP CASH MILESTONES (80 SYMMETRIC MATCHES)")
    print("=" * 70)
    print(f"{'Milestone':<12} | {'V54 Mean Cash':<15} | {'V66 Mean Cash':<15} | {'Delta (V66 - V54)':<18}")
    print("-" * 70)
    for k in milestone_keys:
        print(f"{k:<12} | ${cash_means_v54[k]:<14,.0f} | ${cash_means_v66[k]:<14,.0f} | ${cash_deltas[k]:>+14,.0f}")

    print("\n" + "=" * 70)
    print("COMMODITY SALES DELTAS (80 SYMMETRIC MATCHES)")
    print("=" * 70)
    print(f"{'Commodity':<15} | {'V54 Mean Sold':<15} | {'V66 Mean Sold':<15} | {'Delta (V66 - V54)':<18}")
    print("-" * 70)
    for c in comm_keys:
        print(f"{c:<15} | {comm_means_v54[c]:<14.1f} | {comm_means_v66[c]:<14.1f} | {comm_deltas[c]:>+14.1f}")

    # First Divergences
    act_divs = [r["first_action_divergence"]["step"] for r in results if r["first_action_divergence"]]
    state_divs = [r["first_state_divergence"]["step"] for r in results if r["first_state_divergence"]]
    econ_divs = [r["first_economic_divergence"]["step"] for r in results if r["first_economic_divergence"]]

    first_div_summary = {
        "first_action_step": int(np.min(act_divs)) if act_divs else 0,
        "first_state_step": int(np.min(state_divs)) if state_divs else 0,
        "first_econ_step": int(np.min(econ_divs)) if econ_divs else 0,
        "first_action_example": results[0]["first_action_divergence"],
        "first_state_example": results[0]["first_state_divergence"],
        "first_econ_example": results[0]["first_economic_divergence"]
    }

    print("\n" + "=" * 70)
    print("EARLIEST CAUSAL DIVERGENCE")
    print("=" * 70)
    print(f"First Action Divergence: Step {first_div_summary['first_action_step']} (Day {first_div_summary['first_action_step']//24}, Hour {first_div_summary['first_action_step']%24})")
    print(f"First State Divergence:  Step {first_div_summary['first_state_step']} (Day {first_div_summary['first_state_step']//24}, Hour {first_div_summary['first_state_step']%24})")
    print(f"First Econ Divergence:   Step {first_div_summary['first_econ_step']} (Day {first_div_summary['first_econ_step']//24}, Hour {first_div_summary['first_econ_step']%24})")

    out_telemetry = {
        "cash_means_v54": cash_means_v54,
        "cash_means_v66": cash_means_v66,
        "cash_deltas": cash_deltas,
        "comm_means_v54": comm_means_v54,
        "comm_means_v66": comm_means_v66,
        "comm_deltas": comm_deltas,
        "first_divergences": first_div_summary,
        "raw_matches": results
    }

    os.makedirs("research", exist_ok=True)
    with open("research/v54_v66_matchup_telemetry.json", "w", encoding="utf-8") as f:
        json.dump(out_telemetry, f, indent=2)

    print("\nSaved research/v54_v66_matchup_telemetry.json")

if __name__ == "__main__":
    main()
