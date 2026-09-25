# V44 Land Economics & Capital Opportunity Cost Report

**Document ID:** `research/v44/reports/V44_LAND_ALPHA_REPORT.md`  
**Date:** 2026-09-25  
**Repository:** `The-FOOL-00/kagriculture-economic-simulator`  
**Scope:** In-depth forensic evaluation of land expansion timing, quadrant payback horizons, and the resolution of the historical land expansion controversy.

---

## 1. Executive Summary

In V41, an early truncated evaluation suggested a massive `+$3,385` cash increase from land expansion. V42 later identified this as a truncation artifact, proving that early land expansion failed when rolled out to Step 719.

In V44, we conducted the definitive full-terminal land economics study, testing:
1. **`ADVANCE_LAND_1` (NE Quadrant, Cost $1,000):** Accelerating Land 1 purchase to Step 125.
2. **`ADVANCE_LAND_2` (SW Quadrant, Cost $2,000):** Accelerating Land 2 purchase to Step 230 (A7 baseline executes around Step 265).
3. **`PURCHASE_LAND_3` (SE Quadrant, Cost $4,000):** Purchasing the 4th quadrant at Step 350.
4. **`DEFER_LAND_3` (SE Quadrant, Cost $4,000):** Explicitly forbidding Land 3 purchases.

### Key Empirical Findings:

* **Land 3 is Deeply Destructive:** Purchasing Land 3 destroys **`-$2,740.04`** in mean cash, crashes win rate to **37.5%**, and generates **13 casualties**. Clearing and developing 48 additional tiles costs far more labor and capital than the remaining turns can amortize.
* **The Land 2 Outlier Trap:** Accelerating Land 2 displayed a misleading mean cash delta of **`+$2,009.12`**, but suffered a catastrophic **7 casualties** and P5 downside of **`-$12,064.25`**. On seeds where workforce or cash reserves are constrained, spending $2,000 early creates liquidity failure and stalls crop planting.
* **A7's Baseline Land Timing is Exceptionally Well-Calibrated:** A7 buys Land 1 around Step 150 (when cash is safely > $2,000) and Land 2 around Step 265 (when cash is > $15,000), while deliberately skipping Land 3. Attempting to accelerate these purchases creates severe capital risk.

---

## 2. Experimental Data Table

| Candidate Strategy | Target Quadrant | Price ($) | Mean Cash $\Delta$ | Mean Margin $\Delta$ | Casualties | Rescues | Win Rate (%) | Strategic Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **`ADVANCE_LAND_1`** | NE (Quad 2) | $1,000 | $0.00 | $0.00 | **0** | 0 | 91.7% | Neutral (A7 already buys promptly) |
| **`ADVANCE_LAND_2`** | SW (Quad 3) | $2,000 | +$2,009.12 | -$1,867.00 | **7** | 1 | 66.7% | **REJECTED (Severe Casualties)** |
| **`PURCHASE_LAND_3`**| SE (Quad 4) | $4,000 | -$2,740.04 | -$4,332.75 | **13** | 0 | 37.5% | **REJECTED (Catastrophic)** |
| **`DEFER_LAND_3`** | SE (Quad 4) | $4,000 | $0.00 | $0.00 | **0** | 0 | 91.7% | Verified Safe (A7 naturally skips) |

---

## 3. Mathematical Payback Decomposition

The marginal revenue of an additional quadrant of land is bounded by the available farm hands and remaining turns:
$$\text{ROI}(\text{Land}) = \sum_{t=t_{\text{buy}}}^{718} \min(\text{Tiles}_{\text{unlocked}}, \text{LaborCapacity}_t) \cdot \mathbb{E}[\text{YieldProfit}_t] - \text{Cost}_{\text{land}}$$

1. **Quadrant 2 (NE, $1,000):** Purchased at Step 150, leaves 568 steps. Amortization requires only $1.76/step. Easily profitable.
2. **Quadrant 3 (SW, $2,000):** Purchased at Step 265, leaves 453 steps. Amortization requires $4.41/step. Profitable when farm hand count exceeds 15.
3. **Quadrant 4 (SE, $4,000):** Even if purchased at Step 350, leaves 368 steps. Amortization requires **$10.87/step**. Because farm hands are already fully occupied weeding and harvesting Quadrants 1–3, Quadrant 4 tiles remain idle, resulting in a net $4,000 capital loss.

---

## 4. Final Policy Recommendation

* **Prohibit Land 3:** Explicitly maintain A7's refusal to buy Quadrant 4.
* **Preserve Land 1 & 2 Timing:** Do not accelerate Land 1 or Land 2 ahead of A7's safe liquidity thresholds.
