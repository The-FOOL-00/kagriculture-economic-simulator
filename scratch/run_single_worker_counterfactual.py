import sys
import os
import json
import kaggle_environments

sys.path.insert(0, os.path.abspath('.'))

import candidates.candidate_cl_fert_gated as m1_module
from scratch.run_wheat_quota_sweep_50seeds import ParameterizedQuotaAgent

# Phase 8 Diagnostic Agent:
# ParameterizedQuotaAgent(50) + Gated Wheat Harvest (only harvest wheat when no sheep/animal is hungry or uncared)
class CausalCounterfactualAgent(ParameterizedQuotaAgent):
    def __init__(self, quota=50):
        super().__init__(quota)

    def _scan_field(self, tiles, quads, seeds, shed, invs, day):
        res = super()._scan_field(tiles, quads, seeds, shed, invs, day)
        
        # Check if any animal needs attention
        has_critical_animal = (
            len(res["hungry"]) > 0 or
            len(res["care_a"]) > 0 or
            int(shed.get("SHEEP", 0) or 0) > 0 or
            int(shed.get("COW", 0) or 0) > 0
        )

        # If animal needs attention, remove WHEAT from ripe_crops!
        # (Preserve STRAWBERRY and MELON in ripe_crops)
        if has_critical_animal:
            new_ripe_crops = []
            for pos in res["ripe_crops"]:
                x, y = pos
                t = tiles[y][x] if 0 <= y < 10 and 0 <= x < 10 else None
                crop = t.get("crop") if isinstance(t, dict) else None
                if crop != "WHEAT":
                    new_ripe_crops.append(pos)
                else:
                    # If day >= 28 (terminal days), still allow harvest to prevent game-end waste
                    if day >= 28:
                        new_ripe_crops.append(pos)
            res["ripe_crops"] = new_ripe_crops

        return res

def run_counterfactual_diagnostic():
    seeds = [1060, 1086, 1076, 1047, 1004]
    print(f"=== PHASE 8 CAUSAL COUNTERFACTUAL AUDIT ===")
    print(f"{'Seed':<6} | {'M1 Rew':<10} {'Q50 Rew':<10} {'Counterfact Rew':<16} | {'Diff vs M1':<12} {'Diff vs Q50':<12}")
    
    results = []
    for s in seeds:
        cfg = {"episodeSteps": 720, "seed": s}

        # 1. M1
        agent_m1 = m1_module.ClosedLoopEconomicV1()
        env = kaggle_environments.make("kaggriculture", configuration=cfg)
        steps_m1 = env.run([agent_m1, "starter"])
        rew_m1 = steps_m1[-1][0]["reward"]

        # 2. Q50
        agent_q50 = ParameterizedQuotaAgent(50)
        env = kaggle_environments.make("kaggriculture", configuration=cfg)
        steps_q50 = env.run([agent_q50, "starter"])
        rew_q50 = steps_q50[-1][0]["reward"]

        # 3. Counterfactual
        agent_cf = CausalCounterfactualAgent(50)
        env = kaggle_environments.make("kaggriculture", configuration=cfg)
        steps_cf = env.run([agent_cf, "starter"])
        rew_cf = steps_cf[-1][0]["reward"]

        diff_m1 = rew_cf - rew_m1
        diff_q50 = rew_cf - rew_q50

        print(f"{s:<6} | {rew_m1:<10,.0f} {rew_q50:<10,.0f} {rew_cf:<16,.0f} | {diff_m1:<+12,.0f} {diff_q50:<+12,.0f}")
        
        # Detailed commodity production breakdown
        def get_farm_stats(steps):
            obs = steps[-1][0]["observation"]
            priv = obs.get("private", {})
            shed = priv.get("shed", {})
            farm = obs.get("farms", [{}])[0]
            # Track sales from market transactions
            sold = {"WHEAT": 0, "WOOL": 0, "STRAWBERRY": 0, "MILK": 0, "FERTILIZER": 0}
            for step_data in steps:
                action = step_data[0].get("action") or {}
                market = action.get("market") or []
                for order in market:
                    if isinstance(order, list) and len(order) >= 3 and order[0] == "SELL":
                        item, qty = order[1], order[2]
                        if item in sold:
                            sold[item] += qty
            return sold

        stats_m1 = get_farm_stats(steps_m1)
        stats_q50 = get_farm_stats(steps_q50)
        stats_cf = get_farm_stats(steps_cf)

        print(f"  M1:  Wheat={stats_m1['WHEAT']:3d}, Wool={stats_m1['WOOL']:3d}, Straw={stats_m1['STRAWBERRY']:3d}, Milk={stats_m1['MILK']:3d}, Fert={stats_m1['FERTILIZER']:3d}")
        print(f"  Q50: Wheat={stats_q50['WHEAT']:3d}, Wool={stats_q50['WOOL']:3d}, Straw={stats_q50['STRAWBERRY']:3d}, Milk={stats_q50['MILK']:3d}, Fert={stats_q50['FERTILIZER']:3d}")
        print(f"  CF:  Wheat={stats_cf['WHEAT']:3d}, Wool={stats_cf['WOOL']:3d}, Straw={stats_cf['STRAWBERRY']:3d}, Milk={stats_cf['MILK']:3d}, Fert={stats_cf['FERTILIZER']:3d}")

        results.append({
            "seed": s,
            "rew_m1": rew_m1,
            "rew_q50": rew_q50,
            "rew_cf": rew_cf,
            "stats_m1": stats_m1,
            "stats_q50": stats_q50,
            "stats_cf": stats_cf
        })

    with open("scratch/phase8_counterfactual_results.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    run_counterfactual_diagnostic()
