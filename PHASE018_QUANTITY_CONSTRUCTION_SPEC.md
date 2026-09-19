# PHASE018 — BOUNDARY-SAFE QUANTITY CONSTRUCTION SPEC (Repair B, preregistered)

**Status**: PREREGISTERED (before Arm B execution; design derives from the frozen
Phase016 probe arithmetic, not from pilot outcomes)
**Date**: 2026-09-19
**Scope**: tranche quantity-anchor generation only. No evaluator, safety, WinModel,
trigger, or reservation change.

---

## 1. Failure under repair

Phase017: coarse tranche quantities cross V3 macro cash thresholds (capex gates,
cash-bracket edges), forcing escalation and, when committed, harmful downstream
policy transitions. The evaluator correctly rejects most of these; the defect is
that the generator never offers the intermediate quantity that would have captured
value *without* crossing.

Phase018 ledger diagnostic (existing `results/PHASE017_ATTRIBUTION_LEDGER.csv`, no
new sims): all 1,832 simulated tranche candidates carried reason
`MINIMAL_TRANCHE` with q ∈ {1, 5}; larger structural anchors (depth/full) never
reached simulation. Boundary crossings therefore come from small sales applied on
top of baseline queues near gates — the generator must reason about the **merged
queue**, not the tranche in isolation.

## 2. Boundary map (authoritative source: frozen probe arithmetic)

From `aec/counterfactual/macro_detector.py` (read-only; Repair B mirrors, never
modifies):

| Boundary | Levels / rule | Probe effect |
|---|---|---|
| Cash gates `V3_CASH_GATES` | 500, 600, 1000, 2000, 5000, 7500, 10000, 12000 | any cross → `CASH_CAPEX_GATE` |
| Cash-bracket edges | 500, 2000, 8000, 12000 | bracket shift → `MATERIAL_REGIME_SHIFT` |
| Sheep proximity | cand ≥ 7500 while base < 7500, step < 288 | `CASH_CAPEX_GATE` |
| Tomato proximity | cand ≥ 11000 while base < 11000, step < 432 | `CASH_CAPEX_GATE` |
| Budget guard | within 18 steps of 72-block + \|cashΔ\| ≥ 150 or \|shedΔ\| ≥ 5 | `BUDGET_GUARD_BLOCK` |
| Feed risk | animals + (post wheat < 12 or wheat drop ≥ 4) | `LIVESTOCK_FEED_RISK` |
| Shed saturation | near 90 + Δ ≥ 5 (material shift) | `MATERIAL_REGIME_SHIFT` |

Effective cash-boundary set: {500, 600, 1000, 2000, 5000, 7500, 8000, 10000, 11000*,
12000} (*11000 only when step < 432).

## 3. Projection primitive (mirrors probe lines 216–236 exactly)

```text
project_post_queue_cash(state, baseline_market_orders, commodity, quantity):
    cash = state.cash; shed = copy(state.shed)
    merged = construct_sequential_market_orders(baseline_market_orders, commodity, quantity)
    for o in merged:
        SELL c q:        real = min(shed[c], q); cash += real * price(c); shed[c] -= real
        BUY_PRODUCT c q: cash -= q * price(c); shed[c] += q
    return cash, shed
```

Price source and 20.0 fallback identical to the probe. The generator's "safe"
prediction therefore agrees with the probe's escalation input by construction
(same arithmetic, same inputs). Per §15 this is NOT naive `threshold − cash`: it
accounts for full queue semantics, realizability caps, and feed floors.

## 4. B1 anchor menu (replaces the legacy anchor menu, still ≤ 4 quantities)

For each (commodity, uncommitted) synthesis with baseline queue M:

1. **q_small = 1** (always, if realizable). Minimal probe; also dodges the
   \|shedΔ\| ≥ 5 budget-guard tripwire near block boundaries.
2. **q_current = min(5, uncommitted)** (the legacy minimal tranche). Preserves the
   status-quo alternative so B1 strictly *adds* options rather than retuning.
3. **q_boundary_safe** = largest q ≤ uncommitted such that projected post-queue
   cash stays strictly below the next cash boundary above the projected
   baseline-only cash ($1 epsilon), post-sale wheat ≥ 12 when animals are held,
   and wheat drop < 4. Included iff ≥ 1, distinct, and a boundary actually binds
   (q_current would cross or trip feed while a smaller q does not).
4. **q_boundary_minus** = largest q ≤ uncommitted such that projected post-queue
   cash stays at least $150 below that boundary (the probe's own budget-guard
   noise margin). Included iff ≥ 1 and distinct from the above.

Dedup, realizability-gated (`verify_inventory_realizability`), feed-floor valid,
cap 4. When no boundary binds, the menu collapses to {1, min(5, uncommitted)} —
near-identical to legacy survivors (zero interference in non-boundary windows).

Explicitly NOT included: q=10/depth and q=full anchors are dropped from the B1
menu (they never survived to simulation in Phase017; re-adding them would only
add funnel pressure). If Arm B shows value destruction from their absence, that
is a reportable finding, not a silent re-add.

## 5. Untouched layers

Evaluator, probe, horizon, safety, WinModel, trigger firing rules, reservation
(off in Arm B), and V3 are unchanged. The generator offers alternatives; the
long-horizon evaluator remains the sole authority on whether a crossing is
harmful (some crossings may still commit — that is the evaluator's correct call).

## 6. Arm definition (isolation)

- **B0** = A1 (`build_phase015_treatment_config()`), re-run on the fresh cohort
  as the within-phase control leg.
- **B1** = B0 + boundary-safe quantity menu (`enable_boundary_safe_quantities=True`,
  reservation OFF, trigger unmodified).

## 7. Success criteria (preregistered)

1. Boundary-adjacent turns offer a committable non-crossing alternative where B0
   offered only crossing-or-abstain (candidate-level mechanism check).
2. Macro-escalation rate on tranche candidates decreases without any probe change.
3. Terminal margin improves B0 → B1 with zero safety violations.
4. No candidate-count explosion: mean generated quantities per synthesis ≤ legacy.
