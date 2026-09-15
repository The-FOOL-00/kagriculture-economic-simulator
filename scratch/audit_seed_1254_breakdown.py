import sys
import os
import json
from collections import defaultdict
import kaggle_environments

sys.path.insert(0, os.path.abspath('.'))

from scratch.qualification_counterfactual_suite import BaseQ50Agent, L_MinimalAgent

def compare_seed_1254():
    # Run Q50
    q_agent = BaseQ50Agent(50)
    cfg = {"episodeSteps": 720, "seed": 1254}
    env_q = kaggle_environments.make("kaggriculture", configuration=cfg)
    steps_q = env_q.run([q_agent, "starter"])

    # Run L_Minimal
    l_agent = L_MinimalAgent(50)
    env_l = kaggle_environments.make("kaggriculture", configuration=cfg)
    steps_l = env_l.run([l_agent, "starter"])

    # Sales
    def get_sales(steps):
        s = defaultdict(int)
        for st in steps:
            for o in (st[0].get("action") or {}).get("market", []):
                if isinstance(o, list) and len(o) >= 3 and o[0] == "SELL":
                    s[o[1]] += int(o[2])
        return dict(s)

    q_sales = get_sales(steps_q)
    l_sales = get_sales(steps_l)

    print("SEED 1254 COMPARISON:")
    print(f"Q50 Reward: ${steps_q[-1][0]['reward']}")
    print(f"L_Min Reward: ${steps_l[-1][0]['reward']}")
    print(f"Delta: ${steps_l[-1][0]['reward'] - steps_q[-1][0]['reward']:+,.2f}")
    print("\nCommodity Sales:")
    for k in set(list(q_sales.keys()) + list(l_sales.keys())):
        print(f"  {k:12s} | Q50: {q_sales.get(k, 0):4d} | L_Min: {l_sales.get(k, 0):4d} | Delta: {l_sales.get(k, 0) - q_sales.get(k, 0):+4d}")

    # Track worker actions: weed digging count vs strawberry harvest count
    def get_action_counts(steps):
        acts = defaultdict(int)
        for st in steps:
            a = st[0].get("action") or {}
            all_a = [a.get("farmer")] + (a.get("hands") or [])
            for w in all_a:
                if w and isinstance(w, list):
                    acts[w[0]] += 1
        return acts

    print("\nWorker Actions:")
    q_acts = get_action_counts(steps_q)
    l_acts = get_action_counts(steps_l)
    for k in sorted(set(list(q_acts.keys()) + list(l_acts.keys()))):
        print(f"  {k:12s} | Q50: {q_acts.get(k, 0):4d} | L_Min: {l_acts.get(k, 0):4d} | Delta: {l_acts.get(k, 0) - q_acts.get(k, 0):+4d}")

if __name__ == "__main__":
    compare_seed_1254()
