import sys
import os
import json
from collections import defaultdict
import numpy as np
from concurrent.futures import ProcessPoolExecutor
import kaggle_environments

sys.path.insert(0, os.path.abspath('.'))

import candidates.candidate_cl_fert_gated as m1_module
from scratch.run_wheat_quota_sweep_50seeds import ParameterizedQuotaAgent

def audit_seed_strawberry(seed):
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    steps = env.run([ParameterizedQuotaAgent(50), "starter"])

    strawberry_events = []
    # Track each tile
    # Track each strawberry bush lifecycle
    bushes = {} # (x, y) -> dict

    for s_idx in range(len(steps)):
        obs = steps[s_idx][0]["observation"]
        day = obs["day"]
        hour = obs["hour"]
        tiles = obs["farms"][0]["tiles"]
        workers = [obs["farms"][0].get("farmer")] + (obs["farms"][0].get("hands") or [])

        # Check all tiles
        for r in range(len(tiles)):
            for c in range(len(tiles[r])):
                t = tiles[r][c]
                pos = (c, r)

                if isinstance(t, dict) and t.get("crop") == "STRAWBERRY":
                    p_day = t["planted_day"]
                    if pos not in bushes:
                        bushes[pos] = {
                            "pos": pos,
                            "planted_day": p_day,
                            "planted_step": s_idx,
                            "first_yield_day": None,
                            "rot_day": None,
                            "rot_reason": None,
                            "harvest_steps": [],
                            "unwatered_days": [],
                            "max_unwatered_streak": 0,
                            "watered_history": [],
                            "yield_history": [],
                            "worker_task_at_rot": None
                        }
                    rec = bushes[pos]
                    yu = t.get("yield_units", 0)
                    rec["yield_history"].append((s_idx, yu))
                    if yu > 0 and rec["first_yield_day"] is None:
                        rec["first_yield_day"] = day
                    if hour == 23:
                        w_today = t.get("watered_today", False)
                        rec["watered_history"].append((day, w_today))
                        if not w_today:
                            rec["unwatered_days"].append(day)
                        cu = t.get("consecutive_unwatered", 0)
                        if cu > rec["max_unwatered_streak"]:
                            rec["max_unwatered_streak"] = cu

                elif pos in bushes and bushes[pos]["rot_day"] is None:
                    # Bush was previously tracked, but now disappeared or became WEED
                    rec = bushes[pos]
                    rec["rot_day"] = day
                    rec["rot_step"] = s_idx
                    if isinstance(t, dict) and t.get("kind") == "WEED":
                        # Check whether it died from lack of watering or decay
                        if rec["max_unwatered_streak"] >= 1:
                            rec["rot_reason"] = "DROUGHT_UNWATERED"
                        else:
                            rec["rot_reason"] = "OVERRIPE_DECAY"
                    else:
                        rec["rot_reason"] = "DUG_OR_REPLACED"

                    # Check what workers were doing at this step
                    act = steps[s_idx][0].get("action") or {}
                    all_acts = [act.get("farmer")] + (act.get("hands") or [])
                    rec["worker_actions_at_rot"] = [a[0] if (a and isinstance(a, list)) else "PASS" for a in all_acts]

        # Check harvests
        act = steps[s_idx][0].get("action") or {}
        all_acts = [act.get("farmer")] + (act.get("hands") or [])
        for w_idx, a in enumerate(all_acts):
            if a and isinstance(a, list) and a[0] == "HARVEST":
                w_pos = workers[w_idx] if w_idx < len(workers) else None
                if w_pos and tuple(w_pos) in bushes:
                    bushes[tuple(w_pos)]["harvest_steps"].append(s_idx)

    # Classify each strawberry bush loss into A, B, C, D, E, F
    classifications = defaultdict(int)
    details = []

    for pos, rec in bushes.items():
        if rec["rot_day"] is not None:
            reason = rec["rot_reason"]
            if reason == "DROUGHT_UNWATERED":
                # Drought: Was worker labor unavailable?
                # A: True labor contention (workers were busy doing other tasks like pasture/clearing/animals)
                classifications["A_TRUE_LABOR_CONTENTION"] += 1
            elif reason == "OVERRIPE_DECAY":
                # Decayed after max yield: Workers did not harvest in time
                # B: Movement inefficiency / routing delay
                classifications["B_MOVEMENT_INEFFICIENCY"] += 1
            else:
                classifications["F_OTHER"] += 1
        else:
            # Did not rot
            # Check if harvest was delayed
            if len(rec["harvest_steps"]) == 0 and rec["first_yield_day"] is not None:
                classifications["D_CROP_TIMING_TERMINAL"] += 1
            else:
                classifications["SUCCESS_HARVESTED"] += 1

    return {
        "seed": seed,
        "total_bushes": len(bushes),
        "classifications": dict(classifications),
        "rot_reasons": {
            "DROUGHT_UNWATERED": sum(1 for b in bushes.values() if b["rot_reason"] == "DROUGHT_UNWATERED"),
            "OVERRIPE_DECAY": sum(1 for b in bushes.values() if b["rot_reason"] == "OVERRIPE_DECAY"),
            "DUG_OR_REPLACED": sum(1 for b in bushes.values() if b["rot_reason"] == "DUG_OR_REPLACED")
        },
        "rot_days": [b["rot_day"] for b in bushes.values() if b["rot_day"] is not None],
        "planted_days": [b["planted_day"] for b in bushes.values()],
        "first_yield_days": [b["first_yield_day"] for b in bushes.values() if b["first_yield_day"] is not None]
    }

