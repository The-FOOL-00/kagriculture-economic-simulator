#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Phase 018 Repair A diagnostic: seed 249288 funnel-crowding replay.

Consumed-seed diagnostic (NOT qualification evidence): replays the documented
Phase017 crowding failure (control +$1,485 DEPENDENCY_AWARE_MARKET_TIMING commit
at step 649, treatment 0 commits) under A1 (reservation OFF) vs A2 (reservation
ON) to verify the repair mechanism at the unit-of-causality level.

Fresh-cohort Arm A pilot remains the evidentiary basis; this script answers
spec §13 ("whether seed 249288 is repaired") mechanistically.
"""

from __future__ import annotations

import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
CPPSIM = os.path.join(REPO_ROOT, "external_repos", "kaggriculture-cppsim")
if CPPSIM not in sys.path:
    sys.path.insert(0, CPPSIM)

import kagsim
from aec.config import build_phase015_treatment_config, build_phase018_arm_a2_config
from aec.integration.executor import AECExecutor

SEED = 249288
FOUND = "DEPENDENCY_AWARE_MARKET_TIMING"


def run_mirror(make_trt_cfg, label: str) -> dict:
    margins = []
    step649: dict = {}
    for seat in (0, 1):
        game = kagsim.Game(SEED)
        trt = AECExecutor(config=make_trt_cfg())
        ctrl = AECExecutor(config=__import__("aec.config", fromlist=["x"]).build_robust_qualified_config())
        while not game.done:
            o0, o1 = game.observe(0), game.observe(1)
            if seat == 0:
                a0, a1 = trt.act(o0), ctrl.act(o1)
            else:
                a0, a1 = ctrl.act(o0), trt.act(o1)
            game.step(a0, a1)
        r0, r1 = float(game.reward(0)), float(game.reward(1))
        margins.append((r0 - r1) if seat == 0 else (r1 - r0))
        for t in getattr(trt, "_telemetry_history", []):
            if t.step == 649:
                fams = [(c.patch_id, c.mechanism_family, c.simulation_run,
                         c.patch_pruned, c.commit_decision) for c in t.candidates]
                step649[seat] = {
                    "decision": t.decision, "abstain": t.abstain_reason,
                    "opps": t.opportunities_count, "cands": t.candidates_count,
                    "sims": t.simulations_run,
                    "foundation_simulated": any(
                        m == FOUND and s for _, m, s, _, _ in fams),
                    "foundation_committed": t.committed_mechanism == FOUND,
                    "committed": t.committed_mechanism,
                    "reservation": {k: (v.to_dict() if hasattr(v, "to_dict") else v)
                                    for k, v in (t.funnel_reservation or {}).items()},
                }
    paired = sum(margins) / 2
    print(f"[{label}] seat margins={margins} paired={paired:+.0f}")
    for seat in (0, 1):
        s = step649.get(seat, {})
        print(f"  seat {seat} step649: decision={s.get('decision')} "
              f"opps={s.get('opps')} sims={s.get('sims')} "
              f"found_sim={s.get('foundation_simulated')} "
              f"found_commit={s.get('foundation_committed')} "
              f"commit={s.get('committed')} abstain={s.get('abstain')}")
        for site, rec in (s.get("reservation") or {}).items():
            print(f"    res[{site}]: before={rec['before']} after={rec['after']} "
                  f"saved={[x['id'] for x in rec['saved']]}")
    return {"label": label, "margins": margins, "paired": paired, "step649": step649}


def main() -> None:
    a1 = run_mirror(build_phase015_treatment_config, "A1-OFF")
    a2 = run_mirror(build_phase018_arm_a2_config, "A2-ON")
    print(f"249288 repair delta (A2-A1 paired): {a2['paired'] - a1['paired']:+.0f}")


if __name__ == "__main__":
    main()
