import sys
import os
import json
from collections import defaultdict
import kaggle_environments

sys.path.insert(0, os.path.abspath('.'))

from scratch.qualification_counterfactual_suite import BaseQ50Agent, L_MinimalAgent

def trace_seed_events(seed):
    # Run Q50
    q_agent = BaseQ50Agent(50)
    cfg = {"episodeSteps": 720, "seed": seed}
    env_q = kaggle_environments.make("kaggriculture", configuration=cfg)
    steps_q = env_q.run([q_agent, "starter"])

    # Run L_Minimal
    l_agent = L_MinimalAgent(50)
    env_l = kaggle_environments.make("kaggriculture", configuration=cfg)
    steps_l = env_l.run([l_agent, "starter"])

    # Extract all planted strawberry tiles in both
    def extract_strawberry_lifecycle(steps):
        bushes = {}
        for s_idx, st in enumerate(steps):
            obs = st[0]["observation"]
            farm = obs["farms"][0]
            tiles = farm["tiles"]
            day = obs["day"]
            hour = obs["hour"]
            act = st[0].get("action") or {}
            f_act = act.get("farmer")
            h_acts = act.get("hands") or []
            all_acts = [f_act] + h_acts
            all_workers = [farm["farmer"]] + (farm.get("hands") or [])

            for r in range(len(tiles)):
                for c in range(len(tiles[r])):
                    t = tiles[r][c]
                    pos = (c, r)
                    if isinstance(t, dict) and t.get("crop") == "STRAWBERRY":
                        if pos not in bushes:
                            bushes[pos] = {
                                "pos": pos,
                                "planted_day": t.get("planted_day"),
                                "planted_step": s_idx,
                                "water_history": [],
                                "yield_history": [],
                                "harvest_steps": [],
                                "died_to_weed": False,
                                "death_step": None,
                                "competing_tasks": []
                            }
                        bushes[pos]["water_history"].append((s_idx, day, hour, t.get("watered_today"), t.get("consecutive_unwatered")))
                        bushes[pos]["yield_history"].append((s_idx, day, hour, t.get("yield_units", 0)))
                    elif pos in bushes and not bushes[pos]["died_to_weed"]:
                        if isinstance(t, dict) and t.get("kind") == "WEED":
                            bushes[pos]["died_to_weed"] = True
                            bushes[pos]["death_step"] = s_idx

            # Track worker actions
            for w_pos, w_act in zip(all_workers, all_acts):
                if w_act and isinstance(w_act, list):
                    op = w_act[0]
                    if op == "HARVEST" and tuple(w_pos) in bushes:
                        bushes[tuple(w_pos)]["harvest_steps"].append((s_idx, day, hour))

        return bushes

    b_q = extract_strawberry_lifecycle(steps_q)
    b_l = extract_strawberry_lifecycle(steps_l)

    # Find bushes that died in Q50 but survived in L_Minimal
    saved_bushes = []
    for pos, q_rec in b_q.items():
        if q_rec["died_to_weed"] and pos in b_l and not b_l[pos]["died_to_weed"]:
            saved_bushes.append({
                "pos": pos,
                "seed": seed,
                "q50_death_step": q_rec["death_step"],
                "l_min_harvests": len(b_l[pos]["harvest_steps"]),
                "q_rec": q_rec,
                "l_rec": b_l[pos]
            })

    return {
        "seed": seed,
        "q50_reward": steps_q[-1][0]["reward"],
        "l_min_reward": steps_l[-1][0]["reward"],
        "saved_bushes": saved_bushes
    }

if __name__ == "__main__":
    test_seeds = [1254, 1258, 1283, 1312, 1315]
    all_saved = []
    for s in test_seeds:
        res = trace_seed_events(s)
        print(f"Seed {s}: Q50=${res['q50_reward']} | L_Min=${res['l_min_reward']} | Saved Bushes: {len(res['saved_bushes'])}")
        for sb in res["saved_bushes"]:
            print(f"  Saved Strawberry at {sb['pos']}: Q50 died at step {sb['q50_death_step']} | L_Min harvested {sb['l_min_harvests']} times")
            all_saved.append(sb)

    with open("scratch/event_level_causal_evidence.json", "w") as f:
        # Save summary
        json.dump([{
            "seed": s["seed"],
            "pos": s["pos"],
            "q50_death_step": s["q50_death_step"],
            "l_min_harvests": s["l_min_harvests"]
        } for s in all_saved], f, indent=2)
