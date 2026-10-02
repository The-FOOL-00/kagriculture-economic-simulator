# PHASE022R1 — PERFORMANCE AUDIT (latency claim correction)

**Date**: 2026-09-20
**Sources**: stored V22 aggregates (`results/phase022_consolidation.json:latency`,
Windows/kagsim) + fresh V22R1 measurements (Linux/KE, §5 below).

## 1. Stored V22 aggregates (restated, distribution unverifiable)

| Metric | Value | Kaggle budget | Note |
| --- | --- | --- | --- |
| n steps | 28,760 | — | = 40 × 719 (see §3) |
| mean | 75.76 ms | 1,000 ms/turn | PASS |
| median | 50.89 ms | 1,000 ms/turn | PASS |
| P95 | 229.40 ms | 1,000 ms/turn | PASS vs Kaggle budget |
| P99 | 404.87 ms | 1,000 ms/turn | PASS vs Kaggle budget |
| max | 2,346.68 ms | 1,000 ms/turn | **EXCEEDS turn budget**; step unattributed in exports |
| `within_limit` (max < 100 ms) | **false** | config's own 100 ms cap | contradicts the V22 PASS verdict |

No per-step latency export exists, so the distribution (P95/P99/max) cannot be
independently recomputed — the aggregates are trusted as computed, flagged as
unverifiable. `within_limit=false` is internally consistent (max > 100).

## 2. Original claim → corrected claim

- Original: "predictable, sub-100ms turn latencies with zero risk of timeout
  disqualification" (`PHASE022_PERFORMANCE_AUDIT.md` §5).
- Audit finding: CONFIRMED misleading — P95/P99/max all exceed 100 ms.
- Corrected: **"Median decision latency was approximately 51 ms; tail latency
  was materially higher (P95 ≈ 229 ms, P99 ≈ 405 ms, max ≈ 2,347 ms).
  All turns were within the 1,000 ms Kaggle budget except the unattributed
  max; the config's own 100 ms limit was breached (`within_limit=false`)."**
- "Under 100 ms" is claimed only for the median, never as a blanket.

## 3. Step-count correction (verified under two engines)

- V22 text: "28,760 game steps (40 full 720-step matches)", "28,800 steps".
- Corrected: **719 decision steps/match, 28,760 total** (40 × 719).
  Verified: kagsim `sim.hpp` done-at-718 (per audit) AND independently in V22R1:
  KE with `episodeSteps=720` calls the agent exactly 719 times (steps 0..718;
  the 720th `env.steps` entry is terminal with no agent call) — probed live in
  this session (`test_phase022r1_competition_loader.py` asserts 719 telemetry
  records per 720-step game).

## 4. Removed / qualified figures

- The 9-stage pipeline table (summing to 75.76) is **deleted**: unsourced —
  `AECTelemetry` carries 6 latency fields
  (`ir/event/opp/sim/safety/total_time_ms`, `executor.py:158-164`), not 9
  stages, and no per-stage export exists.
- "Max occurs strictly on Step 0" (V3 load under the 60 s init budget):
  qualified as **plausible but unverified** (no per-step export identifies the
  max step). The V22R1 QA's bare-exec step-0 probe is consistent with a slow
  first step (V3 tarball exec) but does not prove the 2,347 ms attribution.
- "Under 2.5 ms no-event fast path" and "1.8 ms" figures: **unverified** (no
  per-step export); deleted from claims.

## 5. Fresh V22R1 measurements (Linux, KE 1.32.7, driver-side timing)

Measured during the §6 equivalence matrix: wall time per treatment-agent call
(AEC `act()` incl. V3 backbone call), 40 seeds × 2 seats × 719 decisions × 2
implementations, plus packaged-QA full-game timings. Driver-side ≠ V22's
in-executor telemetry; reported separately, never mixed:

| Metric | V22R1 KE/Linux (driver-side) |
| --- | --- |
| clean run (unloaded, rep 249380/0) | n=719: mean 72.13, median 51.06, P95 195.36, P99 256.31, max 340.15, min 0.34 ms |
| loaded matrix (6-way parallel, 80 games) | n=57,520: mean 148.97, median 121.38, P95 378.83, P99 503.12, max 886.12 ms |
| full-game wall (720-step) | ≈ 39–56 s unloaded (≈ 54–72 ms/step); ≈ 96–136 s under 6-way load |
| step-0 (V3 load) in clean run | 74.76 ms — NOT the max (max 340.15 ms on a later step) |

Clean median 51.06 ms reproduces V22's 50.89 ms across engines/OSes. The
loaded-matrix distribution is reported for completeness with its contention
caveat — the clean run is the representative figure. All V22R1 measurements
fall within the 1,000 ms Kaggle budget. The clean run directly contradicts a
blanket "max is always step 0" reading (here step 0 was mid-distribution),
supporting the §4 qualification.

These figures describe the repaired artifact under the competition engine on
the release machine; they are engineering measurements, not economic evidence.
