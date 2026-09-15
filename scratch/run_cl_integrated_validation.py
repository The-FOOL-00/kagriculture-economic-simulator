"""
Phase 4: Full Integration Validation & H2H Decomposition
=========================================================
Runs:
1. 100-Seed Matched Solo Tournament (Seeds 1000-1099, vs starter)
   - CL-Integrated-V1 vs CL-Economic-V1
2. 100 Direct Head-to-Head Matches vs Frozen V2 (Seeds 5000-5099, Alternating Seats)
   - CL-Integrated-V1 vs Frozen V2
3. Full 9-Component H2H Margin Gap Decomposition
4. Daily Cash Trajectory Analysis
5. Replay Purity Audit
"""

import sys
import os
import json
import time
import re
from collections import defaultdict
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import kaggle_environments
from candidates.candidate_cl_integrated_v1 import agent as integrated_agent
from candidates.candidate_cl_economic_v1 import agent as econ_agent
from candidates.slot2_aethel_refined_v2 import agent as v2_agent

CHECKPOINT_DAYS = [4, 8, 12, 16, 20, 24, 28]

def _eval_solo_match(args):
    agent_name, seed = args
    ag = integrated_agent if agent_name == "CL-Integrated-V1" else econ_agent
    try:
        cash_history = {}
        def tracking_agent(obs, cfg=None):
            day = obs.get("day", obs["step"] // 24)
            hour = obs.get("hour", obs["step"] % 24)
            if hour == 23 and day in CHECKPOINT_DAYS:
                cash_history[day] = float(obs["farms"][0].get("money") or 0.0)
            return ag(obs, cfg)

        cfg = {"episodeSteps": 720, "seed": seed}
        env = kaggle_environments.make("kaggriculture", configuration=cfg)
        env.run([tracking_agent, "starter"])
        steps = env.steps
        reward = float(steps[-1][0].get("reward") or 0.0)

        sales = defaultdict(int)
        for s in range(1, len(steps)):
            act = steps[s][0].get("action") or {}
            for o in (act.get("market") or []):
                if isinstance(o, list) and len(o) > 2 and o[0] == "SELL":
                    sales[o[1]] += int(o[2])

        return {
            "agent": agent_name, "seed": seed, "reward": reward,
            "straw_sold": sales.get("STRAWBERRY", 0),
            "wool_sold": sales.get("WOOL", 0),
            "milk_sold": sales.get("MILK", 0),
            "wheat_sold": sales.get("WHEAT", 0),
            "fert_sold": sales.get("FERTILIZER", 0),
            "cash_history": cash_history,
            "error": None
        }
    except Exception as e:
        return {"agent": agent_name, "seed": seed, "reward": 0.0, "error": str(e)}

def _eval_h2h_match(args):
    seed, cand_seat = args
    try:
        cfg = {"episodeSteps": 720, "seed": seed}
        env = kaggle_environments.make("kaggriculture", configuration=cfg)
        if cand_seat == 0:
            env.run([integrated_agent, v2_agent])
            c_idx, v_idx = 0, 1
        else:
            env.run([v2_agent, integrated_agent])
            c_idx, v_idx = 1, 0

        steps = env.steps
        c_rew = float(steps[-1][c_idx].get("reward") or 0.0)
        v_rew = float(steps[-1][v_idx].get("reward") or 0.0)
        margin = c_rew - v_rew
        win = 1 if c_rew > v_rew else (0.5 if c_rew == v_rew else 0)

        c_sales = defaultdict(int)
        v_sales = defaultdict(int)
        c_feed = 0
        v_feed = 0
        c_moves = 0
        v_moves = 0

        for s in range(1, len(steps)):
            act_c = steps[s][c_idx].get("action") or {}
            act_v = steps[s][v_idx].get("action") or {}
            for o in (act_c.get("market") or []):
                if isinstance(o, list) and len(o) > 2:
                    if o[0] == "SELL": c_sales[o[1]] += int(o[2])
                    elif o[0] == "BUY_PRODUCT" and o[1] == "WHEAT": c_feed += int(o[2])
            for o in (act_v.get("market") or []):
                if isinstance(o, list) and len(o) > 2:
                    if o[0] == "SELL": v_sales[o[1]] += int(o[2])
                    elif o[0] == "BUY_PRODUCT" and o[1] == "WHEAT": v_feed += int(o[2])

            w_c = [act_c.get("farmer")] + (act_c.get("hands") or [])
            for a in w_c:
                if isinstance(a, list) and len(a) > 0 and a[0] in ("NORTH", "SOUTH", "EAST", "WEST"): c_moves += 1
            w_v = [act_v.get("farmer")] + (act_v.get("hands") or [])
            for a in w_v:
                if isinstance(a, list) and len(a) > 0 and a[0] in ("NORTH", "SOUTH", "EAST", "WEST"): v_moves += 1

        return {
            "seed": seed, "cand_seat": cand_seat,
            "cand_reward": c_rew, "v2_reward": v_rew, "margin": margin, "win": win,
            "c_straw": c_sales.get("STRAWBERRY", 0), "v_straw": v_sales.get("STRAWBERRY", 0),
            "c_wool": c_sales.get("WOOL", 0), "v_wool": v_sales.get("WOOL", 0),
            "c_milk": c_sales.get("MILK", 0), "v_milk": v_sales.get("MILK", 0),
            "c_wheat": c_sales.get("WHEAT", 0), "v_wheat": v_sales.get("WHEAT", 0),
            "c_fert": c_sales.get("FERTILIZER", 0), "v_fert": v_sales.get("FERTILIZER", 0),
            "c_feed": c_feed, "v_feed": v_feed,
            "c_moves": c_moves, "v_moves": v_moves,
            "error": None
        }
    except Exception as e:
        return {"seed": seed, "cand_seat": cand_seat, "cand_reward": 0.0, "v2_reward": 0.0, "margin": 0.0, "win": 0, "error": str(e)}

def audit_purity(file_path):
    print(f"\nPerforming Replay Purity Audit on {file_path}...")
    with open(file_path, "r", encoding="utf-8") as f: code = f.read()
    checks = {
        "Zero base85 / base64 payloads": not bool(re.search(r"b85decode|b64decode|base64|zlib\.decompress", code)),
        "Zero historical _TRACE structures": not bool(re.search(r"_TRACE\s*=", code)),
        "Zero serialized pickle/json payloads": not bool(re.search(r"pickle\.loads|json\.loads\(zlib", code)),
        "Zero external non-standard dependencies": not bool(re.search(r"import (?!collections|math|random|copy|sys|os|json|time|deque|defaultdict)", code)),
        "Zero hardcoded step lookup tables": not bool(re.search(r"\{\s*\d+\s*:\s*\[", code)),
    }
    for desc, passed in checks.items():
        print(f"  [{'PASS' if passed else 'FAIL'}] {desc}")
    return all(checks.values())

def run_integration_validation():
    print("="*100)
    print("CL-INTEGRATED-V1 FULL VALIDATION & H2H BENCHMARKING SUITE")
    print("="*100)

    # 1. Purity Audit
    cand_path = "candidates/candidate_cl_integrated_v1.py"
    assert audit_purity(cand_path), "Purity audit failed!"

    # 2. 100-Seed Matched Solo Tournament
    print("\nRunning 100-Seed Matched Solo Tournament (Seeds 1000-1099)...")
    solo_tasks = []
    for s in range(1000, 1100):
        solo_tasks.append(("CL-Integrated-V1", s))
        solo_tasks.append(("CL-Economic-V1", s))

    solo_res = defaultdict(list)
    start_t = time.time()
    with ProcessPoolExecutor(max_workers=10) as ex:
        futs = {ex.submit(_eval_solo_match, t): t for t in solo_tasks}
        for fut in as_completed(futs):
            r = fut.result()
            solo_res[r["agent"]].append(r)
    print(f"100-seed matched solo screen completed in {time.time() - start_t:.1f}s.")

    int_rews = [r["reward"] for r in solo_res["CL-Integrated-V1"] if r["error"] is None]
    eco_rews = [r["reward"] for r in solo_res["CL-Economic-V1"] if r["error"] is None]

    eco_map = {r["seed"]: r["reward"] for r in solo_res["CL-Economic-V1"]}
    wins = sum(1 for r in solo_res["CL-Integrated-V1"] if r["reward"] > eco_map.get(r["seed"], 0))
    ties = sum(1 for r in solo_res["CL-Integrated-V1"] if r["reward"] == eco_map.get(r["seed"], 0))
    win_pct = (wins + 0.5 * ties) / len(int_rews) * 100.0

    i_mean, i_std, i_med = np.mean(int_rews), np.std(int_rews), np.median(int_rews)
    i_ci = 1.96 * i_std / np.sqrt(len(int_rews))
    e_mean, e_std, e_med = np.mean(eco_rews), np.std(eco_rews), np.median(eco_rews)
    e_ci = 1.96 * e_std / np.sqrt(len(eco_rews))

    print("\n" + "="*90)
    print("100-SEED MATCHED SOLO SCREENING RESULTS (SEEDS 1000-1099)")
    print("="*90)
    print(f"{'CANDIDATE':<22} {'MEAN REWARD ($)':<16} {'95% CI':<12} {'MEDIAN ($)':<14} {'WIN % VS ECON':<14}")
    print("-"*90)
    print(f"{'CL-Integrated-V1':<22} ${i_mean:>12,.2f}  ±${i_ci:>7,.2f}  ${i_med:>10,.2f}  {win_pct:>10.1f}%")
    print(f"{'CL-Economic-V1 (Base)':<22} ${e_mean:>12,.2f}  ±${e_ci:>7,.2f}  ${e_med:>10,.2f}  {'Baseline':>10}")
    print("="*90)

    # 3. Direct H2H Tournament vs Frozen V2 (100 Matches, Seeds 5000-5099, Alternating Seats)
    print("\nRunning Direct H2H Tournament (100 Matches vs Frozen V2, Seeds 5000-5099)...")
    h2h_tasks = [(s, 0 if s % 2 == 0 else 1) for s in range(5000, 5100)]
    h2h_res = []
    start_t = time.time()
    with ProcessPoolExecutor(max_workers=10) as ex:
        futs = {ex.submit(_eval_h2h_match, t): t for t in h2h_tasks}
        for fut in as_completed(futs):
            h2h_res.append(fut.result())
    print(f"Direct H2H tournament completed in {time.time() - start_t:.1f}s.")

    c_rews = [r["cand_reward"] for r in h2h_res if r["error"] is None]
    v_rews = [r["v2_reward"] for r in h2h_res if r["error"] is None]
    margins = [r["margin"] for r in h2h_res if r["error"] is None]
    h2h_wins = sum(r["win"] for r in h2h_res if r["error"] is None)

    c_m, v_m = np.mean(c_rews), np.mean(v_rews)
    m_mean, m_std = np.mean(margins), np.std(margins)
    m_ci = 1.96 * m_std / np.sqrt(len(margins))
    h2h_wr = (h2h_wins / len(h2h_res)) * 100.0

    print("\n" + "="*90)
    print("DIRECT HEAD-TO-HEAD VS FROZEN V2 RESULTS (100 MATCHES, SEEDS 5000-5099)")
    print("="*90)
    print(f"Matches Played:             100 (50 Seat 0 / 50 Seat 1)")
    print(f"CL-Integrated-V1 Mean:      ${c_m:,.2f}")
    print(f"Frozen V2 Benchmark Mean:   ${v_m:,.2f}")
    print(f"Net Margin Deficit:         ${m_mean:,.2f}  ±${m_ci:,.2f}")
    print(f"Win Rate:                   {h2h_wr:.1f}%")
    print(f"Mean Strawberries Sold:     CL={np.mean([r['c_straw'] for r in h2h_res]):.1f}u  vs  V2={np.mean([r['v_straw'] for r in h2h_res]):.1f}u")
    print(f"Mean Wool Sold:             CL={np.mean([r['c_wool'] for r in h2h_res]):.1f}u  vs  V2={np.mean([r['v_wool'] for r in h2h_res]):.1f}u")
    print(f"Mean Wheat Sold:            CL={np.mean([r['c_wheat'] for r in h2h_res]):.1f}u  vs  V2={np.mean([r['v_wheat'] for r in h2h_res]):.1f}u")
    print(f"Mean Milk Sold:             CL={np.mean([r['c_milk'] for r in h2h_res]):.1f}u  vs  V2={np.mean([r['v_milk'] for r in h2h_res]):.1f}u")
    print(f"Mean Feed Bought:           CL={np.mean([r['c_feed'] for r in h2h_res]):.1f}u  vs  V2={np.mean([r['v_feed'] for r in h2h_res]):.1f}u")
    print(f"Mean Movement Turns:        CL={np.mean([r['c_moves'] for r in h2h_res]):.0f}  vs  V2={np.mean([r['v_moves'] for r in h2h_res]):.0f}")
    print("="*90)

    # 4. H2H Gap Decomposition (Base Prices)
    # Straw $120, Wool $200, Milk $160, Wheat $25, Feed $30
    d_straw = (np.mean([r['v_straw'] for r in h2h_res]) - np.mean([r['c_straw'] for r in h2h_res])) * 120.0
    d_wool = (np.mean([r['v_wool'] for r in h2h_res]) - np.mean([r['c_wool'] for r in h2h_res])) * 200.0
    d_milk = (np.mean([r['v_milk'] for r in h2h_res]) - np.mean([r['c_milk'] for r in h2h_res])) * 160.0
    d_wheat = (np.mean([r['v_wheat'] for r in h2h_res]) - np.mean([r['c_wheat'] for r in h2h_res])) * 25.0
    d_feed = (np.mean([r['c_feed'] for r in h2h_res]) - np.mean([r['v_feed'] for r in h2h_res])) * 30.0
    total_physical = d_straw + d_wool + d_milk + d_wheat + d_feed

    print("\nH2H MARGIN GAP DECOMPOSITION (AT BASE PRICE):")
    print(f"  1. Strawberry Volume Deficit:  +${d_straw:>10,.2f}  ({d_straw/abs(m_mean)*100:.1f}%)")
    print(f"  2. Wool Volume Deficit:        +${d_wool:>10,.2f}  ({d_wool/abs(m_mean)*100:.1f}%)")
    print(f"  3. Wheat Volume Deficit:       +${d_wheat:>10,.2f}  ({d_wheat/abs(m_mean)*100:.1f}%)")
    print(f"  4. Milk Volume Deficit:        +${d_milk:>10,.2f}  ({d_milk/abs(m_mean)*100:.1f}%)")
    print(f"  5. Feed Cost Excess:           +${d_feed:>10,.2f}  ({d_feed/abs(m_mean)*100:.1f}%)")
    print(f"  Total Physical Production Gap: +${total_physical:>10,.2f}  ({total_physical/abs(m_mean)*100:.1f}%)")

    # 5. Average Daily Cash Trajectory
    print("\nDAILY CASH TRAJECTORY ($) COMPARISON:")
    print(f"{'DAY':<6} {'CL-INTEGRATED ($)':<20} {'CL-ECONOMIC ($)':<20}")
    for d in CHECKPOINT_DAYS:
        i_c = np.mean([r["cash_history"].get(d, 0) for r in solo_res["CL-Integrated-V1"] if r["error"] is None])
        e_c = np.mean([r["cash_history"].get(d, 0) for r in solo_res["CL-Economic-V1"] if r["error"] is None])
        print(f"D{d:<5} ${i_c:>12,.0f}        ${e_c:>12,.0f}")

    os.makedirs("scratch", exist_ok=True)
    out_file = "scratch/cl_integrated_validation_results.json"
    with open(out_file, "w") as f:
        json.dump({
            "solo_summary": {"integrated": {"mean": i_mean, "ci95": i_ci, "median": i_med, "win_rate": win_pct},
                             "economic": {"mean": e_mean, "ci95": e_ci, "median": e_med}},
            "h2h_summary": {"cand_mean": c_m, "v2_mean": v_m, "margin_mean": m_mean, "margin_ci95": m_ci, "win_rate": h2h_wr},
            "decomposition": {"straw": d_straw, "wool": d_wool, "milk": d_milk, "wheat": d_wheat, "feed": d_feed, "total": total_physical}
        }, f, indent=2)
    print(f"\nSaved all integration validation data to {out_file}")

if __name__ == "__main__":
    run_integration_validation()
