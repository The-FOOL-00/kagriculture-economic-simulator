"""
Comprehensive Execution Script for Steps 1 through 5
===================================================
"""
import sys
import os
import copy
import json
import time
from collections import defaultdict, Counter
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import kaggle_environments
from candidates.candidate_cl_economic_v1 import ClosedLoopEconomicV1

BOARD = 10
TPD = 24
SHED_ACCESS = frozenset([(4, 4), (5, 4), (4, 5), (5, 5)])
WELL_ACCESS = frozenset([(4, 5), (5, 5), (4, 6), (5, 6)])

def _dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def _region(x, y):
    if (x, y) in SHED_ACCESS:
        return "SHED"
    if x < 5 and y < 5: return "NW"
    if x >= 5 and y < 5: return "NE"
    if x < 5 and y >= 5: return "SW"
    return "SE"

PRODUCTIVE_OPS = frozenset([
    "WATER", "HARVEST", "FEED", "CARE", "PLANT", "BUILD_PASTURE",
    "FERTILIZE", "COLLECT_FERTILIZER", "DIG", "DROP", "PICKUP", "PLACE"
])
MOVE_OPS = frozenset(["NORTH", "SOUTH", "EAST", "WEST"])

# ==============================================================================
# INSTRUMENTED AGENT FOR FORENSICS (SEED 1000)
# ==============================================================================
class InstrumentedClosedLoopEconomicV1(ClosedLoopEconomicV1):
    def __init__(self):
        super().__init__()
        self.step_snapshots = []

    def __call__(self, obs, config=None):
        # Capture pre-dispatch state
        raw_step = obs.get("step")
        step = int(raw_step) if raw_step is not None else 0
        day = int(obs.get("day", 0) or 0) if obs.get("day") is not None else step // TPD
        hour = int(obs.get("hour", 0) or 0) if obs.get("hour") is not None else step % TPD

        p = int(obs.get("player", 0) or 0)
        farms = obs.get("farms") or [{}, {}]
        farm = farms[p] if p < len(farms) else {}
        priv = obs.get("private") or {}
        shed = dict(priv.get("shed") or {})
        invs = list(priv.get("inventories") or [])
        tiles = farm.get("tiles") or []
        farmer_pos = tuple(farm.get("farmer") or [4, 4])
        hands_pos = [tuple(h) for h in (farm.get("hands") or [])]
        workers = [farmer_pos] + hands_pos
        money = float(farm.get("money") or 0)
        quads = farm.get("unlocked_quadrants") or ["NW"]

        # Call underlying policy
        action = super().__call__(obs, config)

        # Snapshot worker targets and state immediately after dispatch
        farmer_act = action.get("farmer") or ["PASS"]
        hands_act = action.get("hands") or []
        all_acts = [farmer_act] + hands_act

        targets_snapshot = copy.deepcopy(self._worker_targets)

        self.step_snapshots.append({
            "step": step,
            "day": day,
            "hour": hour,
            "workers": workers,
            "invs": invs,
            "shed": shed,
            "money": money,
            "quads": quads,
            "actions": all_acts,
            "targets": targets_snapshot,
            "tiles": copy.deepcopy(tiles)
        })

        return action


