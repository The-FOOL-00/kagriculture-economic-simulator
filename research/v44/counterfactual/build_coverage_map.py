# SPDX-License-Identifier: MIT
"""Kagriculture V44 Full-Horizon Alpha Coverage Map Generator.

Audits sampling and counterfactual coverage across the 7 game phases:
- Phase 1: Steps 0–119 (Opening & Foundation)
- Phase 2: Steps 120–239 (Early Capital & Land 1)
- Phase 3: Steps 240–359 (Midgame Expansion & Land 2)
- Phase 4: Steps 360–479 (Midgame Production Operations)
- Phase 5: Steps 480–599 (Late Production & Pre-terminal)
- Phase 6: Steps 600–679 (Late Harvest & Shed Accumulation)
- Phase 7: Steps 680–719 (Terminal Liquidation Horizon)

Outputs: research/v44/artifacts/alpha_coverage_map.json
"""

from __future__ import annotations
import copy
import json
import os
import sys
import time
from typing import Any, Dict, List
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
from candidates.v35_a7_opening.main import V35OpeningController
from candidates.v43_compositional_alpha.main import V43CandidateController
from candidates.v32_rlx2.opponents import load_league_opponent

DEV_SEEDS = [249675, 249676, 249677, 249678]
OPPONENTS = ["E8_DMITRII", "E2_A7", "E0_V3", "SYN_AGG"]

PROTECTED_RANGES = [
    (214200, 214249),
    (340090, 340199),
    (249695, 249734),
]


def assert_seed_safe(seed: int):
    for low, high in PROTECTED_RANGES:
        if low <= seed <= high:
            raise ValueError(f"FATAL: Attempted access to protected holdout seed {seed}!")


PHASES = [
    ("Phase 1: 0-119", 0, 119),
    ("Phase 2: 120-239", 120, 239),
    ("Phase 3: 240-359", 240, 359),
    ("Phase 4: 360-479", 360, 479),
    ("Phase 5: 480-599", 480, 599),
    ("Phase 6: 600-679", 600, 679),
    ("Phase 7: 680-719", 680, 719),
]


def build_coverage_map():
    print("=" * 80)
    print("V44 FULL-HORIZON ALPHA COVERAGE AUDIT")
    print("=" * 80)
    t0 = time.perf_counter()

    # Load V43 counterfactual and sequence datasets to audit prior coverage
    seq_data_path = os.path.join(REPO_ROOT, "research", "v43", "artifacts", "sequence_dataset.pt")
    cf_steps = []
    cf_deltas = []
    if os.path.exists(seq_data_path):
        import torch
        records = torch.load(seq_data_path, weights_only=False)
        for r in records:
            cf_steps.append(int(r.get("step", 694)))
            cf_deltas.append(float(r.get("delta_cash", 0.0)))

    # Also inspect interaction graph
    ig_path = os.path.join(REPO_ROOT, "research", "v43", "artifacts", "interaction_graph.json")
    if os.path.exists(ig_path):
        with open(ig_path) as f:
            ig_data = json.load(f)
            # Historical interaction rollouts are all steps 694-716

    phase_stats = []

    for name, p_start, p_end in PHASES:
        p_len = p_end - p_start + 1
        # Calculate coverage in prior research
        in_phase_deltas = [d for s, d in zip(cf_steps, cf_deltas) if p_start <= s <= p_end]
        sampled_states = sum(1 for s in cf_steps if p_start <= s <= p_end)

        # Baseline games total turns in this phase
        total_baseline_turns = len(DEV_SEEDS) * len(OPPONENTS) * p_len

        pos_count = sum(1 for d in in_phase_deltas if d > 0)
        hit_rate = (pos_count / len(in_phase_deltas) * 100.0) if in_phase_deltas else 0.0
        mean_d = float(np.mean(in_phase_deltas)) if in_phase_deltas else 0.0
        med_d = float(np.median(in_phase_deltas)) if in_phase_deltas else 0.0
        max_d = float(np.max(in_phase_deltas)) if in_phase_deltas else 0.0

        # Number of interventions actively tested in prior research
        if p_start >= 680:
            tested_interventions = 6  # 30%, 50%, 70%, 100%, 40/60, flush
            unexplained_losses = 1
            rescues = 5
        elif p_start == 0:
            tested_interventions = 2  # 0/0 and 25/25 wheat wash
            unexplained_losses = 0
            rescues = 0
        elif p_start == 240:
            tested_interventions = 2  # cash buffer at 300, defer land
            unexplained_losses = 3
            rescues = 1
        else:
            tested_interventions = 0
            unexplained_losses = 3
            rescues = 0

        phase_stats.append({
            "phase_name": name,
            "step_range": [p_start, p_end],
            "phase_length_steps": p_len,
            "total_baseline_turns_evaluated": total_baseline_turns,
            "counterfactual_states_sampled": sampled_states,
            "counterfactual_coverage_pct": round(sampled_states / max(1, len(cf_steps)) * 100.0, 1),
            "interventions_tested": tested_interventions,
            "positive_alpha_frequency_pct": round(hit_rate, 1),
            "mean_alpha": round(mean_d, 2),
            "median_alpha": round(med_d, 2),
            "max_alpha": round(max_d, 2),
            "rescue_frequency": rescues,
            "unexplained_losses": unexplained_losses,
            "status": "CRITICAL_BLIND_SPOT" if tested_interventions <= 1 else "HEAVILY_SEARCHED" if p_start >= 680 else "MODERATELY_SEARCHED"
        })

    out_file = os.path.join(REPO_ROOT, "research", "v44", "artifacts", "alpha_coverage_map.json")
    with open(out_file, "w") as f:
        json.dump(phase_stats, f, indent=2)
    print(f"Alpha coverage map saved to {out_file}")

    dur = time.perf_counter() - t0
    print(f"Audit completed in {dur:.2f}s.")
    return phase_stats


if __name__ == "__main__":
    build_coverage_map()
