# FORENSIC AUDIT: EXP-DEV-006 QUALIFICATION
**Experiment**: EXP-DEV-006 Qualification (50050–50099, N=50, 200 games)
**Date**: 2026-09-14 (post-execution; treatment frozen throughout)
**Verdict**: **GUARD INERT — ZERO NEW LATE ENTRIES IN EITHER ARM; DEV-006 ≡ DEV-005 ON ALL 50 SEEDS.
ZERO LOSSES, ZERO NEW FAILURE MODES, THREE EARLY-ENTRY WINS WITH CLEAN TRAJECTORIES.**

---

## A. All Losses (DEV-006 primary arm)

**Zero losses.** Minimum paired delta $0.00 across all 50 seeds (tail gate: $0.00 ≥ −$800.00 PASS).
No loss-level forensic trace is applicable; the prevented-loss class did not occur in this cohort.

## B. All Wins (DEV-006 primary arm — 3 seeds, all with full traces)

| Seed | Paired Δ | m0 Δ | m1 Δ | First spec | Plan | DEV-005 Δ (same seed) |
|------|----------|------|------|------------|------|----------------------|
| 50059 | +$7,888 | +$7,888 | +$7,888 | Step 216 | YARN_SPECIALIZED | +$7,888 (identical) |
| 50069 | +$8,110 | +$8,110 | +$8,110 | Step 216 | YARN_SPECIALIZED | +$8,110 (identical) |
| 50091 | +$9,881 | +$9,881 | +$9,881 | Step 216 | YARN_SPECIALIZED | +$9,881 (identical) |

All three wins entered specialization at **Step 216** (remaining 504 ≥ 500 — the guard structurally
cannot fire), confirmed-shop gated on YARN_STORE. Both matches (seats) agree to the dollar; both
arms are byte-identical at every 12-step snapshot (`QUALIFICATION_FORENSIC_TRACES.json`, 12 games).

Money trajectories (DEV-006 minus baseline) show the healthy early-entry compounding shape with no
hidden artifact:

| Seed | @216 | @288 | @384 | @480 | @576 | @672 | Final |
|------|------|------|------|------|------|------|-------|
| 50059 | $0 | −$1,584 | −$5,117 | +$1,943 | +$3,250 | +$7,024 | +$7,888 |
| 50069 | $0 | −$1,584 | −$5,133 | +$2,130 | +$3,304 | +$7,156 | +$8,110 |
| 50091 | $0 | −$1,171 | −$1,916 | +$4,992 | +$4,706 | +$8,998 | +$9,881 |

Identical to baseline through step 216, a bounded investment dip, then smooth compounding into the
win — the same shape as the Discovery wins. Terminal money equals reward exactly in all traced games
(cand and base), so there is no hidden terminal-inventory wedge at the observable layer. The
observation schema exposes only `money` per farm at terminal state; finer inventory breakdowns and
worker/animal/service starvation flags are not instrumented in this harness (same scope limit as
Discovery) — no proxy (liquidity, expected values, match symmetry) indicates distress.

## C. All Specialization Events

- 228 `SPECIALIZE_CONFIRMED` decisions (DEV-006: 114, DEV-005: 114 — identical sets),
  **100% YARN_SPECIALIZED** — this cohort presented no eligible non-YARN route at any checkpoint.
- 200 `REJECT_UNCONFIRMED` (100/arm, identical sets), all `REQUIRED_SHOP_NOT_UNLOCKED:YARN_STORE`.
- 372 `BASELINE` (186/arm, identical).
- 0 `REJECT_HORIZON` in either arm. The arms are event-identical across all 800 checkpoint decisions.
- All 68 at-step-288 `SPECIALIZE_CONFIRMED` (34/arm) verified as **maintenance** (an earlier
  specialize exists in the same seed×match); **zero new late entries** in either arm. The late-entry
  failure class the guard targets did not arise on this cohort.

## D. All Horizon-Gate Rejections

**None.** `QUALIFICATION_HORIZON_GUARD_EVENTS.csv` contains 0 rows. The guard was inert because no
game in either arm attempted a first-time step-288 entry — there was nothing to block.

## E. Did the Guard Prevent Any Large Win?

**No — vacuously, and verified.** Mechanism contrast (DEV-006 − DEV-005) is exactly $0.00 on all 50
seeds (min $0.00, max $0.00, 50 ties). All three wins were step-216 entries the guard structurally
cannot block.

## F. Did the Guard Prevent Any Loss?

**Not on this cohort — no losses occurred in either arm to prevent.** DEV-005 diagnostic:
3W/0L/47T, identical numbers to DEV-006. Combined cross-cohort evidence stands at 4/4 historical
late-entry losses eliminated (retrospective 2 + Discovery 2), with 0 additional tests on this cohort.

## G. Activated Ties and New Failure Modes

- 17 activated seeds per arm (identical sets); 14 are activated ties, all exactly $0.00 in both
  matches and both arms — no hidden within-match offsets.
- Liquidity healthy at all 800 checkpoints (min $142, zero below the $100 floor).
- **No new failure mode observed.** Zero DEV-006 losses; zero contrast with DEV-005 anywhere.

## H. Mechanism Assessment (§B of the frozen gates)

The mechanism was **not replicated** on this cohort because its trigger condition never occurred:
zero first-time step-288 entry attempts in 200 games. This is a Category-C-like inert outcome for
the mechanism gate — it neither confirms nor refutes the guard. It does confirm, for the third
consecutive cohort, that the guard carries zero observed cost (no prevented wins, no new losses,
no behavior change where it does not fire).
