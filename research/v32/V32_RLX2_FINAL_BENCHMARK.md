# V32 RL-X2: Master Tournament Benchmark (RLX2-F11)

## 1. Executive Summary

This document presents the final, independent tournament benchmark comparing the search-initialized strategic learning policy (**RLX2-F7**) against the protected incumbent **A7** across the frozen 6-opponent league over mirrored matches on the held-out development cohort (`V32_DEV_HIST`, seeds 249675..249677).

All 36 match legs were executed in parallel using 8 isolated workers. For every leg, both the candidate policy and the pure frozen A7 baseline were simulated in identical match configurations (same random seed, same opponent, same seating).

---

## 2. Master Benchmark Distribution Table

| Policy | Opponent | Seeds / Legs | Mean Cash ($) | Median Cash ($) | P25 ($) | P75 ($) | Min ($) | W | L | T | Paired $\Delta$ vs A7 ($) | Win Rate (%) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **RLX2-F7** | `E2_A7` | 6 | $13,418.0 | $12,327.0 | $8,294.5 | $17,450.5 | $6,218.0 | 0 | 6 | 0 | **-$75,556.7** | 0.0% |
| **RLX2-F7** | `E1_V22R1` | 6 | $13,418.0 | $12,327.0 | $8,294.5 | $17,450.5 | $6,218.0 | 0 | 6 | 0 | **-$80,897.0** | 0.0% |
| **RLX2-F7** | `E0_V3` | 6 | $13,418.0 | $12,327.0 | $8,294.5 | $17,450.5 | $6,218.0 | 0 | 6 | 0 | **-$80,910.7** | 0.0% |
| **RLX2-F7** | `E8_DMITRII` | 6 | $11,551.0 | $7,380.0 | $4,821.0 | $18,281.0 | $2,262.0 | 0 | 6 | 0 | **-$73,451.3** | 0.0% |
| **RLX2-F7** | `V54` | 6 | $11,627.7 | $17,387.0 | $4,240.0 | $18,740.0 | $1,095.0 | 0 | 6 | 0 | **-$87,227.0** | 0.0% |
| **RLX2-F7** | `SYN_AGG` | 6 | $18,782.2 | $22,819.5 | $12,045.0 | $25,519.4 | $8,120.0 | 4 | 2 | 0 | **-$141,935.8** | 66.7% |
| **RLX2-F7** | **OVERALL** | **36** | **$13,702.5** | **$12,327.0** | **$6,218.0** | **$18,281.0** | **$1,095.0** | **4** | **32** | **0** | **-$89,996.4** | **11.1%** |
| | | | | | | | | | | | | |
| **A7 (Baseline)** | `OVERALL` | **36** | **$103,698.9** | **$98,415.0** | **$85,210.0** | **$125,495.0** | **$71,014.0** | **34** | **2** | **0** | **$0.00** | **94.4%** |

---

## 3. Forensic Analysis of End-to-End Degradation

The contrast between exact local search (**RLX2-F5**) and end-to-end neural policy execution (**RLX2-F7**) provides conclusive empirical insight into the limits of learned strategic control in Kaggriculture:

### 1. Counterfactual Search Discovery vs Sequential Compounding
* In local counterfactual search (**RLX2-F5**), a single macro-action $a \neq 0$ is applied for exactly $H = 4$ steps, after which the policy *instantly resumes pure A7 execution* for the remaining $720 - (t+4)$ steps. Under this isolated intervention, exact simulation proved that discrete decisions yield immense value:
  * Seed 249635 @ Step 288 (Day 12): `EXPAND_LAND` yields **+$11,179.00** alpha.
  * Seed 249636 @ Step 216 (Day 9): `CROP_FOCUS` yields **+$3,420.00** alpha.
  * Seed 249636 @ Step 72 (Day 3): `HARVEST_PRIORITY` yields **+$2,128.00** alpha.
* However, in end-to-end policy execution, the neural actor makes a decision every $H = 4$ steps across all 180 decision boundaries.
* Because the policy deviates ~60% of the time, the agent executes dozens of uncoordinated interventions across the episode.

### 2. Physical Desynchronization Cascade
* A7's $100k+ performance relies on a tightly coupled, open-loop "choreography" where specific workers are positioned near pastures, barns, and market squares at exact ticks to execute feed cycles and harvest routes.
* When the neural policy orders `CROP_EXPANSION` or `OPPORTUNISTIC_SELL` mid-game, it alters worker inventory and delays travel routines.
* Even though the executor enforces hard safety constraints (no invalid orders, cash buffers), the altered physical state prevents A7 from executing its subsequent pre-planned chores when control returns to Action 0.
* Compounded over 180 macro steps, this leads to stranded crops, missed animal feed windows, and an aggregate loss of **-$89,996.40**.

---

## 4. Promotion Gate Evaluation

| Criterion | Requirement | RLX2-F7 Result | Status |
| :--- | :--- | :--- | :---: |
| **Gate 1** | Outperform A7 on held-out development cohort | Mean Cash: $13,702.5 vs A7 $103,698.9 (Paired $\Delta = -$89,996.4) | **FAILED** |
| **Gate 2** | Reproduced across multiple seeds | Consistent negative delta across all 3 dev seeds | **FAILED** |
| **Gate 3** | Robust across opponent families | Lost against 5 of 6 league opponents | **FAILED** |
| **Gate 4** | Acceptable worst-case tail risk | Minimum score dropped to $1,095 (catastrophic tail) | **FAILED** |
| **Gate 5** | Zero information leakage | 100% compliant (no future/opponent state) | **PASSED** |
| **Gate 6** | Runtime safety & legality | 100% legal, zero simulation errors | **PASSED** |
| **Gate 7** | Package determinism | 100% deterministic | **PASSED** |
| **Gate 8** | Repository freeze integrity | All frozen files bit-identical | **PASSED** |

**OVERALL PROMOTION DECISION: REJECT (NO-GO).**
