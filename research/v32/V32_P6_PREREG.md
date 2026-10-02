# V32 P6 — PREREGISTRATION DOCUMENT

## 1. PURPOSE & SCIENTIFIC HYPOTHESES

Phase **V32 P6** continues the Kagriculture V32 research program to resolve the first post-opening economically catastrophic policy decision identified in Phase P5.

The immediate scientific question:
> *Why does the current repaired BC policy, after correctly reproducing Step 0 and Step 1, choose `PICKUP(COW)` at Step 2 instead of the expert `SOUTH` action, and can this exact failure be eliminated with a simulator-grounded semantic action mask and targeted early farmer-head stabilization?*

### H1 — SIMULATOR-LEGALITY MISMATCH (SEMANTIC MASK HYPOTHESIS)
The model predicts `['PICKUP', 'COW']` at Step 2 while standing at coordinate [4, 3]. Under simulator source semantics (`kaggriculture.py:350-352`), `PICKUP` is only valid when `_is_shed_adjacent((fx, fy), board_size)` is True. Because [4, 3] is outside the 4 shed-access tiles `{(4, 4), (5, 4), (4, 5), (5, 5)}`, the simulator silently rejects the action. An exact, source-grounded semantic action mask will prevent this illegal prediction and force the categorical distribution to select from simulator-valid actions.

### H2 — ON-MANIFOLD CLASS IMBALANCE (FARMER HEAD HYPOTHESIS)
Even on the exact teacher-generated Step-2 observation, the unweighted farmer action head prefers `PICKUP` over `SOUTH` due to global training class imbalance or feature confusion between [4, 3] and shed tiles. Targeted early farmer-head rebalancing or hard-negative loss will elevate `SOUTH` above `PICKUP`.

### H3 — DOWNSTREAM CAUSAL RESTORATION HYPOTHESIS
Executing `SOUTH` at Step 2 returns the farmer to the shed access tile [4, 4], enabling legitimate animal pickup at Step 3, active deployment of hired hands, and prevention of the $1,005 wage-drain starvation cascade.

---

## 2. EXPERIMENTAL ARMS

| Arm | Name | Training Required? | Core Question / Intervention |
|:---:|:---|:---:|:---|
| **Arm 0** | Frozen P5 Arm 2 Baseline | No | Control baseline reproducing the Step-2 failure across 120 screen legs. |
| **Arm 1** | Exact Semantic Mask Only | No | Apply source-grounded legality mask at inference. Does removing illegal `PICKUP` alone allow `SOUTH` to win? |
| **Arm 2** | Targeted Farmer-Head Rebalancing | Yes | If `SOUTH` loses to another valid action in Arm 1, train with targeted early farmer-head class weighting ($\lambda_{farmer\_early}$). |
| **Arm 3** | Hard-Negative Margin Training | Yes | If logits show systematic wrong-action bias, apply margin loss between `SOUTH` and the top false action. |
| **Arm 4** | Prefix Distillation | Yes | If individual step weighting fails, apply bounded trajectory sequence distillation on Steps 0–24. |
| **Arm 5** | State-Conditioned Safety Gate | Conditional | Generalized exact action feasibility predicates across all unit actions. |

---

## 3. STRICT DECISION GATES

### Gate 1: Simulator-Legality Verification
The semantic mask must strictly reflect the exact source implementation of `_apply_unit_action` in `kaggriculture.py`. It must never mask an action that the simulator would execute, and must never permit an action the simulator would reject as a no-op.
*Requirement*: 0 discrepancies across the test corpus in `tests/test_v32_p6_semantic_mask.py`.

### Gate 2: First Divergence Delay
A candidate passes behavioral stabilization only if:
- Step 0 Wash = 100%
- Step 0 Farmer PASS = 100%
- Step 1 Farmer NORTH = 100%
- Step 1 Hires = 5.00 / 5.00
- Step 2 Farmer SOUTH > 95%
- Median First Action Divergence > Step 2.

### Gate 3: Economic Compounding Gate
A candidate achieves P6 PASS only if closed-loop terminal cash improves materially above the flat-zero regime (Mean Cash > $500, non-zero median, no wage-drain starvation).

### Gate 4: Holdout Protection Gate
Protected cohorts (`249685–249694`, `249695–249734`, `214200–214249`, `340090–340199`) remain strictly unopened. Only development seeds `249675:249684` are used for screen evaluations.

### Gate 5: PPO Gate
`PPO 1M SLOPE GATE: CLOSED`. No RL training is permitted during Phase P6.
