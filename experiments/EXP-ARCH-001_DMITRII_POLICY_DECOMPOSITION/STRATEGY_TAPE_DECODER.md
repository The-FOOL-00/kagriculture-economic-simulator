# STRATEGY TAPE DECODER — method and per-strategy narratives

Decoder: `decode_tapes.py`, `decode_tapes2.py` (static analysis only).
Evidence: `analysis/01`–`analysis/12`. No engine execution was used;
all claims below are grounded in tape bytes plus engine source law.

## 1. Method (what the decoder does, and does not do)

1. Structural: pairwise per-step equality over 0..143 / 144..647 /
   648..718; per-day distinct-action counts; targeted diff-step lists.
2. Schedules: per-day PLANT by crop, BUY_SEED/BUY_ANIMAL/BUY_PRODUCT/
   BUY_LAND/HIRE timelines, FEED/CARE/COLLECT/BUILD timelines, SELL
   cadence by product with quantities, deterministic spend timeline
   (seeds at list price, animals at 1.32.7 prices, HIRE at Fibonacci
   cost; market-price buys and all revenue excluded as unknowable).
3. Workforce: hands-list length per step (midday sample), hires/day.
4. Worker roles: pooled op histogram by worker index.
5. Guard compatibility: tape-2 712..717 market shape, weed-blocked ops
   in 712..718, empty-order census.

The decoder does NOT reconstruct tile positions (tapes carry ops, not
coordinates), does NOT simulate the engine, and does NOT estimate
revenue (SELL orders clear `min(requested, stock)` at marginal shared
prices — statically unknowable). "First revenue turn" below therefore
means first SELL *order* turn per product, flagged where the order is
provably dead (zero possible stock: TOMATO everywhere, EGG/CARROT in
no-geese/pre-harvest plans).

## 2. Reading guide: the tape has 3 regimes, not 13 strategies

From `Policy.act` (steps 144/648 checkpoints):

- Steps 0..143: ALWAYS tape 0. All other tapes' bytes here are dead.
  (Tape 1's 10 dead diffs at steps 70–141 are shown in
  `analysis/11_targeted_diffs.md`; they never execute.)
- Steps 144..647: the selected tape (the ONLY economically live
  per-strategy region, 504 steps).
- Steps 648..718: ALWAYS tape 2. All other tapes' bytes here are dead
  (tapes 3–12 are byte-identical to tape 2 here; tape 0 differs in 11
  steps and tape 1 in 68 — dead either way).

Consequence: every per-strategy summary below shares the §3 opening
and the §5 terminal. Only §4 differs per strategy.

## 3. Shared opening (tape 0, steps 0..143 = days 0..5)

Day 0: BUY 12 MELON + 7 WHEAT seeds and plant all 19; buy 2 COW +
2 SHEEP (step 1); build 4 PASTURE; PLACE all 4 animals; buy ~31 WHEAT
as feed. Deterministic spend $2,842 of $3,000 (94.7%). Hands: 5.
Day 1: 4 animals fed/cared; fertilizer collection begins; first SELL
FERTILIZER at step 30 (first revenue order in the game). Hands: 3.
Day 2–3: +1 COW each day (placed); wheat top-ups planted (3–4/day).
Day 4: wheat top-up; herd at 6.
Day 5: first STRAWBERRY seeds bought (step 130) and 4 planted.
Workforce 3–5 hands/day, re-hired every dawn (day labor).
Shed-adjacent spawn every dawn; farmer respawns at the NW shed tile.

## 4. Per-strategy narratives (live region 144..647 + market style)

Format note: "Macro crop mix" and "Animals" are near-identical for all
(see §6); the narratives below highlight what actually differs.

### STRATEGY 0 — default (49 non-YARN pairs)

