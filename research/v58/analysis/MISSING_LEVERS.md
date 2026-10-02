# V58 Missing Levers

For each family: what does it consistently do that V49 does not — and does it
causally help? (Capture evidence; tournament verdict pending in
counterfactuals/PLAN_TOURNAMENT.json.)

## August families F1/F2 (24/42/108@land7, melon-heavy, no carrot, no wash)

- Distinctive: +12 melon, +9 strawberry, -55 wheat, land day 7, crew 14.
- Causal read: lower tile throughput (174/158 vs 239) and no wash engine.
  F2's 121k bank_med is a patch-1.32.4/5 artifact, not a strategy advantage
  (night_harvest = F2 line scores 40-55k on 1.32.7 vs V49 100k+ same seeds).
- Lever status: **no lever; superseded line.**

## August families F3-F6 (19/37/143@land6, wheat-heavy tape line)

- Distinctive: -20 wheat, -12 straw... i.e. slightly smaller crop book than
  V49, zero carrot, zero wash, 8-9C/4S herds, day-0 4S/1C.
- Causal read: P3090/P3000 (exact F5/F4 lines) lose to V49 by 25-45k on
  discovery seeds. The wheat-heavy/carrot-0 line scales worse on 1.32.7.
- Lever status: **no lever; superseded line.**

## kaitofukami_3009 (sheep-only day-0, SELL 583, no wash)

- Distinctive: only elite with sheep-only opening and 583 micro-sales; 11C/4S end.
- Causal read: loses to V49 by 15-45k on discovery seeds despite ladder 3009.
  Regime-dependent (fast-routes tape tuned to ladder-shop distribution?).
- Lever status: **candidate regime lever, unproven** — needs tournament seeds;
  if it wins any regime, isolate the shop/price trigger before promoting.

## saiteja_3000 (2-quad end, 6C/1S)

- Distinctive: moon/frontier/hamburger router; misses SW quad on capture seeds.
- Causal read: execution leak, not a lever. Loses by ~100k.
- Lever status: **none.**

## tetsutani_pasture (herd liquidation)

- Distinctive: ends with zero animals (full late liquidation).
- Causal read: loses by ~20k; liquidation forfeits terminal milk/wool flow.
- Lever status: **none (anti-lever).**

## indarkarhana_top10 (10C/4S, W187)

- Distinctive: most wheat (187), 10 cows.
- Causal read: loses by ~20-30k; wheat-heavy without wash scale.
- Lever status: **none.**

## thomastschinkel_2945 (V49-family, 6C/6S, C55)

- Distinctive: MORE carrot (55 vs 49), sheep-heavy herd (6/6 vs 12/5),
  otherwise V49-identical census.
- Causal read: within $150 of V49 on both discovery seeds —the only elite at
  the boundary. The lever candidate is *herd composition given the same
  route*: 12C/5S (V49) vs 6C/6S (t2945).
- Lever status: **closest boundary probe**. Tournament will show whether 6C/6S
  ever wins a regime; if yes, the selector reduces to a herd-mix rule.

## dmitrii_lb2800 (V49-family, 8C/6S)

- Distinctive: same wash census, mid herd.
- Causal read: loses by ~10-13k. Supports "herd scale calibrates the family".
- Lever status: **supporting evidence for the herd-mix gradient, not a lever.**

## V44 (conditional no-op)

- Distinctive: the only agent that sometimes does nothing at all — and the
  only one that ever beats V49 (ladder 250617/250621, queue collision).
- Causal read (V56): wins are a step-697 market-queue artifact, not a macro
  strategy. Off-regime it scores 3000.
- Lever status: **no macro lever (V56 closed); regime artifact.**

## Best macro lever (current)

**End-herd mix within the September wash route (12C/5S vs 6C/6S)** — the only
boundary where an elite (t2945) sits within striking distance of V49.
Everything else is ≥$10k away on discovery seeds. Tournament decides whether
this boundary ever flips.
