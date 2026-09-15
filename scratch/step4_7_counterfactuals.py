"""
Step 4-7: Morning Bottleneck Counterfactual Experiment Engine
============================================================
Compares 5 Variants across 30 identical seeds (101 to 130):
  A: Canonical V54 Baseline
  B: Oracle Morning Routing (Optimal task matching & shortest path during hours 0-3)
  C: Livestock Chores Removed (Morning livestock workload neutralized, upper bound)
  D: Strawberry Priority (1: feed, 2: care, 3: mature strawberry harvest, 4: strawberry water, 5: other)
  E: Movement-Only Optimization (Exact same V54 task choices, shortest path routing)

Measures for all 5 variants across all 30 seeds:
- Final Reward
- Strawberries Sold
- Wheat Sold
- Milk Sold
- Wool Sold
- Fertilizer Sold
- Total Movement Steps (First 4 hours & whole game)
- Productive Actions (First 4 hours & whole game)
- Unserved Urgent Tasks at Hour 4

Computes paired deltas vs Baseline A:
- B - A (Oracle Ceiling)
- C - A (Livestock Neutralization Ceiling)
- D - A (Strawberry Priority Delta)
- E - A (Movement-Only Delta)
With 95% Bootstrap Confidence Intervals.
"""

import os
import sys
import time
import json
import csv
import copy
import importlib.util
from collections import defaultdict
import numpy as np
from concurrent.futures import ProcessPoolExecutor

V54_PATH = os.path.abspath("external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py")
SEEDS = list(range(101, 131))  # 30 seeds

SHED_TILES_10 = [(4, 4), (4, 5), (5, 4), (5, 5)]
SHED_ACCESS_10 = [
    (3, 4), (3, 5), (4, 3), (4, 6), (5, 3), (5, 6), (6, 4), (6, 5)
]

def manhattan_dist(p1, p2):
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

def move_towards(cur_pos, target_pos, board_size, tiles):
    cx, cy = cur_pos
    tx, ty = target_pos
    if cx == tx and cy == ty:
        return "PASS"
    dx = tx - cx
    dy = ty - cy
    
    # Try horizontal first if dx != 0
    moves = []
    if dx > 0: moves.append(("EAST", (cx + 1, cy)))
    elif dx < 0: moves.append(("WEST", (cx - 1, cy)))
    if dy > 0: moves.append(("SOUTH", (cx, cy + 1)))
    elif dy < 0: moves.append(("NORTH", (cx, cy - 1)))

    for m_act, (nx, ny) in moves:
        if 0 <= nx < board_size and 0 <= ny < board_size:
            if tiles[ny][nx] != "LOCKED":
                return m_act
    return "PASS"

