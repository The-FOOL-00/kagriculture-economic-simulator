# SPDX-License-Identifier: MIT
"""
=============================================================================
EXP-DEV-006 QUALIFICATION RUNNER: RESERVED QUALIFICATION PARTITION
=============================================================================
Experiment: EXP-DEV-006 Qualification (confirmatory replication)
Governing Protocol: QUALIFICATION_PROTOCOL.md (frozen pre-registration)
Protocol Hash (SHA-256): 1484e0059f6196f82fe3db27fc07cf33b50cd99fadef298f156e642bb4466dc4
Qualification Partition: Seeds 50050 to 50099 (N=50, 200 CRN matches)
Engine: kagsim_py validated port (ENGINE_VERSION 1.32.7) per Qualification Protocol
Treatment: frozen DEV-006 (06db94e5...), byte-identical to Discovery. NO TUNING.
Quarantined: 214200-214249, 248000-248049, 245000-245049, 246000-246049,
             247000-247049, 50000-50049, 50100-50149 (hard abort on any request)
Discovery record (parent dir) is NEVER written by this runner.
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

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
PORT_DIR = os.path.join(BASE_DIR, "experiments", "EXP-DEV-006_HORIZON_KILLTEST", "port")
sys.path.insert(0, PORT_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))

import kagsim_py as kagsim
from dev_005_confirmed_shop_scheduler import Dev005ConfirmedShopScheduler
from dev_006_horizon_guard_scheduler import Dev006HorizonGuardScheduler

EXP_DIR = os.path.abspath(os.path.dirname(__file__))
LOG_FILE = os.path.join(EXP_DIR, "QUALIFICATION_EXECUTION_LOG.txt")
RAW_RESULTS_FILE = os.path.join(EXP_DIR, "QUALIFICATION_RAW_RESULTS.json")
PAIRED_DELTAS_FILE = os.path.join(EXP_DIR, "QUALIFICATION_PAIRED_DELTAS.csv")
DECISION_EVENTS_FILE = os.path.join(EXP_DIR, "QUALIFICATION_DECISION_EVENTS.csv")
SPECIALIZATION_EVENTS_FILE = os.path.join(EXP_DIR, "QUALIFICATION_SPECIALIZATION_EVENTS.csv")
HORIZON_GUARD_EVENTS_FILE = os.path.join(EXP_DIR, "QUALIFICATION_HORIZON_GUARD_EVENTS.csv")
STATS_FILE = os.path.join(EXP_DIR, "QUALIFICATION_STATISTICS_RECOMPUTED.json")

BASELINE_PATH = os.path.join(BASE_DIR, "candidates", "compiled_v54_plus_residual.py")
DEV005_PATH = os.path.join(BASE_DIR, "candidates", "closed_loop_architecture", "dev_005_confirmed_shop_scheduler.py")
DEV006_PATH = os.path.join(BASE_DIR, "candidates", "closed_loop_architecture", "dev_006_horizon_guard_scheduler.py")

EXPECTED_PROTO_SHA = "1484e0059f6196f82fe3db27fc07cf33b50cd99fadef298f156e642bb4466dc4"
EXPECTED_BASE_SHA = "18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb"
EXPECTED_DEV005_SHA = "f52b168619e47bea6a052faff890fc84804cb39b47392d247139967f910e2a78"
EXPECTED_DEV006_SHA = "06db94e59e2c271b5490aad78fdb760bd8a250f28ec4407de2d2f6be0644f5eb"
EXPECTED_SHOP_SHA = "f651ccd220e701968bc33579812d8917da63f5b0582f2fd0d363fa6a16ffd8b8"
EXPECTED_DISCOVERY_PROTO_SHA = "e52a0570a8bc9cfeafe1165f49f4c9d77ef9a3b7aa030783f8aef7e9ee7b04e8"

COHORT_LO = 50050
COHORT_HI = 50099


def log(msg: str):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    line = f"[{timestamp} UTC] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def assert_not_quarantined(seed: int):
    if 214200 <= seed <= 214249:
        raise RuntimeError(f"CRITICAL PROTOCOL VIOLATION: Virgin Holdout seed {seed} requested!")
    if 248000 <= seed <= 248049:
        raise RuntimeError(f"CRITICAL PROTOCOL VIOLATION: Discovery seed {seed} requested during Qualification!")
    if 245000 <= seed <= 245049:
        raise RuntimeError(f"CRITICAL PROTOCOL VIOLATION: DEV-003 consumed seed {seed} requested!")
    if 246000 <= seed <= 246049:
        raise RuntimeError(f"CRITICAL PROTOCOL VIOLATION: DEV-004 consumed seed {seed} requested!")
    if 247000 <= seed <= 247049:
        raise RuntimeError(f"CRITICAL PROTOCOL VIOLATION: DEV-005 consumed seed {seed} requested!")
    if 50000 <= seed <= 50049:
        raise RuntimeError(f"CRITICAL PROTOCOL VIOLATION: DEV-001/002 consumed seed {seed} requested!")
    if 50100 <= seed <= 50149:
        raise RuntimeError(f"CRITICAL PROTOCOL VIOLATION: Contaminated seed {seed} requested!")
    if not (COHORT_LO <= seed <= COHORT_HI):
        raise RuntimeError(f"CRITICAL PROTOCOL VIOLATION: Seed {seed} outside Qualification cohort 50050-50099!")


def sha256_of(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def audit_agent_ast_standalone(filepath: str) -> List[str]:
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
    log("PREFLIGHT GOVERNANCE VERIFICATION FOR EXP-DEV-006 QUALIFICATION RUN")
    log("=" * 80)
    proto_sha = sha256_of(os.path.join(EXP_DIR, "QUALIFICATION_PROTOCOL.md"))
    assert proto_sha == EXPECTED_PROTO_SHA, f"Qualification protocol SHA mismatch: {proto_sha}"
    log(f"  [1/10] Qualification protocol verified: {proto_sha}")
    disc_sha = sha256_of(os.path.join(os.path.dirname(EXP_DIR), "DEVELOPMENT_EXPERIMENT_PROTOCOL_V1_5.md"))
    assert disc_sha == EXPECTED_DISCOVERY_PROTO_SHA, f"Discovery protocol mutated: {disc_sha}"
    log("  [2/10] Discovery protocol V1.5 unmutated (parent record intact)")
    base_sha = sha256_of(BASELINE_PATH)
    assert base_sha == EXPECTED_BASE_SHA, f"Baseline SHA mismatch: {base_sha}"
    log(f"  [3/10] Baseline (V54++ Residual / Sub 56146971) verified: {base_sha}")
    dev006_sha = sha256_of(DEV006_PATH)
    assert dev006_sha == EXPECTED_DEV006_SHA, f"DEV-006 SHA mismatch: {dev006_sha}"
    log(f"  [4/10] Treatment dev_006 verified byte-identical to Discovery: {dev006_sha}")
    dev005_sha = sha256_of(DEV005_PATH)
    assert dev005_sha == EXPECTED_DEV005_SHA, f"DEV-005 SHA mismatch: {dev005_sha}"
    log(f"  [5/10] Diagnostic dev_005 verified: {dev005_sha}")
    shop_sha = sha256_of(os.path.join(BASE_DIR, "candidates", "compiled_v54_plus_shop.py"))
    assert shop_sha == EXPECTED_SHOP_SHA, f"Shop control SHA mismatch: {shop_sha}"
    log("  [6/10] Frozen fallback (56146971) & control (56146947) verified bit-for-bit")
    viol = audit_agent_ast_standalone(DEV006_PATH)
    assert len(viol) == 0, f"DEV-006 AST violations: {viol}"
    log("  [7/10] DEV-006 AST zero-leakage audit: clean (0 violations)")
    assert getattr(kagsim, "ENGINE_VERSION", None) == "1.32.7", "port engine version drift"
    with open(os.path.join(PORT_DIR, "PORT_MANIFEST.json"), "r", encoding="utf-8") as f:
        manifest = json.load(f)
    for rel, exp_sha in manifest["port_files"].items():
        got = sha256_of(os.path.join(PORT_DIR, rel))
        assert got == exp_sha, f"Port file {rel} modified since validation: {got}"
    log(f"  [8/10] Execution engine: kagsim_py port ({kagsim.__version__}), 4/4 files match validated manifest")
    g = kagsim.Game(COHORT_LO)
    o = g.observe(0)
    assert isinstance(o, dict) and "farms" in o
    log("  [9/10] Simulator smoke test passed (Game construct + observe)")
    for doc in ("QUALIFICATION_PROTOCOL.md", "QUALIFICATION_PRECHECK.md", "QUALIFICATION_SEED_PROVENANCE.md"):
        assert os.path.exists(os.path.join(EXP_DIR, doc)), f"Missing {doc}"
    log("  [10/10] Precheck / provenance / protocol documents verified on disk")
    log("All preflight invariants passed.\n")


def load_isolated_baseline(name: str):
    spec = importlib.util.spec_from_file_location(name, BASELINE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def play_match(seed: int, cand_cls, cand_seat: int) -> Tuple[float, float, Any]:
    g = kagsim.Game(seed)
    cand = cand_cls(seat=cand_seat, seed=seed)
    base = load_isolated_baseline(f"base_{cand_cls.__name__}_s{seed}_c{cand_seat}")
    if cand_seat == 0:
        while not g.done:
            o0 = g.observe(0)
            o1 = g.observe(1)
            g.step(cand.act(o0), base.agent(o1))
        return float(g.reward(0)), float(g.reward(1)), cand
    while not g.done:
        o0 = g.observe(0)
        o1 = g.observe(1)
        g.step(base.agent(o0), cand.act(o1))
    return float(g.reward(1)), float(g.reward(0)), cand


def first_spec_step(decision_events) -> Any:
    for ev in decision_events:
        if ev["decision"] == "SPECIALIZE_CONFIRMED":
            return ev["step"]
    return None


def collect_events(cand, seed: int, arm: str, match: int, decisions: List[Dict], specs: List[Dict]):
    for ev in cand.decision_events:
        row = dict(ev)
        row["arm"] = arm
        row["match"] = match
        decisions.append(row)
    for ev in cand.specialization_events:
        row = dict(ev)
        row["arm"] = arm
        row["match"] = match
        specs.append(row)


def pct(sorted_arr, p):
    k = (len(sorted_arr) - 1) * p
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_arr[int(k)]
    return sorted_arr[f] * (c - k) + sorted_arr[c] * (k - f)


def describe(deltas: List[float], label: str) -> Dict[str, Any]:
    n = len(deltas)
    s = sorted(deltas)
    total = sum(deltas)
    mean_val = total / n
    var = sum((x - mean_val) ** 2 for x in deltas) / (n - 1) if n > 1 else 0.0
    sd_val = math.sqrt(var)
    se_val = sd_val / math.sqrt(n) if n else 0.0
    t_stat = mean_val / se_val if se_val > 0 else 0.0
    try:
        from scipy import stats
        p_val = float(stats.t.sf(abs(t_stat), df=n - 1) * 2)
        t_crit = float(stats.t.ppf(0.975, df=n - 1))
    except ImportError:
        p_val = 2.0 * (1.0 - 0.5 * (1.0 + math.erf(abs(t_stat) / math.sqrt(2.0))))
        t_crit = 2.0096
    wins = sum(1 for d in deltas if d > 0.0)
    losses = sum(1 for d in deltas if d < 0.0)
    ties = sum(1 for d in deltas if d == 0.0)
    return {
        "label": label,
        "n_seeds": n,
        "mean": round(mean_val, 2),
        "median": round(pct(s, 0.5), 2),
        "sd": round(sd_val, 4),
        "se": round(se_val, 4),
        "t_stat": round(t_stat, 4),
        "p_value": round(p_val, 6),
        "t_crit_95": round(t_crit, 4),
        "ci_95_lower": round(mean_val - t_crit * se_val, 3),
        "ci_95_upper": round(mean_val + t_crit * se_val, 3),
        "trimmed_mean_10pct": round(sum(s[5:-5]) / (n - 10), 3),
        "p01": round(pct(s, 0.01), 3),
        "p05": round(pct(s, 0.05), 3),
        "p10": round(pct(s, 0.10), 3),
        "p25": round(pct(s, 0.25), 3),
        "p50": round(pct(s, 0.50), 3),
        "p75": round(pct(s, 0.75), 3),
        "p90": round(pct(s, 0.90), 3),
        "p95": round(pct(s, 0.95), 3),
        "p99": round(pct(s, 0.99), 3),
        "min": round(min(deltas), 2),
        "max": round(max(deltas), 2),
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "nonzero_seeds": wins + losses,
        "win_rate": round(wins / n, 4),
        "loss_rate": round(losses / n, 4),
        "tie_rate": round(ties / n, 4),
        "mean_excluding_best": round(sum(s[:-1]) / (n - 1), 4),
        "mean_excluding_worst": round(sum(s[1:]) / (n - 1), 4),
        "mean_excluding_top2": round(sum(s[:-2]) / (n - 2), 4),
        "top1_contribution_pct": round((s[-1] / total * 100.0) if total > 0 else 0.0, 2),
        "top2_contribution_pct": round(((s[-1] + s[-2]) / total * 100.0) if total > 0 else 0.0, 2),
    }


def count_decisions(decisions: List[Dict], arm: str) -> Dict[str, int]:
    rows = [d for d in decisions if d["arm"] == arm]
    return {
        "total_checkpoint_decisions": len(rows),
        "specialize_confirmed": sum(1 for d in rows if d["decision"] == "SPECIALIZE_CONFIRMED"),
        "reject_unconfirmed": sum(1 for d in rows if d["decision"] == "REJECT_UNCONFIRMED"),
        "reject_horizon": sum(1 for d in rows if d["decision"] == "REJECT_HORIZON"),
        "baseline": sum(1 for d in rows if d["decision"] == "BASELINE"),
        "specialize_before_guard_boundary": sum(1 for d in rows
                                               if d["decision"] == "SPECIALIZE_CONFIRMED" and int(d["step"]) < 288),
        "specialize_at_step_288": sum(1 for d in rows
                                      if d["decision"] == "SPECIALIZE_CONFIRMED" and int(d["step"]) == 288),
    }


def run_experiment():
    verify_governance()
    log("=" * 80)
    log(f"RUNNING EXP-DEV-006 QUALIFICATION ({COHORT_LO}-{COHORT_HI}, N=50)")
    log("Primary arm: DEV-006 vs V54++ baseline | Diagnostic arm: DEV-005 vs baseline, identical CRN")
    log("=" * 80)

    raw_results, paired_rows = [], []
    all_decisions, all_specs = [], []
    d6_list, d5_list, contrast_list = [], [], []
    purity_violations = []

    t_start = time.time()
    for idx, seed in enumerate(range(COHORT_LO, COHORT_HI + 1), start=1):
        assert_not_quarantined(seed)
        t0 = time.perf_counter()

        c0_6, b1_6, cand0_6 = play_match(seed, Dev006HorizonGuardScheduler, 0)
        c1_6, b0_6, cand1_6 = play_match(seed, Dev006HorizonGuardScheduler, 1)
        d0_6, d1_6 = c0_6 - b1_6, c1_6 - b0_6
        paired_6 = 0.5 * (d0_6 + d1_6)

        c0_5, b1_5, cand0_5 = play_match(seed, Dev005ConfirmedShopScheduler, 0)
        c1_5, b0_5, cand1_5 = play_match(seed, Dev005ConfirmedShopScheduler, 1)
        d0_5, d1_5 = c0_5 - b1_5, c1_5 - b0_5
        paired_5 = 0.5 * (d0_5 + d1_5)

        contrast = paired_6 - paired_5
        d6_list.append(paired_6)
        d5_list.append(paired_5)
        contrast_list.append(contrast)
        elapsed = time.perf_counter() - t0

        ev6 = cand0_6.decision_events + cand1_6.decision_events
        guard_fired = any(ev["decision"] == "REJECT_HORIZON" for ev in ev6)
        activated_6 = any(ev["decision"] == "SPECIALIZE_CONFIRMED" for ev in ev6)
        activated_5 = any(ev["decision"] == "SPECIALIZE_CONFIRMED"
                          for ev in cand0_5.decision_events + cand1_5.decision_events)
        if contrast != 0.0 and not guard_fired:
            purity_violations.append({"seed": seed, "contrast": contrast,
                                      "reason": "DIFF_WITHOUT_GUARD_EVENT"})
        for ev in ev6:
            if ev["decision"] == "REJECT_HORIZON" and ev["step"] != 288:
                purity_violations.append({"seed": seed, "step": ev["step"],
                                          "reason": "GUARD_FIRED_OFF_288"})

        collect_events(cand0_6, seed, "DEV006", 0, all_decisions, all_specs)
        collect_events(cand1_6, seed, "DEV006", 1, all_decisions, all_specs)
        collect_events(cand0_5, seed, "DEV005", 0, all_decisions, all_specs)
        collect_events(cand1_5, seed, "DEV005", 1, all_decisions, all_specs)

        out6 = "WIN" if paired_6 > 0 else ("LOSS" if paired_6 < 0 else "TIE")
        out5 = "WIN" if paired_5 > 0 else ("LOSS" if paired_5 < 0 else "TIE")
        raw_results.append({
            "seed": seed,
            "dev006": {"match0_cand": c0_6, "match0_base": b1_6, "match0_delta": d0_6,
                       "match1_base": b0_6, "match1_cand": c1_6, "match1_delta": d1_6,
                       "paired_mean": paired_6, "outcome": out6, "activated": activated_6,
                       "plan_m0": cand0_6.active_plan, "plan_m1": cand1_6.active_plan,
                       "first_spec_step_m0": first_spec_step(cand0_6.decision_events),
                       "first_spec_step_m1": first_spec_step(cand1_6.decision_events)},
            "dev005": {"match0_cand": c0_5, "match0_base": b1_5, "match0_delta": d0_5,
                       "match1_base": b0_5, "match1_cand": c1_5, "match1_delta": d1_5,
                       "paired_mean": paired_5, "outcome": out5, "activated": activated_5,
                       "plan_m0": cand0_5.active_plan, "plan_m1": cand1_5.active_plan,
                       "first_spec_step_m0": first_spec_step(cand0_5.decision_events),
                       "first_spec_step_m1": first_spec_step(cand1_5.decision_events)},
            "contrast_dev006_minus_dev005": contrast,
            "horizon_guard_fired": guard_fired,
            "runtime_sec": round(elapsed, 3),
        })
        paired_rows.append({
            "seed": seed,
            "dev006_match0_delta": d0_6, "dev006_match1_delta": d1_6,
            "dev006_paired_mean": paired_6, "dev006_outcome": out6,
            "dev005_match0_delta": d0_5, "dev005_match1_delta": d1_5,
            "dev005_paired_mean": paired_5, "dev005_outcome": out5,
            "contrast_dev006_minus_dev005": contrast,
            "horizon_guard_fired": guard_fired,
        })
        log(f"[{idx:02d}/50] Seed {seed} | DEV-006 ${paired_6:+9.1f} ({out6}) | "
            f"DEV-005 ${paired_5:+9.1f} ({out5}) | contrast ${contrast:+9.1f} | "
            f"guard={'FIRED' if guard_fired else '-'} | {elapsed:.1f}s")

    total_time = time.time() - t_start
    log(f"\nAll 50 seeds complete in {total_time:.2f}s ({total_time / 50:.2f}s/seed, 4 games each).")

    with open(RAW_RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(raw_results, f, indent=2)
    log(f"  Saved {RAW_RESULTS_FILE}")
    with open(PAIRED_DELTAS_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(paired_rows[0].keys()))
        w.writeheader()
        w.writerows(paired_rows)
    log(f"  Saved {PAIRED_DELTAS_FILE}")

    dec_fields = ["arm", "match", "seed", "step", "current_shops", "confirmation_status",
                  "remaining_horizon", "horizon_satisfied", "selected_route", "baseline_route",
                  "best_candidate_plan", "expected_incremental_value", "liquidity",
                  "physical_feasibility", "decision", "rejection_reason", "active_plan_after"]
    with open(DECISION_EVENTS_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=dec_fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(all_decisions)
    log(f"  Saved {DECISION_EVENTS_FILE} ({len(all_decisions)} rows)")
    with open(SPECIALIZATION_EVENTS_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=dec_fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(all_specs)
    log(f"  Saved {SPECIALIZATION_EVENTS_FILE} ({len(all_specs)} rows)")
    guard_rows = [d for d in all_decisions if d["decision"] == "REJECT_HORIZON"]
    with open(HORIZON_GUARD_EVENTS_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=dec_fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(guard_rows)
    log(f"  Saved {HORIZON_GUARD_EVENTS_FILE} ({len(guard_rows)} rows)")

    stats = {
        "primary_dev006_vs_baseline": describe(d6_list, "DEV-006 minus V54++ baseline (qualification 50050-50099)"),
        "diagnostic_dev005_vs_baseline": describe(d5_list, "DEV-005 minus V54++ baseline (same qual seeds)"),
        "mechanism_contrast_dev006_minus_dev005": describe(contrast_list, "DEV-006 minus DEV-005 (identical CRN)"),
        "mechanism_counts_dev006": count_decisions(all_decisions, "DEV006"),
        "mechanism_counts_dev005": count_decisions(all_decisions, "DEV005"),
        "activated_seeds_dev006": sum(1 for r in raw_results if r["dev006"]["activated"]),
        "activated_seeds_dev005": sum(1 for r in raw_results if r["dev005"]["activated"]),
        "guard_fired_seeds": sum(1 for r in raw_results if r["horizon_guard_fired"]),
        "one_factor_purity_violations": purity_violations,
        "one_factor_purity_ok": len(purity_violations) == 0,
        "n_games_total": 200,
        "total_runtime_sec": round(total_time, 2),
    }
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    log(f"  Saved {STATS_FILE}")

    p = stats["primary_dev006_vs_baseline"]
    log("=" * 80)
    log("EXP-DEV-006 QUALIFICATION SUMMARY (DEV-006 vs V54++ baseline)")
    log("=" * 80)
    log(f"  Paired Mean Delta:  {p['mean']:+,.2f}")
    log(f"  10% Trimmed Mean:   {p['trimmed_mean_10pct']:+,.2f}")
    log(f"  Median Delta:       {p['median']:+,.2f}")
    log(f"  t = {p['t_stat']:.2f} (p = {p['p_value']:.4f}), 95% CI [${p['ci_95_lower']:,.2f}, ${p['ci_95_upper']:,.2f}]")
    log(f"  Record: {p['wins']}W / {p['losses']}L / {p['ties']}T")
    log(f"  Guard fired on {stats['guard_fired_seeds']} seeds; purity: {'OK' if stats['one_factor_purity_ok'] else 'VIOLATED'}")
    if purity_violations:
        raise SystemExit(f"GATE FAILURE: one-factor purity violated: {purity_violations}")


if __name__ == "__main__":
    run_experiment()
