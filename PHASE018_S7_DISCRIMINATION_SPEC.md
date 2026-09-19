# PHASE018 — S7/S9 MARKET-PATCH DISCRIMINATION SPEC (Repair A2, preregistered)

**Status**: PREREGISTERED (before Arm B2 execution)
**Date**: 2026-09-19
**Scope**: funnel S7 grouping + S9 ranking for market patches + generator priority
stamping + B1 menu order. No evaluator, probe, safety, WinModel, trigger, or V3
change. B1 menu *contents* (Q_SMALL/Q_CURRENT/BOUNDARY_SAFE/MINUS) are unchanged
from `PHASE018_QUANTITY_CONSTRUCTION_SPEC.md`; only emission order changes.

---

## 1. Blocking defect (proven from ledgers + code, independent of Arm B's sign)

Across 6,384 simulated turns (Phase017 2,082 + Arm B 4,302), **max sims/turn = 1**,
never 2; zero turns with >1 tranche sim; zero turns with tranche + market-timing
sims. Mechanism:

- S7 groups by `(worker_id, target_pos)`. `CoupledPatch` defines neither attr, so
  ALL market patches (every family, commodity, quantity) share one group.
- S7's value keys (`estimated_economic_value/relevance/net_delta`) are all 0 on
  patches (relevance lives only on opportunities, never propagated), so the
  within-group sort is a stable no-op → **input-first survives, rest die**.
- Consequence: the effective sim budget is 1/turn by accident (not the designed
  K=8); B1's menu never reached evaluation (B1 ≡ forced-q1: 100% of B1 tranche
  sims were `Q_SMALL`); S9/prune reservation sites are vacuous (≤1 patch arrives).

Arm B's B1−B0 = −$75.8 therefore measures "forced-q1 vs legacy-first-anchor",
NOT boundary-safe construction. Repair B is **untestable** until S7 discriminates.
This repair (A2, funnel family) unblocks the retest. It is motivated by the S7
mechanism proof, not tuned to B1's outcome sign.

## 2. Repair A2 design (gated by `enable_market_patch_discrimination`, default OFF)

### 2.1 Generator priority stamping (always on; inert metadata when A2 off)

`PatchGenerator` stamps every emitted patch: `source_relevance` (source
opportunity's `estimated_economic_relevance`) and `anchor_index` (per-opportunity
emission sequence). Proven inert when A2 off: legacy S7/S9 keys ignore both attrs
(unit-verified legacy equivalence).

### 2.2 S7 market-patch exemption (only when A2 on)

A candidate is a market patch iff `market_mutations is not None` and
`worker_mutations` is empty. Market patches are exempt from (worker, target)
dominance collapse: each forms its own S7 group (pass-through). Rationale: same
worker+target dominance is meaningful for worker tasks (one worker, one task —
`test_int_05` preserved exactly) but meaningless across distinct market actions,
whose size⇆macro tradeoff only the evaluator can judge. Worker/task patches and
opportunities: legacy S7 verbatim. Exempt count recorded in S7 telemetry.

### 2.3 S9 patch-aware ranking (only when A2 on)

Rank key becomes `(source_relevance desc, anchor_index asc, family, wid, pos,
step, patch_id)` with relevance falling back through legacy value attrs (so
unstamped patches and opportunities rank exactly as before). This restores the
architect's intent (rank by economic promise, keep designed top-K=8) instead of
the all-zero → patch_id-alphabetical lottery. Deterministic. Legacy key verbatim
when A2 off.

### 2.4 B1 menu emission order (revised, rationale preregistered)

Within a commodity, S9 consumes anchors in emission order when slots are tight, so
order = search priority. Most-committable-first: when a boundary binds,
`[BOUNDARY_SAFE, Q_CURRENT, BOUNDARY_MINUS, Q_SMALL]` (SAFE = max value without
cross; CURRENT = legacy continuity incl. possibly-benign cross; MINUS =
conservative; SMALL = least value; sim cost is size-independent so value-first
dominates). When no boundary binds: `[Q_CURRENT, Q_SMALL]` (legacy value order).
Rationale derives from Phase017's 97.6% escalated-reject rate (crossers usually
waste their sim), not from Arm B outcomes.

## 3. Arm B2 definition (isolation; fresh cohort 249316..249325)

- **S0** — treatment-A1 vs control-A0, legacy funnel (replicates B0vA0; sanity).
- **S1** — treatment-A1 vs control-A0-discrimination-ON... precisely: BOTH sides
  `enable_market_patch_discrimination=True`, legacy quantities.
  S1−S0 (paired within seed/seat) = joint funnel-discrimination effect.
- **S1B** — treatment-B1 (discrimination + boundary menu) vs same S1 control.
  S1B−S1 = boundary-menu effect under a working funnel (the true Repair B test;
  control config identical across S1/S1B, so the menu flag isolates cleanly).

Reservation OFF in all B2 legs (orthogonal infrastructure; combination later iff
justified). 60 matches total. Per-turn latency persisted; sims/turn distribution
reported (explosion guardrail: mean sims/turn must stay ≤ designed K=8 — by
construction — and match elapsed must stay operationally bounded).

## 4. Success criteria (preregistered)

1. S7 exemption observable: turns with >1 sim exist; tranche + market-timing sims
   co-occur; BOUNDARY_SAFE/MINUS anchors reach simulation (menu testable).
2. No candidate-count explosion: generated/turn unchanged (generator untouched in
   volume); sims/turn ≤ 8 always.
3. S1−S0 reported with CI (discrimination may help, hurt, or be neutral — any
   sign is informative; adoption needs §33 A–F).
4. S1B−S1: the isolated boundary-menu effect. Positive + safe → Repair B viable;
   neutral/negative → Repair B falsified (Outcome E for B).
5. Zero safety violations in all legs; evaluator code untouched (regime mix
   reported for stability).
