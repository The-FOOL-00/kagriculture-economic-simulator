#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Phase 020: Census Analysis & Headroom Survival Funnel Processor (§15, §16, §22, §23, §25, §27, §41)."""

from __future__ import annotations

import csv
import json
import os
import sys
from collections import Counter, defaultdict
from typing import Any, Dict, List

import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RESULTS_DIR = os.path.join(REPO_ROOT, "results")
LEDGER_PATH = os.path.join(RESULTS_DIR, "PHASE020_CENSUS_LEDGER.csv")


def analyze_census() -> Dict[str, Any]:
    if not os.path.exists(LEDGER_PATH):
        raise FileNotFoundError(f"Census ledger not found at {LEDGER_PATH}")

    rows: List[Dict[str, Any]] = []
    with open(LEDGER_PATH, "r", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            r["turn"] = int(r["turn"])
            r["seed"] = int(r["seed"])
            r["seat"] = int(r["seat"])
            r["local_delta"] = float(r["local_delta"])
            r["long_horizon_delta"] = float(r["long_horizon_delta"])
            r["direct_intervention_effect"] = float(r["direct_intervention_effect"])
            r["macro_continuation_delta"] = float(r["macro_continuation_delta"])
            r["macro_escalated"] = (r["macro_escalated"] == "True")
            r["is_safe"] = (r["is_safe"] == "True")
            r["is_tranche_related"] = (r["is_tranche_related"] == "True")
            r["is_representable"] = (r["is_representable"] == "True")
            rows.append(r)

    total_probes = len(rows)
    print(f"Loaded {total_probes} candidate probe records.")

    # 1. Non-Tranche Filter (§11)
    non_tranche_rows = [r for r in rows if not r["is_tranche_related"]]
    tranche_rows = [r for r in rows if r["is_tranche_related"]]

    # 2. Funnel Stages (§16)
    stage_all = total_probes
    stage_local_sig = [r for r in rows if r["local_delta"] > 0]
    stage_feasible = stage_local_sig  # All generated pass static feasibility
    stage_macro_safe = [r for r in stage_feasible if not (r["macro_escalated"] and r["long_horizon_delta"] < 0)]
    stage_hard_safe = [r for r in stage_macro_safe if r["is_safe"]]
    stage_lh_positive = [r for r in stage_hard_safe if r["long_horizon_delta"] > 0]
    stage_non_tranche = [r for r in stage_lh_positive if not r["is_tranche_related"]]
    stage_representable = [r for r in stage_non_tranche if r["is_representable"]]

    # Group by family in surviving non-tranche
    family_seeds: Dict[str, set] = defaultdict(set)
    for r in stage_representable:
        family_seeds[r["family"]].add(r["seed"])

    stage_repeated = [r for r in stage_representable if len(family_seeds[r["family"]]) >= 2]

    funnel_data = {
        "all_probes": len(rows),
        "local_positive": len(stage_local_sig),
        "feasible": len(stage_feasible),
        "macro_safe": len(stage_macro_safe),
        "hard_safe": len(stage_hard_safe),
        "long_horizon_positive": len(stage_lh_positive),
        "non_tranche": len(stage_non_tranche),
        "representable": len(stage_representable),
        "repeated_states": len(stage_repeated),
    }

    # 3. Category Breakdown H0..H5 (§15)
    h_counts = Counter(r["survival_category"] for r in non_tranche_rows)

    # 4. Family Matrix (§41)
    families = sorted(list(set(r["family"] for r in rows)))
    family_metrics = {}
    for fam in families:
        sub = [r for r in non_tranche_rows if r["family"] == fam]
        if not sub:
            # Check if tranche
            sub_tr = [r for r in rows if r["family"] == fam]
            deltas = [r["long_horizon_delta"] for r in sub_tr]
            family_metrics[fam] = {
                "count": len(sub_tr),
                "mean_lh_delta": float(np.mean(deltas)) if deltas else 0.0,
                "median_lh_delta": float(np.median(deltas)) if deltas else 0.0,
                "max_lh_delta": float(np.max(deltas)) if deltas else 0.0,
                "unique_seeds": len(set(r["seed"] for r in sub_tr)),
                "macro_escalation_pct": 100.0 * sum(1 for r in sub_tr if r["macro_escalated"]) / max(1, len(sub_tr)),
                "safety_pass_pct": 100.0 * sum(1 for r in sub_tr if r["is_safe"]) / max(1, len(sub_tr)),
                "non_tranche": False,
                "representable": True,
                "decision": "PERMANENT_QUARANTINE",
            }
            continue

        deltas = [r["long_horizon_delta"] for r in sub]
        unique_s = set(r["seed"] for r in sub if r["long_horizon_delta"] > 0)
        pos_cnt = sum(1 for r in sub if r["long_horizon_delta"] > 0)
        macro_esc_cnt = sum(1 for r in sub if r["macro_escalated"])
        safe_cnt = sum(1 for r in sub if r["is_safe"])

        # Decision rule (§32, §36, §51)
        mean_d = float(np.mean(deltas))
        max_d = float(np.max(deltas))
        decision = "ELIMINATED"
        if len(unique_s) >= 3 and mean_d >= 5.0 and pos_cnt >= 5:
            decision = "QUALIFIED_FOR_PILOT"
        elif pos_cnt > 0 and max_d > 10.0:
            decision = "WEAK_SIGNAL_NO_REPEAT"
        else:
            decision = "NO_ECONOMIC_HEADROOM"

        family_metrics[fam] = {
            "count": len(sub),
            "mean_lh_delta": mean_d,
            "median_lh_delta": float(np.median(deltas)),
            "max_lh_delta": max_d,
            "unique_seeds": len(unique_s),
            "macro_escalation_pct": round(100.0 * macro_esc_cnt / len(sub), 1),
            "safety_pass_pct": round(100.0 * safe_cnt / len(sub), 1),
            "non_tranche": True,
            "representable": True,
            "decision": decision,
        }

    # 5. Backbone Divergence Classes D0..D6 (§27)
    div_counts = Counter(r["divergence_class"] for r in non_tranche_rows)
    div_deltas = defaultdict(list)
    for r in non_tranche_rows:
        div_deltas[r["divergence_class"]].append(r["long_horizon_delta"])

    divergence_summary = {}
    for d_class in sorted(div_counts.keys()):
        d_sub = div_deltas[d_class]
        divergence_summary[d_class] = {
            "count": len(d_sub),
            "mean_delta": round(float(np.mean(d_sub)), 2),
            "positive_count": sum(1 for x in d_sub if x > 0),
        }

    return {
        "funnel": funnel_data,
        "h_counts": dict(h_counts),
        "family_metrics": family_metrics,
        "divergence_summary": divergence_summary,
        "total_probes": total_probes,
        "tranche_probes": len(tranche_rows),
        "non_tranche_probes": len(non_tranche_rows),
    }


if __name__ == "__main__":
    res = analyze_census()
    print(json.dumps(res, indent=2))
