# Live Submission Manifest — Championship Deployment

**Date**: 2026-09-10  
**Competition**: `kaggriculture` (Featured, $50,000 USD)  
**Team**: `Eldritch` (`thefool00`)  
**Deployment State**: **DEPLOYED — BOTH COMPILED AGENTS ACTIVE**  

---

## 1. Candidate Specification & Submission Records

### Submission 1: Control Baseline
- **Agent Name**: V54++ Control Standalone
- **Source File**: `candidates/v54_plus_shop.py`
- **Source SHA256**: `592f0ba31b3b20b5a3aad409a753b5e6bdeb29a9eb2381342b1cd527509fa9e8`
- **Compiled File**: `candidates/compiled_v54_plus_shop.py`
- **Compiled SHA256**: `f651ccd220e701968bc33579812d8917da63f5b0582f2fd0d363fa6a16ffd8b8`
- **Submission Ref ID**: `56146947`
- **Timestamp (UTC)**: `2026-09-10 15:13:16.067000`
- **Status**: `SubmissionStatus.COMPLETE`
- **Score**: `600.0`
- **Active Slot**: **Slot 2 (Baseline Control)**

### Submission 2: Validated Improvement
- **Agent Name**: V54++ Residual Standalone
- **Source File**: `candidates/v54_plus_residual.py`
- **Source SHA256**: `5b2d5080ba38287812d137a21c7b09071e1f66a10c32d7c3ec4bb61be4520e80`
- **Compiled File**: `candidates/compiled_v54_plus_residual.py`
- **Compiled SHA256**: `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb`
- **Submission Ref ID**: `56146971`
- **Timestamp (UTC)**: `2026-09-10 15:14:36.043000`
- **Status**: `SubmissionStatus.COMPLETE`
- **Score**: `600.0`
- **Active Slot**: **Slot 1 (Newest / Experimental Challenger)**

---

## 2. Active Ladder Verification

| Slot | Ref ID | File Name | Date (UTC) | Status | Score | Role |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Active 1 (Newest)** | `56146971` | `compiled_v54_plus_residual.py` | 2026-09-10 15:14:36 | `COMPLETE` | 600.0 | V54++ Residual Challenger |
| **Active 2** | `56146947` | `compiled_v54_plus_shop.py` | 2026-09-10 15:13:16 | `COMPLETE` | 600.0 | V54++ Control Baseline |
| *Retired 3* | `56099752` | `compiled_research_b_only_v2.py` | 2026-09-08 13:53:27 | `COMPLETE` | 727.0 | Inactive History |
| *Retired 4* | `55958978` | `submission_slot2_aethel_refined_v2.tar.gz` | 2026-09-02 09:41:40 | `COMPLETE` | 869.1 | Inactive History |

---

## 3. Protocol Invariants Enforced

1. **Zero Algorithm / Logic Changes**: Proven turn-by-turn action equivalence across 50 fresh seeds ($0 / 72,000$ action divergence).
2. **Zero Parameter Tuning**: Exact preemption parameter values preserved (`preempt_money_deficit = 2000.0`, `preempt_minimum_delta = 4.0`, `preempt_maximum_batch = 12`).
3. **Zero Third Submissions**: Exactly 2 submissions uploaded.
4. **Anti-Chasing Rules**: No rerolls or parameter tweaks based on initial ratings.
