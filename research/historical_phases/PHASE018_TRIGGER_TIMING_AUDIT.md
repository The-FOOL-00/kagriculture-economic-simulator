# PHASE018 — ASSET-HOLDING TRIGGER TIMING AUDIT (Repair C)

**Status**: STATIC AUDIT + PREREGISTERED MATRIX (Arm C results PENDING)
**Date**: 2026-09-19
**Scope**: `ASSET_HOLDING_VALUATION_TRIGGER` firing rules only. No quantity,
evaluator, safety, or reservation change in Arm C.

---

## 1. Static threshold audit (from `aec/opportunities/asset_holding.py`)

| Class | Firing rule | Distress-driven? |
|---|---|---|
| A FAVOURABLE_MARKET_HOLDING | (ratio ≥ 1.15 & qty ≥ 3) or (ratio ≥ 1.10 & qty ≥ 10); deferred if baseline already sells c | No — gain-seeking |
| B TERMINAL_HOLDING_RISK | runway ≤ 68 & qty > 0 | Yes (qty ≥ 1 fires) |
| C LIQUIDITY_HOLDING_CONFLICT | deficit > 0 & qty > 0 & ratio ≥ 0.85 | Yes (qty ≥ 1 fires) |
| D MARKET_SATURATION_RISK | storage ≥ 70% & falling & qty ≥ 5 | Yes |
| E OPPONENT_PRESSURE | rival ≤ 3 & qty > 0 & ratio ≥ 0.95 | Yes (qty ≥ 1 fires) |
| F DEPENDENCY_COUPLED_HOLDING | storage ≥ 80% & qty ≥ 10 & ratio ≥ 0.95 | Yes |

Single-unit (q=1) synthesis can only originate from classes B, C, or E (A needs
qty ≥ 3, D needs ≥ 5, F needs ≥ 10). "Fires when one unit appears" is therefore
a property of the *distress* classes firing on any positive holding — Class A is
never a first-unit trigger.

## 2. Ledger patterns (existing `results/PHASE017_ATTRIBUTION_LEDGER.csv`, no new sims)

- Simulated tranche firings by episode phase: EARLY(<288) 148, MID 226, LATE 608,
  TERM(650+) 850. q=1 spread across all phases (62/56/90/182) — not terminal-only.
- Local-delta distribution: q=1 median **$0** (p75 $0); q=5 median $0 (p75 +$8).
  Most firings carry zero measurable local edge — candidate-volume without value.
- Commits by phase: EARLY **0**, MID 12, LATE 14, TERM 26. All 148 early-game
  simulations produced zero commits: early firing is currently pure funnel cost.
- Escalation rate peaks LATE (59.5%) around capex/feed boundaries.

These patterns motivate — but do not tune — the preregistered matrix below. All
thresholds derive from existing architecture, fixed before Arm C execution.

## 3. Preregistered variant matrix (fixed before Arm C)

All variants scope the added gate to **Class A only**. Rationale: B–F are
event-driven distress detectors (terminal clock, wage deficit, rival proximity,
shed state); gating them risks killing valid rescues. Class A is the
gain-seeking impulsive leg and the correct minimal repair surface. Cross-class
firing counts are reported to verify B–F are unaffected.

- **C0** — current trigger (all classes as-is). Control leg.
- **C1 (persistence)** — Class A emits only if the same commodity fingerprint
  (commodity + price_band + terminal_phase) evaluated favorable on **≥ 2
  consecutive turns**. N=2 is the minimal persistence: single-observation spikes
  are noise; the fingerprint bands already quantize state so repeats are
  structurally identical.
- **C2 (economic significance)** — Class A requires raw premium
  `(price − base) × qty` ≥ **$15.00**, the established sub-hurdle (Phase017 O2/O3:
  <$15 deltas; WinModel $15 margins). Filters price-flicker firings with no
  meaningful premium.
  - *Pre-execution correction (before Arm C, no data seen)*: the gate applies to
    the raw premium, not the padded `max(20, premium)` relevance accessor — a
    relevance floor ≤ $20 would be vacuous since every Class A firing reports
    relevance ≥ $20. Intent (significance filtering) unchanged.
- **C3 (V3-schedule separation)** — Class A suppressed when V3's own tape
  (`future_trajectory`) contains a SELL of the same commodity within the next
  **2 turns** (V3 `advance_sales` horizon, architecture-derived). Front-running
  V3's native liquidation by ≤2 turns captures ≈$2–10 while incurring concessions
  (Phase017 §7.1); separation removes pure-duplicate firing.

Implementation notes (preregistered): config flags `enable_trigger_persistence`,
`trigger_min_premium_class_a` (None = off), `enable_tape_separation`; tape
passed as an optional kwarg through `detect_opportunities` (C3 inactive when no
tape is supplied); opt-in per-turn firing log (commodity, class, qty, price,
ratio, trajectory, step, decision, suppression reason) for §32 metrics. No other
trigger semantics change; deduplication (`record_counterfactual_outcome`) stays.

## 4. Arm definition (isolation)

- **C0-leg** = A1 (`build_phase015_treatment_config()`), re-run on the fresh
  cohort as the within-phase control leg.
- **C1/C2/C3-legs** = C0-leg + exactly one variant flag each. Reservation OFF,
  quantities legacy, evaluator unchanged. Variants are tested independently, never
  stacked in the pilot.

## 5. Success criteria (preregistered)

1. Variant reduces zero-edge firings (firing count down) while committing ≥ the
   C0-leg's economically meaningful commits (no lost-opportunity regression —
   report firings, valid misses, terminal economics per §23).
2. Terminal margin improves vs C0-leg with zero safety violations.
3. B–F class firing counts unchanged (scope integrity).

## 6. Arm C results

See `PHASE018_ARM_C_RESULTS.md` (full report). Summary: C1 +$5.8 null (978 noise
firings removed, no effect); C2 exactly $0.0 (floor never bound — vacuous); C3
−$68.1 (suppression reshuffles the collapsed-funnel order-lottery). No variant
adoptable. The matrix above was frozen before execution and is unchanged.
