"""
Comprehensive Temporal Telemetry Evaluator for Kaggriculture
Measures:
- reward
- productive actions
- movement actions
- idle actions
- mean movement leg
- % 1-step legs
- % <=2-step legs
- worker assignment changes / commitment drops
- zone transitions
- shed round-trips
- productive actions per movement action
"""

import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
from collections import defaultdict, Counter
import numpy as np

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

def run_telemetry_match(agent_fn, seed=42, opponent="starter"):
    worker_history = defaultdict(list)
    final_reward = 0.0

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
    steps = env.run([wrapped_agent, opponent])
    final_reward = steps[-1][0]["reward"] or 0.0

    # Aggregate telemetry
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

            # Zone transitions
            if r["zone"] != cur_zone:
                total_zone_changes += 1
                cur_zone = r["zone"]

            # Shed returns
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
        "zone_transitions": total_zone_changes,
        "zone_per_w_day": zone_per_w_day,
        "shed_returns": total_shed_returns,
        "shed_per_w_day": shed_per_w_day,
        "prod_per_move": prod_per_move
    }

def run_suite(agent_fn, seeds, name="Agent"):
    results = []
    print(f"Profiling {name} across {len(seeds)} seeds...")
    for s in seeds:
        res = run_telemetry_match(agent_fn, seed=s)
        results.append(res)
    
    rewards = [r["reward"] for r in results]
    prods = [r["productive"] for r in results]
    moves = [r["movement"] for r in results]
    idles = [r["idle"] for r in results]
    mean_legs = [r["mean_leg"] for r in results]
    pct_1s = [r["pct_1step"] for r in results]
    pct_2s = [r["pct_2step"] for r in results]
    zones = [r["zone_per_w_day"] for r in results]
    sheds = [r["shed_per_w_day"] for r in results]
    prod_moves = [r["prod_per_move"] for r in results]

    summary = {
        "name": name,
        "N": len(seeds),
        "mean_reward": float(np.mean(rewards)),
        "std_reward": float(np.std(rewards)),
        "mean_prod": float(np.mean(prods)),
        "mean_move": float(np.mean(moves)),
        "mean_idle": float(np.mean(idles)),
        "mean_leg": float(np.mean(mean_legs)),
        "mean_pct_1step": float(np.mean(pct_1s)),
        "mean_pct_2step": float(np.mean(pct_2s)),
        "mean_zone_per_w_day": float(np.mean(zones)),
        "mean_shed_per_w_day": float(np.mean(sheds)),
        "mean_prod_per_move": float(np.mean(prod_moves)),
    }
    print(f"--- Summary for {name} (N={len(seeds)}) ---")
    print(f"Reward:     {summary['mean_reward']:.1f} +/- {summary['std_reward']:.1f}")
    print(f"Productive: {summary['mean_prod']:.1f} | Movement: {summary['mean_move']:.1f} | Idle: {summary['mean_idle']:.1f}")
    print(f"Mean Leg:   {summary['mean_leg']:.2f} | 1-step%: {summary['mean_pct_1step']:.1f}% | <=2-step%: {summary['mean_pct_2step']:.1f}%")
    print(f"Zone/w/day: {summary['mean_zone_per_w_day']:.2f} | Shed/w/day: {summary['mean_shed_per_w_day']:.2f} | Prod/Move: {summary['mean_prod_per_move']:.3f}")
    return summary, results

if __name__ == "__main__":
    import candidates.slot2_aethel_refined_v2 as v2_mod
    from candidates.candidate_closed_loop_execution_v1 import agent as cl_v1_agent

    test_seeds = [42, 101, 215, 305, 412]
    run_suite(v2_mod.agent, test_seeds, name="Frozen V2")
    run_suite(cl_v1_agent, test_seeds, name="CL-Execution-V1")
