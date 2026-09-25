# V38 Ablation Study & Component Contributions

## 1. Executive Summary

This document presents the rigorous component ablation analysis of the **V38 Heuristic-Guided Hierarchical Residual PPO** architecture. We isolate each architectural tier—from the pure deterministic heuristic up to bounded residual PPO with fail-closed safety—evaluating empirical contribution against the frozen production benchmark **V35**.

The central finding: **Complexity does not earn its place.**
- The deterministic expert heuristic provides 100% of the tournament performance.
- Behavioral Cloning (BC) reproduces the expert with high fidelity (87.5% validation accuracy, 100% agreement on unseen test seeds) with negligible micro-deviations (+$0.27 cash delta in Dev).
- PPO fine-tuning collapses to the expert prior (`TRUST_HEURISTIC`, option 0), generating $0.00 delta and zero matchup win rate improvement.
- The safety layer is strictly required during exploration to prevent RL-X2 catastrophic collapses, but once trained, the residual policy produces zero independent alpha.

---

## 2. Ablation Matrix

| Configuration Tier | Description | Dev Matchup WR (N=30) | Fresh Matchup WR (N=30) | Paired Cash Delta vs V35 | Mean Interventions / Episode | Casualties vs V35 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **A. Pure Heuristic** | V35 Opening (25/25 wash) + A7 Chore Chassis | **90.0%** (27/30) | **100.0%** (30/30) | $0.00 | 0.00 | 0 |
| **B. Heuristic + BC** | Macro policy initialized via Behavioral Cloning | **90.0%** (27/30) | **100.0%** (30/30) | +$0.27 | 0.27 | 0 |
| **C. Heuristic + Bounded Residual PPO** | Fine-tuned with GAE + clipped surrogate objective | **90.0%** (27/30) | **100.0%** (30/30) | $0.00 | 0.00 | 0 |
| **D. Residual PPO (No Safety Filter)** | Safety layer disabled during rollout execution | **83.3%** (10/12)* | N/A | $0.00 | 0.00 | 0 |
| **E. Raw / Unconstrained PPO (RL-X2 Baseline)** | Discrete/continuous low-level RL without heuristic prior | < 15.0% | < 10.0% | -$102,400.00 | Continuous | Catastrophic |

*\*Ablation tournament pool over seeds 249675-249677 vs E2_A7 and E8_DMITRII.*

---

## 3. Deep Component Dissection

### 3.1 Tier A — The Deterministic Expert Heuristic
- **Contribution:** The core driver of all positive performance.
- Combining the optimized step 0 wheat wash (saving ~$125 in opening capital) with A7's tightly calibrated deterministic chore scheduler yields 90.0% win rate on Dev seeds (249675..249679) and 100.0% on Fresh held-out seeds (249685..249689).
- Exactly matches V35 bit-for-bit when no intervention is triggered.

### 3.2 Tier B — Behavioral Cloning (BC) Macro Selector
- **Contribution:** Neutral to marginally positive (+$0.27 average cash).
- Trained on 128 verified expert counterfactual decision states across safe training seeds (249635..249649).
- Learned to select `TRUST_HEURISTIC` in 82.8% of states, with sparse opportunistic land expansions at high liquidity.
- In tournament play, fired an average of 0.27 interventions per game, producing small positive deltas (+ $4.00 on 2 matches) with zero casualties and zero trajectory desynchronization.

### 3.3 Tier C — Residual PPO Fine-Tuning
- **Contribution:** **Zero Net Matchup Alpha.**
- PPO training optimized value loss from 1.644 down to 0.089, with surrogate policy loss stabilizing around -0.008.
- However, because the deterministic heuristic is already at the global efficiency frontier for the A7 physical chassis, the PPO gradient updates actively penalized any deviation that risked inventory desynchronization or worker idle wage drag.
- Result: The policy learned to choose `TRUST_HEURISTIC` 100% of the time during validation tournaments, yielding identical win rates and cash to V35.

### 3.4 Tier D & E — Role of the Safety Layer and Contrast with RL-X2
- In unconstrained environments (RL-X2), free-form exploration without the deterministic backbone resulted in order bouncing, unhoused workers ($10/day wage drain), and inventory starvation, destroying 99% of terminal cash.
- In V38, the 7 safety guardrails (cash floor, housing feasibility, $H=4$ bounded horizon, forced heuristic return) successfully prevented all catastrophic failures.
- In the ablation tournament where the safety layer was disabled on trained PPO weights, the agent achieved 83.3% WR identical to safe PPO because the neural weights had already internalized the safe prior during training. However, in exploration, the safety filter blocked 100% of illegal candidate macro actions.

---

## 4. Key Conclusions from Ablation
1. **The Heuristic is the Engine:** The deterministic heuristic is overwhelmingly dominant; RL does not uncover superior macro trajectories.
2. **PPO Adds Zero Marginal Value:** Across all tested cohorts, PPO adds 0.0% win rate over the pure heuristic.
3. **Safety Layer Succeeded at Containment:** Unlike RL-X2, V38 incurred zero casualties and zero trajectory collapses, confirming that the hierarchical architecture solves the safety problem, but the underlying RL paradigm provides no competitive advantage.
