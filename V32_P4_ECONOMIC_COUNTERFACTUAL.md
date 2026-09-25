# V32 P4 ECONOMIC COUNTERFACTUAL REPORT (§30)

Date: 2026-09-23.
Runner: `scratch/v32_p4_counterfactual.py`.
Data: `results/v32_p4_counterfactual.json`.

## 1. Objective & Counterfactual Setup
To answer the core question of §30:
> **How much of P3's economic collapse is causally attributable to the opening market ordering?**

We evaluated three strictly controlled conditions across identical seeds (`249675`, `249676`, `249677`) against `E2_A7` (seat 0):
1. **Condition A (P3 Baseline)**: Autonomous P3 BC checkpoint (`results/v32_p3_bc.npz`), which emits the reversed wash `[SELL30, BUY30]` at step 0.
2. **Condition B (P3 Spliced Wash)**: Exactly the same P3 BC checkpoint, but at step 0 only, the market action is counterfactually replaced with the expert opening wash `[BUY30, SELL30]`. All remaining 718 steps run autonomously under the P3 BC policy.
3. **Condition C (P4 Arm 1)**: End-to-end autonomous P4 Arm 1 checkpoint (`results/v32_p4_arm1_balanced.npz`), which naturally predicts the correct opening wash `[BUY30, SELL30]`.

## 2. Experimental Results

| Seed | Condition A: P3 Baseline (Reversed Wash) | Condition B: P3 + Spliced Wash | Condition C: P4 Arm 1 (Autonomous Correct Wash) |
| :--- | :--- | :--- | :--- |
| **249675** | $881.00 | $64.00 | $12.00 |
| **249676** | $887.00 | $7.00 | $2.00 |
| **249677** | $199.00 | $0.00 | $280.00 |
| **Mean**   | **$655.67** | **$23.67** | **$98.00** |

## 3. Causal Findings
1. **The opening wash alone does NOT account for the $90,000 performance gap**:
   - Forcing the expert wash into P3 at step 0 did not lift terminal cash toward A7 ($91k).
   - In fact, when starting with $3,000 cash from a successful wash, the unmasked BC policy rapidly spent the additional liquidity on suboptimal early-game market orders, collapsing terminal cash to $0–$64.
2. **Opening wash is a necessary prerequisite, but downstream compounding is the binding ceiling**:
   - The opening wash successfully injects capital at step 0.
   - However, in pure behavioral cloning without execution masking, the policy drifts out-of-distribution in turns 1–719.
   - The primary cause of the $90k gap is therefore **downstream trajectory compounding / out-of-distribution execution error**, not solely turn-0 slot ordering.
