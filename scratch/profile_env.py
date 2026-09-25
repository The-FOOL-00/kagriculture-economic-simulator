import sys
import os
sys.path.insert(0, '.')
sys.path.insert(0, './scripts')
import time
import copy
from scripts.v32_common import load_agent
from kaggle_environments import make

def run_profiled():
    env = make('kaggriculture', configuration={'seed': 249635})
    a = load_agent('E2_A7')
    b = load_agent('E0_V3')
    
    t_agent_a = 0.0
    t_agent_b = 0.0
    t_env_step = 0.0
    t_obs_prep = 0.0
    
    env.reset()
    
    while not env.done:
        t0 = time.perf_counter()
        # Obs prep
        obs_a = copy.deepcopy(env.steps[-1][0]['observation'])
        obs_b = copy.deepcopy(env.steps[-1][1]['observation'])
        for k in ('step', 'market', 'town', 'day', 'hour'):
            if k in env.steps[-1][0]['observation']:
                obs_a[k] = env.steps[-1][0]['observation'][k]
                obs_b[k] = env.steps[-1][0]['observation'][k]
        t1 = time.perf_counter()
        t_obs_prep += (t1 - t0)
        
        act_a = a.act(obs_a)
        t2 = time.perf_counter()
        t_agent_a += (t2 - t1)
        
        act_b = b.act(obs_b)
        t3 = time.perf_counter()
        t_agent_b += (t3 - t2)
        
        env.step([act_a, act_b])
        t4 = time.perf_counter()
        t_env_step += (t4 - t3)
        
    tot = t_obs_prep + t_agent_a + t_agent_b + t_env_step
    print(f"Total time: {tot:.2f}s (SPS: {720/tot:.1f})")
    print(f"  Obs prep (deepcopy): {t_obs_prep:.2f}s ({t_obs_prep/tot*100:.1f}%)")
    print(f"  Agent A act:         {t_agent_a:.2f}s ({t_agent_a/tot*100:.1f}%)")
    print(f"  Agent B act:         {t_agent_b:.2f}s ({t_agent_b/tot*100:.1f}%)")
    print(f"  Env step:            {t_env_step:.2f}s ({t_env_step/tot*100:.1f}%)")

if __name__ == '__main__':
    run_profiled()
