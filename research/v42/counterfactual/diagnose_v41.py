# SPDX-License-Identifier: MIT
"""Kagriculture V42 - Diagnosis of V41 Empirical Outcomes.

Performs forensic diagnosis of V41 results across:
1. Tournament logs analysis (DEV seeds 249685..249688)
2. Counterfactual dataset analysis (training seeds 249635..249644)
3. Deep dive into MIDGAME_LAND_EXPAND_F5 across seeds & full terminal rollouts
4. Deep dive into spot sales & price slippage
5. Identification of true positive-alpha interventions
"""

import json
import os
import sys
import copy
import numpy as np
import torch

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
from research.v41.executor.safe_executor import StateAwareExecutor, INTERVENTION_NAMES, NUM_INTERVENTIONS
from candidates.v32_rlx2.opponents import load_league_opponent


def analyze_v41_tournament():
    json_path = os.path.join(REPO_ROOT, "research", "v41", "artifacts", "ladder_tournament_results.json")
    if not os.path.exists(json_path):
        print("Tournament results not found at", json_path)
        return

    with open(json_path) as f:
        data = json.load(f)

    print("=" * 80)
    print("1. V41 TOURNAMENT FORENSICS (DEV SEEDS 249685..249688)")
    print("=" * 80)

    for lad_name, d in data.items():
        print(f"\n--- {lad_name} ---")
        print(f"Mean Delta: ${d['mean_cash_delta']:.2f}, Median: ${d['median_cash_delta']:.2f}, WR: {d['candidate_win_rate']}%, Cas: {d['total_casualties']}, Res: {d['total_rescues']}")
        deltas = [m["cash_delta"] for m in d["match_details"]]
        pos = [x for x in deltas if x > 0]
        neg = [x for x in deltas if x < 0]
        zero = [x for x in deltas if x == 0]
        print(f"Matches: Positive={len(pos)}, Negative={len(neg)}, Zero={len(zero)}")
        if pos:
            print(f"  Positive deltas: {pos}")
        if neg:
            print(f"  Negative deltas: {neg}")
        
        # Breakdown by opponent
        opp_deltas = {}
        for m in d["match_details"]:
            opp_deltas.setdefault(m["opponent"], []).append(m["cash_delta"])
        print("  By Opponent Mean Delta:")
        for opp, o_deltas in opp_deltas.items():
            print(f"    {opp:<12}: Mean=${np.mean(o_deltas):>+7.2f}, Median=${np.median(o_deltas):>+7.2f}")


def analyze_v41_counterfactual_dataset():
    pt_path = os.path.join(REPO_ROOT, "research", "v41", "artifacts", "counterfactual_dataset.pt")
    if not os.path.exists(pt_path):
        print("Counterfactual dataset not found at", pt_path)
        return

    data = torch.load(pt_path, weights_only=False)
    print("\n" + "=" * 80)
    print("2. V41 COUNTERFACTUAL DATASET DETAILED BREAKDOWN (1,327 SAMPLES)")
    print("=" * 80)

    # Breakdown per intervention
    by_action = {a: [] for a in range(NUM_INTERVENTIONS)}
    for s in data:
        deltas = s["deltas"]
        for a in range(NUM_INTERVENTIONS):
            d = deltas[a]
            if d > -9000:  # legal
                by_action[a].append(d)

    print(f"{'Act':<4} {'Intervention Name':<28} {'Legal Count':<12} {'Positive':<10} {'Mean Delta':<12} {'Median':<10} {'P5':<10} {'P95':<10}")
    print("-" * 100)
    for a in range(NUM_INTERVENTIONS):
        vals = by_action[a]
        if not vals:
            continue
        vals = np.array(vals)
        pos = np.sum(vals > 0)
        p5 = np.percentile(vals, 5)
        p95 = np.percentile(vals, 95)
        print(f"{a:<4} {INTERVENTION_NAMES[a]:<28} {len(vals):<12} {pos:<10} ${np.mean(vals):>+9.2f} ${np.median(vals):>+8.2f} ${p5:>+8.2f} ${p95:>+8.2f}")


