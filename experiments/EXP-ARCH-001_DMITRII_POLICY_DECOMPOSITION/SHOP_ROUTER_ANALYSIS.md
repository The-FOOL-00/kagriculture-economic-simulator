# SHOP ROUTER ANALYSIS

Code: `router_parent.py` `SHOP_PLANS` + `Policy.act` steps 144/648.
Engine: shops unlock at days 3,6,…,24 (steps 72,144,…,576), drawn
WITH replacement (`sim.hpp`: `rng.choice_index(8)`).

## 1. Exact mapping (first two shops -> plan)

YARN second (7): (BAKERY,YARN)->3, (BRUNCH,YARN)->4, (FARMERS,YARN)->5,
(ICE_CREAM,YARN)->6, (PET_CAFE,YARN)->5, (PIZZA,YARN)->7,
(SMOOTHIE,YARN)->8.
YARN first (7): (YARN,BAKERY)->9, (YARN,BRUNCH)->9, (YARN,FARMERS)->1,
(YARN,ICE_CREAM)->9, (YARN,PET_CAFE)->10, (YARN,PIZZA)->6,
(YARN,SMOOTHIE)->11.
Double YARN (1): (YARN,YARN)->12.
All other 49 pairs -> 0 (dict miss).

## 2. Reachability

- Reachable ordered pairs: 8x8 = 64 (with replacement). All 15 listed
  pairs are reachable, INCLUDING (YARN,YARN) at p=1/64.
- Covered: 15/64 = 23.44% = P(YARN in first two shops). Uncovered:
  49/64 = 76.56% -> plan 0.
- Structural fact: EVERY covered pair contains YARN_STORE; NO covered
  pair lacks it. The router is a pure YARN-presence detector with
  order+partner refinement.
- Plan sharing: 5<-(FM,Y),(PET,Y); 6<-(ICE,Y),(Y,PIZ); 9<-(Y,BAK),
  (Y,BRU),(Y,ICE). Distinct YARN continuations: 11 (plans
  1,3,4,5,6,7,8,9,10,11,12).
- Plan 2 is unreachable at step 144 (no entry); plan 0 is the
  miss-default, never an explicit entry.

## 3. Is selection irreversible? Yes.

`state.plan` is written at step 144 and only ever overwritten at step
648 (to 2). No re-evaluation on later reveals (days 9–24, six more
shops) regardless of how the world unfolds.

## 4. Why step 144?

OBSERVED: 144 = day-6 dawn = the first step at which exactly two
shops are unlocked (unlocks at day 3 and day 6).
HYPOTHESIZED REASON: two shops are the minimum needed for the
(YARN, X)/(X, YARN) ordered-pair key; and day 6 coincides with the
first LAND purchase (step 150), first WOOL revenue (step 149–150),
and the sheep-flock expansion window — the last moment a YARN vs
non-YARN livestock decision can still be acted on before capital is
sunk. Also day 6 is when sheep placed on day 0 first pay (first
yield day 6), so YARN demand confirmation arrives exactly as wool
starts flowing. These are consistent with the tape evidence but the
choice itself is not proven optimal — it is also simply the earliest
step the pair-key exists.

## 5. Does step 648 create a second macro regime? Yes, mechanically.

OBSERVED: at 648 (day-27 dawn) plan := 2 for all games; tapes 3–12
are byte-identical to tape 2 over 648..718, so the switch is
seamless for YARN plans and an 11-step content change for plan 0
(dead bytes) / live content change to the shared tail.
HYPOTHESIZED REASON: day 27 closes the planting window (nothing
planted later can mature: wheat needs 2–4 days, carrot 2–3; last
plants are day-27 wheat/carrot top-ups) and ends the livestock
build (herd complete since day 11–12); the remaining game is pure
harvest/collect/liquidate, for which one shared tail suffices and
for which the terminal planner needs a guard-compatible baseline
(9-product clearing markets, no weed-blocked ops at 712–718).
Note the tape still PLANTs on day 27 (8 wheat + 2 carrot) — the
"regime" is harvest-dominated, not plant-free.

## 6. Is strategy #2 special terminally? Yes — it IS the terminal.

OBSERVED: (a) plan 2's 144..647 body is a near-copy of plan 0 (110
diffs, late-mid); (b) its 648..718 tail is THE shared tail; (c) its
712..717 markets satisfy `_fixed_market` exactly (verified in
`analysis/05_guard_checks.md`); (d) its 712..718 unit ops contain
zero PLANT/BUILD (verified), satisfying `shadow_baseline`'s
weed-independence guard; (e) `policy.py` REQUIRES `live.plan == 2`
at step 711 or the terminal planner never engages.
HYPOTHESIZED REASON: plan 2 exists to be a planner-compatible
landing strip. The 110 body diffs vs tape 0 (days 21–26) plausibly
steer the day-27 state (positions, shed, carried stock) into the
narrower envelope the shared tail + shadow planner assume — but
this steering effect is hypothesized, not measured here.

## 7. Observed vs hypothesized (discipline table)

- OBSERVED: 15-pair YARN-only map; single write at 144; forced 2 at
  648; 49 pairs -> 0; plan sharing as listed.
- HYPOTHESIZED: YARN-only coverage is optimal (untested — no
  PET/PIZZA/SMOOTHIE-first plans exist to compare); step 144 is the
  best checkpoint (untested — 72 and 216 were available and unused);
  forced convergence at 648 beats per-plan tails (untested —
  confounded with planner-compatibility requirements).
- The strength of the bot does NOT imply any of these choices is
  optimal; §7 of the transferability matrix treats each as a
  hypothesis with a smallest discriminating experiment.
