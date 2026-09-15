import sys
import os
import json
import numpy as np
from scipy import stats
from concurrent.futures import ProcessPoolExecutor
import kaggle_environments

sys.path.insert(0, os.path.abspath('.'))

from scratch.counterfactual_policies_w1_w7 import BaseQ50Agent
from scratch.labor_reservation_policies import L3_SafeWindowUrgencyAgent

class L_Minimal_CombinedAgent(BaseQ50Agent):
    """
    Minimal policy:
    1. Sort ripe crops by safe window urgency (Strawberry > Melon > Wheat)
    2. If ripe strawberry backlog > 0, suppress peripheral weed digging
    """
    def _scan_field(self, tiles, quads, seeds, shed, invs, day):
        res = super()._scan_field(tiles, quads, seeds, shed, invs, day)
        
        has_ripe_straw = False
        def crop_urgency_key(pos):
            nonlocal has_ripe_straw
            t = tiles[pos[1]][pos[0]]
            if not isinstance(t, dict): return 999
            c = t.get("crop")
            yu = t.get("yield_units", 0)
            if c == "STRAWBERRY":
                has_ripe_straw = True
                return 0 if yu >= 2 else 5
            elif c == "MELON":
                return 10
            elif c == "WHEAT":
                return 20
            return 50
        
        res["ripe_crops"].sort(key=crop_urgency_key)
        if has_ripe_straw:
            res["weeds"] = [] # Prohibit discretionary weed digging when ripe strawberries wait
        return res

POLICIES = {
    "Raw_Q50": BaseQ50Agent,
    "L3_SafeWindow": L3_SafeWindowUrgencyAgent,
    "L_Minimal_Combined": L_Minimal_CombinedAgent
}

def run_seed(args):
    p_name, seed = args
    cls = POLICIES[p_name]
    agent = cls()
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    steps = env.run([agent, "starter"])
    return p_name, seed, float(steps[-1][0]["reward"])

def main():
    seeds = list(range(1250, 1350))
    jobs = [(p, s) for p in POLICIES.keys() for s in seeds]
    results = {p: {} for p in POLICIES}

    with ProcessPoolExecutor(max_workers=11) as ex:
        for p_name, seed, rew in ex.map(run_seed, jobs, chunksize=5):
            results[p_name][seed] = rew

    q50_rews = np.array([results["Raw_Q50"][s] for s in seeds])

    for p in ["L3_SafeWindow", "L_Minimal_Combined"]:
        rews = np.array([results[p][s] for s in seeds])
        diff = rews - q50_rews
        win = np.mean(diff > 0) * 100
        t_stat, p_t = stats.ttest_rel(rews, q50_rews)
        w_stat, p_w = stats.wilcoxon(rews, q50_rews)
        print(f"Policy: {p}")
        print(f"  Mean Reward: ${np.mean(rews):,.2f}")
        print(f"  Delta vs Q50: ${np.mean(diff):+,.2f} | Win: {win:.1f}% | p(t)={p_t:.4f} | p(W)={p_w:.4f}")

if __name__ == "__main__":
    main()
