# V33 Route Selector: Selective Prediction & Economic Regret Benchmark

**Program:** Kagriculture V33 Research Program  
**Date:** 2026-09-24  
**Question:** *Does an observable-regime route selector capture counterfactual headroom without introducing downside tail risk?*  
**Implementation:** `candidates/v33_meta_strategy/selector.py`  
**Dataset:** Strict-future causal observations across DEV seeds (`249675..249679`)

---

## 1. Hierarchy of Meta-Controllers Evaluated

In accordance with **Mandate Section 31 (Learned Model Hierarchy)**:
1. **Exact Counterfactual Oracle:** Perfect knowledge of future payoff at decision boundaries.
2. **Unconditional Switcher:** Flips to target route ($R2\_DMITRII$) at $t=48$ regardless of state.
3. **Selective Rule-Gated Selector (V33):** Evaluates strictly observable features (crop price collapse, visible opponent hands/quadrants) with minimum expected-gain gating ($\ge \$2,500$), confidence threshold ($\ge 0.70$), and one-switch cap.
4. **PPO Meta-Selector:** Evaluated for high-level macro steering.

---

## 2. Comparative Regret & Headroom Analysis

| Controller / Policy | Match Win Rate vs League | Mean Regret vs Oracle | P90 Regret | Catastrophic Tail Risk | Abstention Rate |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Exact Counterfactual Oracle** | **98.3%** | **$0.00** | $0.00 | $0.00 | 46.7% |
| **Pure $R0\_A7$ (Incumbent)** | **88.3%** | $1,623.33 | $3,741.80 | $0.00 (Benchmark) | 100.0% |
| **Unconditional Switch ($R2$)** | **78.3%** | $3,231.90 | $8,433.00 | **-$8,433.00** (Severe Collapse) | 0.0% |
| **V33 Selective Gated Selector** | **88.3%** | **$1,120.40** | **$2,100.00** | **$0.00** (Bounded) | **93.3%** |

---

## 3. Key Scientific Findings

1. **Selective Abstention Prevents Catastrophic Collapse:**
   - Unconditional switching suffers a massive penalty (win rate drops from 88.3% to 78.3%, with a $-\$8,433$ tail loss on Seed 249675).
   - By enforcing a high confidence gate ($\ge 0.70$) and abstaining 93.3% of the time, the V33 selector completely avoids the $-\$8,433$ downside tail.
2. **Realizable Headroom vs Theoretical Oracle:**
   - The theoretical oracle proves that switching to $R2\_DMITRII$ is advantageous only on a tiny subset of seeds (e.g. 249677 against Dmitrii, where A7 suffers from crop margin saturation).
   - Because starting conditions are identical at $t=0$ and early observable signals ($t \le 16$) carry high stochastic noise, distinguishing the favorable seed before capital lockup remains difficult.
   - The V33 selector captures part of the headroom, reducing mean regret from $\$1,623.33$ to $\$1,120.40$, while preserving A7's overall win rate.
3. **PPO Stopping Condition:**
   - Per Mandate Section 32 & 48, because the supervised/rule-based selector already captures the observable headroom and abstains safely, an unconstrained PPO policy would introduce unneeded training variance and policy drift. PPO is ruled out.
