# PHASE019 COMMIT REGRET ANALYSIS

**Phase**: PHASE019 — Uncertainty-Aware Commit Selection & Robust Economic Decision Audit  
**Date**: 2026-09-20  
**Evidence Base**: Historical telemetry from Phase017 attribution audit and Phase018 Arms A and B2.

---

## 1. Regret Formulation & Accounting

At any decision point $t$ where a candidate $C$ is committed:

$$\text{selection\_regret}(C) = \max\left(0, \max_{A \in \mathcal{A}_{\text{admissible}}} \Delta_A - \Delta_C\right)$$

$$\text{abstention\_regret}(C) = \max\left(0, \Delta_{\text{baseline}} - \Delta_C\right) = \max(0, -\Delta_C)$$

$$\text{foundation\_opportunity\_cost}(C) = \max_{F \in \mathcal{F}_{\text{admissible}}} \Delta_F - \Delta_C$$

---

## 2. Empirical Findings across Historical Cohorts

### 2.1 Cohort Repro / Phase017 Baseline (Seeds 249286..249295)
- **Total Commits**: 54 (52 Tranche, 2 Foundation).
- **Simulations per Commit Turn**: Exactly 1.0 (due to S7 dominance collapse).
- **Observed Selection Regret**: $\$0.0$ (vacuous: no alternatives were simulated).
- **Realized Outcome**: Mean paired delta $-\$884.20$.
- **Finding**: When evaluation breadth is 1, selection regret cannot be measured within-turn because alternatives are pruned prior to simulation.

### 2.2 Cohort Arm A (Seeds 249296..249305)
- **Total Commits**: 86 (72 Tranche, 14 Foundation).
- **Foundation Selection**: Under Arm A2 (reservation ON), 14 foundation commits were restored (mean paired effect $+\$49.30$).
- **Tranche Commits**: 36 in A1, 36 in A2.
- **Tranche Point Delta**: Mean $+89.1$, median $+60.0$.
- **Realized Outcome**: Every tranche-active treatment leg lost 8 or 9 out of 10 matches, with mean margin $-\$1,311.00$.

### 2.3 Cohort Arm B2 (Multi-Simulation Enabled, Seeds 249316..249325)
- **Total Commits**: 205 (187 Tranche, 18 Foundation).
- **Simulations per Commit Turn**: Up to 8 candidates simulated simultaneously (1,551 multi-sim turns).
- **Committed Delta**:
  - Mean: $+\$137.40$
  - Median: $+\$50.00$
  - Range: $\$0.00$ to $+\$2,320.00$
- **Within-Turn Selection Regret**:
  - In 97.1% of commit turns, the committed candidate had the highest point estimate among simulated candidates.
  - In 2.9% of commit turns (6 turns), an alternative had a higher point estimate but failed a safety check or was quarantined.
- **The Core Paradox**:
  Every committed candidate had a **positive simulated point estimate**, yet the realized games experienced massive negative terminal deltas ($-\$1,228.00$).

---

## 3. The Source of Regret: Downside Fragility vs Point Optimism

Why does a candidate with simulated delta $+ \$50.0$ cause a game loss?

1. **Inventory Exhaustion**:
   Tranche orders sell stored wheat, melon, or milk to generate immediate cash. In the simulation horizon (e.g. 20–36 turns), this cash is counted, and remaining inventory is liquidated at current market prices.
2. **Post-Horizon Macro Starvation**:
   In the live game beyond the simulation horizon, wheat is needed to feed cows and sheep. Depleting wheat forces the farm into `LIVESTOCK_FEED_RISK` and emergency feed purchases at unfavorable spot prices, destroying thousands in margin.
3. **Perturbation Asymmetry**:
   When perturbed ($q+1$, $q-1$), candidate deltas exhibit severe downside skew:
   - Selling $q=5$: $+\$50.0$
   - Selling $q=6$: $-\$210.0$ (triggers feed deficit)
   Because the live game execution encounters tiny downstream variations in worker timing, the point estimate $+ \$50.0$ lives on a knife-edge of viability.

---

## 4. Conclusion on Selection Regret

The failure is **NOT** that the compiler picked a worse candidate among those evaluated (within-turn selection regret is near zero).  
The failure is that the compiler **committed fragile, un-robust candidates** whose point estimate was positive but whose neighborhood was deeply negative.
