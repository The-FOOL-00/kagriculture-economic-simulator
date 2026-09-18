#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""AEC Phase 009: Development Full-Game Replay & Mechanism Attribution.

Runs 25 fresh development seeds (249025-249049, N=25 seeds, 50 mirror matches)
to assess:
1. Architectural stability in full-game continuous execution.
2. End-to-end mechanism attribution (opportunities, candidates, simulations, commits, abstentions).
3. Live vs dormant status confirmation under empirical play.
4. Strict governance enforcement (touchless holdout protection, V3 chassis hash invariant).
"""

from __future__ import annotations

import copy
import csv
import hashlib
import json
import math
import os
import sys
import tarfile
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import kagsim
from aec.config import AECConfig
from aec.integration.executor import AECExecutor

V3_TARBALL_PATH = os.path.join(REPO_ROOT, "submission_Vj_kc_v3.tar.gz")
V3_EXPECTED_SHA256 = "845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943"

# Untouched development cohort (25 seeds)
DEV_SEEDS = list(range(249025, 249050))

RESULTS_DIR = os.path.join(REPO_ROOT, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


def sha256_of_file(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def assert_governance(seed: int) -> None:
    # 1. Primary Locked Holdout
    if 340050 <= seed <= 340199:
        raise RuntimeError(f"FATAL GOVERNANCE BREACH: Primary holdout seed {seed} accessed!")
    # 2. Gate 0.3 Virgin Final Holdout
    if 214200 <= seed <= 214249:
        raise RuntimeError(f"FATAL GOVERNANCE BREACH: Gate 0.3 holdout seed {seed} accessed!")
    # 3. Prospective Tournament Cohort
    if 340300 <= seed <= 340349:
        raise RuntimeError(f"FATAL GOVERNANCE BREACH: Prospective cohort seed {seed} accessed!")

    # Verify V3 hash
    actual_sha = sha256_of_file(V3_TARBALL_PATH)
    if actual_sha != V3_EXPECTED_SHA256:
        raise RuntimeError(f"FATAL CHASSIS BREACH: V3 hash {actual_sha} != {V3_EXPECTED_SHA256}")


def load_v3_agent() -> Any:
    with tarfile.open(V3_TARBALL_PATH, "r:gz") as tar:
        member = tar.extractfile("main.py")
        if member is None:
            raise RuntimeError("Failed to extract main.py from V3 tarball")
        v3_code = member.read().decode("utf-8")
    ns: Dict[str, Any] = {"__name__": f"frozen_v3_{time.time_ns()}"}
    exec(compile(v3_code, "frozen_v3_main.py", "exec"), ns)
    return ns["agent"]


class FrozenV3ControlAgent:
    """Isolated raw frozen V3 control loaded in memory."""
    def __init__(self) -> None:
        self._agent = load_v3_agent()

    def act(self, obs: Dict[str, Any], cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self._agent(obs, cfg)


def run_mirror_match(
    seed: int,
    aec_seat: int,
    executor: Any,
    rival_agent: Any
) -> Dict[str, Any]:
    """Runs a single match under Common Random Numbers with specified seat assignment."""
    assert_governance(seed)
    game = kagsim.Game(seed)
    latencies: List[float] = []

    while not game.done:
        obs0 = game.observe(0)
        obs1 = game.observe(1)

        t0 = time.perf_counter()
        if aec_seat == 0:
            act0 = executor.act(obs0)
            lat_ms = (time.perf_counter() - t0) * 1000.0
            act1 = rival_agent.act(obs1)
        else:
            act0 = rival_agent.act(obs0)
            t0 = time.perf_counter()
            act1 = executor.act(obs1)
            lat_ms = (time.perf_counter() - t0) * 1000.0

        latencies.append(lat_ms)
        game.step(act0, act1)

    r0 = float(game.reward(0))
    r1 = float(game.reward(1))

    treatment_reward = r0 if aec_seat == 0 else r1
    control_reward = r1 if aec_seat == 0 else r0
    margin = treatment_reward - control_reward

    telemetry_history = getattr(executor, "_telemetry_history", [])
    total_opportunities = sum(t.opportunities_count for t in telemetry_history)
    total_candidates = sum(len(t.candidates) for t in telemetry_history)
    total_simulations = sum(t.simulations_run for t in telemetry_history)
    committed = sum(1 for t in telemetry_history if t.decision == "COMMIT")
    abstained = sum(1 for t in telemetry_history if t.decision == "ABSTAIN")
    fallback_count = getattr(executor, "fallback_policy", None).fallback_count if hasattr(executor, "fallback_policy") else 0

    # Per-mechanism breakdown
    commits_by_mech: Dict[str, int] = {}
    quarantined_by_mech: Dict[str, int] = {}
    for t in telemetry_history:
        if t.decision == "COMMIT" and t.committed_mechanism:
            commits_by_mech[t.committed_mechanism] = commits_by_mech.get(t.committed_mechanism, 0) + 1
        for fam, cnt in getattr(t, "quarantined_by_mechanism", {}).items():
            quarantined_by_mech[fam] = quarantined_by_mech.get(fam, 0) + cnt

    return {
        "seed": seed,
        "seat": aec_seat,
        "treatment_reward": treatment_reward,
        "control_reward": control_reward,
        "margin": margin,
        "win": margin > 0,
        "loss": margin < 0,
        "tie": margin == 0,
        "latency_p50": float(np.percentile(latencies, 50)) if latencies else 0.0,
        "latency_p95": float(np.percentile(latencies, 95)) if latencies else 0.0,
        "worst_turn_ms": float(np.max(latencies)) if latencies else 0.0,
        "mean_latency_ms": float(np.mean(latencies)) if latencies else 0.0,
        "total_opportunities": total_opportunities,
        "total_candidates": total_candidates,
        "total_simulations": total_simulations,
        "committed": committed,
        "abstained": abstained,
        "fallback_count": fallback_count,
        "commits_by_mech": commits_by_mech,
        "quarantined_by_mech": quarantined_by_mech,
    }


def main():
    print("==============================================================")
    print("AEC PHASE 009: DEVELOPMENT FULL-GAME REPLAY (25 SEEDS / 50 MATCHES)")
    print("==============================================================")
    print(f"Cohort: Fresh Development Seeds {DEV_SEEDS[0]}–{DEV_SEEDS[-1]} (N={len(DEV_SEEDS)})")
    
    # Governance pre-flight check
    for s in DEV_SEEDS:
        assert_governance(s)
    print("GOVERNANCE CHECK: All 25 seeds verified non-overlapping with protected cohorts.")
    print(f"V3 HASH CHECK: Verified {V3_EXPECTED_SHA256[:16]}...")

    cfg = AECConfig()
    matches_data: List[Dict[str, Any]] = []
    seed_deltas: List[float] = []

    t_start_all = time.time()

    for idx, seed in enumerate(DEV_SEEDS):
        t_seed0 = time.time()

        # Match 1: AEC Seat 0, V3 Seat 1
        exec0 = AECExecutor(config=cfg)
        ctrl1 = FrozenV3ControlAgent()
        res_m1 = run_mirror_match(seed, aec_seat=0, executor=exec0, rival_agent=ctrl1)
        matches_data.append(res_m1)

        # Match 2: V3 Seat 0, AEC Seat 1
        exec1 = AECExecutor(config=cfg)
        ctrl0 = FrozenV3ControlAgent()
        res_m2 = run_mirror_match(seed, aec_seat=1, executor=exec1, rival_agent=ctrl0)
        matches_data.append(res_m2)

        net_delta = (res_m1["margin"] + res_m2["margin"]) / 2.0
        seed_deltas.append(net_delta)
        tot_commits = res_m1["committed"] + res_m2["committed"]

        print(f"[{idx+1:02d}/{len(DEV_SEEDS)}] Seed {seed}: S0={res_m1['margin']:+.0f}, S1={res_m2['margin']:+.0f} | NetDelta={net_delta:+.1f} | Commits={tot_commits} | ({time.time()-t_seed0:.2f}s)")

    elapsed = time.time() - t_start_all
    arr = np.array(seed_deltas)
    mean_delta = float(np.mean(arr))
    std_delta = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
    se_delta = std_delta / np.sqrt(len(arr)) if len(arr) > 1 else 0.0
    t_stat = (mean_delta / se_delta) if se_delta > 0 else 0.0
    p_val = 2.0 * (1.0 - 0.5 * (1.0 + math.erf(abs(t_stat) / math.sqrt(2.0))))

    wins = sum(1 for d in seed_deltas if d > 0)
    losses = sum(1 for d in seed_deltas if d < 0)
    ties = sum(1 for d in seed_deltas if d == 0)

    # Attribution totals
    all_commits_by_mech: Dict[str, int] = {}
    all_quarantined_by_mech: Dict[str, int] = {}
    total_opps = sum(m["total_opportunities"] for m in matches_data)
    total_cands = sum(m["total_candidates"] for m in matches_data)
    total_sims = sum(m["total_simulations"] for m in matches_data)
    total_commits = sum(m["committed"] for m in matches_data)
    total_abstains = sum(m["abstained"] for m in matches_data)
    total_fallbacks = sum(m["fallback_count"] for m in matches_data)

    for m in matches_data:
        for k, v in m["commits_by_mech"].items():
            all_commits_by_mech[k] = all_commits_by_mech.get(k, 0) + v
        for k, v in m["quarantined_by_mech"].items():
            all_quarantined_by_mech[k] = all_quarantined_by_mech.get(k, 0) + v

    # Save to CSV
    csv_path = os.path.join(RESULTS_DIR, "PHASE009_DEVELOPMENT_REPLAY.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "seed", "seat", "treatment_reward", "control_reward", "margin",
            "win", "loss", "tie", "latency_p50", "latency_p95", "worst_turn_ms",
            "total_opportunities", "total_candidates", "total_simulations",
            "committed", "abstained", "fallback_count"
        ], extrasaction="ignore")
        writer.writeheader()
        for row in matches_data:
            writer.writerow(row)

    print("\n==============================================================")
    print("PHASE 009 DEVELOPMENT REPLAY SUMMARY")
    print("==============================================================")
    print(f"Total Matches: 50 (25 seeds x 2 mirror seats)")
    print(f"Elapsed Time: {elapsed:.2f}s ({elapsed/50:.2f}s/match)")
    print(f"Mirror Win/Loss/Tie: {wins}W / {losses}L / {ties}T")
    print(f"Mean Net Delta: ${mean_delta:+.2f} +/- ${se_delta:.2f} (t={t_stat:.2f}, p={p_val:.4f})")
    print(f"Total Opportunities Detected: {total_opps}")
    print(f"Total Candidates Screened: {total_cands}")
    print(f"Total Exact Counterfactual Simulations: {total_sims}")
    print(f"Total Commits: {total_commits}")
    print(f"Total Abstains: {total_abstains}")
    print(f"Total Fallbacks: {total_fallbacks} (Zero unexpected aborts)")
    print(f"Commits by Mechanism: {all_commits_by_mech}")
    print(f"Quarantined by Mechanism: {all_quarantined_by_mech}")
    print(f"Results CSV: {csv_path}")


if __name__ == "__main__":
    main()
