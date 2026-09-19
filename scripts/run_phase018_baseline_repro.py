#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Phase 018: Baseline reproducibility re-execution of the Phase 017 audit harness.

Re-runs the exact Phase 017 treatment-vs-foundation CRN mirror protocol on the
consumed Phase 017 cohort (249286..249295) to prove the frozen baseline is
reproducible from the current working tree. Outputs are redirected to
PHASE018_BASELINE_REPRO_* so Phase 017 artifacts stay untouched.

Run with the canonical Windows interpreter:
  PYTHONPATH="external_repos/kaggriculture-cppsim;." python -m scripts.run_phase018_baseline_repro
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

import scripts.run_phase017_attribution_audit as audit

audit.LEDGER_CSV = os.path.join(audit.RESULTS_DIR, "PHASE018_BASELINE_REPRO_LEDGER.csv")
audit.CTRL_COMMITS_CSV = os.path.join(
    audit.RESULTS_DIR, "PHASE018_BASELINE_REPRO_CONTROL_COMMITS.csv"
)
audit.SUMMARY_JSON = os.path.join(audit.RESULTS_DIR, "PHASE018_BASELINE_REPRO_SUMMARY.json")


def main() -> None:
    print("PHASE018 BASELINE REPRO: re-executing Phase017 protocol on 249286..249295")
    summary = audit.execute_attribution_audit(max_workers=6)
    print(f"REPRO mean check: total={summary['total_candidates']} "
          f"sim={summary['simulated_candidates']} esc={summary['escalated_candidates']} "
          f"comm={summary['committed_candidates']}")


if __name__ == "__main__":
    main()
