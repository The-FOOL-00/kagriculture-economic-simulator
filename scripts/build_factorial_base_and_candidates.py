# SPDX-License-Identifier: MIT
"""
Build Immutable Factorial Baseline and Clean Candidates A, B, C, D
Strictly Isolating Market Controller and Step-712 Terminal Trigger.
"""

import os
import hashlib
import json

def sha256_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def main():
    os.makedirs("agents", exist_ok=True)
    os.makedirs("scratch", exist_ok=True)

    with open("replays/raw/reference_agents/closer_cleo.py", "r", encoding="utf-8") as f:
        src = f.read()

    # 1. Parameterize cleanly at module level
    # Disable front running (_FRONT_RUN_HORIZON = 0) in all candidates
    old_fr = "_FRONT_RUN_HORIZON = 1"
    new_params = "_FRONT_RUN_HORIZON = 0\n_MARKET_CONTROLLER_ENABLED = False\n_TERMINAL_START_STEP = 717"
    assert old_fr in src, "Could not find _FRONT_RUN_HORIZON = 1"
    base_code = src.replace(old_fr, new_params, 1)

    # In _base_agent, use _TERMINAL_START_STEP
    old_base_terminal = "if step >= 717:\n        return _terminal_action(obs)"
    new_base_terminal = "if step >= _TERMINAL_START_STEP:\n        return _terminal_action(obs)"
    assert old_base_terminal in base_code, "Could not find old terminal in _base_agent"
    base_code = base_code.replace(old_base_terminal, new_base_terminal, 1)

    # In agent, check _MARKET_CONTROLLER_ENABLED and use _TERMINAL_START_STEP
    old_agent_def = 'def agent(obs, config=None):\n    """c27 with its SELL layer partially replaced by the market controller."""\n    action = _base_agent(obs, config)\n    try:\n        step = int(obs.get("step", 0) or 0)\n        if step >= 717:\n            return action  # proven terminal controller; leave untouched'
    
    new_agent_def = 'def agent(obs, config=None):\n    """c27 with parameterized market controller and terminal trigger."""\n    if not _MARKET_CONTROLLER_ENABLED:\n        return _base_agent(obs, config)\n    action = _base_agent(obs, config)\n    try:\n        step = int(obs.get("step", 0) or 0)\n        if step >= _TERMINAL_START_STEP:\n            return action  # proven terminal controller; leave untouched'

    assert old_agent_def in base_code, "Could not find old agent def"
    base_code = base_code.replace(old_agent_def, new_agent_def, 1)

    # Write immutable baseline
    base_path = "agents/aethel_factorial_base.py"
    with open(base_path, "w", encoding="utf-8") as f:
        f.write(base_code)
    base_sha = sha256_file(base_path)
    print(f"Factorial Base written to {base_path} (SHA-256: {base_sha})")

    # Generate Candidate A: MC = OFF, T = 717, FR = 0
    cand_a_code = base_code
    cand_a_path = "agents/candidate_a_aethel_v1.py"
    with open(cand_a_path, "w", encoding="utf-8") as f:
        f.write(cand_a_code)
    sha_a = sha256_file(cand_a_path)

    # Generate Candidate B: MC = ON, T = 717, FR = 0
    cand_b_code = base_code.replace("_MARKET_CONTROLLER_ENABLED = False", "_MARKET_CONTROLLER_ENABLED = True", 1)
    cand_b_path = "agents/candidate_b_aethel_mc.py"
    with open(cand_b_path, "w", encoding="utf-8") as f:
        f.write(cand_b_code)
    sha_b = sha256_file(cand_b_path)

    # Generate Candidate C: MC = OFF, T = 712, FR = 0
    cand_c_code = base_code.replace("_TERMINAL_START_STEP = 717", "_TERMINAL_START_STEP = 712", 1)
    cand_c_path = "agents/candidate_c_aethel_t712.py"
    with open(cand_c_path, "w", encoding="utf-8") as f:
        f.write(cand_c_code)
    sha_c = sha256_file(cand_c_path)

    # Generate Candidate D: MC = ON, T = 712, FR = 0
    cand_d_code = base_code.replace("_MARKET_CONTROLLER_ENABLED = False", "_MARKET_CONTROLLER_ENABLED = True", 1)
    cand_d_code = cand_d_code.replace("_TERMINAL_START_STEP = 717", "_TERMINAL_START_STEP = 712", 1)
    cand_d_path = "agents/candidate_d_aethel_refined.py"
    with open(cand_d_path, "w", encoding="utf-8") as f:
        f.write(cand_d_code)
    sha_d = sha256_file(cand_d_path)

    manifest = {
        "engine_version": "1.32.7",
        "baseline_file": base_path,
        "baseline_sha256": base_sha,
        "candidate_a": {
            "path": cand_a_path,
            "sha256": sha_a,
            "market_controller": False,
            "terminal_712": False,
            "front_running": False
        },
        "candidate_b": {
            "path": cand_b_path,
            "sha256": sha_b,
            "market_controller": True,
            "terminal_712": False,
            "front_running": False
        },
        "candidate_c": {
            "path": cand_c_path,
            "sha256": sha_c,
            "market_controller": False,
            "terminal_712": True,
            "front_running": False
        },
        "candidate_d": {
            "path": cand_d_path,
            "sha256": sha_d,
            "market_controller": True,
            "terminal_712": True,
            "front_running": False
        },
        "market_controller": {
            "A": False,
            "B": True,
            "C": False,
            "D": True
        },
        "terminal_712": {
            "A": False,
            "B": False,
            "C": True,
            "D": True
        },
        "front_running": {
            "A": False,
            "B": False,
            "C": False,
            "D": False
        }
    }

    manifest_path = "scratch/factorial_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print("\n--- GENERATED CANDIDATES ---")
    print(f"Candidate A (Baseline: MC=OFF, T=717, FR=OFF): {cand_a_path} (SHA-256: {sha_a})")
    print(f"Candidate B (Market:   MC=ON,  T=717, FR=OFF): {cand_b_path} (SHA-256: {sha_b})")
    print(f"Candidate C (Terminal: MC=OFF, T=712, FR=OFF): {cand_c_path} (SHA-256: {sha_c})")
    print(f"Candidate D (Combined: MC=ON,  T=712, FR=OFF): {cand_d_path} (SHA-256: {sha_d})")
    print(f"\nSaved experiment manifest to {manifest_path}")

if __name__ == "__main__":
    main()
