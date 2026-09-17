# Formal Governance Invalidation Notice: EXP-AEC-001 Smoke Test 9999 (V1)

**Document Identifier**: `EXP-AEC-001_SMOKE_TEST_9999_V1_INVALIDATION`  
**Date**: 2026-09-17  
**Status**: **RECLASSIFIED — HISTORICAL EVIDENCE ONLY**  
**Classification**: **INFRASTRUCTURE LAYER: PASS | MECHANISM-ISOLATION LAYER: FAIL**

---

### 1. Reclassification Summary
This directory (`experiments/EXP-AEC-001/smoke_test_9999/`) contains raw execution telemetry, checkpoints, and logs from the initial infrastructure smoke test executed on Seed 9999.

A mandatory pre-execution protocol audit identified a **MATERIAL IMPLEMENTATION vs. PREREGISTRATION DISCREPANCY**:
- The binding preregistration (`EXP-AEC-001_AEC_V1_PREREGISTRATION.md`, Sections 7 & 8) froze the treatment to include ONLY four verified foundation mechanisms: `LOCAL_WEED_DIG`, `FRONTLOAD_ORDERS`, `TERMINAL_LIQUIDATION`, `PHASE_SHUTDOWN`.
- All other mechanisms (`OPPONENT_PREEMPT_SELL`, `DYNAMIC_SHADOW_HARVEST`, `CARGO_FERRY_PRIORITY`, `EMERGENCY_FEED_PURCHASE`, `TERMINAL_HARVEST_SWEEP`, `evaluate_town_cycle_signal`) were explicitly preregistered as **DISABLED / QUARANTINED**.
- The initial runtime implementation did not enforce this mechanism boundary at the OpportunityEngine, PatchGenerator, or Executor commit gates. Consequently, `TimingOpportunityAnalyzer` proposed `OPPONENT_PREEMPT_SELL` patches, which were compiled, simulated, and committed across all non-baseline decisions in this smoke test.

---

### 2. Dual-Layer Evaluation Verdict

| Evaluation Layer | Status | Justification |
| :--- | :--- | :--- |
| **Infrastructure Layer** | **PASSED** | Single-live-call invariant strictly satisfied (719/719 turns). Zero duplicate calls. Zero runtime exceptions. Sub-millisecond no-event latency ($0.04\text{ ms}$). Deterministic match replay identical. |
| **Mechanism-Isolation Layer** | **FAILED** | Treatment isolation violated. Committed patches belonged exclusively to `OPPONENT_PREEMPT_SELL` (quarantined family) rather than the authorized foundation set. |

---

### 3. Binding Prohibitions
To uphold scientific validity:
1. The numeric gameplay metrics from this run (scores, margins, win deltas) **MUST NOT** be used for parameter tuning, hypothesis testing, treatment evaluation, or EXP-AEC-001 statistical analysis.
2. The artifacts are preserved unaltered strictly as forensic evidence of infrastructure stability.
3. A corrected smoke test enforcing multi-layer defense-in-depth mechanism gating is established in `experiments/EXP-AEC-001/smoke_test_9999_v2/`.
