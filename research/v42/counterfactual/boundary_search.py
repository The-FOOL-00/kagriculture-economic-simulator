# SPDX-License-Identifier: MIT
"""Kagriculture V42 - Boundary Search on Land Expansion and Terminal Liquidation.

Explores exact boundary conditions across:
1. Land Expansion:
   - Cash levels: $10k, $12k, $14k, $16k, $18k, $20k
   - Timing steps: 270, 280, 290, 300, 310
   - Full terminal step 719 margin evaluation
2. Terminal Liquidation:
   - Full liquidation (100%) vs Partial liquidation (50%) vs Hold
   - Timing steps: 690, 692, 694, 696, 700, 705, 710
   - Terminal margin delta and rescue impact
"""

import copy
import json
import os
import sys
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
from research.v42.executor.safe_executor import StateAwareExecutor
from candidates.v32_rlx2.opponents import load_league_opponent

SEEDS = [249635, 249636, 249637, 249638, 249640, 249644, 249650, 249657]
OPPONENTS = ["E8_DMITRII", "E2_A7", "E0_V3", "SYN_AGG"]


def run_land_boundary_search():
    print("=" * 80)
    print("RUNNING LAND EXPANSION BOUNDARY SEARCH (FULL TERMINAL STEP 719 EVALUATION)")
    print("=" * 80)

    cash_buckets = [10000, 12000, 14000, 16000, 18000, 20000]
    results_by_cash = {c: [] for c in cash_buckets}
    results_by_step = {s: [] for s in [270, 280, 290, 300, 310]}

    for seed in SEEDS:
        for opp_id in OPPONENTS:
            sim = FastKagricultureSim(seed=seed)
            opp_master = load_league_opponent(opp_id)
            v35 = StateAwareExecutor()
            obs0, obs1 = sim.reset(seed=seed)

            while obs0["step"] < 270 and not sim.done:
                a0 = v35.execute(0, obs0, player=0)
                a1 = opp_master(obs1)
                [obs0, obs1], _, _, _ = sim.step([a0, a1])

            # Test steps 270, 280, 290, 300, 310
            for target_step in [270, 280, 290, 300, 310]:
                while obs0["step"] < target_step and not sim.done:
                    a0 = v35.execute(0, obs0, player=0)
                    a1 = opp_master(obs1)
                    [obs0, obs1], _, _, _ = sim.step([a0, a1])

                if sim.done:
                    break

                cash = float(obs0["farms"][0].get("money", 0.0))
                quads = len(obs0["farms"][0].get("unlocked_quadrants", []))

                if quads >= 4 or cash < 9000.0:
                    continue

                # Run baseline to 719
                sim_base = copy.deepcopy(sim)
                v35_base = StateAwareExecutor()
                opp_base = copy.deepcopy(opp_master)
                ob0, ob1 = copy.deepcopy(obs0), copy.deepcopy(obs1)
                while not sim_base.done:
                    [ob0, ob1], _, _, _ = sim_base.step([v35_base.execute(0, ob0, player=0), opp_base(ob1)])

                base_margin = ob0["farms"][0]["money"] - ob1["farms"][1]["money"]
                base_win = base_margin > 0

                # Run land expand branch to 719
                sim_cand = copy.deepcopy(sim)
                v35_cand = StateAwareExecutor()
                opp_cand = copy.deepcopy(opp_master)
                oc0, oc1 = copy.deepcopy(obs0), copy.deepcopy(obs1)
                # Inject BUY_LAND
                act_c = v35_cand.execute(7, oc0, player=0)
                # Force buy land order to test the counterfactual
                if not any(o[0] == "BUY_LAND" for o in act_c.get("market", [])):
                    act_c.setdefault("market", []).append(["BUY_LAND"])
                [oc0, oc1], _, _, _ = sim_cand.step([act_c, opp_cand(oc1)])

                while not sim_cand.done:
                    [oc0, oc1], _, _, _ = sim_cand.step([v35_cand.execute(0, oc0, player=0), opp_cand(oc1)])

                cand_margin = oc0["farms"][0]["money"] - oc1["farms"][1]["money"]
                cand_win = cand_margin > 0
                delta_margin = cand_margin - base_margin
                delta_cash = oc0["farms"][0]["money"] - ob0["farms"][0]["money"]

                entry = {
                    "seed": seed, "opp_id": opp_id, "step": target_step,
                    "cash": cash, "quads": quads,
                    "delta_cash": delta_cash, "delta_margin": delta_margin,
                    "base_win": base_win, "cand_win": cand_win
                }

                results_by_step[target_step].append(entry)
                # Find matching cash bucket
                for cb in sorted(cash_buckets, reverse=True):
                    if cash >= cb:
                        results_by_cash[cb].append(entry)
                        break

    print("\n--- RESULTS BY CASH THRESHOLD ---")
    for cb in cash_buckets:
        entries = results_by_cash[cb]
        if entries:
            mean_dc = np.mean([e["delta_cash"] for e in entries])
            mean_dm = np.mean([e["delta_margin"] for e in entries])
            pos = sum(1 for e in entries if e["delta_margin"] > 0)
            cas = sum(1 for e in entries if e["base_win"] and not e["cand_win"])
            print(f"Cash >= ${cb:>5}: Count={len(entries):<3} | Mean Cash Delta=${mean_dc:>+8.1f} | Mean Margin Delta=${mean_dm:>+8.1f} | Pos={pos}/{len(entries)} | Casualties={cas}")

    print("\n--- RESULTS BY TIMING STEP ---")
    for st, entries in results_by_step.items():
        if entries:
            mean_dc = np.mean([e["delta_cash"] for e in entries])
            mean_dm = np.mean([e["delta_margin"] for e in entries])
            pos = sum(1 for e in entries if e["delta_margin"] > 0)
            cas = sum(1 for e in entries if e["base_win"] and not e["cand_win"])
            print(f"Step {st:>3}: Count={len(entries):<3} | Mean Cash Delta=${mean_dc:>+8.1f} | Mean Margin Delta=${mean_dm:>+8.1f} | Pos={pos}/{len(entries)} | Casualties={cas}")

    return {"by_cash": results_by_cash, "by_step": results_by_step}


