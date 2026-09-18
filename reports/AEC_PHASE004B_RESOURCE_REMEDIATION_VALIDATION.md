# SPDX-License-Identifier: MIT
# AEC Phase 004B: Resource Conversion Remediation Validation Report

**Phase**: AEC Phase 004B  
**Mechanism Under Evaluation**: `RESOURCE_CONVERSION`  
**Evaluation Scope**: 200 Offline Replay Matches across Development Seeds `50000–50024`  
**Chassis**: Frozen V3 Baseline Chassis (`submission_Vj_kc_v3.tar.gz`) — SHA-256: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`  
**Scientific Status**: **OFFLINE MICRO-VALIDATED / NOT READY FOR PROSPECTIVE DEPLOYMENT**  
**Date**: 2026-09-18  

---

### 1. Authoritative Batch Replay Results (Seeds 50000–50024)

The complete 200-match offline development replay matrix ($25 \text{ seeds} \times 2 \text{ seats} \times 4 \text{ arms}$) executed with zero runtime errors, zero invariant breaches, and zero holdout touches:

#### Table 1: Population Arm Performance (50 Matches per Arm)
| Experimental Arm | Matches | Mean Margin | Median Margin | Std Dev | p05 Margin | p95 Margin | Total Commits | Seeds w/ Commits | Farmer Displaced | Aux Absorbed | Shed Overflow | Elapsed Time |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Arm A (CONTROL)** | 50 | **+$86.92** | +$17.00 | $254.15 | -$49.00 | +$525.25 | 78 | 25 | **0** | 0 | None (0) | 173.4s |
| **Arm B (RESOURCE_CONVERSION_ONLY)** | 50 | **-$1330.62** | -$8.00 | $2650.50 | -$7288.75 | +$125.35 | 362 | 25 | **0** | **288** | None (0) | 1134.0s |
| **Arm C (EMERGENCY_FEED_ONLY)** | 50 | **+$87.24** | +$18.00 | $254.11 | -$49.00 | +$525.25 | 82 | 25 | **0** | 4 | None (0) | 283.6s |
| **Arm D (COMBINED_RESOURCE)** | 50 | **-$1330.30** | -$8.00 | $2650.67 | -$7288.75 | +$125.35 | 366 | 25 | **0** | **292** | None (0) | 407.9s |

#### Table 2: Paired Delta vs Arm A (CONTROL)
| Experimental Arm | ITT Mean $\Delta$ | ITT Median $\Delta$ | ITT Std | Wins | Losses | Ties | Triggered Matches | Triggered Mean $\Delta$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **RESOURCE_CONVERSION_ONLY** | **-$1417.54** | **$0.00** | $2708.89 | 0 | 14 | **36 (72%)** | 50 | -$1417.54 |
| **EMERGENCY_FEED_ONLY** | **+$0.32** | **$0.00** | $3.03 | 2 | 2 | **46 (92%)** | 50 | +$0.32 |
| **COMBINED_RESOURCE** | **-$1417.22** | **$0.00** | $2709.06 | 2 | 16 | **32 (64%)** | 50 | -$1417.22 |

---

### 2. Forensic Analysis of Remediation Objectives

#### 2.1 Remediation Goals Achieved
1. **Zero Pure Market Seed Purchases under RESOURCE_CONVERSION**:
   - Phase 004: **184 / 210 commits (87.6%)** were `PATCH_CONV_CONV_CHAIN_SEED_TO_CARROT`.
   - Phase 004B: **0 commits** (100% reduction). Pure seed acquisitions were successfully quarantined and routed to `RESOURCE_ACQUISITION`.
2. **Zero Primary Labor Diversions (Farmer Displacements)**:
   - Phase 004: **24 / 210 commits** diverted the Farmer away from critical backbone farming.
   - Phase 004B: **0 Farmer displacements** across all 200 matches.
3. **100% Auxiliary Worker Absorption**:
   - In Arm B, **288 physical conversion commits** were absorbed exclusively by auxiliary hands (`Hand 1`), preserving the Farmer on the agricultural backbone.
4. **Zero Invariant Violations**:
   - Zero shed overflows, zero cash overdrafts, zero illegal movement commands, and zero trajectory desynchronizations.

#### 2.2 Conversion Category Distribution & Accounting Reconciliation
Across all committed patches in Phase 004B:
- **`TRUE_PHYSICAL_CONVERSION`**: 576 commits across the entire 4-arm experiment (Arms B and D combined):
  * **Arm B (`RESOURCE_CONVERSION_ONLY`)**: 288 physical conversions (all absorbed by auxiliary Hand 1).
  * **Arm D (`COMBINED_RESOURCE`)**: 288 physical conversions (all absorbed by auxiliary Hand 1).
  * Arms A and C: 0 physical conversions.
  * Farmer displaced: **0** (100% auxiliary absorption across all physical conversions).
  * Target commodities: `MILK` (Wheat $\to$ Cow $\to$ Milk), `EGG` (Wheat $\to$ Goose $\to$ Egg).
- **`MARKET_ACQUISITION`**: **0 commits** committed under `RESOURCE_CONVERSION`.
- **`OTHER`**: 312 total commits across all 4 arms:
  * Arm A (`CONTROL`): 78 `DEPENDENCY_AWARE_MARKET_TIMING` commits.
  * Arm B (`RESOURCE_CONVERSION_ONLY`): 74 `DEPENDENCY_AWARE_MARKET_TIMING` commits (4 superseded by conversion scheduling).
  * Arm C (`EMERGENCY_FEED_ONLY`): 78 `DEPENDENCY_AWARE_MARKET_TIMING` + 4 `EMERGENCY_FEED` commits = 82 commits.
  * Arm D (`COMBINED_RESOURCE`): 74 `DEPENDENCY_AWARE_MARKET_TIMING` + 4 `EMERGENCY_FEED` commits = 78 commits.
  * Total `OTHER`: $78 + 74 + 82 + 78 = 312$ ($304 \text{ market timing} + 8 \text{ emergency feed}$).
- **Total Commits Reconciliation**:
  * Arm A (78) + Arm B (362) + Arm C (82) + Arm D (366) = **888 total commits** ($576 \text{ physical conversions} + 312 \text{ other}$).
- **Total Auxiliary Absorption Reconciliation**:
  * Arm A (0) + Arm B (288) + Arm C (4) + Arm D (292) = **584 total auxiliary absorptions** ($576 \text{ on physical conversions} + 8 \text{ on emergency feed}$).

> [!NOTE]
> **Phase 005 Accounting Reconciliation Note**:
> The category totals above reflect the complete experiment across all 4 experimental arms (200 matches). The 576 physical conversions represent the sum of 288 commits in Arm B and 288 commits in Arm D. Raw data files (`results/PHASE004B_MATCHES.csv`, `results/PHASE004B_PATCHES.csv`, `results/PHASE004B_SUMMARY.json`) remain strictly unmodified.

---

### 3. Forensic Root Cause of Economic Drag in Genuine Conversions

While the architectural remediation completely repaired liquidity accounting, labor preconditions, and opportunity classification, Arm B exhibited negative paired performance (-$1417.54 ITT mean delta, 0 wins, 14 losses, 36 ties):

#### Diagnostic Seed Breakdown:
In 36 out of 50 matches (72%), `RESOURCE_CONVERSION_ONLY` tied CONTROL exactly ($\Delta = \$0.00$).  
The entire economic loss occurred in exactly 7 seeds (evaluated symmetrically in Seat 0 and Seat 1 = 14 matches):
1. **Seed 50024** (Seat 0 & 1): $\Delta = -\$8,314.0$
2. **Seed 50019** (Seat 0 & 1): $\Delta = -\$7,801.0$ / $-\$6,676.0$
3. **Seed 50001** (Seat 0 & 1): $\Delta = -\$6,443.0$
4. **Seed 50023** (Seat 0 & 1): $\Delta = -\$5,945.0$
5. **Seed 50007** (Seat 0 & 1): $\Delta = -\$5,745.0$
6. **Seed 50000** (Seat 0 & 1): $\Delta = -\$1,354.0$
7. **Seed 50011** (Seat 0 & 1): $\Delta = -\$399.0$

#### Physical Root Cause:
Trace analysis of Hand 1 on these seeds (e.g. Seed 50024) reveals:
- In the **CONTROL** arm, auxiliary Hand 1 performs high-value agricultural labor: planting strawberries (`['PLANT', 'STRAWBERRY']`), watering strawberries (`['WATER']`), and caring for crops (`['CARE']`). A mature strawberry field yields thousands of dollars in high-margin commodity sales.
- In the **RESOURCE_CONVERSION** arm, Hand 1 is diverted to purchase wheat feed and transit to the pasture to feed the cow.
- **Economic Asymmetry**:
  $$\text{Gross Return of Cow Feeding} \approx 1 \text{ Milk} \times \$160 - 1 \text{ Wheat} \times \$25 = +\$135$$
  $$\text{Opportunity Cost of Hand 1 Diverted from Cash Crop Field} \gg \$5,000$$

Even though the Farmer was preserved on the backbone, the **auxiliary hand's opportunity cost in high-value cash crop cultivation exceeds the gross revenue of livestock feeding**.

---

### 4. Application of Section 36 Governance Rule

Section 36 of the remediation directive explicitly specifies:
> *"If the remediation discovers that genuine conversions remain economically negative even after liquidity and labor problems are fixed: do NOT continue adding heuristics. Classify the mechanism as: NOT READY and document the exact structural reason. It may indicate that the candidate family itself is economically unsuitable. Do not optimize it indefinitely."*

In accordance with this scientific mandate:
1. No ad-hoc economic bonuses, artificial crop penalties, or tuning heuristics will be introduced.
2. `RESOURCE_CONVERSION` is formally classified as **NOT READY FOR PROSPECTIVE DEPLOYMENT**.
3. Live production status remains **QUARANTINED**.
4. The structural defect is permanently documented: physical livestock conversions in the current environment yield returns that are orders of magnitude lower than the opportunity cost of auxiliary labor in cash crop farming.
