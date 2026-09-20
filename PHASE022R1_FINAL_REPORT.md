# PHASE022R1 — FINAL REPORT (release repair & evidence correction)

**Date**: 2026-09-20
**Mission**: repair the V22 submission so the exact packaged artifact executes
correctly under the competition loader, remove unsupported claims, correct
audit instrumentation, preserve validated AEC semantics, rebuild, and
independently re-verify. No new mechanisms, no new alpha, no score
optimization, no economic-logic change.
**Foundation (frozen)**: V3 (`845e0d10...`) +
DEPENDENCY_AWARE_MARKET_TIMING + TERMINAL_LIQUIDATION + PHASE_SHUTDOWN.
**Release candidate**: `submission_aec_v22r1.tar.gz`
(`6b879b3e...`; retired V22: `2b23bc22...`).

## 1. Engineering repair (the release blocker)

**Root cause** (reproduced before fixing): packaged V22 `main.py:9` evaluated
`__file__` unconditionally at module top; the competition loader
(`kaggle_environments` `get_last_callable`: `exec(source, {})`) provides no
`__file__`, so every step raised `NameError`, every action coerced to PASS,
and the submission scored $3,000.00 (starting money) — certified by vacuous
QA (`DONE` + `reward > 0` + `$3k==$3k`). Full record:
`PHASE022R1_LOADER_FAILURE_REPRO.md`.

**Repair** (entrypoint only): new loader-safe `main.py` — no unconditional
`__file__` (tokenize-verified); append-only, marker-validated sys.path
fallback (never shadows); V3 tarball by ordered existence-validated
candidates with BackboneAdapter self-relative default. Freeze proof:
V22→V22R1 packaged diff is `main.py` ONLY (`aec/`, `config.py`,
`extracted_agents/`, V3 payload all byte-identical).
`PHASE022R1_SUBMISSION_INTEGRITY.md`.

**Re-verification**: hardened QA (bare-exec sim, full KE game vs starter at
$185,041 V3-scale, H2H vs V3 $101,807 tie, reward+action-sequence
determinism, all `debug=True`); loader regression suite
(`tests/aec/test_phase022r1_competition_loader.py`, 3 tests); old-vs-repaired
semantic equivalence on 249376..249395 (§2); three-mode loader equivalence
(`PHASE022R1_LOADER_EQUIVALENCE.md`).

## 2. Semantic preservation (software-equivalence, not economics)

40 games (20 seeds × 2 seats, treatment vs frozen V3) run under KE 1.32.7
twice: once via normal dev imports (known-working V22 implementation), once
via the packaged V22R1 entrypoint under bare-exec loader semantics
(no `__file__`, repo-isolated, cwd=`/tmp`). Compared exactly per step: both
seats' actions, V3 base action, decision, events, candidates (IDs, mechanisms,
safety/economic flags), commits, terminal rewards, paired deltas.

**Result: 40/40 EXACT — 0 differences across 28,800 step records × 10
fields** (both seats' actions, V3 base action, decision, events, candidates,
commits, rewards, paired deltas). Full table:
`PHASE022R1_SEMANTIC_EQUIVALENCE.md`.

Control: dev-vs-dev cross-process repeats 4/4 bit-identical (engine +
harness deterministic), so any dev-vs-rep difference would have been
repair-caused. None found. Bonus corroboration: all 40 KE/Linux triples
reproduce the kagsim/Windows ledger exactly (40/40) — engineering evidence,
not re-qualification.

## 3. Economic result (corrected wording governs)

> "On the fresh 40-match development cohort, the validated foundation
> produced a positive mean paired terminal-margin delta of approximately
> $33.35 relative to pure V3. The result is cohort-specific and accompanied
> by substantial uncertainty; the available evidence does not establish a
> universal or globally optimal effect."

Ledger data exact (R1 scipy recomputation: mean +$33.35, median +$22, std
$1152.01, CI [-$335.08, +$401.78], 21/7/12, d = 0.03, ledger-vs-JSON 0
mismatches). Inference corrected: no Phase 022 preregistration exists;
four-test table — match t FAIL (p=0.86), match Wilcoxon nominal p=0.034,
seed t p=0.024, seed Wilcoxon ≈0.050–0.055 (method band straddling 0.05);
98.6% of sum-of-squares is seat artifact; "passed the author's stated
Wilcoxon gate" replaces "FOUNDATION QUALIFIED" as superiority verdict.
Experiment characterized as fresh-cohort validation / confirmatory-looking
but post hoc documented evaluation.

## 4. Attribution (valid enforcement, scoped headline)

3-layer ablation enforcement re-verified from code (L1 opportunity filter,
L2 patch generation, L3 commit gate; 7 genuinely distinct arm configs):

