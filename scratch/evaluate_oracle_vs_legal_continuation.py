import sys, os
sys.path.insert(0, os.path.abspath("."))
import json
from collections import defaultdict
import numpy as np

from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod

critical_seeds = [250416, 250436, 250439]

# In V54 we tested COWSWAP:
# On 250436:
# Baseline V49: margin ~ +$2,284
# V54 COWSWAP (early intervention at step 150, trading sheep for cows): margin ~ +$7,000+ on 250436, but -$1,400 on 250416!
# Why? Because 250416 didn't have pizza shop, so cows were worse than sheep!
# An illegal early policy distinguishes 250436 and 250416 at step 150 (before reveal) -> illegal alpha.
# A legal post-reveal policy can only branch at step 216 (when pizza shop appears on 250436).

def test_continuation_branches():
    results = {}
    
    # 1. Baseline V49
    for s in critical_seeds:
        sim = FastKagricultureSim(seed=s)
        obs = sim.reset()
        for step in range(719):
            a0 = v49_mod.agent(obs[0], sim.configuration)
            a1 = v44_mod.agent(obs[1], sim.configuration)
            obs, _, done, _ = sim.step([a0, a1])
            if done: break
        m0 = float(obs[0]["farms"][0]["money"])
        m1 = float(obs[0]["farms"][1]["money"])
        results[f"baseline_{s}"] = {
            "p0_money": m0, "p1_money": m1, "margin": m0 - m1
        }
        
    print("Baseline V49 results on critical seeds:")
    for s in critical_seeds:
        print(f"  Seed {s}: margin = ${results[f'baseline_{s}']['margin']:>9.2f}")

    # 2. Test Legal Post-Reveal (Step 216) Market Interventions
    # At Step 216, PIZZA_SHOP unlocks on 250436.
    # Continuation families:
    # Family B: Demand-aware sale timing (holding milk/selling milk only when price is high or town demand exists)
    # Family C: Production emphasis (attempting to buy cow / place cow / produce more milk)
    # Family D: Inventory protection (hold minimum buffer of 1-3 milk in shed without overflowing)
    
    return results

if __name__ == "__main__":
    test_continuation_branches()
