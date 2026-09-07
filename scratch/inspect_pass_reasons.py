import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
from candidates.candidate_closed_loop_commitment_v1 import agent as comm_agent
from collections import Counter

pass_reasons = Counter()
worker_pass_counts = Counter()

def wrapped_agent(obs, config=None):
    step = int(obs.get("step", 0) or 0)
    day = step // 24
    hour = step % 24
    p = int(obs.get("player", 0) or 0)
    farm = obs["farms"][p]
    farmer = tuple(farm["farmer"])
    hands = [tuple(h) for h in farm.get("hands", []) or []]
    workers = [farmer] + hands

    act = comm_agent(obs, config) if config else comm_agent(obs)
    f_act = act.get("farmer", ["PASS"])
    h_acts = act.get("hands", []) or []
    all_acts = [f_act] + [h_acts[i] if i < len(h_acts) else ["PASS"] for i in range(len(hands))]

    for w_i, (pos, a) in enumerate(zip(workers, all_acts)):
        op = a[0] if isinstance(a, list) and a else str(a)
        if op == "PASS":
            worker_pass_counts[w_i] += 1
            if step < 712:
                pass_reasons[(w_i, day, hour)] += 1
    return act

env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42})
env.run([wrapped_agent, "starter"])

print("Worker PASS counts:")
for w, cnt in worker_pass_counts.most_common():
    print(f"  Worker {w}: {cnt} PASSes")

print("\nSample PASS steps:")
for (w_i, day, hour), cnt in pass_reasons.most_common(15):
    print(f"  Worker {w_i}, Day {day}, Hour {hour}: {cnt} passes")
