# DEVELOPMENT EXPERIMENT PROTOCOL V1.4
## EXP-DEV-005: Confirmed-Shop Gated Whole-Route Adaptive Planning over V54++ Residual Preemption

**Document Identifier**: `DEVELOPMENT_EXPERIMENT_PROTOCOL_V1_4.md`  
**Experiment Identifier**: `EXP-DEV-005`  
**Date**: 2026-09-14  
**Status**: PRE-REGISTRATION FREEZE (Must be committed to Git prior to first simulation)  
**Governance Authority**: Autonomous Verification Engine (Zero-Leakage Governance)  
**Authoritative Baseline**: `candidates/compiled_v54_plus_residual.py` (Submission `56146971`)  
**Baseline Verified SHA-256**: `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb`  
**Treatment Candidate**: `candidates/closed_loop_architecture/dev_005_confirmed_shop_scheduler.py`  
**Treatment SHA-256**: `f52b168619e47bea6a052faff890fc84804cb39b47392d247139967f910e2a78`  
**Discovery Partition**: Seeds `247000` to `247049` ($N=50$ contiguous seeds, 100 paired CRN matches)  

---

## 1. Executive Summary & Research Question

### 1.1 Context from Preceding Experiments
- **EXP-DEV-003**: Demonstrated that runtime crop substitution without whole-route synchronization destroys worker scheduling and triggers severe lifespan cliffs.
- **EXP-DEV-004**: Demonstrated that whole-route macro production planning captures massive specialization upside (+1.65k mean delta), but suffered losses from mid-flight route reversals.
- **EXP-DEV-005_KILLTEST**: Conclusively proved that "never reverse" commitment hysteresis is **MIXED_UNSAFE** (<21% recovery, doubled losses on 7 seeds, -$25.7k collapse on positive control). Reversals were defensive retreats against unabsorbable products. The root cause was **premature speculative commitment at Step 72 before the matching town shop was confirmed**.

### 1.2 Primary Research Question
> *"Does delaying irreversible whole-route specialization until sufficient commercial shop absorption is confirmed improve the robustness and expected economic value of the whole-route production planner over the V54++ baseline?"*

### 1.3 Secondary Research Question
> *"Can a confirmation-gated planner preserve the large specialization upside discovered in DEV-004 while preventing the premature-specialization failures caused by acting on a single early shop reveal?"*

---

## 2. Formal Hypotheses

### Primary Hypothesis ($H_1$)
> A whole-route planner that remains in the V54++ baseline state while shop information is unconfirmed, and activates specialization only after a confirmed commercial shop unlock, will improve out-of-sample economic robustness (reduced downside variance and positive paired mean cash delta) relative to V54++ on unseen seeds.

### Null Hypothesis ($H_0$)
> Delaying specialization until commercial shop confirmation does not materially improve economic performance or sacrifices too much early-specialization upside, producing a mean delta indistinguishable from or worse than baseline.

---

## 3. Operational Definition of "Confirmed Shop" Gating

A specialized candidate macro route $R$ is defined as **CONFIRMED** at checkpoint step $t$ if and only if:
1. **Physical Commercial Shop Unlock**: The specific town shop required to absorb route $R$'s primary specialized output at high throughput ($1\text{ unit} / 4\text{ turns}$) is present in currently observable `town.unlocked_shops`.
   - `YARN_SPECIALIZED`: Requires `"YARN_STORE" in unlocked_shops`
   - `BAKERY_SPECIALIZED`: Requires `"BAKERY" in unlocked_shops`
   - `PET_SPECIALIZED`: Requires `"PET_CAFE" in unlocked_shops`
   - `SMOOTHIE_SPECIALIZED`: Requires `"SMOOTHIE_SHOP" in unlocked_shops`
   - `PIZZA_ADAPTIVE`: Requires `"PIZZA_SHOP" in unlocked_shops`
2. **Economic Viability Hurdle**: Under confirmed shop absorption, route $R$'s net expected terminal value exceeds baseline continuation by at least $\tau = 1500.0$ coins.
3. **Liquidity Invariant**: Current farm cash satisfies $L \ge L_{\text{min}} = 100.0$ coins.
4. **Physical Feasibility**: Maturation window $T_{\text{rem}} \ge T_{\text{mat}}$, worker service rate $T_{\text{srv}} \le T_{\text{int}}$, and lifespan constraints are satisfied.

### Pre-Confirmation Invariant
If route $R$'s required commercial shop is **NOT** present in `unlocked_shops`, route $R$ is **STRICTLY UNCONFIRMED**.
- The planner **MUST** remain in `BASELINE_BACKBONE`.
- The candidate executes 100% default V54++ behavior bit-for-bit.
- The candidate does **not** purchase specialization-specific livestock (e.g. extra sheep) or alter planting vectors.
- Telemetry records `decision = "REJECT_UNCONFIRMED"` with reason `REQUIRED_SHOP_NOT_UNLOCKED:<shop>` to monitor the opportunity cost of waiting.

---

## 4. Checkpoint Schedule & Mechanics Justification

