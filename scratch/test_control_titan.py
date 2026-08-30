import os, sys, json
sys.path.insert(0, r'c:\Users\Sundareswaran\Kagriculture')
from scratch.master_tournament_runner import run_paired_tournament

if __name__ == '__main__':
    control_path = r'c:\Users\Sundareswaran\Kagriculture\agents\slot4_control_frozen_v2.py'
    titan_path = r'c:\Users\Sundareswaran\Kagriculture\opponents\o1_titan.py'

    print("Running Control vs Titan on seeds 10000, 10001...")
    res = run_paired_tournament(control_path, titan_path, [10000, 10001])
    print("Result:", json.dumps(res, indent=2))
