"""
Phase 2 Causal Study: Evaluating Arms A through G across N=100 Matched Seeds
=============================================================================
Arms:
Arm A: Frozen V2
Arm B: Existing CL-Execution-V1
Arm C: CL-V1 + Persistent Worker Commitments
Arm D: Arm C + Zone Ownership (Z2)
Arm E: Arm D + Short-Horizon Lookahead (H10)
Arm F: Arm E + Event-Triggered Replanning
Arm G: Best Combined Architecture (CL-Commitment-V1)
"""

import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
from collections import defaultdict
import numpy as np
import json
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

BOARD = 10
SHED_ACCESS = frozenset([(4, 4), (5, 4), (4, 5), (5, 5)])
MOVES = {"NORTH", "SOUTH", "EAST", "WEST"}
PROD_ACTIONS = {
    "PLANT", "WATER", "HARVEST", "FEED", "CARE",
    "COLLECT_FERTILIZER", "FERTILIZE", "BUILD_PASTURE",
    "PLACE", "PICKUP", "DROP", "DIG"
}

def get_quad(pos):
    x, y = pos
    if x < 5 and y < 5: return "NW"
    if x >= 5 and y < 5: return "NE"
    if x < 5 and y >= 5: return "SW"
    return "SE"

def _run_single_match(agent_module_name, agent_attr_name, seed):
    # Dynamically import agent inside child process
    import importlib
    mod = importlib.import_module(agent_module_name)
    agent_fn = getattr(mod, agent_attr_name)

    worker_history = defaultdict(list)
    def wrapped_agent(obs, config=None):
        step = int(obs.get("step", 0) or 0)
        day = step // 24
        hour = step % 24
        p = int(obs.get("player", 0) or 0)
        farm = obs["farms"][p]
        farmer = tuple(farm["farmer"])
        hands = [tuple(h) for h in farm.get("hands", []) or []]
        workers = [farmer] + hands

        act = agent_fn(obs, config) if config else agent_fn(obs)
        f_act = act.get("farmer", ["PASS"])
        h_acts = act.get("hands", []) or []
        all_acts = [f_act] + [h_acts[i] if i < len(h_acts) else ["PASS"] for i in range(len(hands))]

        for w_i, (pos, a) in enumerate(zip(workers, all_acts)):
            op = a[0] if isinstance(a, list) and a else str(a)
            worker_history[w_i].append({
                "step": step, "day": day, "hour": hour, "pos": pos,
                "op": op, "zone": get_quad(pos), "in_shed": pos in SHED_ACCESS
            })
        return act

    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    steps = env.run([wrapped_agent, "starter"])
    final_reward = steps[-1][0]["reward"] or 0.0

    total_prod = 0
    total_move = 0
    total_idle = 0
    total_zone_changes = 0
    total_shed_returns = 0
    all_legs = []

    for w_i, records in worker_history.items():
        if not records: continue
        cur_leg = 0
        cur_zone = records[0]["zone"]
        was_in_shed = records[0]["in_shed"]

        for r in records:
            op = r["op"]
            if op in MOVES:
                total_move += 1
                cur_leg += 1
            elif op in PROD_ACTIONS:
                total_prod += 1
                if cur_leg > 0:
                    all_legs.append(cur_leg)
                    cur_leg = 0
            else:
                total_idle += 1
                if cur_leg > 0:
                    all_legs.append(cur_leg)
                    cur_leg = 0

            if r["zone"] != cur_zone:
                total_zone_changes += 1
                cur_zone = r["zone"]

            if r["in_shed"] and not was_in_shed:
                total_shed_returns += 1
            was_in_shed = r["in_shed"]

        if cur_leg > 0:
            all_legs.append(cur_leg)

    n_workers = max(1, len(worker_history))
    mean_leg = float(np.mean(all_legs)) if all_legs else 0.0
    pct_1step = float(sum(1 for l in all_legs if l == 1) / len(all_legs) * 100) if all_legs else 0.0
    pct_2step = float(sum(1 for l in all_legs if l <= 2) / len(all_legs) * 100) if all_legs else 0.0
    zone_per_w_day = total_zone_changes / 30.0 / n_workers
    shed_per_w_day = total_shed_returns / 30.0 / n_workers
    prod_per_move = total_prod / max(1, total_move)

    return {
        "seed": seed,
        "reward": final_reward,
        "productive": total_prod,
        "movement": total_move,
        "idle": total_idle,
        "mean_leg": mean_leg,
        "pct_1step": pct_1step,
        "pct_2step": pct_2step,
        "zone_per_w_day": zone_per_w_day,
        "shed_per_w_day": shed_per_w_day,
        "prod_per_move": prod_per_move
    }

