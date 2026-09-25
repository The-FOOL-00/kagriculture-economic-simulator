# V32 P12 PPO Option Selector Report (P12-07)

## Executive Summary

Phase P12 explicitly tested whether introducing reinforcement learning (PPO) over the discrete option space ($a \in \{0, 1, \dots, 6\}$) adds any marginal economic advantage over the Exact Search-Gated Controller and the Supervised Option Selector.

In Experiment **P12-07 (PPO Option Selector)**:
1. We trained `OptionActorCritic` and `PPOOptionSelector` over discrete option choice decisions.
2. We evaluated the resulting closed-loop policy across 20 tournament legs against `E2_A7` and `E8_DMITRII`.
3. **Findings & Comparative Analysis:**
   - **PPO Selector:** Collapses to the safe absorbing state $a = 0$ (`FOLLOW_A7`), achieving 0 activations, Mean Cash = $94,950.40, and Paired Delta = **+$0.00**.
   - **Supervised Selector:** Captures 100% of validated opportunities, achieving Mean Cash = $102,177.60 and Paired Delta = **+$7,227.20**.
   - **Exact Search Gated Controller:** Oracle lookahead benchmark achieving identical Mean Cash = $102,177.60 and Paired Delta = **+$7,227.20**.

### Decision (Section 71 Decision Tree):
Under Section 71 of the Phase P12 specification:
> *"If PPO selector destabilizes or fails to improve robustly: discard PPO and retain exact / supervised controller."*

**Verdict: DISCARD PPO.** The supervised neural selector and deterministic search-gated controller are strictly superior, faster, more interpretable, and mathematically guaranteed against exploration-induced policy collapse.

---

## 1. Experimental Methodology

- **Actor-Critic Architecture:** 71-dim S2 economic features $\to$ 2-layer MLP (128, 64) $\to$ Categorical distribution over 7 discrete options.
- **Reward Signal:** Terminal cash advantage $\Delta = \text{Cash}_{\text{cand}} - \text{Cash}_{A7}$.
- **Safety Invariant:** PPO only controls discrete option triggering at detected milestones; it never controls low-level worker movement or farm chores.

---

## 2. Quantitative Comparative Benchmark

| Controller Architecture | Mode | Mean Cash ($) | Paired Mean $\Delta$ vs A7 ($) | Worst-Case $\Delta$ ($) | Active Option Activations | Inference Latency | Governance Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **A7 Incumbent** | Passive Default | $94,950.40 | +$0.00 | +$0.00 | 0 / 20 | 0.72 ms | Protected Incumbent |
| **P12 Candidate A: Search-Gated Options** | Exact Lookahead | **$102,177.60** | **+$7,227.20** | **+$0.00** | 10 / 20 | 48.60 ms | **Qualified (Oracle)** |
| **P12 Candidate B: Supervised Selector** | PyTorch MLP ($\tau=0.65$) | **$102,177.60** | **+$7,227.20** | **+$0.00** | 10 / 20 | **0.12 ms** | **Promoted (Production)** |
| **P12 Candidate C: PPO Selector** | Policy Gradient | $94,950.40 | +$0.00 | +$0.00 | 0 / 20 | 0.25 ms | **Discarded** |

---

## 3. Causal Post-Mortem: Why Continuous and Discrete RL Struggle on Kagriculture

1. **Severe Sparsity of Strategic Optima:**
   In an episode of 360 ticks, the optimal macro-economic intervention occurs exactly **once** (at Day 12, Step 288), unlocking Quadrant 4 when Bakery demand exists.
2. **Gradient Starvation in Policy Gradient Methods:**
   Because 359 out of 360 steps require strictly executing A7's route tape, the entropy regularization in PPO either drives exploratory actions that destroy worker choreography (as observed in RL-X2's continuous PPO collapse to $93.8k) or collapses to the zero-entropy absorbing state $a=0$ (as observed in P12-07).
3. **The Power of Supervised Distillation from Search:**
   Supervised classification directly minimizes cross-entropy against exact counterfactual oracle labels, bypassing gradient variance entirely. This allows Candidate B to learn the exact decision boundary in under 3 seconds of training with 100% precision.
