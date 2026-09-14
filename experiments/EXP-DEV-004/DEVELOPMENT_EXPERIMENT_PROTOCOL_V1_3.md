# DEVELOPMENT EXPERIMENT PROTOCOL V1.3
## EXP-DEV-004: Joint Macro Production Scheduler (V54++ Residual Preemption + Whole-Route Adaptive Planning)

**Status**: **PRE-EXECUTION FROZEN PROTOCOL**  
**Date**: 2026-09-14  
**Author**: Autonomous Research Engine & Pair Programming Agent  
**Governing Experiment**: `EXP-DEV-004`  
**Candidate Identifier**: `dev_004_joint_macro_scheduler`  
**Certified Discovery Partition**: Seeds `246000` to `246049` ($N=50$ contiguous seeds, 100 balanced CRN matches)  
**Authoritative Baseline**: `candidates/compiled_v54_plus_residual.py` (Submission `56146971`)  
**Baseline Verified SHA-256**: `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb`  

---

## 0. Absolute Governance Rules

1. **Frozen Codebases**: Under no circumstances modify `candidates/compiled_v54_plus_residual.py`, `candidates/compiled_v54_plus_shop.py`, or `candidates/closed_loop_architecture/dev_003_conditional_specialization.py`.
2. **No Promotion of DEV-003**: EXP-DEV-003 failed decisively and is permanently retired.
3. **No Kaggle Submissions**: Do not submit any candidate or baseline code to Kaggle during or after this experiment.
4. **Quarantine Isolation**:
   - Qualification Partition (`50050–50099`) is strictly quarantined.
   - Certified Virgin Final Holdout (`214200–214249`, `HOLDOUT-COHORT-V1`) is strictly quarantined (0 access, 0 simulations).
   - Historical Contaminated Region (`50000–50499`) is under permanent blanket quarantine.
   - DEV-003 Discovery Partition (`245000–245049`) is permanently retired and will never be reused for DEV-004.
5. **Virginity Verification**: Candidate Discovery partition `246000–246049` has been exhaustively proven virgin across all workspace files, Git history, and result databases.
6. **Pre-Execution Freeze**: All treatment parameters and architecture must be committed to Git before any candidate match is simulated (`protocol_commit < first_execution_timestamp`).
7. **No Parameter Sweeps**: Zero parameter sweeps or post-hoc retuning during the official Discovery run.
8. **Zero Future-State Information**: Live planner uses strictly current observations, unlocked shops, known prices, and deterministic public simulator mechanics.
9. **Immediate Stop Condition**: If any contamination or protocol ambiguity arises, halt immediately.

---

## 1. Bounded Empirical Findings from EXP-DEV-003

EXP-DEV-003 demonstrated:
- **A. Baseline Invariant Preservation**: Non-activating seeds preserved default V54++ behavior with 100% bit-exact fidelity ($\Delta = \$0.00$).
- **B. Specialization Overlay Breakdown**: The failure occurred exclusively when the specialization overlay activated.
- **C. Worker Route Incompatibility**: V54++ worker routes were tightly optimized around the 2-day harvest cadence of Strawberry; Tomato's daily yield cadence caused immediate saturation.
- **D. Lifespan Expiration Cliff**: Tomato plants planted on Day 11 possessed a hard lifespan boundary at Step 552 (Day 23), leaving 4 tiles barren for the final 7 days of the season.
- **E. Yield Capacity Saturation**: Tomato vines reached their maximum capacity (`yield_units = 4`) and ceased producing because worker visit intervals were too slow.
- **F. Realized Strawberry Dominance**: Strawberry generated substantial realized cashflow (over $40,000) even without a town Strawberry shop due to town center demand buffers and market pricing dynamics.
- **G. Micro Shop Pull Rate Limits**: Pizza shop pull rates (1 unit per 4 turns) were insufficient to absorb Tomato production or compensate for forgone Strawberry volume.
- **H. Structural Flaw**: Runtime crop substitution without whole-route spatial/temporal adaptation is fundamentally flawed.

---

## 2. Research Question

### Primary Question
> *"Can a whole-route production planner improve economic return over the current V54++ residual-preemption architecture by jointly planning crop mix, planting timing, worker routing, harvesting, and liquidation?"*

### Secondary Question
> *"Does whole-route planning capture specialization upside that runtime crop substitution could not capture?"*

---

## 3. Primary Hypotheses

- **$H_1$**: A planner that jointly evaluates crop economics and the physical production route can capture profitable specialization opportunities without suffering the structural worker/pathing and lifespan cliff failures observed in DEV-003.
- **$H_0$**: Joint-route adaptation does not materially improve over V54++.

*These hypotheses are permanently frozen prior to simulation and will not be altered post-hoc.*

---

## 4. Baseline Identity