Day 6: LAND NE ($1,000) + 2 COW + feed/fertilizer (step 150);
7 pastures built; 8 STRAWBERRY + 5 WHEAT planted.
Day 7: +2 COW (herd 10). Day 8: +2 SHEEP. Day 9: +1 SHEEP.
Day 10: 4 COOPs + 2 GOOSE placed; MELON harvest begins (~step 249;
sales 6–24 units, drip cadence). Day 11: LAND SW ($2,000) + 13
STRAWBERRY + 11 WHEAT planted (second wave); +1 GOOSE.
Days 12–26: steady state — 17 head fed/cared/collected daily
(17/17/17 ops), wheat replanted 6–14/day, WOOL/MILK/FERTILIZER/
STRAWBERRY drip-sold in small lots (1–18 units, no x100 bursts).
Days 24–27: CARROT wave planted (4/14/11/2) on freed tiles.
Terminal behavior: shared plan-2 tape from 648; clearing bursts
x1000 from step 685; 9-product clearing 712–717.
Macro crop mix: MELON 12 → WHEAT ~163 (feed + drip sales) →
STRAWBERRY 33 (waves day 5–8, 11) → CARROT 31 (late).
Animals: 8 COW + 6 SHEEP + 3 GOOSE = 17.
Primary revenue sources (order evidence): FERTILIZER (108 SELL turns
from step 30), MILK (65), WHEAT (63), STRAWBERRY (51), WOOL (42),
MELON (13), EGG (25, real — geese owned), CARROT (23, late).
Shop assumptions: no YARN in first two shops; diversified livestock
(geese hedge) and cautious wool liquidation (42 small lots).
Workforce: 260 hires, peak 11 hands.

### STRATEGY 1 — (YARN_STORE, FARMERS_MARKET)

Agronomy identical to 0 (same PLANT day×crop table). Diffs vs 0:
430/504 action steps, but daily op-mix L1 ≈ 10% (route permutation).
Economics: 6 COW + 10 SHEEP, NO geese (EGG SELL orders from step 360
are dead — zero stock); WOOL 84 SELL turns with x100 clearing lots
(2× the count, ~10× the size of strategy 0); x1000 full-clear bursts
at steps 402–407, 430–431, 669–671. More hires (277).
Reading: YARN-confirmed wool demand → bigger sheep flock, aggressive
wool liquidation, geese dropped.

### STRATEGY 2 — forced terminal plan (live only via step-648 switch)

Identical investments to 0 (8/6/3 herd, same seeds, 260 hires).
Live region 144..647 differs from tape 0 in 110 steps, concentrated
days 13+ and especially days 21–26 (late-mid route variant). Its
defining property is its 648..718 tail (shared by tapes 3–12):
guard-compatible terminal (9-product SELL≥100 at 712–717, zero
PLANT/BUILD at 712–718). Never selected at step 144
(no SHOP_PLANS entry points to 2).

### STRATEGY 3 — (BAKERY, YARN_STORE)

Cluster member (17–72 diffs from neighbors). Same agronomy; 6 COW +
11 SHEEP, no geese; aggressive WOOL clearing + x1000 bursts like 1.
276 hires.

### STRATEGY 4 — (BRUNCH_SPOT, YARN_STORE)

Cluster member. Same agronomy; 6 COW + 10 SHEEP, no geese;
aggressive WOOL clearing + bursts. 276 hires. Differs from 1 only on
day 9 (steps 216–239) plus scattered steps.

### STRATEGY 5 — (FARMERS_MARKET, YARN_STORE) and (PET_CAFE, YARN_STORE)

Cluster member (closest to 1: 17 scattered single-step diffs).
6 COW + 10 SHEEP, no geese; aggressive wool clearing. 276 hires.
Shared by two shop pairs.

### STRATEGY 6 — (ICE_CREAM_SHOP, YARN_STORE) and (YARN_STORE, PIZZA_SHOP)

Cluster member. 6 COW + 11 SHEEP, no geese; aggressive wool clearing.
276 hires. Shared by two shop pairs.

### STRATEGY 7 — (PIZZA_SHOP, YARN_STORE)

Cluster member (16 diffs from 8 — nearest pair in the set).
6 COW + 11 SHEEP, no geese. 275 hires (one fewer on day 9).

### STRATEGY 8 — (SMOOTHIE_SHOP, YARN_STORE)

Cluster member. 6 COW + 11 SHEEP, no geese. 275 hires.

### STRATEGY 9 — (YARN_STORE, {BAKERY, BRUNCH_SPOT, ICE_CREAM_SHOP})

Route outlier (504/504 action diffs vs 0) but same PLANT table and
~9–18% daily op-mix distance: a full route permutation, not a new
economy. 6 COW + 11 SHEEP, no geese (all EGG orders dead). Sparse
sales style: WHEAT sold ~daily in single lots from step 337 (vs
continuous drip in 0); STRAWBERRY only 33 SELL turns (vs 51);
FERTILIZER bought late (first step 359 vs 150) and less (23 vs ~40
units). Shared by three shop pairs.

