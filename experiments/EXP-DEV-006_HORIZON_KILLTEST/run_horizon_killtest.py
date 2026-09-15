# SPDX-License-Identifier: MIT
"""
=============================================================================
EXP-DEV-006 RETROSPECTIVE HORIZON-GATE KILL-TEST RUNNER (ONE-FACTOR REVISION)
=============================================================================
Experiment: EXP-DEV-006_HORIZON_KILLTEST
Title: Retrospective Horizon-Gate Mechanism Kill-Test over DEV-005 Discovery Cohort
Partition: Seeds 247000 to 247049 (Consumed DEV-005 Discovery Partition ONLY)
Mandate: Diagnostic Mechanism Evaluation (Do NOT Qualify DEV-005 Yet)

Revision note: this runner supersedes the draft run_horizon_killtest.py logged at
2026-09-14 16:33 UTC. The draft compared a live DEV-006 arm against HISTORICAL
DEV-005 numbers and used a treatment file (sha 13d328f9...) that rewrote the
valuation model -- violating one-factor isolation. This revision:
  1. Uses the TRUE one-factor treatment (exact DEV-005 copy + horizon guard).
  2. Runs BOTH arms live (DEV-005 replay vs baseline, DEV-006 vs baseline)
     under identical CRN, 4 games per seed.
  3. Asserts bit-for-bit DEV-005 replay parity with frozen RAW_RESULTS.json
     (engine determinism / cross-platform validation gate).
  4. Asserts one-factor purity: diffs permitted ONLY where REJECT_HORIZON fired.
=============================================================================
"""

import os
import sys
import csv
import json
import math
import time
import hashlib
import importlib.util
from typing import Dict, List, Tuple, Any

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))

import kagsim
from dev_005_confirmed_shop_scheduler import Dev005ConfirmedShopScheduler
from dev_006_horizon_guard_scheduler import Dev006HorizonGuardScheduler

EXP_DIR = os.path.abspath(os.path.dirname(__file__))
LOG_FILE = os.path.join(EXP_DIR, "EXECUTION_LOG.txt")
RAW_RESULTS_FILE = os.path.join(EXP_DIR, "RAW_RESULTS.json")
PAIRED_DELTAS_FILE = os.path.join(EXP_DIR, "PAIRED_DELTAS.csv")
LATE_SPEC_FILE = os.path.join(EXP_DIR, "LATE_SPECIALIZATION_TABLE.csv")
POS_CONTROL_FILE = os.path.join(EXP_DIR, "POSITIVE_CONTROL_RESULTS.csv")
STATS_FILE = os.path.join(EXP_DIR, "STATISTICS_RECOMPUTED.json")

BASELINE_PATH = os.path.join(BASE_DIR, "candidates", "compiled_v54_plus_residual.py")
DEV005_PATH = os.path.join(BASE_DIR, "candidates", "closed_loop_architecture", "dev_005_confirmed_shop_scheduler.py")
DEV006_PATH = os.path.join(BASE_DIR, "candidates", "closed_loop_architecture", "dev_006_horizon_guard_scheduler.py")
DEV005_RAW_RESULTS = os.path.join(BASE_DIR, "experiments", "EXP-DEV-005", "RAW_RESULTS.json")
DEV005_DECISIONS = os.path.join(BASE_DIR, "experiments", "EXP-DEV-005", "DECISION_EVENTS.csv")

EXPECTED_BASE_SHA = "18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb"
EXPECTED_DEV005_SHA = "f52b168619e47bea6a052faff890fc84804cb39b47392d247139967f910e2a78"
EXPECTED_PROTO_SHA = "ac69fc602083f232792ad5bdabd699e4b9f96e73462f9edc740ccd63c727e9f6"
EXPECTED_SHOP_SHA = "f651ccd220e701968bc33579812d8917da63f5b0582f2fd0d363fa6a16ffd8b8"

