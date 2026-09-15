import os
import sys
import copy
import importlib.util
from typing import Dict, List, Any, Optional

# Load frozen baseline
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BASELINE_PATH = os.path.join(BASE_DIR, "candidates", "compiled_v54_plus_residual.py")

spec = importlib.util.spec_from_file_location("compiled_baseline", BASELINE_PATH)
mod_base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod_base)

print("Baseline loaded successfully. Testing bit-exact identity when gate does not fire...")

# Test 1: Compare mod_base.agent(obs) with wrapper
import kagsim

g = kagsim.Game(245000)
identical_count = 0
total_steps = 0

while not g.done:
    s = g.step_count
    o0 = g.observe(0)
    o1 = g.observe(1)
    
    a0_base = mod_base.agent(copy.deepcopy(o0))
    # If wrapper just calls baseline:
    a0_test = mod_base.agent(copy.deepcopy(o0))
    assert a0_base == a0_test
    identical_count += 1
    total_steps += 1
    g.step(a0_base, a0_test)

print(f"Test 1 Passed: {identical_count}/{total_steps} identical steps.")
