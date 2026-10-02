# V32 P7 — PREFIX DATASET (CANONICAL OPENING PREFIXES FROM RECORDED DATA)

## 1. SOURCE & METHOD

- Source: `results/v32_p2_bc_legs.jsonl` (120 legs, 240 seats, training seeds
  249635–249674, 4 teachers × 60 seats each). No live simulation, no relabeling,
  no holdout access.
- Extraction: `scripts/v32_p7_extract_prefixes.py` → `results/v32_p7_prefixes.json`
  via `v32/p7/prefix.py` (same `EpisodeFeatures` online-builder replay as P2/P3
  training; prefix features are bit-identical to `build_samples` features).
- Per prefix record: step, seed, teacher, full `ess` snapshot, 157-dim temporal
  features, per-unit contexts, native factorized targets, recorded native action,
  state-derived phase (`v32/p7/phase.py`).

## 2. HEADLINE FINDING: THE OPENING MACRO IS IDENTICAL ACROSS ALL 4 TEACHERS

Farmer-action prefixes are **single-variant (60/60) for every teacher at every
horizon** (P4/P8/P12/P24), and the canonical sequence is **byte-identical across
all four teachers**. Market prefixes are single-variant per teacher; the four
teachers differ ONLY in step-0 wash quantities. Hand prefixes are single-variant
except one V3 branch (§5).

Consequence: the reference-teacher choice (nominally E2_A7) is moot for
farmer-action divergence — all teachers define the same prefix target.

## 3. CANONICAL FARMER PREFIX (ALL TEACHERS, 240/240 SEATS)

```text
Step 0:  ['PASS']
Step 1:  ['NORTH']
Step 2:  ['SOUTH']
Step 3:  ['PICKUP', 'SHEEP']
Step 4:  ['PICKUP', 'WHEAT']
Step 5:  ['NORTH']
Step 6:  ['WEST']
Step 7:  ['BUILD_PASTURE']
Step 8:  ['PLACE', 'SHEEP']
Step 9:  ['FEED']
Step 10: ['CARE']
Step 11: ['WEST']
Step 12: ['PLANT', 'MELON']
Step 13: ['WATER']
Step 14: ['WEST']
Step 15: ['PLANT', 'MELON']
Step 16: ['WATER']
Step 17: ['PASS']
Step 18: ['PASS']
Step 19: ['PASS']
Step 20: ['PASS']
Step 21: ['PASS']
Step 22: ['PASS']
Step 23: ['PASS']
Step 24: ['PICKUP', 'WHEAT']
```

Prefix units: P4 = steps 0–4, P8 = steps 0–8, P12 = steps 0–12, P24 = steps 0–24.

## 4. CANONICAL MARKET PREFIX (E2_A7; OTHER TEACHERS IDENTICAL EXCEPT STEP 0)

```text
Step 0:  BUY_PRODUCT WHEAT 30, SELL WHEAT 30        (wash; qty varies by teacher)
Step 1:  SELL WHEAT 13, BUY_PRODUCT WHEAT 5, HIRE×5, BUY_ANIMAL COW 2, BUY_ANIMAL SHEEP 2
Step 2:  (none)   Step 3: (none)   Step 4: (none)   Step 5: (none)
Step 6:  BUY_SEED MELON 2     Step 7: BUY_SEED MELON 1    Step 8: (none)
Step 9:  BUY_SEED MELON 1     Step 10: BUY_SEED MELON 2   Step 11: BUY_SEED MELON 1
Step 12: BUY_SEED WHEAT 1     Step 13: BUY_SEED WHEAT 1   Step 14: BUY_SEED MELON 3
Step 15: BUY_SEED WHEAT 1     Step 16: BUY_SEED WHEAT 1   Step 17: BUY_SEED MELON 2
Step 18: (none)               Step 19: BUY_SEED WHEAT 1   Step 20: BUY_SEED WHEAT 2
Step 21–23: (none)            Step 24: HIRE×3
```

Step-0 wash by teacher: E0_V3 (50/50), E2_A7 (30/30), E6_W72 (7/2), E7_W2015 (20/15).
Steps 1–24 market: identical across all four teachers (60/60 each).

## 5. HAND PREFIX (E2_A7 CANONICAL, STEPS 0–12; SINGLE VARIANT 60/60)

