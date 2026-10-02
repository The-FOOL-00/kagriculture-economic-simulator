# V32 P6 — DECISION REPORT: CRITICAL STEP-2 RECOVERY & SEMANTIC ACTION STABILIZATION

## 1. PRIMARY CONCLUSION

```text
PRIMARY CONCLUSION:
P6 PARTIAL — Step-2 failure repaired, but downstream compounding remains

PPO 1M SLOPE GATE: CLOSED
```

---

## 2. EXECUTIVE SUMMARY

Phase **V32 P6** was launched to resolve the primary post-opening failure identified at the conclusion of P5:
> *Why does the repaired P5 BC policy choose `['PICKUP', 'COW']` at Step 2 instead of the expert `['SOUTH']` action, and can this exact failure be eliminated with a simulator-grounded semantic action mask and targeted early farmer-head stabilization?*

Through an exhaustive series of controlled diagnostic experiments, logit analyses, simulator source audits, and full 120-leg closed-loop screen evaluations across two active experimental arms (Arm 1: Mask-only; Arm 2: Targeted Rebalancing + Mask), P6 establishes the following definitive conclusions:

1. **Step-2 Failure Was an On-Manifold Action Classification Error**:
   Bit-identical pre-action state reconstruction (`V32_P6_STEP2_RECONSTRUCTION.md`) proved that the policy at Step 2 is physically and observationally identical to the expert (farmer at `[4, 3]`, 5 hands at identical coordinates, shed containing 2 cows and 2 sheep, ~$1,005 in cash). Covariate shift is the *consequence*, not the *cause*, of the Step-2 action error.
2. **Simulator Source Semantics Confirmed Illegal Pickup**:
   Under `kaggriculture.py:350-352`, `PICKUP` is only permitted when `_is_shed_adjacent((fx, fy), board_size)` is True. At coordinate `[4, 3]`, `PICKUP` is outside the 4 shed-access tiles `{(4, 4), (5, 4), (4, 5), (5, 5)}` and is silently rejected by the simulator engine as a no-op.
3. **Semantic Mask Alone is Necessary But Insufficient (Arm 1 Result)**:
   Logit decomposition (`V32_P6_STEP2_LOGITS.md`) revealed the policy's unmasked logits: Rank 1: `PICKUP` (+8.204, 81.6%), Rank 2: `NORTH` (+6.599, 16.4%), Rank 3: `SOUTH` (+4.487, 2.0%). In Arm 1 (`V32_P6_MASK_EVAL.md`), masking out illegal `PICKUP` caused the policy to select Rank 2 `NORTH` (120/120 legs), walking further north to `[4, 2]` instead of `SOUTH` to `[4, 4]`.
4. **Targeted Farmer-Head Rebalancing Completely Repaired Step 2 (Arm 2 Result)**:
   By training with targeted Step-2 farmer loss ($\lambda_{s2} = 50.0$), `SOUTH` became Rank 1 with >99% probability. Across all 120 development screen legs (`V32_P6_CLOSED_LOOP.md`), the policy achieved **120/120 (100.0%) execution of `SOUTH`** at Step 2.
5. **The Error Horizon Shifted to Step 3 ($t_{\text{act}} = 3$)**:
   With Step 2 repaired, the farmer arrived at `[4, 4]` (shed tile) at Step 3, bit-identical to the expert. However, at Step 3, the unweighted policy commanded `['SOUTH']` instead of retrieving livestock via `['PICKUP', 'SHEEP']`. The divergence was delayed by exactly +1 step, confirming that pointwise step-weighting shifts the failure boundary sequentially.
6. **Economic Compounding Remains Blocked**:
   Because livestock was not retrieved at Step 3, pasture construction and stocking stalled. The 5 hired hands idled on the field while drawing $25/step in wages, completely exhausting capital by Step 41 ($0.07 mean terminal cash, $0.00 median, 0 wins).
7. **PPO Remains Strictly CLOSED**:
   Because economic compounding was not recovered, Gate 3 failed. PPO is firmly closed.

---

## 3. ANSWERS TO SECTION 42 MANDATORY QUESTIONS

