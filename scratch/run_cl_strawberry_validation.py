"""
Full Robust Validation & Benchmarking for CL-Strawberry-V1
==========================================================
Executes:
1. 100-Seed Matched Screen vs CL-Economic-V1 (Seeds 1000-1099, vs starter)
2. 100 Direct Head-to-Head Matches vs Frozen V2 (Seeds 5000-5099, 50 Seat 0 / 50 Seat 1)
3. Macroeconomic Perturbation Suite (50 Seeds 2000-2049):
   - Low Capital: $2,250 (-25%)
   - High Capital: $3,750 (+25%)
4. Static & Semantic Replay Purity Audits
"""

import sys
import os
import json
import time
import re
import hashlib
from collections import defaultdict
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import kaggle_environments
from candidates.candidate_cl_strawberry_v1 import agent as straw_agent
from candidates.candidate_cl_economic_v1 import agent as econ_agent
from candidates.slot2_aethel_refined_v2 import agent as v2_agent

# ---------------------------------------------------------------------------
# Part 1: Matched Solo Screen (100 Seeds 1000-1099)
# ---------------------------------------------------------------------------
def _eval_solo_seed(args):
    agent_name, seed = args
    ag = straw_agent if agent_name == "CL-Strawberry-V1" else econ_agent
    try:
        cfg = {"episodeSteps": 720, "seed": seed}
        env = kaggle_environments.make("kaggriculture", configuration=cfg)
        env.run([ag, "starter"])
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
            "melon_sold": sales.get("MELON", 0),
            "error": None
        }
    except Exception as e:
        return {"agent": agent_name, "seed": seed, "reward": 0.0, "error": str(e)}

# ---------------------------------------------------------------------------
# Part 2: Direct H2H vs Frozen V2 (100 Matches Seeds 5000-5099, Alternating Seats)
# ---------------------------------------------------------------------------
def _eval_h2h_match(args):
    seed, cand_seat = args
    try:
        cfg = {"episodeSteps": 720, "seed": seed}
        env = kaggle_environments.make("kaggriculture", configuration=cfg)
        if cand_seat == 0:
            env.run([straw_agent, v2_agent])
            c_idx, v_idx = 0, 1
        else:
            env.run([v2_agent, straw_agent])
            c_idx, v_idx = 1, 0
            
        steps = env.steps
        c_rew = float(steps[-1][c_idx].get("reward") or 0.0)
        v_rew = float(steps[-1][v_idx].get("reward") or 0.0)
        margin = c_rew - v_rew
        win = 1 if c_rew > v_rew else (0.5 if c_rew == v_rew else 0)
        
        # Sales breakdown
        c_sales = defaultdict(int)
        v_sales = defaultdict(int)
        for s in range(1, len(steps)):
            act_c = steps[s][c_idx].get("action") or {}
            act_v = steps[s][v_idx].get("action") or {}
            for o in (act_c.get("market") or []):
                if isinstance(o, list) and len(o) > 2 and o[0] == "SELL": c_sales[o[1]] += int(o[2])
            for o in (act_v.get("market") or []):
                if isinstance(o, list) and len(o) > 2 and o[0] == "SELL": v_sales[o[1]] += int(o[2])
                
        return {
            "seed": seed, "cand_seat": cand_seat,
            "cand_reward": c_rew, "v2_reward": v_rew, "margin": margin, "win": win,
            "cand_straw": c_sales.get("STRAWBERRY", 0), "v2_straw": v_sales.get("STRAWBERRY", 0),
            "cand_wool": c_sales.get("WOOL", 0), "v2_wool": v_sales.get("WOOL", 0),
            "cand_wheat": c_sales.get("WHEAT", 0), "v2_wheat": v_sales.get("WHEAT", 0),
            "cand_milk": c_sales.get("MILK", 0), "v2_milk": v_sales.get("MILK", 0),
            "error": None
        }
    except Exception as e:
        return {"seed": seed, "cand_seat": cand_seat, "cand_reward": 0.0, "v2_reward": 0.0, "margin": 0.0, "win": 0, "error": str(e)}

# ---------------------------------------------------------------------------
# Part 3: Perturbation Evaluation
# ---------------------------------------------------------------------------
def _eval_perturb(args):
    scenario, starting_money, seed = args
    try:
        # In kaggriculture, starting money is in config or farm setup
        cfg = {"episodeSteps": 720, "seed": seed, "startingMoney": starting_money}
        env = kaggle_environments.make("kaggriculture", configuration=cfg)
        env.run([straw_agent, "starter"])
        reward = float(env.steps[-1][0].get("reward") or 0.0)
        return {"scenario": scenario, "seed": seed, "reward": reward, "error": None}
    except Exception as e:
        return {"scenario": scenario, "seed": seed, "reward": 0.0, "error": str(e)}

