# V55 Final Fresh Paired Benchmark Ladder

## Executive Summary

**Evaluation Protocol**:
* **Suite Size**: 576 strictly paired legs per candidate (1,728 total 719-step simulation matches)
* **Dataset**: 32 strictly disjoint fresh seeds `[250600..250631]` $\times$ 2 Seats (0 and 1) $\times$ 9 Established Opponents
* **Opponent League**:
  - 6 Elite: `V44`, `dmitrii_lb2800`, `tetsutani_pasture`, `kaitofukami_v48_3009`, `indarkarhana_top10`, `saiteja_mega_3000`
  - 3 Adversarial: `DAIRY_FLOOD`, `WOOL_FLOOD`, `TERMINAL_DUMPER`
* **Engine**: Current official `kaggle-environments 1.32.7` via bit-exact `FastKagricultureSim`
* **Holdout Protection**: Zero holdout seeds accessed (`214200–214249`, `340090–340199`, `249695–249734` 100% untouched).

---

## 1. Overall Fresh Benchmark Leaderboard

| Candidate | Total Legs | Wins | Draws | Losses | Win Rate | Paired Margin Delta vs V49 | Bootstrap 95% CI | Rescues | Casualties | Active Fraction | Gate Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`V49_Meta_Fusion` (Incumbent)** | **576** | **572** | **0** | **4** | **99.31%** | **+$0.00** | **[$0.00, $0.00]** | **0** | **0** | **0.0%** | **SOVEREIGN BASELINE** |
| **`V55_Blocked_Action`** | 576 | 572 | 0 | 4 | 99.31% | +$0.00 | [$0.00, $0.00] | 0 | 0 | 0.0% | **REJECTED (Inactive)** |
| **`V55_Post_Reveal_Shop`** | 576 | 453 | 0 | 123 | 78.65% | -$6,524.25 | [-$7,539.46, -$5,572.90] | 0 | **119** | 56.4% | **REJECTED (Catastrophic)** |

---

## 2. Sub-Suite Performance Decomposition

### 2.1 Elite Opponent Suite (384 legs)

| Candidate | Legs | Wins | Win Rate | Mean Delta vs V49 | Rescues | Casualties | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`V49_Meta_Fusion`** | 384 | 380 | **98.96%** | **+$0.00** | 0 | 0 | **Dominant** |
| **`V55_Blocked_Action`** | 384 | 380 | **98.96%** | +$0.00 | 0 | 0 | Exact Parity |
| **`V55_Post_Reveal_Shop`** | 384 | 261 | **67.97%** | **-$9,625.60** | 0 | **119** | Fatal Collapse |

### 2.2 Adversarial Stress Suite (192 legs)

| Candidate | Legs | Wins | Win Rate | Mean Delta vs V49 | Rescues | Casualties | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`V49_Meta_Fusion`** | 192 | 192 | **100.00%** | **+$0.00** | 0 | 0 | **Flawless** |
| **`V55_Blocked_Action`** | 192 | 192 | **100.00%** | +$0.00 | 0 | 0 | Exact Parity |
| **`V55_Post_Reveal_Shop`** | 192 | 192 | **100.00%** | -$321.55 | 0 | 0 | Safe |

---

## 3. Per-Opponent Granular Results

### Candidate: `V55_Post_Reveal_Shop` vs `V49_Meta_Fusion`

| Opponent | Legs | V49 WR | Cand WR | Mean Delta vs V49 | 95% Bootstrap CI | Casualties | Active Legs |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `V44` | 64 | 93.75% | 46.88% | -$6,744.80 | [-$10,126.60, -$3,734.27] | **30** | 44 (68.8%) |
| `dmitrii_lb2800` | 64 | 100.00% | 59.38% | -$8,592.86 | [-$11,896.72, -$5,562.35] | **26** | 48 (75.0%) |
| `tetsutani_pasture` | 64 | 100.00% | 59.38% | -$11,176.53 | [-$14,947.19, -$7,571.31] | **26** | 54 (84.4%) |
| `kaitofukami_v48_3009`| 64 | 100.00% | 65.62% | -$10,421.12 | [-$13,492.31, -$7,489.47] | **22** | 48 (75.0%) |
| `indarkarhana_top10` | 64 | 100.00% | 76.56% | -$11,725.09 | [-$15,792.72, -$8,036.71] | **15** | 44 (68.8%) |
| `saiteja_mega_3000` | 64 | 100.00% | 100.00% | -$9,093.22 | [-$12,020.94, -$6,353.43] | **0** | 41 (64.1%) |
| `DAIRY_FLOOD` | 64 | 100.00% | 100.00% | -$321.55 | [-$959.57, +$172.46] | **0** | 20 (31.3%) |
| `WOOL_FLOOD` | 64 | 100.00% | 100.00% | -$321.55 | [-$959.57, +$172.46] | **0** | 20 (31.3%) |
| `TERMINAL_DUMPER` | 64 | 100.00% | 100.00% | -$321.55 | [-$959.57, +$172.46] | **0** | 20 (31.3%) |
| **TOTAL / OVERALL** | **576** | **99.31%** | **78.65%** | **-$6,524.25** | **[-$7,539.46, -$5,572.90]** | **119** | **325 (56.4%)** |

### Candidate: `V55_Blocked_Action` vs `V49_Meta_Fusion`

Across all 9 opponents and all 576 legs:
* **Active Legs**: 0 (0.0%)
* **Mean Paired Delta**: +$0.00
* **Rescues**: 0
* **Casualties**: 0
* **Win Rate**: 99.31% (Bit-exact parity with V49).

---

## 4. Promotion Gate Evaluation

| Gate | Requirement | V55_Post_Reveal_Shop | V55_Blocked_Action | Gate Ruling |
| :--- | :--- | :---: | :---: | :---: |
| **Gate A: Fresh Safety** | Zero fresh casualties preferred & mandatory | **119 Casualties** | 0 Casualties | Post-Reveal: **FAIL**, Blocked: **PASS** |
| **Gate B: Real Improvement** | Credible positive WR or causal rescues | 0 Rescues, -20.66% WR | 0 Rescues, +$0.00 | Post-Reveal: **FAIL**, Blocked: **FAIL** |
| **Gate C: Generalization** | Gains generalize out-of-sample | Severe regression on 6/6 elite opps | Inactive across all opps | **FAIL** (Both) |
| **Gate D: Legal Information** | Public callback state only | 100% Legal | 100% Legal | **PASS** (Both) |
| **Gate E: Prefix Preservation**| Bit-exact V49 before branch | Bit-exact through Step 215 | Bit-exact throughout | **PASS** (Both) |
| **Gate F: Complexity Discipline**| Minimal mechanism with demonstrated alpha | Complex sale withholding | Inactive wrapper | **FAIL** (Both) |

---

## 5. Formal Verdict

Neither candidate satisfies the promotion gates:
1. `V55_Post_Reveal_Shop` produces **119 catastrophic casualties** due to the engine shed-capacity crop deletion trap.
2. `V55_Blocked_Action` produces **$0.00 delta** because V49 already executes zero weed-blocked planting actions.

**Final Decision**: **`V55_RETAIN_V49`**.
`V49_Meta_Fusion` remains the unassailable sovereign incumbent.
