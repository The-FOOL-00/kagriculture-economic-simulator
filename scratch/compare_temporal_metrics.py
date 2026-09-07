import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
from candidates.candidate_cl_aethel_grandmaster import agent as gm_agent
from candidates.candidate_closed_loop_execution_v1 import agent as cl_v1_agent
from collections import defaultdict, Counter
import numpy as np

SHED_ACCESS = frozenset([(4, 4), (5, 4), (4, 5), (5, 5)])

def get_quad(pos):
    x, y = pos
    if x < 5 and y < 5: return "NW"
    if x >= 5 and y < 5: return "NE"
    if x < 5 and y >= 5: return "SW"
    return "SE"

def profile_temporal_metrics(name, agent_fn, seed=42):
    worker_history = defaultdict(list)
    def wrapped(obs, config=None):
        step = int(obs.get("step", 0) or 0)
        day = step // 24
        hour = step % 24
        farm = obs["farms"][0]
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
    env.run([wrapped, "starter"])
    
    total_zone_changes = 0
    total_shed_returns = 0
    for w_i, records in worker_history.items():
        if not records: continue
        cur_zone = records[0]["zone"]
        for r in records[1:]:
            if r["zone"] != cur_zone:
                total_zone_changes += 1
                cur_zone = r["zone"]
        was_in_shed = records[0]["in_shed"]
        for r in records[1:]:
            if r["in_shed"] and not was_in_shed:
                total_shed_returns += 1
            was_in_shed = r["in_shed"]
            
    avg_zone_per_day = total_zone_changes / 30 / len(worker_history)
    avg_shed_per_day = total_shed_returns / 30 / len(worker_history)
    print(f"{name:<20}: Total Zone Transitions = {total_zone_changes:4d} ({avg_zone_per_day:4.2f}/w/day) | Total Shed Returns = {total_shed_returns:4d} ({avg_shed_per_day:4.2f}/w/day)")

if __name__ == "__main__":
    profile_temporal_metrics("Grandmaster", gm_agent)
    profile_temporal_metrics("CL-Execution-V1", cl_v1_agent)
