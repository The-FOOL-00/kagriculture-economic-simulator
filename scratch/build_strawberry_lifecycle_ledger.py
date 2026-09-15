import json
import os
import sys
import numpy as np

sys.path.insert(0, os.getcwd())
import kaggle_environments

from candidates.candidate_cl_economic_v1 import agent as cl_agent
from candidates.slot2_aethel_refined_v2 import agent as v2_agent

SEEDS = list(range(1000, 1010))

def run_episode(agent, seed):
    env = kaggle_environments.make("kaggriculture", configuration={"seed": seed})
    steps = env.run([agent, "starter"])
    return steps

def extract_strawberry_lifecycle(steps, agent_name, seed):
    """
    Reconstructs complete lifecycle for every strawberry bush in the episode.
    Uses steps[s-1] for pre-action tile state and steps[s] for post-action state.
    """
    bushes = []
    active_bushes = {}  # (x, y) -> bush dict
    bush_counter = 0

    for s_idx in range(1, len(steps)):
        prev_obs = steps[s_idx - 1][0]["observation"]
        curr_obs = steps[s_idx][0]["observation"]
        act = steps[s_idx][0].get("action") or {}

        day = prev_obs["day"]
        hour = prev_obs["hour"]
        prev_farm = prev_obs["farms"][0]
        curr_farm = curr_obs["farms"][0]
        prev_tiles = prev_farm["tiles"]
        curr_tiles = curr_farm["tiles"]

        prev_farmer = prev_farm["farmer"]
        prev_hands = prev_farm["hands"]
        prev_workers = ([prev_farmer] if prev_farmer else []) + [h for h in prev_hands if h]
        prev_invs = prev_obs["private"]["inventories"]

        # 1. Detect new strawberry plants planted during step s-1 -> s
        # A tile has PLANT STRAWBERRY if it wasn't strawberry in prev_tiles, but is in curr_tiles
        for y in range(10):
            for x in range(10):
                pt = prev_tiles[y][x]
                ct = curr_tiles[y][x]
                was_straw = isinstance(pt, dict) and pt.get("kind") == "PLANT" and pt.get("crop") == "STRAWBERRY"
                is_straw = isinstance(ct, dict) and ct.get("kind") == "PLANT" and ct.get("crop") == "STRAWBERRY"

                if is_straw and not was_straw:
                    bush_counter += 1
                    planted_day = ct.get("planted_day", day)
                    bush = {
                        "bush_id": f"{seed}_{agent_name}_{x}_{y}_{bush_counter}",
                        "seed": seed,
                        "agent": agent_name,
                        "coord": [x, y],
                        "planting_step": s_idx,
                        "planting_day": planted_day,
                        "planting_hour": hour,
                        "fertilization_events": [],
                        "watering_events": [],
                        "production_nights": [],
                        "harvest_events": [],
                        "decay_events": [],
                        "cycles_realized": 0,
                        "units_harvested": 0,
                        "units_decayed": 0,
                        "units_residual": 0,
                        "mls": ct.get("max_lifespan_step", -1)
                    }
                    active_bushes[(x, y)] = bush
                    bushes.append(bush)

        # 2. Check actions taken by workers during step s-1 -> s
        farmer_act = act.get("farmer")
        all_acts = ([farmer_act] if farmer_act else []) + [h for h in act.get("hands", []) if h]
        for w_idx, w_act in enumerate(all_acts):
            if not w_act or len(w_act) == 0:
                continue
            if w_idx >= len(prev_workers) or prev_workers[w_idx] is None:
                continue
            wx, wy = prev_workers[w_idx]
            w_pos = (wx, wy)
            if w_pos not in active_bushes:
                continue

            op = w_act[0]
            bush = active_bushes[w_pos]

            if op == "FERTILIZE":
                fert_inv = int(prev_invs[w_idx].get("FERTILIZER", 0) or 0) if w_idx < len(prev_invs) else 0
                bush["fertilization_events"].append({
                    "step": s_idx,
                    "day": day,
                    "hour": hour,
                    "worker_idx": w_idx,
                    "fert_inv_before": fert_inv
                })

            elif op == "WATER":
                bush["watering_events"].append({
                    "step": s_idx,
                    "day": day,
                    "hour": hour,
                    "worker_idx": w_idx
                })

            elif op == "HARVEST":
                pt = prev_tiles[wy][wx]
                yu = int(pt.get("yield_units", 0) or 0) if isinstance(pt, dict) else 0
                if yu > 0:
                    bush["harvest_events"].append({
                        "step": s_idx,
                        "day": day,
                        "hour": hour,
                        "worker_idx": w_idx,
                        "units": yu
                    })
                    bush["units_harvested"] += yu

        # 3. Track tile state transitions, decay, and end-of-day production refresh
        for (bx, by), bush in list(active_bushes.items()):
            ct = curr_tiles[by][bx]
            is_still_straw = isinstance(ct, dict) and ct.get("kind") == "PLANT" and ct.get("crop") == "STRAWBERRY"

            if not is_still_straw:
                if isinstance(ct, dict) and ct.get("kind") == "WEED":
                    bush["decay_events"].append({
                        "step": s_idx,
                        "day": day,
                        "hour": hour,
                        "reason": "WEED_TRANSITION"
                    })
                del active_bushes[(bx, by)]
                continue

            bush["mls"] = ct.get("max_lifespan_step", -1)

            # Check lifespan decay:
            # Engine decrements yield_units by 1 every 2 steps once step >= mls
            pt = prev_tiles[by][bx]
            if isinstance(pt, dict):
                mls = pt.get("max_lifespan_step", -1)
                if mls >= 0 and s_idx >= mls and (s_idx - mls) % 2 == 0:
                    harvest_here = any(h["step"] == s_idx for h in bush["harvest_events"])
                    if not harvest_here:
                        prev_yu = pt.get("yield_units", 0)
                        curr_yu = ct.get("yield_units", 0)
                        if prev_yu > curr_yu:
                            lost = prev_yu - curr_yu
                            bush["decay_events"].append({
                                "step": s_idx,
                                "day": day,
                                "hour": hour,
                                "reason": "LIFESPAN_DECAY",
                                "units": lost
                            })
                            bush["units_decayed"] += lost

            # Check production night at hour 23 (refresh from day -> day + 1)
            if hour == 23:
                P = bush["planting_day"]
                days_since_first = (day + 1) - P - 10
                if days_since_first >= 0 and days_since_first % 2 == 0:
                    cycle = days_since_first // 2 + 1
                    if cycle <= 4:
                        was_watered = pt.get("watered_today", False) if isinstance(pt, dict) else False
                        fert_until = pt.get("fertilized_until_day", -1) if isinstance(pt, dict) else -1
                        is_fert = was_watered and fert_until >= day
                        yield_add = 2 if is_fert else 1
                        bush["production_nights"].append({
                            "cycle": cycle,
                            "day": day,
                            "step": s_idx,
                            "was_watered": was_watered,
                            "fertilized_until_day": fert_until,
                            "is_fertilized": is_fert,
                            "yield_added": yield_add,
                            "yield_units_before": pt.get("yield_units", 0) if isinstance(pt, dict) else 0
                        })
                        bush["cycles_realized"] += 1

    # End of episode residuals
    final_tiles = steps[-1][0]["observation"]["farms"][0]["tiles"]
    for bush in bushes:
        bx, by = bush["coord"]
        t_final = final_tiles[by][bx]
        if isinstance(t_final, dict) and t_final.get("kind") == "PLANT" and t_final.get("crop") == "STRAWBERRY":
            bush["units_residual"] = int(t_final.get("yield_units", 0) or 0)

    return bushes

