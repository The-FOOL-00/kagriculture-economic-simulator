import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
from candidates.candidate_closed_loop_execution_v1 import agent as cl_v1_agent

def check_counts():
    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42})
    env.reset()
    
    daily_stats = {}
    
    def wrapped_agent(obs, config=None):
        step = int(obs.get("step", 0) or 0)
        day = step // 24
        hour = step % 24
        
        farm = obs["farms"][0]
        priv = obs.get("private", {})
        money = farm.get("money", 0)
        hands = len(farm.get("hands", []) or [])
        tiles = farm.get("tiles", [])
        
        crops = Counter()
        animals = Counter()
        for r in tiles:
            for t in r:
                if isinstance(t, dict):
                    if t.get("crop"): crops[t.get("crop")] += 1
                    if t.get("animal"): animals[t.get("animal")] += 1
                    
        if hour == 1:
            daily_stats[day] = {
                "money": money,
                "hands": hands,
                "crops": dict(crops),
                "animals": dict(animals),
                "shed": dict(priv.get("shed", {}))
            }
        return cl_v1_agent(obs, config)

    env.run([wrapped_agent, "starter"])
    
    print("=== CL-Execution-V1 Daily Farm Stats ===")
    for d in range(0, 30, 3):
        if d in daily_stats:
            st = daily_stats[d]
            print(f"Day {d:02d}: Money={st['money']:>8.1f} | Hands={st['hands']:2d} | Crops={st['crops']} | Animals={st['animals']}")

if __name__ == "__main__":
    from collections import Counter
    check_counts()
