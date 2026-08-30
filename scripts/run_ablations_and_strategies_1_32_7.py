import os
import sys
import json
import time
from master_harness import run_paired_tournament

def main():
    control_path = "agents/ground_truth_control_current_engine.py"
    master_json_path = "current_engine_master_results.json"
    
    with open(master_json_path, "r", encoding="utf-8") as f:
        all_results = json.load(f)

    # 25 paired seeds (50 matches each) across dev and holdout
    seeds = list(range(1000, 1015)) + list(range(50000, 50010)) # 25 paired seeds = 50 matches
    print(f"Running Ablations, Batch Sweep, and Strategy Search with {len(seeds)} paired seeds (50 matches each)...", flush=True)

    # =========================================================================
    # PART 13: CORE APEX ONE-VARIABLE ABLATIONS
    # =========================================================================
    print("\n" + "=" * 80, flush=True)
    print("PART 13: CORE APEX ONE-VARIABLE ABLATIONS VS GROUND TRUTH CONTROL", flush=True)
    print("=" * 80, flush=True)
    ablations = {
        "Apex Base (1.32.7)": "generated_agents_1_32_7/apex_base.py",
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
        res = run_paired_tournament(ab_file, control_path, seeds, max_workers=10)
        ablation_results[name] = res
        print(f"Ablation [{name:<35}]: WR = {res['pooled_wr']*100:5.1f}% (P0={res['p0_wr']*100:4.1f}%, P1={res['p1_wr']*100:4.1f}%) | Margin = ${res['mean_margin']:+7.1f} | Cash = ${res['mean_cash']:.0f} ({time.time()-t0:.1f}s)", flush=True)
    
    all_results["part13_ablations"] = ablation_results
    with open(master_json_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    # =========================================================================
    # PART 14: CLEAN BATCH SWEEP UNDER 1.32.7
    # =========================================================================
    print("\n" + "=" * 80, flush=True)
    print("PART 14: CLEAN BATCH SWEEP UNDER 1.32.7 VS GROUND TRUTH CONTROL", flush=True)
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
        res = run_paired_tournament(b_file, control_path, seeds, max_workers=10)
        batch_results[name] = res
        print(f"Batch Sweep [{name:<12}]: WR = {res['pooled_wr']*100:5.1f}% (P0={res['p0_wr']*100:4.1f}%, P1={res['p1_wr']*100:4.1f}%) | Margin = ${res['mean_margin']:+7.1f} | Cash = ${res['mean_cash']:.0f} ({time.time()-t0:.1f}s)", flush=True)
    
    all_results["part14_batch_sweep"] = batch_results
    with open(master_json_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    # =========================================================================
    # PART 19 & 20: STRATEGY SPACE & JOINT POLICIES UNDER 1.32.7
    # =========================================================================
    print("\n" + "=" * 80, flush=True)
    print("PART 19 & 20: STRATEGY SPACE & JOINT POLICIES UNDER 1.32.7", flush=True)
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
        res = run_paired_tournament(s_file, control_path, seeds, max_workers=10)
        strat_results[name] = res
        print(f"Strategy [{name:<35}]: WR = {res['pooled_wr']*100:5.1f}% (P0={res['p0_wr']*100:4.1f}%, P1={res['p1_wr']*100:4.1f}%) | Margin = ${res['mean_margin']:+7.1f} | Cash = ${res['mean_cash']:.0f} ({time.time()-t0:.1f}s)", flush=True)
    
    all_results["part19_strategy_space"] = strat_results
    with open(master_json_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    print("\nAll Revalidated Results successfully written to current_engine_master_results.json", flush=True)

if __name__ == "__main__":
    main()