### Q1. Was the Step-2 failure mechanism successfully reproduced?
**YES.**
In `V32_P6_STEP2_RECONSTRUCTION.md` and `V32_P6_STEP2_LOGITS.md`, the canonical P5 Arm 2 model was evaluated on the exact Step-2 pre-action state. Across all 120 control screen legs in P5, the policy emitted `['PICKUP', 'COW']` at coordinate `[4, 3]`. Logit evaluation confirmed that `PICKUP` held an overwhelming +8.204 logit (81.6% probability) compared to +4.487 (1.98%) for the expert `SOUTH` action.

### Q2. Did the simulator-grounded semantic action mask eliminate illegal PICKUP?
**YES, COMPLETELY (100.0%).**
The source-grounded mask derived in `v32/p6/mask.py` strictly mirrors `kaggriculture.py:350-352`. In `tests/test_v32_p6_semantic_mask.py`, the mask achieved 0 discrepancies against the simulator across 1,000 randomized unit positions and states. Across all 240 screen legs evaluated under masking (120 in Arm 1, 120 in Arm 2), illegal `PICKUP` at coordinate `[4, 3]` occurred **0 / 240 times (0.0%)**.

### Q3. Did the semantic mask alone allow SOUTH to win (Arm 1 result)?
**NO.**
In `V32_P6_MASK_EVAL.md`, evaluating P5 Arm 2 with the semantic mask demonstrated that removing `PICKUP` merely promoted the next-highest unmasked legal action, which was `NORTH` (+6.599 logit, 89.2% of remaining mass). In **120 / 120 legs (100.0%)**, the policy moved `NORTH` to `[4, 2]`. `SOUTH` received 0 / 120 selections. Terminal cash was $0.03 mean ($0.00 median). Masking is strictly necessary to prevent illegal execution, but cannot change preference order among valid actions.

### Q4. Did targeted farmer-head rebalancing repair Step 2 (Arm 2 result)?
**YES, COMPLETELY (100.0%).**
In `V32_P6_FARMER_REBALANCE.md`, training with targeted loss formulation $\mathcal{L}_{total} = \mathcal{L}_{unit} + \mathcal{L}_{mkt} + 50.0 \cdot \mathcal{L}_{crit}^{s=0} + 10.0 \cdot \mathcal{L}_{early}^{s \in [1, 10]} + 50.0 \cdot \mathcal{L}_{farmer\_op}^{s=2}$ elevated `SOUTH` to >99.8% probability. In the 120-leg closed-loop screen (`results/v32_p6_eval_arm2.jsonl`), **120 / 120 legs (100.0%)** executed `SOUTH` at Step 2.

### Q5. Did the first action divergence move later?
**YES.**
- In P4 Arm 1: Median $t_{\text{act}} = \text{Step 0}$ (`WEST` instead of `PASS`).
- In P5 Arm 2: Median $t_{\text{act}} = \text{Step 2}$ (`PICKUP` instead of `SOUTH`).
- In P6 Arm 2: Median $t_{\text{act}} = \text{Step 3}$ (`SOUTH` instead of `PICKUP`).
First action divergence was successfully delayed by **+1 step later** relative to P5, and **+3 steps later** relative to P4.

### Q6. What was the exact first divergence point under Arm 2?
**STEP 3 ($t_{\text{act}} = 3, t_{\text{state}} = 3$).**
Pre-action state at Step 3 was bit-identical to the teacher: farmer at `[4, 4]`, 5 hands surrounding the shed, cash ~$1,005. At Step 3, the teacher executed `['PICKUP', 'SHEEP']` (or `['PICKUP', 'COW']`), whereas the P6 Arm 2 policy executed `['SOUTH']`, moving to `[4, 5]`.

### Q7. What happened at Step 3?
**LIVESTOCK PICKUP WAS SKIPPED.**
Standing at the shed tile `[4, 4]`, where `PICKUP` is fully legal, the policy had not been assigned a specific Step-3 loss multiplier. The categorical distribution chose `SOUTH`, moving the farmer away from the shed with zero livestock in inventory. The 5 hired hands were left without livestock to tend, and wage deductions ($25/step) drained the farm to starvation ($0.00 cash).

