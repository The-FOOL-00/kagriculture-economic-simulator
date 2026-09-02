# SPDX-License-Identifier: MIT
"""
Comprehensive Forensic Ablation Suite & Single-Factor Experiments (Fast Parallel)
"""

import os
import sys
import json
import copy
import time
import importlib.util
from concurrent.futures import ProcessPoolExecutor
from kaggle_environments import make

SEEDS_TRAIN = [1, 2, 5, 7, 10, 13, 17, 21, 25, 30]
SEEDS_HOLDOUT = [201, 202, 205, 210, 220, 233, 242, 255, 277, 300]

def _run_single_match_worker(args):
    agent_a_path, agent_b_path, seed, seat = args
    agents = [agent_a_path, agent_b_path] if seat == 0 else [agent_b_path, agent_a_path]
    env = make("kaggriculture", configuration={"seed": seed})
    env.run(agents)
    
    cand_idx = seat
    opp_idx = 1 - seat
    cand_reward = float(env.steps[-1][cand_idx]["reward"] or 0)
    opp_reward = float(env.steps[-1][opp_idx]["reward"] or 0)
    margin = cand_reward - opp_reward
    
    return {
        "seed": seed,
        "seat": f"P{seat}",
        "cand_reward": cand_reward,
        "opp_reward": opp_reward,
        "margin": margin,
        "is_win": margin > 0,
        "is_loss": margin < 0,
        "is_tie": margin == 0
    }

def create_ablation_agents():
    os.makedirs("scratch/ablation_forensics", exist_ok=True)
    
    # Read Closer Cleo (Aethel) source code
    with open("replays/raw/reference_agents/closer_cleo.py", "r", encoding="utf-8") as f:
        cleo_code = f.read()

    # 1. Aethel Clean (Exact Closer Cleo)
    with open("scratch/ablation_forensics/aethel_clean.py", "w", encoding="utf-8") as f:
        f.write(cleo_code)

    # 2. Aethel No Front-Running
    aethel_no_fr = cleo_code.replace("_FRONT_RUN_HORIZON = 1", "_FRONT_RUN_HORIZON = 0")
    with open("scratch/ablation_forensics/aethel_no_fr.py", "w", encoding="utf-8") as f:
        f.write(aethel_no_fr)

    # 3. Aethel No Market Controller (Raw tape only + frontrun/terminal)
    aethel_no_mc = cleo_code.replace("def agent(obs, config=None):\n    \"\"\"c27 with its SELL layer partially replaced by the market controller.\"\"\"\n    action = _base_agent(obs, config)", "def agent(obs, config=None):\n    return _base_agent(obs, config)")
    with open("scratch/ablation_forensics/aethel_no_market_controller.py", "w", encoding="utf-8") as f:
        f.write(aethel_no_mc)

    # 4. Aethel With Hydra Terminal (Step 712 instead of 717)
    aethel_t712 = cleo_code.replace("if step >= 717:", "if step >= 712:")
    with open("scratch/ablation_forensics/aethel_t712.py", "w", encoding="utf-8") as f:
        f.write(aethel_t712)

    # 5. Aethel With Hydra Knapsack Solver
    hydra_knapsack_def = """
def _knapsack_terminal_liquidation(action, obs, step):
    if step < 680:
        return
    shed = (obs.get("private") or {}).get("shed") or {}
    market = action.setdefault("market", [])
    already = {order[1] for order in market if isinstance(order, list) and len(order) >= 2 and order[0] == "SELL"}
    prices = (obs.get("market") or {}).get("prices") or {}
    sells = []
    for item in ("STRAWBERRY", "MELON", "MILK", "WOOL", "EGG", "TOMATO", "CARROT", "WHEAT", "FERTILIZER"):
        qty = int(shed.get(item, 0) or 0)
        if qty > 0 and item not in already:
            p = float(prices.get(item, 50) or 50)
            sells.append((p * qty, item, qty))
    sells.sort(reverse=True)
    for _, item, qty in sells:
        if len(market) < 10:
            market.append(["SELL", item, qty])
"""
    aethel_with_ks = cleo_code + "\n" + hydra_knapsack_def
    aethel_with_ks = aethel_with_ks.replace("_terminal_liquidation(action, obs, step)", "_terminal_liquidation(action, obs, step)\n    _knapsack_terminal_liquidation(action, obs, step)")
    with open("scratch/ablation_forensics/aethel_with_knapsack.py", "w", encoding="utf-8") as f:
        f.write(aethel_with_ks)

    # 6. Hydra V1 with Cleo's Market Controller restored
    hydra_with_mc = cleo_code + """
def _active_weed_guard(action, obs):
    player = int(obs.get("player", 0) or 0)
    farm = (obs.get("farms") or [])[player]
    tiles = farm.get("tiles") or []
    farmer_pos = farm.get("farmer", [0, 0])
    x, y = farmer_pos
    if 0 <= y < len(tiles) and 0 <= x < len(tiles[0]):
        tile = tiles[y][x]
        fa = action.get("farmer", ["PASS"])
        if isinstance(fa, list) and len(fa) > 0 and fa[0] in ("BUILD_PASTURE", "BUILD_COOP", "PLANT"):
            if isinstance(tile, dict) and (tile.get("weed") or tile.get("kind") == "WEED"):
                action["farmer"] = ["DIG"]
"""
    hydra_with_mc = hydra_with_mc.replace("action = copy.deepcopy(_TRACE[step])", "action = copy.deepcopy(_TRACE[step])\n    _active_weed_guard(action, obs)")
    with open("scratch/ablation_forensics/hydra_with_market_controller.py", "w", encoding="utf-8") as f:
        f.write(hydra_with_mc)


