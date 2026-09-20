# PHASE019 FOUNDATION OPPORTUNITY COST

**Phase**: PHASE019 — Uncertainty-Aware Commit Selection & Robust Economic Decision Audit  
**Date**: 2026-09-20  
**Scope**: Competition dynamics between foundation mechanisms and experimental tranche logic (§30).

---

## 1. Accounting Framework

Whenever an experimental tranche candidate is generated, evaluated, or committed, we trace its interaction with the live foundation mechanisms:
- `DEPENDENCY_AWARE_MARKET_TIMING`
- `TERMINAL_LIQUIDATION`
- `PHASE_SHUTDOWN`

We measure across four sequential gates:
1. **Availability**: Was a foundation candidate detected?
2. **Funnel Survival**: Did the foundation candidate survive static pruning to reach exact simulation?
3. **Comparative Evaluation**: When both were simulated, what were their relative counterfactual margins?
4. **Selection & Realized Outcome**: Was the foundation candidate chosen, or did the tranche candidate displace it?

---

## 2. Historical Telemetry Audit

### 2.1 Funnel Crowding at Pruning (Phase017 vs Phase018)
- **Phase017 (No Reservation)**:
  In seed 249288 step 649, a high-value foundation market timing opportunity ($+\$1,485.00$) was detected. However, 8 speculative tranche candidates filled the top-$K$ prune list, completely crowding out the foundation candidate from simulation. The compiler committed a tranche order that lost the match.
- **Phase018 Repair A (Funnel Reservation ON)**:
  `FunnelReservationPolicy` guaranteed a 25% floor for foundation mechanisms at pruning truncation points.
  - In the fresh Arm A cohort (seeds 249296..249305), foundation commits were restored from **0 to 14 commits**.
  - Reservation produced a clean, isolated **$+\$49.30$** paired delta across 20 matches.
  - Funnel-level crowding was successfully neutralized as an adopted infrastructure layer.

### 2.2 Commit-Level Displacement (Layer 3)
- When both foundation and tranche candidates survive to exact simulation:
  - If the tranche point estimate is $\Delta_T = +\$45.0$ and foundation is $\Delta_F = +\$35.0$, current commit selection chooses the tranche candidate strictly because $\Delta_T > \Delta_F$.
  - **Foundation Opportunity Cost**:
    $$\text{foundation\_opportunity\_cost} = \Delta_F - \Delta_T$$
  - While nominally negative at the point estimate ($-\$10.0$), the foundation candidate has **zero inventory risk** and is 100% boundary-safe. The tranche candidate absorbs downstream livestock starvation risk for an unhedged point gain of $\$10.00$.

---

## 3. Policy Recommendation

To permanently eliminate foundation displacement risk:
1. Preserve `enable_funnel_reservation = True` across all configurations.
2. Introduce **Foundation Primacy in Commit Selection**:
   If a valid, certified foundation candidate is available with $\Delta_F > 0$, an experimental tranche candidate may NOT displace it unless:
   $$\Delta_T - \Delta_F \ge \$15.0 \quad \text{AND} \quad \text{Candidate is R0 (Robustly Positive)}$$
