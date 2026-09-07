import sys, os
sys.path.insert(0, os.path.abspath('.'))
from scratch.evaluate_temporal_telemetry import run_telemetry_match
from candidates.candidate_closed_loop_commitment_v1 import agent as comm_agent
import time

print("Starting smoke test of candidate_closed_loop_commitment_v1...")
t0 = time.time()
res = run_telemetry_match(comm_agent, seed=42)
t1 = time.time()
print(f"Elapsed: {t1-t0:.2f}s")
print(f"Seed 42 Results:")
for k, v in res.items():
    if isinstance(v, float):
        print(f"  {k:<20}: {v:.2f}")
    else:
        print(f"  {k:<20}: {v}")
