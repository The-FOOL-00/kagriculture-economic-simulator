# V32 P5 — DECISION REPORT: CLOSED-LOOP BC RECOVERY & COVARIATE-SHIFT DIAGNOSIS

## 1. PRIMARY CONCLUSION

```text
P5 PARTIAL — divergence delayed, but downstream compounding remains
```

```text
PPO 1M SLOPE GATE: CLOSED
```

---

## 2. EXECUTIVE SUMMARY

Phase V32 P5 was launched to resolve the core scientific bottleneck identified at the conclusion of P4:
> *Why does the P4 policy, after correctly executing the economically critical step-0 opening action, begin diverging at approximately steps 1–10 and then catastrophically compound error over the remaining horizon — and can closed-loop training recover stable behavior without changing the already-validated state/action architecture?*

Through an exhaustive series of controlled diagnostic experiments, forensic audits, counterfactual replays, and bounded early-horizon training (Arm 2), P5 establishes:

1. **Covariate Shift & Compounding Error are Empirically Proven (H1 Confirmed)**:
   In teacher-forced Mode A, the model achieves high action fidelity (89.17% step-0 full-action match, 82.4% overall). In free-running Mode B, exact action accuracy collapses to 0.0% by Step 2. As policy-generated states leave the training demonstration manifold ($\min_{x \in \mathcal{D}} \|s_t^P - x\|_2$ jumps from $0.000$ to $16.791$ at Step 2 and $30.66$ at Step 718), error compounds catastrophically.
2. **First Divergence Was Successfully Delayed (H2 Confirmed & Partially Repaired)**:
   In P4 Arm 1, the unweighted unit head caused the farmer to move `WEST` (54.6% probability) instead of `PASS` (4.46% probability) at Step 0, derailing hiring at Step 1.
   Under P5 Arm 2 (bounded early-horizon weighting $\lambda_{crit}=50.0, \lambda_{early}=10.0$), Step 0 was 100% repaired (`PASS` 120/120, Wash 120/120) and Step 1 was 100% repaired (`NORTH` 120/120, 5-hires 120/120, mean 5.00 hands).
   The median first action divergence moved from **Step 0 to Step 2 (+2 steps later)**.
3. **Downstream Economic Compounding Remained Unrepaired**:
   Despite perfect Step 0 and Step 1 execution, the policy diverged at Step 2 by issuing a premature `['PICKUP', 'COW']` at coordinate [4, 3] rather than stepping `SOUTH` into shed [4, 4]. The pickup command was rejected by the game engine, the farmer became stranded at [4, 0], and the 5 hired hands idled on the field. Wage deductions rapidly consumed the remaining $1,005 capital, leaving **$2.94 mean terminal cash ($0.00 median, 0 wins)** across all 120 development screen legs.
4. **Valid Off-Distribution Expert Relabeling is Infeasible (Case B Expert Oracle)**:
   The Expert Oracle Audit revealed that `E2_A7` is an open-loop macro tape replayer (`routes[route][step]`), not a Markovian or counterfactual state planner. When queried on off-distribution states, it emits illegal actions (e.g. buying animals with $0 cash). True DAgger / dataset aggregation is therefore mathematically impossible without faking or fabricating heuristic labels (which is strictly prohibited).
5. **Rigid Open-Loop Trajectory Limits Behavioral Cloning**:
   Pure Behavioral Cloning without an interactive corrective oracle cannot reliably maintain the multi-step temporal dependencies of the A7 macro-choreography. A single physical timing mismatch at Step 2 renders the entire upstream capital investment in livestock and workers completely unrecoverable.

---

## 3. ANSWERS TO SECTION 41 MANDATORY QUESTIONS

### Q1. Was P4's step-1–10 divergence reproduced?
**YES.**
In the baseline reproduction (`V32_P5_BASELINE_REPRO.md`), the canonical P4 Arm 1 checkpoint was evaluated across 240 diagnostic steps and 120 screen legs. While step-0 wash execution was 100% intact (240/240 probe, 120/120 screen), the unweighted unit head caused the farmer to move `WEST` at Step 0 with 54.64% probability (vs 4.46% for `PASS`). At Step 1, under the resulting displaced observation ($\|s_1^P - s_1^T\| = 21.376$), the model failed to hire hands and failed to purchase livestock contracts, leading to terminal cash of $108.39 mean ($0.50 median) and 0 wins.

### Q2. How large was teacher-forced vs free-running degradation?
**MASSIVE (Catastrophic Degradation).**
- **Mode A (Teacher-Forced)**:
  - Step-0 Action Accuracy: **89.17%**
  - Step-1 Action Accuracy: **87.50%**
  - Overall Trajectory Action Accuracy: **82.4%**
  - Manifold Distance: Strictly **0.000** (constrained to expert trajectory)