# True one-factor treatment hash (exact DEV-005 copy + REJECT_HORIZON guard).
# Supersedes flawed draft 13d328f9b6363aceeac9b5b2b9026355b1e3ffcd0d3854d7f44791067cb67091.
EXPECTED_DEV006_SHA = "06db94e59e2c271b5490aad78fdb760bd8a250f28ec4407de2d2f6be0644f5eb"

COHORT_LO = 247000
COHORT_HI = 247049


def log(msg: str):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    line = f"[{timestamp} UTC] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def assert_not_quarantined(seed: int):
    """Hard invariant: virgin holdout / qualification / contaminated / consumed
    partitions must NEVER be executed. Only 247000-247049 is permitted."""
    if 214200 <= seed <= 214249:
        raise RuntimeError(f"CRITICAL PROTOCOL VIOLATION: Virgin Holdout seed {seed} requested!")
    if 50050 <= seed <= 50099:
        raise RuntimeError(f"CRITICAL PROTOCOL VIOLATION: Qualification seed {seed} requested!")
    if 50100 <= seed <= 50149:
        raise RuntimeError(f"CRITICAL PROTOCOL VIOLATION: Contaminated seed {seed} requested!")
    if 245000 <= seed <= 245049:
        raise RuntimeError(f"CRITICAL PROTOCOL VIOLATION: DEV-003 consumed seed {seed} requested!")
    if 246000 <= seed <= 246049:
        raise RuntimeError(f"CRITICAL PROTOCOL VIOLATION: DEV-004 consumed seed {seed} requested!")
    if not (COHORT_LO <= seed <= COHORT_HI):
        raise RuntimeError(f"CRITICAL PROTOCOL VIOLATION: Seed {seed} outside cohort 247000-247049!")


