# V32 P6 — CAUSAL COUNTERFACTUAL ANALYSIS: STEP 2 INTERVENTION

## 1. EXECUTIVE SUMMARY & OBJECTIVE

The purpose of this causal counterfactual analysis is to rigorously determine whether forcing the expert action `SOUTH` at Step 2 is causally sufficient to restore economic compounding, or whether downstream imitation errors immediately re-emerge at subsequent steps.

Using the frozen P5 model in the actual Kaggle simulator environment across representative development seeds (`249675`, `249676`, `249677`), we compared two strictly controlled branches:
- **Counterfactual A (Intervention)**: Step 2 action is forcibly overridden to `['SOUTH']` (the ground-truth expert action), and the policy subsequently runs autonomously.
- **Counterfactual B (Control)**: Step 2 action is executed as `['PICKUP', 'COW', 1]` (the unconstrained P5 policy error), and the policy subsequently runs autonomously.

---

## 2. SIMULATION RESULTS MATRIX

| Metric / Step | Counterfactual A (`SOUTH` at Step 2) | Counterfactual B (`PICKUP` at Step 2) | Causal Delta / Implication |
|:---|:---|:---|:---|
| **Step 2 Action** | `['SOUTH']` | `['PICKUP', 'COW', 1]` | Interventional divergence point |
| **Step 2 Legality** | **LEGAL** (Valid move to [4, 4]) | **ILLEGAL** (Silent no-op at [4, 3]) | Mask / Legality discrepancy |
| **Step 3 Pre-Action Pos** | **[4, 4]** (Shed access tile) | **[4, 3]** (Stranded north of shed) | $\Delta = (0, +1)$ coordinate shift |
| **Step 3 Shed Adjacency** | **TRUE** (`_is_shed_adjacent` = True) | **FALSE** (`_is_shed_adjacent` = False) | Prerequisite for livestock pickup |
| **Step 3 Teacher Action** | `['PICKUP', 'COW', 1]` | `['PICKUP', 'COW', 1]` | Teacher retrieves animal from shed |
| **Step 3 Policy Action** | `['SOUTH']` (Moves to [4, 5]) | `['PICKUP', 'COW', 1]` (No-op) | **Second divergence occurs at Step 3** |
| **Terminal Cash (Seed 249675)** | **$0.00** | **$0.00** | Wage-drain starvation persists |
| **Terminal Cash (Seed 249676)** | **$0.00** | **$0.00** | Wage-drain starvation persists |
| **Terminal Cash (Seed 249677)** | **$0.00** | **$0.00** | Wage-drain starvation persists |

---

## 3. CAUSAL MECHANISM ANALYSIS

### 3.1 Step 2 Geometrical Restoration
In Counterfactual A, executing `['SOUTH']` successfully moves the farmer from `[4, 3]` to `[4, 4]`.
This repairs the primary physical defect identified in P5:
1. The farmer arrives at a valid shed-adjacent tile (`[4, 4]`), exactly matching the teacher's physical location at Step 3.
2. Shed adjacency predicate `_is_shed_adjacent((4, 4), 10)` evaluates to `True`.
3. In contrast, in Counterfactual B, `['PICKUP', 'COW', 1]` is rejected by the simulator engine, leaving the farmer frozen at `[4, 3]`.

### 3.2 The Horizon Shift Phenomenon (The Step-3 Barrier)
Crucially, Counterfactual A reveals that fixing Step 2 alone **does not restore economic compounding**.
Why does terminal cash remain $0.00 in Counterfactual A?

When the policy arrives at `[4, 4]` at Step 3, the teacher's action is `['PICKUP', 'COW', 1]`.
However, because Step 3 was not separately weighted with a massive objective multiplier ($\lambda = 50.0$), the feed-forward policy outputs `['SOUTH']`, moving to `[4, 5]`.
- The farmer skips picking up livestock from the shed.
- Without livestock in inventory, the farmer cannot place cows or sheep into pastures.
- The 5 hired hands (hired at Step 1 for $500 total, with $25/step ongoing wages) remain idle or wander purposelessly.
- Cash drains from ~$1,005 at Step 1 down to $0.00 by Step 41 due to worker wages without agricultural revenue.

### 3.3 Theoretical Significance: The Limits of Step-by-Step Behavioral Cloning
This counterfactual provides definitive scientific evidence for the nature of the policy's failure mode:
1. **Covariate shift is not the root cause of the early errors**: At Step 0, Step 1, and Step 2, the policy is on the exact teacher manifold.
2. **Feed-forward reactive policies lack open-loop script coherence**: In an expert scripted policy like A7, actions at Steps 0, 1, 2, 3, 4 form a rigid, non-Markovian sequence (`WASH -> NORTH+HIRE -> SOUTH -> PICKUP COW -> PICKUP SHEEP -> ...`).
3. **Weighting individual steps shifts the error horizon by +1**:
   - In P4: Policy failed at Step 1 (predicted `SOUTH` instead of `NORTH+HIRE`). Weighted Step 1 $\to$ Step 1 repaired.
   - In P5: Error moved to Step 2 (predicted `PICKUP` at [4, 3] instead of `SOUTH`). Weighted Step 2 $\to$ Step 2 repaired.
   - In P6: Step 2 repaired $\to$ error moves to Step 3 (predicts `SOUTH` instead of `PICKUP`).

---

## 4. CONCLUSION & PREREGISTERED VERDICT

The causal counterfactual proves:
1. The Step-2 error was an on-manifold classification failure that prevented shed access.
2. Executing `SOUTH` at Step 2 physically restores the farmer to the shed access tile [4, 4].
3. However, **single-step intervention at Step 2 is insufficient to recover economic compounding** because the feed-forward policy immediately diverges at Step 3 (`SOUTH` instead of `PICKUP`).
4. This confirms **P6 PARTIAL**: Step-2 failure repaired, but downstream compounding remains blocked.
