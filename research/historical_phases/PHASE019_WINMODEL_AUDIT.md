# PHASE019 WINMODEL AUDIT

**Phase**: PHASE019 — Uncertainty-Aware Commit Selection & Robust Economic Decision Audit  
**Date**: 2026-09-20  
**Target Component**: `aec/evaluation/win_model.py` (`WinModel`, `estimate_p_win`, `evaluate`)

---

## 1. Executive Summary

The WinModel in `aec/evaluation/win_model.py` was designed to implement the AEC lexicographic hierarchy and provide an uncalibrated ranking score (`expected_p_win`). A forensic audit of its mathematical properties and operational usage reveals several critical structural behaviors:

1. **Strict Monotonicity & Point-Estimate Dominance**:
   `estimate_p_win(current_gap, margin_delta)` is a monotonic logistic function:
   $$S(\Delta) = \frac{1}{1 + e^{-(\text{gap} + \Delta) / 1000}}$$
   Because `gap` is identical across all candidates in a turn, ranking candidates by $S(\Delta)$ is **mathematically identical to ranking candidates by single-point $\Delta_{\text{terminal\_margin}}$**.
2. **Zero-Spread Winner Selection**:
   The model commits the candidate with the highest point estimate, even if its advantage over runner-ups is within numerical noise ($+\$0.10$).
3. **Absence of Downside / Variance Weighting**:
   The WinModel possesses zero awareness of candidate variance, perturbation sensitivity, or downside tail risk. A candidate with point estimate $+\$50.0$ and worst-case neighbor $-\$500.0$ will strictly beat a candidate with point estimate $+\$40.0$ and worst-case neighbor $+\$35.0$.

---

## 2. Seven Diagnostic Questions (§26)

### Q1: Is the WinModel objective consistent with the established economic hierarchy?
**Partially.** The economic hierarchy specifies:
1. Legal feasibility & feed security (hard safety gate).
2. Damage avoidance / solvency preservation.
3. Terminal wealth margin dominance.
4. Lead preservation.

The safety checker enforces step 1. However, at step 3, the WinModel relies on a single deterministic forward trajectory. If that trajectory over-optimistically assumes continuation actions that diverge from reality, the candidate appears accretive when it is actually catastrophic.

### Q2: Is its output dominated by a small terminal-margin difference?
**Yes.** Because greedy selection uses `eval_res.expected_p_win > best_eval_result.expected_p_win`, an infinitesimal margin difference ($\Delta_A - \Delta_B = +\$0.01$) guarantees replacement. In multi-candidate evaluations (as seen in Arm B2), this induces the classical **Winner's Curse**: the maximum of multiple noisy evaluations is systematically biased upward.

### Q3: Does it favor risky high-upside candidates over robust alternatives?
**Yes.** Tranche orders that liquidate substantial crop inventory show large immediate cash gains and positive margin deltas in the counterfactual simulation (which liquidates terminal shed at market price). If this sale later deprives livestock of feed or town cycles of working capital beyond the CF horizon, the WinModel cannot see the downstream penalty and selects the high-upside fragile tranche.

### Q4: Does it penalize small positive but robust candidates?
**Yes.** The $\$15$ hurdle rejects any candidate with $\Delta \in (\$0.0, \$15.0]$. In Phase018 Arm B, boundary-safe tranches designed to avoid inventory depletion produced consistent $+ \$7.0$ to $+\$12.0$ edges, all of which were rejected by the hurdle.

### Q5: Is the $15 hurdle being applied at the correct point?
**Audit finding:** The hurdle is currently applied in `win_model.py` lines 345–353 as a step-function gate:
```python
elif outcome.delta_terminal_margin > 15.0:
    is_superior = True
```
This correctly filters sub-hurdle noise for speculative actions. However, applying the *same* hurdle uniformly to all actions regardless of mechanism type creates asymmetry: a speculative tranche sale needs $>\$15$, but once above $\$15$, it faces no robustness checks.

### Q6: Does candidate ranking accidentally mix incomparable quantities?
**Yes.** Candidates can have different adaptive horizons (e.g. Market Timing horizon = 6 steps; Tranche horizon = 20–36 steps). Comparing the undiscounted terminal delta of an intervention evaluated over 6 steps directly against one evaluated over 36 steps compares wealth outcomes across different temporal endpoints without annualized or step-normalized discounting.

### Q7: Is candidate selection using a proxy where exact terminal delta is available?
**Yes.** `expected_p_win` is an uncalibrated sigmoid proxy. Computing the sigmoid adds no information beyond sorting directly on `delta_terminal_margin`, while introducing non-linear scaling that compresses large margin differences when far ahead or far behind.

---

## 3. Scientific Recommendation

1. Retain the $\$15$ hurdle to filter background simulation noise.
2. Replace blind point-estimate greedy selection with **neighborhood-aware robustness gating**:
   A candidate must not only clear $\Delta > \$15.0$, but must also satisfy **perturbation sign stability** ($\min_{p \in \mathcal{N}} \Delta_p > \$0.0$) before committing.
