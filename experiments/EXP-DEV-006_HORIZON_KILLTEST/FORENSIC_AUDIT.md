# EXP-DEV-006 FORENSIC AUDIT — Horizon-Gate Mechanism Analysis

**Experiment**: EXP-DEV-006_HORIZON_KILLTEST (retrospective mechanism test)
**Cohort**: 247000–247049 (consumed DEV-005 Discovery partition ONLY)
**Date**: 2026-09-14
**Sources**: frozen `experiments/EXP-DEV-005/` telemetry (`RAW_RESULTS.json`,
`DECISION_EVENTS.csv` — 400 events, `SPECIALIZATION_EVENTS.csv`),
`candidates/compiled_v54_plus_residual.py` (SHA `18402ec6…`),
`candidates/closed_loop_architecture/dev_005_confirmed_shop_scheduler.py`
(SHA `f52b1686…`), route-tape decodes, bundled policy-module decodes,
kill-test execution (`RAW_RESULTS.json`, 200 games), and instrumented
counterfactual replays (`port/trace_losses.py` → `port/loss_seed_traces.json`).
No quarantined partition was touched. Claims are labeled OBSERVED (frozen
telemetry), DERIVED (exact code/tape analysis), or TRACED (executed replay
on the validated port: 47,520 golden + 100/100 replay checkpoints).

---

## 1. Loss reconstruction: seed 247025 (OBSERVED + DERIVED)

- Checkpoint decisions (both matches identical): 72 REJECT_UNCONFIRMED
  (YARN proj +$2,215.30, liq $142) → 144 REJECT_UNCONFIRMED (+$2,058.65,
  liq $213) → 216 REJECT_UNCONFIRMED (+$2,476.60, liq $673) →
  **288 SPECIALIZE_CONFIRMED YARN_SPECIALIZED** (proj +$13,491.80, liq $13,638).
- Shop unlock order: PET_CAFE, PET_CAFE, BRUNCH_SPOT, **YARN_STORE at step 288**.
- Remaining horizon at confirmation: **432 steps**.
- Terminal: candidate $58,338.00 vs baseline $60,182.00 → **−$1,844.00**.
- Model prediction error: realized − projected = **−$15,335.80**.

## 2. Loss reconstruction: seed 247034 (OBSERVED + DERIVED)

- Checkpoint decisions (both matches identical): 72 BASELINE (no candidate
  beat TAU; best=BASELINE, exp $0.00) → 144 BASELINE → 216 BASELINE →
  **288 SPECIALIZE_CONFIRMED YARN_SPECIALIZED** (proj +$6,027.68, liq $15,587).
- Shop unlock order: ICE_CREAM_SHOP, PIZZA_SHOP, SMOOTHIE_SHOP,
  **YARN_STORE at step 288**.
- Remaining horizon: **432 steps**.
- Terminal: candidate $120,362.00 vs baseline $125,755.00 → **−$5,393.00**.
- Model prediction error: **−$11,420.68**.

