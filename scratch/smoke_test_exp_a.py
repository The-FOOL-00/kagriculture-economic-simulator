"""
EXP-A Smoke Test: 5 seeds vs IDLE and V2
Checks for crashes and minimum reward > 20,000.
"""
import sys
import os
import json
import traceback

sys.path.insert(0, ".")
sys.path.insert(0, "candidates/declarative_backbone")

# Reset agent between games
from candidates.declarative_backbone.agent import agent as backbone_agent, reset as backbone_reset

# Load the harness / arena
from benchmark_harness import run_match

SMOKE_SEEDS = [1000, 1001, 1002, 1003, 1004]
OPPONENTS = {
    "IDLE": None,  # will handle idle below
    "V2":   "agents/slot4_control_frozen_v2.py",
}

results = {}

for opp_name, opp_path in OPPONENTS.items():
    opp_results = []
    print(f"\n=== {opp_name} ===")
    for seed in SMOKE_SEEDS:
        backbone_reset()
        try:
            if opp_path is None:
                # IDLE opponent
                def idle_agent(obs, cfg=None):
                    return {"market": [], "farmer": ["PASS"], "hands": []}
                r = run_match(backbone_agent, idle_agent, seed=seed, max_steps=720)
            else:
                import importlib.util
                spec = importlib.util.spec_from_file_location("opp_mod", opp_path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                opp_fn = getattr(mod, "agent", None) or mod._kaggle_submission_entrypoint
                r = run_match(backbone_agent, opp_fn, seed=seed, max_steps=720)
            
            our_reward = r["rewards"][0]
            opp_reward = r["rewards"][1]
            status = "PASS" if our_reward > 20000 else "FAIL"
            print(f"  seed={seed}: our={our_reward:.0f}  opp={opp_reward:.0f}  [{status}]")
            opp_results.append({"seed": seed, "our": our_reward, "opp": opp_reward, "ok": our_reward > 20000, "error": None})
        except Exception as e:
            tb = traceback.format_exc()
            print(f"  seed={seed}: CRASH: {e}")
            print(f"    {tb[:500]}")
            opp_results.append({"seed": seed, "our": 0, "opp": 0, "ok": False, "error": str(e)})
        finally:
            backbone_reset()
    
    results[opp_name] = opp_results

print("\n=== SMOKE TEST SUMMARY ===")
all_pass = True
for opp_name, rows in results.items():
    ok = all(r["ok"] for r in rows)
    crashes = sum(1 for r in rows if r["error"])
    means = sum(r["our"] for r in rows) / len(rows)
    print(f"{opp_name}: {'PASS' if ok else 'FAIL'}  mean_reward={means:.0f}  crashes={crashes}")
    if not ok:
        all_pass = False

print()
print("OVERALL:", "PASS - proceed to VALIDATION panel" if all_pass else "FAIL - diagnose before proceeding")
json.dump(results, open("scratch/smoke_test_results.json", "w"), indent=2)
