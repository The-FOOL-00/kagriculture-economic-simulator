import os, sys, json, multiprocessing, time
sys.path.insert(0, r'c:\Users\Sundareswaran\Kagriculture')

from scratch.master_tournament_runner import run_paired_tournament
from agents.apex_grandmaster_v4 import ApexGrandmasterV4
from agents.slot4_control_frozen_v2 import FrozenControlSlot4

# Load seed sets
def load_seeds(filepath, limit=50):
    with open(filepath, 'r') as f:
        seeds = [int(line.strip()) for line in f if line.strip().isdigit()]
    return seeds[:limit]

dev_seeds_50 = load_seeds(r'benchmarks/seeds/development.txt', 50)
holdout_seeds_50 = load_seeds(r'benchmarks/seeds/holdout.txt', 50)
val_seeds_50 = [30000 + i for i in range(50)]
full_100_seeds = dev_seeds_50 + holdout_seeds_50

ctrl_path = r'c:\Users\Sundareswaran\Kagriculture\agents\ground_truth_control_current_engine.py'
titan_path = r'c:\Users\Sundareswaran\Kagriculture\opponents\o1_titan.py'
apex_path = r'c:\Users\Sundareswaran\Kagriculture\agents\apex_grandmaster_v4.py'

print("="*70)
print("STARTING FULL RIGOROUS BENCHMARK & EXPERIMENTATION SUITE")
print("="*70)

# Helper to generate custom wrapper agents for parameter / ablation sweeps
def create_agent_wrapper(classname, kwargs, output_path):
    code = f'''import sys
sys.path.insert(0, r"c:\\Users\\Sundareswaran\\Kagriculture")
from agents.apex_grandmaster_v4 import ApexGrandmasterV4

_instance = ApexGrandmasterV4(**{repr(kwargs)})
def agent(obs, cfg=None):
    return _instance(obs, cfg)
'''
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(code)
    return output_path

