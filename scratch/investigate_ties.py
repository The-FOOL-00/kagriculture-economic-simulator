import os
import sys
import pandas as pd
import json

base_dir = r"c:\Users\Sundareswaran\Kagriculture"
sys.path.insert(0, os.path.join(base_dir, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(base_dir, "candidates", "closed_loop_architecture"))
sys.path.insert(0, os.path.join(base_dir, "scratch"))

import kagsim
from dev_004_joint_macro_scheduler import Dev004JointMacroScheduler, BASELINE_PATH
import importlib.util

spec = importlib.util.spec_from_file_location("base_check", BASELINE_PATH)
base_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base_mod)

deltas = pd.read_csv('experiments/EXP-DEV-004/PAIRED_DELTAS.csv')
ties_yarn = [246002, 246011, 246013, 246019, 246027, 246038, 246040, 246044, 246045, 246046]

print("Investigating the 10 ties with YARN_SPECIALIZED:")
for seed in ties_yarn:
    row = deltas[deltas['seed'] == seed].iloc[0]
    print(f"Seed {seed}: cand0={row['match0_cand_p0']}, base0={row['match0_base_p1']}, delta0={row['match0_delta']}, cand1={row['match1_cand_p1']}, base1={row['match1_base_p0']}, delta1={row['match1_delta']}")