### STRATEGY 10 — (YARN_STORE, PET_CAFE)

Cluster-adjacent (72 diffs from 1, days 8–9 block). 6 COW + 11 SHEEP,
no geese; WHEAT seeds 161 (fewest), STRAWBERRY 34. 277 hires.

### STRATEGY 11 — (YARN_STORE, SMOOTHIE_SHOP)

Cluster member (24 diffs from 6, day-8 block). 6 COW + 11 SHEEP, no
geese; WHEAT seeds 167. 276 hires.

### STRATEGY 12 — (YARN_STORE, YARN_STORE)

Most distinctive economics, still on the shared skeleton. 4 COW +
14 SHEEP bought (largest flock) but only 17 pastures built, so one
animal is unhoused (steady FEED ≈ 16–17); no geese; STRAWBERRY 44
seeds (most);
CARROT 24 (fewest, bought from step 264 vs 590 — early bulk);
MELON 13. Seed purchasing is BULK (e.g. step 264: WHEAT x11 +
STRAWBERRY x23; daily WHEAT x8–11 at 24-step intervals) vs the JIT
trickle (1–3/step) in all other tapes. Route is a full permutation
(494–504/504 diffs) with ~8–12% op-mix distance. 277 hires.

## 5. Shared terminal (tape 2, steps 648..718 = days 27..29)

Day 27: last planting (8 WHEAT + 2 CARROT); herd work continues
(17/17/17) but COLLECT tapers (11). Day 28: FEED drops (9), a
stray BUILD_COOP appears (functionally useless this late — search
artifact). Day 29: only CARE + COLLECT_FERTILIZER remain; steps
712–717 are 9-product SELL≥100 clearing with moves/HARVEST/DROP/
PLACE; step 718 is replaced at runtime by `liquidate(view)`
(tape bytes there never execute).
Terminal inventory composition (structural, not simulated): shed
holds late CARROT/WHEAT harvests, last MILK/WOOL/EGG waves, and
accumulated FERTILIZER; carried inventories are auto-dropped at the
day-29 dawn and hand-DROPped/PLACEd through the window.

## 6. Cross-strategy invariants (the shared skeleton)

- PLANT day×crop table: IDENTICAL for all 13 (MELON 12 day 0;
  STRAWBERRY 4/8/4/4 days 5–8 + 13 day 11; WHEAT 1–14 every other day;
  CARROT days 24–27; TOMATO never).
- LAND: NE at step 150, SW at step 265, all tapes. SE never bought.
- Herd scale: 16–17 head; FEED/CARE/COLLECT converge to 17/17/17
  (or 16/16/16) daily from day 12 in every tape.
- Workforce scale: 3–5 hands days 0–5, 7–12 thereafter; hires/day
  equals hands commanded (exact, no spam).
- Day-0 spend: $2,842 / $3,000 in all tapes (identical opening).
- First-revenue order turns: FERTILIZER 30; WOOL 149–150; MILK
  195–196; MELON 248–249; STRAWBERRY 382–393; CARROT 670 (drip
  plans) — all within ±3 steps except dead-order artifacts.
- Worker roles: none — all hand indices show the same op mix
  (WATER/moves/CARE/FEED/COLLECT/HARVEST); homogeneous labor pool.

## 7. Generation artifacts (evidence about how tapes were made)

1. Hour-0 hands are ALWAYS empty (day-labor re-hire; deterministic).
2. 131 empty `[]` market orders (inert via `_parse_order`→None),
   concentrated in tapes 0/2 (45 each): vacated order slots.
3. `SELL x 0` orders (e.g. step 452, 607): leftover of
   advance-then-subtract processing — tapes passed through (or were
   recorded under) the reactive sales overlay.
4. Step 0–1 `BUY WHEAT 13 + SELL WHEAT 13`: ~zero-net round trip,
   almost certainly search noise, harmless.
5. Dead SELL orders: TOMATO in all tapes (never grown), EGG/CARROT
   x1000 bursts in plans without stock — free (sell min(stock,
   requested)) but consume order slots.
6. Day-28 BUILD_COOP: functionless this late; search residue.