def main():
    print("Building raw strawberry lifecycle ledger for Seeds 1000-1009...")
    all_data = {"CL": {}, "V2": {}}
    summary = []

    for seed in SEEDS:
        print(f"--- Running Seed {seed} ---")
        cl_steps = run_episode(cl_agent, seed)
        cl_bushes = extract_strawberry_lifecycle(cl_steps, "CL-Economic-V1", seed)
        cl_reward = cl_steps[-1][0]["observation"]["farms"][0]["money"]
        cl_harvest = sum(b["units_harvested"] for b in cl_bushes)
        all_data["CL"][seed] = cl_bushes

        v2_steps = run_episode(v2_agent, seed)
        v2_bushes = extract_strawberry_lifecycle(v2_steps, "Frozen-V2", seed)
        v2_reward = v2_steps[-1][0]["observation"]["farms"][0]["money"]
        v2_harvest = sum(b["units_harvested"] for b in v2_bushes)
        all_data["V2"][seed] = v2_bushes

        gap = v2_harvest - cl_harvest
        summary.append({
            "seed": seed,
            "cl_reward": cl_reward,
            "v2_reward": v2_reward,
            "cl_harvest": cl_harvest,
            "v2_harvest": v2_harvest,
            "gap": gap,
            "cl_bushes": len(cl_bushes),
            "v2_bushes": len(v2_bushes),
            "cl_yield_per_bush": cl_harvest / max(1, len(cl_bushes)),
            "v2_yield_per_bush": v2_harvest / max(1, len(v2_bushes))
        })
        print(f"Seed {seed}: CL={cl_harvest} ({len(cl_bushes)} bushes) | V2={v2_harvest} ({len(v2_bushes)} bushes) | Gap={gap:+d}")

    os.makedirs("scratch", exist_ok=True)
    with open("scratch/strawberry_lifecycle_ledger.json", "w") as f:
        json.dump(all_data, f, indent=2)
    with open("scratch/strawberry_lifecycle_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    cl_h = [s["cl_harvest"] for s in summary]
    v2_h = [s["v2_harvest"] for s in summary]
    gaps = [s["gap"] for s in summary]
    cl_b = [s["cl_bushes"] for s in summary]
    v2_b = [s["v2_bushes"] for s in summary]
    cl_r = [s["cl_reward"] for s in summary]
    v2_r = [s["v2_reward"] for s in summary]

    # Bootstrap 95% CI for Gap
    boot_gaps = []
    rng = np.random.default_rng(42)
    for _ in range(10000):
        sample = rng.choice(gaps, size=len(gaps), replace=True)
        boot_gaps.append(np.mean(sample))
    ci_lower, ci_upper = np.percentile(boot_gaps, [2.5, 97.5])

    print("\n" + "="*80)
    print("INDEPENDENT RAW TELEMETRY RECONSTRUCTION (SEEDS 1000-1009)")
    print("="*80)
    print(f"{'Seed':<6} | {'CL Reward':<12} | {'V2 Reward':<12} | {'CL Straw':<8} | {'V2 Straw':<8} | {'Delta':<6} | {'CL Bush':<7} | {'V2 Bush':<7} | {'CL Y/B':<6} | {'V2 Y/B':<6}")
    print("-" * 88)
    for s in summary:
        print(f"{s['seed']:<6} | ${int(s['cl_reward']):<11,d} | ${int(s['v2_reward']):<11,d} | {s['cl_harvest']:<8} | {s['v2_harvest']:<8} | {s['gap']:<+6} | {s['cl_bushes']:<7} | {s['v2_bushes']:<7} | {s['cl_yield_per_bush']:<6.2f} | {s['v2_yield_per_bush']:<6.2f}")
    print("-" * 88)
    print(f"{'MEAN':<6} | ${np.mean(cl_r):<11,.1f} | ${np.mean(v2_r):<11,.1f} | {np.mean(cl_h):<8.2f} | {np.mean(v2_h):<8.2f} | {np.mean(gaps):<+6.2f} | {np.mean(cl_b):<7.2f} | {np.mean(v2_b):<7.2f} | {np.mean(cl_h)/np.mean(cl_b):<6.2f} | {np.mean(v2_h)/np.mean(v2_b):<6.2f}")
    print(f"{'MEDIAN':<6} | ${np.median(cl_r):<11,.1f} | ${np.median(v2_r):<11,.1f} | {np.median(cl_h):<8.1f} | {np.median(v2_h):<8.1f} | {np.median(gaps):<+6.1f}")
    print(f"{'STD':<6}    |              |              | {np.std(cl_h):<8.2f} | {np.std(v2_h):<8.2f} | {np.std(gaps):<6.2f}")
    print(f"Gap 95% Bootstrap CI: [{ci_lower:.2f}, {ci_upper:.2f}]")
    print("="*80)

if __name__ == "__main__":
    main()
