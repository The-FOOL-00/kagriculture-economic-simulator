# DEVELOPMENT EXPERIMENT PROTOCOL V1.2
## EXP-DEV-003: Conditional Opportunity-Value Specialization over V54++ Residual Preemption
**Governing Standard**: Strict Zero-Leakage & Anti-Contamination Covenant  
**Experiment Version**: EXP-DEV-003 Protocol V1.2 (Post-Recovery Certified)  
**Date Established**: 2026-09-14  
**Auditor**: Autonomous Verification Engine (Zero-Leakage Governance)  
**Status**: **FROZEN & IMMUTABLE — DO NOT MODIFY**

---

## 1. Experiment Identity & Core Research Question

- **Experiment Identifier**: `EXP-DEV-003`
- **Formal Title**: Conditional Opportunity-Value Specialization over V54++ Residual Preemption
- **Discovery Partition**: `245000` to `245049` ($N=50$ contiguous seeds, 100 balanced Common Random Number matches)
- **Primary Research Question**:
  > *"Can an information-conditioned agricultural/shop specialization policy add generalizable economic value to the current best V54++ residual-preemption architecture, without materially degrading its downside protection?"*
- **Experiment Classification**: This is an independent, new experimental investigation. It is NOT DEV-001, NOT DEV-002, and NOT a continuation or retuning of the failed DEV-002 qualification run.

---

## 2. Authoritative Frozen Baseline Specification