def run_paired_tournament_parallel(pool, agent_a_path, agent_b_path, seeds, name_a="AgentA", name_b="AgentB"):
    work_items = [(agent_a_path, agent_b_path, seed, seat) for seed in seeds for seat in (0, 1)]
    matches = list(pool.map(_run_single_match_worker, work_items))
    
    total = len(matches)
    wins = sum(1 for m in matches if m["is_win"])
    losses = sum(1 for m in matches if m["is_loss"])
    ties = sum(1 for m in matches if m["is_tie"])
    win_rate = (wins / total) * 100.0 if total > 0 else 0.0
    mean_margin = sum(m["margin"] for m in matches) / total if total > 0 else 0.0
    
    p0_wins = sum(1 for m in matches if m["seat"] == "P0" and m["is_win"])
    p1_wins = sum(1 for m in matches if m["seat"] == "P1" and m["is_win"])
    p0_total = sum(1 for m in matches if m["seat"] == "P0")
    p1_total = sum(1 for m in matches if m["seat"] == "P1")
    
    print(f"{name_a:32s} vs {name_b:20s}: {wins:2d}W - {losses:2d}L - {ties:1d}T ({win_rate:5.1f}% WR) | Mean Margin: {mean_margin:+8.1f} | P0 WR: {p0_wins/p0_total*100:4.1f}% | P1 WR: {p1_wins/p1_total*100:4.1f}%", flush=True)
    
    return {
        "candidate": name_a,
        "opponent": name_b,
        "games": total,
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "win_rate": win_rate,
        "mean_margin": mean_margin,
        "p0_wr": p0_wins / p0_total * 100 if p0_total > 0 else 0,
        "p1_wr": p1_wins / p1_total * 100 if p1_total > 0 else 0,
        "matches": matches
    }


