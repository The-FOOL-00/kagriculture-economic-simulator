# SPDX-License-Identifier: MIT
"""Phase 021: Deterministic Minimal Reproduction of the Cargo-Trapping Failure (§7).

Traces seed 249366, Seat 0, Step 319 where Hand 5 is forced to HARVEST mature wheat
at tile (4, 9), reproducing:
1. Baseline V3 behavior (scheduled WATER).
2. Forced HARVEST mutation at step 319.
3. Worker inventory mutation (f.inv[5]['WHEAT'] = 1).
4. Subsequent worker actions (continuing watering route carrying dead weight).
5. Downstream biological impact (crop destroyed at yield 1 instead of growing to yield 3).
6. Downstream market blockage (wheat trapped in backpack, invisible to market sells).
7. Downstream day-end reset (farmhand despawns at step 335, end-of-day dump).
"""

from __future__ import annotations

import copy
import json
import os
import sys
import tarfile

import kagsim

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
V3_TARBALL = os.path.join(REPO_ROOT, "submission_Vj_kc_v3.tar.gz")


def load_v3_agent():
    with tarfile.open(V3_TARBALL, "r:gz") as tar:
        code = tar.extractfile("main.py").read().decode("utf-8")
    ns = {}
    exec(compile(code, "v3_agent.py", "exec"), ns)
    return ns["agent"]


def run_cargo_trap_reproduction(seed: int = 249366, target_step: int = 319) -> dict:
    agent_b0 = load_v3_agent()
    agent_b1 = load_v3_agent()
    agent_m0 = load_v3_agent()
    agent_m1 = load_v3_agent()

    g_base = kagsim.Game(seed)
    g_mut = kagsim.Game(seed)

    trace = {
        "seed": seed,
        "target_step": target_step,
        "intervened_worker": "Hand 5 (unit 5)",
        "tile_coords": [4, 9],
        "steps": [],
    }

    # 1. Advance both games to target_step - 1
    for s in range(target_step):
        obs_b0, obs_b1 = g_base.observe(0), g_base.observe(1)
        g_base.step(agent_b0(obs_b0), agent_b1(obs_b1))
        obs_m0, obs_m1 = g_mut.observe(0), g_mut.observe(1)
        g_mut.step(agent_m0(obs_m0), agent_m1(obs_m1))

    # 2. At target_step: Baseline does normal plan, Mutated arm intervenes
    obs_b0, obs_b1 = g_base.observe(0), g_base.observe(1)
    act_b0 = agent_b0(obs_b0)
    act_b1 = agent_b1(obs_b1)

    obs_m0, obs_m1 = g_mut.observe(0), g_mut.observe(1)
    act_m0 = agent_m0(obs_m0)
    act_m1 = agent_m1(obs_m1)

    # Hand 5 is at index 4 of 'hands'
    b_h5_act = act_b0["hands"][4] if len(act_b0.get("hands", [])) > 4 else ["PASS"]
    pre_tile = obs_m0["farms"][0]["tiles"][9][4]

    # Apply mutation
    act_m0_patched = copy.deepcopy(act_m0)
    act_m0_patched["hands"][4] = ["HARVEST"]

    g_base.step(act_b0, act_b1)
    g_mut.step(act_m0_patched, act_m1)

    step_record = {
        "step": target_step,
        "hour": obs_m0["hour"],
        "day": obs_m0["day"],
        "pre_tile": pre_tile,
        "baseline_h5_action": b_h5_act,
        "mutated_h5_action": ["HARVEST"],
    }
    trace["steps"].append(step_record)

    # 3. Trace subsequent steps through day end (step 336)
    for s in range(target_step + 1, target_step + 18):
        obs_b0, obs_b1 = g_base.observe(0), g_base.observe(1)
        act_b0 = agent_b0(obs_b0)
        g_base.step(act_b0, agent_b1(obs_b1))

        obs_m0, obs_m1 = g_mut.observe(0), g_mut.observe(1)
        act_m0 = agent_m0(obs_m0)
        g_mut.step(act_m0, agent_m1(obs_m1))

        h5_b_inv = obs_b0["private"]["inventories"][5] if len(obs_b0["private"]["inventories"]) > 5 else None
        h5_m_inv = obs_m0["private"]["inventories"][5] if len(obs_m0["private"]["inventories"]) > 5 else None

        t_b = obs_b0["farms"][0]["tiles"][9][4]
        t_m = obs_m0["farms"][0]["tiles"][9][4]

        rec = {
            "step": s,
            "hour": obs_m0["hour"],
            "day": obs_m0["day"],
            "tile_b": t_b,
            "tile_m": t_m,
            "h5_b_inv": h5_b_inv,
            "h5_m_inv": h5_m_inv,
            "shed_b_wheat": obs_b0["private"]["shed"].get("WHEAT", 0),
            "shed_m_wheat": obs_m0["private"]["shed"].get("WHEAT", 0),
            "money_delta": obs_m0["farms"][0]["money"] - obs_b0["farms"][0]["money"],
        }
        trace["steps"].append(rec)

    return trace


if __name__ == "__main__":
    res = run_cargo_trap_reproduction()
    print("Cargo Trap Reproduction Finished.")
    print("Step 319 Intervention:")
    print("  Pre-tile state:", res["steps"][0]["pre_tile"])
    print("  Baseline action:", res["steps"][0]["baseline_h5_action"])
    print("  Mutated action:", res["steps"][0]["mutated_h5_action"])

    print("\nDownstream Trace Samples:")
    for r in res["steps"][1:]:
        s = r["step"]
        if s in (320, 325, 334, 335, 336):
            print(f"Step {s} (Day {r['day']}, Hour {r['hour']}):")
            print(f"  Tile (4,9) Base: {r['tile_b']}")
            print(f"  Tile (4,9) Mut : {r['tile_m']}")
            print(f"  Hand 5 Cargo Base: {r['h5_b_inv']} | Mut: {r['h5_m_inv']}")
            print(f"  Shed Wheat Base: {r['shed_b_wheat']} | Mut: {r['shed_m_wheat']}")
            print(f"  Cumulative Money Delta: {r['money_delta']}")

    # Save to scratch / results
    os.makedirs("results", exist_ok=True)
    with open("results/PHASE021_CARGO_TRAP_TRACE.json", "w") as f:
        json.dump(res, f, indent=2)
    print("\nSaved detailed trace to results/PHASE021_CARGO_TRAP_TRACE.json")
