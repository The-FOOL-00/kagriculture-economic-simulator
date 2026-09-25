# V32 P4 FIRST DIVERGENCE ANALYSIS

Date: 2026-09-23.
Runner: `scripts/v32_p3_divergence.py`.
Records: `results/v32_p4_divergence_arm1.jsonl`.
Seeds: 249675, 249676 (Seat 0 vs `E2_A7`).

## 1. Comparison: P3 Baseline vs P4 Arm 1

### 1.1 P3 Baseline First Divergence (from `V32_P3_FIRST_DIVERGENCE.md`)
- First Divergence: **Step 0**.
- Cause: **Market slot ordering only**.
  - BC step-0 market: `[[SELL, WHEAT, 30], [BUY_PRODUCT, WHEAT, 30]]`.
  - Expert step-0 market (A7): `[[BUY_PRODUCT, WHEAT, 30], [SELL, WHEAT, 30]]`.
- Unit Actions: 100% match with all teachers (`farmer: ["PASS"]`).
- Classification: Market slot-order confusion.

### 1.2 P4 Arm 1 First Divergence
- Step 0 Market Action:
  $$\text{Market} = [[\text{BUY\_PRODUCT}, \text{WHEAT}, 30], [\text{SELL}, \text{WHEAT}, 30]]$$
- Market Divergence vs E2_A7 at Step 0: **ZERO DIFFERENCE**.
  - Both Slot 0 and Slot 1 match A7 ground truth bit-identically in opcode, crop, and quantity!
- Divergence Classification:
  - The **critical market slot-ordering divergence at step 0 is 100% ELIMINATED**.
  - The first minor discrepancy vs A7 is on the unit movement side (`farmer: ["WEST"]` vs `["PASS"]`).
  - At step 0, player farm starts at the shed; stepping WEST is a benign legal movement, while the market wash executes cleanly.

## 2. Downstream First Divergence Timeline

| Step | Arm 1 Policy Action | A7 Expert Action | Differing Components | Consequence |
| :--- | :--- | :--- | :--- | :--- |
| **0** | `mkt: [BUY30, SELL30]`, `farmer: WEST` | `mkt: [BUY30, SELL30]`, `farmer: PASS` | Unit move only (Market matches!) | **Wash succeeds**, Money = $3,000 |
| **1** | `farmer: BUILD_PASTURE`, `mkt: [BUY80, SELL998, ...]` | `farmer: WATER`, `mkt: []` | Unit + Market | Policy over-purchases non-vital inventory |
| **2** | `farmer: PLACE COW` (0 cows in shed) | `farmer: HARVEST` | Unit validity | Suboptimal unexecutable action |

## 3. Causal Attribution
The repair of the market head objective in P4 Arm 1 successfully shifted the market behavior into 100% alignment with the expert wash at step 0. The remaining divergence occurs in subsequent turns (steps 1–10) due to unit-planning and general behavioral-cloning compounding drift.