if __name__ == '__main__':
    all_master_results = {}
    
    # -------------------------------------------------------------
    # 1. CONTROL VS CONTROL SELF-PLAY (DEV, VAL, HOLDOUT BLOCKS)
    # -------------------------------------------------------------
    print("\n[PHASE 1] Running Control vs Control Self-Play across 3 Seed Blocks...")
    res_ctrl_dev = run_paired_tournament(ctrl_path, ctrl_path, dev_seeds_50)
    res_ctrl_val = run_paired_tournament(ctrl_path, ctrl_path, val_seeds_50)
    res_ctrl_hold = run_paired_tournament(ctrl_path, ctrl_path, holdout_seeds_50)
    
    all_master_results["control_selfplay"] = {
        "dev_50": res_ctrl_dev,
        "val_50": res_ctrl_val,
        "holdout_50": res_ctrl_hold
    }
    print("  Dev 50 matches:", res_ctrl_dev["matches"], "Pooled WR:", res_ctrl_dev["pooled_wr"], "P0 WR:", res_ctrl_dev["p0_wr"], "P1 WR:", res_ctrl_dev["p1_wr"])
    print("  Val 50 matches:", res_ctrl_val["matches"], "Pooled WR:", res_ctrl_val["pooled_wr"], "P0 WR:", res_ctrl_val["p0_wr"], "P1 WR:", res_ctrl_val["p1_wr"])
    print("  Holdout 50 matches:", res_ctrl_hold["matches"], "Pooled WR:", res_ctrl_hold["pooled_wr"], "P0 WR:", res_ctrl_hold["p0_wr"], "P1 WR:", res_ctrl_hold["p1_wr"])
    
    # -------------------------------------------------------------
    # 2. APEX V4 VS GROUND TRUTH CONTROL (100 PAIRED SEEDS)
    # -------------------------------------------------------------
    print("\n[PHASE 2] Running Apex v4 vs Ground Truth Control on 100 Paired Seeds...")
    res_apex_vs_ctrl = run_paired_tournament(apex_path, ctrl_path, full_100_seeds)
    all_master_results["apex_vs_control_100"] = res_apex_vs_ctrl
    print(f"  Apex vs Control: {res_apex_vs_ctrl['cand_wins']}/{res_apex_vs_ctrl['matches']} ({res_apex_vs_ctrl['pooled_wr']*100:.1f}%), Mean Margin: +${res_apex_vs_ctrl['mean_margin']:,.1f}")

    # -------------------------------------------------------------
    # 3. APEX V4 VS CANONICAL TITAN (100 PAIRED SEEDS)
    # -------------------------------------------------------------
    print("\n[PHASE 3] Running Apex v4 vs Canonical Titan on 100 Paired Seeds...")
    res_apex_vs_titan = run_paired_tournament(apex_path, titan_path, full_100_seeds)
    all_master_results["apex_vs_titan_100"] = res_apex_vs_titan
    print(f"  Apex vs Titan: {res_apex_vs_titan['cand_wins']}/{res_apex_vs_titan['matches']} ({res_apex_vs_titan['pooled_wr']*100:.1f}%), Mean Margin: +${res_apex_vs_titan['mean_margin']:,.1f}")

    # -------------------------------------------------------------
    # 4. BATCH SIZE SWEEP (4, 8, 12, 14, 16, 18, 20, 24, 28, 32)
    # -------------------------------------------------------------
    print("\n[PHASE 4] Running Full 10-Point Batch Size Sweep vs Control (50 Paired Seeds each)...")
    batch_results = {}
    os.makedirs('scratch/batch_sweep_agents', exist_ok=True)
    for b in [4, 8, 12, 14, 16, 18, 20, 24, 28, 32]:
        b_agent_path = create_agent_wrapper(
            "ApexGrandmasterV4",
            {"sell_batch": b},
            f"scratch/batch_sweep_agents/apex_batch_{b}.py"
        )
        b_res = run_paired_tournament(b_agent_path, ctrl_path, dev_seeds_50)
        batch_results[b] = b_res
        print(f"  Batch {b:2d}: WR {b_res['pooled_wr']*100:5.1f}% | Mean Cash: ${b_res['mean_cand_cash']:,.0f} | Margin: +${b_res['mean_margin']:,.0f}")
    all_master_results["batch_sweep"] = batch_results

    # -------------------------------------------------------------
    # 5. COMPONENT ATTRIBUTION / ABLATION STUDY
    # -------------------------------------------------------------
    print("\n[PHASE 5] Running Component Attribution Study (50 Paired Seeds each)...")
    ablation_configs = {
        "apex_baseline": {},
        "no_4day_feed_buffer": {"feed_buffer_days": 2},
        "no_400_cow_cost": {"cow_cost": 600},
        "no_cycle2_melons": {"cycle2_melons": 0},
        "no_emergency_liquidity": {"emergency_liquidity": False},
        "batch_14_control": {"sell_batch": 14}
    }
    ablation_results = {}
    os.makedirs('scratch/ablation_agents_v4', exist_ok=True)
    for name, cfg in ablation_configs.items():
        ab_path = create_agent_wrapper("ApexGrandmasterV4", cfg, f"scratch/ablation_agents_v4/{name}.py")
        ab_res = run_paired_tournament(ab_path, ctrl_path, dev_seeds_50)
        ablation_results[name] = ab_res
        print(f"  Ablation [{name:22s}]: WR {ab_res['pooled_wr']*100:5.1f}% | Mean Cash: ${ab_res['mean_cand_cash']:,.0f} | Margin: +${ab_res['mean_margin']:,.0f}")
    all_master_results["ablation_study"] = ablation_results

    # Save all results to disk
    out_file = r'c:\Users\Sundareswaran\Kagriculture\scratch\full_forensic_suite_results.json'
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(all_master_results, f, indent=2)
    print("\n" + "="*70)
    print(f"ALL BENCHMARKS COMPLETED SUCCESSFULLY! Results saved to {out_file}")
    print("="*70)
