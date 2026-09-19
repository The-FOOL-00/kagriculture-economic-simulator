# PHASE018 — ARM B RESULTS (Boundary-Safe Quantities + S7 Discrimination Retest)

**Status**: COMPLETE
**Date**: 2026-09-19
**Designs**: `PHASE018_QUANTITY_CONSTRUCTION_SPEC.md`, `PHASE018_S7_DISCRIMINATION_SPEC.md`
**Cohorts**: Arm B fresh `249306..249315` (40 matches); Arm B2 fresh `249316..249325` (60 matches)

---

## 1. Arm B (B0/B1): menu untestable under the collapsed funnel

| Arm | Mean | Std | 95% CI | W/L/T |
|---|---|---|---|---|
| B0vA0 | -$1,312.0 | 2302.8 | [-$2,739.2, +$115.3] | 3/7/0 |
| B1vA0 | -$1,387.8 | 2245.5 | [-$2,779.5, +$4.0] | 1/9/0 |
| **B1−B0** | **-$75.8** | 157.7 | [-$173.5, +$21.9] | 2/8/0 |

Mechanism forensics overturned the naive reading: B1 simulated **100% q=1**
(1,898/1,898 `Q_SMALL`); `Q_CURRENT`/`BOUNDARY_SAFE`/`BOUNDARY_MINUS` never
reached simulation. Root cause — **S7 dominance collapse** (proven from ledgers +
code, independent of B1's sign): S7 groups by `(worker_id, target_pos)`, which
`CoupledPatch` never defines, so ALL market patches share one group with all-zero
value keys → stable-sort keeps input-first only. Ledger proof: **max sims/turn =
1 over 6,384 simulated turns** (Phase017 2,082 + Arm B 4,302), zero turns with
>1 tranche sim, zero tranche+market-timing co-sims. The designed K=8 budget never
bound; the effective budget was 1/turn by accident. B1−B0 = −$75.8 therefore
measures "forced-q1 vs legacy-first-anchor", NOT boundary-safe construction.
**B1-as-ordered is rejected; Repair B declared untestable-under-collapse (not
yet falsified).** Zero unsafe commits; latency identical (mean 148.6 vs 148.9 ms).

## 2. Arm B2 (S0/S1/S1B): discrimination + identical-menu retest

S0 = legacy funnel replication; S1 = +discrimination (legacy qty); S1B =
+discrimination + B1 menu (contents identical; emission order preregistered
most-committable-first). Reservation OFF all legs. Control configs matched per
leg (S1/S1B controls run discrimination; control commits identical 18/18/18 —
the S1−S0 effect is purely treatment-side).

| Contrast | Mean | 95% CI | W/L/T | Median | Ex-249318 mean |
|---|---|---|---|---|---|
| S0 | -$1,240.0 | [-$2,249.3, -$230.8] | 0/10/0 | — | — |
| S1 | -$947.8 | [-$1,778.4, -$117.2] | 0/10/0 | — | — |
| S1B | -$1,227.7 | [-$2,192.1, -$263.3] | 0/10/0 | — | — |
| **S1−S0 (discrimination)** | **+$292.2** | [-$539.8, +$1,124.3] | 3/7/0 | **-$81.5** | -$130.3 (W2/L7) |
| **S1B−S1 (menu)** | **-$279.9** | [-$1,018.2, +$458.4] | 8/2/0 | **+$81.5** | +$93.0 (W8/L1) |

### 2.1 Criterion 1 (observability): PASS

S0: 0 multi-sim turns (collapse replicated ✓). S1: **1,551 multi-sim turns**
(sims/turn up to the designed 8; 10 tranche+market-timing co-sims); the full
legacy menu reaches simulation (quantities 1–65; DEPTH/FULL/STORAGE/TERMINAL
reasons). S1B: `BOUNDARY_SAFE` simulated 220× (menu testable ✓;
`BOUNDARY_MINUS` 0× — anchor-index 2 rarely makes S9 top-8). No explosion:
generated/turn unchanged; sims/turn ≤ 8 always; latency +7% mean (155.7→166.5),
p95 +9% (414→450), max 1.6 s single turn. Zero unsafe commits all legs (205
commits). Evaluator code untouched; escalation 31.4%→37.9%→38.5% (busier, same
regime kinds).

### 2.2 Seed 249318 (both seats identical): the ±$4k outlier

- S0 (−$4,252): 7 commits incl. terminal q5 dribble at 674/675/676.
- S1 (−$156): 3 commits; step-677 `FULL_UNCOMMITTED q17` (sim +$305) replaced
  the dribble → near-parity. Discrimination unlocked the right large action.
- S1B (−$3,792): B1 menu has NO large anchor (DEPTH/FULL dropped per spec), so
  step 677 sold q5 (sim +$104) instead of q17 → catastrophic divergence.
  The spec's anticipated risk ("value destruction from their absence") materialized.

### 2.3 Why the menu typically helped yet is still rejected

Ex-249318 menu effect is +$93 (W8/L1, median +$81.5) — but **zero of 220 SAFE
sims committed**. SAFE sims: 98% escalated (mostly material-shift/proximity, not
gate-cross — the projection works), 79% favorable, yet **median final_delta
+$7** — below every WinModel hurdle ($15 margin / $20 cash / p_win gain). Safe
quantities near gates are small by construction, hence economically
insignificant by construction. The typical +$81 came from commit-stream
recomposition (fewer, reordered anchors → different S9 winners), not from
safe-anchor value — a reorder artifact without mechanism-level justification,
which §26 forbids combining. Combined with the −$3,636 inexpressive-menu tail:
**the boundary-value theory is falsified as implemented.**

## 3. Success-criteria verdicts

**Repair A2 (discrimination)**: A (causal mechanism ✓ — 1,551 multi-sim turns),
B (funnel integrity ✓ — designed K=8 restored), C (safety ✓ — 0 violations),
D (evaluator intact ✓), E (runtime bounded ✓ — +7%), F (economics ✗ — typical
−$81; winner's-curse among noisy sim estimates). **Adopted as flag-gated
RESEARCH infrastructure** (generator work is untestable without it); NOT a live
behavior change (typical economics negative).

**Repair B (boundary menu)**: mechanism testable ✓, but effect −$279.9 mean
(tail-dominated), typical +$81 without mechanism justification, SAFE 0/220
commits (sub-hurdle by construction), catastrophic inexpressive tail.
**FALSIFIED as a value-recovery mechanism (Outcome E for B).** Not adopted, not
combined. Follow-up direction (Outcome B): any future quantity work must keep a
large/terminal-expressive anchor and confront the significance-hurdle problem —
a new preregistration, not a Phase018 extension.

## 4. Implication for Arm C

Arm C runs under the **legacy funnel exactly as preregistered/implemented** (no
post-hoc protocol change): C-leg builders verified single-flag diffs from the
A1 base. Funnel-interaction caveat (C effects measured under legacy funnel; any
combination re-verifies under adopted infra) is recorded for the final report.
