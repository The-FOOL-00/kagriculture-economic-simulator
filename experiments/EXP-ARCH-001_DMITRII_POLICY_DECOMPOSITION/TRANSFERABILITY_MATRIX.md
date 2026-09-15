# TRANSFERABILITY MATRIX — Dmitrii ideas vs our systems

Our systems: V54++ (`v54_plus_shop/residual`: route-following + residual
preemption + overlays, YARN-detector over 3 routes, sticky from 72/144);
DEV-004 (6 whole-route candidates, checkpoints 72/144/216/288, valuation
tau=1500/Lmin=100/Fswitch=200); DEV-005 (+confirmed-shop gate); DEV-006
(+H=500 horizon guard: no new entry at 288); DEV-007 (exposure protocol,
runner unbuilt). Honesty note: V54 route-follower internals live in
`v50.hybrid`, absent from the workspace — our-side V54 execution claims
below rest on workspace docs/reports, flagged where unverified in this
track. All Dmitrii-side claims trace to `analysis/` + cited source lines.

## How to read each item

Dmitrii behavior (observed) / Our behavior / Benefit / Risk / Evidence
required / Possible isolated experiment. No item below is a design; each
is an independently testable hypothesis (classification in HYPOTHESES.md).

### 1. Single irreversible macro choice at step 144

Dmitrii: one write of `plan` at 144 from the 2-shop pair; never
revisited (later 6 reveals ignored); forced to 2 at 648.
Ours: V54++ re-evaluates a sticky YARN predicate (effective 1–2
decision points); DEV-004/5/6 decide at 4 checkpoints with model
valuation + gates, and maintain specializations.
Benefit: zero late-transition cascades by construction (the DEV-005
step-288 failure class cannot occur); no valuation-model risk; simple.
Risk: forfeits days 9–24 information (62.5% of shops); our wins came
from step-216 entries (+$5.8k/+$8.7k in DEV-006) that a 144-only rule
would miss or mistime.
Evidence required: distribution of OUR wins/losses by entry checkpoint;
counterfactual: what would 144-only have done on 247xxx/248xxx.
Isolated experiment: cap DEV-006 checkpoints to {144} (decide once,
maintain thereafter) on a fresh Discovery cohort vs DEV-006.

### 2. Forced terminal-regime convergence at step 648

Dmitrii: all games converge to the shared plan-2 tail at day-27 dawn.
Ours: routes run to 718 with terminal overlays (recall 713–716,
liquidation 717–718); no regime switch at 648.
Benefit: a single well-validated harvest/liquidate tail; removes
late-route divergence exactly when planning windows close.
Risk: discards plan-specific terminal positioning (e.g. YARN wool
waves may want a different tail); transition friction at 648.
Evidence required: per-route terminal (648–718) performance split in
our replays; whether our specialized tails beat our backbone tail.
Isolated experiment: force all DEV-006 arms onto the backbone
648–718 tail (routes differ only ≤647) vs unforced DEV-006.

### 3. YARN-only shop conditioning (ignore 49 pairs + all non-YARN info)

Dmitrii: 15 YARN pairs get continuations; everything else plays the
default; non-YARN shops never change anything.
Ours: V54++ also YARN-gated (3 routes); DEV-004 has 6 routes incl.
BAKERY/PET/SMOOTHIE/PIZZA — but ALL 184 DEV-006 specializes were
YARN_SPECIALIZED (non-YARN routes never fired on 248xxx).
Benefit: kills model-selection overfitting surface; matches where our
own evidence concentrates (100%-YARN activations).
Risk: real PET/PIZZA/SMOOTHIE edge (cf. Audit 2.2's Triple-Pet-Cafe
$126k episode) stays on the table.
Evidence required: activation audit of non-YARN routes across ALL our
cohorts (do they ever fire? ever win?).
Isolated experiment: prune DEV-006 registry to {BACKBONE, YARN} vs
full registry on fresh seeds (tests whether the extra routes add
anything beyond variance).

### 4. Route-permutation variants of ONE economy (not N economies)

Dmitrii: 11 YARN continuations share one agronomic skeleton; they
differ in paths/timing/sales cadence, not crop mix.
Ours: DEV routes are distinct economies (different animals/crops per
route); V54 routes (V56/V58) likewise differ economically.
Benefit: robustness through path diversity without economic bets;
cheap to generate (search over routes, one economy).
Risk: if the single economy is wrong for the world, all variants
lose together (correlated failure); our distinct-economy routes
hedge Economic risk instead.
Evidence required: our cross-route loss correlation (do our routes
fail on the same seeds?); Dmitrii-style variant generation cost.
Isolated experiment: generate 3 timing/route variants of OUR
backbone (same economy, different worker timing), pick by a fixed
rule, vs single backbone.

