# PHASE022R1 — HOLDOUT INTEGRITY (tournament cohort re-designation)

**Date**: 2026-09-20
**Rule**: history is corrected by re-designation, never by editing the past.
No experiment was run on any holdout in V22R1; the consumed cohort below was
consumed by a prior experiment, documented here.

## 1. Re-designation (the correction)

| Cohort | Prior label (V22 docs) | Corrected status | Evidence |
| --- | --- | --- | --- |
| `340300..340349` | "Virgin / Untouched" (`PHASE022_BASELINE_FREEZE.md` §4; final-report table; qual manifest `tournament_cohort_340300_340349: true`) | **CONSUMED / RETIRED HOLDOUT — experiment `EXP-AEC-004`** | manifest `seed_start 340300 / seed_end 340349`, 50 seeds × 2 = 100 matches; `results/EXP_AEC_004_MATCHES.csv` (50 seed rows, real scores, commits); `results/EXP_AEC_004_SUMMARY.json` |
| `340050..340199` | "Virgin / Untouched" | **UNTOUCHED (retained)** | R1 boundaried re-search (`results/`, `experiments/`, `scripts/`): only covenant strings (range endpoints in guards/manifests/metrics); zero executions |
| `214200..214249` | "Virgin / Untouched" | **UNTOUCHED (retained)** | Same search: only endpoint covenants + guard-fire records (`EXP-ARCH-002` quarantine tests assert `RuntimeError` on 214200/214225/214249; `EXP-DEV-004` log shows guard FATAL-refusal of 214220, run proceeding on 246000..246049); one `214236` hit is a float substring (`16.564100002142368`), not a seed. Registry `HOLDOUT-COHORT-V1` intact |
| `249376..249395` | "100% pristine / never previously executed" | **Softened**: "no prior gameplay, tuning, or selection on this cohort" | reservation-only pre-use; pre-run tests constructed `kagsim.Game(249376)` initial state (immaterial literal exception, per audit) |

## 2. Consumption record for 340300..340349

- Experiment: `EXP-AEC-004` (Sept 18; manifest + `experiments/EXP-AEC-004/`).
- Scope: seeds 340300..340349 (50 seeds, 100 CRN mirror matches).
- Reality of use: real treatment/control scores (e.g. seed 340300:
  121903/121983), real commits (`commits_treat_a/b`), real telemetry
  (`TELEMETRY_EVENTS.csv`, `COMMITTED_PATCHES.csv`).
- Consequence: permanently retired as a holdout. Never reuse for tuning,
  debugging, selection, or future qualification. V22R1 ran nothing on it.

## 3. Registry update

`DEVELOPMENT_HOLDOUT_REGISTRY.md` §4 (new, versioned addendum; prior sections
untouched): records 340300..340349 under disqualified/consumed cohorts with
pointer to this document. The Phase 022 "untouched" strings are preserved in
the original files and explicitly corrected in the §22 rewrite pass
(correction blocks, not silent edits).

## 4. V22R1 cohort hygiene statement

- Semantic-equivalence (§6) and loader-equivalence (§7) testing used only the
  already-consumed Phase 022 development cohort `249376..249395` (a
  software-equivalence comparison, not an economic experiment) plus the
  RELEASE_SMOKE_ONLY seed 249376 for packaged QA/regression.
- `340050..340199` and `214200..214249` were searched as text, never executed.
- `340300..340349` was not executed either (already consumed; stays retired).