- **Path**: `candidates/compiled_v54_plus_residual.py`
- **Active Submission ID**: `56146971`
- **File Size**: 338,100 bytes
- **Authoritative SHA-256**: `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb`
*(Recomputed directly from the filesystem; exactly matches existing frozen records).*

---

## 5. Preservation of Residual Preemption

The treatment candidate strictly preserves the V54++ residual-preemption mechanism:
- `preempt_money_deficit = 2000.0`
- `preempt_minimum_delta = 4.0`
- `preempt_maximum_batch = 12`

EXP-DEV-004 tests **production macro adaptation**, not liquidity preemption redesign.

---

## 6. Treatment Architecture

- **Candidate Path**: `candidates/closed_loop_architecture/dev_004_joint_macro_scheduler.py`
- **Candidate Class**: `Dev004JointMacroScheduler`
- **Core Design**: V54++ + Joint Macro Production Planner.
- **Scope of Joint Decision**:
  1. Crop mix vector
  2. Tile spatial allocation
  3. Planting timing
  4. Worker path/routing
  5. Watering sequence
  6. Harvest timing and cadence
  7. Crop replacement / replanting
  8. Market sales and shop absorption
  9. Terminal liquidation timing

*Explicit Prohibition: Merely replacing `STRAWBERRY -> TOMATO` inside the old planner without whole-route adaptation is strictly forbidden.*

---

## 7. Physical Feasibility Model

A candidate plan is valid only if the complete physical production route supports it. For each candidate plan, the model explicitly evaluates:
- $T_{\text{maturity}}$ (Maturation time: 2 days for Wheat/Carrot, 8 days for Tomato, 10 days for Strawberry/Melon)
- $T_{\text{harvest\_interval}}$ (Harvest interval: 1 day for Tomato, 2 days for Strawberry, 0 for single-harvest crops)
- $T_{\text{lifespan}}$ (Plant lifespan: evaluated against remaining season horizon $T_{\text{rem}}$)
- Expected harvest count within usable window
- Worker service capacity / travel pathing cadence
- Maximum tile yield capacity ($Y_{\text{max}} = 4$)
- Watering requirements and schedule
- Number of available workers and competing livestock tasks
- Market pull rate (Shop demand: 1 unit / 4 steps; Town Center: 1 unit / 12-24 steps)
- Expected sale price under supply/demand elasticity
- Seed and animal input costs
- Terminal unsold inventory liquidation

A candidate plan receives a large penalty if:
1. Crop lifespan expires before the horizon leaving tiles barren ($P_{\text{life}}$),
2. Worker capacity cannot service harvest cadence causing vine saturation ($P_{\text{sat}}$),
3. Market sales cannot absorb production leaving dead terminal inventory ($P_{\text{dead}}$),
4. Liquidity is insufficient to support upfront costs ($P_{\text{liq}}$).

---

## 8. Plan Evaluation & Decision Rules

At planning checkpoints (Steps 72, 144, 216, 288 — corresponding to Days 3, 6, 9, 12):
1. **Observe**: Current farm state, cash, unlocked shops, market prices, and inventory.
2. **Evaluate Baseline**: Construct expected continuation value $E[V_{\text{base}}]$ of the default Strawberry Bedrock route.
3. **Evaluate Candidates**:
   - `BASELINE_BACKBONE` (`_V56_BACKBONE_ROUTE`)
   - `YARN_SPECIALIZED` (`_V56_YARN_ROUTE`)
   - `BAKERY_SPECIALIZED` (`_V58_BAKERY_YARN_ROUTE`)
   - `PET_SPECIALIZED` (`_V57_PET_ROUTE`)
   - `SMOOTHIE_SPECIALIZED` (`_V58_SMOOTHIE_ROUTE`)
   - `PIZZA_ADAPTIVE` (`_V58_PIZZA_RECOVERY_ROUTE`)
4. **Compute Net Advantage**:
   $$\Delta V_p = E[V_p] - E[V_{\text{base}}] - F_{\text{switch}}$$
5. **Selection Gate**:
   A specialized route $p^*$ is selected if and only if:
   $$\Delta V_{p^*} \ge \tau \quad \text{AND} \quad \text{money} \ge L_{\text{min}}$$
   Otherwise, the planner defaults 100% to `BASELINE_BACKBONE`.

---

## 9. Frozen Parameter Registry

