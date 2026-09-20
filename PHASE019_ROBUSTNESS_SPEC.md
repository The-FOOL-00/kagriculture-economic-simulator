# PHASE019 ROBUSTNESS SPECIFICATION

**Phase**: PHASE019 — Uncertainty-Aware Commit Selection & Robust Economic Decision Audit  
**Date**: 2026-09-20  
**Authority**: Preregistered Diagnostic Robustness & Perturbation Engine Specification

---

## 1. Core Principle & Governance

> [!CAUTION]
> **No Manufactured Probabilities**: The counterfactual simulator is largely deterministic. A single simulation trajectory does NOT provide an empirical probability distribution. Uncalibrated statements such as $P(\text{win}) = 0.73$ or "82% confidence" are strictly prohibited.
> 
> Robustness in Phase019 is defined as **deterministic sensitivity across a preregistered neighborhood of actions, timings, and alternatives**.

---

## 2. Diagnostic Perturbation Neighborhood (§12)

For any committed tranche action $A = (\text{SELL}, \text{commodity}, q)$ at step $t$:

### 2.1 Quantity Perturbations
Where legally admissible within the current shed inventory:
1. $q - 1$ (if $q > 1$)
2. $q$ (central committed action)
3. $q + 1$ (if $q < \text{inventory}$)

### 2.2 Timing Perturbations
1. $t$ (execution at the current turn)
2. $t + 1$ (execution delayed by 1 turn: pass at $t$, order at $t+1$)
3. $t + 2$ (execution delayed by 2 turns)

### 2.3 Composition Alternatives
1. Tranche alone (pure isolated market intervention)
2. Tranche combined with existing baseline market orders
3. Pure baseline continuation ($\Delta = \$0.0$)

---

## 3. Robustness Vector Definition (§13)

For each candidate, the evaluator computes the deterministic vector:

$$\mathbf{v} = \begin{bmatrix}
\text{local\_delta} \\
\text{long\_horizon\_delta} \\
\text{min\_neighbor\_delta} \\
\text{median\_neighbor\_delta} \\
\text{max\_neighbor\_delta} \\
\text{sign\_stability} \\
\text{quantity\_sensitivity} \\
\text{timing\_sensitivity} \\
\text{macro\_boundary\_distance} \\
\text{safety\_margin} \\
\text{foundation\_relative\_delta} \\
\text{runner\_up\_gap}
\end{bmatrix}$$

- **`local_delta`**: Immediate turn effect $cand\_money_0 - base\_money_0$.
- **`long_horizon_delta`**: Terminal wealth margin delta $\Delta_{\text{committed}}$ across the adaptive counterfactual horizon.
- **`min_neighbor_delta`**: $\min_{p \in \mathcal{N}} \Delta_p$.
- **`median_neighbor_delta`**: $\text{median}_{p \in \mathcal{N}} \Delta_p$.
- **`max_neighbor_delta`**: $\max_{p \in \mathcal{N}} \Delta_p$.
- **`sign_stability`**: $\mathbf{1}_{\{\min_{p \in \mathcal{N}} \Delta_p > 0\}}$.
- **`quantity_sensitivity`**: $\frac{|\Delta(q+1) - \Delta(q-1)|}{2}$.
- **`timing_sensitivity`**: $\max_{k \in \{0, 1, 2\}} \Delta(t+k) - \min_{k \in \{0, 1, 2\}} \Delta(t+k)$.
- **`macro_boundary_distance`**: Distance in turns to next macro transition / end of day.
- **`safety_margin`**: $\Delta_{\text{committed}} - \$15.0$ (hurdle clearance).
- **`foundation_relative_delta`**: $\Delta_{\text{committed}} - \Delta_{\text{foundation}}$.
- **`runner_up_gap`**: $\Delta_{\text{committed}} - \Delta_{\text{runner\_up}}$.

---

## 4. Deterministic Robustness Categories (§14)

Candidates are partitioned into mutually exclusive categories evaluated in strict hierarchy:

| Category | Definition | Actionable Interpretation |
| :--- | :--- | :--- |
| **R5 — Clearly Negative** | $\Delta_{\text{committed}} \le \$0.0$ | Gross economic regression; immediate abstention. |
| **R3 — Ranking-Dependent** | $\Delta_{\text{foundation}} - \Delta_{\text{committed}} > \$5.0$ OR $\Delta_{\text{alt}} - \Delta_{\text{committed}} > \$15.0$ | Commit is an artifact of bad candidate ranking/displacement. |
| **R4 — Macro-Sensitive** | Macro-escalated AND $\Delta_{\text{continuation}} < -\$50.0$ | Long-horizon macro regime collapse outweighs immediate gain. |
| **R1 — Sensitive Positive** | $\Delta_{\text{committed}} > \$0.0$ BUT $\min_{p \in \mathcal{N}} \Delta_p \le \$0.0$ | Positive point estimate, but fragile under neighboring perturbations. |
| **R2 — Marginal** | $\Delta_{\text{committed}} \in (\$0.0, \$15.0]$ OR $\text{safety\_margin} \le \$5.0$ | Barely clears hurdle; sensitive to minor noise. |
| **R0 — Robustly Positive** | $\Delta_{\text{committed}} > \$15.0$ AND $\min_{p \in \mathcal{N}} \Delta_p > \$0.0$ | Stable, strictly positive across the entire neighborhood. |

---

## 5. Regret Metrics (§10)

1. **Selection Regret**:
   $$\text{selection\_regret} = \max\left(0, \Delta_{\text{best\_admissible\_alt}} - \Delta_{\text{committed}}\right)$$
2. **Abstention Regret**:
   $$\text{abstention\_regret} = \max\left(0, \Delta_{\text{baseline}} - \Delta_{\text{committed}}\right) = \max\left(0, -\Delta_{\text{committed}}\right)$$
3. **Foundation Opportunity Cost**:
   $$\text{foundation\_opportunity\_cost} = \Delta_{\text{foundation}} - \Delta_{\text{committed}}$$

---

## 6. Safety & Isolation Guarantee

The shadow evaluation engine:
- Operates strictly in detached `ShadowRolloutState`.
- Restores V3 internal state byte-for-byte before and after every shadow rollout.
- Emits results only to telemetry (`AECTelemetry.shadow_records`).
- Does NOT alter the action emitted by `AECExecutor.act()` during observational arms (U0/U1).
