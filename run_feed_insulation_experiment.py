"""
=============================================================================
FEED INSULATION EXPERIMENT & RIGOROUS BENCHMARK HARNESS
=============================================================================
Executes the controlled evaluation comparing:
- Control: SLOT4_CONTROL_FROZEN (agents/slot4_control_frozen.py)
- Challenger: Hybrid_8C4S_15M_FeedInsulated (agents/hybrid_8c4s_15m_feed_insulated.py)

Evaluates:
1. Direct Paired Head-to-Head (Control vs Challenger) across 50 paired seeds (100 matches).
2. Control & Challenger vs Key Opponents:
   - Titan Production (o1_titan.py)
   - Market Aggressor (o9_market_aggressor.py)
   - Cow Specialist (o5_cow_specialist.py)
   - Balanced Livestock (o7_balanced_livestock.py)
   - Golden Control v1 (o2_golden_v1.py)
3. Parameter Sweeps on Wheat Plots (0, 2, 4, 5, 6, 8) and Thresholds ($30, $35, $40, $45, None).
4. Day-by-Day Feed Ledger Telemetry extraction.
5. Loss Forensics & Categorization (Feed, Market, Capital, Labor, etc.).
=============================================================================
"""

import os
import sys
import time
import json
import hashlib
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
from kaggle_environments import make

project_root = r"c:\Users\Sundareswaran\Kagriculture"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import importlib.util

def load_agent_from_path(filepath):
    spec = importlib.util.spec_from_file_location("agent_module", filepath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def get_sha256(filepath):
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def wilson_score_interval(wins, total, confidence=0.95):
    if total == 0: return 0.0, 0.0
    z = 1.95996
    p = wins / total
    denom = 1.0 + (z**2) / total
    center = (p + (z**2) / (2 * total)) / denom
    spread = (z / denom) * np.sqrt((p * (1.0 - p) / total) + ((z**2) / (4 * (total**2))))
    return max(0.0, center - spread) * 100.0, min(1.0, center + spread) * 100.0

def resolve_agent(agent_spec):
    if isinstance(agent_spec, str):
        return agent_spec
    if isinstance(agent_spec, dict):
        mod = load_agent_from_path(os.path.join(project_root, "agents", "hybrid_8c4s_15m_feed_insulated.py"))
        kwargs = dict(agent_spec)
        kwargs.pop("type", None)
        return mod.HybridFeedInsulatedAgent(**kwargs)
    return agent_spec

def _run_single_match(task):
    agent0, agent1, seed, max_steps, swapped = task
    cfg = {"episodeSteps": max_steps, "seed": seed}
    env = make("kaggriculture", configuration=cfg, debug=False)
    t0 = time.time()
    try:
        a0 = resolve_agent(agent0)
        a1 = resolve_agent(agent1)
        env.run([a0, a1])
        elapsed = time.time() - t0
        final_step = env.steps[-1]
        raw_r0 = float(final_step[0].reward or 0.0)
        raw_r1 = float(final_step[1].reward or 0.0)
        
        r_us = raw_r1 if swapped else raw_r0
        r_opp = raw_r0 if swapped else raw_r1
        win = 1.0 if r_us > r_opp else (0.0 if r_opp > r_us else 0.5)
        margin = r_us - r_opp
        per_turn_ms = (elapsed / max_steps) * 1000.0

        # Step progression checks for forensics
        peak_wheat_price = 25
        wheat_prices = []
        for s in env.steps:
            m = s[0].get("observation", {}).get("market", {}) or {}
            wp = m.get("prices", {}).get("WHEAT", 25)
            wheat_prices.append(wp)
        peak_wheat_price = max(wheat_prices) if wheat_prices else 25

        return {
            "seed": seed, "swapped": swapped, "r_us": r_us, "r_opp": r_opp,
            "margin": margin, "win": win, "elapsed": elapsed, "per_turn_ms": per_turn_ms,
            "peak_wheat_price": peak_wheat_price,
            "error": None
        }
    except Exception as e:
        return {
            "seed": seed, "swapped": swapped, "r_us": 0.0, "r_opp": 0.0,
            "margin": 0.0, "win": 0.0, "elapsed": 0.0, "per_turn_ms": 0.0,
            "peak_wheat_price": 25,
            "error": str(e)
        }

def run_paired_benchmark(cand_path_or_obj, opp_path_or_obj, num_pairs=20, start_seed=40000, max_workers=6):
    tasks = []
    for i in range(num_pairs):
        s = start_seed + i
        tasks.append((cand_path_or_obj, opp_path_or_obj, s, 720, False))
        tasks.append((opp_path_or_obj, cand_path_or_obj, s, 720, True))

    results = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_run_single_match, t) for t in tasks]
        for f in as_completed(futures):
            results.append(f.result())

    wins = sum(r["win"] for r in results)
    total = len(results)
    cash_us = [r["r_us"] for r in results]
    cash_opp = [r["r_opp"] for r in results]
    margins = [r["margin"] for r in results]
    runtimes = [r["per_turn_ms"] for r in results]
    peaks = [r["peak_wheat_price"] for r in results]
    low_ci, upp_ci = wilson_score_interval(wins, total)

    losses = [r for r in results if r["win"] == 0.0]

    return {
        "matches": total,
        "wins": wins,
        "losses": total - wins,
        "win_rate": (wins / total) * 100.0,
        "ci_95": [low_ci, upp_ci],
        "mean_us": float(np.mean(cash_us)),
        "median_us": float(np.median(cash_us)),
        "std_us": float(np.std(cash_us)),
        "mean_opp": float(np.mean(cash_opp)),
        "margin": float(np.mean(margins)),
        "min_margin": float(np.min(margins)),
        "max_margin": float(np.max(margins)),
        "worst_loss": float(np.min(margins)),
        "mean_peak_wheat_price": float(np.mean(peaks)),
        "mean_per_turn_ms": float(np.mean(runtimes)),
        "loss_records": losses
    }

