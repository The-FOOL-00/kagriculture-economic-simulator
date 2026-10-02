# V51 Final Fresh Validation Ladder (Phase 11 & 13)

**Benchmark Protocol**:
- **Dataset**: 32 strictly disjoint fresh seeds `[250600..250631]`
- **Protected Holdouts Quarantined**: `214200–214249`, `340090–340199`, `249695–249734` (0 holdout seeds accessed)
- **Opponent Suite (9 Total)**:
  - **Elite Suite (6)**: V44 (`v44_economic_portfolio`), `dmitrii_lb2800`, `tetsutani_pasture`, `kaitofukami_v48_3009`, `indarkarhana_top10`, `saiteja_mega_3000`
  - **Adversarial Suite (3)**: `DAIRY_FLOOD`, `WOOL_FLOOD`, `TERMINAL_DUMPER`
- **Volume**: 32 seeds $\times$ 2 seats $\times$ 9 opponents = **576 paired legs per candidate** (2,304 total 719-step simulation matches)
- **Runtime Environment**: Python 3.12 (10 CPU parallel workers), zero Kaggle submissions.

---

## 1. Grand Candidate Evaluation Matrix

| Candidate Key | Description | Total Legs | Mean Delta vs V49 ($) | 95% Bootstrap CI | Overall WR (%) | Rescues | Casualties | Active Legs | Promotion Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **V49_Meta_Fusion** | Frozen Champion Baseline | 576 | +$0.00 | [+$0.00, +$0.00] | 99.31% (572/576) | 0 | 0 | 0 / 576 (0.0%) | **INCUMBENT (RETAINED)** |
| **V51_Blocked_Repair** | Isolated Weed & Tile Blocker Repair | 576 | +$0.00 | [+$0.00, +$0.00] | 99.31% (572/576) | 0 | 0 | 0 / 576 (0.0%) | **RESEARCH ARTIFACT (INERT)** |
| **V51_Midgame_Reset_Variant** | Early Route Re-Evaluation (Step 72) | 576 | +$0.00 | [+$0.00, +$0.00] | 99.31% (572/576) | 0 | 0 | 0 / 576 (0.0%) | **REJECTED (INERT)** |
| **V51_Sell_Reorder_Variant** | Rival Exposure Priority Reordering | 576 | -$199.17 | [-$221.75, -$177.38] | 97.22% (560/576) | 0 | 12 | 394 / 576 (68.4%) | **REJECTED (DEGRADATION)** |

---

## 2. Suite Breakdown: Elite vs. Adversarial

### A. Elite Opponent Suite (384 Legs per Candidate)
| Candidate Key | Elite Legs | Mean Delta vs V49 ($) | 95% Bootstrap CI | Elite WR (%) | Rescues | Casualties |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **V49_Meta_Fusion** | 384 | +$0.00 | [+$0.00, +$0.00] | 98.96% (380/384) | 0 | 0 |
| **V51_Blocked_Repair** | 384 | +$0.00 | [+$0.00, +$0.00] | 98.96% (380/384) | 0 | 0 |
| **V51_Midgame_Reset_Variant** | 384 | +$0.00 | [+$0.00, +$0.00] | 98.96% (380/384) | 0 | 0 |
| **V51_Sell_Reorder_Variant** | 384 | -$296.71 | [-$326.99, -$268.39] | 95.83% (368/384) | 0 | 12 |

### B. Adversarial Opponent Suite (192 Legs per Candidate)
| Candidate Key | Adv Legs | Mean Delta vs V49 ($) | 95% Bootstrap CI | Adv WR (%) | Rescues | Casualties |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **V49_Meta_Fusion** | 192 | +$0.00 | [+$0.00, +$0.00] | 100.00% (192/192) | 0 | 0 |
| **V51_Blocked_Repair** | 192 | +$0.00 | [+$0.00, +$0.00] | 100.00% (192/192) | 0 | 0 |
| **V51_Midgame_Reset_Variant** | 192 | +$0.00 | [+$0.00, +$0.00] | 100.00% (192/192) | 0 | 0 |
| **V51_Sell_Reorder_Variant** | 192 | -$4.09 | [-$7.58, -$1.30] | 100.00% (192/192) | 0 | 0 |

---

## 3. Per-Opponent Deep Dive (64 Legs per Opponent)