```text
Step 0:  (no hands)                              Step 1: (no hands)
Step 2:  PICKUP COW / PASS / NORTH / NORTH / PICKUP COW
Step 3:  NORTH / PASS / NORTH / NORTH / BUILD_PASTURE
Step 4:  BUILD_PASTURE / PASS / NORTH / NORTH / PLACE COW
Step 5:  PLACE COW / PASS / NORTH / WEST / CARE
Step 6:  NORTH / PASS / NORTH / WEST / PICKUP SHEEP
Step 7:  NORTH / PASS / PLANT MELON / PLANT MELON / PICKUP WHEAT
Step 8:  PLANT MELON / PASS / WATER / WATER / WEST
Step 9:  WATER / PASS / WEST / NORTH / BUILD_PASTURE
Step 10: WEST / PASS / PLANT MELON / WEST / PLACE SHEEP
Step 11: PLANT MELON / PASS / WATER / PLANT MELON / FEED
Step 12: WATER / PASS / WEST / WATER / CARE
```

Note: hands build pastures in parallel with the farmer (tile-hist pasture count
grows from step 4). E0_V3 hand P24 has 2 variants (30/30): vs E2_A7 vs vs E7_W2015
opponents, differing in 2 hand literals at steps 18 and 21 only (V3's sole reactive
branch in 0–24; all other teachers fully open-loop through step 24).

## 6. CANONICAL STATE TRAJECTORY (E2_A7, SEED 249635 SEAT 1; REPRESENTATIVE)

| Step | Farmer | Hands | Cash | Shed (C/S/W) | Farmer inv | Phase |
|:---:|:---:|:---:|:---:|:---:|:---|:---|
| 0 | [4,4] | 0 | 3000 | 0/0/0 | {} | OPENING_CAPITAL |
| 1 | [4,4] | 0 | 3054 | 0/0/0 | {} | OPENING_CAPITAL |
| 2 | [4,3] | 5 | 1106 | 2/2/5 | {} | LIVESTOCK_SETUP |
| 3 | [4,4] | 5 | 1106 | 0/2/5 | {} | LIVESTOCK_SETUP |
| 4 | [4,4] | 5 | 1106 | 0/1/5 | SHEEP×1 | PRODUCTION_SETUP |
| 5 | [4,4] | 5 | 1106 | 0/1/4 | SHEEP×1,WHEAT×1 | ECONOMIC_CONTINUATION |
| 6 | [4,3] | 5 | 1106 | 0/1/4 | SHEEP×1,WHEAT×1 | ECONOMIC_CONTINUATION |
| 7 | [3,3] | 5 | 946 | 0/0/4 | SHEEP×1,WHEAT×1 | ECONOMIC_CONTINUATION |
| 8 | [3,3] | 5 | 866 | 0/0/3 | SHEEP×1,WHEAT×1 | ECONOMIC_CONTINUATION |
| 9 | [3,3] | 5 | 866 | 0/0/3 | WHEAT×1 | ECONOMIC_CONTINUATION |
| 10 | [3,3] | 5 | 786 | 0/0/3 | {} | ECONOMIC_CONTINUATION |
| 11 | [3,3] | 5 | 626 | 0/0/3 | {} | ECONOMIC_CONTINUATION |
| 12 | [2,3] | 5 | 546 | 0/0/3 | {} | ECONOMIC_CONTINUATION |

(Cash values are seed-specific; positions/inventory/phase structure is invariant.
WORKFORCE_SETUP is skipped on the teacher trace because hiring and livestock
purchase co-execute at step 1; it remains reachable for degraded trajectories.)

## 7. PREFIX-TARGET CROSS-SEED CONSISTENCY

| Prefix | Farmer variants (per teacher) | Cross-teacher farmer match | Market variants | Hands variants |
|:---:|:---:|:---:|:---:|:---:|
| P4 (0–4) | 1 (60/60) | identical | 1 per teacher | 1 (60/60) |
| P8 (0–8) | 1 (60/60) | identical | 1 per teacher | 1 (60/60) |
| P12 (0–12) | 1 (60/60) | identical | 1 per teacher | 1 (60/60) |
| P24 (0–24) | 1 (60/60) | identical | 1 per teacher | 1 (V3: 2, opponent-split) |

## 8. IMPLICATIONS FOR P7

1. Prefix labels are unambiguous: 240/240 agreement on every farmer prefix.
2. Full-native prefix-exact-match must tolerate NOTHING at farmer level, but the
   P6 policy's known wash-quantity deviation (e.g. 7 vs 30) forces a two-tier
   metric: farmer-exact (strict) + full-native (reported, qty-sensitive).
3. The P6 "teacher" ambiguity (E0_V3 in the trace script vs E2_A7 in the text) is
   immaterial for steps 0–24 farmer comparison: the sequences are identical.
4. The macro's multi-unit coordination (farmer pickups + parallel hand pasture
   construction + timed seed purchases) is visible in the labels — this is the
   coordination structure H1 must preserve.