| Arm | Intended mechanisms | Actual mechanisms | Valid? |
| --- | --- | --- | --- |
| FULL_FOUNDATION | Timing + Liq + Shutdown | Timing + Liq + Shutdown (Liq/Shutdown eligible, never fired) | YES |
| NO_MARKET_TIMING | Liq + Shutdown | Liq + Shutdown (never fired) | YES |
| NO_TERMINAL_LIQUIDATION | Timing + Shutdown | Timing + Shutdown | YES |
| NO_PHASE_SHUTDOWN | Timing + Liq | Timing + Liq | YES |
| MARKET_TIMING_ONLY | Timing | Timing | YES |
| TERMINAL_LIQUIDATION_ONLY | Liq | Liq (never fired) | YES |
| PHASE_SHUTDOWN_ONLY | Shutdown | Shutdown (never fired) | YES |

Retained phrasing: "Within this experimental design and fresh cohort,
DEPENDENCY_AWARE_MARKET_TIMING was the mechanism associated with the observed
incremental economic effect." Liq/Shutdown: "no evidence of regression in
this cohort (neither triggered a committable candidate); live protective
value unproven." (Per-arm ledgers missing — reproducibility gap disclosed;
interaction-collision zeros conditional on never-co-firing mechanisms.)

## 5. Claims withdrawn or downgraded

- Counterfactual fidelity MAE=$0.00: WITHDRAWN as circular
  (`PHASE022R1_COUNTERFACTUAL_FIDELITY.md`).
- "720/720 steps bit-identical": replaced by genuine R1 per-turn replay audit
  (`PHASE022R1_DETERMINISM_AUDIT.md`).
- "Sub-100ms turn latencies / zero timeout risk": replaced by median/tail
  split; 9-stage table deleted; 719 steps/match
  (`PHASE022R1_PERFORMANCE_AUDIT.md`).
- Tournament cohort "untouched": re-designated CONSUMED/RETIRED (EXP-AEC-004)
  (`PHASE022R1_HOLDOUT_INTEGRITY.md`).
- "0 safety violations" (vacuous counter): restated as observed outcomes;
  counters repaired; placeholders documented
  (`PHASE022R1_SAFETY_AUDIT.md`).
- Optimality/proven/Pareto/ceiling adjectives: cut to evidence-graded
  phrasing throughout the §22 rewrite.

## 6. Autonomy (revised description, verified against code)

> "The system is a deterministic supervisory economic control layer wrapped
> around a frozen V3 policy. Each turn it receives the environment
> observation, retains V3's action as the baseline, constructs an economic
> state representation, detects supported events and opportunities,
> synthesizes candidate patches, evaluates candidates using exact
> continuation and safety gates, and either commits a permitted intervention
> or emits the V3 action unchanged. It is not an independently trained
> end-to-end policy and does not discover arbitrary strategies outside its
> implemented mechanism families."

Clause-by-clause: observation in (`act(obs)`); V3 baseline retained
(`call_once` + immutable `BaselineResult`); economic state
(`build_economic_state`); events/opportunities (`EventBus`,
`OpportunityEngine` + L1 filter); candidate patches (`PatchGenerator` + L2);
exact continuation + safety gates (`CounterfactualSimulator`, `WinModel`,
`SafetyChecker.verify`); commit-or-baseline (L3 gate, fail-closed
`ABSTAIN`/`BACKBONE`/`FAIL_SAFE` paths); no training loop anywhere (no RNG,
no learned weights — verified by import + determinism evidence); mechanism
families bounded by `enabled_mechanisms` + 3-layer enforcement.

## 7. Residual risks and non-release-follow-ups (honest disclosure)

- Live LIQ/SHUT behavior unproven (never fired in validation).
- Per-arm match ledgers and per-step V22 telemetry/latency unexported
  (V22 aggregates trusted via reviewed code, not re-derived).
- V22 full suite re-execution impossible on Linux (Windows-only `kagsim`);
  counts reconciled, runs not re-executed.
- Which step produced the 2,347 ms V22 latency max is unattributed.
- Release commit/tag (audit A3) NOT performed: committing requires explicit
  user authorization (pending user decision — see release gate).
- No preregistration exists; no universal/optimality claim is made.

## 8. Artifact index (R1 deliverables)

`PHASE022R1_REPAIR_LOG.md`, `PHASE022R1_LOADER_FAILURE_REPRO.md`,
`PHASE022R1_SEMANTIC_EQUIVALENCE.md`, `PHASE022R1_LOADER_EQUIVALENCE.md`,
`PHASE022R1_COUNTERFACTUAL_FIDELITY.md`, `PHASE022R1_DETERMINISM_AUDIT.md`,
`PHASE022R1_SAFETY_AUDIT.md`, `PHASE022R1_PERFORMANCE_AUDIT.md`,
`PHASE022R1_HOLDOUT_INTEGRITY.md`, `PHASE022R1_SUBMISSION_INTEGRITY.md`,
`PHASE022R1_FINAL_REPORT.md` (this file), `PHASE022R1_RELEASE_GATE.md`,
`PHASE022R1_QUAL_MANIFEST.json`, `PHASE022R1_SUBMISSION_SHA256.txt`,
`PHASE022R1_QA_RESULTS.json`,
`scripts/build_phase022r1_submission.py`,
`tests/aec/test_phase022r1_competition_loader.py`,
`tests/aec/test_phase022r1_safety_predicates.py`.