ARMS = [
    ("Arm A (Frozen V2)", "candidates.slot2_aethel_refined_v2", "agent"),
    ("Arm B (CL-Execution-V1)", "candidates.candidate_closed_loop_execution_v1", "agent"),
    ("Arm C (CL-V1 + Commitment)", "scratch.test_arm_c", "arm_c_agent"),
    ("Arm D (C + Zone Ownership)", "scratch.test_arm_d", "arm_d_agent"),
    ("Arm E (D + Lookahead H10)", "scratch.test_arm_e_z", "arm_e_agent"),
    ("Arm F (E + Event Triggers)", "scratch.test_arm_f", "arm_f_agent"),
    ("Arm G (CL-Commitment-V1)", "candidates.candidate_closed_loop_commitment_v1", "agent"),
]

def run_causal_study(seeds, max_workers=8):
    os.makedirs("reports", exist_ok=True)
    study_results = {}
    print(f"=== Starting Phase 2 Causal Study: {len(ARMS)} Arms across N={len(seeds)} Seeds ===")
    t_start = time.time()

    for arm_name, mod_name, attr_name in ARMS:
        arm_t0 = time.time()
        print(f"\nEvaluating {arm_name} on {len(seeds)} seeds...")
        tasks = []
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            future_to_seed = {
                executor.submit(_run_single_match, mod_name, attr_name, s): s
                for s in seeds
            }
            results = []
            for future in as_completed(future_to_seed):
                res = future.result()
                results.append(res)

        rewards = [r["reward"] for r in results]
        prods = [r["productive"] for r in results]
        moves = [r["movement"] for r in results]
        idles = [r["idle"] for r in results]
        legs = [r["mean_leg"] for r in results]
        pct1s = [r["pct_1step"] for r in results]
        pct2s = [r["pct_2step"] for r in results]
        zones = [r["zone_per_w_day"] for r in results]
        sheds = [r["shed_per_w_day"] for r in results]
        prod_moves = [r["prod_per_move"] for r in results]

        summary = {
            "name": arm_name,
            "N": len(seeds),
            "mean_reward": float(np.mean(rewards)),
            "std_reward": float(np.std(rewards)),
            "mean_prod": float(np.mean(prods)),
            "mean_move": float(np.mean(moves)),
            "mean_idle": float(np.mean(idles)),
            "mean_leg": float(np.mean(legs)),
            "mean_pct_1step": float(np.mean(pct1s)),
            "mean_pct_2step": float(np.mean(pct2s)),
            "mean_zone_per_w_day": float(np.mean(zones)),
            "mean_shed_per_w_day": float(np.mean(sheds)),
            "mean_prod_per_move": float(np.mean(prod_moves)),
        }
        study_results[arm_name] = summary
        arm_elapsed = time.time() - arm_t0
        print(f"  Completed {arm_name} in {arm_elapsed:.1f}s:")
        print(f"    Reward:     {summary['mean_reward']:9.1f} +/- {summary['std_reward']:6.1f}")
        print(f"    Productive: {summary['mean_prod']:6.1f} | Moves: {summary['mean_move']:6.1f} | Idle: {summary['mean_idle']:6.1f}")
        print(f"    Mean Leg:   {summary['mean_leg']:6.2f} | 1-step%: {summary['mean_pct_1step']:5.1f}% | <=2-step%: {summary['mean_pct_2step']:5.1f}%")
        print(f"    Zone/w/day: {summary['mean_zone_per_w_day']:6.2f} | Shed/w/day: {summary['mean_shed_per_w_day']:6.2f} | Prod/Move: {summary['mean_prod_per_move']:5.3f}")

    total_elapsed = time.time() - t_start
    print(f"\n=== Full Causal Study Finished in {total_elapsed:.1f}s ===")

    # Save to json
    with open("reports/causal_study_results.json", "w") as f:
        json.dump(study_results, f, indent=2)

    # Print summary table
    print("\n" + "=" * 115)
    print(f"{'Arm':<28} | {'Reward':<16} | {'Prod':<6} | {'Move':<6} | {'Idle':<6} | {'MeanLeg':<7} | {'1-step%':<7} | {'Zone/w/d':<8} | {'Shed/w/d':<8}")
    print("=" * 115)
    for arm_name, s in study_results.items():
        print(f"{arm_name:<28} | {s['mean_reward']:8.1f} +/- {s['std_reward']:5.1f} | {s['mean_prod']:6.1f} | {s['mean_move']:6.1f} | {s['mean_idle']:6.1f} | {s['mean_leg']:7.2f} | {s['mean_pct_1step']:6.1f}% | {s['mean_zone_per_w_day']:8.2f} | {s['mean_shed_per_w_day']:8.2f}")
    print("=" * 115)

if __name__ == "__main__":
    study_seeds = list(range(1000, 1100))  # N=100 matched seeds
    run_causal_study(study_seeds, max_workers=8)