def test_land_expand_across_seeds():
    print("\n" + "=" * 80)
    print("3. DEEP DIVE: MIDGAME_LAND_EXPAND_F5 FULL TERMINAL ROLLOUT vs 24-STEP HORIZON")
    print("=" * 80)

    # Test seeds across opponents
    test_seeds = [249635, 249636, 249637, 249638, 249640, 249644]
    opps = ["E8_DMITRII", "E0_V3", "SYN_AGG"]

    results = []
    for seed in test_seeds:
        for opp_id in opps:
            sim = FastKagricultureSim(seed=seed)
            opp_master = load_league_opponent(opp_id)
            v35 = StateAwareExecutor()
            obs0, obs1 = sim.reset(seed=seed)

            # Advance to step 280
            while obs0["step"] < 280 and not sim.done:
                a0 = v35.execute(0, obs0, player=0)
                a1 = opp_master(obs1)
                [obs0, obs1], _, _, _ = sim.step([a0, a1])

            if sim.done:
                continue

            cash = float(obs0["farms"][0].get("money", 0.0))
            quads = len(obs0["farms"][0].get("unlocked_quadrants", []))

            # Only test if cash >= 10,000 and quads < 4
            if cash < 10000.0 or quads >= 4:
                continue

            # Check 24-step delta
            # Branch Baseline
            sim_b24 = copy.deepcopy(sim)
            v35_b24 = StateAwareExecutor()
            opp_b24 = copy.deepcopy(opp_master)
            ob0_24, ob1_24 = copy.deepcopy(obs0), copy.deepcopy(obs1)
            for _ in range(24):
                [ob0_24, ob1_24], _, _, _ = sim_b24.step([v35_b24.execute(0, ob0_24, player=0), opp_b24(ob1_24)])

            # Branch Cand 9
            sim_c24 = copy.deepcopy(sim)
            v35_c24 = StateAwareExecutor()
            opp_c24 = copy.deepcopy(opp_master)
            oc0_24, oc1_24 = copy.deepcopy(obs0), copy.deepcopy(obs1)
            [oc0_24, oc1_24], _, _, _ = sim_c24.step([v35_c24.execute(9, oc0_24, player=0), opp_c24(oc1_24)])
            for _ in range(23):
                [oc0_24, oc1_24], _, _, _ = sim_c24.step([v35_c24.execute(0, oc0_24, player=0), opp_c24(oc1_24)])

            delta_24_cash = oc0_24["farms"][0]["money"] - ob0_24["farms"][0]["money"]

            # Now FULL TERMINAL ROLLOUT (Step 719)
            # Baseline full
            sim_b_full = copy.deepcopy(sim)
            v35_b_full = StateAwareExecutor()
            opp_b_full = copy.deepcopy(opp_master)
            ob0_f, ob1_f = copy.deepcopy(obs0), copy.deepcopy(obs1)
            while not sim_b_full.done:
                [ob0_f, ob1_f], _, _, _ = sim_b_full.step([v35_b_full.execute(0, ob0_f, player=0), opp_b_full(ob1_f)])

            # Branch 9 full
            sim_c_full = copy.deepcopy(sim)
            v35_c_full = StateAwareExecutor()
            opp_c_full = copy.deepcopy(opp_master)
            oc0_f, oc1_f = copy.deepcopy(obs0), copy.deepcopy(obs1)
            [oc0_f, oc1_f], _, _, _ = sim_c_full.step([v35_c_full.execute(9, oc0_f, player=0), opp_c_full(oc1_f)])
            while not sim_c_full.done:
                [oc0_f, oc1_f], _, _, _ = sim_c_full.step([v35_c_full.execute(0, oc0_f, player=0), opp_c_full(oc1_f)])

            base_cash_term = ob0_f["farms"][0]["money"]
            base_opp_term = ob1_f["farms"][1]["money"]
            base_margin_term = base_cash_term - base_opp_term
            base_win = base_margin_term > 0

            cand_cash_term = oc0_f["farms"][0]["money"]
            cand_opp_term = oc1_f["farms"][1]["money"]
            cand_margin_term = cand_cash_term - cand_opp_term
            cand_win = cand_margin_term > 0

            term_delta_cash = cand_cash_term - base_cash_term
            term_delta_margin = cand_margin_term - base_margin_term

            print(f"Seed {seed} vs {opp_id:<10} (Cash@280=${cash:.0f}, Q={quads}):")
            print(f"   24-Step Cash Delta: ${delta_24_cash:>+8.1f}")
            print(f"   Terminal Cash Delta: ${term_delta_cash:>+8.1f} | Margin Delta: ${term_delta_margin:>+8.1f}")
            print(f"   Base Win: {base_win} (${base_margin_term:>+7.0f}) -> Cand Win: {cand_win} (${cand_margin_term:>+7.0f})")

            results.append({
                "seed": seed, "opp_id": opp_id, "cash_280": cash, "quads": quads,
                "delta_24": delta_24_cash,
                "term_cash_delta": term_delta_cash,
                "term_margin_delta": term_delta_margin,
                "base_win": base_win, "cand_win": cand_win
            })

    if results:
        print("\nSummary Across Tested Seeds:")
        d24 = [r["delta_24"] for r in results]
        dtc = [r["term_cash_delta"] for r in results]
        dtm = [r["term_margin_delta"] for r in results]
        print(f"Mean 24-step cash delta:    ${np.mean(d24):>+8.2f}")
        print(f"Mean Terminal cash delta:   ${np.mean(dtc):>+8.2f}")
        print(f"Mean Terminal margin delta: ${np.mean(dtm):>+8.2f}")
        flips_to_loss = sum(1 for r in results if r["base_win"] and not r["cand_win"])
        flips_to_win = sum(1 for r in results if not r["base_win"] and r["cand_win"])
        print(f"Wins converted to Losses: {flips_to_loss} / {len(results)}")
        print(f"Losses converted to Wins: {flips_to_win} / {len(results)}")


