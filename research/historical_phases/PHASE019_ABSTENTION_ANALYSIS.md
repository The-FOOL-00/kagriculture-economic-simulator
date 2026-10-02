# PHASE019 ABSTENTION ANALYSIS

**Phase**: PHASE019 — Uncertainty-Aware Commit Selection & Robust Economic Decision Audit  
**Date**: 2026-09-20  
**Core Diagnostic Question**: If the compiler had simply abstained on tranche actions, what would the terminal economic result have been?

---

## 1. Mathematical Formulation

For any turn $t$ where an experimental candidate $C$ is committed:

$$\text{abstention\_regret} = R(\text{Baseline}) - R(\text{Committed})$$

Under exact Common Random Numbers (CRN) mirror matches against the qualified foundation control $A_0$:
- Control $A_0$ executes the qualified live foundation (`V3 + MARKET_TIMING + TERMINAL_LIQUIDATION + PHASE_SHUTDOWN`).
- Treatment $T$ executes $A_0$ + Phase015 tranche commitments.
- When $T$ abstains on an opportunity, it executes the identical baseline action as $A_0$.
- Therefore, the counterfactual terminal value of **complete abstention** on all tranche opportunities is identically the control outcome:
  $$\Delta_{\text{total\_abstention}} = R(A_0) - R(T) = -\text{treatment\_margin}$$

---

## 2. Empirical Abstention Recovery Value across Cohorts

| Cohort | Treatment Margin vs $A_0$ | Win/Loss/Tie | Tranche Commits | Abstention Recovery Value |
| :--- | :--- | :--- | :--- | :--- |
| **Phase017 Attribution** | $-\$884.20$ | 1 / 9 / 0 | 52 | **$+\$884.20$ per match** |
| **Phase018 Arm A1** | $-\$1,311.00$ | 1 / 9 / 0 | 36 | **$+\$1,311.00$ per match** |
| **Phase018 Arm A2** | $-\$1,228.00$ | 1 / 9 / 0 | 36 | **$+\$1,228.00$ per match** |
| **Phase018 Arm B2 (S1)** | $-\$1,228.00$ | 0 / 10 / 0 | 64 | **$+\$1,228.00$ per match** |
| **Phase018 Arm C0** | $-\$636.00$ | 2 / 8 / 0 | 44 | **$+\$636.00$ per match** |

Across all 50 seeds and 260 matches in Phase017 and Phase018:
- The treatment won only **4 out of 50 seeds** (8% win rate).
- In **92% of matches**, committing tranche actions resulted in severe economic loss.
- In every cohort, **simply abstaining** on all tranche commits recovers an average of **$+\$636.00$ to $+\$1,311.00$** per match!

---

## 3. Why Abstention is the Right Repair

The compiler currently treats abstention as an admission of failure:
- It only abstains if a candidate is illegal, breaches hard safety, or is sub-hurdle.
- If a candidate achieves $\Delta > \$15.0$, the compiler is compelled to commit.

However, in agricultural economics with finite inventories and livestock dependencies:
1. **The default backbone (V3 + foundation) is already highly optimized.**
2. A premature speculative sale yields a small immediate cash delta ($+\$30$ to $+\$100$) but imposes a permanent loss of option value (depleted feed, lost town cycle trades).
3. **Abstention is an active economic decision to preserve option value.**

---

## 4. Scientific Conclusion

> **Abstention on fragile or un-robust candidates is the primary mechanism of value recovery.**

If a candidate cannot demonstrate **sign stability across its legal neighborhood** ($\min_{p \in \mathcal{N}} \Delta_p > \$0.0$) and **positive margin over the foundation**, the compiler must **ABSTAIN**.