def sha256_of(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def audit_agent_ast_standalone(filepath: str) -> List[str]:
    """Self-contained replica of scratch/verify_agent_zero_leakage.audit_agent_ast
    (module-level kagsim import in that file would couple the static audit to the
    simulator; the check itself is pure AST)."""
    import ast
    real_path = os.path.realpath(filepath)
    with open(real_path, "r", encoding="utf-8", errors="ignore") as f:
        source = f.read()
    tree = ast.parse(source, filename=real_path)
    prohibited_modules = {"ctypes", "inspect", "socket", "urllib", "requests", "subprocess"}
    prohibited_names = {"__subclasses__", "_sim", "_rng", "kagsim_internal"}
    violations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in prohibited_modules:
                    violations.append(f"Prohibited import '{alias.name}' line {node.lineno}")
        elif isinstance(node, ast.ImportFrom):
            if node.module in prohibited_modules:
                violations.append(f"Prohibited from-import '{node.module}' line {node.lineno}")
        elif isinstance(node, ast.Name):
            if node.id in prohibited_names:
                violations.append(f"Prohibited symbol '{node.id}' line {node.lineno}")
    return violations


def verify_governance():
    log("=" * 80)
    log("PHASE 0: GOVERNANCE & IMMUTABILITY VERIFICATION (ONE-FACTOR REVISION)")
    log("=" * 80)

    base_sha = sha256_of(BASELINE_PATH)
    assert base_sha == EXPECTED_BASE_SHA, f"Baseline SHA mismatch: {base_sha}"
    log(f"  [1/7] Baseline (V54++ Residual / Sub 56146971) verified: {base_sha}")

    dev005_sha = sha256_of(DEV005_PATH)
    assert dev005_sha == EXPECTED_DEV005_SHA, f"DEV-005 SHA mismatch: {dev005_sha}"
    log(f"  [2/7] Historical DEV-005 treatment verified: {dev005_sha}")

    proto_dev005 = os.path.join(BASE_DIR, "experiments", "EXP-DEV-005", "DEVELOPMENT_EXPERIMENT_PROTOCOL_V1_4.md")
    proto_sha = sha256_of(proto_dev005)
    assert proto_sha == EXPECTED_PROTO_SHA, f"DEV-005 protocol SHA mismatch: {proto_sha}"
    log(f"  [3/7] Historical DEV-005 protocol verified: {proto_sha}")

    dev006_sha = sha256_of(DEV006_PATH)
    assert dev006_sha == EXPECTED_DEV006_SHA, f"DEV-006 SHA mismatch: {dev006_sha}"
    log(f"  [4/7] One-factor DEV-006 treatment verified: {dev006_sha}")

    ast_violations = audit_agent_ast_standalone(DEV006_PATH)
    assert len(ast_violations) == 0, f"DEV-006 AST violations: {ast_violations}"
    log("  [5/7] DEV-006 AST zero-leakage audit: clean (0 violations)")

    shop_base_path = os.path.join(BASE_DIR, "candidates", "compiled_v54_plus_shop.py")
    shop_sha = sha256_of(shop_base_path)
    assert shop_sha == EXPECTED_SHOP_SHA, f"Shop baseline SHA mismatch: {shop_sha}"
    log("  [6/7] Frozen fallback (56146971) & control (56146947) verified bit-for-bit")

    assert hasattr(kagsim, "Game"), "kagsim simulator missing Game class"
    try:
        g = kagsim.Game(247000)
        o = g.observe(0)
        assert isinstance(o, dict) and "farms" in o
    except Exception as e:
        raise RuntimeError(f"Simulator smoke test failed: {e}")
    log("  [7/7] Simulator engine kagsim verified (Game construct + observe smoke test)")
    log("All Phase 0 governance invariants passed.\n")


def load_isolated_baseline(name: str):
    spec = importlib.util.spec_from_file_location(name, BASELINE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def play_match(seed: int, cand_cls, cand_seat: int) -> Tuple[float, float, Any]:
    """Play one match: candidate on cand_seat, baseline on the other. Returns
    (cand_score, base_score, candidate_instance)."""
    g = kagsim.Game(seed)
    cand = cand_cls(seat=cand_seat, seed=seed)
    base = load_isolated_baseline(f"base_{cand_cls.__name__}_s{seed}_c{cand_seat}")
    if cand_seat == 0:
        while not g.done:
            o0 = g.observe(0)
            o1 = g.observe(1)
            g.step(cand.act(o0), base.agent(o1))
        c_score = float(g.reward(0))
        b_score = float(g.reward(1))
    else:
        while not g.done:
            o0 = g.observe(0)
            o1 = g.observe(1)
            g.step(base.agent(o0), cand.act(o1))
        b_score = float(g.reward(0))
        c_score = float(g.reward(1))
    return c_score, b_score, cand


def first_spec_step(decision_events) -> Any:
    for ev in decision_events:
        if ev["decision"] == "SPECIALIZE_CONFIRMED":
            return ev["step"]
    return None


def run_experiment():
    verify_governance()

    log("=" * 80)
    log("RUNNING EXP-DEV-006 HORIZON-GATE KILL-TEST (50 SEEDS: 247000-247049)")
    log("Both arms live: DEV-005 replay + DEV-006 guard, identical CRN")
    log("=" * 80)

    with open(DEV005_RAW_RESULTS, "r", encoding="utf-8") as f:
        frozen005 = {item["seed"]: item for item in json.load(f)}

    # Frozen DEV-005 first-spec steps (match 0) for positive-control table.
    frozen_first_spec: Dict[int, Any] = {}
    with open(DEV005_DECISIONS, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["match"] != "0":
                continue
            seed = int(row["seed"])
            if seed not in frozen_first_spec:
                frozen_first_spec[seed] = None
            if row["decision"] == "SPECIALIZE_CONFIRMED" and frozen_first_spec[seed] is None:
                frozen_first_spec[seed] = int(row["step"])

    raw_results = []
    paired_rows = []
    late_spec_rows = []
    pos_control_rows = []

    dev006_deltas, dev005_deltas, diff_deltas = [], [], []
    replay_mismatches = []
    purity_violations = []

    t_start = time.time()
    for seed in range(COHORT_LO, COHORT_HI + 1):
        assert_not_quarantined(seed)
        t0 = time.perf_counter()

        # Arm A: original DEV-005 replay vs baseline (CRN-identical to frozen run).
        # play_match always returns (cand_score, base_score, cand_instance).
        c0_5, b1_5, cand0_5 = play_match(seed, Dev005ConfirmedShopScheduler, 0)
        c1_5, b0_5, cand1_5 = play_match(seed, Dev005ConfirmedShopScheduler, 1)
        d0_5 = c0_5 - b1_5
        d1_5 = c1_5 - b0_5
        paired_5 = 0.5 * (d0_5 + d1_5)

        # Arm B: DEV-005 + Horizon Guard vs baseline (identical CRN).
        c0_6, b1_6, cand0_6 = play_match(seed, Dev006HorizonGuardScheduler, 0)
        c1_6, b0_6, cand1_6 = play_match(seed, Dev006HorizonGuardScheduler, 1)
        d0_6 = c0_6 - b1_6
        d1_6 = c1_6 - b0_6
        paired_6 = 0.5 * (d0_6 + d1_6)

        elapsed = time.perf_counter() - t0

        # Replay-parity gate: live DEV-005 must match frozen DEV-005 bit-for-bit.
        fz = frozen005[seed]
        if not (paired_5 == fz["paired_mean_delta"] and d0_5 == fz["match0_delta"] and d1_5 == fz["match1_delta"]):
            replay_mismatches.append({
                "seed": seed,
                "frozen": [fz["match0_delta"], fz["match1_delta"], fz["paired_mean_delta"]],
                "replay": [d0_5, d1_5, paired_5],
            })

        # PRIMARY COMPARISON: guard candidate MINUS original DEV-005 candidate.
        diff = paired_6 - paired_5
        dev006_deltas.append(paired_6)
        dev005_deltas.append(paired_5)
        diff_deltas.append(diff)

        ev6_m0 = {ev["step"]: ev for ev in cand0_6.decision_events}
        horizon_fired = any(ev["decision"] == "REJECT_HORIZON"
                            for ev in cand0_6.decision_events + cand1_6.decision_events)
        activated_6 = any(ev["decision"] == "SPECIALIZE_CONFIRMED"
                          for ev in cand0_6.decision_events + cand1_6.decision_events)

        # One-factor purity gate: any nonzero diff REQUIRES a REJECT_HORIZON event,
        # and REJECT_HORIZON may only fire at step 288 (remaining 432 < 500).
        if diff != 0.0 and not horizon_fired:
            purity_violations.append({"seed": seed, "diff": diff, "reason": "DIFF_WITHOUT_GUARD_EVENT"})
        for ev in cand0_6.decision_events + cand1_6.decision_events:
            if ev["decision"] == "REJECT_HORIZON" and ev["step"] != 288:
                purity_violations.append({"seed": seed, "step": ev["step"], "reason": "GUARD_FIRED_OFF_288"})

        outcome_6 = "WIN" if paired_6 > 0 else ("LOSS" if paired_6 < 0 else "TIE")
        outcome_5 = "WIN" if paired_5 > 0 else ("LOSS" if paired_5 < 0 else "TIE")

        raw_results.append({
            "seed": seed,
            "dev005_replay": {"match0_cand": c0_5, "match0_base": b1_5, "match0_delta": d0_5,
                              "match1_base": b0_5, "match1_cand": c1_5, "match1_delta": d1_5,
                              "paired_mean": paired_5},
            "dev006_guard": {"match0_cand": c0_6, "match0_base": b1_6, "match0_delta": d0_6,
                             "match1_base": b0_6, "match1_cand": c1_6, "match1_delta": d1_6,
                             "paired_mean": paired_6},
            "frozen_dev005_paired_mean": fz["paired_mean_delta"],
            "replay_matches_frozen": bool(paired_5 == fz["paired_mean_delta"]),
            "diff_dev006_minus_dev005": diff,
            "outcome_dev005_replay": outcome_5,
            "outcome_dev006": outcome_6,
            "outcome_dev005_frozen": fz["outcome"],
            "activated_dev006": activated_6,
            "horizon_rejected": horizon_fired,
            "dev006_first_spec_step_m0": first_spec_step(cand0_6.decision_events),
            "dev006_decision_steps_m0": {str(k): {"decision": v["decision"],
                                                  "best_plan": v["best_candidate_plan"],
                                                  "exp_val": v["expected_incremental_value"],
                                                  "remaining": v.get("remaining_horizon"),
                                                  "shops": v["current_shops"]}
                                         for k, v in ev6_m0.items()},
            "runtime_sec": round(elapsed, 3),
        })

        paired_rows.append({
            "seed": seed,
            "dev005_match0_delta": d0_5,
            "dev005_match1_delta": d1_5,
            "dev005_paired_mean": paired_5,
            "dev006_match0_delta": d0_6,
            "dev006_match1_delta": d1_6,
            "dev006_paired_mean": paired_6,
            "frozen_dev005_paired_mean": fz["paired_mean_delta"],
            "diff_dev006_minus_dev005": diff,
            "outcome_dev005": outcome_5,
            "outcome_dev006": outcome_6,
            "horizon_rejected": horizon_fired,
        })

        ev288 = ev6_m0.get(288)
        if ev288 is not None and (ev288["decision"] == "REJECT_HORIZON"
                                  or ev288["decision"] == "SPECIALIZE_CONFIRMED"):
            late_spec_rows.append({
                "seed": seed,
                "step": 288,
                "shops_at_288": ev288["current_shops"],
                "best_plan": ev288["best_candidate_plan"],
                "exp_val": ev288["expected_incremental_value"],
                "remaining_horizon": ev288.get("remaining_horizon"),
                "dev005_delta": paired_5,
                "dev006_delta": paired_6,
                "diff_recovered": diff,
                "decision_dev006": ev288["decision"],
                "frozen_first_spec_step_dev005": frozen_first_spec.get(seed),
            })

        if paired_5 >= 2000.0:
            pos_control_rows.append({
                "seed": seed,
                "frozen_first_spec_step_dev005": frozen_first_spec.get(seed),
                "dev006_first_spec_step_m0": first_spec_step(cand0_6.decision_events),
                "dev005_delta": paired_5,
                "dev006_delta": paired_6,
                "diff": diff,
                "upside_preserved": bool(paired_6 >= paired_5 - 1e-9),
            })

        log(f"Seed {seed}: DEV-006 ${paired_6:+9.1f} | DEV-005 replay ${paired_5:+9.1f} "
            f"(frozen ${fz['paired_mean_delta']:+9.1f}) | Diff ${diff:+9.1f} | "
            f"{outcome_6} (was {outcome_5}) | guard={'FIRED' if horizon_fired else '-'}")

    total_time = time.time() - t_start
    log(f"\nAll 50 seeds complete in {total_time:.2f}s "
        f"({total_time / 50:.2f}s/seed, 4 games each).")

    with open(RAW_RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(raw_results, f, indent=2)
    with open(PAIRED_DELTAS_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(paired_rows[0].keys()))
        w.writeheader()
        w.writerows(paired_rows)
    with open(LATE_SPEC_FILE, "w", newline="", encoding="utf-8") as f:
        if late_spec_rows:
            w = csv.DictWriter(f, fieldnames=list(late_spec_rows[0].keys()))
            w.writeheader()
            w.writerows(late_spec_rows)
    with open(POS_CONTROL_FILE, "w", newline="", encoding="utf-8") as f:
        if pos_control_rows:
            w = csv.DictWriter(f, fieldnames=list(pos_control_rows[0].keys()))
            w.writeheader()
            w.writerows(pos_control_rows)

    n = len(dev006_deltas)
    mean_6 = sum(dev006_deltas) / n
    mean_5 = sum(dev005_deltas) / n
    mean_diff = sum(diff_deltas) / n
    var_6 = sum((x - mean_6) ** 2 for x in dev006_deltas) / (n - 1)
    sd_6 = math.sqrt(var_6)
    se_6 = sd_6 / math.sqrt(n)
    var_d = sum((x - mean_diff) ** 2 for x in diff_deltas) / (n - 1) if n > 1 else 0.0
    sd_d = math.sqrt(var_d) if var_d > 0 else 0.0
    se_d = sd_d / math.sqrt(n) if n else 0.0

    loss_fix, new_losses, sac_wins, other = [], [], [], []
    for seed, d6, d5, dd in zip(range(COHORT_LO, COHORT_HI + 1), dev006_deltas, dev005_deltas, diff_deltas):
        entry = {"seed": seed, "dev005": d5, "dev006": d6, "diff": dd}
        if seed in (247025, 247034):
            loss_fix.append(entry)
        elif dd < 0:
            if d5 > 0 and d6 <= 0:
                sac_wins.append(entry)
            elif d6 < 0 and d5 >= 0:
                new_losses.append(entry)
            else:
                other.append(entry)
        elif dd > 0:
            other.append(entry)

    stats = {
        "n_seeds": n,
        "n_games_per_seed": 4,
        "mean_dev005_replay": round(mean_5, 2),
        "mean_dev006": round(mean_6, 2),
        "mean_difference_dev006_minus_dev005": round(mean_diff, 2),
        "total_recovery": round(sum(diff_deltas), 2),
        "sd_dev006": round(sd_6, 4),
        "se_dev006": round(se_6, 4),
        "sd_diff": round(sd_d, 4),
        "se_diff": round(se_d, 4),
        "wins_dev006": sum(1 for d in dev006_deltas if d > 0),
        "losses_dev006": sum(1 for d in dev006_deltas if d < 0),
        "ties_dev006": sum(1 for d in dev006_deltas if d == 0),
        "residual_loss_recovery": loss_fix,
        "losses_introduced": new_losses,
        "wins_sacrificed": sac_wins,
        "other_seed_changes": other,
        "replay_mismatches_vs_frozen": replay_mismatches,
        "replay_parity_ok": len(replay_mismatches) == 0,
        "one_factor_purity_violations": purity_violations,
        "one_factor_purity_ok": len(purity_violations) == 0,
        "total_runtime_sec": round(total_time, 2),
    }
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    log("\n" + "=" * 80)
    log("SUMMARY RESULTS (DEV-006 guard MINUS DEV-005 original, identical CRN)")
    log("=" * 80)
    log(f"DEV-005 replay mean:   ${mean_5:+.2f}")
    log(f"DEV-006 guard mean:    ${mean_6:+.2f}")
    log(f"Mean paired diff:      ${mean_diff:+.2f}")
    log(f"Total cohort recovery: ${sum(diff_deltas):+.2f}")
    log(f"DEV-006 W/L/T: {stats['wins_dev006']}/{stats['losses_dev006']}/{stats['ties_dev006']}")
    for e in loss_fix:
        log(f"  Seed {e['seed']}: DEV-005 ${e['dev005']:.1f} -> DEV-006 ${e['dev006']:.1f} (diff ${e['diff']:+.1f})")
    log(f"Losses introduced: {len(new_losses)} | Wins sacrificed: {len(sac_wins)} | Other: {len(other)}")
    log(f"Replay parity vs frozen: {'OK (50/50 bit-identical)' if not replay_mismatches else f'FAILED {replay_mismatches}'}")
    log(f"One-factor purity: {'OK' if not purity_violations else f'FAILED {purity_violations}'}")
    if replay_mismatches or purity_violations:
        raise SystemExit("GATE FAILURE: replay or purity invariant violated -- see log.")


if __name__ == "__main__":
    run_experiment()
