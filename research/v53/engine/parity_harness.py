#!/usr/bin/env python3
"""Current Engine Parity Harness (V53 Critical Phase Zero).

Performs exhaustive bit-for-bit parity testing between the official installed
kaggle_environments.envs.kaggriculture engine and research.v40.env.fast_sim.FastKagricultureSim.
"""

import copy
import hashlib
import json
import os
import sys
import time
from typing import Any, Dict, List, Tuple

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import kaggle_environments
from kaggle_environments import make
import kaggle_environments.envs.kaggriculture.kaggriculture as official_kg
from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod


def get_file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def normalize_obj(obj: Any) -> Any:
    """Recursively converts structify objects, dicts, lists, and tuples into standard JSON-comparable types."""
    if hasattr(obj, "__dict__") and not isinstance(obj, dict):
        return {k: normalize_obj(v) for k, v in obj.__dict__.items() if not k.startswith("_")}
    elif isinstance(obj, dict):
        return {k: normalize_obj(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [normalize_obj(v) for v in obj]
    else:
        return obj


def compare_states(official_obs: Any, fast_obs: Any, step: int) -> List[str]:
    """Compares all observation fields between official engine and FastSim."""
    o_dict = normalize_obj(official_obs)
    f_dict = normalize_obj(fast_obs)

    mismatches = []
    
    # 1. Step, day, hour
    for k in ("step", "day", "hour"):
        if o_dict.get(k) != f_dict.get(k):
            mismatches.append(f"Step {step}: field '{k}' mismatch (Official={o_dict.get(k)}, FastSim={f_dict.get(k)})")

    # 2. Market inventory and prices
    o_mkt = o_dict.get("market", {})
    f_mkt = f_dict.get("market", {})
    if o_mkt.get("inventory") != f_mkt.get("inventory"):
        mismatches.append(f"Step {step}: market inventory mismatch (Official={o_mkt.get('inventory')}, FastSim={f_mkt.get('inventory')})")
    if o_mkt.get("prices") != f_mkt.get("prices"):
        mismatches.append(f"Step {step}: market prices mismatch (Official={o_mkt.get('prices')}, FastSim={f_mkt.get('prices')})")

    # 3. Town unlocked shops
    o_town = o_dict.get("town", {})
    f_town = f_dict.get("town", {})
    if o_town.get("unlocked_shops") != f_town.get("unlocked_shops"):
        mismatches.append(f"Step {step}: town unlocked_shops mismatch (Official={o_town.get('unlocked_shops')}, FastSim={f_town.get('unlocked_shops')})")

    # 4. Farms comparison (for both seats 0 and 1)
    o_farms = o_dict.get("farms", [])
    f_farms = f_dict.get("farms", [])
    if len(o_farms) != len(f_farms):
        mismatches.append(f"Step {step}: farms length mismatch")
    else:
        for p in range(len(o_farms)):
            of = o_farms[p]
            ff = f_farms[p]
            for field in ("money", "farmer", "hands", "shed", "animals", "tiles"):
                if of.get(field) != ff.get(field):
                    mismatches.append(f"Step {step}: Player {p} farm '{field}' mismatch (Official={of.get(field)}, FastSim={ff.get(field)})")

    return mismatches


def run_parity_test(seed: int, steps: int = 719) -> Dict[str, Any]:
    print(f"\n--- Running Parity Test: Seed {seed} ({steps} steps) ---")
    t0 = time.time()

    # Official environment
    env = make("kaggriculture", configuration={"seed": seed})
    env.reset()

    # FastSim environment
    fast = FastKagricultureSim(seed=seed)
    f_obs = fast.reset(seed=seed)

    all_mismatches = []
    
    # Check reset state
    init_mismatches = compare_states(env.state[0].observation, f_obs[0], step=0)
    if init_mismatches:
        all_mismatches.extend(init_mismatches)
        print(f"  FAILED at Step 0: {len(init_mismatches)} mismatches")

    agent0 = v49_mod.agent
    agent1 = v44_mod.agent

    for step in range(steps):
        # Obtain actions from agents using official observation
        obs0 = env.state[0].observation
        obs1 = env.state[1].observation

        act0 = agent0(obs0)
        act1 = agent1(obs1)

        # Step official engine
        env.step([act0, act1])

        # Step FastSim
        fast_obs, fast_rew, fast_done, fast_info = fast.step([act0, act1])

        # Compare observations
        step_mismatches = compare_states(env.state[0].observation, fast_obs[0], step=step + 1)
        if step_mismatches:
            all_mismatches.extend(step_mismatches)
            print(f"  MISMATCH at Step {step + 1}: {step_mismatches[0]}")
            if len(all_mismatches) > 10:
                print("  Truncating further mismatch logging.")
                break

    elapsed = time.time() - t0
    final_official_money = [env.state[0].observation.farms[0]["money"], env.state[1].observation.farms[1]["money"]]
    final_fast_money = [fast_obs[0]["farms"][0]["money"], fast_obs[1]["farms"][1]["money"]]

    passed = (len(all_mismatches) == 0)
    print(f"  Parity Result: {'PASS (100% BIT-EXACT)' if passed else 'FAIL'}")
    print(f"  Official Money: P0=${final_official_money[0]:,.2f}, P1=${final_official_money[1]:,.2f}")
    print(f"  FastSim Money:  P0=${final_fast_money[0]:,.2f}, P1=${final_fast_money[1]:,.2f}")
    print(f"  Elapsed: {elapsed:.2f}s ({steps / elapsed:.1f} steps/s)")

    return {
        "seed": seed,
        "steps_evaluated": steps,
        "passed": passed,
        "mismatches_count": len(all_mismatches),
        "sample_mismatches": all_mismatches[:5],
        "final_official_money": final_official_money,
        "final_fast_money": final_fast_money,
        "elapsed_seconds": elapsed,
    }


def main():
    print("=" * 80)
    print("V53 CRITICAL PHASE ZERO: CURRENT ENGINE PARITY HARNESS")
    print("=" * 80)

    # 1. Inspect installed engine metadata
    kg_pkg_dir = os.path.dirname(official_kg.__file__)
    kg_py_path = os.path.join(kg_pkg_dir, "kaggriculture.py")
    kg_json_path = os.path.join(kg_pkg_dir, "kaggriculture.json")
    fast_sim_path = os.path.join(REPO_ROOT, "research", "v40", "env", "fast_sim.py")

    hashes = {
        "kaggle_environments_version": kaggle_environments.__version__,
        "official_kaggriculture_py": {
            "path": kg_py_path,
            "sha256": get_file_sha256(kg_py_path),
            "size_bytes": os.path.getsize(kg_py_path),
        },
        "official_kaggriculture_json": {
            "path": kg_json_path,
            "sha256": get_file_sha256(kg_json_path),
            "size_bytes": os.path.getsize(kg_json_path),
        },
        "fast_sim_py": {
            "path": fast_sim_path,
            "sha256": get_file_sha256(fast_sim_path),
            "size_bytes": os.path.getsize(fast_sim_path),
        }
    }

    out_hashes_path = os.path.join(REPO_ROOT, "research", "v53", "engine", "ENGINE_HASHES.json")
    os.makedirs(os.path.dirname(out_hashes_path), exist_ok=True)
    with open(out_hashes_path, "w", encoding="utf-8") as f:
        json.dump(hashes, f, indent=2)
    print(f"Saved engine hashes to {out_hashes_path}")

    # 2. Run deterministic identical matches
    test_seeds = [250400, 250436, 250439]
    results = []
    for s in test_seeds:
        res = run_parity_test(seed=s, steps=719)
        results.append(res)

    out_results_path = os.path.join(REPO_ROOT, "research", "v53", "engine", "ENGINE_PARITY_RESULTS.json")
    with open(out_results_path, "w", encoding="utf-8") as f:
        json.dump({
            "version": kaggle_environments.__version__,
            "tests": results,
            "overall_parity": all(r["passed"] for r in results),
        }, f, indent=2)
    print(f"\nSaved parity test results to {out_results_path}")


if __name__ == "__main__":
    main()
