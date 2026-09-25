# V32 RL-X2 — REWARD FORMULATION & POTENTIAL SHAPING STUDY
**Phase:** V32 RL-X2  
**Date:** 2026-09-23  
**Status:** SPECIFIED, IMPLEMENTED & ANALYZED  
**Package:** `candidates/v32_rlx2/rewards.py`  
**Author:** Kagriculture Autonomous Research Agent  

---

## 1. Executive Summary & Problem Formulation (§35, §36, §37)

In Kagriculture's 720-step economic horizon, designing an effective reinforcement learning reward requires balancing:
1. **Goal Alignment:** The ultimate tournament metric is final cash at Step 719.
2. **Variance Reduction:** Raw terminal cash varies wildly across random seeds (from $50,000 to $175,000) solely due to initial shop sequences, creating massive environmental variance unrelated to agent decisions.
3. **Credit Assignment:** Mid-game decisions (e.g. planting melon seeds at Step 288 or buying a cow at Step 360) do not yield cash until many tens of steps later.

To rigorously address these challenges, RL-X2 investigates four distinct reward formulations.

---

## 2. Mathematical Reward Formulations

### 2.1 Formulation R0: Raw Terminal Cash
$$R_0(s_t, a_t) = \begin{cases} \frac{\text{Cash}(s_T)}{100,000.0} & \text{if } t = T \\ 0.0 & \text{if } t < T \end{cases}$$
- **Characteristics:** Completely unshaped; pure tournament objective.
- **Limitation:** Extremely sparse (non-zero only at $t=719$). GAE with $\gamma=0.99, \lambda=0.95$ helps, but variance remains dominated by seed difficulty.

### 2.2 Formulation R1: A7-Relative Paired Terminal Delta (Primary Hypothesis)
$$R_1(s_t, a_t) = \begin{cases} \frac{\text{Cash}(s_T) - \text{Cash}_{A7}(s_T)}{10,000.0} & \text{if } t = T \\ 0.0 & \text{if } t < T \end{cases}$$
- **Characteristics:** Uses the protected incumbent A7 as a Common Random Number (CRN) control variate.
- **Advantages:** Eliminates cross-seed macroeconomic noise. If a seed is inherently low-scoring ($59,000) or high-scoring ($145,000), A7 establishes the baseline. The learner receives positive reward **if and only if** its strategic deviation out-earned A7.

### 2.3 Formulation R2: Opponent-Relative Win Margin
$$R_2(s_t, a_t) = \begin{cases} \frac{\text{Cash}(s_T) - \text{Cash}_{\text{opp}}(s_T)}{10,000.0} & \text{if } t = T \\ 0.0 & \text{if } t < T \end{cases}$$
- **Characteristics:** Directly optimizes head-to-head match margin.
- **Limitation:** Susceptible to opponent-specific exploits (e.g. running up margin against passive or suicidal dumpers while ignoring conservative play vs A7/Dmitrii).

### 2.4 Formulation R3: Potential-Based Intermediate Economic Shaping
Following Ng, Harada & Russell (1999), potential-based shaping preserves the optimal policy $\pi^*$ while providing dense intermediate feedback:

$$R_3(s_t, a_t, s_{t+1}) = \gamma \Phi(s_{t+1}) - \Phi(s_t) + R_1(s_t, a_t)$$

The economic potential function $\Phi(s)$ estimates total unrealized farm net worth:
$$\Phi(s) = \frac{\text{Cash} + \text{LiquidShedVal} + \text{PlantedCropVal} + \text{LivestockVal}}{100,000.0}$$
where:
- $\text{PlantedCropVal} = \sum_{\text{crops}} N_{\text{planted}} \times \$30.00$
- $\text{LivestockVal} = N_{\text{cow}} \times \$600 + N_{\text{sheep}} \times \$500 + N_{\text{goose}} \times \$300$

---

## 3. Comparative Evaluation & Hypotheses

| Formulation | Dense/Sparse | Seed Variance | Opponent Invariance | Policy Invariance | Recommended Use |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **R0** | Sparse | Extreme ($> \$100\text{k}$) | High | Strict | Unbiased baseline benchmark |
| **R1** | Sparse | **Minimal** ($< \$5\text{k}$) | High | Strict | **Highest-priority default for PPO** |
| **R2** | Sparse | High | Low | Shifted | League fine-tuning only |
| **R3** | **Dense** | Low | High | Proven ($Ng \, 1999$) | Early sample-efficient training |

**Conclusion:** Formulation **R1** is adopted as the primary optimization objective for RL-X2 because it directly isolates strategic alpha over A7 with minimal environmental variance.
