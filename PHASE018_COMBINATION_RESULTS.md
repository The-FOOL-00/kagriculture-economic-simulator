# PHASE018 — COMBINATION STAGE: DECISION RECORD

**Status**: NO COMBINATION ARM — §26 bar not met (documented, not skipped)
**Date**: 2026-09-19

---

## 1. Rule (§26)

Combine at most interventions satisfying ALL of: (1) causal improvement,
(2) safety preservation, (3) no evaluator degradation, (4) clear
mechanism-level justification, (5) manageable runtime.

## 2. Scorecard

| Intervention | (1) Improvement | (2) Safety | (3) Evaluator | (4) Mechanism | (5) Runtime | Qualifies |
|---|---|---|---|---|---|---|
| Reservation (A) | WEAK +$49.3, CI touches 0; mechanism 0→14 strong | ✓ 0 viol | ✓ intact | ✓ crowding | ✓ same | **YES (sole)** |
| Discrimination (A2) | ✗ typical −$81 (mean +$292 outlier-driven) | ✓ 0 viol | ✓ intact | ✓ multi-eval | ✓ +7% | NO (fails 1) |
| Boundary menu (B) | ✗ −$279.9; SAFE 0/220; tail −$3,636 | ✓ 0 viol | ✓ intact | ✗ recomposition artifact | ✓ same | NO (fails 1, 4) |
| Trigger C1 | ✗ +$5.8 null | ✓ | ✓ | ✓ (noise cut, no effect) | ✓ | NO (fails 1) |
| Trigger C2 | ✗ exactly $0 (vacuous) | ✓ | ✓ | — | ✓ | NO (fails 1) |
| Trigger C3 | ✗ −$68.1 | ✓ | ✓ | ✗ reshuffle harm | ✓ | NO (fails 1, 4) |
| Staged exec | ✗ 0/6 diagnostic | — (unbuilt) | — | ✗ | — | NO |

Only ONE intervention qualifies. A "combination" of one is Arm A, already run.
No second member exists; any multi-member arm would violate §26 (combining
non-improvers to fish for positivity) and §33F.

## 3. Considered and rejected

- **Reservation + discrimination** ("full funnel repair"): tempting as
  infrastructure, but discrimination fails the economics bar (typical −$81);
  combining it cannot be justified as improvement-seeking. The open question it
  would answer (do Repair A's S9/prune sites matter under multi-eval?) is
  recorded as future work, not a Phase018 arm.
- **Reservation + C1**: C1 is null (+$5.8); adding a null cannot improve D over
  A2 alone, and would consume a fresh cohort to re-prove the null.
- **Menu + large anchor (B1')**: a NEW design requiring its own preregistration
  (Outcome B follow-up), not a combination of validated parts.

## 4. Decision

**No ARM D. No combination pilot. No fresh cohort consumed.** The phase's
adoptable output is two flag-gated infrastructure pieces (reservation,
discrimination-for-research) validated in isolation. Final synthesis in
`PHASE018_FINAL_REPORT.md`.
