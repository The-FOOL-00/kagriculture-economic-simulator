import os
import sys
import time
import json
import importlib.util
import statistics
import kagsim
from kaggle_environments import make

# Load V66 agent
sys.path.insert(0, os.path.abspath('external_repos/kaggriculture-v66-agent'))
from main import agent as v66_agent

# Load V2 agent
spec_v2 = importlib.util.spec_from_file_location('v2', 'agents/slot4_control_frozen_v2.py')
v2_mod = importlib.util.module_from_spec(spec_v2)
spec_v2.loader.exec_module(v2_mod)
v2_agent = v2_mod.agent

class SimpleObs:
    def __init__(self, obs_dict):
        for k, v in obs_dict.items():
            setattr(self, k, v)

class SimpleConfig:
    def __init__(self, **kwargs):
        self.episodeSteps = kwargs.get('episodeSteps', 720)
        self.actTimeout = kwargs.get('actTimeout', 5)
        self.runTimeout = kwargs.get('runTimeout', 1200)

def run_e2e_kagsim(seed):
    game = kagsim.Game(seed)
    cfg = SimpleConfig()
    for t in range(720):
        # Build agent observations
        obs0_dict = game.observe(0)
        obs1_dict = game.observe(1)
        obs0 = SimpleObs(obs0_dict)
        obs1 = SimpleObs(obs1_dict)
        
        # Agent compute
        a0 = v66_agent(obs0, cfg)
        a1 = v2_agent(obs1, cfg)
        
        game.step(a0 if isinstance(a0, dict) else {}, a1 if isinstance(a1, dict) else {})
    return game.reward(0), game.reward(1)

def run_e2e_kaggle_env(seed):
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.run([v66_agent, v2_agent])
    return env.steps[-1][0]['reward'], env.steps[-1][1]['reward']

print("Measuring End-to-End Throughput of Real Agents (V66 vs V2)...")

# 1. Measure kagsim L1 with real Python agents (10 episodes)
N_E2E = 10
t0 = time.perf_counter()
kagsim_res = []
for s in range(N_E2E):
    r0, r1 = run_e2e_kagsim(100 + s)
    kagsim_res.append((r0, r1))
t1 = time.perf_counter()
wall_kagsim = t1 - t0
eps_kagsim_e2e = N_E2E / wall_kagsim

print(f"kagsim L1 (V66 vs V2): {N_E2E} episodes in {wall_kagsim:.2f}s = {eps_kagsim_e2e:.2f} ep/s ({((wall_kagsim/N_E2E)*1000):.1f} ms/ep)")

# 2. Measure official kaggle-environments with real Python agents (3 episodes)
N_OFFICIAL = 3
t0 = time.perf_counter()
official_res = []
for s in range(N_OFFICIAL):
    r0, r1 = run_e2e_kaggle_env(100 + s)
    official_res.append((r0, r1))
t1 = time.perf_counter()
wall_official = t1 - t0
eps_official_e2e = N_OFFICIAL / wall_official

print(f"Official kaggle-env (V66 vs V2): {N_OFFICIAL} episodes in {wall_official:.2f}s = {eps_official_e2e:.2f} ep/s ({((wall_official/N_OFFICIAL)*1000):.1f} ms/ep)")

speedup_e2e = eps_kagsim_e2e / eps_official_e2e
print(f"\nREAL END-TO-END SPEEDUP: {speedup_e2e:.1f}x (NOT 2,000x!)")

e2e_data = {
    "N_kagsim": N_E2E,
    "wall_kagsim": wall_kagsim,
    "eps_kagsim_e2e": eps_kagsim_e2e,
    "ms_per_ep_kagsim": (wall_kagsim / N_E2E) * 1000,
    "N_official": N_OFFICIAL,
    "wall_official": wall_official,
    "eps_official_e2e": eps_official_e2e,
    "ms_per_ep_official": (wall_official / N_OFFICIAL) * 1000,
    "speedup_factor": speedup_e2e,
    "kagsim_results_sample": kagsim_res[:3],
    "official_results_sample": official_res[:3]
}

with open(r"forensic_verification\benchmark_raw\end_to_end_throughput.json", "w", encoding="utf-8") as f:
    json.dump(e2e_data, f, indent=2)
