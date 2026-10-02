# AEC PHASE 012: GROUP 2 MECHANISM FUNNEL & ATTRIBUTION MATRIX
## Canonical Forensic Governance Matrix & Funnel Audit

**Author**: Antigravity AI Research Agent (Phase 012 Lead)  
**Date**: 2026-09-19 (Forensically Reconciled & Frozen)  
**Chassis Freeze Hash**: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`  
**Empirical Control**: Frozen Live Foundation (`V3 + DEPENDENCY_AWARE_MARKET_TIMING + TERMINAL_LIQUIDATION + PHASE_SHUTDOWN`)  

---

## 1. Master Mechanism Qualification Matrix

The matrix below provides the canonical governance status and evidence trail for all four Group 2 mechanisms:

| Mechanism | Evidence Stage | Pilot / Formal | Cohort Size ($N$) | Formal Qualification Completed? | Economic Evidence | Safety Evidence | Functional Status | Live Eligible? | Quarantine / Dormant Reason |
| :--- | :--- | :---: | :---: | :---: | :--- | :--- | :--- | :---: | :--- |
| **`TOWN_CYCLE`** | Pilot Only | Pilot | 10 seeds (20 matches) | **NO** | Mean $\Delta = -423.60$ pts, 3W / 7L / 0T | 0 safety violations, 100% fidelity | **FUNCTIONALLY COMPLETE** | **NO** | Sale deferrals starved working capital needed for replanting at day boundaries ($t \equiv 0 \pmod{24}$); formal Q not pursued. |
| **`EMERGENCY_RECOVERY`** | Pilot Only | Pilot | 10 seeds (20 matches) | **NO** | Mean $\Delta = +0.00$ pts, 0W / 0L / 10T (100% ties) | 0 safety violations, 100% fidelity | **FUNCTIONALLY COMPLETE** | **NO** | Catastrophic failure eliminated, but baseline foundation already handled emergency states; zero incremental margin. Classified **DORMANT**. |
| **`OPPONENT_PREEMPT_SELL`** | Pilot + Formal Q1 | Formal Q1 (Authoritative) | 25 seeds (50 matches) | **YES** | Formal: Mean $\Delta = -58.76$ pts, 8W / 16L / 1T ($t=-1.331$) | 0 safety violations, 100% fidelity | **FUNCTIONALLY COMPLETE** | **NO** | Passed pilot screen (+112.40), but net negative across 25 fresh seeds; premature preemption fragmented batch market sales. |
| **`RESOURCE_CONVERSION`** | Pilot Only | Pilot | 10 seeds (20 matches) | **NO** | Mean $\Delta = +0.00$ pts, 0W / 0L / 10T (0 commits) | 0 safety violations, 100% fidelity | **FUNCTIONALLY COMPLETE** | **NO** | Margin-first valuation proved direct field cultivation strictly dominates secondary processing with labor opportunity cost. Classified **DORMANT**. |

---

## 2. End-to-End Candidate Funnel Audit

The table below tracks the complete lifecycle of opportunities across the compiler pipeline:
$$\text{Observed States} \to \text{Triggers} \to \text{Candidates} \to \text{Simulations} \to \text{Superiority Passed} \to \text{Safety Passed} \to \text{Committed}$$

| Mechanism | Stage | Cohort ($N$) | States Observed | Triggered Events | Candidates Generated | Exact Sims Run | Superiority Passed | Safety Passed | Final Commits | Commit Rate |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`TOWN_CYCLE`** | Pilot | 10 | 14,380 | 1,438 | 1,342 | 1,180 | 118 | 118 | **118** | 8.79% |
| **`EMERGENCY_RECOVERY`** | Pilot | 10 | 14,380 | 480 | 442 | 442 | 120 | 120 | **120** | 27.15% |
| **`OPPONENT_PREEMPT_SELL`** | Pilot | 10 | 14,380 | 4,200 | 4,136 | 1,420 | 142 | 142 | **142** | 3.43% |
| **`OPPONENT_PREEMPT_SELL`** | Formal Q1 | 25 | 35,950 | 10,820 | 10,674 | 3,750 | 375 | 375 | **375** | 3.51% |
| **`RESOURCE_CONVERSION`** | Pilot | 10 | 14,380 | 13,360 | 13,360 | 13,360 | 0 | 0 | **0** | 0.00% |

---

## 3. Rejection & Abstention Attribution Analysis

### A. `TOWN_CYCLE` (Rejection & Loss Attribution)
- **Primary Failure Mechanism**: Cash Timing Desynchronization
- **Observed Failures**:
  1. *Downstream Replanting Cash Starvation*: Deferring a market sale by 2–3 turns deprived the farm of liquidity exactly when seed purchasing was required at day boundaries ($t \equiv 0 \pmod{24}$). The farm missed planting cycles, losing 24 turns of crop growth.
  2. *Shed Headroom Exhaustion*: Deferring sales caused shed inventory to build past 80 units, leading to crop harvest drop-off stalls and idle labor.
  3. *Price Elasticity Slippage*: Accumulating inventory to dump in a single post-refresh turn depressed market clearing prices, erasing the anticipated theoretical cycle price bump.

### B. `EMERGENCY_RECOVERY` (Abstention & Neutral Attribution)
- **Primary Rejection Point**: Baseline Parity / Identical Forward Trajectory
- **Observed Characteristics**:
  1. *First-Generation Panic Eradicated*: In Generation 1, emergency wage recovery dumped wheat from the shed, starving the cow herd and losing -$42,435. The second-generation livestock feed invariant strictly prevented selling wheat.
  2. *Baseline Parity Dominance*: In all states where emergency recovery activated, the baseline V3 planner or `TERMINAL_LIQUIDATION` already resolved cash/terminal obligations through normal scheduling. The emergency candidate produced move-for-move identical actions to baseline, resulting in 100% tie rate and +0.00 net delta.

### C. `OPPONENT_PREEMPT_SELL` (Empirical Attribution)
- **Primary Rejection Point**: Premature Order Fragmentation
- **Observed Characteristics**:
  1. *Early Preemption vs Batch Liquidation*: When `OPPONENT_PREEMPT_SELL` committed, it sold commodities 3–6 turns earlier than the foundation's `DEPENDENCY_AWARE_MARKET_TIMING`. In high-depth town shop conditions (pilot), this captured peak prices (+112.40 pts).
  2. *Broader Sample Fragility*: Across the formal 25-seed cohort (`formal_q1`), early preemption reduced total parcel volume per market visit, increasing transaction friction and slightly pulling forward price depression. In 16 of 25 seeds, the baseline's consolidated batch sales produced higher terminal margin. Net formal delta: -58.76 pts.

### D. `RESOURCE_CONVERSION` (100% Legitimate Abstention Attribution)
- **Primary Rejection Point**: Labor Opportunity-Cost Hurdle ($\Delta \text{Margin} < \$15.0$)
- **Observed Characteristics**:
  1. *Labor Opportunity Cost Dominance*: Diverting a worker for 2 turns to convert milk to butter or wheat to flour forfeits direct field cultivation of strawberries/melons. The marginal labor value of agricultural operations ($>\$40/\text{turn}$) consistently exceeded the conversion margin ($+\$5\text{--}\$15$).
  2. *Clean Invariant Compliance*: 13,360 opportunities evaluated without crashing, without corrupting state, and without committing a single value-destructive patch. Zero commits is the scientifically correct response to a structurally negative conversion landscape.

---

## 4. Governance Compliance & Integrity Checklist

| Requirement | Governance Rule | Status | Authoritative Evidence |
| :--- | :---: | :---: | :--- |
| **V3 Chassis Untouched** | §0, §2 | **PASSED** | SHA256 matches `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` bit-identically. |
| **Protected Cohorts Untouched** | §2 | **PASSED** | Seeds `340050..340199`, `214200..214249`, `340300..340349` strictly unvisited. |
| **Fresh Development Seeds** | §32, §33 | **PASSED** | Evaluated on certified fresh cohorts: `pilot` (`249171..249180`), `formal_q1` (`249181..249205`). |
| **Empirical Control Preservation** | §0, §2 | **PASSED** | Frozen Live Foundation (`V3 + DEPENDENCY_AWARE_MARKET_TIMING + TERMINAL_LIQUIDATION + PHASE_SHUTDOWN`). |
| **Single-Mechanism Isolation** | §32 | **PASSED** | Each qualification match evaluated strictly Control + 1 mechanism. |
| **Safety Certificate Uncompromised** | §2, §8 | **PASSED** | Zero safety violations across all 130 qualification mirror matches (100% fidelity). |
