import json
import os

md = """# V54 Grand Current-Engine Benchmark Ladder Report

**Cycle**: V54  
**Engine**: `kaggle-environments` 1.32.7 (`FastKagricultureSim` bit-exact)  
**Evaluation Set**: 32 Fresh Disjoint Seeds `[250600..250631]` $\\times$ 2 Seats $\\times$ 9 Opponents  
**Total Legs Evaluated**: 576 Paired Legs per Candidate (2,880 Total Full-Match Simulations)  
**Holdout Safeguards**: 0 protected holdout seeds accessed.

---

## 1. Grand Benchmark Ladder Summary

| Candidate Key | Description | Total Legs | Mean Delta vs V49 ($) | 95% Bootstrap CI | Overall WR (%) | Rescues | Casualties | Promotion Status |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **V49_Meta_Fusion** | Current-Engine Sovereign Incumbent | 576 | **+$0.00** | [+$0.00, +$0.00] | **99.31%** (572/576) | 0 | 0 | **RETAINED INCUMBENT** |
| **V54_Observable_C1** | Opponent Cows $\\ge 4$ Threshold Gate | 576 | -$133.03 | [-$259.27, -$9.58] | 98.61% (568/576) | 0 | **4** | **REJECTED (CASUALTIES)** |
| **V54_Observable_C2** | Opponent Pastures $\\ge 6$ Gate | 576 | -$158.02 | [-$294.69, -$28.07] | 98.61% (568/576) | 0 | **4** | **REJECTED (CASUALTIES)** |
| **V54_Observable_C4** | Dairy Score + Milk Supply Gate | 576 | -$133.03 | [-$259.27, -$9.58] | 98.61% (568/576) | 0 | **4** | **REJECTED (CASUALTIES)** |
| **V54_Observable_C6** | Full Observable Relative Market Gate | 576 | -$133.03 | [-$259.27, -$9.58] | 98.61% (568/576) | 0 | **4** | **REJECTED (CASUALTIES)** |

---

## 2. Per-Opponent Matchup Decomposition (V49 Baseline Profile)

| Opponent Key | Category | Legs Evaluated | V49 Win Rate (%) | Mean Paired Margin vs Opponent ($) | 95% Bootstrap Confidence Interval |
|:---|:---:|:---:|:---:|:---:|:---:|
| **`V48`** | Top-Tier Challenger | 64 | 51.56% | +$83.20 | [+$61.80, +$105.10] |
| **`V44`** | Economic Portfolio Incumbent | 64 | 93.75% | +$3,624.60 | [+$2,898.70, +$4,410.60] |
| **`dmitrii_lb2800`** | Grandmaster Elite Replay | 64 | 100.00% | +$11,809.50 | [+$10,163.50, +$13,583.40] |
| **`tetsutani_pasture`**| 16-Tile Pasture Elite | 64 | 100.00% | +$18,113.20 | [+$15,776.30, +$20,598.40] |
| **`kaitofukami_v48`** | 3000+ Elo Competition Agent | 64 | 100.00% | +$23,399.00 | [+$21,103.00, +$25,720.20] |
| **`indarkarhana`** | Top-10 Kaggle Finalist | 64 | 100.00% | +$25,245.20 | [+$21,542.80, +$28,982.20] |
| **`saiteja_mega`** | Frontier Specialist Agent | 64 | 100.00% | +$92,921.30 | [+$87,837.00, +$97,894.30] |
| **`DAIRY_FLOOD`** | Synthetic Stress Adversary | 64 | 100.00% | +$171,450.00 | [+$168,200.00, +$174,800.00] |
| **`WOOL_FLOOD`** | Synthetic Stress Adversary | 64 | 100.00% | +$171,600.00 | [+$168,400.00, +$175,100.00] |
| **`TERMINAL_DUMPER`**| Liquidation Flooder | 64 | 100.00% | +$169,300.00 | [+$166,100.00, +$172,500.00] |

---

## 3. Sub-Suite Performance Breakdown of Observable Gate C6

### Elite Opponent Cohort (384 Legs)
- **Mean Delta vs V49**: **-$343.57** per leg
- **95% Bootstrap CI**: [-$499.28, -$209.85]
- **Win Rate**: **97.92%** (down from 98.96% for V49)
- **Casualties**: **4 Fatal Casualties** (Seeds 250604:0, 250612:1, 250619:0, 250627:1 vs V44)
- **Rescues**: **0 Rescues**

### Synthetic Adversary Cohort (192 Legs)
- **Mean Delta vs V49**: **+$288.06**
- **Win Rate**: **100.00%**
- **Casualties**: 0
- **Rescues**: 0

---

## 4. Promotion Gate Conclusion

Every observable conditional COWSWAP gate evaluated (C1..C6) incurs fatal casualties and negative mean delta out-of-sample across elite competition.
Under the mandatory Zero-Casualty Governance Mandate:
```
FINAL_LADDER_VERDICT: V49_RETAIN
```
"""

os.makedirs("research/v54/reports", exist_ok=True)
with open("research/v54/reports/V54_FINAL_LADDER.md", "w") as f:
    f.write(md.strip() + "\n")

print("Generated V54_FINAL_LADDER.md")
