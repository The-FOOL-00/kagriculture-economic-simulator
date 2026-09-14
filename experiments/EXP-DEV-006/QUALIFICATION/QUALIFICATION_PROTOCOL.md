# EXP-DEV-006 QUALIFICATION PROTOCOL (FROZEN PRE-REGISTRATION)
## Confirmatory Replication of the Frozen DEV-006 Treatment on the Reserved Qualification Cohort

**Document Identifier**: `QUALIFICATION_PROTOCOL.md`
**Parent Experiment**: `EXP-DEV-006` (Discovery: virgin seeds 248000–248049, Category A / Strong mechanism reproduction)
**Phase**: Formal Qualification (confirmatory replication — NOT Discovery, NOT optimization)
**Date**: 2026-09-14
**Status**: PRE-REGISTRATION FREEZE (Must be committed to Git prior to first Qualification seed execution)
**Governance Authority**: Zero-Leakage Governance

### Frozen Identity (verified against the frozen Discovery manifest before any Qualification execution)

| Artifact | Path | SHA-256 (frozen) |
|---|---|---|
| Baseline (live submission 56146971 / V54++) | `candidates/compiled_v54_plus_residual.py` | `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb` |
| Treatment DEV-006 (byte-identical to Discovery) | `candidates/closed_loop_architecture/dev_006_horizon_guard_scheduler.py` | `06db94e59e2c271b5490aad78fdb760bd8a250f28ec4407de2d2f6be0644f5eb` |
| Diagnostic DEV-005 | `candidates/closed_loop_architecture/dev_005_confirmed_shop_scheduler.py` | `f52b168619e47bea6a052faff890fc84804cb39b47392d247139967f910e2a78` |
| Control (submission 56146947) | `candidates/compiled_v54_plus_shop.py` | `f651ccd220e701968bc33579812d8917da63f5b0582f2fd0d363fa6a16ffd8b8` |
| Discovery protocol V1.5 | `experiments/EXP-DEV-006/DEVELOPMENT_EXPERIMENT_PROTOCOL_V1_5.md` | `e52a0570a8bc9cfeafe1165f49f4c9d77ef9a3b7aa030783f8aef7e9ee7b04e8` |

Note on the task order's "commit 06db94e5": no such Git commit exists; `06db94e5…` is the
SHA-256 prefix of the frozen DEV-006 treatment file. The treatment file on disk recomputes to the
full frozen hash above, which matches the committed Discovery manifest (`f42c72b`). No STOP triggered.

### Treatment (ONLY permitted change — no tuning, no sweep)

DEV-005 (exact, byte-identical) + fixed H=500 late-entry guard (reject NEW specialization from
`BASELINE_BACKBONE` when `720 - step < 500`; guard can only fire at step 288 by construction).
Absolutely no H sweep, H2, runway model, threshold tuning, route rewrite, YARN special case,
additional hysteresis, parameter search, or post-hoc treatment modification.

### Qualification Cohort (pre-specified, not post-hoc)

- Seeds `50050–50099` inclusive, N=50 contiguous seeds, 200 paired CRN games:
  - Primary arm: DEV-006 vs V54++ baseline × 2 seats → Δ⁶ᵢ = 0.5(Δ⁶ᵢ,₀ + Δ⁶ᵢ,₁).
  - Diagnostic arm (permitted by this frozen protocol, diagnostics only): DEV-005 vs V54++ baseline
    × 2 seats, identical CRN → Δ⁵ᵢ. Mechanism contrast Δ⁶ᵢ − Δ⁵ᵢ per seed. Never used for tuning.
- This is the protocol-reserved Qualification partition (`DEVELOPMENT_EXPERIMENT_PROTOCOL_V1_1.md`
  §2.7 Stage 2). Virginity with respect to the DEV-006/DEV-005 treatments is certified in
  `QUALIFICATION_SEED_PROVENANCE.md` (zero prior DEV-005/DEV-006 simulations on these seeds;
  prior EXP-DEV-002 consumption under a different treatment disclosed therein).

### Quarantined / read-only (runner hard-aborts on any request)

- `214200–214249` (virgin final holdout — zero access beyond non-consumption certification)
- `248000–248049` (EXP-DEV-006 Discovery cohort — consumed, never re-run here)
- `245000–245049`, `246000–246049`, `247000–247049` (consumed DEV-003/004/005 cohorts)
- `50000–50049`, `50100–50149`, `50000–50499` sweep/contaminated regions (outside-cohort guard)
- Live submissions 56146971 / 56146947, all EXP-DEV-004/005 artifacts — read-only, hash-verified

### Simulator

Authoritative Windows binary (`kagsim.cp314-win_amd64.pyd`) is not loadable on Linux
(ModuleNotFoundError confirmed this session). The validated pure-Python port is used:
- Port: `experiments/EXP-DEV-006_HORIZON_KILLTEST/port/kagsim_py` (`__version__ 0.4.0.port1`)
- Engine: `ENGINE_VERSION 1.32.7`
- Combined port-bytes SHA-256: `3ed2ab4ca3d30421a7b2d73a909951dc45283305d8752623c3267f0eabcb28a8`
- Python: `3.14.4 (main, Jun 18 2026, 14:25:02) [GCC 15.2.0]`, `Linux-6.6.114.1-microsoft-standard-WSL2-x86_64-with-glibc2.43`
- Integrity gates (all verified BEFORE execution, see `QUALIFICATION_PRECHECK.md`):
  port manifest 4/4 + validators 2/2, golden traces 47,520/47,520, DEV-005 replay 100/100
  bit-identical, decision events 400/400 identical, runtime probe one-factor PASS (exit 0).

