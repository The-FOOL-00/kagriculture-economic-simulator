# V32 EXP-1 — EXPERT BENCHMARK (executed 2026-09-22)

448 legs, seeds 249635–249640 (V32-TRAIN block 1), mirrored seats, hermetic
adapters, `max_tasks_per_child=1`, engine 1.32.7. Records:
`results/v32_exp1.jsonl`. Fingerprints: `V32_STRATEGY_FINGERPRINTS.json`.

## 1. Win/loss standings (core round-robin, 96 legs each)

| # | Expert | W-L-T | Mean Δ | Mean cash |
| :--- | :--- | :--- | :--- | :--- |
| 1 | E6_W72 | 84-12-0 | +1,400 | 93,278 |
| 1 | E7_W2015 | 84-12-0 | +1,611 | 102,580 |
| 3 | E2_A7 | 72-24-0 | +2,690 | 103,114 |
| 4 | E1_V22R1 | 60-34-2 | +1,467 | 101,055 |
| 5 | E4_A1 | 41-46-9 | +1,424 | 101,045 |
| 6 | E3_V25P3 | 36-60-0 | +1,090 | 102,263 |
| 7 | E0_V3 | 33-54-9 | +1,407 | 101,037 |
| 8 | E5_A2 | 12-84-0 | −183 | 100,127 |
| 9 | E8_DMITRII | 0-96-0 | −10,906 | 97,430 |

(Mean Δ is inflated by +$8–13k DMITRII blowouts for every expert; pairwise
margins below are the honest numbers.)

## 2. Pairwise mechanisms (12 legs each, virgin seeds)

- **A7 beats V3 12-0 by EXACTLY +$1,286 every leg.** The canonical mechanism
  reproduces on all 6 virgin seeds × both seats.
- **A7 beats V22R1 12-0 by +$1,250.** V22R1 opens 50/50 V3-regime and inherits
  the wash vulnerability; AEC timing does not save it (consistent with V31R2).
- **Wash ordering by W/L: W72 > W2015 > A7(30) > V3(50)**, all pairwise 12-0
  or 8-4 with SMALL margins: W72–V3 +$28, W2015–V3 +$241, W72–A7 +$23,
  W2015–A7 +$36, W72–W2015 +$24. Smaller wash wins (n=6 caveat).
- **V27-dispatch 2×2 (wash × dispatch)**: A2−V3 = −$1,255; A1−A7 = −$1,304.
  Dispatch costs ≈ −$1.3k regardless of wash; A1 ≈ V3 parity (8 ties).
- **V25P3 below V3** (V3 wins 8-4, +$593): consistent with V27 OUTCOME D.
- **DMITRII loses everything** (−$8.5k to −$13.4k): weak-lane only, direction
  matches V30 (−$6.8k) with seed variance.
- **V22R1 beats V3 10-1-1** (+$68–78) and W72 8-4 (+$37–47): AEC timing earns
  small edges inside the V3 regime but collapses vs wash-30 (−$1,250).

## 3. The opponent IS the economy (post-hoc, §44 at scale)

Same expert, same seed, different opponent → different ABSOLUTE cash by up to
$31k (seed 249638: A7 scores 137k vs V3 but 106k vs V25P3; V25P3 scores 137k
vs V3 but 105k vs A7 — mutual suppression).

Descriptive block summary (G1={V3,V22R1,A1,A2}, G2={A7,V25P3,W2015}):
CROSS-group pairs average ~$107k pair-cash vs ~$93k WITHIN, same sign on 6/6
seeds (gaps +$1k…+$35k). W72 pairs sit at ~$92k on every seed — W72 never
participates in a high economy yet finishes joint-top on W/L: the population's
denial specialist (100% extractive, lowest winner cash).

Caveats (explicit): G1/G2 was fit post-hoc on n=6 seeds — descriptive, not
confirmed. Pre-registered follow-up: on fresh TRAIN seeds (249643+), CROSS
pairs (e.g. A7+V3) will out-cash WITHIN pairs (e.g. A7+V25P3) on the majority
of seeds. Mechanism forensics (price-path collision vs niche partitioning):
open item, seed 249637/249638 A7×V25P3 vs A7×V3 first.

## 4. Controls

- **Seat symmetry**: mirrored legs give byte-identical per-expert cash
  (deterministic, seat-independent play). Mirrors are determinism checks, not
  independent samples — future power analyses must count seeds, not legs.
- **Parity**: A7 adapter vs packaged AST 12/12 EXACT ties (Δ=0). §51(15) holds.
- **Sanity**: V3 vs PASS — V3 151k/176k, PASS 3000. No scoring inversion.
- **Cost**: V22R1 legs ~160–182 s (12× fast legs) → V22R1 is eval-only for
  all V32 training, as decided in `V32_COMPUTE_FEASIBILITY.md`.

## 5. EXP-1 verdict

Population is DIVERSE (mechanism-exact wash ladder + dispatch factorial +
reactive external + denial specialist), ORDERED (transitive W/L with one
pending confirmation), and HONEST (no expert dominates absolutely; W/L and
cash decouple). It is a valid training/eval population for Phase A/B.
Champion for the league: E2_A7 is the highest-cash winner; E6_W72/E7_W2015
are co-#1 on W/L. Per `V32_PROMOTION_PROTOCOL.md`, the initial frozen
champion stays E2_A7 (live-validated); the wash-ladder inversion is exactly
the kind of regime effect the learned policy must master.