The primary control baseline for EXP-DEV-003 is the current best deployment candidate in the repository:
- **Baseline File**: [`candidates/compiled_v54_plus_residual.py`](file:///c:/Users/Sundareswaran/Kagriculture/candidates/compiled_v54_plus_residual.py)
- **Kaggle Submission Reference**: Submission `56146971`
- **Exact File Size**: `338,100 bytes`
- **Recomputed Authoritative SHA256**:
  ```text
  18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb
  ```
- **Frozen Baseline Properties**:
  Executes the proven V54++ macroeconomic route tables coupled with adaptive residual market preemption (`preempt_money_deficit = 2000.0`, `preempt_minimum_delta = 4.0`, `preempt_maximum_batch = 12`).

### Independent Frozen Control Verification:
- **Control File**: [`candidates/compiled_v54_plus_shop.py`](file:///c:/Users/Sundareswaran/Kagriculture/candidates/compiled_v54_plus_shop.py)
- **Kaggle Submission Reference**: Submission `56146947`
- **Exact File Size**: `337,768 bytes`
- **Recomputed Authoritative SHA256**:
  ```text
  f651ccd220e701968bc33579812d8917da63f5b0582f2fd0d363fa6a16ffd8b8
  ```

---

## 3. Simulator Compatibility & Baseline Validation

1. **Local Simulator Engine**: Bit-exact C++ simulator `kagsim` (Engine Version `1.32.7`), identical to official Kaggle environment.
2. **Interface Parity**: `compiled_v54_plus_residual.py` natively exposes `agent(obs, configuration=None)`.
3. **Execution Verification**: Tested in `kagsim.Game(100)` self-play. Executes all 719 steps with 0 errors, generating bit-exact symmetric rewards ($55862.0$ vs $55862.0$).
4. **Adapter Invariant**: Zero wrappers or adapters are required. The baseline executes bit-for-bit identical to its live Kaggle submission.

---

## 4. Observational Live Submission Evidence (Diagnostic Only)

Live Kaggle competitive telemetry across 349 total matches (2026-09-10 to 2026-09-14) provides observational context:
- **Submission 56146971 (Residual)**: Elo **`1499.1`**, Rank **`2,368 / 9,001`** (Top 26.31%), Win Rate **`44.32%`** ($N=185$), Mean Cash **`88,788.5`**.
- **Submission 56146947 (Control)**: Elo **`1453.0`**, Rank **`2,462`** equivalent (Top 27.35%), Win Rate **`42.68%`** ($N=164$), Mean Cash **`83,390.1`**.
- **Observational Delta**: $+46.1$ Elo, $+5,398.4$ mean cash, $+29,503$ peak upside, $+7,134$ floor protection.
- **Claim Discipline**: The live evidence is strongly consistent with residual preemption being beneficial and motivates controlled testing against the frozen residual baseline. Live results are strictly diagnostic and will NEVER be used to tune treatment parameters.

---

## 5. Partitions & Quarantines

### 5.1 Certified Virgin Discovery Partition
- **Range**: **`245000` to `245049`** ($N=50$ contiguous seeds)
- **Provenance Status**: **100% Certified Virgin** (0 workspace file hits, 0 Git commits, 0 result records, 0 range overlaps, 0 stride overlaps).
- **Evaluation Design**: Paired Common Random Numbers (CRN), 100 total matches:
  - Match A: Seed $s$, Player 0 = Candidate, Player 1 = Baseline
  - Match B: Seed $s$, Player 0 = Baseline, Player 1 = Candidate

### 5.2 Absolute Quarantines
- **`50000–50049`**: Used Discovery — **Quarantined**.
- **`50050–50099`**: Qualification Partition — **Strictly Quarantined for confirmatory qualification only**.
- **`50100–50149`**: Contaminated Benchmark — **Permanently Decommissioned**.
- **`50000–50499`**: Broader Historical Census — **Quarantined**.
- **`214200–214249`**: Certified Virgin Final Holdout (`HOLDOUT-COHORT-V1`) — **Completely Quarantined. Zero access, zero simulations, zero inspection.**

---

## 6. Treatment Specification: `dev_003_conditional_specialization`

- **Treatment Artifact File**: [`candidates/closed_loop_architecture/dev_003_conditional_specialization.py`](file:///c:/Users/Sundareswaran/Kagriculture/candidates/closed_loop_architecture/dev_003_conditional_specialization.py)
- **Architectural Composition**:
  $$\text{Treatment} = \text{V54++ Residual Baseline} + \text{Opportunity-Value Conditional Gating Overlay}$$
- **Default Invariant**: In all ambiguous, unpromising, or unverified states, the treatment executes **100% default V54++ baseline behavior**.
- **Preservation Invariant**: The overlay **MUST NOT** remove, weaken, or modify the residual-preemption engine (`preempt_money_deficit = 2000.0`, `preempt_minimum_delta = 4.0`, `preempt_maximum_batch = 12`).

### 6.1 Decision Checkpoints
Grounded directly in the game mechanics (`townShopUnlockInterval = 3` turns/day = 24):
- **Checkpoint 1**: Day 3 (Step 72) — 1st Town Shop Unlocks
- **Checkpoint 2**: Day 6 (Step 144) — 2nd Town Shop Unlocks
- **Checkpoint 3**: Day 9 (Step 216) — 3rd Town Shop Unlocks
- **Checkpoint 4**: Day 12 (Step 288) — 4th Town Shop Unlocks

### 6.2 Information Containment Standard
The opportunity-value gate evaluates **ONLY** current observable state at decision step $t$:
- `obs["town"]["unlocked_shops"]`: Unlocked shop identities.
- `obs["farms"][seat]["money"]`: Current liquid cash.
- `obs["farms"][seat]["tiles"]`: Current tile allocation and crop states.
- `obs["town"]["market"]["prices"]`: Current observable market prices.
- Elapsed step/day.
- **FORBIDDEN**: Future shops, future prices, terminal score, opponent actions, replayed trajectories, offline data. Explicit assertion checks guard against future state leakage.

### 6.3 Mathematical Opportunity-Value Model
At checkpoint step $t$, for candidate crop specialization $C \in \{\text{TOMATO}, \text{CARROT}, \text{WHEAT}\}$ corresponding to an active town shop (e.g. Pizza Shop $\implies$ Tomato, Pet Cafe $\implies$ Carrot, Bakery $\implies$ Wheat):
1. **Expected Specialization Revenue $\mathbb{E}[R_{\text{spec}}(C)]$**:
   $$\mathbb{E}[R_{\text{spec}}(C)] = k_{\text{spec}} \cdot N_{\text{harvests}}(C, t_{\text{remain}}) \cdot Y_{\text{cycle}}(C) \cdot P_{\text{eff}}(C)$$
   where $k_{\text{spec}} = 4$ tiles, $P_{\text{eff}}(C) = \min(P_{\text{shop}}(C), P_{\text{market}}(C))$.
2. **Expected Baseline Revenue Forgone $\mathbb{E}[R_{\text{base}}]$**:
   $$\mathbb{E}[R_{\text{base}}] = k_{\text{spec}} \cdot N_{\text{harvests}}(\text{Straw}, t_{\text{remain}}) \cdot Y_{\text{cycle}}(\text{Straw}) \cdot P_{\text{eff}}(\text{Straw})$$
3. **Direct Input Seed Costs**:
   $$\text{Cost}_{\text{seed}} = k_{\text{spec}} \cdot \text{SeedPrice}(C)$$
4. **Liquidity Risk Penalty $\mathcal{R}$**:
   $$\mathcal{R} = \lambda \cdot \max(0, L_{\text{min}} - \text{money}) + k_{\text{spec}} \cdot \text{SwitchingFriction}$$
5. **Net Incremental Opportunity Value $\Delta \mathbb{E}[V]$**:
   $$\Delta \mathbb{E}[V] = \mathbb{E}[R_{\text{spec}}(C)] - \mathbb{E}[R_{\text{base}}] - \text{Cost}_{\text{seed}} - \mathcal{R}$$

### 6.4 Activation Rule
$$\text{State}(t) = \begin{cases} 
\text{SPECIALIZE}(C, k=4) & \text{if } \Delta \mathbb{E}[V] \ge \tau \text{ AND } \text{money} \ge L_{\text{min}} \\
\text{BASELINE (V54++)} & \text{otherwise}
\end{cases}$$

---

## 7. Frozen Parameter Registration (Zero Post-Hoc Tuning)

All newly introduced parameters are frozen prior to simulation:
- **Opportunity-Value Threshold ($\tau$)**: `1500.0` coins (Requires at least $+1500$ net expected advantage over proven baseline).
- **Risk Penalty Multiplier ($\lambda$)**: `0.25`
- **Minimum Liquidity Floor ($L_{\text{min}}$)**: `100.0` coins (Calibrated to V54++ tight early reinvestment cashflow; ensures seed purchases never starve labor or daily wages).
- **Specialization Tile Allocation ($k_{\text{spec}}$)**: `4` tiles (Conservative cap preserving $\ge 12$ tiles for bedrock Strawberry).
- **Switching Friction**: `200.0` coins.
- **Inherited V54++ Parameters**: 100% frozen from `compiled_v54_plus_residual.py`.

---

## 8. Primary & Secondary Metrics

### Primary Metric:
- **Paired Mean Final-Cash Delta**:
  $$\bar{\Delta} = \frac{1}{N} \sum_{s=1}^{50} \frac{1}{2} \left[ (\text{Cash}_{\text{cand}}^{s, 0} - \text{Cash}_{\text{base}}^{s, 1}) + (\text{Cash}_{\text{cand}}^{s, 1} - \text{Cash}_{\text{base}}^{s, 0}) \right]$$

### Mandatory Secondary & Tail Statistics:
- Median, SD, SE, Student's $t$, two-sided $p$-value, 95% CI.
- Trimmed mean (10%), percentiles (p01, p05, p10, p25, p50, p75, p90, p95, p99), Min, Max.
- Win/Loss/Tie count, Win Rate, Downside Frequency ($\Delta < 0$).
- Outlier Sensitivity: Total surplus, Top-1 contribution, Top-2 contribution, Mean excluding best seed, Mean excluding worst seed, Mean excluding top 2 seeds.

---

## 9. Preregistered Development Success Criteria (Gates A–E)

| Gate | Criterion | Numerical Threshold | Justification |
| :--- | :--- | :---: | :--- |
| **Gate A** | Positive Mean Paired Delta | $\bar{\Delta} \ge +\$30.00$ | Minimum economically meaningful improvement to justify architectural complexity over V54++. |
| **Gate B** | Positive Win Rate | $\text{Win Rate} \ge 50.0\%$ | Candidate must win at least half of paired seeds against V54++. |
| **Gate C** | Downside Floor Protection | $\text{Worst Paired Loss} \ge -\$350.00$ | Strict risk containment; prevents catastrophic blowups like DEV-002. |
| **Gate D** | Outlier Non-Dominance | $\text{Mean Excl. Best Seed} > +\$0.00$ | Net positive effect must not depend exclusively on a single jackpot seed. |
| **Gate E** | Selective Gate Firing | $5 \le N_{\text{active}} \le 35$ seeds | Proves the gate fires conditionally rather than never (0) or blindly (50). |

---

## 10. Epistemic Classification Taxonomy

- **ROBUST DISCOVERY**: Passes Gates A, B, C, D, E with $p < 0.10$. Eligible for Qualification Protocol.
- **PROMISING**: Passes Gates A and B with positive trimmed mean, but marginal tail breach (Gate C).
- **SIGNAL**: Positive mean ($\bar{\Delta} > 0$) but fails Gate B or D. Requires diagnostic investigation.
- **FAILURE**: $\bar{\Delta} \le \$0.00$ or severe downside breach. Null hypothesis H0 accepted.