def main():
    print("=" * 100, flush=True)
    print("STARTING HYDRA ROOT-CAUSE FORENSIC & SINGLE-FACTOR EXPERIMENTS (PARALLEL)", flush=True)
    print("=" * 100, flush=True)

    create_ablation_agents()

    aethel_path = os.path.abspath("scratch/ablation_forensics/aethel_clean.py")
    hydra_path = os.path.abspath("agents/hydra_prime.py")
    
    workers = min(12, os.cpu_count() or 4)
    print(f"Executing with {workers} parallel worker processes...", flush=True)

    with ProcessPoolExecutor(max_workers=workers) as pool:
        # 1. Component Ablation vs Aethel
        print("\n--- 1. COMPONENT ABLATION EXPERIMENTS VS AETHEL (Closer Cleo) ---", flush=True)
        exp_results = {}
        
        candidates = [
            ("Hydra_Prime_V1", hydra_path),
            ("Aethel_No_MarketController", os.path.abspath("scratch/ablation_forensics/aethel_no_market_controller.py")),
            ("Aethel_No_FrontRun", os.path.abspath("scratch/ablation_forensics/aethel_no_fr.py")),
            ("Aethel_T712_Terminal", os.path.abspath("scratch/ablation_forensics/aethel_t712.py")),
            ("Aethel_With_Knapsack", os.path.abspath("scratch/ablation_forensics/aethel_with_knapsack.py")),
            ("Hydra_Restored_MarketCtrl", os.path.abspath("scratch/ablation_forensics/hydra_with_market_controller.py")),
        ]
        
        for name, path in candidates:
            res = run_paired_tournament_parallel(pool, path, aethel_path, SEEDS_TRAIN, name_a=name, name_b="Aethel_Clean")
            exp_results[name] = res

        # 2. Reference Suite Evaluations
        print("\n--- 2. BENCHMARK SUITE PERFORMANCE ---", flush=True)
        suite_opponents = [
            ("Aethel_V1", os.path.abspath("replays/raw/reference_agents/closer_cleo.py")),
            ("Slotter_Silas_T8", os.path.abspath("replays/raw/reference_agents/slotter_silas.py")),
            ("Ledger_Lena_T7", os.path.abspath("replays/raw/reference_agents/ledger_lena.py")),
            ("Broker_Bea_T6", os.path.abspath("replays/raw/reference_agents/broker_bea.py")),
            ("Rancher_Rita_T5", os.path.abspath("replays/raw/reference_agents/rancher_rita.py")),
            ("Melon_Mateo_T4", os.path.abspath("replays/raw/reference_agents/melon_mateo.py")),
            ("Titan_Apex_V4", os.path.abspath("agents/apex_grandmaster_v4.py")),
        ]
        
        suite_results = {"Aethel": {}, "Hydra": {}, "Aethel_No_FR": {}}
        for opp_name, opp_path in suite_opponents:
            suite_results["Aethel"][opp_name] = run_paired_tournament_parallel(
                pool, aethel_path, opp_path, SEEDS_TRAIN[:5], name_a="Aethel_Clean", name_b=opp_name
            )
            suite_results["Hydra"][opp_name] = run_paired_tournament_parallel(
                pool, hydra_path, opp_path, SEEDS_TRAIN[:5], name_a="Hydra_Prime_V1", name_b=opp_name
            )
            suite_results["Aethel_No_FR"][opp_name] = run_paired_tournament_parallel(
                pool, os.path.abspath("scratch/ablation_forensics/aethel_no_fr.py"), opp_path, SEEDS_TRAIN[:5], name_a="Aethel_No_FR", name_b=opp_name
            )

        # 3. Holdout Generalization
        print("\n--- 3. HOLDOUT GENERALIZATION (10 Unseen Seeds) ---", flush=True)
        holdout_results = {}
        for name, path in [("Aethel_Clean", aethel_path), ("Hydra_Prime_V1", hydra_path), ("Aethel_No_FR", os.path.abspath("scratch/ablation_forensics/aethel_no_fr.py"))]:
            res = run_paired_tournament_parallel(pool, path, aethel_path, SEEDS_HOLDOUT, name_a=name, name_b="Aethel_Clean")
            holdout_results[name] = res

    # Save all results
    payload = {
        "ablations_vs_aethel": exp_results,
        "suite_performance": suite_results,
        "holdout_performance": holdout_results,
    }
    with open("scratch/forensic_suite_complete_results.json", "w") as f:
        json.dump(payload, f, indent=2)
    print("\nSaved all forensic results to scratch/forensic_suite_complete_results.json", flush=True)

if __name__ == "__main__":
    main()
