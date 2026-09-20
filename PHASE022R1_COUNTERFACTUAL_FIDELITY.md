# PHASE022R1 — COUNTERFACTUAL FIDELITY (claim withdrawn as circular)

**Date**: 2026-09-20
**Disposition**: empirical MAE=$0.00 claim WITHDRAWN; architecture description
retained; no code changed (freeze).

## 1. Original claim (V22)

> "34 committed intervention traces audited against realized match outcomes;
> MAE = $0.00, max discrepancy = $0.00, r = 1.0000; bit-exact mathematical
> fidelity." (`PHASE022_COUNTERFACTUAL_FIDELITY.md`, qual manifest
> `counterfactual_fidelity_audit`)

## 2. Audit finding — CONFIRMED in this session

1. `aec/evaluation/win_model.py:373-374` (main return) and `:167-168`
   (spatial-desync early return) assign `delta_money_realized=delta_money`
   (prediction copied to "realized").
2. Repo-wide, only `win_model.py` and `executor.py:680-681` (telemetry copy)
   write these fields; nothing ever overwrites them with an observed outcome.
   `projection_status="REALIZED"` is a constructor default.
3. The V22 "audit" (`run_phase022_consolidation.py`, fidelity fn) computes
   `realized_delta = c.get("delta_money_realized", pred_delta)` and diffs it
   against `pred_delta` — the value against itself, with a copy fallback. The
   imported `CounterfactualSimulator`/`CoupledPatch` there are unused: zero
   independent re-simulation.
4. All 34 records in `results/phase022_decision_traces.json` satisfy
   `delta_money == delta_money_realized` (tautology reproduced, not a
   measurement).

## 3. Why a genuine post hoc audit is not established

The mission's preferred repair (recover pre-intervention state → reconstruct
both continuations → independent exact continuation → compare) requires the
recorded pre-intervention full state. The 34 exported traces contain, per
commit: seed/seat/step, mechanism, candidate telemetry
(prediction fields, safety/economic flags), `baseline_action`,
`candidate_action`, macro fields — but **no observation, no EconomicState, no
engine state**. Reconstructing the exact pre-intervention state from actions
alone is not safely possible, and the kagsim engine the cohort ran on is
unavailable on Linux. Re-running the cohort to capture new states would be a
new experiment on the consumed cohort, prohibited by §21. Re-simulating
through the same `CounterfactualSimulator` would repeat the circularity.

Therefore, per §13 fallback, the claim is downgraded rather than re-measured.
No $0.00 figure is retained anywhere in V22R1 reporting.

## 4. Corrected wording (used in all V22R1 reports)

> "Counterfactual fidelity is supported by the exact simulator architecture,
> but an independent post hoc realized-vs-predicted audit was not established
> in Phase 022."

Supporting (non-empirical) architecture facts, retained as description only:

- Market-timing candidates are pure basket reorders evaluated by exact
  sequential clearing arithmetic (`compute_market_price`), with zero physical
  footprint (farmer/hands identical to baseline), which bounds divergence risk
  by construction — an engineering argument, not a measured MAE.
- Per-commit "Impact on Match" attributions in the V22 fidelity report are
  deleted: horizon-limited simulation deltas do not decompose 719-step
  equilibrium match deltas (e.g. seed 249378: +$103 match delta on predictions
  $0 + $36).

## 5. What a future genuine audit would require (not done here)

Persist, at each commit: full observation (or engine checkpoint), baseline
action, candidate action, horizon; then fork the engine from the checkpoint
and run both continuations independently. The repository's unused
`aec/counterfactual/parity_harness.py` gestures at this but is not wired in
and imports Windows-only `kagsim`.
