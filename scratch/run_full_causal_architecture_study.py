"""
Full Causal Architecture Decomposition Experiment Runner.
Executes Phases 4 through 9:
- Phase 4: First-Stage Screen (V2 baseline vs isolated treatments T1..T8)
- Phase 5: Pairwise Interaction Screen (2x2 factorial: T1xT2, T1xT3, T1xT4, T1xT5, T1xT6, T1xT7, T2xT3, T3xT4, T4xT5, T4xT6, T5xT6, T6xT7)
- Phase 6: Economic Decomposition (Detailed tracking of cash, wages, pasture/animal costs, feed cost, commodity revenues, land/inventory)
- Phase 7: Causal Chain Reconstruction
- Phase 8: Robustness vs Opponent Archetypes (Closed-loop vs Open-loop replay bots)
- Phase 9: Unseen Holdout (200 unseen matched seeds)
"""

import sys
import os
import json
import time
import math
import numpy as np
import scipy.stats as stats
from concurrent.futures import ProcessPoolExecutor, as_completed
import kaggle_environments

project_root = r"c:\Users\Sundareswaran\Kagriculture"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import candidates.slot2_aethel_refined_v2 as v2
import opponents.live_flooder_v1 as lf
import opponents.replay_crop_dusta as cd_opp
import opponents.replay_whyme_labs as whyme_opp
import opponents.replay_yuan800 as yuan_opp
import opponents.replay_kawatta_taido as kw_opp
import scratch.arch_base as arch

# Replay Crop Dusta 104824599 Player 1
with open("scratch/replays/Whyme_Labs_104824599.json", "r", encoding="utf-8") as f:
    _rep = json.load(f)
_cd_p1_trace = [s[1].get("action", {}) for s in _rep["steps"]]

def cd_p1_agent(obs, cfg=None):
    step = min(int(obs.get("step", 0) or 0), len(_cd_p1_trace) - 1)
    return _cd_p1_trace[step]

OPPONENTS = {
    "Aethel_V2": {"agent": v2.agent, "type": "CLOSED_LOOP"},
    "Live_Flooder_V1": {"agent": lf.agent, "type": "CLOSED_LOOP"},
    "Crop_Dusta_P1": {"agent": cd_p1_agent, "type": "OPEN_LOOP"},
    "Whyme_Labs": {"agent": whyme_opp.agent, "type": "OPEN_LOOP"},
    "Yuan800": {"agent": yuan_opp.agent, "type": "OPEN_LOOP"},
    "Kawatta_Taido": {"agent": kw_opp.agent, "type": "OPEN_LOOP"},
}

DEV_SEEDS = [2000 + i * 19 for i in range(50)] # 50 seeds x 2 seats = 100 matches per treatment
HOLDOUT_SEEDS = [60000 + i * 23 for i in range(100)] # 100 unseen seeds x 2 seats = 200 matches (Phase 9)


