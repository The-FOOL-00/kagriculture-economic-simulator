# PHASE018 — FUNNEL RESERVATION SPEC (Repair A, preregistered)

**Status**: PREREGISTERED (before Arm A execution)
**Date**: 2026-09-19
**Scope**: candidate-funnel allocation policy only. No quantity, trigger, evaluator,
safety, or WinModel change.

---

## 1. Failure under repair

Phase017 seed 249288: treatment generated a large experimental tranche-candidate pool;
rank truncation (`max_candidates=8`) selected only experimental candidates; the
validated foundation opportunity (`DEPENDENCY_AWARE_MARKET_TIMING`, worth +$1,485 in
control) never reached simulation; treatment lost -$1,561 with 0 commits. This is a
cross-mechanism scheduling defect, not an evaluator defect.

## 2. Mechanism: minimal-displacement class-floor enforcement

At every rank-truncation point the funnel selects top-K by the stage's existing
canonical ranking key (unchanged). Reservation adds **class floors**:

- Partition ranked items into `FOUNDATION` vs `GENERAL` via a configurable
  classifier (default: `mechanism_family ∈ ENABLED_FOUNDATION_MECHANISMS`).
- Reserved foundation seats: `R = max(1, floor(K × 0.25))`
  (K=16 → R=4 opportunities; K=8 → R=2 candidates). Preregistered; the quarter
  share is the minimal minority-protection fraction that covers the foundation's
  typical ≤3 proposals/turn while leaving ≥75% of capacity to search.
- Floors: `floor_F = min(|F|, R)`, `floor_G = min(|G|, K − R)`.
- Start from pure rank top-K. If a class is below its floor, displace the
  lowest-ranked selected items of the over-represented class with the highest-ranked
  unselected items of the under-represented class, until both floors hold.
- Final output keeps canonical rank order.

Consequences (by construction):

1. If pure rank top-K already satisfies both floors, output is **bit-identical** to
   the unreserved funnel (zero interference in uncongested turns).
2. Foundation keeps ≥ `min(|F|, R)` seats; experimental keeps ≥ `min(|G|, K−R)`.
3. No fabrication: only pre-existing items are selected; underflow backfills.
4. No commit implication: only evaluation/selection capacity is allocated.
5. Dominant items are never suppressed: displacement always removes the lowest-ranked
   selected items first, and floors never exceed available supply.
6. Deterministic: pure function of (ranked list, K, R, classifier).
7. Mechanism-agnostic: the allocator sees (class, rank) only; no family names.

## 3. Application sites (one mechanism, three rank truncations)

| # | Site | K | Ranking key (unchanged) |
|---|------|---|--------------------------|
| 1 | `OpportunityEngine.detect_opportunities` | `max_opportunities` (16) | `estimated_economic_relevance` desc |
| 2 | `OpportunityCandidateFunnel._stage_deterministic_top_k` (S9) | `max_exact_simulations` (8) | §31 tie-break hierarchy |
| 3 | `prune_patches` final cap | `max_candidates` (8) | pipeline order (post-META) |

Site 3 is included because META re-sorts by adjusted score between S9 and the final
cap, so crowding could otherwise re-emerge after S9. All sites are gated by a single
flag: `AECConfig.enable_funnel_reservation` (default **False**). When False, every
site executes its legacy path verbatim.

## 4. Untouched layers

Safety gates, macro probe, adaptive horizon, V3 continuation, WinModel hierarchy,
commit/abstain logic, quarantine gates, and V3 itself are not modified and not
bypassed. Reservation changes only *which* candidates reach simulation, never how
they are evaluated or committed.

## 5. Telemetry (per site, per turn)

```text
candidates_before, candidates_after, seats_k, reserved_seats_r,
foundation_available, general_available,
saved_by_reservation:   [{id, mechanism}],
displaced_by_reservation:[{id, mechanism, displaced_for_class}],
foundation_selected, general_selected,
funnel_saturation = before > k,
foundation_displacement_rate =
    foundation items displaced by reservation-or-rank / foundation items reaching funnel
```

Aggregated per turn into `AECTelemetry.funnel_reservation` and per seed by the Arm A
harness. Foundation-loss accounting additionally compares control commits against
treatment selection (see `PHASE018_ARM_A_RESULTS.md`).

## 6. Arm definition (isolation)

- **A0** — `build_robust_qualified_config()` (foundation control).
- **A1** — `build_phase015_treatment_config()` (diagnostic treatment, reservation off).
- **A2** — `build_phase018_arm_a2_config()` = A1 + `enable_funnel_reservation=True`.
  No quantity, trigger, representation, or evaluator change.

## 7. Success criteria (decision rules, preregistered)

1. Seed-249288 class failures: foundation opportunities reaching simulation in A2 on
   turns where A1 crowded them out (measured on fresh cohort, not by re-tuning 249288).
2. `foundation_displacement_rate` decreases A1 → A2 with no safety regression.
3. Terminal margin improves A1 → A2 without reducing total candidate quality
   (report both direct reservation benefit and reserved-slot opportunity cost).
4. Overall positive alpha is NOT required for Repair A to be architecturally adopted;
   funnel integrity + no harm is sufficient for infrastructure status.
