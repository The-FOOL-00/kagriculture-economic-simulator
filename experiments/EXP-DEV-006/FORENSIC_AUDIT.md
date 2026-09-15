# FORENSIC AUDIT: EXP-DEV-006 FRESH DISCOVERY
**Experiment**: EXP-DEV-006 (248000–248049, N=50, 200 games)
**Date**: 2026-09-14 (post-execution; treatment frozen throughout)
**Verdict**: **MECHANISM REPRODUCED — both fresh late-entry losses eliminated at zero observed cost.**

---

## A. All Losses (DEV-006 primary arm)

**Zero losses.** Minimum paired delta $0.00 across all 50 seeds.

## B. All Wins (DEV-006 primary arm)

| Seed | Paired Δ | m0 Δ | m1 Δ | First spec | Plan | DEV-005 Δ (same seed) |
|------|----------|------|------|------------|------|----------------------|
| 248002 | +$5,807 | +$5,807 | +$5,807 | Step 216 | YARN_SPECIALIZED | +$5,807 (identical) |
| 248029 | +$8,738 | +$8,738 | +$8,738 | Step 216 | YARN_SPECIALIZED | +$8,738 (identical) |

Both wins entered specialization at **Step 216** (remaining 504 ≥ 500 — guard cannot fire), after a Step-72 `REJECT_UNCONFIRMED` (YARN_STORE not yet revealed) and a quiet Step 144. Step-288 events are maintenance re-selections of the already-active YARN route. Both matches (seats) agree to the dollar. Trajectories (forensic_traces.json) show both arms byte-identical at every 12-step snapshot: an investment dip after entry (−$1,115/−$1,153 at step 288, −$4,826/−$3,578 at step 384) compounding into +$5,807/+$8,738 by game end. **Early-entry upside fully preserved.**

## C. All Specialization Events

- 184 `SPECIALIZE_CONFIRMED` decisions (DEV-006: 90, DEV-005: 94), **100% YARN_SPECIALIZED** — this cohort presented no eligible non-YARN route at any checkpoint.
- 168 `REJECT_UNCONFIRMED` (84/arm, identical sets), all with reason `REQUIRED_SHOP_NOT_UNLOCKED:YARN_STORE`.
- 444 `BASELINE` (222/arm, identical).
- The ONLY arm difference: 4 `REJECT_HORIZON` (DEV-006) replacing 4 `SPECIALIZE_CONFIRMED` (DEV-005) — see §D.
- All 26 at-step-288 DEV-006 `SPECIALIZE_CONFIRMED` verified as **maintenance** (an earlier specialize exists in the same seed×match); **zero new late entries** under the guard.

## D. All Horizon-Gate Rejections (4 events, 2 seeds)

| Seed | Match | Step | Blocked plan | Model expected value | Shops at 288 | Liquidity |
|------|-------|------|--------------|---------------------|--------------|-----------|
| 248007 | 0, 1 | 288 | YARN_SPECIALIZED | +$7,520.60 | SMOOTHIE_SHOP;BAKERY;FARMERS_MARKET;**YARN_STORE** | $14,991 |
| 248009 | 0, 1 | 288 | YARN_SPECIALIZED | +$5,919.68 | PIZZA_SHOP;SMOOTHIE_SHOP;ICE_CREAM_SHOP;**YARN_STORE** | $15,645 |

Both rejections: YARN_STORE revealed as the 4th shop at step 288; no eligible candidate at steps 72/144/216 (best plan BASELINE, value $0.00); first-time entry attempt with 432 steps remaining. Model predicted +$5.9k–$7.5k gains.

## E. Did the Guard Prevent Any Large Win?

**No.** Mechanism contrast (DEV-006 − DEV-005) minimum is $0.00 across all 50 seeds; no seed has DEV-006 < DEV-005. Both fresh wins were step-216 entries the guard structurally cannot block.

## F. Did the Guard Prevent Any Loss?

**Yes — both fresh DEV-005 losses, converted to exactly $0.00:**

| Seed | DEV-005 paired Δ | DEV-006 paired Δ | Recovered | First spec (DEV-005) |
|------|------------------|------------------|-----------|----------------------|
| 248007 | −$8,282 | $0.00 | +$8,282 | Step 288 (both seats) |
| 248009 | −$6,528 | $0.00 | +$6,528 | Step 288 (both seats) |

Total fresh-cohort recovery: **+$14,810** (+$296.20 mean). Money trajectories show the cascade: identical to baseline through step 288, then an investment dip that never recovers — a violent sawtooth (−$4,273 → −$7,349 → −$6,809 on 248007; −$7,737 → −$8,927 → −$6,160 on 248009) ending at −$8,282/−$6,528. Under DEV-006, money is **exactly baseline at every snapshot** ($0.00 difference at all 60 snapshots) — the guard restored bit-identical generalist play.

The model's +$5.9k/+$7.5k predictions vs −$6.5k/−$8.3k realizations (a ~$14k miss per seed) confirm the retrospective diagnosis: the valuation model cannot price the late-transition cascade, and the fixed horizon guard is the correct structural fix for this failure class.

## G. New Failure Modes

**None observed.** Zero DEV-006 losses; all 11 activated-tie seeds are exactly $0.00 in both matches and both arms (no hidden within-match offsets); liquidity healthy at all 800 checkpoints (min $142, zero below the $100 floor); no worker/liquidity/asset/market anomalies in telemetry. Worker under-service and terminal dead-inventory internals are not instrumented in this harness — no proxy (liquidity, expected values, match symmetry) indicates distress.

## H. Mechanism-Generalization Assessment (§15)

The fresh cohort reproduced the retrospective pattern almost exactly:

| Dimension | Retrospective (247xxx) | Fresh (248xxx) |
|-----------|------------------------|----------------|
| Late-entry losses (DEV-005) | 2 (step 288) | 2 (step 288) |
| Guard saves | 2 → $0.00 | 2 → $0.00 |
| Wins preserved | 5/5 | 2/2 |
| Other seeds bit-identical | 48/48 | 48/48 |
| New losses introduced | 0 | 0 |
| Prevented wins | 0 | 0 |

The retrospective result did **not** depend on the particular two seeds: on unseen seeds, the same class (first-time step-288 YARN entry on 4th-shop reveal) failed twice more, and the guard eliminated both again. Combined evidence: 4/4 late-entry losses eliminated, 7/7 wins preserved, 96/96 other seeds bit-identical, 0/100 new losses or prevented wins.

**Scope limits (honest)**: (1) N=2 fresh activations is still small — now 4 total across cohorts; (2) this cohort is 100% YARN — guard effects on BAKERY/PET/SMOOTHIE/PIZZA late entries remain untested; (3) primary mean (+$290.90, p=0.168, CI covers 0) is not statistically significant and is 100% top-2 concentrated (trimmed mean $0) — the strength of this result is the replicated loss-elimination mechanism, not the mean.
