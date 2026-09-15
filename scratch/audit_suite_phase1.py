import sys
import os
import json
import numpy as np
from collections import defaultdict, Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
import kaggle_environments

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from candidates.candidate_cl_economic_v1 import agent as cl_baseline_agent
from candidates.slot2_aethel_refined_v2 import agent as v2_agent
from scratch.produce_drop_threshold_experiment import ProduceBatchingAgent
from scratch.feed_pickup_experiment import FeedBatchingAgent

def run_single_eval(args):
    arm_type, arm_name, seed = args
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg, debug=False)
    
    if arm_type == "CL_BASELINE":
        # Fresh instance of baseline
        from candidates.candidate_cl_economic_v1 import ClosedLoopEconomicV1
        agent_inst = ClosedLoopEconomicV1()
    elif arm_type == "FROZEN_V2":
        # Fresh instance of V2
        import candidates.slot2_aethel_refined_v2 as v2_mod
        # V2 uses module-level agent function, which maintains state inside _base_agent or similar
        # Let's inspect how v2 is run
        agent_inst = v2_mod.agent
    elif arm_type == "PRODUCE":
        agent_inst = ProduceBatchingAgent(drop_policy=arm_name)
    elif arm_type == "FEED":
        agent_inst = FeedBatchingAgent(feed_policy=arm_name)
    else:
        raise ValueError(f"Unknown arm_type {arm_type}")

    # Run vs starter
    env.run([agent_inst, "starter"])
    steps = env.steps
    total_steps = len(steps)

    # Detailed action decomposition
    harvest_opcodes_by_target = Counter()
    total_harvest_ops = 0
    total_pickup_ops = 0
    total_wheat_pickups = 0
    wheat_pickup_quantities = []
    total_drop_ops = 0
    drop_payloads = []
    total_moves = 0
    total_prods = 0
    total_idles = 0
    shed_max = 0
    
    # Commodity yield units harvested (from tile state transitions)
    harvested_units = Counter()

    # Animal feeding telemetry
    hungry_occurrences = 0
    fed_occurrences = 0

    for s_idx in range(1, total_steps):
        prev_f = steps[s_idx - 1][0]["observation"]["farms"][0]
        act = steps[s_idx][0].get("action") or {}
        all_acts = [act.get("farmer") or ["PASS"]] + (act.get("hands") or [])
        workers = [tuple(prev_f["farmer"])] + [tuple(h) for h in prev_f["hands"]]
        priv = steps[s_idx - 1][0]["observation"].get("private") or {}
        shed = priv.get("shed") or {}
        invs = priv.get("inventories") or []

        s_occ = sum(int(v or 0) for v in shed.values())
        if s_occ > shed_max:
            shed_max = s_occ

        # Track hungry animals
        for r in prev_f["tiles"]:
            for t in r:
                if isinstance(t, dict) and t.get("kind") == "PASTURE":
                    hungry_occurrences += 1
                    if t.get("fed_today"):
                        fed_occurrences += 1

        for w_idx, a in enumerate(all_acts):
            if not a:
                total_idles += 1
                continue
            op = a[0]
            if op in ("NORTH", "SOUTH", "EAST", "WEST"):
                total_moves += 1
            elif op == "HARVEST":
                total_prods += 1
                total_harvest_ops += 1
                pos = workers[w_idx] if w_idx < len(workers) else (0, 0)
                t = prev_f["tiles"][pos[1]][pos[0]] if 0 <= pos[1] < 10 and 0 <= pos[0] < 10 else None
                if isinstance(t, dict):
                    k = t.get("kind")
                    yu = int(t.get("yield_units", 0) or 0)
                    if k == "PLANT":
                        crop = t.get("crop", "UNKNOWN")
                        harvest_opcodes_by_target[crop] += 1
                        harvested_units[crop] += yu
                    elif k == "PASTURE":
                        anim = t.get("animal", "UNKNOWN")
                        harvest_opcodes_by_target[anim] += 1
                        harvested_units[anim] += yu
                    else:
                        harvest_opcodes_by_target["OTHER"] += 1
                else:
                    harvest_opcodes_by_target["EMPTY"] += 1
            elif op == "PICKUP":
                total_prods += 1
                total_pickup_ops += 1
                item = a[1] if len(a) > 1 else None
                amt = int(a[2]) if len(a) > 2 else 1
                if item == "WHEAT":
                    total_wheat_pickups += 1
                    wheat_pickup_quantities.append(amt)
            elif op == "DROP":
                total_prods += 1
                total_drop_ops += 1
                p_inv = invs[w_idx] if w_idx < len(invs) else {}
                load = sum(int(v or 0) for v in p_inv.values())
                drop_payloads.append(load)
            elif op in ("WATER", "FEED", "CARE", "PLANT", "BUILD_PASTURE", "FERTILIZE", "COLLECT_FERTILIZER", "DIG", "PLACE"):
                total_prods += 1
            else:
                total_idles += 1

    terminal_reward = float(steps[-1][0].get("reward") or 0.0)
    final_money = float(steps[-1][0]["observation"]["farms"][0].get("money") or 0.0)
    care_fed_pct = (fed_occurrences / hungry_occurrences * 100.0) if hungry_occurrences > 0 else 0.0

    return {
        "arm_type": arm_type,
        "arm_name": arm_name,
        "seed": seed,
        "reward": terminal_reward,
        "money": final_money,
        "harvest_ops": total_harvest_ops,
        "harvest_by_target": dict(harvest_opcodes_by_target),
        "harvested_units": dict(harvested_units),
        "pickup_ops": total_pickup_ops,
        "wheat_pickups": total_wheat_pickups,
        "mean_wheat_batch": float(np.mean(wheat_pickup_quantities)) if wheat_pickup_quantities else 0.0,
        "drop_ops": total_drop_ops,
        "mean_payload": float(np.mean(drop_payloads)) if drop_payloads else 0.0,
        "moves": total_moves,
        "prods": total_prods,
        "idles": total_idles,
        "shed_max": shed_max,
        "care_fed_pct": care_fed_pct
    }