### Q8. Did closed-loop terminal cash improve?
**NO.**
Terminal cash remained in the flat-zero regime:
- Mean cash: **$0.07** (vs $2.94 in P5 Arm 2, $108.39 in P4 Arm 1).
- Median cash: **$0.00**.
- Standard deviation: **$0.82**.
- Win rate: **0.0% (0 / 120 wins)**.

### Q9. Did the policy achieve positive economic compounding?
**NO.**
Economic compounding requires completing the full agricultural production loop: hiring workers $\to$ stocking pastures $\to$ harvesting wool/milk $\to$ reinvesting profits. Because the sequence broke at Step 3, the initial capital outlay ($1,747) was lost, resulting in 100% economic starvation.

### Q10. Did the causal counterfactual prove Step 2 is causally necessary/sufficient?
**CAUSALLY NECESSARY, BUT INSUFFICIENT ALONE.**
The causal counterfactual analysis (`V32_P6_COUNTERFACTUAL.md`):
- Forcing `SOUTH` at Step 2 (Counterfactual A) physically placed the farmer at `[4, 4]` at Step 3, repairing the physical dislocation.
- However, because the unconstrained policy immediately diverged at Step 3 (`SOUTH` instead of `PICKUP`), terminal cash in Counterfactual A was still $0.00.
- Executing `SOUTH` at Step 2 is strictly necessary to reach the shed, but insufficient without downstream trajectory coherence.

### Q11. What is the fundamental limitation of feed-forward BC revealed by P4 $\to$ P5 $\to$ P6?
**POINTWISE REBALANCING CAUSES SEQUENTIAL HORIZON SHIFTING.**
A feed-forward policy without temporal memory or an explicit step-index token cannot learn an open-loop 25-step scripted sequence through independent per-step cross-entropy rebalancing. Forcing step $t$ via a massive loss multiplier ($\lambda = 50.0$) merely shifts the policy divergence to step $t+1$. Pure reactive BC on a rigid macro-script suffers from the curse of sequential imitation error.

### Q12. Is generalization testing on protected holdouts justified?
**NO.**
Because Gate 3 (Economic Compounding Gate) failed, the Generalization Gate is firmly closed. All protected holdout cohorts (`249685–249694`, `249695–249734`, `214200–214249`, `340090–340199`) were audited and confirmed 100% virgin (`V32_P6_COMPETITION_SAFETY_EXIT.md`).

### Q13. Is PPO still closed?
**YES. PPO 1M SLOPE GATE: CLOSED.**
The prerequisite condition for opening PPO (a viable closed-loop BC policy producing positive economic compounding above $500) has not been achieved. Launching RL on a policy that collapses into wage-drain starvation within 25 steps would fail due to zero-reward gradient sparsity.

### Q14. What is the primary conclusion and next step?
**P6 PARTIAL — Step-2 failure repaired, but downstream compounding remains.**
The next phase must address trajectory-level sequence coherence rather than step-by-step pointwise rebalancing (e.g. bounded trajectory prefix distillation, state-conditioned safety gates, or explicit macro-phase conditioning).

---

## 4. EXPERIMENTAL ARMS SUMMARY

| Arm | Description | Purpose | Status | Key Results (120 Legs) |
|:---:|:---|:---|:---:|:---|
| **Arm 0** | Frozen P5 Arm 2 Baseline | Control baseline | **Complete** | S0 Wash: 100%, S0 Pass: 100%, S1 North: 100%, S2 Pickup: 100% (Illegal), Cash: $2.94 |
| **Arm 1** | Exact Semantic Mask Only | Test if mask alone fixes Step 2 | **Complete** | S2 Pickup: 0.0%, S2 North: 100.0%, S2 South: 0.0%, Div: Step 2, Cash: $0.03 |
| **Arm 2** | Targeted Rebalancing + Mask | Test early class-rebalancing ($\lambda_{s2}=50$) | **Complete** | S0 Pass: 100%, S1 North: 100%, S2 South: 100.0% (120/120), Div: Step 3, Cash: $0.07 |
| **Arm 3** | Hard-Negative Margin Training | Margin loss on top false action | **Not Needed** | Arm 2 achieved 100% Step 2 accuracy without margin loss |
| **Arm 4** | Prefix Distillation | Sequence distillation on Steps 0–24 | **Recommended for P7** | Pointwise weighting exhausted; sequence-level supervision needed |
| **Arm 5** | State-Conditioned Safety Gate | Legality predicates across all units | **Partially Integrated** | `compute_unit_op_mask` active across all units |

