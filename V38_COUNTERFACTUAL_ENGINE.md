# V38 Forward Value Model and Counterfactual Engine Specification

**Document ID:** `V38_COUNTERFACTUAL_ENGINE.md`  
**Date:** 2026-09-25  
**Candidate:** `candidates/v38_heuristic_ppo/`  
**Author:** Kagriculture Autonomous Research Agent  

---

## 1. Role in the V38 Architecture

The counterfactual rollout engine is the **ground-truth validation mechanism** of V38:
1. It replaces subjective or heuristic guesses about whether a strategic decision is good with exact forward simulation.
2. It generates supervisory training data for Behavioral Cloning and reward labels for residual PPO.
3. It evaluates whether proposed neural policy interventions actually cause terminal cash improvements over V35 ($C_T(a) - C_T(\text{V35}) > 0$) across matched random seeds and opponent matchups.

---

## 2. Mathematical Formulation of Counterfactual Search

Let $s_t$ be a decision state at step $t \in [0, 718]$.
Let $\pi_{\text{expert}}$ be the frozen V38 deterministic expert heuristic.
For any candidate macro option $a \in \mathcal{A}_{\text{macro}}$ with horizon $H \in \{4, 8, 12\}$:

1. **Intervention Window ($t \le \tau < t + H$):**
   The executor applies the bounded macro option $a$ on top of observation $s_\tau$.
2. **Resumption Window ($t + H \le \tau < 719$):**
   Control returns unconditionally to $\pi_{\text{expert}}$ for the remainder of the episode.
3. **Terminal Evaluation ($\tau = 719$):**
   The environment evaluates final rewards:
   $$\hat{V}_H(s_t, a) = C_{719}(a)$$
4. **Counterfactual Advantage:**
   $$\hat{A}_H(s_t, a) = \hat{V}_H(s_t, a) - \hat{V}_H(s_t, \pi_{\text{expert}})$$

---

## 3. Horizon Sensitivity: $H = 4$ vs $H = 8$ vs $H = 12$

To measure whether longer horizons add predictive power without destabilizing physical routing, the engine supports parameterized horizons:

* **$H = 4$ (Default):** Coincides with the 4-tick town consumption cycle ($step \equiv 0 \pmod 4$). Minimizes physical drift ($D_{\text{phys}} \le 2$ tiles) and allows rapid recovery to expert choreography.
* **$H = 8$:** Spans 1/3 of a day. Useful for multi-step capital reallocation (e.g. land purchase followed by seed planting).
* **$H = 12$:** Half-day horizon. Evaluated only when $H=4$ indicates positive derivative but requires longer execution to manifest yield.

---

## 4. State Coherence and Cloned Simulation Invariants

1. **Non-Destructive Simulation:** Simulations are executed on independent environment instances (`kaggle_environments.make("kaggriculture")`), never mutating live episodes.
2. **Identical Opponent Protocol:** In paired rollouts, the opponent executes bit-identical moves under both the candidate branch and the baseline branch.
3. **Deterministic Reset:** Random seeds are preserved exactly, guaranteeing that weather, prices, and initial tiles remain identical across paired comparisons.
