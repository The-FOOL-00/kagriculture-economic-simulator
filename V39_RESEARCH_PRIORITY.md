# V39 Research Priority — Objective Ranking of Intervention Opportunities

## 1. Prioritization Framework
To avoid chasing low-probability or non-recoverable noise, failure modes are scored using the formal ranking formula:

$$
Priority = Frequency \times MeanLossMargin \times Recoverability \times InterventionConfidence
$$

Where:
- **Frequency ($F$)**: Share of all live losses attributable to this mechanism ($N_{losses} = 6$).
- **Mean Loss Margin ($\bar{M}$)**: Normalized magnitude of lost cash ($\bar{M} = \min(1.0, \frac{|\text{Deficit}|}{\$5,000})$).
- **Recoverability ($R \in [0, 1]$)**: Feasibility of reversing the loss using information legally available before or at the divergence step.
- **Intervention Confidence ($C \in [0, 1]$)**: Confidence that a minimal, bounded deterministic intervention can fix the flaw without causing collateral damage / regressions to existing V35 wins.

---

## 2. Priority Ledger
| Rank | Failure Mode | Frequency ($F$) | Mean Deficit | Norm Margin ($\bar{M}$) | Recoverability ($R$) | Confidence ($C$) | **Priority Score** | Strategic Recommendation |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | **`TERMINAL_LIQUIDATION_OMISSION`** | **0.67** (4/6) | **$1,506** | 0.30 | **1.00** | **0.95** | **0.191** | **HIGH PRIORITY**: Target with Step 694 shed liquidation flush. |
| **2** | **`TERMINAL_HIRE_BURN`** | **0.33** (2/6) | **$1,313** | 0.26 | **1.00** | **0.90** | **0.077** | **HIGH PRIORITY**: Strip Day 29 `HIRE` orders in terminal phase. |
| **3** | **`LAND_TIMING_SE`** | **0.17** (1/6) | $11,630 | 1.00 | 0.30 | 0.20 | **0.010** | **REJECTED**: High casualty risk, single isolated episode. |
| **4** | **`SEAT_TIEBREAKER_ASYMMETRY`** | **0.17** (1/6) | $640 | 0.13 | 0.00 | 0.00 | **0.000** | **REJECTED**: Inherent environmental tiebreaker parity limit. |

---

## 3. Justification for Top Priority Focus
### Why Focus on `TERMINAL_LIQUIDATION_OMISSION` + `TERMINAL_HIRE_BURN`?
1. **Pervasive & Systemic**:
   Present in **5 out of 6 live losses** (83.3% coverage).
2. **Zero Downstream Drift ($D(t) = 0$ for $t < 694$)**:
   The entire development and opening chassis of V35 (steps 0 to 693) remains **100% bit-identical and untouched**. All 23 live wins and +$21.1k mean margin are completely preserved.
3. **High Recoverability**:
   The products (`MILK`, `STRAWBERRY`, `WOOL`) are already harvested and resting inside `observation['private']['shed']` at Step 694. Selling them at Step 694 instead of Step 696 captures the peak price before the opponent's sale depresses it.
4. **Immediate Rescue Potential**:
   - Episode `113183263`: Loss margin is -$791. Rescuing Milk/Strawberry price slippage adds +$915. Net result: **RESCUED TO WIN (+124)**!
   - Episode `113171441`: Loss margin is -$996. Eliminating slippage adds +$950. Net result: **RESCUED TO NEAR-TIE / WIN**!
   - Episode `113164394`: Loss margin -$1,988. Eliminating late hire burn ($639) + liquidating wool adds +$1,450. Deficit drops to negligible micro-margin.