Note the seeds differ pre-confirmation (247025 wanted YARN all along and was
gated; 247034's model saw zero value until YARN unlocked), yet both fail at
the same confirmation step. The common factor is the 288-entry, not the
pre-history.

## 3. Cohort structure: entry step stratifies outcomes (OBSERVED)

| First SPECIALIZE_CONFIRMED | Seeds | Outcomes |
|---|---|---|
| Step 72 | 8 (002,005,009,010,016,024,029,048) | all ties ($0.00) |
| Step 144 | 7 (006,015,021,026,028,040,042) | all ties ($0.00) |
| Step 216 | 5 (000,012,017,033,039) | all large wins (+$5,426…+$13,064) |
| Step 288 | 2 (025, 034) | both losses (−$1,844, −$5,393) |
| Never | 28 | all ties ($0.00) |

Telemetry is perfectly seat-symmetric (match 0 ≡ match 1 on all fields,
all 50 seeds). The two loss seeds are the ONLY first-at-288 seeds.

## 4. Valuation-model error analysis (OBSERVED + DERIVED)

Predicted (at last SPECIALIZE checkpoint) vs realized paired delta:

- 15 early-entry (72/144) seeds: predicted +$12.9k…+$25.3k, realized $0.00.
- 5 mid-entry (216) seeds: predicted +$8.7k…+$18.8k, realized +$5.4k…+$13.1k
  (4 overpredicted, 1 underpredicted: 247017 realized +$13,064 vs +$11,195.68
  at step 288).
- 2 late-entry (288) seeds: predicted +$13.5k/+$6.0k, realized negative.

The model overpredicts in **21 of 22** activated seeds. Structural causes
(read directly from `evaluate_plan_feasibility_and_value`):

1. **No amortization cliff.** Revenue scales smoothly with `t_rem`:
   wool cycles `t_rem//72` = 7 at step 216 vs 6 at step 288 (model retains
   ~86% of wool value); milk `t_rem//48` = 10 vs 9; wheat `t_rem//48` similar.
   Nothing in the model represents fixed-commitment recovery over a shrinking
   window.
2. **Livestock capital is never charged.** The livestock section adds wool/milk
   revenue with NO purchase-cost term (no 500/sheep, 600/cow), while crop
   seed costs ARE charged (× cycles). A route's defining capital commitment
   is free in-model.
3. **Transition friction is a flat $200** (`SWITCHING_FRICTION`), applied only
   when leaving a non-baseline plan — i.e. exactly $0 for every baseline→
   specialized entry, including the Day-12 entries.

Consequence for criterion E: the model's own "projected route value" cannot
adjudicate the runway hypothesis — it is uncalibrated by construction
(ranking heuristic, not a forecast). Runway attribution must come from
executed-behavior analysis (tape + replay), not from model numbers.

## 5. Commitment-bundle analysis: what the switch actually buys (DERIVED)

Route tapes decoded from the frozen baseline (`_V56_YARN_ROUTE`,
`_V55_LIVE_ROUTE` = backbone; 719 entries each). The executed policy replays
the active tape **indexed by current game step**
(`replay_policy`: `actions[step]`, clamped), with market proposals gated by
the observation-conditioned residual controller. Therefore a switch at game
step S adopts tape suffix [S:] and **skips all earlier tape entries**.

Animal-buy tape schedules:

- YARN tape: SHEEP ×2 @1, ×2 @150, ×2 @195, ×2 @217, ×2 @241, ×1 @265
  (total 11); COW ×2 @1, ×1 @65,88,174,178 (total 6).
- LIVE tape: SHEEP ×2 @1, ×2 @195, ×1 @313 (total 5);
  COW ×2 @1, ×1 @65,88, ×2 @150, ×1 @169,176,195 (total 9).

Implications by entry step (proposals; residual gating may pass/reject —
executed truth is PENDING replay):

- **216-entry (wins)**: still captures YARN sheep buys at 217/241/265
  (5 sheep) + 504 steps of yarn-flavored operations. Pre-switch herd per
  LIVE tape: ~6 cows / 4 sheep.
- **288-entry (losses)**: captures **ZERO** further animal buys (last YARN
  sheep buy is tape-step 265; LIVE suffix has 1 sheep at 313 which the
  switcher now also skips). Pre-switch herd per LIVE tape: 9 cows / 4 sheep.
  The switcher adopts the yarn-flavored operating suffix (heavy wheat-product
  feed buying, fertilizer, milk/carrot-sell and hire differences — see
  suffix diff below) against a cow-heavy herd, with no compensating sheep
  intake.
- **72/144-entry (ties)**: capture most/all YARN sheep buys yet tie exactly —
  the proposals evidently converge behaviorally to baseline outcomes in those
  seeds (mechanism PENDING replay; see §6).

Post-288 tape-suffix market-proposal differences (YARN vs LIVE), largest first:
BUY_PRODUCT WHEAT in ~30 quantity-buckets (YARN-heavy, LIVE-zero),
SELL WHEAT/WOOL/MILK/STRAWBERRY/CARROT slot-size differences (YARN wool-sale
slots are sized for an 11-sheep flock the 288-switcher does not own),
HIRE 196 vs 204, BUY_SEED WHEAT/CARROT small differences, fertilizer
size-mix differences. Prime suspect for the realized cash losses (to confirm
by replay): executed wheat-product FEED buys with no matching sheep flock —
outflow without production. Full suffix diff retained at `/tmp/tape_suffix_diff.txt`.

### 5.1 Correction to the DEV-005 audit narrative (DERIVED)

`experiments/EXP-DEV-005/FORENSIC_AUDIT.md` §5 states the 288 losses occurred
because "buying sheep at Step 288 incurs immediate cash outflow" that cannot
amortize. **The tape contradicts this**: no sheep purchase is proposed at or
after tape-step 288 on EITHER tape. The 288-switcher's capital outlay on
livestock is ~$0 by construction. The operative mechanism must be one of:
(a) operating-pattern/herd mismatch (yarn suffix on a cow-heavy herd),
(b) foregone LIVE-suffix actions (e.g. the 313 sheep, sell timing),
(c) feed/market-timing losses in the adopted suffix — with "insufficient
runway" as one mediator, not the sole demonstrated cause (see §6).
Executed post-288 market totals (TRACED, both seeds near-identical):
BUY_PRODUCT WHEAT 1,895 units, BUY_SEED WHEAT 134, HIRE 196, SELL WHEAT ~2.2k,
SELL WOOL 256, SELL MILK ~240, SELL STRAWBERRY 260; executed sheep-tile counts
frozen at 4 post-288 (vs counterfactual 5: the switcher skips the LIVE tape's
step-313 sheep).

## 6. First divergence and own/world decomposition (TRACED)

Pre-288 play in both loss seeds was bit-identical backbone policy
(`active_plan == BASELINE_BACKBONE` at all prior checkpoints; same
`_POLICY_BACKBONE` + identical seed-trim/shed-guard/terminal wrappers as the
baseline agent). Step 288 is therefore the first step at which the
candidate's `active_policy` differs from the baseline's, Instrumented counterfactual replay (M1 = dev005-vs-baseline vs
M0 = baseline-vs-baseline, per seed and seat; pre-288 focal money
bit-identical in all 4 pairs) gives, both seats identical:

| Item | 247025 | 247034 |
|---|---|---|
| First ACTION divergence | step 288 | step 288 |
| First MONEY divergence | step 289 | step 289 |
| Shop-sequence divergence | step 359 (5th unlock differs; later unlocks differ) | NONE (all 8 unlocks identical) |
| Own effect (treat minus own counterfactual) | **-$4,310** (58,338 vs 62,648) | **+$630** (120,362 vs 119,732) |
| Opponent channel (opp shared minus opp counterfactual) | -$2,466 (60,182 vs 62,648) | **+$6,023** (125,755 vs 119,732) |
| Paired delta (frozen, reproduced) | -$1,844 | -$5,393 |

Gap growth (own / opponent, treat-base): 247025 reaches -1,507/+79 by step 300
and -4,375/-2,215 by step 576; 247034 swings (-7,821/+1,086 at step 432) and
settles (+630/+6,023). The 247034 loss arises with IDENTICAL shops - purely
through market-price/inventory and weed-RNG channels: the switcher's
yarn-suffix trading (notably 1,895 units of wheat-product feed buying) moves
shared prices in ways that benefit the backbone opponent's sales (+$6,023)
while its own farm roughly breaks even (+$630).

Criterion-E implication: the guard's recovery is 100% caused by blocking the
two 288 entries (purity-gated: no other behavioral difference exists), but the
mediator is the entry's FULL cascade - own-farm suffix mismatch (dominant in
247025) plus shared-market/RNG world channels (dominant in 247034) - broader
than pure own-farm capital amortization. "Remaining horizon < 500" is a valid
predictive gate (perfectly separates the 2 sub-500 entries on this cohort);
the micro-story "unamortized livestock capital" is refuted as the sole cause
($0 livestock outlay, +$630 own farm in 247034).