def load_canonical_v54():
    d = os.path.dirname(V54_PATH)
    if d not in sys.path:
        sys.path.insert(0, d)
    spec = importlib.util.spec_from_file_location(f"v54_cf_{os.getpid()}_{time.time_ns()}", V54_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod.agent

def run_counterfactual_match(task):
    seed, variant = task
    from kaggle_environments import make

    # Load canonical baseline agent for opponent and fallback
    v54_agent_p0 = load_canonical_v54()
    v54_agent_p1 = load_canonical_v54()

    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.reset()

    # Telemetry metrics
    total_movement_morn = 0
    total_prod_morn = 0
    total_movement_all = 0
    total_prod_all = 0
    unserved_h4_total = 0

    strawberries_sold = 0
    wheat_sold = 0
    milk_sold = 0
    wool_sold = 0
    fertilizer_sold = 0

    # For variant E tracking: target destination for each worker
    worker_targets_e = {}

    for step in range(719):
        obs0 = env.state[0].observation
        obs1 = env.state[1].observation
        farm0 = obs0.farms[0]
        priv0 = obs0.private
        tiles = farm0["tiles"]
        board_size = len(tiles)
        
        day = step // 24
        hour = step % 24
        is_morning = (hour < 4)

        farmer_pos = list(farm0["farmer"])
        hands_pos = [list(p) for p in farm0.get("hands", [])]
        all_workers = [farmer_pos] + hands_pos
        num_workers = len(all_workers)

        # Base action from canonical V54
        base_act0 = v54_agent_p0(obs0, env.configuration)
        act1 = v54_agent_p1(obs1, env.configuration)

        act0 = copy.deepcopy(base_act0)

        # If not morning (hour >= 4), execute canonical action
        if not is_morning:
            final_act0 = act0
        else:
            # Morning hours 0, 1, 2, 3
            if variant == "A":
                # Baseline canonical V54
                final_act0 = act0

            elif variant == "B":
                # ORACLE ROUTING:
                # Find all active chores on the farm
                # Match nearest workers to chores optimally, route along shortest path
                chores = []
                for y in range(board_size):
                    for x in range(board_size):
                        t = tiles[y][x]
                        if isinstance(t, dict):
                            if t.get("kind") == "PLANT":
                                if t.get("crop") == "STRAWBERRY" and t.get("yield_units", 0) > 0:
                                    chores.append({"pos": (x, y), "op": "HARVEST", "priority": 1})
                                elif not t.get("watered_today"):
                                    chores.append({"pos": (x, y), "op": "WATER", "priority": 3})
                            elif "animal" in t:
                                if not t.get("fed_today"):
                                    chores.append({"pos": (x, y), "op": "FEED", "priority": 0})
                                elif not t.get("cared_today"):
                                    chores.append({"pos": (x, y), "op": "CARE", "priority": 2})
                                elif t.get("yield_units", 0) > 0:
                                    chores.append({"pos": (x, y), "op": "HARVEST", "priority": 4})
                                elif t.get("fertilizer_available"):
                                    chores.append({"pos": (x, y), "op": "COLLECT_FERTILIZER", "priority": 5})

                # Sort chores by priority
                chores.sort(key=lambda c: c["priority"])

                # Assign workers greedily by closest distance
                assigned_workers = set()
                worker_actions = [["PASS"] for _ in range(num_workers)]
                for chore in chores:
                    cpos = chore["pos"]
                    cop = chore["op"]
                    # Find closest unassigned worker
                    best_w = None
                    best_d = 999
                    for w_idx in range(num_workers):
                        if w_idx not in assigned_workers:
                            wpos = all_workers[w_idx]
                            d = manhattan_dist(wpos, cpos)
                            if d < best_d:
                                best_d = d
                                best_w = w_idx
                    if best_w is not None:
                        assigned_workers.add(best_w)
                        wpos = all_workers[best_w]
                        if tuple(wpos) == cpos:
                            # Standing on chore tile: execute chore
                            # For FEED, check if worker has wheat; if not, need wheat
                            winv = priv0["inventories"][best_w] if best_w < len(priv0["inventories"]) else {}
                            if cop == "FEED" and winv.get("WHEAT", 0) <= 0:
                                # Needs wheat: route to shed access
                                s_tile = min(SHED_ACCESS_10, key=lambda s: manhattan_dist(wpos, s))
                                m = move_towards(wpos, s_tile, board_size, tiles)
                                worker_actions[best_w] = [m] if m != "PASS" else ["PICKUP", "WHEAT", 3]
                            else:
                                worker_actions[best_w] = [cop]
                        else:
                            # Move toward chore
                            m = move_towards(wpos, cpos, board_size, tiles)
                            worker_actions[best_w] = [m]

                # Any unassigned worker: fall back to canonical V54 action
                for w_idx in range(num_workers):
                    if w_idx not in assigned_workers:
                        if w_idx == 0:
                            worker_actions[w_idx] = act0.get("farmer", ["PASS"])
                        else:
                            h_idx = w_idx - 1
                            h_acts = act0.get("hands", [])
                            worker_actions[w_idx] = h_acts[h_idx] if h_idx < len(h_acts) else ["PASS"]

                final_act0 = {
                    "farmer": worker_actions[0],
                    "hands": worker_actions[1:],
                    "market": act0.get("market", [])
                }

            elif variant == "C":
                # LIVESTOCK CHORES REMOVED:
                # Animals are treated as already fed and cared for by diagnostic oracle
                for y in range(board_size):
                    for x in range(board_size):
                        t = tiles[y][x]
                        if isinstance(t, dict) and "animal" in t:
                            t["fed_today"] = True
                            t["cared_today"] = True

                # Workers only perform crop tasks (strawberries, watering) during morning
                # Any worker whose canonical action was a livestock task is redirected to mature strawberries or watering
                crop_chores = []
                for y in range(board_size):
                    for x in range(board_size):
                        t = tiles[y][x]
                        if isinstance(t, dict) and t.get("kind") == "PLANT":
                            if t.get("crop") == "STRAWBERRY" and t.get("yield_units", 0) > 0:
                                crop_chores.append({"pos": (x, y), "op": "HARVEST", "priority": 0})
                            elif not t.get("watered_today"):
                                crop_chores.append({"pos": (x, y), "op": "WATER", "priority": 1})

                worker_actions = [["PASS"] for _ in range(num_workers)]
                canon_acts = [act0.get("farmer", ["PASS"])] + act0.get("hands", [])
                while len(canon_acts) < num_workers:
                    canon_acts.append(["PASS"])

                for w_idx in range(num_workers):
                    c_act = canon_acts[w_idx]
                    op = c_act[0] if c_act else "PASS"
                    # If action is livestock chore (FEED, CARE, COLLECT_FERTILIZER, or HARVEST on animal)
                    wpos = all_workers[w_idx]
                    cur_tile = tiles[wpos[1]][wpos[0]] if 0 <= wpos[1] < board_size and 0 <= wpos[0] < board_size else None
                    is_animal_tile = isinstance(cur_tile, dict) and "animal" in cur_tile
                    
                    if op in ["FEED", "CARE", "COLLECT_FERTILIZER"] or (op == "HARVEST" and is_animal_tile):
                        # Reassign to nearest crop chore
                        if crop_chores:
                            # Pick closest crop chore
                            best_chore = min(crop_chores, key=lambda c: (c["priority"], manhattan_dist(wpos, c["pos"])))
                            if tuple(wpos) == best_chore["pos"]:
                                worker_actions[w_idx] = [best_chore["op"]]
                                crop_chores.remove(best_chore)
                            else:
                                m = move_towards(wpos, best_chore["pos"], board_size, tiles)
                                worker_actions[w_idx] = [m]
                        else:
                            worker_actions[w_idx] = ["PASS"]
                    else:
                        worker_actions[w_idx] = c_act

                final_act0 = {
                    "farmer": worker_actions[0],
                    "hands": worker_actions[1:],
                    "market": act0.get("market", [])
                }

            elif variant == "D":
                # STRAWBERRY-FIRST PRIORITY:
                # Priority: 1. Starvation feed, 2. Mandatory care, 3. Mature strawberry, 4. Strawberry water, 5. Other
                priority_tasks = []
                for y in range(board_size):
                    for x in range(board_size):
                        t = tiles[y][x]
                        if isinstance(t, dict):
                            if "animal" in t:
                                if not t.get("fed_today"):
                                    priority_tasks.append({"pos": (x, y), "op": "FEED", "prio": 1})
                                elif not t.get("cared_today"):
                                    priority_tasks.append({"pos": (x, y), "op": "CARE", "prio": 2})
                            elif t.get("kind") == "PLANT" and t.get("crop") == "STRAWBERRY":
                                if t.get("yield_units", 0) > 0:
                                    priority_tasks.append({"pos": (x, y), "op": "HARVEST", "prio": 3})
                                elif not t.get("watered_today"):
                                    priority_tasks.append({"pos": (x, y), "op": "WATER", "prio": 4})

                priority_tasks.sort(key=lambda x: x["prio"])
                assigned = set()
                worker_actions = [None] * num_workers
                for task_item in priority_tasks:
                    tpos = task_item["pos"]
                    top = task_item["op"]
                    # Find closest unassigned worker
                    best_w = None
                    best_d = 999
                    for w_idx in range(num_workers):
                        if w_idx not in assigned:
                            d = manhattan_dist(all_workers[w_idx], tpos)
                            if d < best_d:
                                best_d = d
                                best_w = w_idx
                    if best_w is not None:
                        assigned.add(best_w)
                        wpos = all_workers[best_w]
                        if tuple(wpos) == tpos:
                            worker_actions[best_w] = [top]
                        else:
                            m = move_towards(wpos, tpos, board_size, tiles)
                            worker_actions[best_w] = [m]

                # Fallback for remaining workers: canonical V54
                canon_acts = [act0.get("farmer", ["PASS"])] + act0.get("hands", [])
                while len(canon_acts) < num_workers:
                    canon_acts.append(["PASS"])
                for w_idx in range(num_workers):
                    if worker_actions[w_idx] is None:
                        worker_actions[w_idx] = canon_acts[w_idx]

                final_act0 = {
                    "farmer": worker_actions[0],
                    "hands": worker_actions[1:],
                    "market": act0.get("market", [])
                }

            elif variant == "E":
                # PURE MOVEMENT OPTIMIZATION:
                # Same exact V54 task choices, but optimize route between them (shortest path)
                # If canonical V54 planned a chore on a tile, move directly towards it
                canon_acts = [act0.get("farmer", ["PASS"])] + act0.get("hands", [])
                while len(canon_acts) < num_workers:
                    canon_acts.append(["PASS"])

                worker_actions = []
                for w_idx in range(num_workers):
                    c_act = canon_acts[w_idx]
                    op = c_act[0] if c_act else "PASS"
                    wpos = all_workers[w_idx]
                    
                    if op in ["NORTH", "SOUTH", "EAST", "WEST"]:
                        # Canonical is moving. If we have a known chore destination, move directly
                        target = worker_targets_e.get(w_idx)
                        if target and tuple(wpos) != target:
                            m = move_towards(wpos, target, board_size, tiles)
                            worker_actions.append([m])
                        else:
                            worker_actions.append(c_act)
                    else:
                        # Productive action or PASS: standing on chore tile
                        worker_targets_e[w_idx] = tuple(wpos)
                        worker_actions.append(c_act)

                final_act0 = {
                    "farmer": worker_actions[0],
                    "hands": worker_actions[1:],
                    "market": act0.get("market", [])
                }

        # Step environment
        env.step([final_act0, act1])

        # Track telemetry
        farmer_out = final_act0.get("farmer", ["PASS"])
        hands_out = final_act0.get("hands", [])
        all_acts = [farmer_out] + hands_out
        for a in all_acts:
            op = a[0] if a else "PASS"
            is_move = op in ["NORTH", "SOUTH", "EAST", "WEST"]
            is_prod = op not in ["NORTH", "SOUTH", "EAST", "WEST", "PASS"]
            if is_morning:
                if is_move: total_movement_morn += 1
                if is_prod: total_prod_morn += 1
            if is_move: total_movement_all += 1
            if is_prod: total_prod_all += 1

        # Track sales from market actions
        m_orders = final_act0.get("market", [])
        for order in m_orders:
            if order and order[0] == "SELL" and len(order) > 2:
                item = order[1]
                qty = order[2]
                if item == "STRAWBERRY": strawberries_sold += qty
                elif item == "WHEAT": wheat_sold += qty
                elif item == "MILK": milk_sold += qty
                elif item == "WOOL": wool_sold += qty
                elif item == "FERTILIZER": fertilizer_sold += qty

        # Hour 4 unserved count
        if hour == 4:
            for y in range(board_size):
                for x in range(board_size):
                    t = tiles[y][x]
                    if isinstance(t, dict):
                        if t.get("kind") == "PLANT":
                            if t.get("crop") == "STRAWBERRY" and t.get("yield_units", 0) > 0:
                                unserved_h4_total += t.get("yield_units", 0)
                            if not t.get("watered_today"):
                                unserved_h4_total += 1
                        elif "animal" in t:
                            if not t.get("fed_today"): unserved_h4_total += 1
                            if not t.get("cared_today"): unserved_h4_total += 1

    final_reward = float(env.steps[-1][0].reward or 0.0)

    return {
        "seed": seed,
        "variant": variant,
        "reward": final_reward,
        "strawberries_sold": strawberries_sold,
        "wheat_sold": wheat_sold,
        "milk_sold": milk_sold,
        "wool_sold": wool_sold,
        "fertilizer_sold": fertilizer_sold,
        "movement_morning": total_movement_morn,
        "productive_morning": total_prod_morn,
        "movement_total": total_movement_all,
        "productive_total": total_prod_all,
        "unserved_h4_total": unserved_h4_total
    }

def bootstrap_ci_paired(deltas, num_samples=10000, alpha=0.05):
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
    print("STEPS 4-7: COUNTERFACTUAL CEILING EXPERIMENTS (30 COMMON SEEDS)")
    print("Variants: A (Baseline V54), B (Oracle Routing), C (Livestock Chores Removed),")
    print("          D (Strawberry Priority), E (Movement-Only Optimization)")
    print("=" * 80, flush=True)

    tasks = []
    for var in ["A", "B", "C", "D", "E"]:
        for s in SEEDS:
            tasks.append((s, var))

    t0 = time.time()
    results_by_var = defaultdict(list)
    with ProcessPoolExecutor(max_workers=8) as pool:
        for res in pool.map(run_counterfactual_match, tasks):
            results_by_var[res["variant"]].append(res)
            print(f"[{res['variant']}] Seed {res['seed']} | Reward: ${res['reward']:,.0f} | Strawb: {res['strawberries_sold']} | Milk: {res['milk_sold']} | MvMorn: {res['movement_morning']}", flush=True)

    elapsed = time.time() - t0
    print(f"\nAll 150 counterfactual simulations completed in {elapsed:.1f}s.")

    # Sort each variant list by seed
    for v in results_by_var:
        results_by_var[v].sort(key=lambda x: x["seed"])

    baseline_A = results_by_var["A"]

    # Compute comparison table
    summary_table = {}
    for var in ["A", "B", "C", "D", "E"]:
        v_list = results_by_var[var]
        rews = [r["reward"] for r in v_list]
        strawb = [r["strawberries_sold"] for r in v_list]
        wheat = [r["wheat_sold"] for r in v_list]
        milk = [r["milk_sold"] for r in v_list]
        wool = [r["wool_sold"] for r in v_list]
        fert = [r["fertilizer_sold"] for r in v_list]
        morn_mov = [r["movement_morning"] for r in v_list]
        morn_prod = [r["productive_morning"] for r in v_list]
        unserved = [r["unserved_h4_total"] for r in v_list]

        summary_table[var] = {
            "reward_mean": float(np.mean(rews)),
            "reward_median": float(np.median(rews)),
            "strawberries_sold_mean": float(np.mean(strawb)),
            "wheat_sold_mean": float(np.mean(wheat)),
            "milk_sold_mean": float(np.mean(milk)),
            "wool_sold_mean": float(np.mean(wool)),
            "fertilizer_sold_mean": float(np.mean(fert)),
            "morn_movement_mean": float(np.mean(morn_mov)),
            "morn_productive_mean": float(np.mean(morn_prod)),
            "unserved_h4_mean": float(np.mean(unserved))
        }

    # Compute paired deltas vs Baseline A
    deltas = {}
    for var in ["B", "C", "D", "E"]:
        v_list = results_by_var[var]
        rew_deltas = [v_list[i]["reward"] - baseline_A[i]["reward"] for i in range(len(SEEDS))]
        strawb_deltas = [v_list[i]["strawberries_sold"] - baseline_A[i]["strawberries_sold"] for i in range(len(SEEDS))]
        ci_low, ci_high = bootstrap_ci_paired(rew_deltas)

        deltas[f"{var} - A"] = {
            "reward_delta_mean": float(np.mean(rew_deltas)),
            "reward_delta_median": float(np.median(rew_deltas)),
            "bootstrap_ci_95": (ci_low, ci_high),
            "strawb_delta_mean": float(np.mean(strawb_deltas)),
            "wins": sum(1 for d in rew_deltas if d > 0),
            "ties": sum(1 for d in rew_deltas if d == 0),
            "losses": sum(1 for d in rew_deltas if d < 0)
        }

    print("\n" + "=" * 80)
    print("COUNTERFACTUAL CEILING COMPARISON TABLE (SECTION 8)")
    print("=" * 80)
    print(f"{'Variant':<25} | {'Reward':<12} | {'Strawb':<8} | {'Wheat':<8} | {'Milk':<6} | {'Wool':<6} | {'MornMov':<8} | {'MornProd':<8} | {'Unserved':<8}")
    print("-" * 105)
    names = {
        "A": "A (Baseline V54)",
        "B": "B (Oracle Routing)",
        "C": "C (Livestock Chores Off)",
        "D": "D (Strawberry Priority)",
        "E": "E (Movement-Only Opt)"
    }
    for var in ["A", "B", "C", "D", "E"]:
        s = summary_table[var]
        print(f"{names[var]:<25} | ${s['reward_mean']:<11,.0f} | {s['strawberries_sold_mean']:<8.1f} | {s['wheat_sold_mean']:<8.1f} | {s['milk_sold_mean']:<6.1f} | {s['wool_sold_mean']:<6.1f} | {s['morn_movement_mean']:<8.1f} | {s['morn_productive_mean']:<8.1f} | {s['unserved_h4_mean']:<8.1f}")

    print("\n" + "=" * 80)
    print("PAIRED DELTAS VS BASELINE A (WITH 95% BOOTSTRAP CI)")
    print("=" * 80)
    for comp, d in deltas.items():
        print(f"{comp:12s} | Delta Reward: ${d['reward_delta_mean']:+,.2f} [95% CI: ${d['bootstrap_ci_95'][0]:+,.2f}, ${d['bootstrap_ci_95'][1]:+,.2f}] | Strawb Delta: {d['strawb_delta_mean']:+.1f} | Record: {d['wins']}W / {d['ties']}T / {d['losses']}L")

    # Save complete results
    out_all = {
        "summary_table": summary_table,
        "deltas": deltas,
        "raw_results": results_by_var
    }
    with open("scratch/step4_7_counterfactuals_summary.json", "w", encoding="utf-8") as f:
        json.dump(out_all, f, indent=2)

    print("\nResults saved to scratch/step4_7_counterfactuals_summary.json")

if __name__ == "__main__":
    main()