if __name__ == "__main__":
    seeds = list(range(1000, 1010))
    tasks = []
    
    # 1. Baseline CL
    for s in seeds:
        tasks.append(("CL_BASELINE", "BASELINE", s))
    # 2. Frozen V2
    for s in seeds:
        tasks.append(("FROZEN_V2", "FROZEN_V2", s))
    # 3. Produce Batching Arms
    produce_arms = ["DROP_GE_3", "DROP_GE_5", "DROP_GE_8", "DROP_GE_10", "CAPACITY_OR_TERMINAL", "HYBRID_ADAPTIVE"]
    for arm in produce_arms:
        for s in seeds:
            tasks.append(("PRODUCE", arm, s))
    # 4. Feed Batching Arms
    feed_arms = ["MODERATE_BATCH", "LARGE_BATCH", "DEDICATED_FEEDER", "COORDINATED_SHARED"]
    for arm in feed_arms:
        for s in seeds:
            tasks.append(("FEED", arm, s))

    print(f"Executing {len(tasks)} matches across {len(seeds)} seeds...")
    results = defaultdict(list)
    with ProcessPoolExecutor(max_workers=10) as ex:
        futs = [ex.submit(run_single_eval, t) for t in tasks]
        for f in as_completed(futs):
            res = f.result()
            key = f"{res['arm_type']}:{res['arm_name']}"
            results[key].append(res)

    # Save complete raw output
    with open("scratch/audit_reproduced_raw_results.json", "w") as f:
        json.dump({k: v for k, v in results.items()}, f, indent=2)

    print("Completed. Summary statistics:")
    for key, lst in sorted(results.items()):
        lst.sort(key=lambda x: x["seed"])
        rews = [x["reward"] for x in lst]
        harvs = [x["harvest_ops"] for x in lst]
        drops = [x["drop_ops"] for x in lst]
        picks = [x["pickup_ops"] for x in lst]
        moves = [x["moves"] for x in lst]
        straw = [x["harvested_units"].get("STRAWBERRY", 0) for x in lst]
        wool = [x["harvested_units"].get("SHEEP", 0) for x in lst]
        wheat = [x["harvested_units"].get("WHEAT", 0) for x in lst]
        melon = [x["harvested_units"].get("MELON", 0) for x in lst]
        mean_rew = float(np.mean(rews))
        std_rew = float(np.std(rews))
        ci95 = 1.96 * std_rew / np.sqrt(len(rews))
        print(f"{key:<30} | Rew: ${mean_rew:10.2f} ± ${ci95:6.2f} (std {std_rew:6.2f}) | Harvs: {np.mean(harvs):5.1f} | Drops: {np.mean(drops):5.1f} | Picks: {np.mean(picks):5.1f} | Moves: {np.mean(moves):6.1f} | Straw: {np.mean(straw):5.1f} | Wool: {np.mean(wool):5.1f} | Wheat: {np.mean(wheat):5.1f} | Melon: {np.mean(melon):5.1f}")
