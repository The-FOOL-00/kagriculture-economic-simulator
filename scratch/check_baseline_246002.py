import os, sys, importlib.util
spec = importlib.util.spec_from_file_location('base_check', 'candidates/compiled_v54_plus_residual.py')
base_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base_mod)

import kagsim
g = kagsim.Game(246002)
o0 = g.observe(0)
# Let's inspect the baseline agent state as it steps
base = base_mod
step = 0
while not g.done:
    o0 = g.observe(0)
    o1 = g.observe(1)
    a0 = base.agent(o0)
    # Check if base has active route or internal route name
    if step in [72, 144, 216, 288]:
        # print any state attributes
        print(f"Step {step}: base unlocked_shops={o0.get('town', {}).get('unlocked_shops')}")
    g.step(a0, a0)
    step += 1

print("Done stepping baseline.")
