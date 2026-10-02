# V58 — Final Benchmark Ladder Report

Engine: kaggle-environments 1.32.7. Incumbent V49_Meta_Fusion frozen
(SHA256 `8CAFF630...FBBD11`, re-verified at close).

## Stage B — Fixed elite plan tournament (tournament seeds 10100-10119)

40 paired legs per matchup (20 seeds x 2 seats), elite listed first:

| Plan | Elite | W/L/T | Elite WR | Mean | Median | Catast |
|------|-------|-------|----------|------|--------|--------|
| J | v44 | 0/40/0 | 0.000 | -163,440 | -163,262 | 40 |
| C | kaitofukami_3009 | 0/40/0 | 0.000 | -26,115 | -24,474 | 40 |
| D | saiteja_3000 | 0/40/0 | 0.000 | -90,463 | -91,359 | 40 |
| A | thomastschinkel_2945 | 0/20/20 | 0.000 | -79 | -41 | 0 |
| E | tetsutani_pasture | 0/40/0 | 0.000 | -17,445 | -13,484 | 31 |
| F | indarkarhana_top10 | 0/40/0 | 0.000 | -19,971 | -17,193 | 36 |
| B | dmitrii_lb2800 | 0/40/0 | 0.000 | -10,271 | -8,711 | 18 |
| G | P3090_claimed | 0/40/0 | 0.000 | -33,413 | -31,306 | 40 |
| H | P3000_claimed | 0/40/0 | 0.000 | -31,499 | -28,237 | 40 |
| I | night_harvest | 0/40/0 | 0.000 | -44,952 | -47,284 | 40 |
| **Total** | | **0/380/20** | **0.000** | — | — | — |

V49 win rate across the 400-leg current-elite tournament: **100%**
(380 wins + 20 ties, 0 losses).

## Follow-up — t2945 regime scan (seeds 10120-10179, 120 legs)

t2945 2/120 nominal wins (seats 10134-P0 +964, 10153-P1 +961).
Decomposition by self-play control: seat premiums +1084 (10134) and -961
(10153) are identical under V49-self-play and t2945-self-play; t2945's
strategy deficit is -120 and 0 — **0/60 pair sums positive** (mean -217,
max 0). The 2 wins are seat artifacts, neutralized by paired legs.

## Stages C-F

- Transplant: NO_QUALIFYING_TRANSPLANT (no winning macro to transplant).
- Static elite: none (0/400).
- Safe selector: NOT_BUILT (nothing to select between).
- Fresh validation ≥10200: not run — no candidate survived to validate
  (running 576 fresh legs with no candidate would be theater, not evidence).

## Decision

**V58_RETAIN_V49** — V49 retained, 0 casualties inflicted or risked, no
candidate promoted.
