import sys
import os
import json
import kaggle_environments

sys.path.insert(0, os.path.abspath('.'))

import candidates.candidate_cl_fert_gated as m1_module
from scratch.run_wheat_quota_sweep_50seeds import ParameterizedQuotaAgent

# Candidate: M1 + Quota 50 + Defer Wheat Harvest to Hour >= 12
class Quota50WheatDeferralAgent(ParameterizedQuotaAgent):
    def __init__(self, quota=50):
        super().__init__(quota)

    def _scan_field(self, tiles, quads, seeds, shed, invs, day):
        res = super()._scan_field(tiles, quads, seeds, shed, invs, day)
        
        # During morning hours (< 12), remove WHEAT from ripe_crops so workers finish sheep care/feed first
        # Wheat does not decay until Day P+5, so waiting until hour 12 costs 0 yield units
        hour = self._step % 24 if self._step >= 0 else 0
        if hour < 12 and day < 27:
            new_ripe = []
            for pos in res["ripe_crops"]:
                x, y = pos
                t = tiles[y][x] if 0 <= y < 10 and 0 <= x < 10 else None
                crop = t.get("crop") if isinstance(t, dict) else None
                if crop != "WHEAT":
                    new_ripe.append(pos)
            res["ripe_crops"] = new_ripe

        return res

def run_pilot():
    seeds = list(range(1000, 1010))
    print(f"=== PILOT ABLATION: QUOTA 50 + WHEAT DEFERRAL (10 SEEDS) ===")
    print(f"{'Seed':<6} | {'M1 Rew':<10} {'Q50 Rew':<10} {'Q50+Defer':<12} | {'Delta vs M1':<12} {'Wool Diff':<10} {'Wheat Diff':<10}")
    
    diffs_m1 = []
    wool_diffs = []
    wheat_diffs = []

    for s in seeds:
        cfg = {"episodeSteps": 720, "seed": s}

        # M1
        agent_m1 = m1_module.ClosedLoopEconomicV1()
        env = kaggle_environments.make("kaggriculture", configuration=cfg)
        st_m1 = env.run([agent_m1, "starter"])
        rew_m1 = st_m1[-1][0]["reward"]

        # Q50
        agent_q50 = ParameterizedQuotaAgent(50)
        env = kaggle_environments.make("kaggriculture", configuration=cfg)
        st_q50 = env.run([agent_q50, "starter"])
        rew_q50 = st_q50[-1][0]["reward"]

        # Q50 + Defer
        agent_def = Quota50WheatDeferralAgent(50)
        env = kaggle_environments.make("kaggriculture", configuration=cfg)
        st_def = env.run([agent_def, "starter"])
        rew_def = st_def[-1][0]["reward"]

        # Sales stats
        def get_sales(steps):
            sold = {"WHEAT": 0, "WOOL": 0}
            for step_data in steps:
                act = step_data[0].get("action") or {}
                for o in act.get("market", []):
                    if isinstance(o, list) and len(o) >= 3 and o[0] == "SELL":
                        if o[1] in sold: sold[o[1]] += o[2]
            return sold

        s_m1 = get_sales(st_m1)
        s_def = get_sales(st_def)

        d_rew = rew_def - rew_m1
        d_wool = s_def["WOOL"] - s_m1["WOOL"]
        d_wheat = s_def["WHEAT"] - s_m1["WHEAT"]

        diffs_m1.append(d_rew)
        wool_diffs.append(d_wool)
        wheat_diffs.append(d_wheat)

        print(f"{s:<6} | {rew_m1:<10,.0f} {rew_q50:<10,.0f} {rew_def:<12,.0f} | {d_rew:<+12,.0f} {d_wool:<+10d} {d_wheat:<+10d}")

    print(f"\n--- PILOT SUMMARY ---")
    print(f"Mean Reward Delta vs M1: ${sum(diffs_m1)/len(diffs_m1):+,.2f}")
    print(f"Mean Wool Delta vs M1:   {sum(wool_diffs)/len(wool_diffs):+.1f} units")
    print(f"Mean Wheat Delta vs M1:  {sum(wheat_diffs)/len(wheat_diffs):+.1f} units")
    print(f"Win Rate vs M1:          {sum(1 for d in diffs_m1 if d > 0)/len(diffs_m1)*100:.1f}%")

if __name__ == "__main__":
    run_pilot()