### A. V51_Blocked_Repair vs. Baseline V49
| Opponent Family | Mean Delta ($) | 95% Bootstrap CI | V49 WR (%) | V51 WR (%) | Casualties | Rescues | Active Matches |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `V44` | +$0.00 | [+$0.00, +$0.00] | 93.75% | 93.75% | 0 | 0 | 0 / 64 |
| `dmitrii_lb2800` | +$0.00 | [+$0.00, +$0.00] | 100.00% | 100.00% | 0 | 0 | 0 / 64 |
| `tetsutani_pasture` | +$0.00 | [+$0.00, +$0.00] | 100.00% | 100.00% | 0 | 0 | 0 / 64 |
| `kaitofukami_v48_3009` | +$0.00 | [+$0.00, +$0.00] | 100.00% | 100.00% | 0 | 0 | 0 / 64 |
| `indarkarhana_top10` | +$0.00 | [+$0.00, +$0.00] | 100.00% | 100.00% | 0 | 0 | 0 / 64 |
| `saiteja_mega_3000` | +$0.00 | [+$0.00, +$0.00] | 100.00% | 100.00% | 0 | 0 | 0 / 64 |
| `DAIRY_FLOOD` | +$0.00 | [+$0.00, +$0.00] | 100.00% | 100.00% | 0 | 0 | 0 / 64 |
| `WOOL_FLOOD` | +$0.00 | [+$0.00, +$0.00] | 100.00% | 100.00% | 0 | 0 | 0 / 64 |
| `TERMINAL_DUMPER` | +$0.00 | [+$0.00, +$0.00] | 100.00% | 100.00% | 0 | 0 | 0 / 64 |

*Observation*: Exactly zero action divergences observed across all 576 fresh validation legs (414,144 individual unit turns). In every single state where no weed blocker is present (and because V49 already contains pre-scripted DIG actions for periphery weeds), V51 Blocked Repair executes 100% bit-exact parity with V49.

### B. V51_Sell_Reorder_Variant vs. Baseline V49
| Opponent Family | Mean Delta ($) | 95% Bootstrap CI | V49 WR (%) | Cand WR (%) | Casualties | Rescues | Active Matches |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `V44` | -$694.14 | [-$787.28, -$604.11] | 93.75% | 75.00% | **12** | 0 | 64 / 64 |
| `dmitrii_lb2800` | -$387.98 | [-$414.88, -$360.22] | 100.00% | 100.00% | 0 | 0 | 64 / 64 |
| `tetsutani_pasture` | -$339.86 | [-$402.64, -$287.53] | 100.00% | 100.00% | 0 | 0 | 64 / 64 |
| `kaitofukami_v48_3009` | -$178.67 | [-$218.42, -$139.63] | 100.00% | 100.00% | 0 | 0 | 64 / 64 |
| `indarkarhana_top10` | -$115.80 | [-$154.67, -$80.89] | 100.00% | 100.00% | 0 | 0 | 63 / 64 |
| `saiteja_mega_3000` | -$63.78 | [-$97.64, -$31.33] | 100.00% | 100.00% | 0 | 0 | 63 / 64 |
| `DAIRY_FLOOD` | -$7.28 | [-$13.25, -$1.88] | 100.00% | 100.00% | 0 | 0 | 6 / 64 |
| `WOOL_FLOOD` | -$5.00 | [-$10.59, -$0.50] | 100.00% | 100.00% | 0 | 0 | 6 / 64 |
| `TERMINAL_DUMPER` | +$0.00 | [+$0.00, +$0.00] | 100.00% | 100.00% | 0 | 0 | 0 / 64 |

*Observation*: Reordering sell slots in V49's order priority queue systematically delays early-game crop cash returns by prioritizing animal products before large livestock yields exist. Against V44, this caused 12 catastrophic casualties where early capital bottlenecks delayed farm-hand recruitment by multiple turns.

---

## 4. Governance Verdict

Under Section 14 promotion rules:
1. `V51_Blocked_Repair`: 0 casualties, WR == V49, but **paired delta is +$0.00**, 0 natural activations, and 0 historical losses rescued.
2. Section 12 Rule: *"If V49 naturally generates essentially no relevant weed-blocked actions: STOP. Do not force the mechanism into the candidate."*
3. All midgame and top-meta transfer variants either remain completely inert (M3) or produce severe capital degradation and casualties (M4, M5).

**MANDATORY GOVERNANCE DECISION**:
`V49_RETAIN`
