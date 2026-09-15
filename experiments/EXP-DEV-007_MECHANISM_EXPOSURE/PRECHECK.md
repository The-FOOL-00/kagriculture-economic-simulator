# PRECHECK: EXP-DEV-007_MECHANISM_EXPOSURE FREEZE READINESS

**Experiment**: `EXP-DEV-007_MECHANISM_EXPOSURE`
**Date**: 2026-09-15
**Scope**: PROTOCOL-FREEZE gates only. This document authorizes the freeze
commit — it does NOT authorize execution. Execution requires a separate
runner freeze plus same-session re-validation of gates 5–8.

## Gate table

| # | Gate | Expected | Observed | Status |
|---|---|---|---|---|
| 1 | Protocol frozen on disk | `PROTOCOL.md` | SHA-256 in `PROTOCOL_HASH.txt` | PASS at freeze |
| 2 | Baseline (Sub 56146971) | `18402ec6…cb7eeb` | recomputed from disk, match | PASS |
| 3 | Treatment DEV-006 | `06db94e5…44f5eb` | recomputed from disk, match | PASS |
| 4 | Diagnostic DEV-005 | `f52b1686…e2a78` | recomputed from disk, match | PASS |
| 5 | Control (Sub 56146947) | `f651ccd2…fd8b8` | recomputed from disk, match | PASS |
| 6 | Cohort rule + audit | 310000–310499 certified | `SEED_SELECTION_RULE.md`, `SEED_PROVENANCE.md` | PASS at freeze |
| 7 | Trigger definition | exact predicate frozen | PROTOCOL.md §4, source-validated | PASS |
| 8 | N fixed with reasoning | N=500 | `POWER_PLANNING.md` | PASS |
| 9 | Sim port manifest 6/6 | match | re-verified 2026-09-15 | PASS (re-run at launch) |
| 10 | Golden 47,520/47,520 | exact | recorded; MUST re-run pre-execution | PENDING |
| 11 | DEV-005 replay 100/100 | bit-identical | recorded; MUST re-run pre-execution | PENDING |
| 12 | Decision events 400/400 | identical | recorded; MUST re-run pre-execution | PENDING |
| 13 | One-factor probe | exit 0 | recorded; MUST re-run pre-execution | PENDING |
| 14 | Holdout untouched | zero exposure | verified 2026-09-15 (audit phase) | PASS |
| 15 | No experimental seeds | zero executions | no runner exists; none run | PASS |
| 16 | Runner freeze | future commit | NOT WRITTEN — blocks execution | BLOCKED by design |

**Verdict: FREEZE AUTHORIZED — EXECUTION NOT AUTHORIZED.**
Execution is blocked on gate 16 (runner freeze commit) and same-session
re-validation of gates 10–13. Gates 10–13 MUST be re-run in the execution
session on consumed cohorts / frozen references only.
