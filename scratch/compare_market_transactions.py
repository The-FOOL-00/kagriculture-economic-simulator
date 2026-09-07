import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
from candidates.candidate_closed_loop_commitment_v1 import agent as comm_agent
import candidates.slot2_aethel_refined_v2 as v2_mod
from collections import defaultdict

def track_market(agent_fn):
    buys = defaultdict(int)
    sells = defaultdict(int)
    money_history = []
    
    def wrapped(obs, config=None):
        farm = obs["farms"][0]
        money = farm["money"]
        act = agent_fn(obs)
        m_acts = act.get("market", []) or []
        for m in m_acts:
            op = m[0]
            if op == "BUY_SEED":
                buys[m[1]] += int(m[2])
            elif op == "BUY_ANIMAL":
                buys[f"ANIMAL_{m[1]}"] += int(m[2])
            elif op == "BUY_PRODUCT":
                buys[f"PROD_{m[1]}"] += int(m[2])
            elif op == "BUY_LAND":
                buys["LAND"] += 1
            elif op == "SELL":
                sells[m[1]] += int(m[2])
        return act

    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42})
    env.run([wrapped, "starter"])
    return buys, sells

v2_buys, v2_sells = track_market(v2_mod.agent)
comm_buys, comm_sells = track_market(comm_agent)

print("=== V2 Buys ===")
for k, v in sorted(v2_buys.items()):
    print(f"  {k:<20}: {v}")

print("\n=== CL-Commitment Buys ===")
for k, v in sorted(comm_buys.items()):
    print(f"  {k:<20}: {v}")

print("\n=== V2 Sells ===")
for k, v in sorted(v2_sells.items()):
    print(f"  {k:<20}: {v}")

print("\n=== CL-Commitment Sells ===")
for k, v in sorted(comm_sells.items()):
    print(f"  {k:<20}: {v}")
