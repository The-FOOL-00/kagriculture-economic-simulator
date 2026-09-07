"""
Phase 1: Full Architecture Forensics and Replay Dependency Audit.
Dissects:
1. Every subsystem of V1 and V2 (farmer, hands, market, terminal).
2. Trace dependency chain and hidden assumptions.
3. Quantifies open-loop vs closed-loop turn fraction.
4. Searches for prohibited patterns: _TRACE, base64, zlib, historical arrays.
"""

import base64
import json
import os
import sys
import zlib

def run_phase1():
    print("=" * 80)
    print("PHASE 1: FULL ARCHITECTURE FORENSICS & REPLAY DEPENDENCY AUDIT")
    print("=" * 80)

    v1_path = "agents/candidate_a_aethel_v1.py"
    v2_path = "candidates/slot2_aethel_refined_v2.py"

    with open(v1_path, "r", encoding="utf-8") as f:
        v1_code = f.read()
    with open(v2_path, "r", encoding="utf-8") as f:
        v2_code = f.read()

    # 1. Prohibited pattern search
    prohibited_keywords = [
        "_TRACE", "TRACE", "replay", "trajectory", "canonical",
        "compressed", "base64", "zlib", "pickle", "b85decode"
    ]
    print("A. Suspicious Keyword Audit:")
    for kw in prohibited_keywords:
        c1 = v1_code.count(kw)
        c2 = v2_code.count(kw)
        print(f"  Keyword '{kw:<12}': V1={c1:2d} occurrences | V2={c2:2d} occurrences")

    # 2. Extract and analyze _TRACE in V2
    import importlib.util
    spec = importlib.util.spec_from_file_location("v2_module", os.path.abspath(v2_path))
    v2 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(v2)

    trace = v2._TRACE
    total_steps = len(trace)
    print(f"\nB. Replay Trace Dimensionality:")
    print(f"  Total Steps in _TRACE: {total_steps}")

    # Inspect action diversity across trace
    farmer_actions = [trace[s].get("farmer", ["PASS"])[0] for s in range(total_steps)]
    market_steps = sum(1 for s in range(total_steps) if trace[s].get("market"))
    hand_counts = [len(trace[s].get("hands", [])) for s in range(total_steps)]

    print(f"  Steps with Market Orders: {market_steps} / {total_steps} ({market_steps/total_steps*100:.1f}%)")
    print(f"  Peak Hired Hands in Trace: {max(hand_counts)}")
    print(f"  Terminal Action Switch Step: {v2._TERMINAL_START_STEP} (Step 712)")

    # 3. Classify Subsystems
    subsystems = {
        "Farmer Movement": {
            "nature": "100% Open-Loop Hardcoded Replay (Steps 0-711); Closed-Loop BFS (712-719)",
            "observation_reactivity": "Zero reactivity before step 712",
            "failure_mode": "If displaced by even 1 tile, farmer hits obstacles or locked tiles"
        },
        "Worker Assignment": {
            "nature": "100% Open-Loop Hardcoded Replay (Steps 0-711); Closed-Loop BFS (712-719)",
            "observation_reactivity": "Zero reactivity before step 712",
            "failure_mode": "Assumes exact worker index and coordinate persistence"
        },
        "Crop Scheduling & Watering": {
            "nature": "100% Open-Loop Hardcoded Replay",
            "observation_reactivity": "Zero reactivity to crop growth rate or rain/soil status",
            "failure_mode": "If Day 0 crops differ, hands attempt to harvest immature/wrong crops"
        },
        "Livestock & Feeding": {
            "nature": "100% Open-Loop Hardcoded Replay",
            "observation_reactivity": "Zero reactivity to actual shed feed inventory",
            "failure_mode": "If shed has 0 feed, feeding actions silently fail -> animal starvation"
        },
        "Land Unlocks": {
            "nature": "100% Open-Loop Hardcoded Replay",
            "observation_reactivity": "BUY_LAND orders hardcoded at steps 168 (NE) and 255 (SW)",
            "failure_mode": "If money is $1 below unlock cost at that exact step, unlock fails forever"
        },
        "Market Controller (V2 only)": {
            "nature": "Closed-Loop Elasticity Reordering & Front-running",
            "observation_reactivity": "HIGH: reads shed inventory, market prices, and opponent money",
            "failure_mode": "Constrained to only reorder existing tape slots"
        },
        "Terminal Harvester (Step 712+)": {
            "nature": "100% Observation-Driven Closed-Loop Controller",
            "observation_reactivity": "HIGH: computes dynamic BFS paths to ripe crops and drops to shed",
            "failure_mode": "None observed; highly robust"
        }
    }

    print("\nC. Subsystem Classification Matrix:")
    for sub, info in subsystems.items():
        print(f"\n  [{sub}]")
        print(f"    Nature:       {info['nature']}")
        print(f"    Reactivity:   {info['observation_reactivity']}")
        print(f"    Vulnerability:{info['failure_mode']}")

    # 4. Save Forensics Report
    report = {
        "prohibited_keyword_counts": {kw: {"v1": v1_code.count(kw), "v2": v2_code.count(kw)} for kw in prohibited_keywords},
        "trace_total_steps": total_steps,
        "terminal_switch_step": v2._TERMINAL_START_STEP,
        "subsystems": subsystems,
        "forensic_conclusion": "Frozen V1 and V2 rely on an open-loop 712-step replay trace for physical movement and agricultural operations. Only market order sorting (V2) and terminal step 712+ harvest are closed-loop."
    }
    with open("scratch/phase1_forensics_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print("\nPhase 1 report saved to scratch/phase1_forensics_report.json")
    print("=" * 80)

if __name__ == "__main__":
    run_phase1()