def run_seed_metrics(seed, agent_cls_factory=ClosedLoopEconomicV1):
    agent_inst = agent_cls_factory()
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg, debug=False)
    env.run([agent_inst, "starter"])

    steps = env.steps
    total_steps = len(steps)

    straw_harvested = 0
    wool_harvested = 0
    wheat_harvested = 0
    milk_harvested = 0
    feed_bought = 0
    fertilizer_applied = 0
    fertilizer_sold = 0
    movement_turns = 0
    productive_turns = 0
    idle_turns = 0
    water_completion_daily = []
    care_completion_daily = []
    cross_zone_moves = 0
    suspected_deadhead = 0

    # Track worker last productive position & consecutive move steps
    worker_move_streak = defaultdict(int)
    worker_last_prod = {}

    for s_idx in range(1, total_steps):
        prev_f = steps[s_idx - 1][0]["observation"]["farms"][0]
        curr_f = steps[s_idx][0]["observation"]["farms"][0]
        act = steps[s_idx][0].get("action") or {}
        farmer_act = act.get("farmer") or ["PASS"]
        hands_act = act.get("hands") or []
        all_acts = [farmer_act] + hands_act

        prev_farmer = tuple(prev_f["farmer"])
        prev_hands = [tuple(h) for h in prev_f["hands"]]
        prev_workers = [prev_farmer] + prev_hands

        # Market
        for o in act.get("market") or []:
            if isinstance(o, list) and len(o) > 2:
                if o[0] == "BUY_PRODUCT" and o[1] == "WHEAT":
                    feed_bought += int(o[2])
                elif o[0] == "SELL" and o[1] == "FERTILIZER":
                    fertilizer_sold += int(o[2])

        # Workers
        for w_idx, a in enumerate(all_acts):
            if not a:
                idle_turns += 1
                worker_move_streak[w_idx] = 0
                continue
            op = a[0]
            if op in MOVE_OPS:
                movement_turns += 1
                worker_move_streak[w_idx] += 1
                if w_idx < len(prev_workers):
                    p0 = prev_workers[w_idx]
                    dx, dy = 0, 0
                    if op == "NORTH": dy = -1
                    elif op == "SOUTH": dy = 1
                    elif op == "EAST": dx = 1
                    elif op == "WEST": dx = -1
                    p1 = (p0[0] + dx, p0[1] + dy)
                    if _region(p0[0], p0[1]) != _region(p1[0], p1[1]):
                        cross_zone_moves += 1
                # If moving for > 5 consecutive turns without productive action, suspected deadhead
                if worker_move_streak[w_idx] > 4:
                    suspected_deadhead += 1
            elif op in PRODUCTIVE_OPS:
                productive_turns += 1
                worker_move_streak[w_idx] = 0
                if op == "FERTILIZE":
                    fertilizer_applied += 1
                elif op == "HARVEST":
                    if w_idx < len(prev_workers):
                        pos = prev_workers[w_idx]
                        t = prev_f["tiles"][pos[1]][pos[0]]
                        if isinstance(t, dict):
                            yu = int(t.get("yield_units", 0) or 0)
                            k = t.get("kind")
                            if k == "PLANT":
                                crop = t.get("crop")
                                if crop == "STRAWBERRY": straw_harvested += yu
                                elif crop == "WHEAT": wheat_harvested += yu
                            elif k == "PASTURE":
                                anim = t.get("animal")
                                if anim == "SHEEP": wool_harvested += yu
                                elif anim == "COW": milk_harvested += yu
            else:
                idle_turns += 1
                worker_move_streak[w_idx] = 0

        # Daily completion
        if (s_idx % TPD) == (TPD - 1):
            f_tiles = curr_f["tiles"]
            plants = [t for row in f_tiles for t in row if isinstance(t, dict) and t.get("kind") == "PLANT"]
            if plants:
                watered = sum(1 for t in plants if t.get("watered_today"))
                water_completion_daily.append(watered / len(plants))
            animals = [t for row in f_tiles for t in row if isinstance(t, dict) and t.get("kind") == "PASTURE" and t.get("animal")]
            if animals:
                cared = sum(1 for t in animals if t.get("cared_today"))
                care_completion_daily.append(cared / len(animals))

    final_f = steps[-1][0]["observation"]["farms"][0]
    final_reward = float(steps[-1][0].get("reward") or 0.0)
    terminal_cash = float(final_f.get("money") or 0.0)
    num_workers = len(final_f.get("hands") or []) + 1

    priv = steps[-1][0]["observation"].get("private") or {}
    shed = priv.get("shed") or {}
    invs = priv.get("inventories") or []
    total_inv = defaultdict(int)
    for k, v in shed.items(): total_inv[k] += int(v or 0)
    for inv in invs:
        for k, v in inv.items(): total_inv[k] += int(v or 0)

    return {
        "seed": seed,
        "reward": final_reward,
        "strawberry_harvested": straw_harvested,
        "wool_harvested": wool_harvested,
        "wheat_harvested": wheat_harvested,
        "milk_harvested": milk_harvested,
        "feed_bought": feed_bought,
        "fertilizer_applied": fertilizer_applied,
        "fertilizer_sold": fertilizer_sold,
        "movement_turns": movement_turns,
        "productive_turns": productive_turns,
        "idle_turns": idle_turns,
        "num_workers": num_workers,
        "terminal_cash": terminal_cash,
        "terminal_inventory": dict(total_inv),
        "watering_completion": float(np.mean(water_completion_daily)) if water_completion_daily else 1.0,
        "animal_care_completion": float(np.mean(care_completion_daily)) if care_completion_daily else 1.0,
        "cross_zone_moves": cross_zone_moves,
        "suspected_deadhead": suspected_deadhead
    }


