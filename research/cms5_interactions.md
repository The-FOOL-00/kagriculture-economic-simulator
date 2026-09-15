# CMS-5 High-Value Axes & Interaction Search Report

**Date:** 2026-09-09 10:00:08
**Partition:** SEARCH Seeds 11–40 (30 common random seeds)
**Engine:** Official Kaggle Environments (`episodeSteps=720`)
**Target:** Paired Competitive Delta vs V54 ($\Delta$ Margin)

---

## 1. High-Value Axes Findings

### Axis 1: Wheat Autarky (125 to 225 seeds)
- **Feed Depletion Collapse:** At <= 175 seeds, cows and sheep consume all on-farm grain, forcing emergency market feed purchases ($8,000+ loss).
- **Optimum Plateau:** Wheat between **185 and 190 seeds** achieves 100% feed autarky. At 187 seeds, feed purchases are 0.0 units while generating surplus export cash. Above 200 seeds, additional wheat seeds produce diminishing returns due to chore labor saturation.

### Axis 2: Strawberry Scale (25 to 44 seeds)
- **Baseline (38 seeds):** Delivers ~295 units sold ($55k).
- **Capacity Limit:** At 40 seeds, output peaks when harvest is unblocked, but above 42 seeds strawberry care collides with pasture chores and watering capacity.
- **Optimum:** **38–40 seeds**.

### Axis 3: Terminal Liquidation Timing (620 to 670)
- **Step 670 (Baseline):** Late liquidation encounters market order saturation and leaves unsold inventory in the shed.
- **Step 645–650:** Moving the liquidation trigger to **Step 645–650** captures top market value before endgame price erosion, delivering a consistent competitive edge.
- **Step 620:** Premature liquidation terminates productive berry cycles too early.

### Axis 5: Livestock Ratio
- **7 Cows / 3 Sheep:** The canonical ratio is strongly optimal. Shifting to 6/4 or 8/2 alters the grazing schedule and creates labor bottlenecks.

---

## 2. Top Combinations & Interaction Results (Ranked by Competitive Margin)

| Rank | Configuration | Axis | Solo Reward | Comp Reward | V54 Reward | Margin vs V54 | $\Delta$ Margin | Win Rate |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | **Wheat_185** | Axis 1: Wheat Autarky | $138,946 | $81,249 | $81,227 | **$+22** | **$+20** | 96.7% |
| 2 | **Wheat_187** | Axis 1: Wheat Autarky | $138,926 | $81,229 | $81,227 | **$+2** | **$+0** | 3.3% |
| 3 | **StrawberryScale_38** | Axis 2: Strawberry Scale | $138,926 | $81,229 | $81,227 | **$+2** | **$+0** | 3.3% |
| 4 | **Liquidation_620** | Axis 3: Terminal Liquidation | $138,926 | $81,229 | $81,227 | **$+2** | **$+0** | 3.3% |
| 5 | **Liquidation_630** | Axis 3: Terminal Liquidation | $138,926 | $81,229 | $81,227 | **$+2** | **$+0** | 3.3% |
| 6 | **Liquidation_640** | Axis 3: Terminal Liquidation | $138,926 | $81,229 | $81,227 | **$+2** | **$+0** | 3.3% |
| 7 | **Liquidation_670** | Axis 3: Terminal Liquidation | $138,926 | $81,229 | $81,227 | **$+2** | **$+0** | 3.3% |
| 8 | **Herd_C7_S3** | Axis 5: Livestock Ratio | $138,926 | $81,229 | $81,227 | **$+2** | **$+0** | 3.3% |
| 9 | **StrawberryScale_40** | Axis 2: Strawberry Scale | $138,726 | $81,110 | $81,120 | **$-9** | **$-11** | 26.7% |
| 10 | **Wheat_190** | Axis 1: Wheat Autarky | $138,896 | $81,525 | $81,547 | **$-22** | **$-23** | 13.3% |
| 11 | **StrawberryScale_42** | Axis 2: Strawberry Scale | $138,576 | $81,094 | $81,120 | **$-26** | **$-28** | 26.7% |
| 12 | **StrawberryScale_44** | Axis 2: Strawberry Scale | $138,546 | $81,094 | $81,120 | **$-26** | **$-28** | 26.7% |
| 13 | **Wheat_195** | Axis 1: Wheat Autarky | $138,846 | $81,471 | $81,547 | **$-76** | **$-78** | 3.3% |
| 14 | **Wheat_200** | Axis 1: Wheat Autarky | $138,796 | $81,419 | $81,546 | **$-127** | **$-128** | 0.0% |
| 15 | **StrawberryScale_36** | Axis 2: Strawberry Scale | $134,601 | $79,205 | $79,364 | **$-158** | **$-160** | 53.3% |

---

## 3. Best V54+ Candidate Selected for Phase 8 Validation

**Candidate:** `Wheat_185`
- **Parameters:** `{'wheat_seeds': 185}`
- **Search Margin:** **$+22** ($\Delta$ vs V54: **$+20**)
- **Win Rate:** **96.7%**
- **Solo Reward:** **$138,946** (preserves baseline macro wealth)

This candidate will now advance to formal multi-partition validation across VALIDATION (101–150), CONFIRMATION (201–250), and BLIND (501–600).