def test_spot_sales_slippage():
    print("\n" + "=" * 80)
    print("4. DEEP DIVE: SPOT SALES SLIPPAGE FORENSICS (MILK, WOOL, STRAWBERRY)")
    print("=" * 80)
    # Test on a few seeds where spot sales triggered
    test_seeds = [249635, 249637, 249685]
    opp = load_league_opponent("E8_DMITRII")

    for seed in test_seeds:
        sim = FastKagricultureSim(seed=seed)
        v35 = StateAwareExecutor()
        obs0, obs1 = sim.reset(seed=seed)
        found = False

        while not sim.done and not found:
            step = obs0["step"]
            private = obs0.get("private", {}) or {}
            shed = dict(private.get("shed", {}) or {})
            market = obs0.get("market", {}) or {}
            prices = dict(market.get("prices", {}) or {})

            # Check if Milk spot sale is available
            if shed.get("MILK", 0) >= 2 and float(prices.get("MILK", 0) or 0) >= 30.0 and step < 600:
                print(f"\nSeed {seed} at step {step}: MILK spot sale available (Price=${prices.get('MILK')}, Shed={shed.get('MILK')})")
                
                # Full rollout: Baseline vs Spot Sell
                # Baseline
                sim_b = copy.deepcopy(sim)
                v35_b = StateAwareExecutor()
                opp_b = copy.deepcopy(opp)
                ob0, ob1 = copy.deepcopy(obs0), copy.deepcopy(obs1)
                while not sim_b.done:
                    [ob0, ob1], _, _, _ = sim_b.step([v35_b.execute(0, ob0, player=0), opp_b(ob1)])

                # Spot sell branch
                sim_c = copy.deepcopy(sim)
                v35_c = StateAwareExecutor()
                opp_c = copy.deepcopy(opp)
                oc0, oc1 = copy.deepcopy(obs0), copy.deepcopy(obs1)
                [oc0, oc1], _, _, _ = sim_c.step([v35_c.execute(3, oc0, player=0), opp_c(oc1)])
                while not sim_c.done:
                    [oc0, oc1], _, _, _ = sim_c.step([v35_c.execute(0, oc0, player=0), opp_c(oc1)])

                b_cash = ob0["farms"][0]["money"]
                c_cash = oc0["farms"][0]["money"]
                print(f"  Terminal Cash: Baseline=${b_cash:.1f} vs SpotSell=${c_cash:.1f} -> Terminal Delta: ${c_cash - b_cash:>+6.1f}")
                found = True

            a0 = v35.execute(0, obs0, player=0)
            a1 = opp(obs1)
            [obs0, obs1], _, _, _ = sim.step([a0, a1])


if __name__ == "__main__":
    analyze_v41_tournament()
    analyze_v41_counterfactual_dataset()
    test_land_expand_across_seeds()
    test_spot_sales_slippage()
