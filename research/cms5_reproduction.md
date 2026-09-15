# CMS-5 Exact Reproduction Gate Report

**Date:** 2026-09-09 05:53:07
**Seeds:** 50 Fixed Deterministic Seeds (Partition: VALIDATION 101–150)
**Configuration:** Official Kaggle Environments Engine (`episodeSteps=720`)
**Matchup:** Seat 0 (Candidate) vs Seat 1 (IDLE)

---

## 1. Executive Verdict: PASSED (EXACT REPRODUCTION)

| Metric | V54 Canonical | CMS-5 Faithful | Absolute Diff | Relative Error | Gate Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Mean Reward** | **$142,339.68** | **$142,339.68** | **$0.00** | **0.0000%** | **PASS (<0.5%)** |
| **Median Reward** | $142,199.50 | $142,199.50 | $0.00 | 0.0000% | PASS |
| **Reward StdDev** | $29,353.98 | $29,353.98 | $0.00 | 0.0000% | PASS |
| **Total Worker-Days** | 290.0 | 290.0 | 0.0 | 0.0000% | PASS |
| **Pasture Cows** | 9.0 | 9.0 | 0.0 | 0.0000% | PASS |
| **Pasture Sheep** | 5.0 | 5.0 | 0.0 | 0.0000% | PASS |
| **Wheat Seeds** | 187.0 | 187.0 | 0.0 | 0.0000% | PASS |
| **Wheat Sold** | 386.0 | 386.0 | 0.0 | 0.0000% | PASS |
| **Strawberries Planted** | 38.0 | 38.0 | 0.0 | 0.0000% | PASS |
| **Strawberries Sold** | 295.0 | 295.0 | 0.0 | 0.0000% | PASS |
| **Milk Sold** | 270.0 | 270.0 | 0.0 | 0.0000% | PASS |
| **Wool Sold** | 154.0 | 154.0 | 0.0 | 0.0000% | PASS |
| **Fertilizer Sold** | 335.0 | 335.0 | 0.0 | 0.0000% | PASS |
| **Melon Sold** | 72.0 | 72.0 | 0.0 | 0.0000% | PASS |
| **Market Sell Events** | 258.0 | 258.0 | 0.0 | 0.0000% | PASS |
| **Terminal Inventory** | 0.0 | 0.0 | 0.0 | 0.0000% | PASS |

---

## 2. Defined Error Metrics

- **`reward_error`**: **0.0000%** (Requirement: < 0.5000%)
- **`commodity_error`**: **0.0000 units** across all 6 commodities
- **`event_error`**: **0.0000 orders**
- **`timing_error`**: **0.0 steps** (Quadrant 2 at step 150, Quadrant 3 at step 265 in 100% of seeds)

---

## 3. Daily Cash Milestones (Mean across 50 seeds)

| Day | V54 Canonical Cash | CMS-5 Faithful Cash | Discrepancy |
| :---: | :---: | :---: | :---: |
| **Day 0** | $24.00 | $24.00 | $0.00 |
| **Day 1** | $247.00 | $247.00 | $0.00 |
| **Day 3** | $260.68 | $260.68 | $0.00 |
| **Day 5** | $909.64 | $909.64 | $0.00 |
| **Day 10** | $18,660.30 | $18,660.30 | $0.00 |
| **Day 15** | $37,001.84 | $37,001.84 | $0.00 |
| **Day 20** | $69,850.06 | $69,850.06 | $0.00 |
| **Day 25** | $108,050.36 | $108,050.36 | $0.00 |
| **Day 29** | $142,339.68 | $142,339.68 | $0.00 |

CMS-5 reproduces canonical V54 with **zero drift** and **machine-level determinism**. The reproduction gate is fully satisfied.
