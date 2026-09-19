#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Phase 015: Oracle Replay Evaluation Harness (§28, §29, §34).

Replays Phase 014 positive-headroom diagnostic states against:
1. Frozen Empirical Control (Foundation: V3 + Market Timing + Terminal Liq + Phase Shutdown)
2. Phase 015 Treatment (Foundation + Asset-Holding Trigger + Autonomous Tranche Synthesizer)

Evaluates:
- Trigger Coverage (Did AssetHoldingValuationTrigger detect the state?)
- Candidate Coverage (Did AutonomousTrancheOrderSynthesizer synthesize valid action?)
- Exact-Sim Coverage (Did candidate reach CounterfactualSimulator?)
- Commit Coverage (Did candidate pass WinModel and SafetyChecker?)
- Attribution across Phase 014 Gap Categories (Market Timing, Terminal, Opponent, Multi-Worker, Worker Detour).
"""

from __future__ import annotations

import copy
import csv
import json
import os
import sys
import tarfile
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import kagsim
from aec.config import (
    AECConfig,
    build_phase015_treatment_config,
    build_robust_qualified_config,
)
from aec.counterfactual.simulator import CounterfactualSimulator
from aec.evaluation.win_model import WinModel
from aec.events.detectors import detect_events
from aec.integration.executor import AECExecutor
from aec.ir.economic_state import build_economic_state
from aec.opportunities import OpportunityEngine
from aec.patches.generator import PatchGenerator
from aec.safety.checks import SafetyChecker

V3_TARBALL_PATH = os.path.join(REPO_ROOT, "submission_Vj_kc_v3.tar.gz")
GAP_MATRIX_PATH = os.path.join(REPO_ROOT, "results", "PHASE014_CANDIDATE_GAP_MATRIX.csv")
OUTPUT_CSV_PATH = os.path.join(REPO_ROOT, "results", "PHASE015_ORACLE_REPLAY_EVALUATION.csv")
OUTPUT_SUMMARY_PATH = os.path.join(REPO_ROOT, "results", "PHASE015_ORACLE_REPLAY_SUMMARY.json")


def load_v3_agent() -> Any:
    with tarfile.open(V3_TARBALL_PATH, "r:gz") as tar:
        member = tar.extractfile("main.py")
        if member is None:
            raise RuntimeError("main.py not found in V3 tarball")
        v3_code = member.read().decode("utf-8")
    ns: Dict[str, Any] = {}
    exec(compile(v3_code, "frozen_v3_main.py", "exec"), ns)
    return ns["agent"]


def classify_gap_category(oracle_opp: str) -> str:
    opp_upper = (oracle_opp or "").upper()
    if opp_upper.startswith("MARKET"):
        return "Market Timing"
    elif opp_upper.startswith("TERMINAL"):
        return "Terminal"
    elif opp_upper.startswith("OPPONENT"):
        return "Opponent"
    elif opp_upper.startswith("MULTI_WORKER"):
        return "Multi-worker"
    elif opp_upper.startswith("WORKER"):
        return "Worker Detour"
    return "Other"


def run_oracle_replay(
    seeds: Optional[List[int]] = None,
    max_states_per_category: int = 250,
) -> Dict[str, Any]:
    print(f"\n{'='*75}")
    print("STARTING PHASE 015 ORACLE REPLAY VALIDATION (STAGE B)")
    print(f"{'='*75}\n", flush=True)

    if not os.path.exists(GAP_MATRIX_PATH):
        raise FileNotFoundError(f"Gap matrix not found at {GAP_MATRIX_PATH}")

    df_gap = pd.read_csv(GAP_MATRIX_PATH)
    if seeds is None:
        # Use first 10 seeds present in the gap matrix
        avail_seeds = sorted(df_gap["seed"].unique())
        seeds = avail_seeds[:10]
    
    df_filtered = df_gap[df_gap["seed"].isin(seeds)].copy()
    df_filtered["gap_category"] = df_filtered["oracle_opportunity"].apply(classify_gap_category)

    print(f"Target seeds: {seeds} (N={len(seeds)} seeds)")
    print(f"Total diagnosed gap records in selected seeds: {len(df_filtered)}")
    print("Breakdown by category:")
    for cat, cnt in df_filtered["gap_category"].value_counts().items():
        print(f"  - {cat:15s}: {cnt:5d} states")
    print(flush=True)

    # Sample balanced set of states
    sampled_records: List[Dict[str, Any]] = []
    for cat in ["Market Timing", "Terminal", "Opponent", "Multi-worker", "Worker Detour"]:
        cat_df = df_filtered[df_filtered["gap_category"] == cat]
        if len(cat_df) > max_states_per_category:
            cat_df = cat_df.sample(n=max_states_per_category, random_state=42)
        sampled_records.extend(cat_df.to_dict("records"))

    # Group target turns by (seed, seat)
    targets_by_match = defaultdict(lambda: defaultdict(list))
    for r in sampled_records:
        seed = int(r["seed"])
        seat = int(r["seat"])
        step = int(r["step"])
        targets_by_match[(seed, seat)][step].append(r)

    print(f"Total sampled states for exact replay: {len(sampled_records)} across {len(targets_by_match)} matches.\n", flush=True)

    v3_agent = load_v3_agent()
    trt_cfg = build_phase015_treatment_config()
    opp_engine = OpportunityEngine(config=trt_cfg)
    patch_gen = PatchGenerator(config=trt_cfg)
    sim = CounterfactualSimulator()
    win_model = WinModel()
    safety = SafetyChecker()

    evaluation_rows: List[Dict[str, Any]] = []
    t_start = time.time()

    # Category counters: {category: {"total": 0, "trigger": 0, "candidate": 0, "exact_sim": 0, "commit": 0}}
    cat_stats = defaultdict(lambda: {"total": 0, "trigger": 0, "candidate": 0, "exact_sim": 0, "commit": 0})

    match_idx = 0
    total_matches = len(targets_by_match)

    for (seed, seat), step_dict in targets_by_match.items():
        match_idx += 1
        t_m0 = time.time()
        game = kagsim.Game(seed)
        step = 0

        # Reset opportunity deduplication for each match
        if hasattr(opp_engine, "asset_holding_analyzer"):
            opp_engine.asset_holding_analyzer.trigger.reset_step_cache()

        while not game.done:
            o0 = game.observe(0)
            o1 = game.observe(1)

            # Standard V3 backbone actions
            a0 = v3_agent(o0)
            a1 = v3_agent(o1)

            obs_target = o0 if seat == 0 else o1
            base_act_target = a0 if seat == 0 else a1

            if step in step_dict:
                records = step_dict[step]
                econ = build_economic_state(obs_target)
                evs = detect_events(econ, config=trt_cfg)
                opps = opp_engine.detect_opportunities(econ, evs, baseline_action=base_act_target, config=trt_cfg)

                # Filter for Asset-Holding Valuation Trigger opportunities
                asset_opps = [
                    o for o in opps
                    if o.candidate_transformation_family == "AUTONOMOUS_TRANCHE_ORDER_SYNTHESIZER"
                ]

                has_trigger = len(asset_opps) > 0
                patches: List[Any] = []
                if has_trigger:
                    patches = patch_gen.generate_patches(asset_opps, econ, baseline_action=base_act_target, config=trt_cfg)

                has_candidate = len(patches) > 0
                exact_sim_run = False
                passed_safety = False
                is_superior = False
                sim_delta = 0.0
                committed = False
                why_v3 = ""

                if has_candidate:
                    best_patch = patches[0]
                    why_v3 = getattr(best_patch, "dependency_info", {}).get("why_v3_did_not_do_this", "")
                    # Evaluate under forward counterfactual simulation
                    outcome = sim.evaluate(best_patch, base_act_target, econ, horizon=6)
                    exact_sim_run = True
                    sim_delta = outcome.delta_terminal_margin

                    eval_res = win_model.evaluate(best_patch, outcome, econ, baseline_action=base_act_target)
                    is_superior = eval_res.is_superior
                    passed_safety, _, _ = safety.verify(best_patch, outcome, econ, base_act_target)

                    committed = bool(is_superior and passed_safety)

                    # Update deduplicator feedback
                    fp_str = getattr(best_patch, "dependency_info", {}).get("structural_fingerprint")
                    if fp_str and hasattr(opp_engine, "asset_holding_analyzer"):
                        opp_engine.asset_holding_analyzer.trigger.record_counterfactual_outcome(
                            fp_str, was_accepted=committed
                        )

                for rec in records:
                    cat = rec["gap_category"]
                    cat_stats[cat]["total"] += 1
                    if has_trigger:
                        cat_stats[cat]["trigger"] += 1
                    if has_candidate:
                        cat_stats[cat]["candidate"] += 1
                    if exact_sim_run:
                        cat_stats[cat]["exact_sim"] += 1
                    if committed:
                        cat_stats[cat]["commit"] += 1

                    eval_row = {
                        "seed": seed,
                        "seat": seat,
                        "step": step,
                        "gap_category": cat,
                        "oracle_opportunity": rec["oracle_opportunity"],
                        "oracle_delta": rec.get("oracle_delta", 0.0),
                        "p14_layer": rec.get("layer", "NOT_DETECTED"),
                        "p14_detected": rec.get("detected", False),
                        "p14_represented": rec.get("represented", False),
                        "phase015_triggered": has_trigger,
                        "phase015_candidate_synthesized": has_candidate,
                        "phase015_exact_sim": exact_sim_run,
                        "phase015_sim_delta": round(sim_delta, 2),
                        "phase015_superior": is_superior,
                        "phase015_safe": passed_safety,
                        "phase015_committed": committed,
                        "why_v3_did_not_do_this": why_v3,
                    }
                    evaluation_rows.append(eval_row)

            game.step(a0, a1)
            step += 1

        print(f"  [{match_idx:02d}/{total_matches:02d}] Seed {seed} Seat {seat}: Replayed in {time.time()-t_m0:.2f}s", flush=True)

    total_time = time.time() - t_start

    # Save detailed evaluation CSV
    os.makedirs(os.path.dirname(OUTPUT_CSV_PATH), exist_ok=True)
    keys = list(evaluation_rows[0].keys()) if evaluation_rows else []
    with open(OUTPUT_CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(evaluation_rows)

    # Compute attribution summary table
    summary_table = []
    print(f"\n{'='*95}")
    print("PHASE 015 ORACLE REPLAY ATTRIBUTION SUMMARY")
    print(f"{'='*95}")
    header_fmt = "| {:15s} | {:16s} | {:18s} | {:18s} | {:15s} |"
    row_fmt = "| {:15s} | {:15.1f}% | {:17.1f}% | {:17.1f}% | {:14.1f}% |"
    print(header_fmt.format("Phase014 Gap", "Trigger Coverage", "Candidate Coverage", "Exact-Sim Coverage", "Commit Coverage"))
    print(f"|{'-'*17}|{'-'*18}|{'-'*20}|{'-'*20}|{'-'*17}|")

    summary_dict = {}
    for cat in ["Market Timing", "Terminal", "Opponent", "Multi-worker", "Worker Detour"]:
        st = cat_stats[cat]
        tot = max(1, st["total"])
        trig_cov = (st["trigger"] / tot) * 100.0
        cand_cov = (st["candidate"] / tot) * 100.0
        sim_cov = (st["exact_sim"] / tot) * 100.0
        com_cov = (st["commit"] / tot) * 100.0

        print(row_fmt.format(cat, trig_cov, cand_cov, sim_cov, com_cov))
        summary_dict[cat] = {
            "total_states": st["total"],
            "trigger_coverage_pct": round(trig_cov, 2),
            "candidate_coverage_pct": round(cand_cov, 2),
            "exact_sim_coverage_pct": round(sim_cov, 2),
            "commit_coverage_pct": round(com_cov, 2),
        }

    print(f"{'='*95}\n", flush=True)

    with open(OUTPUT_SUMMARY_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "total_replayed_states": len(evaluation_rows),
            "seeds": [int(s) for s in seeds],
            "elapsed_seconds": round(total_time, 2),
            "attribution": summary_dict,
        }, f, indent=2)

    return summary_dict


if __name__ == "__main__":
    run_oracle_replay()
