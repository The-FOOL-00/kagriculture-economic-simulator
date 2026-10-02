import sys, os
sys.path.insert(0, os.path.abspath("."))
import json
from typing import Dict, Any, List

from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod

CRITICAL_SEEDS = [250416, 250436, 250439]
SNAPSHOT_STEPS = [207, 215, 216, 217, 287, 288, 289, 360, 504, 718]

def run_trace(seed: int, seat: int = 0) -> Dict[str, Any]:
    opp_seat = 1 - seat
    sim = FastKagricultureSim(seed=seed)
    obs = sim.reset()
    
    actions_log = []
    snapshots = {}
    
    for step in range(719):
        # Record snapshots at target steps
        if step in SNAPSHOT_STEPS:
            snapshots[str(step)] = {
                "step": step,
                "shops": list(obs[seat]["town"]["unlocked_shops"]),
                "prices": dict(obs[seat]["market"]["prices"]),
                "inventory": dict(obs[seat]["market"]["inventory"]),
                "v49_cash": float(obs[seat]["farms"][seat]["money"]),
                "opp_cash": float(obs[seat]["farms"][opp_seat]["money"]),
                "v49_hands": len(obs[seat]["farms"][seat]["hands"]),
                "opp_hands": len(obs[seat]["farms"][opp_seat]["hands"]),
            }
            
        a0 = v49_mod.agent(obs[0], sim.configuration)
        a1 = v44_mod.agent(obs[1], sim.configuration)
        
        if step < 220:
            actions_log.append({
                "step": step,
                "a0": a0,
                "a1": a1
            })
            
        obs, rewards, done, info = sim.step([a0, a1])
        if done:
            break
            
    final_v49 = float(obs[seat]["farms"][seat]["money"])
    final_opp = float(obs[seat]["farms"][opp_seat]["money"])
    
    return {
        "seed": seed,
        "seat": seat,
        "terminal_v49_cash": final_v49,
        "terminal_opp_cash": final_opp,
        "terminal_margin": final_v49 - final_opp,
        "snapshots": snapshots,
        "prefix_actions": actions_log
    }

traces = {s: run_trace(s, 0) for s in CRITICAL_SEEDS}

# Compare prefix actions between 250416 and 250436
mismatches_actions = []
for t in range(216):
    a0_416 = traces[250416]["prefix_actions"][t]["a0"]
    a0_436 = traces[250436]["prefix_actions"][t]["a0"]
    a1_416 = traces[250416]["prefix_actions"][t]["a1"]
    a1_436 = traces[250436]["prefix_actions"][t]["a1"]
    
    if a0_416 != a0_436:
        mismatches_actions.append(f"Step {t} V49 Action Mismatch")
    if a1_416 != a1_436:
        mismatches_actions.append(f"Step {t} Opponent Action Mismatch")

print("=== PREFIX PARITY AUDIT (Steps 0..215) ===")
print(f"Action mismatches between Seed 250416 and Seed 250436 up to Step 215: {len(mismatches_actions)}")
if not mismatches_actions:
    print("CONFIRMED: Actions are 100% BIT-FOR-BIT IDENTICAL through Step 215.")

# First legal difference point
first_diff_step = None
first_diff_field = None
for s in SNAPSHOT_STEPS:
    s416 = traces[250416]["snapshots"][str(s)]
    s436 = traces[250436]["snapshots"][str(s)]
    if s416 != s436:
        first_diff_step = s
        for k in s416:
            if s416[k] != s436[k]:
                first_diff_field = f"{k}: 416={s416[k]} vs 436={s436[k]}"
                break
        break

print(f"\nFirst legal divergence point between 250416 and 250436: Step {first_diff_step}")
print(f"Diverging field: {first_diff_field}")

parity_data = {
    "prefix_parity_steps": 215,
    "actions_identical": len(mismatches_actions) == 0,
    "first_divergence_step": first_diff_step,
    "first_divergence_field": first_diff_field,
    "critical_snapshots": {
        "250416": traces[250416]["snapshots"],
        "250436": traces[250436]["snapshots"],
        "250439": traces[250439]["snapshots"],
    }
}

os.makedirs("research/v55/analysis", exist_ok=True)
with open("research/v55/analysis/V49_PREFIX_PARITY.json", "w") as f:
    json.dump(parity_data, f, indent=2)

print("\nSaved research/v55/analysis/V49_PREFIX_PARITY.json")