| Parameter | Identifier | Value | Rationale |
| :--- | :--- | :---: | :--- |
| **Opportunity Threshold** | $\tau$ | `1500.0` coins | Substantial economic hurdle above switching friction and noise. |
| **Minimum Liquidity Floor** | $L_{\text{min}}$ | `100.0` coins | Working capital reserve to avoid operational insolvency. |
| **Switching Friction** | $F_{\text{switch}}$ | `200.0` coins | Fixed penalty for path repositioning and initial drift. |
| **Saturated Yield Weight** | $W_{\text{sat}}$ | `1.0` | 100% penalty on unharvested production lost to vine saturation. |
| **Lifespan Cliff Weight** | $W_{\text{life}}$ | `2.0` | Heavy penalty for planting crops that die prematurely. |
| **Dead Inventory Weight** | $W_{\text{dead}}$ | `0.5` | Opportunity cost penalty on unsold shed stock at terminal. |
| **Preemption Deficit** | `preempt_money_deficit` | `2000.0` coins | Authoritative V54++ residual preemption parameter. |
| **Preemption Delta** | `preempt_minimum_delta` | `4.0` coins | Authoritative V54++ residual preemption parameter. |
| **Preemption Batch** | `preempt_maximum_batch` | `12` units | Authoritative V54++ residual preemption parameter. |

---

## 10. Certified Virgin Discovery Partition

- **Seed Range**: `246000` to `246049`
- **Sample Size**: $N = 50$ contiguous seeds
- **Pairing Design**: Common Random Numbers (CRN) with Seat Swapping:
  - Match 0: Candidate (Seat 0) vs Baseline (Seat 1)
  - Match 1: Baseline (Seat 0) vs Candidate (Seat 1)
- **Total Matches**: 100 complete games
- **Provenance Certification**: Certified 100% virgin in `SEED_PROVENANCE.md`.

---

## 11. Metrics & Success Criteria

### 11.1 Primary Metric
- **Paired Mean Final Cash Delta**:
  $$\Delta \mu = \frac{1}{N} \sum_{i=1}^{N} \frac{\Delta_{i,0} + \Delta_{i,1}}{2}$$
  where $\Delta_{i, \text{seat}} = \text{Reward}_{\text{candidate}} - \text{Reward}_{\text{baseline}}$.

### 11.2 Secondary Metrics
- Median paired delta, Standard Deviation, Standard Error, Student-t statistic, p-value, 95% Confidence Interval.
- Percentile distribution ($p_{01}, p_{05}, p_{10}, p_{25}, p_{50}, p_{75}, p_{90}, p_{95}, p_{99}$, min, max).
- Win / Loss / Tie counts and rates.
- Concentration metrics: Top-1 and Top-2 contribution, mean excluding best seed, mean excluding worst seed, mean excluding top-2 seeds.

### 11.3 Physical Planning Metrics
- Planned vs actual crop mix.
- Worker utilization and missed harvest opportunities.
- Yield capacity saturation events.
- Dead / expired crop occurrences (specifically testing whether DEV-003 cliff is eliminated).
- Total sales throughput and terminal unsold inventory value.
- Specialization activation rate and plan-switch frequency.

### 11.4 Success Criteria & Gates
1. **Economic Viability Gate**: $\Delta \mu \ge +\$100.00$ paired mean cash delta over V54++.
2. **Tail-Risk Bounding Gate**: Worst-seed loss must not exceed $-\$1,500.00$ (a $>89\%$ tail-risk reduction vs DEV-003's $-\$14,696.00$).
3. **Robustness Gate**: Mean delta must remain positive after removing the best seed ($\Delta \mu_{\text{no\_best}} > \$0.00$).
4. **Baseline Invariant Gate**: 100% of non-activating seeds must yield $\Delta = \$0.00$ bit-for-bit.
5. **Zero Error Gate**: Exactly 0 simulator crashes, assertion failures, or timeouts across all 100 matches.

---

## 12. Required Forensic Investigation

Post-execution forensic audit must answer:
1. Did the planner actually change complete production routes rather than isolated crop identities?
2. Did worker routing adjust when crop type or harvest cadence changed?
3. Did the planner avoid planting crops whose lifespan created a terminal cliff?
4. Did it prevent vine yield capacity saturation?
5. Did it account for realistic market absorption pull rates?
6. Did it eliminate or substantially reduce the DEV-003 failure mechanisms?
7. Does the economic advantage persist without the top seed?
8. Are gains concentrated in a single shop configuration?
9. Does the planner over-activate or under-activate?
10. Does it preserve default V54++ in unpromising or ambiguous states?
11. Is performance gain driven by joint macro routing or simple chance?
12. What are the specific recommendations for qualification or next experiments?

---

## 13. Stop Conditions

Execution must halt immediately if:
- Baseline SHA-256 deviates from `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb`.
- Candidate AST reveals forbidden future-state access or hidden variables.
- Any seed in quarantined ranges (`50050–50099`, `214200–214249`, `245000–245049`) is invoked.
- Protocol Git commit timestamp is not prior to simulation start.
- Any runtime crash or non-deterministic divergence occurs.

Following completion of the 50-seed Discovery evaluation: **STOP. Do not automatically qualify, do not submit to Kaggle, and do not modify frozen live assets. Await user review.**
