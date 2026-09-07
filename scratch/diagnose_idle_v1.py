import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
from candidates.candidate_closed_loop_execution_v1 import agent as cl_v1_agent
from collections import Counter, defaultdict

def diagnose_v1():
    worker_actions = defaultdict(lambda: Counter())
    idle_reasons = defaultdict(int)
    
    def wrapped_agent(obs, config=None):
        step = int(obs.get("step", 0) or 0)
        day = step // 24
        hour = step % 24
        
        farm = obs["farms"][0]
        farmer = tuple(farm["farmer"])
        hands = [tuple(h) for h in farm.get("hands", []) or []]
        workers = [farmer] + hands
        
        act = cl_v1_agent(obs, config)
        f_act = act.get("farmer", ["PASS"])
        h_acts = act.get("hands", []) or []
        all_acts = [f_act] + [h_acts[i] if i < len(h_acts) else ["PASS"] for i in range(len(hands))]
        
        for w_i, a in enumerate(all_acts):
            op = a[0] if isinstance(a, list) and a else str(a)
            worker_actions[w_i][op] += 1
            if op == "PASS":
                idle_reasons[(day, hour, w_i)] += 1
        return act

    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42})
    env.run([wrapped_agent, "starter"])
    
    print("=== Worker Actions Summary ===")
    for w_i in sorted(worker_actions.keys()):
        tot = sum(worker_actions[w_i].values())
        passes = worker_actions[w_i]["PASS"]
        top_ops = ", ".join(f"{op}: {cnt}" for op, cnt in worker_actions[w_i].most_common(5))
        print(f"Worker {w_i:2d}: Total = {tot:3d} | PASS = {passes:3d} ({passes/tot*100:4.1f}%) | Top: {top_ops}")

if __name__ == "__main__":
    diagnose_v1()
