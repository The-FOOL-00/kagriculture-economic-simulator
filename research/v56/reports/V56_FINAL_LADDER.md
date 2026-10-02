# V56 — Final Benchmark Ladder Report

## 1. Executive Ladder Summary

The V56 research program evaluated the sovereign incumbent **V49_Meta_Fusion** (SHA256: `8CAFF63068BF68A34A9141D48F771D9007AFC0DFA792179A737ECCE919FBBD11`) against our authoritative 576-leg fresh benchmark ladder on `kaggle-environments 1.32.7`.

Across all 576 fresh paired legs:
- **Total Legs**: 576
- **Wins**: 572
- **Losses**: 4
- **Draws**: 0
- **Win Rate**: **99.31%** (572 / 576)
- **Casualties vs Elite Suite**: **0**
- **Casualties vs Adversarial Suite**: **0**

---

## 2. Per-Opponent Ladder Performance

| Opponent | Category | Legs | Wins | Losses | Win Rate | Mean Margin | Casualties | Rescues |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **v44_economic_portfolio** | Elite (Top-3) | 64 | 60 | 4 | **93.75%** | +$6,842.15 | 0 | 0 |
| **dmitrii_lb2800** | Elite (LB #1) | 64 | 64 | 0 | **100.00%** | +$14,218.40 | 0 | 0 |
| **tetsutani_pasture** | Elite (Pasture) | 64 | 64 | 0 | **100.00%** | +$12,890.75 | 0 | 0 |
| **kaitofukami_v48_3009** | Elite (Macro) | 64 | 64 | 0 | **100.00%** | +$15,410.20 | 0 | 0 |
| **indarkarhana_top10** | Elite (Top-10) | 64 | 64 | 0 | **100.00%** | +$11,984.60 | 0 | 0 |
| **saiteja_mega_3000** | Elite (Top-5) | 64 | 64 | 0 | **100.00%** | +$13,450.10 | 0 | 0 |
| **DAIRY_FLOOD** | Adversarial | 64 | 64 | 0 | **100.00%** | +$24,102.80 | 0 | 0 |
| **WOOL_FLOOD** | Adversarial | 64 | 64 | 0 | **100.00%** | +$22,450.50 | 0 | 0 |
| **TERMINAL_DUMPER** | Adversarial | 64 | 64 | 0 | **100.00%** | +$28,910.30 | 0 | 0 |
| **TOTAL BENCHMARK** | **All 9 Opponents** | **576** | **572** | **4** | **99.31%** | **+$16,706.64** | **0** | **0** |

---

## 3. The Four Fresh Loss Worlds

All 4 losses in the 576-leg suite occurred against **`v44_economic_portfolio`**:

| Loss ID | Seed | Seat | Opp Seat | V49 Cash | V44 Cash | Margin | Rescue Margin | Decisive Mechanism |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **L1** | 250617 | 0 | 1 | $115,527.00 | $116,389.00 | -$862.00 | $863.00 | Step 697 market queue priority |
| **L2** | 250617 | 1 | 0 | $115,527.00 | $116,389.00 | -$862.00 | $863.00 | Step 697 market queue priority |
| **L3** | 250621 | 0 | 1 | $116,047.00 | $116,129.00 | -$82.00 | $83.00 | Step 697 market queue priority |
| **L4** | 250621 | 1 | 0 | $116,047.00 | $116,129.00 | -$82.00 | $83.00 | Step 697 market queue priority |

Against the other 8 opponents, V49 is **flawless: 512W / 0L (100.00% WR)**.

---

## 4. Counterfactual Rescue Audit

Four micro-interventions were evaluated to test whether the 4 losses could be flipped:

| Intervention | Historical Rescues | Historical Worsened | Fresh Casualties | Gate A Status |
| :--- | :---: | :---: | :---: | :--- |
| **Price-Sorted Sell Queue (Step 696)** | 0 / 4 | 4 / 4 | 4 (Seeds 250616, 250631) | **FAILED (Casualties)** |
| **Price-Sorted Sell Queue (Step 600)** | 0 / 4 | 4 / 4 | 4 (Seeds 250616, 250631) | **FAILED (Casualties)** |
| **Pre-Emptive Liquidation (Step 696)** | 0 / 4 | 4 / 4 | N/A (Margin -$3,072) | **FAILED (Collapse)** |
| **Step 0 Wash Suppression** | 0 / 4 | 4 / 4 | N/A (Margin -$97,000+) | **FAILED (Tape corruption)** |

---

## 5. Decision

**V56_RETAIN_V49**
- Incumbent `V49_Meta_Fusion` retained with 99.31% win rate and 0 casualties.
- No rescue candidate promoted.
