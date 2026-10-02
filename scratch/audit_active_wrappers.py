import sys, os, copy
sys.path.insert(0, os.path.abspath('.'))
from research.v40.env.fast_sim import FastKagricultureSim

with open('research/final_synthesis/teammates/v27/decoded_inner.py', 'r', encoding='utf-8') as f:
    text = f.read()

ns = {}
exec(compile(text, 'v27_instrumented', 'exec'), ns)

# Let's inspect all telemetry dicts defined in ns
telemetries = {}
for k, v in ns.items():
    if isinstance(v, dict) and ('REPORT' in k or 'STATS' in k):
        telemetries[k] = v

print(f"Total report/stats dicts found: {len(telemetries)}")

# Now run 1 game and observe telemetry changes
sim = FastKagricultureSim(seed=250600)
obs = sim.reset(seed=250600)
agent = ns['agent']

for step in range(719):
    a0 = agent(obs[0])
    a1 = agent(obs[1])
    obs, r, done, info = sim.step([a0, a1])

print("\n--- NON-ZERO TELEMETRY REPORTS AFTER 719 STEPS ---")
active_count = 0
zero_count = 0
for k, v in sorted(telemetries.items()):
    # Check if any field is non-zero
    is_active = any(val > 0 for val in v.values() if isinstance(val, (int, float)))
    if is_active:
        active_count += 1
        print(f"ACTIVE: {k} -> {v}")
    else:
        zero_count += 1

print(f"\nSummary: {active_count} active telemetries, {zero_count} zero/inert telemetries.")
