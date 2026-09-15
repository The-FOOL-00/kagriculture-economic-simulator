#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
scratch/verify_behavioral_equivalence_50seeds.py
================================================
Evaluates 50 fresh seeds comparing original modular harnesses vs compiled standalone deployment artifacts.
Verifies turn-by-turn action equality across all 720 turns, reward equality, and status equality.
Generates `research/compiled_behavior_mismatches.csv`.
"""

from __future__ import annotations

import csv
import importlib.util
import os
import sys
import time
from kaggle_environments import make

# Add paths for modular loading
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for p in [
    os.path.join(BASE_DIR, "external_repos", "lixingtao123-Kaggriculture", "variant_v54_h3q4"),
    os.path.join(BASE_DIR, "external_repos", "kaggriculture-v66-agent"),
    os.path.join(BASE_DIR, "candidates"),
]:
    if p not in sys.path:
        sys.path.insert(0, p)


def load_agent(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.agent


def run_equivalence():
    print("=" * 80)
    print("PHASES 6 & 7: 50-SEED TURN-BY-TURN BEHAVIORAL EQUIVALENCE TEST")
    print("=" * 80)

    orig_ctrl = load_agent("orig_ctrl", "candidates/v54_plus_shop.py")
    comp_ctrl = load_agent("comp_ctrl", "candidates/compiled_v54_plus_shop.py")

    orig_res = load_agent("orig_res", "candidates/v54_plus_residual.py")
    comp_res = load_agent("comp_res", "candidates/compiled_v54_plus_residual.py")

    test_seeds = list(range(960001, 960051))
    mismatches = []

    print(f"Testing {len(test_seeds)} fresh seeds (960001–960050)...")

    t0 = time.time()
    for idx, s in enumerate(test_seeds):
        # 1. Control Test
        env_orig_c = make("kaggriculture", configuration={"episodeSteps": 720, "seed": s})
        env_orig_c.run([orig_ctrl, "starter"])
        r_orig_c = env_orig_c.state[0].reward
        st_orig_c = env_orig_c.state[0].status

        env_comp_c = make("kaggriculture", configuration={"episodeSteps": 720, "seed": s})
        env_comp_c.run([comp_ctrl, "starter"])
        r_comp_c = env_comp_c.state[0].reward
        st_comp_c = env_comp_c.state[0].status

        # Turn-by-turn action comparison
        ctrl_action_mismatch = None
        for step_idx in range(len(env_orig_c.steps)):
            act_o = env_orig_c.steps[step_idx][0].get("action")
            act_c = env_comp_c.steps[step_idx][0].get("action")
            if act_o != act_c:
                ctrl_action_mismatch = (step_idx, act_o, act_c)
                break

        if r_orig_c != r_comp_c or st_orig_c != st_comp_c or ctrl_action_mismatch is not None:
            mismatches.append({
                "agent": "V54++ Control",
                "seed": s,
                "orig_reward": r_orig_c,
                "comp_reward": r_comp_c,
                "orig_status": st_orig_c,
                "comp_status": st_comp_c,
                "action_mismatch_step": ctrl_action_mismatch[0] if ctrl_action_mismatch else None,
                "orig_action": str(ctrl_action_mismatch[1]) if ctrl_action_mismatch else None,
                "comp_action": str(ctrl_action_mismatch[2]) if ctrl_action_mismatch else None,
            })

        # 2. Residual Test
        env_orig_r = make("kaggriculture", configuration={"episodeSteps": 720, "seed": s})
        env_orig_r.run([orig_res, "starter"])
        r_orig_r = env_orig_r.state[0].reward
        st_orig_r = env_orig_r.state[0].status

        env_comp_r = make("kaggriculture", configuration={"episodeSteps": 720, "seed": s})
        env_comp_r.run([comp_res, "starter"])
        r_comp_r = env_comp_r.state[0].reward
        st_comp_r = env_comp_r.state[0].status

        res_action_mismatch = None
        for step_idx in range(len(env_orig_r.steps)):
            act_o = env_orig_r.steps[step_idx][0].get("action")
            act_c = env_comp_r.steps[step_idx][0].get("action")
            if act_o != act_c:
                res_action_mismatch = (step_idx, act_o, act_c)
                break

        if r_orig_r != r_comp_r or st_orig_r != st_comp_r or res_action_mismatch is not None:
            mismatches.append({
                "agent": "V54++ Residual",
                "seed": s,
                "orig_reward": r_orig_r,
                "comp_reward": r_comp_r,
                "orig_status": st_orig_r,
                "comp_status": st_comp_r,
                "action_mismatch_step": res_action_mismatch[0] if res_action_mismatch else None,
                "orig_action": str(res_action_mismatch[1]) if res_action_mismatch else None,
                "comp_action": str(res_action_mismatch[2]) if res_action_mismatch else None,
            })

        if (idx + 1) % 10 == 0 or idx == len(test_seeds) - 1:
            elapsed = time.time() - t0
            print(f"[{idx+1:2d}/{len(test_seeds)}] Seeds processed ({elapsed:5.1f}s) | Current Mismatches: {len(mismatches)}")

    # Write CSV report
    out_csv = os.path.join(BASE_DIR, "research", "compiled_behavior_mismatches.csv")
    fieldnames = [
        "agent", "seed", "orig_reward", "comp_reward", "orig_status",
        "comp_status", "action_mismatch_step", "orig_action", "comp_action"
    ]
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in mismatches:
            writer.writerow(row)

    print("-" * 80)
    print(f"Report written to: {out_csv}")
    print(f"Total Mismatches Detected: {len(mismatches)} across {len(test_seeds) * 2} agent-episodes")
    assert len(mismatches) == 0, f"FAILED: Behavioral mismatches found! {mismatches}"
    print("VERDICT: 100% PERFECT TURN-BY-TURN EQUIVALENCE CONFIRMED ACROSS ALL 50 SEEDS!")


if __name__ == "__main__":
    run_equivalence()