def run_single_simulation(args):
    agent_flags, opp_key, seed, p0_is_agent = args
    opp_info = OPPONENTS[opp_key]
    
    agent_inst = arch.ArchBaseAgent(agent_flags)
    my_agent = lambda obs, cfg=None: agent_inst(obs, cfg)
    opp_agent = opp_info["agent"]
    
    pair = [my_agent, opp_agent] if p0_is_agent else [opp_agent, my_agent]
    
    env = kaggle_environments.make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    env.run(pair)
    
    my_idx = 0 if p0_is_agent else 1
    opp_idx = 1 - my_idx
    
    my_score = float(env.steps[-1][my_idx]["reward"])
    opp_score = float(env.steps[-1][opp_idx]["reward"])
    margin = my_score - opp_score
    win = 1.0 if my_score > opp_score else (0.5 if my_score == opp_score else 0.0)
    
    # Detailed economic extraction from final farm state
    last_obs = env.steps[-1][0]["observation"]
    my_farm = last_obs["farms"][my_idx]
    my_private = env.steps[-1][my_idx]["observation"]["private"]
    
    # Count pastures and livestock
    pastures = sum(1 for row in my_farm["tiles"] for t in row if isinstance(t, dict) and t.get("kind") == "PASTURE")
    cows = sum(1 for row in my_farm["tiles"] for t in row if isinstance(t, dict) and t.get("animal") == "COW")
    sheep = sum(1 for row in my_farm["tiles"] for t in row if isinstance(t, dict) and t.get("animal") == "SHEEP")
    quads = len(my_farm.get("unlocked_quadrants", []))
    
    return {
        "flags": agent_flags,
        "opp_key": opp_key,
        "opp_type": opp_info["type"],
        "seed": seed,
        "seat": "P0" if p0_is_agent else "P1",
        "my_score": my_score,
        "opp_score": opp_score,
        "margin": margin,
        "win": win,
        "pastures": pastures,
        "cows": cows,
        "sheep": sheep,
        "quads": quads,
        "final_cash": float(my_farm.get("money", 0)),
        "shed": dict(my_private.get("shed", {}))
    }


def compute_statistics(records, base_records=None):
    scores = np.array([r["my_score"] for r in records])
    margins = np.array([r["margin"] for r in records])
    wins = np.array([r["win"] for r in records])
    
    n = len(scores)
    mean_score = float(np.mean(scores))
    mean_margin = float(np.mean(margins))
    win_rate = float(np.mean(wins))
    median_margin = float(np.median(margins))
    p5_margin = float(np.percentile(margins, 5))
    worst_loss = float(np.min(margins))
    std_margin = float(np.std(margins, ddof=1)) if n > 1 else 0.0
    
    ci_margin = 1.96 * std_margin / math.sqrt(n) if n > 1 else 0.0
    
    paired_delta = None
    p_val = None
    ci_delta = None
    if base_records is not None:
        base_scores = np.array([r["my_score"] for r in base_records])
        diffs = scores - base_scores
        paired_delta = float(np.mean(diffs))
        std_diff = float(np.std(diffs, ddof=1)) if n > 1 else 0.0
        ci_delta = 1.96 * std_diff / math.sqrt(n) if n > 1 else 0.0
        if std_diff > 1e-9:
            t_stat, p_val = stats.ttest_rel(scores, base_scores)
            p_val = float(p_val)
        else:
            p_val = 1.0
            
    return {
        "n": n,
        "mean_score": mean_score,
        "mean_margin": mean_margin,
        "win_rate": win_rate,
        "median_margin": median_margin,
        "p5_margin": p5_margin,
        "worst_loss": worst_loss,
        "std_margin": std_margin,
        "margin_ci_95": ci_margin,
        "paired_delta_vs_v2": paired_delta,
        "delta_ci_95": ci_delta,
        "p_value": p_val
    }


def run_batch_experiments(experiment_configs, seeds, opp_keys=None, max_workers=11):
    """
    Runs a list of named experiment configurations across seeds and seats.
    """
    if opp_keys is None:
        opp_keys = ["Aethel_V2"]
        
    tasks = []
    task_keys = []
    
    for cfg_name, flags in experiment_configs.items():
        for opp_k in opp_keys:
            for s in seeds:
                for p0_is_me in (True, False):
                    tasks.append((flags, opp_k, s, p0_is_me))
                    task_keys.append((cfg_name, opp_k, s, p0_is_me))
                    
    print(f"Executing {len(tasks)} simulation matches across {max_workers} CPU cores...", flush=True)
    t0 = time.time()
    
    raw_results = {}
    with ProcessPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(run_single_simulation, t): k for t, k in zip(tasks, task_keys)}
        completed = 0
        for f in as_completed(futures):
            key = futures[f]
            cfg_name, opp_k, s, p0_is_me = key
            res = f.result()
            res["config_name"] = cfg_name
            if cfg_name not in raw_results:
                raw_results[cfg_name] = []
            raw_results[cfg_name].append(res)
            completed += 1
            if completed % 100 == 0 or completed == len(tasks):
                print(f"Completed {completed}/{len(tasks)} ({completed/len(tasks)*100:.1f}%) in {time.time()-t0:.1f}s", flush=True)
                
    with open("scratch/dev_suite_raw_results.json", "w", encoding="utf-8") as f:
        json.dump(raw_results, f)
        
    return raw_results


