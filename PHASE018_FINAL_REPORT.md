# PHASE018 — FINAL REPORT: Targeted Candidate-Funnel Repair

**Date**: 2026-09-19 | **Cohorts**: 5 fresh blocks, 50 seeds, 260 matches, all CRN-mirror
**V3**: `845e0d10…18943` verified before AND after (byte-identical)
**Tests**: 765/765 (714 baseline + 51 Phase018) | **Phase016**: untouched (0 diffs in `aec/counterfactual/`)

---

## 1. Primary question

> Can the remaining Phase015 opportunity family be made economically viable by
> repairing candidate construction and funnel interference while keeping the
> Phase016 macro-aware evaluator unchanged?

**Answer: No — not by these repairs.** Funnel interference was real, isolated,
and repaired (foundation selection restored 0→14 commits with experimental
search intact), but the repaired treatment remains deeply negative on every
fresh cohort (−$1,311 Arm A; −$1,228 B2; −$636 Arm C control legs all ≤2W/8L).
The residual loss sits in tranche-commit quality itself (what the evaluator
commits from whatever it evaluates), which candidate-side repairs cannot reach
without touching the evaluator — forbidden, and Phase017 proved the evaluator
correct (0% overblocking). Two repairs are adopted as flag-gated
infrastructure; Phase015 stays quarantined. **Outcome A (+ E for B/C/D).**

## 2. Failure-layer table (§41; effects are paired within-seed treatment−control)

| Repair | Cand/Sims | Commits | Mean Δ | 95% CI | W/L/T | Main effect | Safety | Status |
|---|---|---|---|---|---|---|---|---|
| P17 baseline | 6508/2082 | 54 | −$884.2 | [−$1,494,−$275] | 1/9/0 | — | 0 viol | baseline |
| A Reservation (A2−A1) | 6509/2069 | 50 | **+$49.3** | [−$1,+$100] | 4/2/4 | found 0→14, tranche 36=36 | 0 viol | **ADOPTED (gated)** |
| A2 Discrimination (S1−S0) | 5458/5342 | 64 | +$292.2 (med −$81) | [−$540,+$1,124] | 3/7/0 | 1,551 multi-sim turns | 0 viol | research-infra only |
| B Menu (S1B−S1) | 4734/4669 | 72 | −$279.9 (med +$81) | [−$1,018,+$458] | 8/2/0 | SAFE 0/220; tail −$3,636 | 0 viol | FALSIFIED |
| C1 Persistence | 6011/2038 | 46 | +$5.8 | [−$71,+$83] | 3/4/3 | −978 noise, null | 0 viol | REJECTED |
| C2 Premium floor | 6409/2160 | 44 | $0.0 (T10) | [0,0] | 0/0/10 | never bound (vacuous) | 0 viol | REJECTED |
| C3 Tape separation | 6065/2026 | 44 | −$68.1 | [−$146,+$10] | 1/4/5 | rank-reshuffle harm | 0 viol | REJECTED |
| Staged (§25, 6 states) | 24 CFs | — | 0/6 rescued | — | — | lump ≥ staged always | — | REJECTED (unbuilt) |
| Combination | — | — | not run | — | — | §26 bar unmet (sole qualifier) | — | NOT RUN (recorded) |

## 3. Funnel comparison (§42; per-arm treatment totals, 20 matches each)

|  | P17 | A1 | **A2** | S0 | **S1** | S1B | C0 |
|---|---|---|---|---|---|---|---|
| candidates | 6,508 | 6,651 | 6,509 | 6,593 | 5,458 | 4,734 | 6,409 |
| simulated | 2,082 | 2,093 | 2,069 | 2,104 | 5,342 | 4,669 | 2,160 |
| locally positive sims | 526 | 442 | 452 | 458 | 1,414 | 1,340 | 508 |
| escalated | 736 | 608 | 602 | 661 | 2,023 | 1,799 | 740 |
| safety-passing sims | 642 | 875 | 909 | 703 | 1,745 | 1,506 | 716 |
| committed | 54 | 36 | 50 | 69 | 64 | 72 | 44 |
| foundation commits | 2 | 0 | 14 | 6 | 6 | 6 | 4 |
| foundation lost (vs ctrl) | — | 14 | 0 | — | — | — | — |
| positive-terminal seeds | 1 | 1 | 1 | 0 | 0 | 0 | 2 |

