"""
Benchmarking and simulation arena for Kaggriculture.
"""

import time
from kaggle_environments import make
from bot import agent as my_agent


def run_single_match(agent0, agent1, name0="Agent0", name1="Agent1", seed=None):
    cfg = {"episodeSteps": 720}
    if seed is not None:
        cfg["seed"] = seed
    env = make("kaggriculture", configuration=cfg, debug=True)
    
    t0 = time.time()
    env.run([agent0, agent1])
    elapsed = time.time() - t0
    
    step = env.steps[-1]
    reward0 = step[0].reward
    reward1 = step[1].reward
    status0 = step[0].status
    status1 = step[1].status
    
    print(f"Match: {name0} vs {name1} (seed={seed}) in {elapsed:.2f}s")
    print(f"  {name0} (P0): ${reward0:.2f} [{status0}]")
    print(f"  {name1} (P1): ${reward1:.2f} [{status1}]")
    diff = reward0 - reward1
    if diff > 0:
        print(f"  Winner: {name0} (+${diff:.2f})")
    elif diff < 0:
        print(f"  Winner: {name1} (+${-diff:.2f})")
    else:
        print("  Tie")
    return reward0, reward1


def benchmark_suite(num_matches=5):
    print("=" * 60)
    print("KAGGRICULTURE ARENA BENCHMARK SUITE")
    print("=" * 60)
    
    # 1. Against starter bot
    print("\n--- Testing against starter bot ---")
    scores_my = []
    scores_opp = []
    for i in range(num_matches):
        r0, r1 = run_single_match(my_agent, "starter", "ChampionshipBot", "StarterBot", seed=100+i)
        scores_my.append(r0)
        scores_opp.append(r1)
        
    avg_my = sum(scores_my) / len(scores_my)
    avg_opp = sum(scores_opp) / len(scores_opp)
    print(f"\nSummary vs Starter: ChampionshipBot avg = ${avg_my:.2f} vs Starter avg = ${avg_opp:.2f}")

    # 2. Self-Play
    print("\n--- Testing Self-Play ---")
    r0, r1 = run_single_match(my_agent, my_agent, "ChampionshipBot_P0", "ChampionshipBot_P1", seed=42)


if __name__ == "__main__":
    benchmark_suite(num_matches=3)