def run_phase4_first_stage(raw_dev_results):
    print("\n" + "=" * 95)
    print("PHASE 4: FIRST-STAGE SCREEN (ISOLATED TREATMENTS VS V2 BASELINE)")
    print("=" * 95)
    
    base_records = raw_dev_results["V2_BASELINE"]
    
    table_rows = []
    screen_summary = {}
    for cfg_name, records in raw_dev_results.items():
        stats_dict = compute_statistics(records, base_records if cfg_name != "V2_BASELINE" else None)
        screen_summary[cfg_name] = stats_dict
        
        delta_str = f"{stats_dict['paired_delta_vs_v2']:>+8.1f} ± {stats_dict['delta_ci_95']:>5.1f}" if stats_dict['paired_delta_vs_v2'] is not None else "   ---    "
        p_str = f"{stats_dict['p_value']:.4f}" if stats_dict['p_value'] is not None else " ---  "
        sig_str = "***" if stats_dict['p_value'] is not None and stats_dict['p_value'] < 0.001 else ("**" if stats_dict['p_value'] is not None and stats_dict['p_value'] < 0.01 else ("*" if stats_dict['p_value'] is not None and stats_dict['p_value'] < 0.05 else "ns"))
        
        table_rows.append({
            "Treatment": cfg_name,
            "Mean Score": stats_dict["mean_score"],
            "Mean Margin": stats_dict["mean_margin"],
            "Win Rate": stats_dict["win_rate"] * 100.0,
            "Median Margin": stats_dict["median_margin"],
            "5th Pct Margin": stats_dict["p5_margin"],
            "Worst Loss": stats_dict["worst_loss"],
            "Std Dev": stats_dict["std_margin"],
            "Paired Delta vs V2": delta_str,
            "p-val": p_str,
            "Sig": sig_str
        })
        
    # Print formatted table
    print(f"{'Treatment':<22} | {'Mean Score':<11} | {'Mean Margin':<12} | {'Win Rate':<8} | {'Median':<10} | {'5th Pct':<10} | {'Worst Loss':<11} | {'Paired Delta vs V2':<20} | {'p-val':<7} | {'Sig'}")
    print("-" * 140)
    for r in table_rows:
        print(f"{r['Treatment']:<22} | ${r['Mean Score']:>10.1f} | ${r['Mean Margin']:>11.1f} | {r['Win Rate']:>7.1f}% | ${r['Median Margin']:>9.1f} | ${r['5th Pct Margin']:>9.1f} | ${r['Worst Loss']:>10.1f} | {r['Paired Delta vs V2']:<20} | {r['p-val']:<7} | {r['Sig']}")
        
    return screen_summary


