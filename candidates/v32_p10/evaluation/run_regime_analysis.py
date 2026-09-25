# SPDX-License-Identifier: MIT
"""EXP-V32-P10-02: Opponent Regime Detector Validation & Profiling.

Evaluates the deterministic regime detector across the development panel matches:
- Measures activation frequency of each regime class
- Analyzes stability across seeds and opponents
- Quantifies economic consequences associated with each regime
"""

from __future__ import annotations
import json
import os
import sys
from collections import Counter
from typing import Any, Dict, List

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
P10_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for p in (REPO_ROOT, os.path.join(REPO_ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
if P10_ROOT not in sys.path:
    sys.path.append(P10_ROOT)

from kaggle_environments import make
from v32_common import assert_frozen, check_seed_allowed, load_agent
from candidates.v32_p10.config import DEV_SEEDS_HISTORICAL
from candidates.v32_p10.incumbent import load_fresh_a7
from candidates.v32_p10.regime_detector import DeterministicRegimeDetector


def run_regime_profiling() -> Dict[str, Any]:
    assert_frozen()
    opponents = ["E8_DMITRII", "E0_V3", "SYN_AGG", "V54"]
    seeds = [249675, 249676, 249677, 249678, 249681]  # Representative dev seeds
    
    detector = DeterministicRegimeDetector()
    regime_counts = Counter()
    flag_counts = Counter()
    regime_by_opp = {o: Counter() for o in opponents}
    total_steps = 0
    
    print("\nRunning Regime Profiling across representative development seeds...")
    
    for opp_id in opponents:
        for seed in seeds:
            check_seed_allowed(seed)
            detector.reset()
            
            # Load opponent
            if opp_id == "SYN_AGG":
                from candidates.v32_p10.evaluation.run_loss_forensics import _synthetic_aggressive
                opp_fn = _synthetic_aggressive
            elif opp_id == "V54":
                from candidates.v32_p10.evaluation.run_loss_forensics import _load_opponent
                opp_fn = _load_opponent("V54")
            else:
                opp_fn = load_agent(opp_id)
                
            a7_fn = load_fresh_a7()
            env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720}, debug=False)
            
            # Step-by-step profiling
            obs = env.reset()[0]["observation"]
            
            def _wrapped_agent(obs_p, cfg=None):
                features = detector.detect(obs_p)
                regime_counts[features.primary_regime] += 1
                regime_by_opp[opp_id][features.primary_regime] += 1
                for k, v in features.flags.items():
                    if v:
                        flag_counts[k] += 1
                return a7_fn(obs_p, cfg)
                
            env.run([_wrapped_agent, opp_fn])
            total_steps += len(env.steps)
            print(f"  Profiled vs {opp_id} on Seed {seed} ({len(env.steps)} steps)")
            
    summary = {
        "total_steps": total_steps,
        "regime_distribution": dict(regime_counts),
        "regime_percentages": {k: v / max(1, total_steps) * 100.0 for k, v in regime_counts.items()},
        "flag_distribution": dict(flag_counts),
        "regime_by_opponent": {o: dict(c) for o, c in regime_by_opp.items()}
    }
    
    print("\n" + "=" * 60)
    print("REGIME PROFILE SUMMARY:")
    for reg, pct in summary["regime_percentages"].items():
        print(f"  {reg:<25}: {pct:>5.1f}% ({regime_counts[reg]} steps)")
    print("=" * 60)
    
    out_path = os.path.join(P10_ROOT, "reports", "regime_profile.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Report written to {out_path}")
    return summary


if __name__ == "__main__":
    run_regime_profiling()
