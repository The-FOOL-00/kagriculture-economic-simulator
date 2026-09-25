# V32 P6 — ARM 1 EVALUATION REPORT: EXACT SEMANTIC MASK ONLY

## 1. PURPOSE & HYPOTHESIS

In accordance with Section 15 and Section 16 of the **V32 P6 Protocol**, **P6 Arm 1** tests whether eliminating simulator-rejected actions alone with an exact, source-grounded semantic action mask prevents the Step-2 catastrophe and allows closed-loop economics to recover without retraining.

Hypothesis being tested:
> *If `PICKUP(COW)` is masked out at Step 2 because the farmer at [4, 3] is not shed-adjacent, will the policy naturally fall back to the expert action `SOUTH` and restore the downstream farming trajectory?*

---

## 2. CLOSED-LOOP DEVELOPMENT SCREEN RESULTS (120 LEGS)

Evaluated on Seeds `249675:249684` $\times$ 6 opponents $\times$ 2 seats (120 legs) using `v32_p6_eval_screen.py --mask 1`:

| Metric | P5 Arm 2 Baseline (Unmasked) | P6 Arm 1 (Exact Mask Only) | Status / Delta |
|:---|:---:|:---:|:---|
| **Step-0 Market Wash Execution** | 120 / 120 (100.0%) | 120 / 120 (100.0%) | Preserved (100%) |
| **Step-0 Farmer PASS Rate** | 120 / 120 (100.0%) | 120 / 120 (100.0%) | Preserved (100%) |
| **Step-1 Farmer NORTH Rate** | 120 / 120 (100.0%) | 120 / 120 (100.0%) | Preserved (100%) |
| **Step-1 Mean Hires** | 5.00 / 5.00 hands | 5.00 / 5.00 hands | Preserved (100%) |
| **Step-2 Rejected `PICKUP` Rate** | 120 / 120 (100.0%) | **0 / 120 (0.0%)** | **Successfully Masked Out** |
| **Step-2 Farmer `SOUTH` Rate** | 0 / 120 (0.0%) | **0 / 120 (0.0%)** | **Unrepaired (0% - all NORTH)** |
| **Step-2 Dominant Emitted Action** | `PICKUP` (100%) | **`NORTH` (100.0%)** | Substituted by Rank 2 legal action |
| **First Action Divergence ($t_{\text{act}}$)** | Step 2 | Step 2 | Unchanged (Diverges on Step 2) |
| **Terminal Cash (Mean)** | $2.94 | **$0.03** | Flat zero regime |
| **Terminal Cash (Median)** | $0.00 | **$0.00** | Flat zero regime |
| **Terminal Cash (Max)** | $342.00 | **$3.00** | No economic compounding |
| **Win Rate** | 0.0% (0 / 120) | 0.0% (0 / 120) | 0 wins across panel |

---

## 3. CAUSAL MECHANISM & INTERPRETATION

Section 16 of the Protocol pre-specifies three diagnostic interpretations:

1. *If PICKUP removed $\to$ SOUTH selected $\to$ economics recover*: Problem was pure validity mismatch.
2. *If PICKUP removed $\to$ but another catastrophic action occurs*: **Legality masking is necessary but insufficient**.
3. *If PICKUP removed $\to$ but economics remain near zero*: Downstream policy quality remains the main bottleneck.

The empirical evidence confirms **Case 2 & Case 3**:
- When `PICKUP` is masked out at [4, 3], the unmasked categorical distribution chooses the highest remaining unmasked logit.
- From our logit forensics (`V32_P6_STEP2_LOGITS.md`):
  - `Logit(NORTH) = +6.599` ($P = 89.1\%$ among unmasked)
  - `Logit(SOUTH) = +4.487` ($P = 10.8\%$ among unmasked)
- Because moving `NORTH` from [4, 3] to [4, 2] is a legal simulator movement, the mask legitimately permits it.
- The model commands `NORTH` at Step 2 (moving to [4, 2]), then `NORTH` again at Steps 3 and 4, stranding the farmer at [4, 0] without animals.
- The 5 hired hands idle, wages drain all $1,005, and terminal cash collapses to **$0.00**.

---

## 4. SCIENTIFIC CONCLUSION

> **Exact semantic masking alone is strictly insufficient to restore the expert trajectory.**

While the mask successfully eliminates the simulator-rejected `PICKUP` action, the underlying neural policy has a strong learned preference for `NORTH` over `SOUTH` (+2.112 logit margin) at Step 2.
Therefore, targeted farmer-head rebalancing (**P6 Arm 2**) is mandatory to elevate `SOUTH` above `NORTH`.
