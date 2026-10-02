# V53 Final Current-Engine Benchmark Ladder (Section 17)

## Benchmark Protocol
- **Dataset**: 32 strictly disjoint fresh seeds `[250600..250631]`
- **Protected Holdouts Quarantined**: `214200–214249`, `340090–340199`, `249695–249734` (0 holdout seeds accessed)
- **Discovery Seeds Quarantined**: `250400–250527` (0 discovery seeds accessed)
- **Opponent Suite (9 Total)**:
  - **Elite Suite (6)**: `V44`, `dmitrii_lb2800`, `tetsutani_pasture`, `kaitofukami_v48_3009`, `indarkarhana_top10`, `saiteja_mega_3000`
  - **Adversarial Suite (3)**: `DAIRY_FLOOD`, `WOOL_FLOOD`, `TERMINAL_DUMPER`
- **Volume**: 32 seeds $\times$ 2 seats $\times$ 9 opponents = **576 paired legs per candidate** (2,304 total 719-step simulation matches)
- **Engine**: Verified bit-exact parity with official `kaggle-environments` 1.32.7.
- **Kaggle Submissions**: Exactly 0.

---

## 1. Grand Candidate Evaluation Matrix

| Candidate Key | Description | Total Legs | Mean Delta vs V49 ($) | 95% Bootstrap CI | Overall WR (%) | Rescues | Casualties | Promotion Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **V49_Meta_Fusion** | Current-Engine Incumbent Reference | 576 | +$0.00 | [+$0.00, +$0.00] | **99.31%** (572/576) | 0 | 0 | **INCUMBENT (RETAINED)** |
| **V53_Conditional_COWSWAP_C6** | Surgical Causal Gate on COWSWAP | 576 | -$133.03 | [-$259.27, -$9.58] | 98.61% (568/576) | 0 | **4** | **REJECTED (CASUALTIES)** |
| **V53_Synthesized_9C4S** | Synthesized 9C/4S Choreography | 576 | -$10,250.50 | [-$12,161.60, -$8,323.23] | 79.17% (456/576) | 0 | **116** | **REJECTED (COLLAPSE)** |
| **V53_Combined_9C4S_C6** | Synthesized 9C/4S + C6 Gate | 576 | -$10,250.50 | [-$12,161.60, -$8,323.23] | 79.17% (456/576) | 0 | **116** | **REJECTED (COLLAPSE)** |

---

## 2. Suite Breakdown: Elite vs. Adversarial

### A. Elite Opponent Suite (384 Legs per Candidate)
| Candidate Key | Elite Legs | Mean Delta vs V49 ($) | 95% Bootstrap CI | Elite WR (%) | Rescues | Casualties |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **V49_Meta_Fusion** | 384 | +$0.00 | [+$0.00, +$0.00] | **98.96%** (380/384) | 0 | 0 |
| **V53_Conditional_COWSWAP_C6** | 384 | -$343.57 | [-$478.11, -$219.04] | 97.92% (376/384) | 0 | **4** |
| **V53_Synthesized_9C4S** | 384 | -$5,646.46 | [-$7,312.18, -$4,082.90] | 68.75% (264/384) | 0 | **116** |
| **V53_Combined_9C4S_C6** | 384 | -$5,646.46 | [-$7,312.18, -$4,082.90] | 68.75% (264/384) | 0 | **116** |

### B. Adversarial Opponent Suite (192 Legs per Candidate)
| Candidate Key | Adv Legs | Mean Delta vs V49 ($) | 95% Bootstrap CI | Adv WR (%) | Rescues | Casualties |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **V49_Meta_Fusion** | 192 | +$0.00 | [+$0.00, +$0.00] | **100.00%** (192/192) | 0 | 0 |
| **V53_Conditional_COWSWAP_C6** | 192 | +$288.06 | [+$124.50, +$462.18] | 100.00% (192/192) | 0 | 0 |
| **V53_Synthesized_9C4S** | 192 | -$19,458.58 | [-$22,810.45, -$16,102.30] | 100.00% (192/192) | 0 | 0 |
| **V53_Combined_9C4S_C6** | 192 | -$19,458.58 | [-$22,810.45, -$16,102.30] | 100.00% (192/192) | 0 | 0 |

---

## 3. Causal Breakdown of Candidate Failures

1. **The COWSWAP Invariant**:
   - `V53_Conditional_COWSWAP_C6` was engineered with a surgical causal predicate (`has_egg_shop and not has_milk_shop and milk_price >= egg_price * 1.5`).
   - While this predicate successfully rescues L07..L10 on historical loss seeds where V44 invested in dairy, it simultaneously degrades Seed 250416 (where V44 did not invest in dairy) by -$1,134.
   - Out-of-sample across 576 legs, this inability to anticipate whether a rival will commit to dairy causes **4 casualties** against V44 and an average penalty of **-$343.57** across the elite suite.
2. **The Herd Resynthesis Reality**:
   - The public 3100+ Elo claims of `9C / 4S` or `9C / 5S` superiority belong to an entirely different architectural paradigm: continuous dynamic A* pathing with 16 pasture tiles and dynamic task dispatch.
   - Forcing a `9C / 4S` animal allocation onto a deterministic choreographic tape collapses farm coordination (-$10,250 delta, 116 casualties), as workers cannot maintain synchronized feed delivery and harvest collection without dynamic re-routing.

---

## 4. Promotion Gate Audit (Section 18)

| # | Criterion | Required Threshold | Observed Value | Pass / Fail |
|---|---|---|---|---|
| 1 | Zero Casualties | Exactly 0 casualties vs baseline | **4 casualties** (C6), **116 casualties** (9C4S) | **FAIL** |
| 2 | Current-Engine Fresh WR | $\ge$ V49 WR (99.31%) | 98.61% (C6), 79.17% (9C4S) | **FAIL** |
| 3 | Positive Paired Delta | Strict positive delta (> +$0.00) | -$133.03 (C6), -$10,250.50 (9C4S) | **FAIL** |
| 4 | Actual V49 Rescue | $\ge$ 1 fresh rescue out-of-sample | 0 rescues | **FAIL** |
| 5 | Natural Activation | Activates naturally in game | Verified | **PASS** |
| 6 | Generalization Across Elite | Positive edge across elite bots | Negative across elite suite | **FAIL** |
| 7 | No Catastrophic Herd Regime | Robust to composition | Severe collapse under 9C/4S | **FAIL** |
| 8 | Terminal Liquidation Integrity | Clean liquidation | Preserved | **PASS** |
| 9 | No Choreography Drift | Zero unintended action drift | Preserved | **PASS** |
| 10 | Clean Causal Mechanism | Sound economic explanation | Causal mechanisms fully mapped | **PASS** |

**FINAL GOVERNANCE VERDICT**:
`V49_RETAIN`