---

## 5. MACHINE-READABLE RUN RECORD

```json
{
  "phase": "V32_P6",
  "primary_conclusion": "P6 PARTIAL — Step-2 failure repaired, but downstream compounding remains",
  "ppo_gate": "CLOSED",
  "baseline_checkpoint": "results/v32_p5_arm2_early_weighting.npz",
  "candidate_checkpoint": "results/v32_p6_arm2_rebalanced.npz",
  "architecture": "P3Policy(157, 12)",
  "loss_formulation": "L_unit + L_market + 50.0 * L_crit_s0 + 10.0 * L_early_s1_10 + 50.0 * L_farmer_op_s2",
  "semantic_mask": "v32/p6/mask.py (Source-grounded from kaggriculture.py)",
  "development_seeds": "249675:249684",
  "opponents": ["E0_V3", "E1_V22R1", "E2_A7", "E3_V25P3", "E6_W72", "E7_W2015"],
  "seats": [0, 1],
  "total_eval_legs": 120,
  "metrics": {
    "step0_wash_rate": 1.0,
    "step0_pass_rate": 1.0,
    "step1_north_rate": 1.0,
    "step1_hires_mean": 5.0,
    "step2_south_rate": 1.0,
    "step2_pickup_rate": 0.0,
    "first_action_divergence_median": 3,
    "first_state_divergence_median": 3,
    "terminal_cash_mean": 0.07,
    "terminal_cash_median": 0.0,
    "terminal_cash_std": 0.82,
    "terminal_cash_min": 0.0,
    "terminal_cash_max": 9.0,
    "win_rate": 0.0,
    "worst_5pct_cash": 0.0,
    "worst_1pct_cash": 0.0
  },
  "gate_evaluations": {
    "Gate_1_Simulator_Legality": "PASS",
    "Gate_2_First_Divergence_Delay": "PASS",
    "Gate_3_Economic_Compounding": "FAIL",
    "Gate_4_Holdout_Quarantine": "PASS",
    "Gate_5_PPO_Gate": "CLOSED"
  }
}
```

---

## 6. PRODUCTION ASSET HASH AUDIT & QUARANTINE VERIFICATION

| Asset / File | Purpose | SHA256 Hash | Status |
|:---|:---|:---|:---:|
| `submission_aec_v22r1.tar.gz` | Production Slot A | `6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5` | **FROZEN** |
| `submission_a7_v30.tar.gz` | Production Slot B | `4a07673072b6aef9346bf4c21ee5a5979b9da50fccc609fb731dcdbf8f016619` | **FROZEN** |
| `submission_Vj_kc_v3.tar.gz` | Benchmark Opponent | `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` | **FROZEN** |
| `candidates/v30_a7_standalone/main.py` | Standalone A7 Source | `51c1d25245f68dd8de66b355f2ad6ca1d79de8af02efed521a5a82f7be69ce3f` | **FROZEN** |
| `results/v32_p4_arm1_balanced.npz` | P4 Checkpoint | `34587d45cd5ed4d91ed2cfd0423c0a2af41e9da8f6b14a769082f473089a7470` | **FROZEN** |
| `results/v32_p5_arm2_early_weighting.npz` | P5 Checkpoint | `8bfb219e27c01ca75662706e2329b3524b0a70183b069d2551a1d94a11884fe0` | **FROZEN** |

All protected holdouts (`214200–214249`, `340090–340199`, `249695–249734`, `249685–249694`) remain untouched and virgin.
Zero submission leakage.
Zero simulator modifications.
Zero model architecture modifications.
All 11 protocol invariants in `tests/test_v32_p6.py` verified and passing.
