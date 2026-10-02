# PHASE018 — ARM C RESULTS (Trigger Timing, isolated)

**Status**: COMPLETE
**Date**: 2026-09-19
**Design**: `PHASE018_TRIGGER_TIMING_AUDIT.md` §3–§5 (preregistered; C2 corrected
pre-execution from relevance to premium with documented rationale)
**Cohort**: fresh seeds `249326..249335` (10 seeds × 2 seats × 4 legs = 80 matches,
legacy funnel all legs, common A0 control)

---

## 1. Headline economics (paired margin vs C0)

| Contrast | Mean | Std | 95% CI | W/L/T |
|---|---|---|---|---|
| C0 (current trigger) | -$635.5 | 931.4 | [-$1,212.8, -$58.2] | 2/8/0 |
| C1−C0 (persistence) | **+$5.8** | 123.7 | [-$70.9, +$82.5] | 3/4/3 |
| C2−C0 ($15 premium floor) | **$0.0** | 0.0 | [$0.0, $0.0] | 0/0/10 |
| C3−C0 (tape separation) | **-$68.1** | 126.3 | [-$146.4, +$10.2] | 1/4/5 |

Per-seed C0/C1/C2/C3: 249326 −2626/−2631/−2626/−2626; 249327 +406/+406/+406/+78;
249328 −72 all; 249329 −1781/−1485/−1781/−1781; 249330 −80 all; 249331
+135/+93/+135/+93; 249332 −648/−603/−648/−713; 249333 −388/−427/−388/−388;
249334 −361/−346/−361/−332; 249335 −940/−1152/−940/−1215.

## 2. Firing funnel (§32; 48,656 evaluations/leg)

| Leg | Emitted | Class A | B (term) | D (sat) | C (liq) | F (coup) | C-supp. |
|---|---|---|---|---|---|---|---|
| C0 | 4,186 | 1,062 | 2,460 | 594 | 60 | 10 | 0 |
| C1 | 3,958 | 826 (−22%) | 2,476 | 586 | 60 | 10 | 978 C1 |
| C2 | 4,186 | 1,062 (same) | 2,460 | 594 | 60 | 10 | 0 |
| C3 | 4,010 | 840 (−21%) | 2,512 | 588 | 60 | 10 | 488 C3 |

Candidates/sims/commits: C0 6409/2160/44; C1 6011/2038/46; C2 identical to C0;
C3 6065/2026/44 (commit mix 40 tranche + 4 market-timing in C0/C2/C3; 42+4 in
C1). Zero unsafe commits all legs. B–F firing counts stable up to ±2%
trajectory drift (gates are Class-A-only by construction, unit-verified) —
scope integrity holds. Class-A qty_held median 12 (min 3, max 124): single-unit
firings come only from distress classes, as statically predicted.

## 3. Variant verdicts

- **C1 (persistence)**: mechanically effective (978 noise firings removed, zero
  commit loss: 44→46) but terminally null (+$5.8, CI centered on 0). The
  suppressed first-observation firings were pure noise whose absence promotes
  nothing better. Informative null: Class-A noise is already harmless.
- **C2 (premium floor)**: exactly $0.0 on all 10 seeds — the $15 floor NEVER
  bound (every Class-A firing carried premium ≥ $15; floor sits below the
  empirical premium support). Vacuous, not failed: provides no evidence.
  Not adoptable (no-op).
- **C3 (tape separation)**: −$68.1 (harmful-neutral). 488 suppressions, identical
  commit counts (44), yet worse margins via commit-stream recomposition: under
  the collapsed 1-sim/turn funnel, removing a Class-A opportunity promotes a
  lower-relevance opportunity to the single evaluated slot (S7 order-lottery) —
  suppression reshuffles which noise gets evaluated. Not lost opportunity
  (counts identical); worse selection luck. Not adoptable.

## 4. Success criteria (§5 of audit)

1. Fewer zero-edge firings without lost commits: C1 ✓ (978 fewer, 44→46).
2. Terminal improvement: all three ✗ (null / vacuous / negative).
3. B–F scope integrity: ✓ (Class-A-only gating verified).

## 5. Answer to Q3 (trigger timing)

The trigger DOES fire noisily (8.6% emission from 48.7k evaluations; median
Class-A local edge ≈ $0 from Phase017 patterns), but gating the noise changes
nothing (C1) or backfires through selection reshuffle (C3): the funnel +
evaluator already neutralize firing noise. **Trigger timing is NOT the economic
failure layer.** The residual failure is downstream — which single candidate the
collapsed funnel evaluates and which evaluated candidates the (imperfect)
evaluator commits. Repair C: no variant adoptable, none combinable. Interaction
caveat (as with B): C-gates might behave differently under multi-evaluation
discrimination (suppression would free sim slots rather than reshuffle a 1-slot
lottery) — untested; the preregistered legacy-funnel results stand.
