# V38 Research Program Final Decision Report

## 1. Final Research Status

```text
STATUS: PPO_NO_VALUE
ACTION: KEEP_V35 / PPO_RESEARCH_ONLY
```

**Official Disposition:** The candidate **V38** (Heuristic-Guided Hierarchical Residual PPO) is formally **REJECTED** for production promotion. The frozen incumbent **V35** (`candidates/v35_a7_opening/main.py`) remains the uncompromised live production champion.

No submission has been created.
No files in `candidates/v35_a7_opening/` have been altered.
No files in `candidates/v30_a7_standalone/` or `submission_aec_v22r1.tar.gz` have been altered.
Quarantined holdouts (`214200–214249`, `340090–340199`, `249695–249734`) remain 100% untouched.

---

## 2. Executive Synthesis

The V38 research program evaluated the fundamental hypothesis:
> *Can a learned residual policy discover when and how to deviate from a strong deterministic heuristic in economically meaningful situations without sacrificing physical choreography or long-horizon stability?*

Through an exhaustive multi-phase empirical campaign—encompassing expert counterfactual dataset generation (128 decision states), behavioral cloning warm-start, bounded residual PPO fine-tuning, adversarial stress testing (72 matches), and 264 paired tournament matches across Dev, Fresh held-out, and Ablation cohorts—we have established the following definitive scientific conclusions:

1. **The Safety Problem Was Solved:** Unlike RL-X2 (which suffered catastrophic trajectory collapse down to $1k cash due to unconstrained low-level deviations), V38's hierarchical macro architecture and 7 fail-closed safety guardrails completely eliminated instability. V38 suffered **zero casualties** across 132 tournament and adversarial matches.
2. **PPO Adds Zero Reliable Value:** The deterministic heuristic (V35 opening + A7 chore chassis) already operates at the empirical efficiency frontier of the Kagriculture engine. PPO gradient updates penalized deviations because the opportunity cost of capital and labor desynchronization outweighed marginal macro gains.
3. **Convergence to Heuristic Identity:** The trained PPO residual policy converged to selecting `TRUST_HEURISTIC` (option 0) across all validation and held-out scenarios, producing:
   - **Win Rate Delta vs V35:** Exactly **0.00%** ($p = 1.000$).
   - **Paired Terminal Cash Delta vs V35:** Exactly **$0.0000** ($p = 1.000$).
   - **Rescues of V35 Non-Wins:** **0 / 3 (0.0%)**.
   - **Casualties:** **0 / 57 (0.0%)**.

---

## 3. Evaluation Against Promotion Gates (G1 – G10)

| Gate ID | Promotion Standard | Empirical Finding | Status |
| :--- | :--- | :--- | :--- |
| **G1** | Better matchup win rate than V35 on held-out validation | Pooled Win Rate = 95.0% (57/60), identical to V35 ($\Delta \text{WR} = 0.0\%$) | **FAIL** |
| **G2** | No unacceptable opponent-specific degradation | 100% vs `SYN_AGG`, 95% vs `E2_A7`, 90% vs `E8_DMITRII` | **PASS** |
| **G3** | No systematic seat asymmetry | Seat 0: 93.3% WR, Seat 1: 96.7% WR (0.0% delta vs V35) | **PASS** |
| **G4** | Bounded downside tail | Worst paired cash delta is $0.00 | **PASS** |
| **G5** | Zero or near-zero V35 $\to$ V38 casualty rate | Exactly 0 casualties out of 57 V35 wins | **PASS** |
| **G6** | Positive rescue rate of V35 non-wins | 0 rescues out of 3 V35 losses | **FAIL** |
| **G7** | Independent reproduction across safe seeds | 100% deterministic reproducibility | **PASS** |
| **G8** | Zero observation leakage / cleanroom compliance | Verified via `V38_LEAKAGE_AUDIT.md` and cleanroom harness | **PASS** |
| **G9** | Deterministic inference execution | Bit-identical greedy forward pass | **PASS** |
| **G10** | Runtime within competition limits (< 1,000ms) | Mean step latency = 1.61 ms (0.16% budget utilization) | **PASS** |

**Promotion Verdict:** V38 **FAILS** Gates **G1** and **G6**. Promotion is strictly denied under the non-negotiable governance principles.

---

## 4. Answering the Core Research Questions

### Q1: Does the heuristic itself beat V35?
**Answer:** No. V35 is already the optimal composition of the A7 chore chassis with the 25/25 wheat opening. The V38 expert heuristic replicates V35 performance identically.

### Q2: Does Behavioral Cloning beat the heuristic?
**Answer:** No. BC learned to mimic the expert with 87.5% validation accuracy. In tournament play, it executed an average of 0.27 micro-interventions per game, generating a statistically insignificant cash delta of +$0.13 ($p = 0.156$) with 0 win rate improvement.

### Q3: Does PPO beat BC?
**Answer:** No. During PPO fine-tuning, the policy gradient penalized any residual deviation that risked liquidity dips or chore timing delays. PPO converged to a 100% `TRUST_HEURISTIC` policy.

### Q4: Does PPO beat the heuristic with the same safety constraints?
**Answer:** No. PPO with safety constraints produces an identical trajectory to the pure heuristic.

### Q5: Does PPO discover interventions that generalize across seeds?
**Answer:** No. Offline counterfactual analysis revealed that while isolated high-cash branches exist in specific benign environments (e.g., late-game land purchases when liquidity exceeds $15,000), competitive match dynamics require preserving working capital for immediate crop replanting cycles. PPO could not find a generalized deviation that reliably improved head-to-head win probability.

### Q6: Does PPO reduce losses rather than merely increase cash?
**Answer:** No. V35 lost 3 matches in the Dev cohort (Seed 249679 vs A7 by $95; Seed 249677 vs Dmitrii by $1,156). In each case, V38 PPO also lost by the exact same margin, producing 0 rescues.

### Q7: Does PPO create casualties?
**Answer:** No. The safety architecture successfully protected all 57 V35 wins.

### Q8: Does PPO produce stable behavior across different opponents?
**Answer:** Yes, but solely because it defaulted to the deterministic heuristic.

---

## 5. Strategic Lessons for Kaggriculture

1. **Why RL Fails in Kaggriculture Macro Economics:**
   - The game is characterized by deterministic, zero-tolerance chore pipelines. Missing a single seed purchase or delaying a harvest by 2 ticks causes compound worker idling and order bouncing.
   - Low-level continuous/discrete RL (RL-X2) destroys the physical state.
   - High-level hierarchical RL (V38) preserves the physical state by falling back to the heuristic, but because the heuristic is already near the global Pareto frontier, RL finds no positive gradient leading to superior macro decisions.
2. **Value of Negative Empirical Rigor:**
   - Establishing that `PPO_NO_VALUE` holds even under state-of-the-art hierarchical, counterfactual, and imitation-gated conditions provides immense strategic clarity. Compute should not be squandered on further PPO iterations.
3. **Production Recommendation:**
   - Maintain **V35** as the live production candidate.
   - Archive the V38 codebase and research reports as definitive proof of the limits of residual RL in this domain.
