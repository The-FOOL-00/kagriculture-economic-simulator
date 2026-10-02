# PHASE022R1 — RELEASE GATE

**Date**: 2026-09-20
**Candidate**: `submission_aec_v22r1.tar.gz`
(`6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5`)
**Retired**: `submission_aec_v22.tar.gz` (`2b23bc22...`)

## 1. Gate matrix (§20 + §25)

### Engineering

| Criterion | Result | Evidence |
| --- | --- | --- |
| Competition loader works | PASS | Bare-exec (no `__file__`) + KE file-path games DONE at V3 scale |
| No `__file__` dependency | PASS | Tokenize-verified; every code occurrence guarded; 40-game matrix under bare exec |
| Full game executes | PASS | 80+ full 720-step games DONE/DONE |
| Real AEC behavior occurs | PASS | 719 decisions/game with BACKBONE/ABSTAIN/COMMIT telemetry; 34-commit pattern reproduced; not-all-PASS asserted |
| Package is standalone | PASS | Subprocess/clean-dir isolated runs; packaged-only imports proven; no network/repo/cwd dependence |
| Archive reproduces cleanly | PASS | Extract → simulate from outside repo; 130 members; LF; hardened QA green |

### Semantic preservation

| Criterion | Result | Evidence |
| --- | --- | --- |
| Repaired ≡ known-working V22 behavior | PASS | 40/40 exact; 0/288,000 field diffs; control 4/4 |
| No economic mechanism changed | PASS | Packaged `aec/` byte-identical to V22 (diff-proven); main.py-only delta |
| V3 unchanged | PASS | SHA `845e0d10...` re-verified (`cmp`-identical payload) |

### Scientific honesty

| Criterion | Result | Evidence |
| --- | --- | --- |
| No fake preregistration claim | PASS | Zero preregistration strings in R1 docs; experiment framed as post hoc documented |
| No unsupported robustness claim | PASS | Four-test table; method-band Wilcoxon; d=0.03 negligible; CI-spanning disclosed |
| No unsupported global-optimality claim | PASS | Conservative cohort-specific wording; optimality adjectives cut in §22 rewrite |
| No circular fidelity claim | PASS | MAE=$0.00 withdrawn; downgrade wording adopted |
| No overstated latency claim | PASS | Median/tail split; 9-stage table deleted; 719 counts; fresh clean-run measurements |
| No false holdout claim | PASS | 340300..349 CONSUMED/RETIRED; others verified by boundaried re-search + guard records |

### Safety

| Criterion | Result | Evidence |
| --- | --- | --- |
| Safety predicates genuinely evaluated | PASS WITH DOCUMENTED EXCEPTION | Every commit gated by ~20 evaluated predicates (proven by adversarial tests); the two certificate-only placeholders (`purchase_ok`, `market_collision_ok`) are documented as unevaluated — implementing new rejections would violate the §1 safety-policy freeze, so §15's document-don't-claim fallback applies (see `PHASE022R1_SAFETY_AUDIT.md`) |
| Fail-closed behavior verified | PASS | Exception→baseline, backbone-failure→PASS, quarantine/policy ABSTAIN — tested |

### Determinism

| Criterion | Result | Evidence |
| --- | --- | --- |
| Claimed level actually tested | PASS | Per-turn scope (every action/base/decision/commit/reward) verified across repeats, processes, loader modes, load conditions |

### Traceability

| Criterion | Result | Evidence |
| --- | --- | --- |
| Archive ≡ audited source | PASS | Packaged `aec/` == working tree (diff); QA ran against these exact bytes; SHA recorded |
| Release commit/tag | DEFERRED (not a code blocker) | Requires explicit user authorization per source-control safety rules; recommended follow-up: commit + tag `v22r1` so "audited == packaged" is pinned by hash |

## 2. Release status

### RELEASE READY

All §25 criteria pass (one documented exception, one deferred authorization).
No material issue remains open: the engineering blocker is repaired and
re-verified end-to-end; every scientific claim is no stronger than its
evidence; semantics are preserved bit-for-bit; the sole residual items are
disclosed uncertainties (live LIQ/SHUT, unexported V22 granular data,
kagsim-bound suite) and the user-gated commit/tag step.

Do not start Phase 023 from this gate. Any future work requires a new mission.