The bottleneck moves visibly: A fixes foundation *selection*; A2 fixes *evaluation
breadth* (sims 2.1k→5.3k); but commits stay 36–72 with ≤2 winning seeds — the
evaluator's commit set from any funnel is uneconomic. The constraint is
opportunity/commit quality, no longer funnel throughput.

## 4. The six scientific conclusions (§43)

1. **Did reservation solve crowding?** Yes at mechanism level (within-turn saves
   in 20/20 matches; 249288 step-649 selection repaired; fresh-cohort 0→14
   commits with tranche search intact). Terminal effect small (+$49.3) because
   treatment's own-farm foundation value is small — restoring selection is
   necessary, not sufficient.
2. **Did boundary-safe quantities recover opportunities?** No. Menu falsified:
   safe anchors sub-hurdle by construction (median +$7 vs $15–20 hurdles, 0/220
   commits); typical +$81 is reorder artifact; inexpressive tail −$3,636
   (missing large anchor). B1-as-ordered was additionally untestable (S7 ate it).
3. **Did trigger timing matter?** No. Noise is real (48.7k evals, median edge
   ≈$0) but already-neutralized downstream: gating it is null (C1), vacuous
   (C2), or harmful via selection reshuffle (C3). Trigger is not the failure layer.
4. **Is staged execution required?** No (0/6 diagnostic; lump ≥ staged; feed-hole
   economics invariant to splitting). Machinery not built.
5. **Does any isolated repair produce positive fresh paired evidence?** Weakly:
   reservation +$49.3 (CI touches 0); discrimination mean +$292 but median −$81
   (outlier-driven). Neither is robust positive alpha; both are infrastructure.
6. **Does repaired Phase015 merit formal qualification?** **No.** Every repaired
   treatment leg remains ≤2W/8L with means −$600 to −$1,400. Phase015 stays
   quarantined; live foundation unchanged.

## 5. Secondary discoveries (binding for future work)

- **S7 collapse** (new): all market patches shared one dominance group → max 1
  sim/turn over 6,384 turns. The K=8 budgets never bound before A2. Any future
  generator work MUST run under discrimination (or equivalent) to be testable.
- **Winner's curse under multi-eval**: max-select among noisy sim estimates picks
  worse commits than the collapse's conservative single-filter (typical −$81).
  Future selection needs uncertainty-aware commit rules, not more candidates.
- **Significance-hurdle wall**: near-gate safe quantities (≈+$7) cannot clear
  $15–20 WinModel hurdles. Boundary-avoidance and economic significance are in
  direct tension for small sales.
- **Funnel-interaction caveat**: B/C effects were measured under specific funnel
  regimes (B1 under collapse, C under legacy); combining regimes needs re-validation.

## 6. Adopted output (flag-gated, default-off, live foundation untouched)

1. `enable_funnel_reservation` — class-floor allocation at 3 truncation sites;
   standard for mixed foundation+experimental research arms.
2. `enable_market_patch_discrimination` — S7 exemption + relevance S9 + priority
   stamping; required test infrastructure for any generator research.
3. Firing-log + trigger-gate telemetry; boundary-projection helpers (diagnostic use).

## 7. Governance

V3 SHA `845e0d10…18943` verified pre/post; `aec/counterfactual/` zero-diff;
all pilots on fresh seeds (249296–249335 + 249336+ untouched reserve; protected
and consumed cohorts never touched); 765/765 tests; every arm preregistered
(specs/audits/analyses written before data; two pre-execution
corrections documented: B1 order rationale, C2 premium basis); all thresholds
architecture-derived; no post-hoc tuning; Phase015 quarantine intact.