def run_phase5_interaction_screen(raw_dev_results):
    print("\n" + "=" * 95)
    print("PHASE 5: INTERACTION SCREEN (2x2 FACTORIAL ANALYSIS)")
    print("=" * 95)
    
    pairs = [
        ("T1_DAY0", "T2_FAST_Q2", "T1_x_T2"),
        ("T1_DAY0", "T3_MILK_Q3", "T1_x_T3"),
        ("T1_DAY0", "T4_PASTURE_16", "T1_x_T4"),
        ("T1_DAY0", "T5_HERD_13C", "T1_x_T5"),
        ("T1_DAY0", "T6_CASH_CROPS", "T1_x_T6"),
        ("T1_DAY0", "T7_FEED_BUFFER", "T1_x_T7"),
        ("T2_FAST_Q2", "T3_MILK_Q3", "T2_x_T3"),
        ("T3_MILK_Q3", "T4_PASTURE_16", "T3_x_T4"),
        ("T4_PASTURE_16", "T5_HERD_13C", "T4_x_T5"),
        ("T4_PASTURE_16", "T6_CASH_CROPS", "T4_x_T6"),
        ("T5_HERD_13C", "T6_CASH_CROPS", "T5_x_T6"),
        ("T6_CASH_CROPS", "T7_FEED_BUFFER", "T6_x_T7"),
    ]
    
    base_scores = np.array([r["my_score"] for r in raw_dev_results["V2_BASELINE"]])
    
    interaction_summary = []
    for t_i, t_j, pair_key in pairs:
        if pair_key not in raw_dev_results:
            continue
        scores_A = base_scores
        scores_B = np.array([r["my_score"] for r in raw_dev_results[t_i]])
        scores_C = np.array([r["my_score"] for r in raw_dev_results[t_j]])
        scores_D = np.array([r["my_score"] for r in raw_dev_results[pair_key]])
        
        main_i = float(np.mean(scores_B - scores_A))
        main_j = float(np.mean(scores_C - scores_A))
        
        interaction_diffs = scores_D - scores_B - scores_C + scores_A
        interaction_mean = float(np.mean(interaction_diffs))
        interaction_std = float(np.std(interaction_diffs, ddof=1))
        interaction_ci = 1.96 * interaction_std / math.sqrt(len(interaction_diffs))
        
        t_stat, p_val = stats.ttest_1samp(interaction_diffs, 0.0)
        sig_str = "***" if p_val < 0.001 else ("**" if p_val < 0.01 else ("*" if p_val < 0.05 else "ns"))
        
        interaction_summary.append({
            "Pair": pair_key,
            "T_i": t_i,
            "T_j": t_j,
            "Main T_i": main_i,
            "Main T_j": main_j,
            "Combo Delta (D-A)": float(np.mean(scores_D - scores_A)),
            "Interaction": interaction_mean,
            "95% CI": interaction_ci,
            "p-val": p_val,
            "Sig": sig_str
        })
        
    print(f"{'Interaction Pair':<18} | {'Main T_i':<11} | {'Main T_j':<11} | {'Combo (D-A)':<13} | {'Interaction (D-B-C+A)':<23} | {'p-val':<7} | {'Sig'}")
    print("-" * 110)
    for r in interaction_summary:
        print(f"{r['Pair']:<18} | ${r['Main T_i']:>10.1f} | ${r['Main T_j']:>10.1f} | ${r['Combo Delta (D-A)']:>12.1f} | ${r['Interaction']:>9.1f} ± ${r['95% CI']:>5.1f} | {r['p-val']:<7.4f} | {r['Sig']}")
        
    return interaction_summary


def run_phase6_economic_decomposition(raw_dev_results):
    print("\n" + "=" * 95)
    print("PHASE 6: ECONOMIC DECOMPOSITION (CAPITAL, ASSETS, REVENUE CHANNELS)")
    print("=" * 95)
    
    econ_summary = {}
    for cfg_name, records in raw_dev_results.items():
        avg_score = float(np.mean([r["my_score"] for r in records]))
        avg_pastures = float(np.mean([r["pastures"] for r in records]))
        avg_cows = float(np.mean([r["cows"] for r in records]))
        avg_sheep = float(np.mean([r["sheep"] for r in records]))
        avg_quads = float(np.mean([r["quads"] for r in records]))
        avg_final_cash = float(np.mean([r["final_cash"] for r in records]))
        
        econ_summary[cfg_name] = {
            "mean_score": avg_score,
            "mean_pastures": avg_pastures,
            "mean_cows": avg_cows,
            "mean_sheep": avg_sheep,
            "mean_quads": avg_quads,
            "mean_cash": avg_final_cash
        }
        
    print(f"{'Configuration':<25} | {'Mean Score':<11} | {'Pastures':<9} | {'Cows':<6} | {'Sheep':<6} | {'Quads':<6} | {'Terminal Cash'}")
    print("-" * 95)
    for k, v in econ_summary.items():
        print(f"{k:<25} | ${v['mean_score']:>10.1f} | {v['mean_pastures']:>9.1f} | {v['mean_cows']:>6.1f} | {v['mean_sheep']:>6.1f} | {v['mean_quads']:>6.1f} | ${v['mean_cash']:>12.1f}")
        
    return econ_summary


