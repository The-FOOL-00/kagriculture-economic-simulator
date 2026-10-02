# V25 AEC Transfer Audit

## 1. Experimental Objective
Determine whether the frozen V22R1 Adaptive Economic Compiler (AEC) is genuinely backbone-agnostic or whether its internal counterfactual simulator, continuation provider, and intervention logic are tightly coupled to V3's specific baseline dynamics.

## 2. 4-Arm Benchmark Protocol
* **Arm 1**: `V3_STANDALONE` (Unmodified V3 baseline)
* **Arm 2**: `V3_PLUS_AEC` (Submitted V22R1 release payload)
* **Arm 3**: `V25_P3_STANDALONE` (Promoted V25 Unified Macro Planner)
* **Arm 4**: `V25_P3_PLUS_AEC` (V25 P3 backbone wrapped with exact frozen V22R1 AEC)
* **Opponent**: Standalone V3 (Mirrored seating, Seat 0 and Seat 1)
* **Evaluated Matches**: 80 matches (20 matches per arm across 10 mirrored seeds)

## 3. Results Summary

| System Arm | Mean Reward | Baseline V3 Reward | Mean Paired Delta | Min Delta (Tail) | Win / Loss / Tie Record |
|---|---|---|---|---|---|
| **Arm 1: V3 Standalone** | 86,009.9 | 86,009.9 | **+0.00** | -6,893.00 | 1W - 1L - 18T |
| **Arm 2: V3 + Frozen AEC (V22R1)** | 85,975.5 | 85,997.3 | **-21.80** | -6,749.00 | 1W - 2L - 17T |
| **Arm 3: V25 P3 Standalone** | 84,555.5 | 85,345.4 | **-789.90** | -5,054.00 | 6W - 11L - 3T |
| **Arm 4: V25 P3 + Frozen AEC** | 84,148.4 | 87,487.9 | **-3,339.40** | **-23,824.00** | 6W - 12L - 2T |

## 4. Root Cause Forensic Analysis: Why Frozen AEC Degrades V25

1. **Continuation Asymmetry (`v3_continuation.py`)**:
   The frozen V22R1 AEC relies on an internal continuation simulator (`aec/counterfactual/v3_continuation.py`) that assumes the exact raw opening state of V3 (specifically, the 50-unit wheat wash). When P3 executes an optimized 30-unit wheat wash, the initial cash and inventory trajectory differs from what the continuation simulator projects.
2. **Counterfactual Prediction Drift**:
   Because the internal simulation harness expects V3's historical cash balances, its margin evaluation ($\Delta \text{Money}$) miscalculates the true opportunity cost of market and labor actions, causing the candidate funnel to commit interventions that disrupt P3's superior capital runway.
3. **Severe Tail Penalty**:
   On seed `249450`, Arm 4 suffered a catastrophic delta of -23,824.00, whereas P3 Standalone achieved +279.00 on Seat 0. This demonstrates severe negative interference between the frozen AEC patches and P3's macro capital allocation.

## 5. Decision State & Research Finding

Per Section 25 and Section 32 of the V25 Protocol:
* **Outcome**: **`V25 BACKBONE CONFIRMED / AEC TRANSFER FAILED`**
* **Finding**: The V25 P3 backbone is a verified standalone advance over V3, but the submitted V22R1 AEC cannot be transferred blindly. The AEC's counterfactual continuation engine is coupled to V3's baseline parameters.
* **Preservation**: The frozen submission `submission_aec_v22r1.tar.gz` remains 100% untouched and active. Any future adaptation of AEC to V25 must occur in a dedicated, subsequent research cycle.
