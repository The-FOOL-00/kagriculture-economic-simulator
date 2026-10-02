# V31R2 SIM-TO-LIVE CALIBRATION

Date: 2026-09-22. Engine local = live = `kaggle_environments 1.32.7`
(live replays report `module_version 1.32.7`). NO engine mismatch.

## Offline vs live per candidate

| Candidate | Offline result | Live result | Calibration |
| --------- | -------------: | ----------: | ----------- |
| V22R1 | ties V3; beats DMITRII 16-0; self 101.6k | 1880.3, 108W/128L/1T vs 1926-median field | consistent: ~1900-strength vs ~1900 field |
| A7 | +$1,289 vs V3 (80-0); 80-0 vs reconstructed meta | 1859.6, 50W/32L vs 1857-median field | +$1,286 signature replicated live 6-0 vs 50-wash; losses to UNTESTED families |

## What the simulator got RIGHT

1. A7's +$1,286 vs 50-wash: replicated live EXACTLY (4 exact +$1,286
   incl. 3x vs 2436-rated naren_v; diff trajectory +108 → +28 → +1286
   at step 252, melon-seed +1). Packaging faithful (live A7 = local A7).
2. Wash-size micro-effects: local E3b (W10-vs-A7 +$140 med) mirrors
   live A7-vs-10/10 (−$139 med). Same scale, opposite sign. The
   opening-ledger game transfers quantitatively.
3. Symmetric equivalence: local A7vA7 ≡ V3vV3 predicts live
   flat-mirror games (kevin zhou −$34 set by step 17).

## What the simulator got WRONG (opponent-set mismatch, not engine)

V30's "256-0 frontier-breakout" claim is FALSIFIED as a live
prediction. Cause: the 11 reconstructed meta families were WEAK
proxies (self-play $54.7–95.5k, Sept 8–10 code drops, unverified
directory-label ratings), while the live 1800–2700 field consists of
V3-CLONES with micro/strategy adaptations our gauntlet never contained:

- livestock-mix variants (+3 sheep/−3 geese: wen −$9k; atl132; Ezzzzzekki)
- strawberry-archetype (Fedor −$14k, 392 strawberries)
- high-fertilizer micro (+20–35 FERTILIZE: shawenher, carbonapi)
- sell-execution micro (Marlubie −$4.3k, identical counts)
- small-wash ledgers (10/10, 20/15, 7/2, 5/5 — V29 never tested 30-vs-small)

Local E1/E2/E3 pilots testing the OBVIOUS one-line copies of these
(price-gating 0-48, order-splitting 0-40, wash-switching ±$600 crumbs)
all FAILED — the live edges live in V3-internal policy details
(livestock router, fert/labor timing, crop strategy) that market-level
adapters cannot reproduce, plus shed-clog destruction punishing naive
sell-side changes (−$35k GATE catastrophe).

## Verdict

The simulator is FAITHFUL (engine identical, wash effects replicate,
A7 signature replicates). It OVERESTIMATED A7/V3 because we tested
the WRONG OPPONENTS (weak reconstructions), not because local matches
misresolve. Corrective: future offline gauntlets must include
live-derived V3-clone variants (small-wash, sheep-heavy, strawberry,
high-fert) — harvested from this cycle's 321 replays — before any
frontier claim. V30's result is hereby reclassified OFFLINE
REPLAY-POLICY EVIDENCE, not live competitive proof (per §12).
