"""
Smoke test for causal agents.
"""
import sys
from kaggle_environments import make

project_root = r"c:\Users\Sundareswaran\Kagriculture"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import scratch.causal_agents as ca
import opponents.live_flooder_v1 as lf

agents = [
    ("Base V2", ca.agent_base),
    ("Q3-Only", ca.agent_q3_only),
    ("Shop-Only", ca.agent_shop_only),
    ("Livestock-Only", ca.agent_livestock_only),
    ("Q3+Shop", ca.agent_q3_shop),
    ("Q3+Livestock", ca.agent_q3_livestock),
    ("Shop+Livestock", ca.agent_shop_livestock),
    ("Full Factorial", ca.agent_full_factorial),
]

print("=== Running Smoke Test for all 8 Causal Variants ===")
for name, ag in agents:
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 10001}, debug=False)
    env.run([ag, lf.agent])
    r0 = env.steps[-1][0]["reward"]
    r1 = env.steps[-1][1]["reward"]
    print(f"[{name:16s}] Finished: Us=${r0:.1f} vs LF=${r1:.1f} (Margin: ${r0-r1:+.1f})")

print("All smoke tests passed!")
