import os, sys, json
sys.path.insert(0, r'c:\Users\Sundareswaran\Kagriculture')
from scratch.master_tournament_runner import run_paired_tournament

if __name__ == '__main__':
    apex_path = r'c:\Users\Sundareswaran\Kagriculture\agents\apex_synthesis_v3.py'
    ctrl_path = r'c:\Users\Sundareswaran\Kagriculture\agents\ground_truth_control_current_engine.py'
    titan_path = r'c:\Users\Sundareswaran\Kagriculture\opponents\o1_titan.py'

    print("Running Apex v3 vs Control on 2 seeds...")
    res_ctrl = run_paired_tournament(apex_path, ctrl_path, [10000, 10001])
    print("Apex v3 vs Control:", json.dumps(res_ctrl, indent=2))

    print("\nRunning Apex v3 vs Titan on 2 seeds...")
    res_titan = run_paired_tournament(apex_path, titan_path, [10000, 10001])
    print("Apex v3 vs Titan:", json.dumps(res_titan, indent=2))
