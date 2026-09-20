# AEC PHASE 010B: MASTER MECHANISM STATUS MATRIX
**Author**: Lead Scientific Experiment & Simulation Governance Auditor  
**Date**: 2026-09-19  
**Architecture Freeze Point**: Phase 009 Finalized 44-Item Platform  
**V3 Baseline Chassis Hash**: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`  
**Governance Scope**: Epistemic Audit of All 14 Evaluated Mechanisms  

---

## 1. Epistemic Audit of the "14 Mechanisms Evaluated" Claim

In the conclusion of Phase 010, the statement was made:
> *"All 14 mechanisms have been systematically evaluated... PROSPECTIVE READINESS: READY"*

### Scientific Clarification:
The word **"evaluated"** in Phase 010 represented **preliminary Stage A screening ($N=3$ seeds)** for experimental candidates, and **offline analytical tests ($N=0$ seeds)** for labor infrastructure. It did **NOT** represent formal empirical qualification under the pre-registered 12-item standard ($N \ge 25$ seeds, Common Random Numbers, mirror-seated, replicated).

Only **3** mechanisms possess verified, replicated empirical or structural qualification:
1. `DEPENDENCY_AWARE_MARKET_TIMING` (Phase 008 confirmatory $N=50$ trial: $+52.12$ net delta, $t=5.26, p < 0.0001$, 84% win rate).
2. `TERMINAL_LIQUIDATION` (Verified baseline chassis defense-in-depth).
3. `PHASE_SHUTDOWN` (Verified baseline chassis defense-in-depth).

One mechanism is verified **marginal valuation infrastructure**:
4. `LABOR_SHADOW` (12/12 ground-truth analytical tests passed; Stage S5 funnel screen; not a standalone live transformation).

Seven mechanisms are **functionally complete but naturally dormant**:
5. `DYNAMIC_SHADOW_HARVEST`
6. `TERMINAL_HARVEST_SWEEP`
7. `ROUTE_COMPRESSION`
8. `CARGO_FERRY`
9. `SHOP_ARBITRAGE`
10. `PRODUCTION_ARBITRAGE`
11. `TERMINAL_CONVERSION`

Four mechanisms are **decisively failed and permanently quarantined**:
12. `TOWN_CYCLE` (-$36,655.33 / seed, $p=0.0108$)
13. `EMERGENCY_RECOVERY` (-$25,792.00 / seed, $p=0.0000$)
14. `OPPONENT_PREEMPT_SELL` (-$96.67 / seed, harmful commits)
15. `RESOURCE_CONVERSION` (Prior Negative ITT -$258.96 / seed)

One mechanism is **research-only**:
16. `META` (Exceeds competition per-step latency budget).

---

## 2. Canonical Mechanism Status Matrix

The table below corrects the taxonomy across all mechanisms:

| Mechanism | Category | Pilot ($N$) | Formal ($N$) | Replicated? | Pilot Net Delta | Target Commits | Primary Effect & Significance | True Scientific Status | Live Build Eligibility |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- | :--- | :--- |
| **DEPENDENCY_AWARE_MARKET_TIMING** | Foundation (Market) | N/A | **50** | **YES** | N/A | High | **+$52.12 \pm $9.91** ($t=5.26, p < 10^{-6}$) | **FORMALLY QUALIFIED (FOUNDATION)** | **LIVE-ELIGIBLE** |
| **TERMINAL_LIQUIDATION** | Foundation (Terminal) | N/A | **50** | **YES** | N/A | Terminal | **Verified Baseline Defense-in-Depth** | **FORMALLY QUALIFIED (FOUNDATION)** | **LIVE-ELIGIBLE** |
| **PHASE_SHUTDOWN** | Foundation (Terminal) | N/A | **50** | **YES** | N/A | Late-game | **Verified Baseline Defense-in-Depth** | **FORMALLY QUALIFIED (FOUNDATION)** | **LIVE-ELIGIBLE** |
| **LABOR_SHADOW** | Infrastructure (Labor) | 0 | 0 | Analytical (12/12) | N/A | 0 (Screen) | **Exact Marginal Cost Verified Offline** | **VALIDATED VALUATION INFRASTRUCTURE** | **INFRASTRUCTURE ONLY (NOT A LIVE TRANSFORMATION)** |
| **DYNAMIC_SHADOW_HARVEST** | Labor | 3 | 0 | NO | -$4.67 \pm $4.67 | 0 | Baseline greedy policy already harvests | **FUNCTIONALLY COMPLETE / DORMANT** | **QUARANTINED** |
| **TERMINAL_HARVEST_SWEEP** | Terminal | 3 | 0 | NO | +$13.67 \pm $46.84 | 0 | Delta from 10 foundation market commits | **FUNCTIONALLY COMPLETE / DORMANT** | **QUARANTINED** |
| **ROUTE_COMPRESSION** | Route / Logistics | 3 | 0 | NO | +$62.00 \pm $33.08 | 0 | Delta from 6 foundation market commits | **FUNCTIONALLY COMPLETE / DORMANT** | **QUARANTINED** |
| **CARGO_FERRY** | Labor / Logistics | 3 | 0 | NO | +$26.00 \pm $28.45 | 0 | Delta from 10 foundation market commits | **FUNCTIONALLY COMPLETE / DORMANT** | **QUARANTINED** |
| **SHOP_ARBITRAGE** | Market | 3 | 0 | NO | +$11.00 \pm $21.08 | 0 | Delta from 12 foundation market commits | **FUNCTIONALLY COMPLETE / DORMANT** | **QUARANTINED** |
| **PRODUCTION_ARBITRAGE** | Resource | 3 | 0 | NO | +$126.67 \pm $23.15 | 0 | Delta from 10 foundation market commits | **FUNCTIONALLY COMPLETE / DORMANT** | **QUARANTINED** |
| **TERMINAL_CONVERSION** | Terminal | 3 | 0 | NO | +$89.33 \pm $66.69 | 0 | Delta from 12 foundation market commits | **FUNCTIONALLY COMPLETE / DORMANT** | **QUARANTINED** |
| **EMERGENCY_FEED_PURCHASE** | Resource | 3 | 0 | NO | +$28.67 \pm $52.84 | 0 | Delta from 10 foundation market commits | **FUNCTIONALLY COMPLETE / DORMANT** | **QUARANTINED** |
| **TOWN_CYCLE** | Market Timing | 3 | 0 | NO | -$36,655.33 \pm $14.39k | 247 | **-$36,655.33 / seed** ($t=-2.55, p=0.0108$) | **FAILED QUALIFICATION (HARMFUL)** | **PERMANENTLY QUARANTINED** |
| **EMERGENCY_RECOVERY** | Resource / Crisis | 3 | 0 | NO | -$25,792.00 \pm $4.82k | 20 | **-$25,792.00 / seed** ($t=-5.36, p=0.0000$) | **FAILED QUALIFICATION (HARMFUL)** | **PERMANENTLY QUARANTINED** |
| **OPPONENT_PREEMPT_SELL** | Opponent / Market | 3 | 0 | NO | -$96.67 \pm $96.67 | 2 | **-$145.00 / commit** (False dumping panic) | **FAILED QUALIFICATION (HARMFUL)** | **PERMANENTLY QUARANTINED** |
| **META** | Orchestration | 1 | 0 | NO | +$126.00 | 0 | Exceeds 100ms per-step latency budget | **RESEARCH ONLY (LATENCY EXCEEDED)** | **QUARANTINED** |
| **RESOURCE_CONVERSION** | Resource | Ret. | 25 | YES | Prior -$258.96 | N/A | Prior Phase 004B negative ITT confirmed | **FAILED QUALIFICATION (FALSIFIED)** | **PERMANENTLY QUARANTINED** |

---

## 3. Scientific Rules for Promotion

1. **Synthetic Activation $\ne$ Economic Validation**:
   Passing mock compiler tests (`test_synthetic_mechanism_matrix.py`) proves source-code completeness, interface compatibility, and absence of syntax crashes. It does **not** prove that the mechanism produces positive economic value in competitive multi-agent game dynamics.
2. **0 Natural Commits $\ne$ Economic Qualification**:
   If a mechanism achieves zero commits in full-game play against the baseline, its effect size is unmeasured. It cannot be promoted to live play.
3. **Harmful Signal $\implies$ Quarantine**:
   Mechanisms exhibiting statistically significant economic loss (`TOWN_CYCLE`, `EMERGENCY_RECOVERY`, `OPPONENT_PREEMPT_SELL`) are permanently barred from live deployment. They must not be rerun or re-tuned in an attempt to overturn decisive negative evidence.
4. **Live Allowlist Constraint**:
   The live-eligible configuration is strictly limited to verified, formally qualified mechanisms. Under this standard, only the foundation mechanisms are live-eligible:
   ```python
   ENABLED_FOUNDATION_MECHANISMS = (
       "DEPENDENCY_AWARE_MARKET_TIMING",
       "TERMINAL_LIQUIDATION",
       "PHASE_SHUTDOWN",
   )
   ```
