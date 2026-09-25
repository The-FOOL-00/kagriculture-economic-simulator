# V38 Reward Formulation and Objective Design

**Document ID:** `V38_REWARD_DESIGN.md`  
**Date:** 2026-09-25  
**Candidate:** `candidates/v38_heuristic_ppo/`  
**Author:** Kagriculture Autonomous Research Agent  

---

## 1. Primary Competition Objective vs Secondary Diagnostic Metric

### Primary Competition Win Condition
In the Kagriculture competition tournament, the win condition between player $p$ and opponent $1-p$ is strictly:
$$\text{Win}(p) = \mathbb{I}\left(C_T(p) > C_T(1-p)\right) + 0.5 \cdot \mathbb{I}\left(C_T(p) = C_T(1-p)\right)$$
where $C_T$ is the liquid cash at terminal step $T = 719$.

The primary competition objective is:
$$\max_\theta \mathbb{E}_{\text{seed}, \text{seat}, \text{opp}} \left[ \text{Win}(p; \theta) \right]$$

### Secondary Diagnostic Objective
Terminal cash:
$$\max_\theta \mathbb{E} \left[ C_T(p; \theta) \right]$$

### Prohibited Artificial Targets
We do **not** use arbitrary scalar targets such as "reach $200k" or "reach $300k". In tournament play, scoring $110k against an opponent who made $95k is a 100% win, whereas scoring $220k against an opponent who made $230k is a 0% loss. Optimization must always remain anchored to matchup dominance and marginal cash advantage.

---

## 2. Theoretical Analysis of Candidate Training Rewards

We formulate and analyze four candidate training reward functions:

### Reward Formulation A: Sparse Terminal Cash
$$R_{\text{sparse}} = C_T$$
* **Pros:** Unbiased representation of final score.
* **Cons:** Complete lack of intermediate learning signal over 720 game steps. Extreme credit assignment variance; PPO gradients fail to distinguish which of the 180 macro decisions caused the final win or loss.

### Reward Formulation B: Differential Terminal vs Production Benchmark (V35)
$$R_{\text{diff}} = C_T(\text{V38}) - C_T(\text{V35})$$
* **Pros:** Directly penalizes any drop below V35. If V38 deviates and produces less cash than V35, $R_{\text{diff}} < 0$. If it finds positive alpha, $R_{\text{diff}} > 0$.
* **Cons:** Still sparse (evaluated only at step 719). Requires running a paired V35 baseline rollout for every episode.

### Reward Formulation C: Dense Shaped Observable Economic Value
Using potential-based reward shaping $\Phi(s)$ based strictly on legal observable features:
$$\Phi(s) = C_t + V_{\text{inventory}}(s) + V_{\text{productive\_assets}}(s) - W_{\text{committed}}(s) - \text{Pen}_{\text{liquidity\_risk}}(s)$$
where:
* $C_t$: current liquid cash.
* $V_{\text{inventory}}(s) = \sum_{i} \text{shed}_i \cdot \min(P_{\text{spot}, i}, \bar{P}_i)$: conservative liquidation value.
* $V_{\text{productive\_assets}}(s) = 400 \cdot N_{\text{cow}} + 500 \cdot N_{\text{sheep}} + 300 \cdot N_{\text{goose}} + \sum_{\text{plants}} \text{discounted\_yield}$.
* $W_{\text{committed}}(s)$: upcoming wage liabilities for the current labor force.
* $\text{Pen}_{\text{liquidity\_risk}}(s) = \alpha \cdot \max(0, C_{\text{safe}} - C_t)$: sharp penalty for breaching the safety cash floor.

Step reward:
$$r_t = \Phi(s_{t+1}) - \Phi(s_t)$$
* **Pros:** Dense per-step feedback at every decision tick.
* **Cons:** Risk of potential misalignment. For example, buying animals increases asset value on paper but incurs irreversible daily feed and wage costs that can depress terminal cash if liquidity is stressed.

### Reward Formulation D: Counterfactual Macro Advantage
At macro decision step $t$, given state $s_t$:
$$r_t(a_t) = \hat{V}_H(s_t, a_t) - \hat{V}_H(s_t, a_{\text{heuristic}})$$
where $\hat{V}_H(s_t, a)$ is the projected terminal outcome evaluated by executing action $a$ for $H$ steps and then executing the safe heuristic for steps $t+H \dots T$.
* **Mathematical Properties:**
  1. **Zero-Bias at Heuristic:** When $a_t = \text{TRUST\_HEURISTIC}$, $r_t = 0.0$ by definition.
  2. **Direct Alpha Quantification:** $r_t > 0$ if and only if macro option $a_t$ causes an improvement over following the heuristic.
  3. **Natural Regularization:** Discourages spurious deviations; the agent only deviates when expected counterfactual alpha strictly exceeds zero.

---

## 3. Comparative Reward Matrix

| Dimension | Reward A (Sparse) | Reward B (Differential) | Reward C (Dense Shaped) | Reward D (Counterfactual Advantage) |
| :--- | :---: | :---: | :---: | :---: |
| **Credit Assignment** | Very Poor | Poor | Good | **Excellent** |
| **Correlation with True Win Rate** | Moderate | High | Moderate (misalignment risk) | **Highest** |
| **Resistance to Reward Hacking** | High | High | Low | **High** |
| **Exploration Guidance** | None | Low | High | **High** |
| **Computational Overhead** | Lowest | Moderate (2 rollouts) | Low | High (requires $H$-lookahead) |

---

## 4. V38 Hybrid Training Reward Protocol

Based on the theoretical and empirical comparison, V38 adopts a **two-tiered hybrid reward protocol**:

1. **For Behavioral Cloning & Counterfactual Dataset Generation:**
   Target macro labels are assigned strictly using **Reward D (Counterfactual Advantage)**. Actions with $\hat{V}_H(s, a) - \hat{V}_H(s, a_{\text{heuristic}}) \le 0$ are assigned target label `0: TRUST_HEURISTIC`. Actions with strictly positive, statistically robust alpha ($\Delta > +\$50.0$) are labeled with the winning macro option.

2. **For Residual PPO Fine-Tuning:**
   $$R_t = r_{\text{counterfactual}}(s_t, a_t) + \lambda_{\text{terminal}} \cdot \mathbb{I}(t = T) \cdot \left[ C_T(\text{V38}) - C_T(\text{V35}) \right] - \lambda_{\text{risk}} \cdot \text{Violations}(s_t)$$
   where:
   * $\lambda_{\text{terminal}} = 0.001$: terminal bonus anchored to the true matchup delta.
   * $\lambda_{\text{risk}} = 10.0$: heavy penalty for any violation of the liquidity safety floor.
   * $r_{\text{counterfactual}}$: immediate reward reflecting simulated local gain.

This hybrid ensures that PPO receives immediate, dense gradient signals that are strictly aligned with outperforming the frozen production benchmark V35.