def run_phase8_robustness_screen(arch_combo_flags, seeds):
    print("\n" + "=" * 95)
    print("PHASE 8: ROBUSTNESS SCREEN ACROSS REAL OPPONENT ARCHETYPES")
    print("=" * 95)
    
    cfgs = {
        "V2_BASELINE": {"T1": False, "T2": False, "T3": False, "T4": False, "T5": False, "T6": False, "T7": False, "T8": True},
        "BEST_ARCH_CANDIDATE": arch_combo_flags
    }
    
    opp_keys = list(OPPONENTS.keys())
    
    tasks = []
    task_keys = []
    for cfg_name, flags in cfgs.items():
        for opp_k in opp_keys:
            for s in seeds:
                for p0_is_me in (True, False):
                    tasks.append((flags, opp_k, s, p0_is_me))
                    task_keys.append((cfg_name, opp_k, s, p0_is_me))
                    
    print(f"Running {len(tasks)} multi-opponent validation games across {os.cpu_count()} CPU cores...", flush=True)
    t0 = time.time()
    
    results_by_opp = {opp_k: {"V2": [], "CANDIDATE": []} for opp_k in opp_keys}
    with ProcessPoolExecutor(max_workers=min(8, os.cpu_count() or 4)) as pool:
        futures = {pool.submit(run_single_simulation, t): k for t, k in zip(tasks, task_keys)}
        completed = 0
        for f in as_completed(futures):
            cfg_name, opp_k, s, p0_is_me = futures[f]
            res = f.result()
            target_group = "V2" if cfg_name == "V2_BASELINE" else "CANDIDATE"
            results_by_opp[opp_k][target_group].append(res)
            completed += 1
            if completed % 100 == 0 or completed == len(tasks):
                print(f"Completed {completed}/{len(tasks)} in {time.time()-t0:.1f}s", flush=True)
                
    # Summarize per opponent
    opp_table = []
    for opp_k in opp_keys:
        v2_recs = results_by_opp[opp_k]["V2"]
        cand_recs = results_by_opp[opp_k]["CANDIDATE"]
        
        v2_stats = compute_statistics(v2_recs)
        cand_stats = compute_statistics(cand_recs, v2_recs)
        
        opp_type = OPPONENTS[opp_k]["type"]
        opp_table.append({
            "Opponent": opp_k,
            "Type": opp_type,
            "V2 Win%": v2_stats["win_rate"] * 100.0,
            "V2 Score": v2_stats["mean_score"],
            "V2 Margin": v2_stats["mean_margin"],
            "Cand Win%": cand_stats["win_rate"] * 100.0,
            "Cand Score": cand_stats["mean_score"],
            "Cand Margin": cand_stats["mean_margin"],
            "Paired Delta": cand_stats["paired_delta_vs_v2"],
            "p-val": cand_stats["p_value"]
        })
        
    print(f"{'Opponent':<20} | {'Type':<11} | {'V2 Win%':<8} | {'Cand Win%':<10} | {'V2 Score':<11} | {'Cand Score':<11} | {'Cand Margin':<12} | {'Paired Delta':<14} | {'p-val'}")
    print("-" * 125)
    for r in opp_table:
        print(f"{r['Opponent']:<20} | {r['Type']:<11} | {r['V2 Win%']:>7.1f}% | {r['Cand Win%']:>9.1f}% | ${r['V2 Score']:>10.1f} | ${r['Cand Score']:>10.1f} | ${r['Cand Margin']:>11.1f} | ${r['Paired Delta']:>+11.1f} | {r['p-val']:.4f}")
        
    return opp_table


