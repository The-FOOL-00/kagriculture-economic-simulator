import os, sys, json
sys.path.insert(0, r'c:\Users\Sundareswaran\Kagriculture')
from scratch.master_tournament_runner import run_paired_tournament

if __name__ == '__main__':
    cand_path = r'c:\Users\Sundareswaran\Kagriculture\candidates\slot5_hybrid_8c4s.py'
    titan_path = r'c:\Users\Sundareswaran\Kagriculture\opponents\o1_titan.py'

    print("Running Candidate Slot 5 vs Titan on seeds 10000, 10001...")
    res = run_paired_tournament(cand_path, titan_path, [10000, 10001])
    print("Result:", json.dumps(res, indent=2))