The planning checkpoint evaluation steps remain strictly anchored to the game's natural shop reveal intervals:
- **Step 72 (Day 3, Hour 0)**: Shop 1 unlocked. (If Shop 1 is the matching shop, confirmation occurs immediately).
- **Step 144 (Day 6, Hour 0)**: Shop 2 unlocked. (Primary confirmation gate for late reveals).
- **Step 216 (Day 9, Hour 0)**: Shop 3 unlocked.
- **Step 288 (Day 12, Hour 0)**: Shop 4 unlocked (Final town shop reveal).

*Justification*: Checkpoints are determined strictly by game environment mechanics (shop unlock times). No checkpoint sweeps or post-hoc threshold tuning are permitted.

---

## 5. Candidate Architecture & Isolation Requirements

### 5.1 Controlled Factor
The **sole independent experimental variable** is:
$$\text{TIMING AND CONFIRMATION REQUIREMENT FOR WHOLE-ROUTE SPECIALIZATION}$$

### 5.2 Strict Invariant Preservations (Identical to DEV-004)
- **Route Registry**: `BASELINE_BACKBONE`, `YARN_SPECIALIZED`, `BAKERY_SPECIALIZED`, `PET_SPECIALIZED`, `SMOOTHIE_SPECIALIZED`, `PIZZA_ADAPTIVE` (Identical route profiles).
- **Physical Feasibility Model**: Identical maturation, cadence, lifespan, and dead inventory weights ($W_{\text{sat}}=1.0, W_{\text{life}}=2.0, W_{\text{dead}}=0.5$).
- **Market Absorption Engine**: Identical shop pull rate ($1/4$) and town center pull rate ($1/12$).
- **Authoritative Preemption Engine**: Identical parameters:
  `preempt_money_deficit = 2000.0`, `preempt_minimum_delta = 4.0`, `preempt_maximum_batch = 12`.
- **Decision Parameters**: $\tau = 1500.0$, $L_{\text{min}} = 100.0$, $F_{\text{switch}} = 200.0$.

---

## 6. Strict Zero-Leakage & Governance Invariants

The candidate planner is subject to automated AST and runtime zero-leakage assertions:
1. **Forbidden Keys**: `future_shops`, `terminal_score`, `ground_truth`, `future_market`, `offline_trajectory`, `oracle`, `future_prices`, `future_events`.
2. **Quarantined Partitions**:
   - Qualification `50050–50099`: Strictly quarantined.
   - Final Holdout `214200–214249`: Strictly quarantined.
   - Historical Contaminated `50000–50499`: Quarantined.
   - DEV-003 Consumed `245000–245049`: Quarantined.
   - DEV-004 Consumed `246000–246049`: Quarantined.
3. **Kaggle Invariant**: Zero live submissions.

---

## 7. Experimental Design & Endpoints

### 7.1 Discovery Sample Size
- $N=50$ contiguous virgin seeds (`247000–247049`).
- 100 balanced Common Random Number (CRN) matches:
  - Match 0: Candidate = Seat 0, Baseline = Seat 1.
  - Match 1: Baseline = Seat 0, Candidate = Seat 1.
  - Paired Cash Delta: $\Delta_i = 0.5 \times (\Delta_{i,0} + \Delta_{i,1})$.

### 7.2 Primary Endpoint
- **Paired Mean Cash Delta**: $\Delta \mu = \frac{1}{N} \sum_{i=1}^N \Delta_i$ (Candidate minus V54++ Baseline).

### 7.3 Secondary Diagnostic Endpoints
- DEV-005 vs DEV-004 diagnostic comparison (unpooled).
- 10% Trimmed Mean, Median Delta, Student-t, p-value, 95% Confidence Interval.
- Win / Loss / Tie Counts and Rates.
- Missed Opportunity Rate vs Avoided Premature Specialization Rate.

---

## 8. Pre-Registered Development Gates

| Outcome Category | Quantitative Criteria | Mechanistic Interpretation | Decision |
| :--- | :--- | :--- | :--- |
| **Category A (Clear Success)** | $\Delta \mu \ge +\$1,000.00$, $\text{Trimmed } \mu \ge +\$500.00$, $p < 0.10$, reduced downside variance | Confirmation gating preserves upside while preventing premature mismatch | **Candidate for Qualification Staging** |
| **Category B (Moderate Edge)** | $\$200.00 \le \Delta \mu < \$1,000.00$, Win Rate $>$ Loss Rate | Meaningful economic improvement with minor opportunity cost | **Retain in Discovery for Iteration** |
| **Category C (Neutral / Truncated)** | $-\$200.00 < \Delta \mu < +\$200.00$ | Waiting protects downside but misses equal upside | **No-Go / Exploratory Inconclusive** |
| **Category D (Structural Failure)** | $\Delta \mu \le -\$200.00$ or severe single-seed tail failure | Waiting destroys time-sensitive specialization value | **Reject Hypothesis $H_1$** |

---

## 9. Protocol Commitment Rule

This protocol and its SHA-256 hash must be written to disk, verified, and committed to Git repository history BEFORE the first simulation of EXP-DEV-005 begins.