### 5. Same-day weed queue (insert DIG, delay worker, wipe at dawn)

Dmitrii: per-worker queue; DIG inserted before weed-blocked
PLANT/BUILD; slip absorbed same-day; queues die at dawn.
Ours (V54 execution): unverified in this track (v50.hybrid absent).
DEV-004 models worker service cadence; weed handling not isolated in
DEV reports read here.
Benefit: bounded, legible local repair; no re-planning cost.
Risk: dawn wipe strands queued HARVESTs; slip breaks rendezvous.
Evidence required: our weed-block frequency + cost audit (how often
do PLANT/BUILD fail on weeds? what do we lose?).
Isolated experiment: add dawn-wiped DIG-insertion to a frozen route
follower vs unmodified on weed-heavy cohorts (needs weed telemetry).

### 6. One-turn advance sales (WHEAT/FERT excluded, price≥2, tick guards)

Dmitrii: pull next-turn SELLs one turn early when stock covers;
subtract at due turn; skip unlock steps and 4-step consume ticks.
Ours: V54 residual preemption (deficit-triggered fronting, horizon
2–3, batch caps 4–12, min-delta 4.0); DEV has a market-timing
controller (not decomposed here).
Benefit: lower sale latency + shed-pressure relief with conserved
2-turn totals; simpler than deficit modeling.
Risk: systematically sells before price upticks the tape anticipated;
slot contention at the 10-order cap.
Evidence required: our preemption trigger audit (how often do
deficit-fronts fire? at what prices vs next-turn?).
Isolated experiment: replace V54 preemption with Dmitrii's
advance/subtract rule (same backbone) on fresh seeds.

### 7. Shadow-sim terminal optimizer with unit-dominance (712–718)

Dmitrii: exact 7-turn deterministic sim, frozen prices, adopt iff
strictly-greater value AND row-wise unit dominance AND no-steal;
abstain-by-default with 10+ guards; live re-verification per step.
Ours: V66 `_route_loaded_units` heuristic recall (713–716) + fixed
liquidation (717–718) — no simulation, no dominance proof.
Benefit: terminal gains with a no-harm certificate (units dominate
every turn); our Audit notes Dmitrii wins pure-Straw seeds via the
terminal planner (−$20.48 margin there).
Risk: 128 sims of complexity; model-mismatch abstention rate unknown
(ours would need the same guard suite); price-myopia (frozen prices).
Evidence required: OUR terminal-window audit: carried cargo stranded
at 718, unharvested mature yield in 712–718, DROP overflow frequency.
Isolated experiment: graft a dominance-gated 712–718 reaper onto our
frozen backbone (markets fixed, workers only) vs heuristic recall.

### 8. Frozen-price unit-dominance objective (no price forecasting)