def main():
    print("=" * 95)
    print("CONTROLLED EXPERIMENT: FEED INSULATION (HOMEGROWN WHEAT + DYNAMIC GATING)")
    print("=" * 95)

    control_path = os.path.join(project_root, "agents", "slot4_control_frozen.py")
    challenger_path = os.path.join(project_root, "agents", "hybrid_8c4s_15m_feed_insulated.py")

    control_hash = get_sha256(control_path)
    challenger_hash = get_sha256(challenger_path)

    print(f"Control Frozen File: {control_path}")
    print(f"  SHA256: {control_hash}")
    print(f"Challenger File: {challenger_path}")
    print(f"  SHA256: {challenger_hash}")

    opponents = {
        "Titan Production": os.path.join(project_root, "opponents", "o1_titan.py"),
        "Market Aggressor": os.path.join(project_root, "opponents", "o9_market_aggressor.py"),
        "Cow Specialist": os.path.join(project_root, "opponents", "o5_cow_specialist.py"),
        "Balanced Livestock": os.path.join(project_root, "opponents", "o7_balanced_livestock.py"),
        "Golden Control v1": os.path.join(project_root, "opponents", "o2_golden_v1.py"),
    }

    # 1. DIRECT HEAD-TO-HEAD (Challenger vs Control)
    print("\n" + "-" * 95)
    print("EXPERIMENT 1: DIRECT HEAD-TO-HEAD (Challenger vs Frozen Control) [50 Pairs = 100 Matches]")
    print("-" * 95)
    h2h_res = run_paired_benchmark(challenger_path, control_path, num_pairs=50, start_seed=40000, max_workers=6)
    print(f"Challenger vs Control:")
    print(f"  Win Rate: {h2h_res['win_rate']:5.1f}% ({h2h_res['wins']}W - {h2h_res['losses']}L) | 95% CI: [{h2h_res['ci_95'][0]:4.1f}%, {h2h_res['ci_95'][1]:4.1f}%]")
    print(f"  Challenger Mean: ${h2h_res['mean_us']:8,.2f} | Control Mean: ${h2h_res['mean_opp']:8,.2f} | Net Margin: ${h2h_res['margin']:+8,.2f}")
    print(f"  Worst Margin: ${h2h_res['worst_loss']:+8,.2f} | Runtime: {h2h_res['mean_per_turn_ms']:.2f}ms/turn")

    # 2. COMPARATIVE EVALUATION vs OPPONENT ECOSYSTEM (Control vs Challenger)
    print("\n" + "-" * 95)
    print("EXPERIMENT 2: CONTROL vs CHALLENGER ACROSS OPPONENT SUITE (20 Pairs = 40 Matches Each)")
    print("-" * 95)

    control_opp_results = {}
    challenger_opp_results = {}

    for opp_name, opp_p in opponents.items():
        print(f"\nEvaluating matchup: {opp_name}...")
        c_res = run_paired_benchmark(control_path, opp_p, num_pairs=20, start_seed=41000, max_workers=6)
        ch_res = run_paired_benchmark(challenger_path, opp_p, num_pairs=20, start_seed=41000, max_workers=6)

        control_opp_results[opp_name] = c_res
        challenger_opp_results[opp_name] = ch_res

        delta_wr = ch_res["win_rate"] - c_res["win_rate"]
        delta_margin = ch_res["margin"] - c_res["margin"]

        print(f"  Control:    Win Rate {c_res['win_rate']:5.1f}% | Cash ${c_res['mean_us']:8,.0f} | Margin ${c_res['margin']:+8,.0f}")
        print(f"  Challenger: Win Rate {ch_res['win_rate']:5.1f}% | Cash ${ch_res['mean_us']:8,.0f} | Margin ${ch_res['margin']:+8,.0f}")
        print(f"  --> DELTA (Challenger - Control): Win Rate {delta_wr:+5.1f}% | Margin {delta_margin:+8,.0f}")

    challenger_mod = load_agent_from_path(challenger_path)
    HybridFeedInsulatedAgent = challenger_mod.HybridFeedInsulatedAgent

    # 3. PARAMETER SWEEPS (Wheat Plot Count & Wheat Price Threshold)
    print("\n" + "-" * 95)
    print("EXPERIMENT 3: WHEAT PLOT COUNT SWEEP (0, 2, 4, 5, 6, 8 Plots)")
    print("-" * 95)
    titan_opp = opponents["Titan Production"]
    wheat_plot_results = {}
    for wp in [0, 2, 4, 5, 6, 8]:
        agent_cfg = {"homegrown_wheat_tiles": wp, "wheat_price_threshold": 35.0}
        res = run_paired_benchmark(agent_cfg, titan_opp, num_pairs=15, start_seed=42000, max_workers=6)
        wheat_plot_results[f"{wp}_plots"] = res
        print(f"  Wheat {wp:1d} Plots: Win Rate {res['win_rate']:5.1f}% | Cash ${res['mean_us']:8,.0f} | Margin ${res['margin']:+8,.0f} | Peak Wheat ${res['mean_peak_wheat_price']:.0f}")

    print("\n" + "-" * 95)
    print("EXPERIMENT 4: WHEAT PRICE THRESHOLD SWEEP ($30, $35, $40, $45, None)")
    print("-" * 95)
    thresh_results = {}
    for thresh in [30.0, 35.0, 40.0, 45.0, None]:
        label = f"${int(thresh)}" if thresh is not None else "None"
        agent_cfg = {"homegrown_wheat_tiles": 4, "wheat_price_threshold": thresh}
        res = run_paired_benchmark(agent_cfg, titan_opp, num_pairs=15, start_seed=42000, max_workers=6)
        thresh_results[label] = res
        print(f"  Threshold {label:6s}: Win Rate {res['win_rate']:5.1f}% | Cash ${res['mean_us']:8,.0f} | Margin ${res['margin']:+8,.0f}")

    # 4. FEED LEDGER EXTRACTION (Day 0 to 12)
    print("\n" + "-" * 95)
    print("EXPERIMENT 5: DETAILED DAY-BY-DAY FEED LEDGER EXTRACTION")
    print("-" * 95)
    sim_agent = HybridFeedInsulatedAgent(homegrown_wheat_tiles=4, wheat_price_threshold=35.0)
    cfg = {"episodeSteps": 720, "seed": 40001}
    env = make("kaggriculture", configuration=cfg, debug=False)
    env.run([sim_agent, opponents["Titan Production"]])
    
    feed_ledger = sim_agent.ledger
    print(f"{'Day':4s} | {'Active Animals':14s} | {'Wheat In Shed':13s} | {'Wheat Price':11s} | {'Cash':10s} | {'Wheat Plants':12s} | {'Melons':8s}")
    print("-" * 95)
    for entry in feed_ledger[:13]:
        print(f"{entry['day']:4d} | {entry['active_animals']:14d} | {entry['wheat_in_shed']:13d} | ${entry['wheat_spot_price']:10.1f} | ${entry['money']:8,.0f} | {entry['wheat_plants']:12d} | {entry['melon_plants']:8d}")

    # Save comprehensive results
    full_output = {
        "control_hash": control_hash,
        "challenger_hash": challenger_hash,
        "h2h_challenger_vs_control": h2h_res,
        "control_opponents": control_opp_results,
        "challenger_opponents": challenger_opp_results,
        "wheat_plot_sweep": wheat_plot_results,
        "wheat_threshold_sweep": thresh_results,
        "feed_ledger_sample": feed_ledger[:13]
    }

    with open(os.path.join(project_root, "feed_insulation_experiment_results.json"), "w") as f:
        json.dump(full_output, f, indent=2)

    print("\n" + "=" * 95)
    print("FEED INSULATION EXPERIMENT COMPLETE. DATA SAVED TO feed_insulation_experiment_results.json")
    print("=" * 95)

if __name__ == "__main__":
    main()