def execute_seed_batch(seeds, max_workers=10):
    results = {}
    with ProcessPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(run_seed_metrics, s): s for s in seeds}
        for f in as_completed(futs):
            res = f.result()
            results[res["seed"]] = res
    return [results[s] for s in seeds]


# ==============================================================================
# MAIN PROTOCOL PIPELINE
# ==============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("STARTING PROTOCOL EXECUTION (STEPS 1 - 5)")
    print("=" * 70)

    # -------------------------------------------------------------------------
    # STEP 1: 20 Baseline Seeds (1000 - 1019)
    # -------------------------------------------------------------------------
    print("\n--- STEP 1: Running Baseline 20 Seeds (1000–1019) ---")
    t0 = time.time()
    seeds_s1 = list(range(1000, 1020))
    s1_results = execute_seed_batch(seeds_s1, max_workers=10)
    print(f"Step 1 completed in {time.time()-t0:.1f}s.")

    with open("scratch/step1_baseline_results.json", "w") as f:
        json.dump(s1_results, f, indent=2)

    # Summarize Step 1
    s1_rewards = [r["reward"] for r in s1_results]
    s1_straw = [r["strawberry_harvested"] for r in s1_results]
    s1_wool = [r["wool_harvested"] for r in s1_results]
    s1_wheat = [r["wheat_harvested"] for r in s1_results]
    s1_milk = [r["milk_harvested"] for r in s1_results]
    s1_moves = [r["movement_turns"] for r in s1_results]
    s1_prod = [r["productive_turns"] for r in s1_results]
    s1_idle = [r["idle_turns"] for r in s1_results]
    s1_water = [r["watering_completion"] * 100 for r in s1_results]
    s1_care = [r["animal_care_completion"] * 100 for r in s1_results]
    s1_cash = [r["terminal_cash"] for r in s1_results]
    s1_deadhead = [r["suspected_deadhead"] for r in s1_results]

    print(f"Seeds 1000–1019 (N=20):")
    print(f"  Mean Reward:          ${np.mean(s1_rewards):10.2f} ± ${np.std(s1_rewards):8.2f} (Median: ${np.median(s1_rewards):.2f})")
    print(f"  Strawberry Harvested: {np.mean(s1_straw):8.1f} units")
    print(f"  Wool Harvested:       {np.mean(s1_wool):8.1f} units")
    print(f"  Wheat Harvested:      {np.mean(s1_wheat):8.1f} units")
    print(f"  Milk Harvested:       {np.mean(s1_milk):8.1f} units")
    print(f"  Movement Turns:       {np.mean(s1_moves):8.1f} (Median: {np.median(s1_moves):.1f})")
    print(f"  Productive Turns:     {np.mean(s1_prod):8.1f} (Median: {np.median(s1_prod):.1f})")
    print(f"  Idle Turns:           {np.mean(s1_idle):8.1f} (Median: {np.median(s1_idle):.1f})")
    print(f"  Watering Completion:  {np.mean(s1_water):8.1f}%")
    print(f"  Animal-Care Comp:     {np.mean(s1_care):8.1f}%")
    print(f"  Suspected Deadhead:   {np.mean(s1_deadhead):8.1f} turns")

    # -------------------------------------------------------------------------
    # STEP 2 & 3 & 4: Full Forensics on Representative Seed 1000
    # -------------------------------------------------------------------------
    print("\n--- STEP 2: Running Instrumented Full Forensics on Seed 1000 ---")
    t0 = time.time()
    agent_inst = InstrumentedClosedLoopEconomicV1()
    cfg = {"episodeSteps": 720, "seed": 1000}
    env = kaggle_environments.make("kaggriculture", configuration=cfg, debug=False)
    env.run([agent_inst, "starter"])
    print(f"Forensic trace captured {len(agent_inst.step_snapshots)} steps in {time.time()-t0:.1f}s.")

    # STEP 3: Classify every movement action for Seed 1000
    print("\n--- STEP 3: Movement Action Classification on Seed 1000 ---")
    move_classes = Counter()
    worker_last_pos = {}
    worker_last_task = {}
    worker_last_prod_time = {}
    
    # Tracking for Step 4 transition matrix
    transitions = Counter()
    transition_durations = defaultdict(list)
    transition_distances = defaultdict(list)
    transition_events = []

    snapshots = agent_inst.step_snapshots
    
    for s_idx in range(len(snapshots)):
        snap = snapshots[s_idx]
        step = snap["step"]
        workers = snap["workers"]
        actions = snap["actions"]
        targets = snap["targets"]
        tiles = snap["tiles"]
        invs = snap["invs"]
        
        # Look ahead 1 step to see if next action is productive
        next_actions = snapshots[s_idx + 1]["actions"] if s_idx + 1 < len(snapshots) else [["PASS"]] * len(workers)

        for w_idx in range(len(workers)):
            act = actions[w_idx] if w_idx < len(actions) else ["PASS"]
            op = act[0] if act else "PASS"
            pos = workers[w_idx]
            reg = _region(pos[0], pos[1])

            if op in MOVE_OPS:
                # Classify move
                # Check next action for immediate productivity
                next_act = next_actions[w_idx] if w_idx < len(next_actions) else ["PASS"]
                next_op = next_act[0] if next_act else "PASS"
                
                # Check assigned target
                t_info = targets.get(w_idx)
                target_pos = t_info[0] if t_info else None
                task_type = t_info[1] if t_info else "NONE"
                
                # Classification logic
                if next_op in PRODUCTIVE_OPS:
                    category = "A" # movement toward immediate productive action
                elif task_type in ("HARVEST_CROPS", "HARVEST"):
                    category = "B" # movement toward harvest
                elif task_type in ("WATER_CROPS", "URGENT_WATER", "WATER"):
                    category = "C" # movement toward watering
                elif task_type in ("RIPE_ANIMAL", "FEED", "CARE", "PLACE", "COLLECT_FERTILIZER"):
                    category = "D" # movement toward animal care
                elif task_type in ("DROP",) or (target_pos and target_pos in SHED_ACCESS):
                    category = "E" # movement toward shed
                elif target_pos and target_pos in WELL_ACCESS:
                    category = "F" # movement toward well
                elif task_type in ("PLANT_STRAW", "PLANT_MELON", "PLANT_WHEAT", "UNBUILT_P", "FERT", "WEEDS", "PICKUP"):
                    category = "G" # movement toward another required logistics action
                elif target_pos and _region(target_pos[0], target_pos[1]) != reg:
                    category = "H" # cross-region repositioning
                elif t_info is None:
                    # Moving without active target
                    category = "I" # suspected deadhead movement
                elif t_info[2] > 6:
                    # Stuck or circling target for > 6 turns
                    category = "J" # recovery / stale assignment
                else:
                    category = "K" # unclear

                move_classes[category] += 1

            elif op in PRODUCTIVE_OPS:
                # Worker executed a productive task!
                if w_idx in worker_last_prod_time:
                    prev_reg = worker_last_task[w_idx]["region"]
                    curr_reg = reg
                    trans_key = f"{prev_reg} -> {curr_reg}"
                    t_delta = step - worker_last_prod_time[w_idx]
                    d_dist = _dist(worker_last_pos[w_idx], pos)
                    
                    transitions[trans_key] += 1
                    transition_durations[trans_key].append(t_delta)
                    transition_distances[trans_key].append(d_dist)
                    
                    transition_events.append({
                        "worker": w_idx,
                        "from_region": prev_reg,
                        "to_region": curr_reg,
                        "from_pos": worker_last_pos[w_idx],
                        "to_pos": pos,
                        "from_step": worker_last_prod_time[w_idx],
                        "to_step": step,
                        "time_delta": t_delta,
                        "dist": d_dist,
                        "task_op": op,
                        "from_task": worker_last_task[w_idx]["op"]
                    })

                worker_last_prod_time[w_idx] = step
                worker_last_pos[w_idx] = pos
                worker_last_task[w_idx] = {"op": op, "region": reg, "pos": pos}

    total_move = sum(move_classes.values())
    prod_move = move_classes["A"] + move_classes["B"] + move_classes["C"] + move_classes["D"]
    logistics_move = move_classes["E"] + move_classes["F"] + move_classes["G"]
    cross_region_move = move_classes["H"]
    suspected_deadhead_move = move_classes["I"] + move_classes["J"]
    unknown_move = move_classes["K"]

    print(f"Seed 1000 Movement Classification Summary:")
    print(f"  Total Movement:             {total_move} turns")
    print(f"  Productive Movement (A-D):   {prod_move} ({prod_move/total_move*100:.1f}%)")
    print(f"    - Immediate Prod (A):     {move_classes['A']}")
    print(f"    - Toward Harvest (B):     {move_classes['B']}")
    print(f"    - Toward Watering (C):    {move_classes['C']}")
    print(f"    - Toward Animal Care (D): {move_classes['D']}")
    print(f"  Logistics Movement (E-G):   {logistics_move} ({logistics_move/total_move*100:.1f}%)")
    print(f"    - Toward Shed (E):        {move_classes['E']}")
    print(f"    - Toward Well (F):        {move_classes['F']}")
    print(f"    - Other Logistics (G):    {move_classes['G']}")
    print(f"  Cross-Region Move (H):      {cross_region_move} ({cross_region_move/total_move*100:.1f}%)")
    print(f"  Suspected Deadhead (I-J):   {suspected_deadhead_move} ({suspected_deadhead_move/total_move*100:.1f}%)")
    print(f"    - Unassigned Moves (I):   {move_classes['I']}")
    print(f"    - Stale/Recovery (J):     {move_classes['J']}")
    print(f"  Unknown Movement (K):       {unknown_move} ({unknown_move/total_move*100:.1f}%)")

    # -------------------------------------------------------------------------
    # STEP 4: Transition Matrix & Top Expensive Transitions
    # -------------------------------------------------------------------------
    print("\n--- STEP 4: Spatial Transition Matrix & Top Expensive Transitions ---")
    print(f"{'Transition':<15} | {'Count':<8} | {'Mean Dist':<10} | {'Total Travel':<12} | {'Mean Gap (turns)':<15}")
    print("-" * 68)
    
    sorted_trans = sorted(transitions.items(), key=lambda x: np.sum(transition_distances[x[0]]), reverse=True)
    for t_name, count in sorted_trans[:10]:
        mean_d = float(np.mean(transition_distances[t_name]))
        tot_d = int(np.sum(transition_distances[t_name]))
        mean_t = float(np.mean(transition_durations[t_name]))
        print(f"{t_name:<15} | {count:<8} | {mean_d:10.1f} | {tot_d:12d} | {mean_t:15.1f}")

    # -------------------------------------------------------------------------
    # STEP 5: 20 Diagnostic Seeds (1020 - 1039)
    # -------------------------------------------------------------------------
    print("\n--- STEP 5: Running Diagnostic 20 Seeds (1020–1039) to Test 429-Turn Claim ---")
    t0 = time.time()
    seeds_s5 = list(range(1020, 1040))
    s5_results = execute_seed_batch(seeds_s5, max_workers=10)
    print(f"Step 5 completed in {time.time()-t0:.1f}s.")

    with open("scratch/step5_diagnostic_results.json", "w") as f:
        json.dump(s5_results, f, indent=2)

    s5_rewards = [r["reward"] for r in s5_results]
    s5_straw = [r["strawberry_harvested"] for r in s5_results]
    s5_wool = [r["wool_harvested"] for r in s5_results]
    s5_wheat = [r["wheat_harvested"] for r in s5_results]
    s5_milk = [r["milk_harvested"] for r in s5_results]
    s5_moves = [r["movement_turns"] for r in s5_results]
    s5_prod = [r["productive_turns"] for r in s5_results]
    s5_idle = [r["idle_turns"] for r in s5_results]
    s5_cross = [r["cross_zone_moves"] for r in s5_results]
    s5_deadhead = [r["suspected_deadhead"] for r in s5_results]

    print(f"\nDiagnostic Seeds 1020–1039 (N=20):")
    print(f"  Mean Reward:          ${np.mean(s5_rewards):10.2f} ± ${np.std(s5_rewards):8.2f} (Median: ${np.median(s5_rewards):.2f})")
    print(f"  Strawberry Harvested: {np.mean(s5_straw):8.1f} units")
    print(f"  Wool Harvested:       {np.mean(s5_wool):8.1f} units")
    print(f"  Wheat Harvested:      {np.mean(s5_wheat):8.1f} units")
    print(f"  Milk Harvested:       {np.mean(s5_milk):8.1f} units")
    print(f"  Movement Turns:       {np.mean(s5_moves):8.1f} (Median: {np.median(s5_moves):.1f})")
    print(f"  Productive Turns:     {np.mean(s5_prod):8.1f} (Median: {np.median(s5_prod):.1f})")
    print(f"  Idle Turns:           {np.mean(s5_idle):8.1f} (Median: {np.median(s5_idle):.1f})")
    print(f"  Cross-Zone Moves:     {np.mean(s5_cross):8.1f} (Median: {np.median(s5_cross):.1f})")
    print(f"  Suspected Deadhead:   {np.mean(s5_deadhead):8.1f} (Median: {np.median(s5_deadhead):.1f})")

    # Direct Comparison between Batch 1 and Batch 2
    print("\n" + "=" * 70)
    print("COMPARISON: SEEDS 1000–1019 vs SEEDS 1020–1039 (STABILITY TEST)")
    print("=" * 70)
    print(f"{'Metric':<25} | {'Seeds 1000–1019':<18} | {'Seeds 1020–1039':<18} | {'Delta':<12}")
    print("-" * 75)
    for name, v1, v2 in [
        ("Reward ($)", np.mean(s1_rewards), np.mean(s5_rewards)),
        ("Movement Turns", np.mean(s1_moves), np.mean(s5_moves)),
        ("Productive Turns", np.mean(s1_prod), np.mean(s5_prod)),
        ("Idle Turns", np.mean(s1_idle), np.mean(s5_idle)),
        ("Strawberry Harvested", np.mean(s1_straw), np.mean(s5_straw)),
        ("Wool Harvested", np.mean(s1_wool), np.mean(s5_wool)),
        ("Wheat Harvested", np.mean(s1_wheat), np.mean(s5_wheat)),
        ("Milk Harvested", np.mean(s1_milk), np.mean(s5_milk)),
        ("Suspected Deadhead", np.mean(s1_deadhead), np.mean(s5_deadhead)),
    ]:
        delta = v2 - v1
        print(f"{name:<25} | {v1:18.2f} | {v2:18.2f} | {delta:+12.2f}")
