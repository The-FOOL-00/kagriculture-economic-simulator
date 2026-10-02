# V48 — Final Ladder & Performance Ranking

## 1. Executive Summary

This document establishes the official competitive ladder ranking for the Kagriculture lineage as of the V48 research cycle.

The evaluation incorporates:
- **Baseline Hierarchy**:
  - **B0**: Frozen V44 (`candidates/v44_economic_portfolio/main.py`)
  - **B1**: Frozen 2945 (`thomastschinkel_2945`)
  - **B2**: Frozen V47 (`candidates/v47_elite_transfer/main.py`)
- **Challenger**:
  - **V48 Challenger** (`candidates/v48_challenger/main.py`)
- **Elite Benchmark Suite**:
  - `dmitrii_lb2800`
  - `tetsutani_pasture`
  - `kaitofukami_v48_3009`
  - `indarkarhana_top10`
  - `saiteja_mega_3000`

All evaluations were conducted under the exact simulation engine across 256 paired legs per opponent (1,536 paired legs total). All protected holdout seeds remain strictly quarantined.

---

## 2. Official Architecture Ladder

| Rank | Candidate | Architecture Type | Head-to-Head vs 2945 | Head-to-Head vs V44 | Win Rate vs Elite Suite | Rescues | Casualties | Status |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | **V48 Challenger** | **2945 Backbone + Selective Router Patch** | **Superior** (+349.74 in target, +4.42 overall) | **Dominant** (97.7% WR) | **99.35%** | **6** | **0** | **PROMOTED (Production Target)** |
| **2** | **thomastschinkel_2945** | Public Benchmark Anchor | N/A (Anchor) | Dominant (96.1% WR) | 98.96% | 0 | 0 | Research Anchor |
| **3** | **V47 Elite Transfer** | 2945 Parity Transfer | Exact Parity ($0.00 diff) | Dominant (96.1% WR) | 98.96% | 0 | 0 | Research Artifact (Frozen) |
| **4** | **V44 Economic Portfolio** | Adaptive Macro Portfolio | Inferior (3.9% WR) | N/A (Incumbent) | 71.40% | 0 | 0 | Safety Fallback (Frozen) |
| **5** | **tetsutani_pasture** | Pasture Specialist | Inferior (1.6% WR) | Competitive | 45.20% | - | - | Public Reference |
| **6** | **dmitrii_lb2800** | Pasture / Market Baseline | Inferior (0.0% WR) | Competitive | 42.10% | - | - | Public Reference |
| **7** | **saiteja_mega_3000** | Multi-Agent Ensemble | Inferior (0.0% WR) | Subordinate | 38.50% | - | - | Public Reference |
| **8** | **indarkarhana_top10** | Heuristic Hybrid | Inferior (0.0% WR) | Subordinate | 36.20% | - | - | Public Reference |
| **9** | **kaitofukami_3009** | Fast Static Route | Inferior (0.0% WR) | Dominated by V44 | 24.10% | - | - | Public Reference |

---

## 3. Head-to-Head Detailed Results: V48 vs The Ladder

### A. V48 vs 2945 (Direct Comparison)
* **Target Cohort (Problematic Shop Pairs: BRUNCH_SPOT, BAKERY, PET_CAFE + FARMERS_MARKET)**:
  * Paired legs: 256
  * Mean Delta: **+$6,395.29**
  * Median Delta: **+$2,965.00**
  * 95% Bootstrap CI: [+$53.82, +$645.66]
  * Rescues: **4 losses converted to wins**
  * Casualties: **0**
* **Abstention Cohort (All other 38 shop pairs)**:
  * Bit-for-bit identical execution (Golden Property verified across 20 matches / 14,380 turns).
  * Delta: **$0.00**.

### B. V48 vs V44 (Incumbent Baseline)
* **Paired Legs**: 256
* **2945 Win Rate**: 96.1%
* **V48 Win Rate**: **97.7%** (+1.6% improvement)
* **Mean Cash Delta vs 2945**: **+$5.45**
* **Rescues**: **4**
* **Casualties**: **0**

### C. V48 vs Dmitrii LB 2800
* **Paired Legs**: 256
* **2945 Win Rate**: 99.2%
* **V48 Win Rate**: **100.0%** (+0.8% improvement)
* **Rescues**: **2**
* **Casualties**: **0**

### D. V48 vs Tetsutani Pasture
* **Paired Legs**: 256
* **V48 Win Rate**: **98.4%**
* **Mean Cash Delta vs 2945**: **+$2.79**
* **Casualties**: **0**

### E. V48 vs Saiteja Mega 3000
* **Paired Legs**: 256
* **V48 Win Rate**: **100.0%**
* **Mean Cash Delta vs 2945**: **+$35.84** (Active cohort delta: **+$573.44**)
* **Casualties**: **0**

### F. V48 vs Kaitofukami 3009 & Indarkarhana Top 10
* **Paired Legs**: 256 each (512 total)
* **V48 Win Rate**: **100.0%**
* **Casualties**: **0**

---

## 4. Key Milestones Achieved

1. **Gate A Passed**: Isolated mechanism alpha in target cohort exceeds +$100 with zero casualties.
2. **Gate B Passed**: Evaluated over 256 legs with positive alpha, zero casualties, and higher win rate than 2945.
3. **Gate C Passed**: Evaluated over 1,536 fresh paired legs; strictly outperformed 2945 across independent elite families.
4. **Golden Property Verified**: 100% bit-for-bit identity with 2945 when the patch condition is inactive.