### Primary Metric

Paired per-seed reward difference: DEV-006 reward − baseline reward (paired mean over 2 seats).
Report: mean, median, SD, SE, paired t-statistic, two-sided p-value, 95% Student-t CI, minimum,
maximum, 5th percentile, 10% trimmed mean, win/loss/tie counts, count of nonzero seeds.

### Secondary Mechanism Diagnostics (diagnostics only — never tuning)

DEV-006 vs DEV-005 on the same Qualification seeds (identical CRN): whether H=500 eliminates
late-entry losses, preserves successful early entries, and produces no new losses on seeds where
DEV-005 and baseline were identical. For every non-tie seed record: activation step(s), plan,
entry at step 216/288/other, whether H=500 fired, cash trajectory, route/service feasibility,
terminal inventory, terminal liquidity, worker/animal/service starvation flags where instrumented.
Full seed-level forensic trace for every loss and every unusually large win.

---

## FROZEN QUALIFICATION GATES (from the experiment plan — no new thresholds)

All numeric thresholds below are quoted verbatim from frozen governing documents. No threshold was
invented after seeing data (no Qualification data exists at freeze time).

### A. Statistical performance gate — source: `DEVELOPMENT_EXPERIMENT_PROTOCOL_V1_1.md` §2.7 Stage 2

> "Must achieve t > 1.96 (p < 0.05) and worst loss ≥ −$800.00."

- PASS iff paired t-statistic > 1.96 (two-sided p < 0.05) with mean > 0.

### B. Mechanism replication gate — source: `DEVELOPMENT_EXPERIMENT_PROTOCOL_V1_5.md` §6 Category A

> "late-entry failures < DEV-005 arm AND zero horizon-prevented large wins"

- PASS iff (i) count of late-entry (step-288 first-entry) failures under DEV-006 is strictly fewer
  than under the DEV-005 diagnostic arm on the same seeds, AND (ii) the mechanism contrast
  (DEV-006 − DEV-005) has minimum ≥ $0.00 across all 50 seeds (zero prevented wins / zero new
  losses vs DEV-005), AND (iii) one-factor purity holds (nonzero contrast only on guard-fired seeds).

### C. Tail-risk gate — source: V1.1 §2.7 Stage 2 and V1 §4.1 / V1.1 §2.7 stop criteria

> "worst loss ≥ −$800.00" / "If worst single-seed loss < −$800.00, mark FAILED"

- PASS iff minimum paired seed delta ≥ −$800.00. Violation is an automatic FAIL trigger.

### D. Treatment integrity gate — source: frozen Discovery manifest + V1.5 §3/§7

- PASS iff all five hashes recompute exactly, the runner's one-factor purity gate holds
  (contrast ≠ 0 only where `REJECT_HORIZON` fired, guard only at step 288), and simulator parity
  holds (manifest 4/4, golden 47,520/47,520, replay 100/100, events 400/400, probe exit 0).

## PREDECLARED DECISION RULE (exact — applied without modification after results)

- **QUALIFY** iff A PASS **and** C PASS **and** D PASS.
  (A strong mechanism alone is NOT sufficient: B PASS without A PASS cannot yield QUALIFY.
  B is reported separately and does not gate QUALIFY.)
- **FAIL** iff C violated (worst seed < −$800.00), or statistically significant harm
  (two-sided p < 0.05 with mean < 0), or a guard-caused new severe failure mode is demonstrated
  (contrast minimum < $0.00 with a forensic-confirmed guard-attributable loss), or D violated.
- **INCONCLUSIVE** for all other outcomes (e.g., B PASS but A not significant; guard inert with
  Δμ ≈ 0; significant mean driven by a single seed with trimmed mean $0 and no mechanism support).

Statistical caution (pre-registered): the Discovery mean (+$290.90, p=0.168, trimmed mean $0, two
fresh activations) is NOT evidence of broad expected-value improvement. The Qualification report
must explicitly distinguish replicated mechanism from generalized economic advantage, and must not
oversell either conclusion.

## Governance & Stopping Rule

1. Execute exactly N=50 seeds (50050–50099), then STOP. No extension, no seed replacement, no H
   re-tuning, no automatic follow-on experiment.
2. No inspection-driven treatment changes: forensics run AFTER all 50 seeds complete.
3. Do not run another experiment, tune H, create H2, search other horizons, touch live Kaggle,
   generate a new submission, or touch the final holdout.
4. No Kaggle submission. Deliverables: FINAL_REPORT.md, FORENSIC_AUDIT.md, machine-readable result
   summary, exact hashes, Git commit SHA, explicit QUALIFY / FAIL / INCONCLUSIVE recommendation.

## Protocol Commitment Rule

This protocol, its SHA-256 hash, the precheck, the provenance audit, and the runner were written to
disk, verified, and committed to Git BEFORE the first Qualification simulation. The freeze commit
hash and timestamp are recorded in `QUALIFICATION_PROTOCOL_HASH.txt` and the execution manifest.
The experiment was not modified after any result was observed (no Qualification result existed).
