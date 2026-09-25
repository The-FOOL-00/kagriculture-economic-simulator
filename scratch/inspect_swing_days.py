# SPDX-License-Identifier: MIT
import os, sys
sys.path.insert(0, os.path.abspath("."))
from kaggle_environments import make
from scripts.v32_common import load_agent

a7 = load_agent("E9_AST")
dmitrii = load_agent("E8_DMITRII")
env = make("kaggriculture", configuration={"seed": 249677})
env.run([lambda o, c=None: a7.act(o, c), lambda o, c=None: dmitrii.act(o, c)])

# Let's inspect Day 20, 23, 25, 29 where large cash swings occurred
days_of_interest = [20, 23, 25, 29]

for day in days_of_interest:
    print("=" * 80)
    print(f"ANALYSIS OF DAY {day} (Steps {day*24} to {day*24+23})")
    print("=" * 80)
    for s in range(day * 24, (day + 1) * 24):
        s0 = env.steps[s]
        s1 = env.steps[s + 1] if s + 1 < len(env.steps) else s0
        m0_now = s0[0]["observation"]["farms"][0]["money"]
        m0_next = s1[0]["observation"]["farms"][0]["money"]
        m1_now = s0[1]["observation"]["farms"][1]["money"]
        m1_next = s1[1]["observation"]["farms"][1]["money"]
        
        d0 = m0_next - m0_now
        d1 = m1_next - m1_now
        
        act0 = s0[0].get("action") or {}
        act1 = s0[1].get("action") or {}
        mkt0 = act0.get("market", [])
        mkt1 = act1.get("market", [])
        
        if abs(d0 - d1) > 50 or mkt0 or mkt1:
            px = s0[0]["observation"]["market"]["prices"]
            print(f"Step {s}: A7 dMoney={d0:+7.1f} | Dm dMoney={d1:+7.1f} | Delta(A7-Dm)={d0-d1:+7.1f}")
            if mkt0:
                print(f"   A7 mkt: {mkt0}")
            if mkt1:
                print(f"   Dm mkt: {mkt1}")
