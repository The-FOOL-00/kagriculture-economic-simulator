# V27 — BEHAVIORAL DELTA LEDGER & FIRST-DIVERGENCE ANALYSIS

Machine-readable ledger: `results/v27_ledger.jsonl` (200 records; 120 P3
series + 80 P1′/P2′ controls), built by `scripts/v27_ledger.py all` from
`results/v27_fresh_trajectories.jsonl` (history-free, one match per OS
process) and hermetic V26A1 replays. Trajectory alignment (verified):
`obs[t]` is the pre-action state at game step `t`; `action[t]` is the
action taken at `t` (recorded in `env.steps[t+1]`; `env.steps[0]` holds
a placeholder). Fidelity digests hash the raw recorded array exactly as
V25/V26 did, so parity is directly comparable.

## 1. Replay-fidelity audit (read first: it redefines the evidence base)

| Series | Loader context | Digest match |
| :--- | :--- | ---: |
| DISC-P1 (40) | same queue as V25 | 40/40 |
| DISC-P2 (40) | same queue as V25 | 40/40 |
| DISC-P3 (40) | same queue as V25 | 40/40 |
| CONF-P3 (40) | post-DISC history (alien) | 0/40 |
| CONF-P3 F1 rerun (40) | fresh pool, V25 queue order | 40/40 |
| V26A1 (40) | hermetic adapters, alien history | 40/40 |
| DISC-P1′/P2′/CONF-P3′ (120) | fresh process per match | 120/120 vs checkpoint |
| DISC-P3′ (40) | fresh process per match | 0/40 vs checkpoint |

Root cause (proven by minimal reproducer): V25's file loader lets each
candidate `import main` (the V3 payload) through the process-global
module cache. A reused pool worker therefore replays a STALE V3 module.
P2 is a pure V3 passthrough (calls V3 at step 0); P1/P3 bypass V3 at
step 0. A single P2 primer flips the next P3 match
(`A/249431/s0: +1145/e631d38d` → `+1286/3d5a2860`, exactly the
checkpoint row). In V25's discovery queue (P1×40, P2×40, P3×40 over 9
workers) every worker ran P2 tasks before P3 tasks, so all 40 DISC-P3
rows carry P2-residue. P1 and P3 are behaviorally IDENTICAL programs
(AST-equal modulo docstring/comments/tempdir prefix), so their
discovery contrast (−55.33 vs +1,300.70) is a pure harness artifact.
The stale residue flips one mid-game market micro-decision (localized:
turn-433 `SELL WOOL 2` on A/249431/s0; first money-state divergence at
obs-step 434); the first ~99 turns are history-independent, which is
why the constant `early_idle_rate` (0.27935…) reproduces in all 200
replays and V25's telemetry is exonerated on that point.

Corrected history-free evidence (the series this ledger analyzes):

| Seeds | Program behavior | Mean | Median | W/L/T (exact) |
| :--- | ---: | ---: | ---: | :--- |
| A (249430..449) | P3 fresh (A′ = P1 rows) | −55.33 | +284.5 | 24/16/0 |
| B (249450..469) | P3 fresh (B′ = checkpoint) | +453.77 | +424.5 | 27/13/0 |
| C (249470..489) | P3 hermetic (V26A1) | −218.75 | −287.0 | 18/22/0 |
| A stale (QUARANTINED) | P3 + P2-residue | +1,300.70 | +1,300.0 | 40/0/0 |

Pooled farm-purged program effect (§7): **+$60 (SD $2,126, n=120)** —
indistinguishable from zero. Typical match (|Δ|≤$3,000, excl. the
249450 farm outlier): **−$53 (n=114)**.

## 2. Opening (CAPITAL): a deterministic +$108 transfer

On all 120 P3 matches (all series, seeds, seats): P3's 30/30 wheat wash
nets **+$54.00**, V3's 50/50 wash nets **−$54.00** (zero-sum lockstep;
engine quotes buys at post-buy inventory). P3 opens every game +$108.
The money gap then decays to exactly **+$28.0 at t=24** (bulk hires) on
all 120 matches, and is still +$28.0 at t=144 on all but the farm-outlier
matches (see §6). The early P3-vs-V3 economy is seed-invariant: no early
variance exists to explain terminal variance.

## 3. Labor: +12 waters, −13 passes, +1 plant — nothing else

Median gaps over 120 matches (mean in parens): WATER +12.0 (+12.3),
PASS −13.0 (−10.6), PLANT +1.0 (+1.0); HARVEST/MOVE/FEED/CARE/
COLLECT_FERTILIZER/FERTILIZE/PICKUP/DROP/PLACE/BUILD_* all median 0
(means ≤1.8, outlier-driven). DIG median 0: V3's tape digs weeds on
schedule, so P3's opportunistic digs add nothing net. The dispatch
footprint is a dozen waterings per 7,000+ unit-turns. No dose-response:
corr(choreGap, terminal) = −0.14 (all) / +0.21 (excl. 249463) —
sign-unstable to one seed, not a causal claim.

## 4. Farm structure: identical (except two threshold events)

Final-plant, final-animal, first-pasture-step, and quad-count gaps are
exactly 0.00 on A′/C and ≈0 on B′ (one +6-pasture and one −1-pasture
event, §§5–6). Crop mix identical (wheat/corn/tomato 0.00; melon +0.33
plant-steps, negligible). Hires identical except 249463 (+29 orders).
P3's economy differs from V3's only in money/goods FLOWS, never in
structure — except when a reactive threshold tips (§5).

