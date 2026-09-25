# V31R2 A8 RESULTS — E1/E2/E3/E3b falsification record (NO-BUILD)

Date: 2026-09-22. All pilots preregistered in `V31R2_A8_SPEC.md`,
mirrored both seats, virgin seeds only (protected 340090..340199 and
214200..214249 untouched; E-consumption: 249591..249634 + 2 diagnostic
live seeds 1877695685/1846354605, recorded here as consumed).

## E1 — A8-GATE (price-gated selling, F=0.5), 58 legs, 249591..249604

| Bout | Result (GATE-centric) |
| ---- | --------------------- |
| vs A7 (20) | 0-20, mean −$36.9k |
| vs V3 (20) | 0-20, mean −$32.3k |
| vs GATE (10) | 1-0-9 at $52–75k (below V3 self $101.6k) |
| vs V22R1 (8) | 0-8, mean −$34.1k |

FALSIFIED. Cause: holding goods pins shed-100; engine DROP destroys
overflow (`del inv[item]`); production wasted. Fill instrumentation
(1,608 fills/mirror at $62) killed the flood premise.

## E2 — SPLIT (SELL truncation K=10), 50 legs, 249605..249614

| Bout | Result |
| ---- | ------ |
| vs A7 (20) | 0-20, mean −$3.1k |
| vs V3 (20) | 0-20, mean −$1.7k |
| vs SPLIT (10) | ties at $71–72k |

FALSIFIED. Within-order erosion benefit < shed-clog cost. Additive
decomposition clean (A7-edge +$1.3k preserved inside the −$3k).

## E3 — wash variants (±SPLIT10) vs A7, 160 legs, 249615..249624

W10 20-0 (+$594/+140 med) · W2015 18-2 (+$181) · W5 18-2 (+$189) ·
W72 18-2 (+$5). ALL below +$3k bar → FAILED. wash+SPLIT 0-80
(−$6.5k..−$14k, clog cascades to −$51k tails).

## E3b — full 6x6 wash matrix, 280 legs, 249625..249634

Transitive W5>W10>W72>W2015>A7(30)>V3(50), magnitudes $3–$307.
W5-vs-50 = +$140: switching sacrifices A7's +$1,286 vs 50-wash.
Net live effect of any wash switch ≈ neutral-negative. FAILED A8 bar.

## E6 (fert-cap) — considered and skipped

Predicted E1-style clog catastrophe; fert pattern confounded
(wen: equal fert, −$9k via sheep-mix). No preregistration spent.

## Totals

548 legs (50+8+50+160+280), ~9 workers, engine 1.32.7. A8 record:
0 candidates passed. NO-BUILD per spec §14. Next cycle needs
live-derived clone opponents in the gauntlet before any new A8.
