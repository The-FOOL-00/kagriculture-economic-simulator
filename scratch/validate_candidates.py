import os
import sys
import importlib.util
from kaggle_environments import make

print("=" * 80)
print("VALIDATING CANDIDATES A THROUGH H")
print("=" * 80)

candidates = ["A", "B", "C", "D", "E", "F", "G", "H"]

for c_name in candidates:
    fpath = f"candidates/counterstrategy_ablation/candidate_{c_name}.py"
    assert os.path.exists(fpath), f"File {fpath} does not exist!"
    
    # Test import
    spec = importlib.util.spec_from_file_location(f"cand_{c_name}", fpath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert hasattr(mod, "agent"), f"Candidate {c_name} missing agent() function!"
    
    # Quick 1-step test
    env = make("kaggriculture", configuration={"episodeSteps": 10, "seed": 42}, debug=True)
    env.run([fpath, "opponents/o1_titan.py"])
    r0 = env.steps[-1][0].reward
    print(f"Candidate {c_name} [VALIDATED] -> 10-step reward: ${r0}")

print("\nAll 8 candidates successfully validated.")