def main():
    seeds = list(range(1250, 1300)) # 50 seeds
    print(f"Auditing strawberry failure mechanisms on {len(seeds)} seeds...")
    with ProcessPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(audit_seed_strawberry, seeds))

    print("\n" + "="*80)
    print("PHASE 3: FORENSIC CLASSIFICATION OF STRAWBERRY LOSS MECHANISMS (50 SEEDS)")
    print("="*80)

    total_bushes = sum(r["total_bushes"] for r in results)
    print(f"Total Strawberry Bushes Monitored: {total_bushes} across {len(seeds)} seeds (mean {total_bushes/len(seeds):.1f}/seed)")

    agg_classes = defaultdict(int)
    agg_reasons = defaultdict(int)
    all_rot_days = []
    all_plant_days = []
    all_yield_days = []

    for r in results:
        for k, v in r["classifications"].items():
            agg_classes[k] += v
        for k, v in r["rot_reasons"].items():
            agg_reasons[k] += v
        all_rot_days.extend(r["rot_days"])
        all_plant_days.extend(r["planted_days"])
        all_yield_days.extend(r["first_yield_days"])

    print("\nLoss Classification Breakdown:")
    for k, v in sorted(agg_classes.items()):
        pct = v / total_bushes * 100
        print(f"  {k:<30}: {v:>5} bushes ({pct:>5.1f}%) | Mean {v/len(seeds):.2f}/seed")

    print("\nUnderlying Physical Rot Causes:")
    for k, v in sorted(agg_reasons.items()):
        pct = v / total_bushes * 100
        print(f"  {k:<30}: {v:>5} bushes ({pct:>5.1f}%) | Mean {v/len(seeds):.2f}/seed")

    print(f"\nTiming Analysis:")
    print(f"  Planted Days:    Min = Day {min(all_plant_days)}, Mean = Day {np.mean(all_plant_days):.1f}, Max = Day {max(all_plant_days)}")
    print(f"  First Yield Day: Min = Day {min(all_yield_days)}, Mean = Day {np.mean(all_yield_days):.1f}, Max = Day {max(all_yield_days)}")
    print(f"  Rot Days:        Min = Day {min(all_rot_days)}, Mean = Day {np.mean(all_rot_days):.1f}, Max = Day {max(all_rot_days)}")

    # Rot day distribution
    rot_dist = defaultdict(int)
    for d in all_rot_days:
        rot_dist[d] += 1
    print("\nRot Events by Day:")
    for d in sorted(rot_dist.keys()):
        print(f"  Day {d:>2}: {rot_dist[d]:>4} rots ({rot_dist[d]/len(seeds):.2f}/seed)")

    with open("scratch/strawberry_failure_mechanisms.json", "w") as f:
        json.dump({
            "total_bushes": total_bushes,
            "classes": dict(agg_classes),
            "reasons": dict(agg_reasons),
            "rot_distribution": dict(rot_dist)
        }, f, indent=2)

if __name__ == "__main__":
    main()
