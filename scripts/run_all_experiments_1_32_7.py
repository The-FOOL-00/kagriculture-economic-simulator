import os
import sys
import time
import json
import numpy as np
import kaggle_environments

sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from master_harness import run_paired_tournament

def save_intermediate(results, filename="current_engine_master_results.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

def run_master_suite():
    print("=" * 80, flush=True)
    print(f"KAGGRICULTURE 1.32.7 MASTER SCIENTIFIC VALIDATION SUITE", flush=True)
    print(f"Engine: kaggle-environments {kaggle_environments.__version__}", flush=True)
    print("=" * 80, flush=True)
    
    # 4 distinct seed blocks (100 total seeds = 200 paired matches per test)
    seeds_dev = list(range(1000, 1025))      # 25 seeds
    seeds_val = list(range(2000, 2025))      # 25 seeds
    seeds_test = list(range(3000, 3025))     # 25 seeds
    seeds_holdout = list(range(50000, 50025)) # 25 seeds
    all_100_seeds = seeds_dev + seeds_val + seeds_test + seeds_holdout
    
    # 50 seeds (100 matches) for sweeps/ablations
    fast_50_seeds = list(range(1000, 1025)) + list(range(50000, 50025))
    
    control_path = "agents/ground_truth_control_current_engine.py"
    apex_v2_path = "candidates/slot5_apex_synthesis_v2.py"
    titan_path = "candidates/slot1_titan_control.py"
    
    all_results = {}
    
    # =========================================================================
    # PART 9: CONTROL SELF-PLAY BASELINE & ASYMMETRY
    # =========================================================================
    print("\n" + "=" * 80, flush=True)
    print("PART 9: REBUILD CONTROL SELF-PLAY BASELINE & ASYMMETRY (100 SEEDS / 200 MATCHES)", flush=True)
    print("=" * 80, flush=True)
    t0 = time.time()
    res_control_selfplay = run_paired_tournament(control_path, control_path, all_100_seeds, max_workers=10, show_progress=True)
    all_results["part9_control_selfplay"] = res_control_selfplay
    save_intermediate(all_results)
    print(f"Control Self-Play: Pooled WR = {res_control_selfplay['pooled_wr']*100:.1f}%, P0 WR = {res_control_selfplay['p0_wr']*100:.1f}%, P1 WR = {res_control_selfplay['p1_wr']*100:.1f}%", flush=True)
    print(f"P0/P1 Asymmetry = {(res_control_selfplay['p0_wr'] - res_control_selfplay['p1_wr'])*100:.1f}pp | Mean Cash = ${res_control_selfplay['mean_cash']:.1f}", flush=True)
    print(f"Completed in {time.time() - t0:.1f}s", flush=True)
    
    # =========================================================================
    # PART 10: REVALIDATE APEX V2 VS GROUND TRUTH CONTROL
    # =========================================================================
    print("\n" + "=" * 80, flush=True)
    print("PART 10: REVALIDATE APEX V2 (AS-IS) VS GROUND TRUTH CONTROL (100 SEEDS / 200 MATCHES)", flush=True)
    print("=" * 80, flush=True)
    t0 = time.time()
    res_apex_vs_control = run_paired_tournament(apex_v2_path, control_path, all_100_seeds, max_workers=10, show_progress=True)
    all_results["part10_apex_vs_control"] = res_apex_vs_control
    save_intermediate(all_results)
    print(f"Apex v2 vs Control: Pooled WR = {res_apex_vs_control['pooled_wr']*100:.1f}%, P0 WR = {res_apex_vs_control['p0_wr']*100:.1f}%, P1 WR = {res_apex_vs_control['p1_wr']*100:.1f}%", flush=True)
    print(f"Mean Margin = ${res_apex_vs_control['mean_margin']:+.1f} | Median Margin = ${res_apex_vs_control['median_margin']:+.1f} | Catastrophic (< -$10k) = {res_apex_vs_control['catastrophic']}", flush=True)
    print(f"Apex Cash = ${res_apex_vs_control['mean_cash']:.1f} vs Control Cash = ${res_apex_vs_control['opp_p0_cash']:.1f}", flush=True)
    print(f"Completed in {time.time() - t0:.1f}s", flush=True)
    
    # =========================================================================
    # PART 11: REVALIDATE APEX V2 VS TITAN
    # =========================================================================
    print("\n" + "=" * 80, flush=True)
    print("PART 11: REVALIDATE APEX V2 VS TITAN CONTROL (100 SEEDS / 200 MATCHES)", flush=True)
    print("=" * 80, flush=True)
    t0 = time.time()
    res_apex_vs_titan = run_paired_tournament(apex_v2_path, titan_path, all_100_seeds, max_workers=10, show_progress=True)
    all_results["part11_apex_vs_titan"] = res_apex_vs_titan
    save_intermediate(all_results)
    print(f"Apex v2 vs Titan: Pooled WR = {res_apex_vs_titan['pooled_wr']*100:.1f}%, P0 WR = {res_apex_vs_titan['p0_wr']*100:.1f}%, P1 WR = {res_apex_vs_titan['p1_wr']*100:.1f}%", flush=True)
    print(f"Mean Margin = ${res_apex_vs_titan['mean_margin']:+.1f} | Median Margin = ${res_apex_vs_titan['median_margin']:+.1f}", flush=True)
    print(f"Completed in {time.time() - t0:.1f}s", flush=True)

    # =========================================================================
    # PART 12: REVALIDATE OPPONENT SUITE
    # =========================================================================
    print("\n" + "=" * 80, flush=True)
    print("PART 12: REVALIDATE APEX V2 VS FULL OPPONENT SUITE (50 SEEDS / 100 MATCHES EACH)", flush=True)
    print("=" * 80, flush=True)
    opponents = {
        "Titan": "opponents/o1_titan.py",
        "Golden_v1": "opponents/o2_golden_v1.py",
        "Melon_Specialist_StrongCrop": "opponents/o3_melon_specialist.py",
        "Fast_Crop": "opponents/o4_fast_crop.py",
        "Cow_Specialist": "opponents/o5_cow_specialist.py",
        "Sheep_Specialist": "opponents/o6_sheep_specialist.py",
        "Balanced_Livestock_StrongLivestock": "opponents/o7_balanced_livestock.py",
        "Economic_Optimizer": "opponents/o8_economic_optimizer.py",
        "Market_Aggressor": "opponents/o9_market_aggressor.py",
        "Anti_Melon": "opponents/o10_anti_melon.py",
        "Anti_Livestock": "opponents/o11_anti_livestock.py",
        "Top_Meta": "opponents/o12_top_meta.py",
        "Adversarial_Champion_Killer": "opponents/adversarial_champion_killer.py",
    }
    
    suite_results = {}
    for name, opp_file in opponents.items():
        if not os.path.exists(opp_file):
            print(f"Skipping missing opponent: {opp_file}", flush=True)
            continue
        t0 = time.time()
        res = run_paired_tournament(apex_v2_path, opp_file, fast_50_seeds, max_workers=10)
        suite_results[name] = res
        print(f"vs {name:<35}: WR = {res['pooled_wr']*100:5.1f}% (P0={res['p0_wr']*100:4.1f}%, P1={res['p1_wr']*100:4.1f}%) | Margin = ${res['mean_margin']:+7.1f} ({time.time()-t0:.1f}s)", flush=True)
    
    all_results["part12_opponent_suite"] = suite_results
    save_intermediate(all_results)

    # =========================================================================
    # PART 13: CORE APEX ONE-VARIABLE ABLATIONS
    # =========================================================================
    print("\n" + "=" * 80, flush=True)
    print("PART 13: CORE APEX ONE-VARIABLE ABLATIONS VS GROUND TRUTH CONTROL (50 SEEDS / 100 MATCHES)", flush=True)
    print("=" * 80, flush=True)
    ablations = {
        "Apex Base": "generated_agents_1_32_7/apex_base.py",
        "No 2-day feed buffer (4d buffer)": "generated_agents_1_32_7/ablation_no_2d_buffer.py",
        "No Cycle-2 Melons": "generated_agents_1_32_7/ablation_no_cycle2_melons.py",
        "Batch 14": "generated_agents_1_32_7/ablation_batch_14.py",
        "Batch 24": "generated_agents_1_32_7/ablation_batch_24.py",
        "No Emergency Liquidity": "generated_agents_1_32_7/ablation_no_emergency_liquidity.py",
        "No Day-0 Land": "generated_agents_1_32_7/ablation_no_day0_land.py",
    }
    
    ablation_results = {}
    for name, ab_file in ablations.items():
        t0 = time.time()
        res = run_paired_tournament(ab_file, control_path, fast_50_seeds, max_workers=10)
        ablation_results[name] = res
        print(f"Ablation [{name:<35}]: WR = {res['pooled_wr']*100:5.1f}% (P0={res['p0_wr']*100:4.1f}%, P1={res['p1_wr']*100:4.1f}%) | Margin = ${res['mean_margin']:+7.1f} ({time.time()-t0:.1f}s)", flush=True)
    
    all_results["part13_ablations"] = ablation_results
    save_intermediate(all_results)

    # =========================================================================
    # PART 14: CLEAN BATCH SWEEP UNDER 1.32.7
    # =========================================================================
    print("\n" + "=" * 80, flush=True)
    print("PART 14: CLEAN BATCH SWEEP UNDER 1.32.7 VS GROUND TRUTH CONTROL (50 SEEDS / 100 MATCHES)", flush=True)
    print("=" * 80, flush=True)
    batches = {
        "Batch 4": "generated_agents_1_32_7/sweep_batch_4.py",
        "Batch 8": "generated_agents_1_32_7/sweep_batch_8.py",
        "Batch 12": "generated_agents_1_32_7/sweep_batch_12.py",
        "Batch 14": "generated_agents_1_32_7/sweep_batch_14.py",
        "Batch 18": "generated_agents_1_32_7/sweep_batch_18.py",
        "Batch 24": "generated_agents_1_32_7/sweep_batch_24.py",
    }
    
    batch_results = {}
    for name, b_file in batches.items():
        t0 = time.time()
        res = run_paired_tournament(b_file, control_path, fast_50_seeds, max_workers=10)
        batch_results[name] = res
        print(f"Batch Sweep [{name:<12}]: WR = {res['pooled_wr']*100:5.1f}% (P0={res['p0_wr']*100:4.1f}%, P1={res['p1_wr']*100:4.1f}%) | Margin = ${res['mean_margin']:+7.1f}", flush=True)
    
    all_results["part14_batch_sweep"] = batch_results
    save_intermediate(all_results)

    # =========================================================================
    # PART 19 & 20: STRATEGY SPACE & JOINT POLICIES UNDER 1.32.7
    # =========================================================================
    print("\n" + "=" * 80, flush=True)
    print("PART 19 & 20: STRATEGY SPACE & JOINT POLICIES UNDER 1.32.7 (50 SEEDS / 100 MATCHES)", flush=True)
    print("=" * 80, flush=True)
    strategies = {
        "Cow Heavy 10C/4S (Cheaper Cows)": "generated_agents_1_32_7/strat_cow_heavy_10c_4s.py",
        "Cow Heavy 12C/2S": "generated_agents_1_32_7/strat_cow_heavy_12c_2s.py",
        "Sheep Heavy 4C/8S": "generated_agents_1_32_7/strat_sheep_heavy_4c_8s.py",
        "Geese Hybrid 8C/4S/4G": "generated_agents_1_32_7/strat_geese_hybrid_8c_4s_4g.py",
        "Melon Heavy 25M": "generated_agents_1_32_7/strat_melon_heavy_25m.py",
        "Carrot Hinge Arbitrage": "generated_agents_1_32_7/strat_carrot_hinge_arbitrage.py",
        "High Labor (8 Hands)": "generated_agents_1_32_7/strat_high_labor_8hands.py",
        "Low Labor (4 Hands)": "generated_agents_1_32_7/strat_low_labor_4hands.py",
    }
    
    strat_results = {}
    for name, s_file in strategies.items():
        t0 = time.time()
        res = run_paired_tournament(s_file, control_path, fast_50_seeds, max_workers=10)
        strat_results[name] = res
        print(f"Strategy [{name:<35}]: WR = {res['pooled_wr']*100:5.1f}% (P0={res['p0_wr']*100:4.1f}%, P1={res['p1_wr']*100:4.1f}%) | Margin = ${res['mean_margin']:+7.1f} | Mean Cash = ${res['mean_cash']:.1f}", flush=True)
        
    all_results["part19_20_strategies"] = strat_results
    save_intermediate(all_results)

    print(f"\nAll Master Results successfully written to current_engine_master_results.json", flush=True)

if __name__ == "__main__":
    run_master_suite()