Dmitrii: terminal objective weights units by step-712 prices; safety
is in UNITS (opponent-proof), prices only weight a dominating outcome.
Ours: DEV market-absorption engine models pull rates and penalizes
dead stock; V54 residual uses deficit/value deltas.
Benefit: removes the most error-prone input (price forecasts) from
the safety case; forecasts only affect WHICH dominating plan wins.
Risk: under-frozen-price myopia, real price crashes can still make a
"dominating" plan poorer in money terms (units ≥, money <?).
Evidence required: our valuation-model error audit (predicted vs
realized deltas, esp. the ~$14k/seed late-entry overvaluation seen in
DEV-006 §14 — a dominance gate would have vetoed those entries).
Isolated experiment: add a no-harm unit-dominance veto to DEV-006
checkpoint entry (enter only if projected terminal units dominate
backbone's) vs DEV-006.

### 9. Day-0 95% capital deployment + feed-wheat buying

Dmitrii: $2,842/$3,000 on day 0 (12 melon, 4 animals, wheat); buys
feed wheat at market (~155 units drip) instead of growing it all.
Ours: DEV enforces Lmin=100 + deficit fronting; V54 backbone rhythm
(not decomposed to day-0 granularity here).
Benefit: maximum early compounding (melons day 10, wool day 6).
Risk: liquidity cliff on bad price/weeds (Dmitrii's answer: drip
revenue from day 1 fertilizer + day 6 wool funds day-6 land).
Evidence required: our day-0 spend + day 1–6 cash-low audit vs
Dmitrii's implied curve.
Isolated experiment: shift our backbone's day-0 spend earlier/later
by fixed $-amounts (3 variants) on fresh seeds.

### 10. Drip-selling vs clearing bursts (sales cadence as the decision)

Dmitrii: default plan drips (1–18 units); YARN plans clear wool x100
+ periodic x1000 bursts. Same production, different market impact.
Ours: preemption batches (4–12) on deficit triggers; shed guard sells
overflow at hour 23.
Benefit: cadence tuned to sink depth (thin WOOL T=105/sq-crash vs
deep MELON T=300) without changing production.
Risk: bursts crash thin markets (WOOL above_func sq×0.80 punishes
exactly this); drip pays slot/turn overhead.
Evidence required: our per-product sale-size distribution + realized
price impact vs Dmitrii's implied cadence.
Isolated experiment: fix our backbone, vary ONLY wool sale lots
(drip-8 vs clear-100) on YARN-heavy fresh cohorts.

### 11. Goose-free sheep-heavy YARN herds (6C/10–14S, 0G)

Dmitrii: YARN plans drop geese, run 6 cows + 10–14 sheep; default
keeps 8C/6S/3G.
Ours: DEV YARN_SPECIALIZED = 6C/11S (convergent!); baseline 9C/5S;
no geese anywhere (grep 2026-09-15).
Benefit: (for us) independent corroboration of 6C/11S; (general)
geese only pay in non-YARN worlds (egg diversification).
Risk: sheep concentrate feed demand (1 wheat/head/day × 17) and
WOOL crash risk without YARN.
Evidence required: our YARN-route feed-burden + wool-price audit.
Isolated experiment: add a goose-diversified non-YARN variant
(8C/6S/3G) to our registry vs current baseline on non-YARN cohorts.

### 12. Fertilizer as a cash crop (17 head → ~17/day free)

Dmitrii: COLLECT_FERTILIZER every animal daily; FERTILIZER has the
MOST SELL turns (108) starting step 30 — first revenue in the game.
Ours: no FERTILIZER reference found in dev_004 (grep 2026-09-15);
V54 backbone fertilizer behavior unverified in this track.
Benefit: possibly the cheapest revenue we are leaving: every fed
animal yields 1 free fertilizer/day (base $100!).
Risk: collection labor crowds out watering/harvest; fertilizer
market T=200/linear may crash under 17/day × 2 players.
Evidence required: OUR fertilizer collection + sale audit (do we
collect? sell? at what prices?); engine T=200 impact math.
Isolated experiment: add collect-and-drip-sell-fertilizer to our
frozen backbone vs unmodified.

### 13. Zero tomato (never plant, never buy seeds)

Dmitrii: 0 tomato seeds in all tapes; TOMATO SELLs are dead orders.
Ours: DEV has PIZZA_ADAPTIVE (tomato presumably in its crop mix —
unverified here); Audit 2.2 retracted uncoordinated tomato (−$5.4k).
Benefit: avoids the documented tomato trap (needs cows + wheat +
pizza; rots/daily-harvest burden).
Risk: none identified (pizza worlds are 23% of first-2-draws but
need joint production Dmitrii also lacks).
Evidence required: our PIZZA route's tomato economics + activation
record (does it ever fire? win?).
Isolated experiment: strip tomato from our PIZZA route (milk+wheat
only) vs intact on pizza-heavy fresh cohorts.

### 14. Late carrot wave (days 24–27 on freed tiles)

Dmitrii: 24–31 carrots planted days 24–27, harvested ~days 26–29,
sold from step 670 — fast cash from otherwise-idle tiles/labor.
Ours: unverified in this track (late-game crop use not audited here).
Benefit: converts dead tile-time into (PET/FM-supported) cash.
Risk: competes with terminal harvest labor; rots if unharvested.
Evidence required: our days-24–27 tile/labor utilization audit.
Isolated experiment: append a fixed late-carrot wave to our frozen
backbone vs unmodified.

### 15. No opponent modeling (shared by both sides — agreement, not gap)

Dmitrii: never reads opponent state; only shared-price weights.
Ours: V54++ constraints forbid opponent classifiers; DEV uses own
telemetry + public shops/prices.
Benefit/Risk: none differential — noted to prevent "port Dmitrii's
opponent blindness" from entering as a false idea. Both sides agree.