# ---------------------------------------------------------------------------
# Part 4: Purity & Replay Audit
# ---------------------------------------------------------------------------
def audit_purity(file_path):
    print(f"\nPerforming Replay Purity Audit on {file_path}...")
    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()
        
    checks = {
        "Zero base85 / base64 payloads": not bool(re.search(r"b85decode|b64decode|base64|zlib\.decompress", code)),
        "Zero historical _TRACE structures": not bool(re.search(r"_TRACE\s*=", code)),
        "Zero serialized pickle/json payloads": not bool(re.search(r"pickle\.loads|json\.loads\(zlib", code)),
        "Zero external non-standard dependencies": not bool(re.search(r"import (?!collections|math|random|copy|sys|os|json|time|deque|defaultdict)", code)),
        "Zero hardcoded step lookup tables": not bool(re.search(r"\{\s*\d+\s*:\s*\[", code)),
    }
    all_passed = all(checks.values())
    for desc, passed in checks.items():
        print(f"  [{'PASS' if passed else 'FAIL'}] {desc}")
    return all_passed

def run_full_validation():
    print("="*100)
    print("CL-STRAWBERRY-V1 ROBUST VALIDATION & BENCHMARKING SUITE")
    print("="*100)
    
    # 1. Purity Audit
    cand_file = "candidates/candidate_cl_strawberry_v1.py"
    purity_ok = audit_purity(cand_file)
    assert purity_ok, "Purity audit failed!"
    
    # 2. 100-Seed Matched Screen
    print("\nRunning 100-Seed Matched Screen (Seeds 1000-1099, vs starter)...")
    solo_tasks = []
    for s in range(1000, 1100):
        solo_tasks.append(("CL-Strawberry-V1", s))
        solo_tasks.append(("CL-Economic-V1", s))
        
    solo_res = defaultdict(list)
    start_t = time.time()
    with ProcessPoolExecutor(max_workers=10) as ex:
        futs = {ex.submit(_eval_solo_seed, t): t for t in solo_tasks}
        for fut in as_completed(futs):
            r = fut.result()
            solo_res[r["agent"]].append(r)
    print(f"100-seed matched screen completed in {time.time() - start_t:.1f}s.")
    
    straw_rews = [r["reward"] for r in solo_res["CL-Strawberry-V1"] if r["error"] is None]
    econ_rews = [r["reward"] for r in solo_res["CL-Economic-V1"] if r["error"] is None]
    
    # Matched comparison
    econ_map = {r["seed"]: r["reward"] for r in solo_res["CL-Economic-V1"]}
    wins = sum(1 for r in solo_res["CL-Strawberry-V1"] if r["reward"] > econ_map.get(r["seed"], 0))
    ties = sum(1 for r in solo_res["CL-Strawberry-V1"] if r["reward"] == econ_map.get(r["seed"], 0))
    win_pct = (wins + 0.5 * ties) / len(straw_rews) * 100.0
    
    s_mean, s_std, s_med = np.mean(straw_rews), np.std(straw_rews), np.median(straw_rews)
    s_ci = 1.96 * s_std / np.sqrt(len(straw_rews))
    e_mean, e_std, e_med = np.mean(econ_rews), np.std(econ_rews), np.median(econ_rews)
    e_ci = 1.96 * e_std / np.sqrt(len(econ_rews))
    
    print("\n" + "="*90)
    print("100-SEED MATCHED SCREENING RESULTS (SEEDS 1000-1099)")
    print("="*90)
    print(f"{'CANDIDATE':<22} {'MEAN REWARD ($)':<16} {'95% CI':<12} {'MEDIAN ($)':<14} {'WIN % VS ECON':<14}")
    print("-"*90)
    print(f"{'CL-Strawberry-V1':<22} ${s_mean:>12,.2f}  ±${s_ci:>7,.2f}  ${s_med:>10,.2f}  {win_pct:>10.1f}%")
    print(f"{'CL-Economic-V1 (Base)':<22} ${e_mean:>12,.2f}  ±${e_ci:>7,.2f}  ${e_med:>10,.2f}  {'Baseline':>10}")
    print("="*90)
    
    # 3. Direct H2H vs Frozen V2 (100 Seeds 5000-5099, Alternating Seats)
    print("\nRunning Direct H2H Tournament (100 Matches vs Frozen V2, Seeds 5000-5099)...")
    h2h_tasks = []
    for s in range(5000, 5100):
        seat = 0 if (s % 2 == 0) else 1
        h2h_tasks.append((s, seat))
        
    start_t = time.time()
    h2h_res = []
    with ProcessPoolExecutor(max_workers=10) as ex:
        futs = {ex.submit(_eval_h2h_match, t): t for t in h2h_tasks}
        for fut in as_completed(futs):
            h2h_res.append(fut.result())
    print(f"Direct H2H tournament completed in {time.time() - start_t:.1f}s.")
    
    h2h_cand_rews = [r["cand_reward"] for r in h2h_res if r["error"] is None]
    h2h_v2_rews = [r["v2_reward"] for r in h2h_res if r["error"] is None]
    margins = [r["margin"] for r in h2h_res if r["error"] is None]
    h2h_wins = sum(r["win"] for r in h2h_res if r["error"] is None)
    
    h_c_mean = np.mean(h2h_cand_rews)
    h_v_mean = np.mean(h2h_v2_rews)
    margin_mean = np.mean(margins)
    margin_std = np.std(margins)
    margin_ci = 1.96 * margin_std / np.sqrt(len(margins))
    h2h_win_rate = (h2h_wins / len(h2h_res)) * 100.0
    
    print("\n" + "="*90)
    print("DIRECT HEAD-TO-HEAD VS FROZEN V2 RESULTS (100 MATCHES, SEEDS 5000-5099)")
    print("="*90)
    print(f"Matches Played:             100 (50 Seat 0, 50 Seat 1)")
    print(f"CL-Strawberry-V1 Mean:      ${h_c_mean:,.2f}")
    print(f"Frozen V2 Benchmark Mean:   ${h_v_mean:,.2f}")
    print(f"Net Margin (CL - V2):       ${margin_mean:,.2f}  ±${margin_ci:,.2f}")
    print(f"Win Rate:                   {h2h_win_rate:.1f}%")
    print(f"Mean Strawberries Sold:     CL={np.mean([r['cand_straw'] for r in h2h_res]):.1f}u  vs  V2={np.mean([r['v2_straw'] for r in h2h_res]):.1f}u")
    print(f"Mean Wool Sold:             CL={np.mean([r['cand_wool'] for r in h2h_res]):.1f}u  vs  V2={np.mean([r['v2_wool'] for r in h2h_res]):.1f}u")
    print("="*90)
    
    # 4. Macroeconomic Perturbation Suite (50 Seeds 2000-2049)
    print("\nRunning Macroeconomic Perturbation Suite (50 Seeds 2000-2049)...")
    perturb_tasks = []
    for s in range(2000, 2050):
        perturb_tasks.append(("Baseline ($3,000)", 3000, s))
        perturb_tasks.append(("Low Capital ($2,250, -25%)", 2250, s))
        perturb_tasks.append(("High Capital ($3,750, +25%)", 3750, s))
        
    perturb_res = defaultdict(list)
    start_t = time.time()
    with ProcessPoolExecutor(max_workers=10) as ex:
        futs = {ex.submit(_eval_perturb, t): t for t in perturb_tasks}
        for fut in as_completed(futs):
            r = fut.result()
            perturb_res[r["scenario"]].append(r["reward"])
    print(f"Perturbation suite completed in {time.time() - start_t:.1f}s.")
    
    print("\n" + "="*90)
    print("MACROECONOMIC PERTURBATION ROBUSTNESS GAUNTLET")
    print("="*90)
    for sc in ["Baseline ($3,000)", "Low Capital ($2,250, -25%)", "High Capital ($3,750, +25%)"]:
        rews = perturb_res[sc]
        m, s = np.mean(rews), np.std(rews)
        ci = 1.96 * s / np.sqrt(len(rews))
        print(f"{sc:<30}: Mean = ${m:>10,.2f}  ±${ci:>7,.2f}")
    print("="*90)
    
    # Save full audit results
    os.makedirs("scratch", exist_ok=True)
    out_data = {
        "solo_summary": {
            "cl_strawberry_v1": {"mean": s_mean, "std": s_std, "median": s_med, "ci95": s_ci, "win_rate": win_pct},
            "cl_economic_v1": {"mean": e_mean, "std": e_std, "median": e_med, "ci95": e_ci}
        },
        "h2h_summary": {
            "cand_mean": h_c_mean, "v2_mean": h_v_mean, "margin_mean": margin_mean,
            "margin_ci95": margin_ci, "win_rate": h2h_win_rate
        },
        "perturbation_summary": {
            sc: {"mean": float(np.mean(perturb_res[sc])), "ci95": float(1.96 * np.std(perturb_res[sc]) / np.sqrt(len(perturb_res[sc])))}
            for sc in perturb_res
        }
    }
    with open("scratch/strawberry_validation_final_results.json", "w") as f:
        json.dump(out_data, f, indent=2)
    print("\nSaved all validation results to scratch/strawberry_validation_final_results.json")

if __name__ == "__main__":
    run_full_validation()