## 5. Market flows (order-based; see fill caveat §8)

P3 issues fewer/smaller wheat SELL orders in every series
(qty gap ≈ −27/match, seat-corr 0.91–1.00 — a program effect, both
seats) and fewer SELL events (−1.45/−0.97/match A′/C). Posted-price
goods-P&L gap: A′ −$1,288, C −$1,406, B′ +$7 (median −$1,110; mean
dominated by 249463). By good (fresh totals): WHEAT −$56k, MILK −$19k,
WOOL +$24k, FERTILIZER +$4k. Milk qty gap ≈ 0 with negative revenue gap
(timing/prices, not volume). Terminal sheds are 0 for both sides
(full liquidation), so P3's lower goods revenue is not inventory
holding. SELL-side divergence is the proximate source of most terminal
deltas; §8 discusses orders-vs-fills.

## 6. First material divergence (§11)

Primary-category histogram (thresholds in script docstring):
CAPITAL-first 112/120, MARKET-first 7 (tie-broken at t=252), LIVESTOCK-
first 1 (249450/seat1, t=70). Divergence step: median 252, q10/q90 252,
min 70, max 252. Interpretation: the +$108 opening never crosses the
$250 materiality bar by itself; the first persistent ≥$250 gap forms at
**t≈252 (day 10–11, first strawberry/melon harvest revenue)** on
essentially every match. Divergence is a MEDIUM-HORIZON macro
transition (first cash-crop harvests), not an immediate local decision
(opening) nor a terminal accumulation. Reward emergence (gap locks onto
terminal sign, never flips after): median **553**, min 252 — direction
is decided late even though magnitude diverges at 252.

## 7. Farm-gap control (V3-vs-V3, hermetic, 60 seeds)

`scripts/v27_farm_gaps.py`: farm gap G=0 EXACTLY on 54/60 seeds (farms
are symmetric; V25's seat symmetry is real). Nonzero: 249450 (+$6,893!),
249456 (+$403), 249480 (+$335), 249485 (−$80), 249486 (−$123), 249435
(−$70). Farm-purged program effects eps=(Δ−G): pooled mean +$60,
SD $2,126 — the headline null. Two monster seeds dominate every mean.

## 8. Deep dives

**249463 (+$13,053/+13,026, both seats, G=0): the reactive tip.**
Money gap +$28 through t=144, +$881 by t=288 (mid-game economy), then
at t=289 P3's cash ($11,288) trips a reactive BUY_ANIMAL SHEEP×6 branch
V3 ($10,407) misses. Result: +6 pastures, +2–3 hands (14 vs 12 max),
−$6.5k at t=290 (investment), +$13k terminal. Permanent structural
divergence from a transient cash-threshold crossing. A V3-reactive
mechanism P3's early cash TIPS — present in both players' code. n=1
seed; not a general regime until replicated prospectively.

**249450/seat1 (−$5,054; seat0 +$279; G=+$6,893): the farm route.**
At t=33 V3@farm0's route issues BUILD_PASTURE; P3@farm1's route issues
PASS (P3 cannot skip non-PASS actions, so the routes genuinely differ).
P3 buys the same COWs but one sits unplaced in its shed from t=72 to
t=288 (worthless at terminal: reward = money only). One pasture ≈
−$5k. Origin: FARM/ROUTE asymmetry (V3v3 gap +$6,893 proves
program-independent farm inequality on this seed), not a P3 defect —
V3@farm1 would suffer the same route. Per-farm program effects here
(−$6.6k/+1.8k) are market-regime-confounded (V3v3 ran 50/50 washes vs
P3v3's 30/50) and not taken as clean reads.

**Typical match (median |Δ|, e.g. A/249448 +$277):** +$108 opening →
+$28 through day 6 → first ≥$250 gap at t≈252 on harvest revenue →
late reactive-market wobble → terminal ±$100s. No structural divergence
at any point; programs' labor identical modulo ~12 waters.

## 9. Fill caveat (orders vs fills)

Ledger market panels count ORDERS ISSUED at posted prices. Engine fills
are inventory/cash-constrained per lockstep unit and may partially fill.
Terminal money (ground truth) already accounts for fills; the order
panels describe BEHAVIOR (what the programs attempted), not realized
revenue. The wheat −27 order gap with identical plants/harvests/feed is
consistent with either (a) smaller/fewer fills (real revenue shortfall)
or (b) order sizing with equal fills (behavioral only). Directionally
both imply P3's reactive seller behaves worse-or-equal on wheat; the
terminal null (+$60 pooled) bounds the economic consequence near zero
either way. A fill-exact ledger would require engine instrumentation
(out of scope; the decision question doesn't need it).

## 10. Explicit non-conclusions

- The ledger does NOT show P3's +12 waters cause any terminal effect
  (no dose-response; ablation A3 tests this).
- The ledger does NOT show P3's wheat-order shortfall is a defect vs a
  timing shift (fills unobserved).
- 249463's tip is n=1 and does not establish a general threshold regime.
- No P3-specific livestock, sales, or "macro coupling" code exists (the
  125-line program is wash + dispatch); §§15-A4/A5/A6 of the V27 brief
  have no code target (see V27_ABLATION_PLAN.md).
