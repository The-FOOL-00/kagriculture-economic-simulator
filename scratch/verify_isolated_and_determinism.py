#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
scratch/verify_isolated_and_determinism.py
=========================================
Executes:
  - Phase 8: Isolated Execution Test (temp directory, sys.path stripped, zero local repo files)
  - Phase 9: Kaggle Raw-File Compatibility (720 turns, status DONE)
  - Phase 10: Determinism Test (10 repeated seeds run twice, telemetry SHA256 verification)
"""

from __future__ import annotations

import os
import sys
import shutil
import tempfile
import hashlib
import json
import kaggle_environments


def test_isolated_raw_execution(agent_path: str, agent_name: str, test_seeds: list[int]):
    print(f"\n--- Testing Isolated Execution for {agent_name} ---")
    repo_root = os.path.abspath(".")
    
    with tempfile.TemporaryDirectory(prefix="kagg_championship_iso_") as temp_dir:
        dest_main = os.path.join(temp_dir, "main.py")
        shutil.copyfile(agent_path, dest_main)
        print(f"Copied {agent_path} -> {dest_main}")

        # Execute inside temporary directory with clean sys.path
        orig_cwd = os.getcwd()
        orig_sys_path = list(sys.path)
        
        try:
            # Strip Kagriculture repo paths from sys.path
            sys.path = [
                p for p in sys.path
                if os.path.abspath(p) != repo_root and "kagriculture" not in p.lower() or "site-packages" in p.lower()
            ]
            os.chdir(temp_dir)

            for seed in test_seeds:
                env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
                res = env.run(["main.py", "starter"])
                
                status = env.state[0].status
                reward = env.state[0].reward
                steps_count = len(env.steps)
                act1 = env.steps[1][0].get("action")
                
                print(f"  Seed {seed}: Steps={steps_count} | Status={status} | Reward=${reward:,.2f} | Act1={act1}")
                assert status == "DONE", f"Isolated status failed: {status}"
                assert steps_count == 720, f"Expected 720 steps, got {steps_count}"
                assert reward is not None and reward > 5000.0, f"Reward {reward} indicates failure/inactivity"
                assert act1 is not None, "First action is None!"

        finally:
            os.chdir(orig_cwd)
            sys.path = orig_sys_path

    print(f"PASS: Isolated raw execution verified for {agent_name} across {len(test_seeds)} seeds!")


def test_determinism(agent_path: str, agent_name: str, repeat_seeds: list[int]):
    print(f"\n--- Testing Determinism for {agent_name} ---")
    import importlib.util
    spec = importlib.util.spec_from_file_location("det_mod", agent_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    agent_fn = mod.agent

    for seed in repeat_seeds:
        # Run 1
        env1 = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
        env1.run([agent_fn, "starter"])
        telemetry1 = []
        for step in env1.steps:
            telemetry1.append(step[0].get("action"))
        r1 = env1.state[0].reward
        hash1 = hashlib.sha256(json.dumps(telemetry1, sort_keys=True).encode()).hexdigest()

        # Run 2
        env2 = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
        env2.run([agent_fn, "starter"])
        telemetry2 = []
        for step in env2.steps:
            telemetry2.append(step[0].get("action"))
        r2 = env2.state[0].reward
        hash2 = hashlib.sha256(json.dumps(telemetry2, sort_keys=True).encode()).hexdigest()

        match = (r1 == r2) and (hash1 == hash2)
        print(f"  Seed {seed}: Run1=${r1:,.2f} (sha={hash1[:8]}) | Run2=${r2:,.2f} (sha={hash2[:8]}) | Match: {match}")
        assert match, f"Determinism failure on seed {seed}!"

    print(f"PASS: 100% Determinism verified for {agent_name} across {len(repeat_seeds)} repeated seeds!")


def main():
    print("=" * 80)
    print("PHASES 8, 9, 10: ISOLATED RAW EXECUTION & DETERMINISM HARNESS")
    print("=" * 80)

    ctrl_path = os.path.abspath("candidates/compiled_v54_plus_shop.py")
    res_path = os.path.abspath("candidates/compiled_v54_plus_residual.py")

    iso_seeds = [970001, 970002, 970003, 970004, 970005]
    det_seeds = list(range(970010, 970020))

    # Phase 8 & 9: Isolated Raw Execution
    test_isolated_raw_execution(ctrl_path, "Compiled V54++ Control", iso_seeds)
    test_isolated_raw_execution(res_path, "Compiled V54++ Residual", iso_seeds)

    # Phase 10: Determinism
    test_determinism(ctrl_path, "Compiled V54++ Control", det_seeds)
    test_determinism(res_path, "Compiled V54++ Residual", det_seeds)

    print("\n" + "=" * 80)
    print("ALL PHASES 8, 9, 10 TESTS PASSED WITH 100% CONFORMANCE!")
    print("=" * 80)


if __name__ == "__main__":
    main()
