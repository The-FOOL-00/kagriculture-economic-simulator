# V32 RL-X2 — STRATEGIC SEARCH DESIGN & COUNTERFACTUAL METHODOLOGY
**Phase:** V32 RL-X2  
**Date:** 2026-09-23  
**Status:** DESIGNED, IMPLEMENTED & VERIFIED  
**Package:** `candidates/v32_rlx2/search.py`  
**Author:** Kagriculture Autonomous Research Agent  

---

## 1. Motivation: Why Exact Search Matters (§20, §21)

In complex multi-agent economic games with 720 steps, model-free policy gradient RL (e.g. PPO from random initialization) suffers from severe credit assignment variance: an action taken at step 216 might not realize its cash return until a cow yields milk at step 360 and the milk is sold at step 432.

Because we possess the exact, bit-identical simulator (`kaggle_environments`), we do not need to rely solely on trial-and-error exploration. We can construct an exact counterfactual search engine that directly evaluates the long-horizon causal value of strategic macro deviations.

---

## 2. Mathematical Search Formulation (§22, §23)

For an observable state $s_t$ at turn $t$ and a candidate macro strategic action $a \in \mathcal{A}(s_t)$:

$$V(s_t, a) = \text{TerminalCash}\left(\text{Rollout}\left(s_t, \, a \xrightarrow{H=4} \text{resume } A7\right)\right)$$

### Properties:
1. **Local Strategic Intervention:** The candidate action $a$ is executed for a 4-step macro interval ($[t, t+4)$).
2. **Standardized Continuation:** At step $t+4$, the agent resumes the protected incumbent $A7$ strategy until the game terminates at step 719.
3. **Causal Attribution:** Because both the candidate branch and the baseline branch share the exact same history up to $t$ and the exact same continuation policy after $t+4$, the difference:
   $$\Delta(s_t, a) = V(s_t, a) - V(s_t, 0)$$
   is the **exact, unconfounded economic value** of deviating from A7 at state $s_t$.

---

## 3. Candidate Search Points (§32, §33)

Search targets are generated across high-leverage economic decision states on training cohort seeds (`249635`–`249674`):
1. **Shop Unlock Milestones:**
   - Step 72 (Day 3): Bakery / Dairy / Textile / Pet Cafe revealed.
   - Step 144 (Day 6): Second shop revealed.
   - Step 216 (Day 9): Third shop revealed.
2. **Crop Compounding Windows:**
   - Steps 288 (Day 12), 360 (Day 15), 432 (Day 18): Planting and harvest cycles.
3. **High-Volatility Market Events:**
   - Steps 504, 576, 614, 648, 696: Pre-terminal market price shifts, opponent dump points (e.g. Seed 249677 Dmitrii Melon/Milk dump).

---

## 4. Search Target Curation & Filtering (§24, §56)

A state $s_t$ is recorded as a **High-Consequence Strategic Target** if and only if:
1. **Positive Strategic Alpha:** $\Delta(s_t, \text{best}) > 0.0$ (a deviation strictly beats following A7).
2. **Material Strategic Gap:** $V(s_t, \text{best}) - V(s_t, \text{second}) \ge \$50.00$ (the decision genuinely matters; not an indifferent tie).

Targets meeting these criteria are stored in `reports/strategic_targets.jsonl` with full state vectors, action masks, action return distributions, and optimal intent labels.
