import sys
import os
import csv
import json

sys.path.insert(0, os.path.abspath("."))
from src.environment import AgricultureEnv
from candidates.v54_plus_shop import V54PlusShopAgent
from external_repos.kaggriculture_v66_agent.main import KaggricultureV66Agent

large_loss_seeds = [1542, 1609, 1773, 1871, 1948, 1949, 1969]

results = []

for seed in large_loss_seeds:
    print(f"\n--- TRACING SEED {seed} ---")
    env = AgricultureEnv(seed=seed)
    obs = env.reset()
    
    agent_v54 = V54PlusShopAgent()
    agent_v66 = KaggricultureV66Agent()
    
    first_action_diff_step = None
    first_action_diff = None
    
    first_state_diff_step = None
    first_state_diff = None
    
    # Trace step by step
    for step in range(720):
        # Generate actions
        # Both agents are given their respective perspectives:
        # Let's check seat 0: V54 is P0, V66 is P1
        a0 = agent_v54.act(obs[0])
        a1 = agent_v66.act(obs[1])
        
        # Compare actions (accounting for coordinate/seat differences? Wait! In the environment, seat 0 and seat 1 have different home coordinates!)
        # Wait! To compare the agents identically, we can run each agent in the SAME seat against the SAME opponent, or compare their internal state/decisions!
        # When comparing V54++ vs V66, in match 0, V54++ is P0 and V66 is P1.
        # But wait! P0 and P1 have mirrored or different coordinates on the map!
        # Wait, let's verify if P0 and P1 have different layouts or if we can run:
        # Match A: P0=V54++, P1=V66
        # Match B: P0=V66, P1=V54++
        # OR even clearer: run P0=V54++ vs IDLE, and P0=V66 vs IDLE, OR run both in seat 0 against identical fixed opponent actions!
        pass

