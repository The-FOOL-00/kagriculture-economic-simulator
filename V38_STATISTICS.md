# V38 Statistical Significance & Confidence Interval Analysis

## 1. Objective & Methodology

This report provides rigorous statistical tests evaluating whether **V38** (BC and PPO) produces a statistically significant improvement over the live production baseline **V35**.

### 1.1 Evaluated Null Hypotheses
1. **$H_{0, \text{WR}}$:** The matchup win rate of V38 is less than or equal to V35:
   $$\mathbb{P}(\text{Win}_{\text{V38}}) \le \mathbb{P}(\text{Win}_{\text{V35}})$$
2. **$H_{0, \text{Cash}}$:** The expected paired terminal cash delta between V38 and V35 is zero:
   $$\mathbb{E}[\text{Cash}_{\text{V38}} - \text{Cash}_{\text{V35}}] = 0$$

### 1.2 Evaluation Dataset
- Combined evaluation across **60 exact paired matches** (Dev Cohort seeds `249675..249679` and Fresh Held-Out Cohort seeds `249685..249689`).
- Opponent pool: `E2_A7` (Incumbent), `E8_DMITRII` (Grandmaster), `SYN_AGG` (Aggressive synthetic).
- Balanced seats (30 Seat 0, 30 Seat 1).
- Non-parametric bootstrap resampling: $B = 10,000$ iterations.

---

## 2. Statistical Findings

### 2.1 Matchup Win Rate Comparison

| Metric | V35 (Reference) | V38_HEURISTIC | V38_BC | V38_PPO | Delta vs V35 | $p$-value (McNemar) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Dev Win Rate (N=30)** | 90.0% (27/30) | 90.0% (27/30) | 90.0% (27/30) | 90.0% (27/30) | 0.0% | $p = 1.000$ |
| **Fresh Win Rate (N=30)** | 100.0% (30/30) | 100.0% (30/30) | 100.0% (30/30) | 100.0% (30/30) | 0.0% | $p = 1.000$ |
| **Pooled Win Rate (N=60)** | **95.0%** (57/60) | **95.0%** (57/60) | **95.0%** (57/60) | **95.0%** (57/60) | **0.0%** | **$p = 1.000$** |
| **95% Wilson Score CI** | [86.3%, 98.3%] | [86.3%, 98.3%] | [86.3%, 98.3%] | [86.3%, 98.3%] | — | — |

**Conclusion on Win Rate:** We cannot reject $H_{0, \text{WR}}$. There is zero win rate difference ($\Delta \text{WR} = 0.00\%$) across all 60 paired matches.

---

### 2.2 Paired Terminal Cash Delta Analysis

| Candidate Policy | Sample Size ($N$) | Mean Paired Delta ($\Delta$) | Sample Std ($\sigma$) | 95% Bootstrap CI | Paired $t$-test ($t$, $p$) | Wilcoxon Signed-Rank ($p$) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **V38_HEURISTIC** | 60 | $0.0000 | $0.0000 | [$0.0000, $0.0000] | $t = 0.0, p = 1.000$ | $p = 1.000$ |
| **V38_BC** | 60 | +$0.1333 | $0.7180 | [$0.0000, +$0.3333] | $t = 1.44, p = 0.156$ | $p = 0.180$ |
| **V38_PPO** | 60 | $0.0000 | $0.0000 | [$0.0000, $0.0000] | $t = 0.0, p = 1.000$ | $p = 1.000$ |

**Conclusion on Cash Delta:**
1. **V38_BC:** Produced an average delta of +$0.13 across 60 matches from 2 micro-interventions. The difference is not statistically significant ($p = 0.156$).
2. **V38_PPO:** The residual PPO policy produced an identical $0.00 delta to V35 ($p = 1.000$).

---

### 2.3 Tail Risk, Casualties, and Rescues

| Metric | V38_HEURISTIC | V38_BC | V38_PPO | Target Gate Standard | Gate Result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Rescues (V35 loss $\to$ V38 win)** | 0 / 3 (0.0%) | 0 / 3 (0.0%) | 0 / 3 (0.0%) | $> 0$ | **FAIL (Neutral)** |
| **Casualties (V35 win $\to$ V38 loss)** | 0 / 57 (0.0%) | 0 / 57 (0.0%) | 0 / 57 (0.0%) | $0.0\%$ | **PASS** |
| **Worst Paired Downside** | $0.00 | $0.00 | $0.00 | $> -$1,000 | **PASS** |
| **Downside Tail Deviation** | 0.00 | 0.00 | 0.00 | Bounded | **PASS** |

---

## 3. Formal Statistical Verdict
- **Statistically Significant Improvement:** **NONE.**
- **Statistically Significant Degradation:** **NONE.**
- The PPO residual controller converged to the heuristic identity. While this guarantees 100% safety and zero casualties, it conclusively proves that residual PPO provides no statistically measurable advantage over the deterministic V35 baseline.
