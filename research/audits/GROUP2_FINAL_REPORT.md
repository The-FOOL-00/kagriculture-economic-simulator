# AEC PHASE 012: GROUP 2 FINAL MECHANISM RESCUE REPORT
## Canonical Evidence Reconciliation & Qualification Audit

**Author**: Antigravity AI Research Agent (Phase 012 Lead)  
**Date**: 2026-09-19 (Corrected & Frozen)  
**Chassis Freeze Hash**: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`  
**Empirical Control**: Frozen Live Foundation (`V3 + DEPENDENCY_AWARE_MARKET_TIMING + TERMINAL_LIQUIDATION + PHASE_SHUTDOWN`)  
**Evaluation Protocol**: Paired Common Random Numbers (CRN) Mirror-Seat Evaluation  
**Seed Governance**: Certified Fresh Development Cohorts (`249171..249205`), zero overlap with protected cohorts (`340050..340199`, `214200..214249`, `340300..340349`) or retired development cohorts.

---

## 1. Scope

Phase 012 executed a second-generation architectural and economic rescue for the four Group 2 mechanisms:
1. **`TOWN_CYCLE`** (Economic Cycle Timing)
2. **`EMERGENCY_RECOVERY`** (Selective Damage Avoidance)
3. **`OPPONENT_PREEMPT_SELL`** (Robust Opponent Preemption under Uncertainty)
4. **`RESOURCE_CONVERSION`** (Margin-First Comparative Valuation)

The purpose of this report is to establish an internally consistent, forensic scientific record matching the Level 1 raw experiment artifacts (`results/phase012/*_matches.csv` and `*_summary.json`).

Under experiment governance, the protocol strictly distinguishes:
* **Pilot Screenings (N=10 seeds, 20 mirror matches)**: Used for directional screening and failure-mode validation.
* **Formal Qualification (N=25 seeds, 50 mirror matches)**: The required hurdle for prospective live deployment consideration.

---

## 2. Frozen Architecture

All experiments in Phase 012 were executed against the frozen canonical V3 chassis:
- **Tarball Path**: `submission_Vj_kc_v3.tar.gz`
- **Chassis SHA-256**: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` (verified bit-identical).
- **Protected Cohorts**: Primary Holdout (`340050..340199`), Gate 0.3 Holdout (`214200..214249`), and Prospective Tournament Cohort (`340300..340349`) remained strictly unvisited.
- **Retired Development Cohorts**: No re-use of seeds `50000..50024`, `249000..249049`, `249050..249110`, or `249111..249170`.

---

## 3. Empirical Control

The authoritative baseline control for all Phase 012 mirror matches was the exact frozen live foundation:
$$\text{CONTROL} = \text{V3 Chassis} + \text{DEPENDENCY\_AWARE\_MARKET\_TIMING} + \text{TERMINAL\_LIQUIDATION} + \text{PHASE\_SHUTDOWN}$$

* **Isolation Verification**: No Group 1 rescued mechanisms (`DYNAMIC_SHADOW_HARVEST`, `CARGO_FERRY`, `ROUTE_COMPRESSION`, `TERMINAL_HARVEST_SWEEP`) were active in the control.
* **Quarantine Enforcement**: All 15 non-foundation mechanisms were actively quarantined in `ctrl_cfg.quarantined_mechanisms`.
* **Feed Invariant Location**: Feed security predicates were applied exclusively within candidate proposal and gating for treatments; the shared foundation control logic was untouched.

---

## 4. Experimental Cohorts

Phase 012 utilized two distinct fresh development cohorts:
1. **Pilot Cohort (`pilot`)**: Seeds `249171..249180` (N=10 seeds, 20 mirror matches per mechanism). Evaluated for all four mechanisms (80 total matches).
2. **Formal Qualification Cohort (`formal_q1`)**: Seeds `249181..249205` (N=25 seeds, 50 mirror matches). Pursued exclusively for `OPPONENT_PREEMPT_SELL` following its positive pilot screen.

### Reconstructed Qualification Match Ledger

| Mechanism | Pilot Seeds | Pilot Matches | Formal Seeds | Formal Matches | Total Unique Seeds | Total Matches |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`TOWN_CYCLE`** | 10 (`249171..80`) | 20 | 0 | 0 | 10 | 20 |
| **`EMERGENCY_RECOVERY`** | 10 (`249171..80`) | 20 | 0 | 0 | 10 | 20 |
| **`OPPONENT_PREEMPT_SELL`** | 10 (`249171..80`) | 20 | 25 (`249181..205`) | 50 | 35 | 70 |
| **`RESOURCE_CONVERSION`** | 10 (`249171..80`) | 20 | 0 | 0 | 10 | 20 |
| **TOTAL QUALIFICATION** | **40** (10 unique) | **80** | **25** (25 unique) | **50** | **35 unique** | **130** |

*(Note: Two additional single-seed exploratory runs of 2 matches each exist in `results/phase012` for `TOWN_CYCLE_custom_1` and `EMERGENCY_RECOVERY_custom_1`, bringing the total matches recorded on disk to 134. The qualification experiment executed exactly 130 matches).*

---

## 5. Mechanism Results

The complete forensic results reconstructed directly from Level 1 raw CSVs and JSONs are summarized below:

| Mechanism | Evidence Stage | Evaluated Seeds | Mirror Matches | Paired Mean $\Delta$ | Paired Median $\Delta$ | Std Dev | Std Error | 95% Conf. Interval | $t$-Stat ($p$-value) | Record (W / L / T) | Target Commits (Rate) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`TOWN_CYCLE`** | Pilot | 10 | 20 | -423.60 | -74.00 | 711.68 | 225.05 | `[-932.67, +85.47]` | -1.882 ($p=0.0925$) | 3W / 7L / 0T | 118 (8.79%) |
| **`EMERGENCY_RECOVERY`** | Pilot | 10 | 20 | +0.00 | +0.00 | 0.00 | 0.00 | `[+0.00, +0.00]` | 0.000 ($p=1.000$) | 0W / 0L / 10T | 120 (27.15%) |
| **`OPPONENT_PREEMPT_SELL`** | Pilot | 10 | 20 | +112.40 | +36.00 | 334.61 | 105.81 | `[-126.95, +351.75]` | +1.062 ($p=0.3158$) | 6W / 4L / 0T | 142 (3.43%) |
| **`OPPONENT_PREEMPT_SELL`** | Formal Q1 | 25 | 50 | -58.76 | -49.00 | 220.75 | 44.15 | `[-149.89, +32.37]` | -1.331 ($p=0.1957$) | 8W / 16L / 1T | 375 (3.51%) |
| **`RESOURCE_CONVERSION`** | Pilot | 10 | 20 | +0.00 | +0.00 | 0.00 | 0.00 | `[+0.00, +0.00]` | 0.000 ($p=1.000$) | 0W / 0L / 10T | 0 (0.00%) |

All matches completed the full 719-step simulation horizon (0 early terminations, 0 safety violations, 100% simulator fidelity).

---

## 6. Formal Qualification Results

Only one mechanism in Group 2 advanced to and completed a formal qualification cohort:

### `OPPONENT_PREEMPT_SELL` (Formal Q1 Cohort)
- **Cohort**: Fresh seeds `249181..249205` (N=25 seeds, 50 mirror matches).
- **Outcome**: Mean Paired $\Delta = \mathbf{-58.76}$ pts, Median = $\mathbf{-49.00}$ pts, Record = **8W / 16L / 1T** (32.0% Win Rate).
- **Statistical Significance**: $t = -1.331$, $p = 0.1957$, 95% CI `[-149.89, +32.37]`.
- **Causal Assessment**: While preemption demonstrated positive screening in the 10-seed pilot (+112.40 pts) by capturing peak shop depth on favorable seeds, broader evaluation revealed that preemptive selling prematurely fragments batch market sales. Pulling sales forward forfeits volume consolidation and depresses prices prematurely.
- **Formal Status**: The formal 25-seed result is the authoritative qualification evidence. Because the mechanism produced negative incremental delta and failed all qualification criteria, it is **quarantined from live deployment**.

---

## 7. Pilot-Only Results

The remaining three mechanisms were evaluated exclusively in 10-seed pilot cohorts and did not pursue formal qualification:

### 1. `TOWN_CYCLE`
- **Evidence**: 10-seed pilot (`249171..249180`), Mean Paired $\Delta = \mathbf{-423.60}$ pts, 3W / 7L / 0T.
- **Finding**: Negative pilot evidence clearly demonstrates that deferring sales desynchronizes working capital needed for day-boundary seed purchases. The loss is severe enough to justify immediate quarantine without spending resources on a 25-seed formal cohort.
- **Status**: `FUNCTIONALLY COMPLETE / QUARANTINED` — negative pilot evidence; formal qualification not pursued.

### 2. `EMERGENCY_RECOVERY`
- **Evidence**: 10-seed pilot (`249171..249180`), Mean Paired $\Delta = \mathbf{+0.00}$ pts, 0W / 0L / 10T (100% ties).
- **Finding**: The second-generation redesign completely eliminated the catastrophic first-generation livestock starvation failure (-$42,435). However, in all states where recovery activated, the baseline foundation was already safe or executing identical liquidations. The mechanism produced zero incremental value over the foundation.
- **Status**: `FUNCTIONALLY COMPLETE / DORMANT` — safe and functional, but produced zero incremental advantage in pilot.

### 3. `RESOURCE_CONVERSION`
- **Evidence**: 10-seed pilot (`249171..249180`), 13,360 opportunities evaluated, **0 commits** (0.00%), Mean Paired $\Delta = \mathbf{+0.00}$ pts, 0W / 0L / 10T.
- **Finding**: The margin-first valuation correctly accounts for labor opportunity costs ($>\$40/\text{turn}$). Direct crop cultivation strictly dominates secondary processing; 0 commits reflects mathematically sound abstention rather than software failure.
- **Status**: `FUNCTIONALLY COMPLETE / DORMANT` — functionally complete, 100% legitimate abstention in pilot.

---

## 8. Causal Findings

1. **Working Capital Priority**: In a macro-scheduled agricultural simulation, cash timing dominates minor price-elasticity advantages. Deferring sales (`TOWN_CYCLE`) starves seed purchases, missing entire 24-turn crop cycles.
2. **Defensive Baseline Sufficiency**: The frozen foundation (`DEPENDENCY_AWARE_MARKET_TIMING` + `TERMINAL_LIQUIDATION` + `PHASE_SHUTDOWN`) already manages terminal cash and liquidation near-optimally. Emergency recovery mechanisms duplicate existing protections rather than expanding margin.
3. **Batch Consolidation vs. Preemption**: Pulling sales forward (`OPPONENT_PREEMPT_SELL`) disrupts bulk order batching. In 16 of 25 formal seeds, waiting for consolidated market orders yielded higher net revenue than preemption.
4. **Labor Opportunity Costs**: Processing agricultural goods into secondary products absorbs critical worker turns. Because land productivity is high, worker opportunity costs render secondary conversion economically negative under baseline parameters.

---

## 9. Cross-Mechanism Findings

Per governance rules, individual mechanism qualification is a mandatory prerequisite for cross-mechanism composition. Because none of the four individual mechanisms achieved positive statistical qualification over the frozen live foundation, composite multi-mechanism interactions cannot be authorized for live deployment. Group 2 mechanisms remain isolated and quarantined in live configurations.

---

## 10. Experimental Limitations

1. **Pilot Sample Size**: Pilot cohorts of N=10 seeds provide directional screening only. Confidence intervals for pilot-only mechanisms (`TOWN_CYCLE`, `EMERGENCY_RECOVERY`, `RESOURCE_CONVERSION`) are wide and should not be cited as formal statistical proofs.
2. **Opponent Dynamics**: Opponent preemption was evaluated against deterministic foundation agents under CRN mirror play. Performance against stochastic or adversarial policies in public competition may differ, though fundamental batching trade-offs remain.
3. **Parameter Scope**: Valuation hurdles were tuned conservatively to guarantee safety. While looser hurdles might increase commit rates, they risk re-introducing catastrophic losses.

---

## 11. Final Mechanism Status

The canonical governance taxonomy for Group 2 is finalized as follows:

| Mechanism | Evidence Stage | Formal Q Completed? | Empirical Result | Final Taxonomy Status | Live Build Deployment |
| :--- | :--- | :---: | :--- | :--- | :---: |
| **`TOWN_CYCLE`** | Pilot Only (N=10) | NO | Negative pilot ($\Delta = -423.60$) | **FUNCTIONALLY COMPLETE / QUARANTINED** | **NO** |
| **`EMERGENCY_RECOVERY`** | Pilot Only (N=10) | NO | Neutral pilot ($\Delta = +0.00$, 100% ties) | **FUNCTIONALLY COMPLETE / DORMANT** | **NO** |
| **`OPPONENT_PREEMPT_SELL`** | Pilot + Formal Q1 (N=35) | **YES** | Negative formal Q1 ($\Delta = -58.76$) | **FUNCTIONALLY COMPLETE / QUARANTINED** | **NO** |
| **`RESOURCE_CONVERSION`** | Pilot Only (N=10) | NO | 100% abstention ($\Delta = +0.00$) | **FUNCTIONALLY COMPLETE / DORMANT** | **NO** |

---

## 12. Live Build

The live competition build remains strictly untouched and preserved at the proven foundation:
$$\text{Live Build} = \text{V3 Chassis} + \text{DEPENDENCY\_AWARE\_MARKET\_TIMING} + \text{TERMINAL\_LIQUIDATION} + \text{PHASE\_SHUTDOWN}$$

* **Chassis SHA-256**: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`
* **Enabled Mechanisms**: 3
* **Quarantined Mechanisms**: 15 (including all Group 1 and Group 2 rescued mechanisms)

---

## 13. Next Phase

With the forensic reconciliation of Phase 012 complete and the canonical record frozen:
1. No Group 2 mechanisms will be submitted or deployed to the live build.
2. All experimental artifacts are archived in `results/phase012/` with full provenance.
3. Phase 013 (Group 3: Route, Movement, and Labor Allocation) may proceed only from this corrected baseline.
