import os, sys, json
sys.path.insert(0, r'c:\Users\Sundareswaran\Kagriculture')
from scratch.master_tournament_runner import run_paired_tournament

if __name__ == '__main__':
    apex4_path = r'c:\Users\Sundareswaran\Kagriculture\agents\apex_grandmaster_v4.py'
    ctrl_path = r'c:\Users\Sundareswaran\Kagriculture\agents\ground_truth_control_current_engine.py'
    titan_path = r'c:\Users\Sundareswaran\Kagriculture\opponents\o1_titan.py'

    print("Running Apex v4 vs Control on 2 seeds...")
    res_ctrl = run_paired_tournament(apex4_path, ctrl_path, [10000, 10001])
    print("Apex v4 vs Control:", json.dumps(res_ctrl, indent=2))

    print("\nRunning Apex v4 vs Titan on 2 seeds...")
    res_titan = run_paired_tournament(apex4_path, titan_path, [10000, 10001])
    print("Apex v4 vs Titan:", json.dumps(res_titan, indent=2))
