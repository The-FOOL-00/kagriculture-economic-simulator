import sys
import os

REPO_ROOT = r"c:\Users\Sundareswaran\Kagriculture"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v50.counterfactuals.run_exact_counterfactuals import evaluate_mechanism

if __name__ == "__main__":
    seeds = [250400 + i for i in range(8)]
    res_v49_check = evaluate_mechanism("V49_Parity_Check", {}, seeds, ["V44"])


    print("Active legs vs V49:", res_v49_check["active_legs"])
    print("Mean delta vs V49:", res_v49_check["mean_delta_vs_v49"])

