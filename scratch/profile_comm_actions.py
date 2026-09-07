import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
from candidates.candidate_closed_loop_commitment_v1 import agent as comm_agent
from collections import Counter

comm_actions = Counter()
comm_hires_per_day = {}

def wrapped_comm(obs, config=None):
    step = int(obs.get("step", 0) or 0)
    day = step // 24
    hour = step % 24
    act = comm_agent(obs)
    f_act = act.get("farmer", ["PASS"])
    h_acts = act.get("hands", []) or []
    m_acts = act.get("market", []) or []
    
    hires = sum(1 for m in m_acts if m[0] == "HIRE")
    if hires > 0:
        comm_hires_per_day[day] = comm_hires_per_day.get(day, 0) + hires

    all_acts = [f_act] + h_acts
    for a in all_acts:
        op = a[0] if isinstance(a, list) and a else str(a)
        comm_actions[op] += 1
    return act

env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42})
env.run([wrapped_comm, "starter"])

print("CL-Commitment Action breakdown:")
for op, cnt in comm_actions.most_common():
    print(f"  {op:<20}: {cnt}")

print("\nCL-Commitment Hires per day:")
for d, h in sorted(comm_hires_per_day.items()):
    print(f"  Day {d}: {h} hires")
