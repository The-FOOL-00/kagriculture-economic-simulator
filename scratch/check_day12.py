import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
from candidates.candidate_closed_loop_execution_v1 import agent as cl_v1_agent

def check_day12():
    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42})
    env.reset()
    
    def wrapped_agent(obs, config=None):
        step = int(obs.get("step", 0) or 0)
        day = step // 24
        hour = step % 24
        
        farm = obs["farms"][0]
        money = farm.get("money", 0)
        hired = farm.get("hires_today", 0)
        
        act = cl_v1_agent(obs, config)
        mkt = act.get("market", [])
        
        if day == 12 and hour < 4:
            print(f"Day 12 Hr {hour}: Money={money}, Hired={hired}, Orders ({len(mkt)}): {mkt}")
        return act

    env.run([wrapped_agent, "starter"])

if __name__ == "__main__":
    check_day12()
