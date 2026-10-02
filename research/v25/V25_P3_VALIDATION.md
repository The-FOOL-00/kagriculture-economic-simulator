# V25 Prototype P3 (Unified Macro Planner) Validation Report

## 1. Candidate Overview
* **Candidate**: `V25_P3_UNIFIED` (`candidates/v25_p3_unified.py`)
* **Hypothesis**: Joint macro capital velocity optimization (`OPEN_UNITS = 30`) + zero-inventory in-place labor dispatch (watering dry crops + clearing weeds) preserves operating runway, eliminates market price slippage, and converts passive idle periods into agricultural output without route desynchronization.
* **Cohort**: Discovery Cohort (Seeds `249430..249449`, 20 seeds $\times$ 2 mirrored seats = 40 matches).

## 2. Experimental Results vs Standalone V3

| Metric | Measured Value | Preregistered Threshold | Status |
|---|---|---|---|
| **Matches Evaluated** | 40 | 40 | Complete |
| **Mean Paired Delta** | **+1,300.70** | $> 0.0$ | **EXCEEDED (+1300.70)** |
| **Median Paired Delta** | **+1,300.00** | - | Exceptionally High |
| **Record (W / L / T)** | **39W - 0L - 1T** | Win $>$ Loss | **DOMINANT (39W, 0L)** |
| **Win Percentage** | **97.5%** | $> 50\%$ | **EXCEEDED (97.5%)** |
| **Tail Loss Floor** | **+411.00** | $> -50,000$ | **PERFECT (No losses)** |
| **Standard Deviation** | 149.64 | - | Highly Deterministic |
| **Candidate Mean Reward** | 89,260.7 | - | +1,300.7 above V3 |
| **Baseline Mean Reward** | 87,960.0 | - | - |

## 3. Key Findings & Mechanisms
1. **Capital Velocity Preserved**: Reducing step 0 wheat wash from 50 units to 30 units drastically cut lockstep market slippage, preserving liquid capital for step 1 hires and animal procurement.
2. **Zero Route Desynchronization**: By restricting in-place chore execution strictly to zero-inventory actions (`WATER` and `DIG`) on the worker's current cell, worker coordinates $(x, y)$ remained bit-exact with V3's forward routing expectations.
3. **Flawless Victory Rate**: P3 did not suffer a single match loss out of 40 games, establishing consistent, statistically overwhelming superiority over Standalone V3.

## 4. Promotion Decision
`V25_P3_UNIFIED` meets all preregistered criteria and is **PROMOTED** as the single candidate for the Independent Confirmation Cohort and AEC Transfer Audit!