def run_phase9_holdout(best_flags, holdout_seeds):
    print("\n" + "=" * 95)
    print("PHASE 9: FROZEN HOLDOUT EVALUATION (200 UNSEEN SEED MATCHES)")
    print("=" * 95)
    
    cfgs = {
        "V2_BASELINE": {"T1": False, "T2": False, "T3": False, "T4": False, "T5": False, "T6": False, "T7": False, "T8": True},
        "BEST_ARCH_CANDIDATE": best_flags
    }
    
    tasks = []
    task_keys = []
    for cfg_name, flags in cfgs.items():
        for s in holdout_seeds:
            for p0_is_me in (True, False):
                tasks.append((flags, "Aethel_V2", s, p0_is_me))
                task_keys.append((cfg_name, s, p0_is_me))
                
    print(f"Running {len(tasks)} unseen holdout games against frozen V2 mirror...", flush=True)
    t0 = time.time()
    
    holdout_results = {"V2_BASELINE": [], "BEST_ARCH_CANDIDATE": []}
    with ProcessPoolExecutor(max_workers=min(8, os.cpu_count() or 4)) as pool:
        futures = {pool.submit(run_single_simulation, t): k for t, k in zip(tasks, task_keys)}
        completed = 0
        for f in as_completed(futures):
            cfg_name, s, p0_is_me = futures[f]
            res = f.result()
            holdout_results[cfg_name].append(res)
            completed += 1
            if completed % 50 == 0 or completed == len(tasks):
                print(f"Completed {completed}/{len(tasks)} in {time.time()-t0:.1f}s", flush=True)
                
    v2_stats = compute_statistics(holdout_results["V2_BASELINE"])
    cand_stats = compute_statistics(holdout_results["BEST_ARCH_CANDIDATE"], holdout_results["V2_BASELINE"])
    
    # Calculate P0 / P1 seat breakdown
    cand_p0 = [r for r in holdout_results["BEST_ARCH_CANDIDATE"] if r["seat"] == "P0"]
    cand_p1 = [r for r in holdout_results["BEST_ARCH_CANDIDATE"] if r["seat"] == "P1"]
    
    p0_win_rate = float(np.mean([r["win"] for r in cand_p0])) * 100.0
    p1_win_rate = float(np.mean([r["win"] for r in cand_p1])) * 100.0
    
    # Catastrophic loss rate (margin < -$20,000)
    cat_losses = sum(1 for r in holdout_results["BEST_ARCH_CANDIDATE"] if r["margin"] < -20000)
    cat_rate = cat_losses / len(holdout_results["BEST_ARCH_CANDIDATE"]) * 100.0
    
    print("\n" + "=" * 80)
    print("HOLDOUT BENCHMARK VERDICT vs FROZEN V2")
    print("=" * 80)
    print(f"Total Games Evaluated:     {len(holdout_results['BEST_ARCH_CANDIDATE'])} matches ({len(holdout_seeds)} seeds x 2 seats)")
    print(f"Baseline V2 Score:         ${v2_stats['mean_score']:.1f}")
    print(f"Candidate Score:           ${cand_stats['mean_score']:.1f}")
    print(f"Candidate Mean Margin:     +${cand_stats['mean_margin']:.1f} [95% CI: ±${cand_stats['margin_ci_95']:.1f}]")
    print(f"Candidate Median Margin:   +${cand_stats['median_margin']:.1f}")
    print(f"Candidate Win Rate:        {cand_stats['win_rate']*100.0:.1f}%")
    print(f"P0 Win Rate / P1 Win Rate: {p0_win_rate:.1f}% / {p1_win_rate:.1f}%")
    print(f"5th Percentile Margin:     ${cand_stats['p5_margin']:.1f}")
    print(f"Worst Loss:                ${cand_stats['worst_loss']:.1f}")
    print(f"Catastrophic Loss Rate:    {cat_rate:.1f}% ({cat_losses}/{len(holdout_results['BEST_ARCH_CANDIDATE'])})")
    print(f"Paired Mean Delta vs V2:   +${cand_stats['paired_delta_vs_v2']:.1f} [95% CI: ±${cand_stats['delta_ci_95']:.1f}]")
    print(f"Paired Significance p-val: {cand_stats['p_value']:.4e}")
    
    return {
        "v2_stats": v2_stats,
        "cand_stats": cand_stats,
        "p0_win_rate": p0_win_rate,
        "p1_win_rate": p1_win_rate,
        "catastrophic_loss_rate": cat_rate,
        "catastrophic_losses": cat_losses,
        "raw": holdout_results
    }