- **Mode B (Free-Running)**:
  - Step-0 Action Accuracy: 50.0% (P4) $\to$ 100.0% (P5 Arm 2)
  - Step-1 Action Accuracy: 0.0% (P4) $\to$ 100.0% (P5 Arm 2)
  - Step-2 Action Accuracy: **0.0%**
  - Terminal Cash: **$2.94** (vs expert's ~$28,000+, a >99.9% loss of economic compounding).

### Q3. Did policy-generated states leave the training manifold?
**YES, IMMEDIATELY UPON FIRST ACTION MISMATCH.**
Empirical nearest-neighbor Euclidean distance $\min_{x \in \mathcal{D}} \|s_t^P - x\|_2$ to the 138k expert transitions in the training dataset (`V32_P5_STATE_DISTRIBUTION.md`):
- Steps 0–1: **0.000** (on-manifold demonstration state)
- Step 2: **16.791** (dislocated immediately following the Step 2 action error)
- Step 10: **19.080**
- Step 72: **18.472**
- Step 288: **23.491**
- Step 718: **30.660**
Once displaced, the policy never returned to the training manifold.

### Q4. What was the first economically meaningful divergence?
**STEP 2 (Premature Pickup Attempt).**
- In P4 Arm 1, the first divergence occurred at Step 0 (`WEST` instead of `PASS`).
- In P5 Arm 2, after executing Step 0 (`PASS` + wash) and Step 1 (`NORTH` + 5 hires), the teacher farmer steps `SOUTH` back into the shed [4, 4] to retrieve livestock.
- The Arm 2 model at [4, 3] commanded `['PICKUP', 'COW']` while standing 1 tile away from the shed.
- The simulator rejected the pickup. The farmer held 0 animals, subsequently walked North to [4, 0] and became permanently stranded.
- The 5 hired hands idled on the field. By Step 24 (end of Day 1), wages consumed the remaining $1,005 in cash.

### Q5. Was the error concentrated in one early decision or distributed?
**CONCENTRATED IN ONE EARLY PHYSICAL SEQUENCING DECISION.**
Forensic analysis (`V32_P5_FIRST_DIVERGENCE.md`, `V32_P5_EARLY_HORIZON.md`) established that the entire failure cascade stemmed from the Step 2 positional coordination failure. The upstream market wash and hiring decisions were 100% correct, and the capital expenditure ($1,747) was correctly committed. The failure of that single step rendered all prior investments unrecoverable.

### Q6. Is covariate shift/compounding demonstrated?
**YES, DEFINITIVELY DEMONSTRATED.**
The causal chain was traced step-by-step:
$$\text{Policy Action at } t_2 \implies \text{Simulator Rejection} \implies \text{Unfamiliar State } s_3^P \implies \text{OOD Action Selection} \implies \text{Complete Wage Starvation}.$$

### Q7. Is a valid expert oracle available for off-distribution states?
**NO (CASE B: INFEASIBLE).**
`V32_P5_EXPERT_ORACLE_AUDIT.md` conclusively audited `candidates/v30_a7_standalone/main.py` and `aec/backbone/v3_adapter.py`. A7 is an open-loop macro tape replayer (`routes[route][step]`). It lacks a Markovian state planner or counterfactual evaluator. Querying A7 on off-distribution states yields illegal, invalid actions.
Per Sections 16, 17, and 19 of the Protocol, DAgger / dataset aggregation cannot be faked or run with synthetic heuristic labels.

### Q8. Did the chosen closed-loop training intervention reduce divergence?
**YES, FOR THE FIRST TWO TIMESTEPS.**
Bounded early-horizon weighting ($\lambda_{crit}=50.0, \lambda_{early}=10.0$) completely solved the Step 0 farmer error (`PASS` 100% recovered) and the Step 1 hiring sequence (5.00/5.00 hands hired across 120/120 legs).

### Q9. Did first meaningful divergence move later?
**YES.**
The median first action divergence moved from **Step 0 to Step 2 (+2 steps later)**.
The median first state divergence moved from **Step 1 to Step 2 (+1 step later)**.

### Q10. Did closed-loop economics materially improve?
**NO.**
Terminal cash remained in the flat-zero regime:
- P4 Arm 1: Mean **$108.39**, Median **$0.50**, Wins: **0 / 120**
- P5 Arm 2: Mean **$2.94**, Median **$0.00**, Wins: **0 / 120**
Because Arm 2 successfully hired 5 workers at Step 1, the subsequent stall at Step 2 caused active wage bleed ($100/day starting Day 1), accelerating cash exhaustion compared to P4's idle farmer.

### Q11. What fraction of the original P4 failure was repaired?
**OPENING DISLOCATION: 100% REPAIRED.**
**DOWNSTREAM ECONOMIC COMPOUNDING: 0% REPAIRED.**
The model learned to execute the opening wash and the initial hiring sequence, but failed to maintain the physical multi-step coordination required to extract value from those investments.

### Q12. Is generalization justified?
**NO.**
Per Section 29 and Section 30, because closed-loop economics failed to recover, the Generalization Gate is firmly closed. No protected holdout seeds (`249685–249694`, `249695–249734`, `214200–214249`, `340090–340199`) were accessed or consumed.

### Q13. Is PPO still closed?
**YES. PPO 1M SLOPE GATE: CLOSED.**
The prerequisite conditions for reopening PPO (a viable, closed-loop stabilized BC policy demonstrating positive economic compounding) have not been satisfied.

---

## 4. EXPERIMENT ARMS SUMMARY

| Arm | Description | Purpose | Status | Key Result |
|:---:|:---|:---|:---:|:---|
| **Arm 0** | Frozen P4 Arm 1 Baseline | Control | **Complete** | Wash: 120/120, Farmer Pass: 0/120, Cash: $108.39, Div: Step 0 |
| **Arm 1** | Diagnostic Rollout (Modes A & B) | Covariate-shift detection | **Complete** | Teacher fidelity 82.4% vs Free-run 0% at Step 2; Manifold dist 0 $\to$ 16.79 |
| **Arm 2** | Bounded Early-Horizon Weighting | Test early error concentration | **Complete** | Wash: 120/120, Pass: 120/120, Hires: 5.00/5.00, Div: Step 2, Cash: $2.94 |
| **Arm 3** | Valid DAgger / State Aggregation | Test oracle relabeling | **Infeasible** | Blocked by Case B Audit (A7 is an open-loop tape replayer) |
| **Arm 4** | Mixed Teacher/Policy Roll-in | Test roll-in training | **Infeasible** | Blocked by Case B Audit (Off-distribution labels undefined) |

---

## 5. MACHINE-READABLE RUN RECORD

```json
{
  "phase": "V32_P5",
  "conclusion": "P5 PARTIAL — divergence delayed, but downstream compounding remains",
  "ppo_gate": "CLOSED",
  "baseline_checkpoint": "results/v32_p4_arm1_balanced.npz",
  "candidate_checkpoint": "results/v32_p5_arm2_early_weighting.npz",
  "architecture": "P3Policy(157, 12)",
  "loss_formulation": "L_unit + L_market + 50.0 * L_crit_s0 + 10.0 * L_early_s1_10",
  "development_seeds": "249675:249684",
  "opponents": ["E0_V3", "E1_V22R1", "E2_A7", "E3_V25P3", "E6_W72", "E7_W2015"],
  "seats": [0, 1],
  "total_eval_legs": 120,
  "metrics": {
    "step0_wash_rate": 1.0,
    "step0_pass_rate": 1.0,
    "step1_north_rate": 1.0,
    "step1_mean_hires": 5.0,
    "median_first_action_div": 2,
    "median_first_state_div": 2,
    "terminal_cash_mean": 2.94,
    "terminal_cash_median": 0.0,
    "terminal_cash_std": 31.09,
    "terminal_cash_min": 0.0,
    "terminal_cash_max": 342.0,
    "worst_5pct_cash": 0.0,
    "worst_1pct_cash": 0.0,
    "win_rate": 0.0
  },
  "safety_exit_verified": true,
  "holdout_protection_verified": true
}
```

---

## 6. RECOMMENDATIONS FOR SUBSEQUENT RESEARCH

1. **Acknowledge the Fundamental Barrier of Open-Loop BC for Complex Multi-Step Choreography**:
   Behavioral Cloning on demonstrations generated by non-Markovian, open-loop macro scripts cannot acquire robust error-recovery behavior. A neural policy must either:
   - Learn on demonstrations generated by a true **Markovian closed-loop planner** that exhibits natural recovery behaviors across diverse states; or
   - Be trained with closed-loop policy exploration where the agent experiences the consequences of missteps directly.
2. **Do Not Attempt Unprincipled Synthetic Relabeling**:
   Faking expert labels with ad-hoc heuristics violates scientific reproducibility and risks creating contradictory policy behaviors.
3. **PPO Gate Status**:
   Remains strictly **CLOSED** until an architecture or training methodology provides a baseline policy capable of non-zero economic compounding in closed-loop play.