## 7. Phase 8 — cutoff vs runway-aware rule (DERIVED hypothesis, NOT implemented)

Two confounded mechanisms fit the cohort pattern:

- **H1 (fixed cutoff)**: no NEW specialization after step 216 (H=500).
  Fits: 288-entries lose, 216-entries win. But it is a grid artifact of 4
  checkpoints, and §5 shows entry step also changes the commitment bundle.
- **H2 (runway-aware)**: allow entry only when
  `expected payoff over remaining horizon > required recovery cost`.
  The DEV-005 model cannot express H2 today (§4: no capital term, no cliff).
  A minimal H2 would charge fixed commitment (e.g. livestock capital +
  transition disruption) against per-cycle margin × remaining cycles.

Tape evidence favors investigating H2: the 216-vs-288 outcome gap coincides
with a 5-vs-0 remaining sheep-buy gap, i.e. the later switch is not "the same
investment with less time" but a strictly worse bundle. However H1 vs H2
cannot be separated on N=2 late entries, and any H2 threshold would be fit
post-hoc on this cohort. Per mandate, H2 is documented ONLY as the stronger
mechanistic hypothesis for a future preregistered experiment — it is NOT
implemented, NOT swept, and confers NO qualification.

## 8. One-factor purity record (DERIVED + EXECUTED)

The treatment file is an exact DEV-005 copy plus: `HORIZON_GUARD_THRESHOLD`
constant, class/docstring rename, one counter, the guard branch (fires only
for baseline→specialized transitions with `remaining < 500`), two additive
telemetry fields, `REJECT_HORIZON` event routing, `kaggle_agent` rename.
`diff -u` verified; valuation, confirmation, routing, preemption, terminal
logic byte-identical; AST audit clean. Predicted cohort effect: exactly the
two 288-first seeds convert to $0.00 ties (recovery +$7,237.00); all other
48 seeds bit-identical. EXECUTED 2026-09-14 (200 games, validated port):
`replay_parity_ok` PASS (50/50 seeds bit-identical to frozen),
`one_factor_purity_ok` PASS (guard fired only at step 288 in exactly
247025/247034; all other diffs exactly $0.00). Recovery exactly +$7,237.00.

## 9. Formerly pending items — resolved by replay

1. Executed post-288 purchase lists: RESOLVED (see §5.1: no sheep; 1,895
   wheat-product feed units; full totals in `port/loss_seed_traces.json`).
2. Own/world money decomposition: RESOLVED (see §6 table + gap paths).
3. First divergence: RESOLVED (action step 288, money step 289).
4. Why 15 early-entry seeds tie bit-exactly: OPEN but out of scope — the guard
   never touches them (verified $0.00 diffs); their bit-exact ties imply the
   early-adopted YARN suffix converges behaviorally to baseline outcomes in
   those worlds (residual gating + tape alignment). Flagged for future work;
   immaterial to this verdict since the guard preserves them exactly.
5. Criterion E attribution + Phase 11 verdict: RESOLVED — see §6 and VERDICT.md
   (SUPPORTED with documented mediator nuance).
