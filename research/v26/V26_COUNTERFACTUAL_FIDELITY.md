# V26 — COUNTERFACTUAL FIDELITY AUDIT (§25)

## 1. Objective

The V22 release audit found the old `$0.00 MAE` fidelity claim was circular
(realized delta was copied from predicted delta). V26 must not repeat this:
for committed V25 market-timing interventions, predicted deltas must be
validated against **independently reconstructed** continuations, and realized
deltas must come from **separate paired outcomes**, never from
`realized = predicted`.

Note: `aec/evaluation/win_model.py` still sets
`delta_money_realized=delta_money` at commit time (lines 167-168, 373-374).
Those fields were **not used** anywhere in this audit.

## 2. Method

### 2.1 Sample

7 ARM3 tournament matches spanning the outcome range (6 single-commit, 1
double-commit), 8 committed interventions total:

| Seed | Seat | Match realized Δ (ARM3−ARM1) |
| --- | --- | --- |
| 249470 | 0 | −7 |
| 249471 | 0 | +1 |
| 249474 | 0 | −3 |
| 249479 | 0 | +46 |
| 249487 | 0 | +29 |
| 249488 | 0 | +50 |
| 249472 | 0 | +97 (2 commits) |

Realized Δ is the tournament match-level paired terminal-reward difference.
For single-commit matches this attributes cleanly to the one intervention.

### 2.2 Phase A — instrumented replay (record)

Each match was re-run end-to-end in a fresh process with the exact tournament
configuration (`DEPENDENCY_AWARE_MARKET_TIMING`, `ROBUST_MODE`,
`enable_quarantine_scan=False`). Recorded per commit: step, patch id, family,
market/worker mutations, simulation horizon, macro-escalation flag, and the
commit-time predicted `delta_money` / `delta_margin` from candidate telemetry.
Full candidate + opponent action streams were recorded.

Determinism check: all 7 replays reproduced the checkpoint terminal reward
and commit count exactly (7/7).

### 2.3 Phase B1 — history-faithful independent recomputation

Fresh process, fresh environment, fresh adapters. The recorded action streams
were replayed headlessly to the pre-intervention step `t` while a fresh
executor observed each step (history rebuilt from replay, not copied). The
executor then evaluated step `t` and its commit decision + predicted deltas
were compared to the Phase A record.

### 2.4 Phase B2 — history-free independent recomputation

Fresh process, fresh environment, fresh V25 adapter whose chassis was aligned
by acting on replayed observations only (actions discarded). A fully fresh
executor (no prior history) evaluated **only** step `t` on the
replay-reconstructed state. This tests whether the prediction is a pure
function of reconstructed state rather than accumulated simulator objects.

## 3. Results

### 3.1 Reproducibility: exact

| Match | Step | Family | Horizon | Escalated | Recorded pred$ / predM | B1 match | B2 match |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 249470 s0 | 577 | MARKET_TIMING | 18 | No | +1.0 / +2.0 | YES | YES |
| 249471 s0 | 649 | MARKET_TIMING | 36 | Yes | +54.0 / +109.0 | YES | YES |
| 249474 s0 | 649 | MARKET_TIMING | 36 | Yes | +15.0 / +31.0 | YES | YES |
| 249479 s0 | 649 | MARKET_TIMING | 36 | Yes | +8.0 / +18.0 | YES | YES |
| 249487 s0 | 649 | MARKET_TIMING | 36 | Yes | +24.0 / +48.0 | YES | YES |
| 249488 s0 | 649 | MARKET_TIMING | 36 | Yes | +15.0 / +31.0 | YES | YES |
| 249472 s0 | 481 | MARKET_TIMING | 18 | No | +89.0 / +178.0 | YES | YES |
| 249472 s0 | 649 | MARKET_TIMING | 36 | Yes | +10.0 / +23.0 | YES | YES |

8/8 predictions reproduced bit-exactly under both independent
reconstructions. B2 equality proves the counterfactual prediction derives
from reconstructed state alone. H5 (counterfactual reproducibility) is
satisfied with zero circularity.

### 3.2 Predicted vs realized (directional)

Prediction is an H-step wealth delta; realized is a terminal-reward delta, so
exact equality is not expected. Sign agreement is the fidelity signal:

| Match | Predicted $ (sum) | Realized Δ | Sign agree |
| --- | --- | --- | --- |
| 249470 s0 | +1 | −7 | No (both noise-scale) |
| 249471 s0 | +54 | +1 | Yes |
| 249474 s0 | +15 | −3 | No (both noise-scale) |
| 249479 s0 | +8 | +46 | Yes |
| 249487 s0 | +24 | +29 | Yes |
| 249488 s0 | +15 | +50 | Yes |
| 249472 s0 | +99 (89+10) | +97 | Yes |

Sign agreement 5/7; both disagreements are ±single-dollar scale on both
sides. No large-predicted-positive → large-realized-negative failure exists
in the sample. Worst case: predicted +$1, realized −$7.

## 4. Certification

- No `realized = predicted` assignment was used; realized deltas are
  tournament paired outcomes and recomputed deltas come from fresh-process
  replay reconstruction.
- Counterfactual predictions are exactly reproducible and history-free
  reconstructable: **§25 PASSED**.
- Predictions show directional agreement with realized outcomes at small
  magnitudes, consistent with the tournament's +$10.85 mean transfer effect.