def run_liquidation_boundary_search():
    print("\n" + "=" * 80)
    print("RUNNING TERMINAL LIQUIDATION BOUNDARY SEARCH (FULL vs PARTIAL vs HOLD)")
    print("=" * 80)

    test_steps = [690, 692, 694, 696, 700, 705, 710]
    modes = ["FULL", "PARTIAL"]
    results = {m: {s: [] for s in test_steps} for m in modes}

    for seed in SEEDS:
        for opp_id in OPPONENTS:
            sim = FastKagricultureSim(seed=seed)
            opp_master = load_league_opponent(opp_id)
            v35 = StateAwareExecutor()
            obs0, obs1 = sim.reset(seed=seed)

            while obs0["step"] < 690 and not sim.done:
                a0 = v35.execute(0, obs0, player=0)
                a1 = opp_master(obs1)
                [obs0, obs1], _, _, _ = sim.step([a0, a1])

            # Run baseline to 719
            sim_base = copy.deepcopy(sim)
            v35_base = StateAwareExecutor()
            opp_base = copy.deepcopy(opp_master)
            ob0, ob1 = copy.deepcopy(obs0), copy.deepcopy(obs1)
            while not sim_base.done:
                [ob0, ob1], _, _, _ = sim_base.step([v35_base.execute(0, ob0, player=0), opp_base(ob1)])

            base_cash = ob0["farms"][0]["money"]
            base_opp = ob1["farms"][1]["money"]
            base_margin = base_cash - base_opp
            base_win = base_margin > 0

            # Test each step and each mode
            for s in test_steps:
                # Advance copy of sim to step s
                sim_step = copy.deepcopy(sim)
                v35_step = StateAwareExecutor()
                opp_step = copy.deepcopy(opp_master)
                os0, os1 = copy.deepcopy(obs0), copy.deepcopy(obs1)

                while os0["step"] < s and not sim_step.done:
                    [os0, os1], _, _, _ = sim_step.step([v35_step.execute(0, os0, player=0), opp_step(os1)])

                if sim_step.done:
                    continue

                for mode in modes:
                    sim_cand = copy.deepcopy(sim_step)
                    v35_cand = StateAwareExecutor()
                    opp_cand = copy.deepcopy(opp_step)
                    oc0, oc1 = copy.deepcopy(os0), copy.deepcopy(os1)

                    act_id = 1 if mode == "FULL" else 2
                    act_c = v35_cand.execute(act_id, oc0, player=0)
                    [oc0, oc1], _, _, _ = sim_cand.step([act_c, opp_cand(oc1)])

                    while not sim_cand.done:
                        [oc0, oc1], _, _, _ = sim_cand.step([v35_cand.execute(0, oc0, player=0), opp_cand(oc1)])

                    cand_cash = oc0["farms"][0]["money"]
                    cand_opp = oc1["farms"][1]["money"]
                    cand_margin = cand_cash - cand_opp
                    cand_win = cand_margin > 0

                    delta_cash = cand_cash - base_cash
                    delta_margin = cand_margin - base_margin
                    is_rescue = (not base_win) and cand_win
                    is_cas = base_win and (not cand_win)

                    results[mode][s].append({
                        "seed": seed, "opp_id": opp_id, "step": s, "mode": mode,
                        "delta_cash": delta_cash, "delta_margin": delta_margin,
                        "base_win": base_win, "cand_win": cand_win,
                        "rescue": is_rescue, "casualty": is_cas
                    })

    for mode in modes:
        print(f"\n--- {mode} LIQUIDATION RESULTS BY STEP ---")
        for s in test_steps:
            entries = results[mode][s]
            if entries:
                mean_dc = np.mean([e["delta_cash"] for e in entries])
                mean_dm = np.mean([e["delta_margin"] for e in entries])
                pos = sum(1 for e in entries if e["delta_cash"] > 0)
                res = sum(1 for e in entries if e["rescue"])
                cas = sum(1 for e in entries if e["casualty"])
                p5 = np.percentile([e["delta_cash"] for e in entries], 5)
                p95 = np.percentile([e["delta_cash"] for e in entries], 95)
                print(f"Step {s:>3} ({mode:<7}): Count={len(entries):<3} | Mean dCash=${mean_dc:>+7.1f} | P5=${p5:>+7.1f} | P95=${p95:>+7.1f} | Pos={pos}/{len(entries)} | Res={res} | Cas={cas}")

    # Save artifact
    out_json = os.path.join(REPO_ROOT, "research", "v42", "artifacts", "boundary_search_results.json")
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nSaved boundary search results to {out_json}")
    return results


if __name__ == "__main__":
    # run_land_boundary_search() # Already completed above
    run_liquidation_boundary_search()