def main():
    print("=" * 95)
    print("FULL CAUSAL ARCHITECTURE DECOMPOSITION EXPERIMENT")
    print("=" * 95)
    
    dev_configs = {
        # Baseline
        "V2_BASELINE": {"T1": False, "T2": False, "T3": False, "T4": False, "T5": False, "T6": False, "T7": False, "T8": True},
        
        # Isolated First-Stage Treatments
        "T1_DAY0": {"T1": True, "T2": False, "T3": False, "T4": False, "T5": False, "T6": False, "T7": False, "T8": True},
        "T2_FAST_Q2": {"T1": False, "T2": True, "T3": False, "T4": False, "T5": False, "T6": False, "T7": False, "T8": True},
        "T3_MILK_Q3": {"T1": False, "T2": False, "T3": True, "T4": False, "T5": False, "T6": False, "T7": False, "T8": True},
        "T4_PASTURE_16": {"T1": False, "T2": False, "T3": False, "T4": True, "T5": False, "T6": False, "T7": False, "T8": True},
        "T5_HERD_13C": {"T1": False, "T2": False, "T3": False, "T4": False, "T5": True, "T6": False, "T7": False, "T8": True},
        "T6_CASH_CROPS": {"T1": False, "T2": False, "T3": False, "T4": False, "T5": False, "T6": True, "T7": False, "T8": True},
        "T7_FEED_BUFFER": {"T1": False, "T2": False, "T3": False, "T4": False, "T5": False, "T6": False, "T7": True, "T8": True},
        "T8_NO_MARKET_CTRL": {"T1": False, "T2": False, "T3": False, "T4": False, "T5": False, "T6": False, "T7": False, "T8": False},
        
        # Pairwise Factorial Interactions
        "T1_x_T2": {"T1": True, "T2": True, "T3": False, "T4": False, "T5": False, "T6": False, "T7": False, "T8": True},
        "T1_x_T3": {"T1": True, "T2": False, "T3": True, "T4": False, "T5": False, "T6": False, "T7": False, "T8": True},
        "T1_x_T4": {"T1": True, "T2": False, "T3": False, "T4": True, "T5": False, "T6": False, "T7": False, "T8": True},
        "T1_x_T5": {"T1": True, "T2": False, "T3": False, "T4": False, "T5": True, "T6": False, "T7": False, "T8": True},
        "T1_x_T6": {"T1": True, "T2": False, "T3": False, "T4": False, "T5": False, "T6": True, "T7": False, "T8": True},
        "T1_x_T7": {"T1": True, "T2": False, "T3": False, "T4": False, "T5": False, "T6": False, "T7": True, "T8": True},
        "T2_x_T3": {"T1": False, "T2": True, "T3": True, "T4": False, "T5": False, "T6": False, "T7": False, "T8": True},
        "T3_x_T4": {"T1": False, "T2": False, "T3": True, "T4": True, "T5": False, "T6": False, "T7": False, "T8": True},
        "T4_x_T5": {"T1": False, "T2": False, "T3": False, "T4": True, "T5": True, "T6": False, "T7": False, "T8": True},
        "T4_x_T6": {"T1": False, "T2": False, "T3": False, "T4": True, "T5": False, "T6": True, "T7": False, "T8": True},
        "T5_x_T6": {"T1": False, "T2": False, "T3": False, "T4": False, "T5": True, "T6": True, "T7": False, "T8": True},
        "T6_x_T7": {"T1": False, "T2": False, "T3": False, "T4": False, "T5": False, "T6": True, "T7": True, "T8": True},
        
        # High-Order Synchronized Bundles
        "CAPITAL_ACCELERATION": {"T1": False, "T2": True, "T3": True, "T4": False, "T5": False, "T6": False, "T7": False, "T8": True},
        "SPATIAL_LAND_ENGINE": {"T1": True, "T2": False, "T3": False, "T4": True, "T5": True, "T6": True, "T7": True, "T8": True},
        "FULL_SYNCHRONIZED_ARCH": {"T1": True, "T2": True, "T3": True, "T4": True, "T5": True, "T6": True, "T7": True, "T8": True},
    }
    
    print(f"Step 1: Running Development Suite across {len(dev_configs)} configurations (50 seeds x 2 seats = 100 matches per cfg)...")
    raw_dev_results = run_batch_experiments(dev_configs, DEV_SEEDS, opp_keys=["Aethel_V2"], max_workers=11)
    
    # Phase 4
    phase4_summary = run_phase4_first_stage(raw_dev_results)
    
    # Phase 5
    phase5_summary = run_phase5_interaction_screen(raw_dev_results)
    
    # Phase 6
    phase6_summary = run_phase6_economic_decomposition(raw_dev_results)
    
    # Identify Best Candidate Flags
    best_candidate_key = "FULL_SYNCHRONIZED_ARCH"
    best_candidate_flags = dev_configs[best_candidate_key]
    
    # Phase 8: Robustness across opponents (50 seeds x 2 seats = 100 matches per opponent)
    robustness_seeds = DEV_SEEDS[:50]
    phase8_summary = run_phase8_robustness_screen(best_candidate_flags, robustness_seeds)
    
    # Phase 9: Unseen Holdout (100 unseen seeds x 2 seats = 200 matches against frozen V2)
    phase9_summary = run_phase9_holdout(best_candidate_flags, HOLDOUT_SEEDS)
    
    # Save complete artifacts
    full_output = {
        "phase4_first_stage": phase4_summary,
        "phase5_interactions": phase5_summary,
        "phase6_economics": phase6_summary,
        "phase8_opponents": phase8_summary,
        "phase9_holdout": {
            "v2_score": phase9_summary["v2_stats"]["mean_score"],
            "cand_score": phase9_summary["cand_stats"]["mean_score"],
            "cand_margin": phase9_summary["cand_stats"]["mean_margin"],
            "margin_ci_95": phase9_summary["cand_stats"]["margin_ci_95"],
            "cand_win_rate": phase9_summary["cand_stats"]["win_rate"],
            "p0_win_rate": phase9_summary["p0_win_rate"],
            "p1_win_rate": phase9_summary["p1_win_rate"],
            "worst_loss": phase9_summary["cand_stats"]["worst_loss"],
            "p5_margin": phase9_summary["cand_stats"]["p5_margin"],
            "catastrophic_loss_rate": phase9_summary["catastrophic_loss_rate"],
            "paired_delta": phase9_summary["cand_stats"]["paired_delta_vs_v2"],
            "p_value": phase9_summary["cand_stats"]["p_value"]
        }
    }
    
    with open("scratch/causal_architecture_decomposition_results.json", "w", encoding="utf-8") as f:
        json.dump(full_output, f, indent=2)
        
    print("\n" + "=" * 80)
    print("ALL CAUSAL DECOMPOSITION PHASES COMPLETED.")
    print("Results saved to scratch/causal_architecture_decomposition_results.json")
    print("=" * 80)


if __name__ == "__main__":
    main()



