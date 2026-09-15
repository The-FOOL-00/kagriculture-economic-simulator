# DEVELOPMENT EXPERIMENT REGISTRY (POST-AUDIT 2.2)
## Centralized Immutable Registry of Historical Benchmarks and Pre-Registered Development Experiments

**Governing Standard**: Audit 2.2 Final Evidence Base ([`AUDIT2_2_FINAL_EVIDENCE_BASE.md`](file:///c:/Users/Sundareswaran/Kagriculture/AUDIT2_2_FINAL_EVIDENCE_BASE.md))  
**Multiple Testing Standard**: Section 20, 21, and 22 Experiment Design Rules  
**Date**: 2026-09-11  
**Status**: **ACTIVE REGISTER**

---

## 1. Registry Operating Protocol

To eliminate publication bias, p-hacking, and post-hoc narrative invention:
1. **Pre-Registration Required**: Every new experiment must be entered into this registry **BEFORE** execution, specifying hypothesis, variant, control, seed set, partition, primary metric, and stop rule.
2. **Immutable Experiment Statuses**:
   - `DISCOVERY`: Hypothesis generation and exploratory sweeps.
   - `QUALIFICATION`: Confirmatory testing of frozen candidate variants.
   - `HOLDOUT`: Final unbiased evaluation on unseen seeds. Never accessed during tuning.
   - `CONFIRMED`: Statistically validated improvement across partitions without tail explosion.
   - `FAILED`: Statistically inferior or broken variant. Preserved permanently.
   - `INCONCLUSIVE`: Empirical result within noise margin ($p > 0.05$ or confidence interval spanning zero).
   - `RETRACTED`: Methodologically invalid or refuted experiment permanently decommissioned.
3. **No Hidden Variants**: All tested code branches, parameter sweeps, and negative trials must be preserved in this table.

---

## 2. Master Experiment Registry Table

| ID | Hypothesis | Variant | Control | Seeds | Partition | Metric | Result | Status |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- | :--- | :---: |
| **`EXP-HIST-01`** | `ClosedLoopAgentV2` outperforms `Dmitrii-LB2800` across diverse game seeds. | `ClosedLoopAgentV2` | `Dmitrii-LB2800` | 150 (300 matches) | Discovery (50), Qual (50), Hold (50) | Paired Margin ($), Win Rate (%), Student's $t$, 95% CI | Mean: +$24.61, Median: +$58.00, $t=1.8078$, $p=0.0727$, 95% CI `[-$2.29, +$51.52]`, WR: 54.67%. Spans zero. | **INCONCLUSIVE** |
| **`EXP-HIST-02`** | Pure strawberry allocation achieves the highest risk-adjusted cash among static crop allocations. | 12 Crop Grids (19S/0T to 0S/19T) | `Dmitrii-LB2800` | 50 (100 matches) | Discovery (50000–50049) | Mean Cash ($), Margin ($), Win Rate, Downside Risk | 19S/0T ranked #1 (Mean: $97,026.17, Margin: +$24.98, WR: 59.0%, Downside: 56.72). Tomato monotonically degrades margin. | **CONFIRMED** (Discovery Scoped) |
| **`EXP-HIST-03`** | Specializing in Day-11 Tomato planting on Pizza worlds yields +$3,942 alpha. | Day-11 Tomato Planting Overlay | V2 Strawberry Default | 6 | Ad-hoc (Seed 50042 + 5 Pizza Seeds) | Net Cash Margin ($) | Cherry-picked: Seed 50042 was +$3,942, but 6-seed ensemble was -$5,382.67. 18/18 parameter sweeps negative. | **RETRACTED** |
| **`EXP-HIST-04`** | Raising shed headroom threshold from 88 to 96 with feed reservation prevents premature resource purges. | Shed Threshold 96 + Feed Reserve | Shed Threshold 88 (`ClosedLoopAgentV1`) | 100 | Discovery (50), Qualification (50) | Resource Waste Rate, Feed Shortage Events | Feed purges reduced to 0; fertilizer inventory preserved into late-game; margin protected. | **CONFIRMED** |
| **`EXP-HIST-05`** | No exploitable resource slack exists anywhere in the V2 strawberry schedule. | Secondary Crop Additive Arm (`run_additive_investigation.py`) | V2 Base | 50 | Discovery (50000–50049) | Additive Net Cash ($) | Invalid trial: test script failed to water/harvest secondary crops and hired unbudgeted workers daily. Slack question remains open. | **RETRACTED** |
| **`EXP-HIST-06`** | Dynamic adaptive switching (`ClosedLoopAgentV3`) improves macro performance over static V2. | `ClosedLoopAgentV3` | `Dmitrii-LB2800` & V2 | 150 | Discovery (50), Qual (50), Hold (50) | Paired Margin ($), Win Rate, Tail Loss | Overfit discovery (+264.46), tied qual ($0.00), collapsed on holdout (-$41.64 vs V2, 4.0% WR, worst loss -$2,082). | **FAILED** |
| **`EXP-HIST-07`** | Step 696 order truncation is the causal root cause of V2 loss on Seed 50081. | Step 696 Order Queue Analysis | Unmodified Replay | 1 | Seed 50081 | Cash Deficit Step Timing ($) | Refuted: V2 was already down -$292 before Step 696 due to Step 164 cash divergence and Step 217 sheep failure. Truncation was a symptom. | **RETRACTED** |
| **`EXP-HIST-08`** | Live tournament losses were caused by an "$800 dawn hiring collapse". | Replay Parser Telemetry (`reconstruct_live_losses.py`) | Live Tournament Match | 1 | Episode 107543042 | Dawn Cash ($), Hands Hired, Fibonacci Costs | Refuted: Dawn cash was $9,847, hired 9 hands, paid $88 Fibonacci. Claim caused by dictionary parser error (`units` vs `hands`). | **RETRACTED** |
| **`EXP-DEV-001`** | **RQ1: Dynamic Crop Portfolio**: Conditioning planting on revealed town shops (Days 3 & 6) outperforms static 19S/0T strawberry baseline without increasing downside tail variance. | `dev_001_dynamic_portfolio` | 19S/0T Static Baseline & `ClosedLoopAgentV2` | 50 Discovery (100 matches) | Discovery (50000–50049) | Paired Margin ($), $p_{05}$ Tail Risk ($), Win Rate (%) | Mean Margin: +$265.18 (100% dependent on Seed 50004 outlier +$15,264; 10% trimmed mean +$0.40; 42/50 seeds tied V2). Worst loss: -$2,388.00 (Seed 50018 tomato substitution under late strawberry boom). Failed -$800 tail limit. Forensic audit: RETAIN FAILURE / CORRECT INTERPRETATION. | **FAILED** |
| **`EXP-DEV-002`** | **RQ2: Hedged Adaptive Crop Portfolio**: Enforcing a Bedrock Strawberry Floor (>= 13 plants) and capping Day-11 Tomato substitution to <= 6 tiles captures revealed town demand without catastrophic downside exposure. | `dev_002_hedged_portfolio` | `ClosedLoopAgentV2` & 19S/0T Baseline | 50 Discovery (100 matches) | Discovery (50000–50049) | Paired Margin ($), $p_{05}$ Tail Risk ($), Worst Loss ($), Win Rate (%) | Mean Margin: +$250.06, Median: +$0.00, Worst Loss: -$11.00 (vs -$2,388 in DEV-001; 99.5% tail risk reduction). Seed 50018: +$3,820.00. WR vs Dmitrii: 68.0%. Discovery Gating PASSED. | **QUALIFIED (DISCOVERY)** |
| **`EXP-DEV-003`** | **RQ3: Controlled Spatial & Action Slack**: Utilizing physical vacant tiles on Days 11–12 with properly watered and harvested secondary cycles generates positive net terminal cash. | `dev_003_controlled_slack_arm` | Unmodified `ClosedLoopAgentV2` (Controlled Workers & Cash) | 50 Discovery, 50 Qual | Discovery $\to$ Qualification | Incremental Net Cash ($), Core Strawberry Yield Preservation | *Pre-Registered (Pending Execution)* | **DISCOVERY** |
| **`EXP-DEV-004`** | **RQ4: World Regime Downside Resilience**: Maintaining dynamic cash reserves and targeted hedging eliminates catastrophic tail losses on adverse shop worlds (e.g. Pure Straw gluts, Pet Cafe / Yarn Store). | `dev_004_robust_hedging` | `ClosedLoopAgentV2` | 150 Paired Seeds | Discovery (50), Qual (50), Hold (50) | Worst Paired Loss ($), $p_{05}$ Margin ($), Cash Buffer at Step 217 | *Pre-Registered (Pending Execution)* | **DISCOVERY** |
| **`EXP-DEV-005`** | **RQ5: Micro-Architectural Dissection**: Monte Carlo terminal planning at Steps 712–718 isolates the terminal realization gap between V2 and Dmitrii without adopting static macro tape. | `dev_005_mc_terminal_closure` | Base `ClosedLoopAgentV2` (Pass at 712–718) | 150 Paired Seeds | Discovery (50), Qual (50), Hold (50) | Terminal Step Cash Delta ($), Net Game Margin ($) | *Pre-Registered (Pending Execution)* | **DISCOVERY** |

---

## 3. Pre-Registered Development Experiment Protocols (RQ1 to RQ5)

### 3.1 EXP-DEV-001 (RQ1: Dynamic vs. Static Allocation)
- **Primary Hypothesis**: A dynamic policy that evaluates revealed town shops at Day 3 (Step 72) and Day 6 (Step 144) to select between Strawberry Bedrock and targeted complementary production will achieve a positive paired margin over static 19S/0T with no worsening of $p_{05}$ downside.
- **Treatment**: Candidate `dev_001_dynamic_portfolio` (conditional crop selection on Days 3 and 6).
- **Control**: Static 19S / 0T Strawberry Bedrock in `ClosedLoopAgentV2`.
- **Primary Metric**: Paired Margin $(\text{Variant} - \text{Control})$ in coins.
- **Secondary Metrics**: $p_{05}$ lower-tail quantile, Win Rate (%), Total Farm Cash ($).
- **Partition Schedule**: Evaluated first on 50 Discovery seeds (50000–50049). If and only if margin $> +\$50$ (derived from the empirical TOST equivalence bound) and $p_{05}$ is non-inferior, advance to Qualification (50050–50099). Holdout (50100–50149) remains locked.
- **Stop Rule**: If Discovery paired margin $< 0$ or worst loss $< -\$500$, mark `FAILED`.
- **Outcome**: FAILED. Worst loss was -$2,388.00 on Seed 50018 (exceeded -$800.00 tail limit). Decommissioned.

### 3.2 EXP-DEV-002 (RQ2: Hedged Adaptive Crop Portfolio)
- **Primary Hypothesis**: Enforcing a Bedrock Strawberry Floor of $\ge 13$ plants and capping Day-11 Tomato substitution to $\le 6$ tiles captures town demand surplus while preventing the catastrophic tail failure observed in EXP-DEV-001.
- **Governing Protocol**: `DEVELOPMENT_EXPERIMENT_PROTOCOL_V1_1.md` (SHA-256: `735ad844...`).
- **Treatment**: Candidate `dev_002_hedged_portfolio` ([`candidates/closed_loop_architecture/dev_002_hedged_portfolio.py`](file:///c:/Users/Sundareswaran/Kagriculture/candidates/closed_loop_architecture/dev_002_hedged_portfolio.py)).
- **Controls**: `ClosedLoopAgentV2` (Control A), Static 19S/0T Baseline (Control B), `Dmitrii-LB2800` (Reference).
- **Primary Metric**: Paired Margin vs `ClosedLoopAgentV2` in coins.
- **Gating Threshold**: Advance to Stage 4 (Qualification) if $\Delta \mu > +\$50.00$, $p_{05} \ge -\$200.00$, and worst loss $\ge -\$800.00$.
- **Discovery Outcome**: Mean Margin: +$250.06 coins, Median: +$0.00, $p_{05}$: +$0.00, Worst Loss: -$11.00 (vs -$2,388 in DEV-001). Seed 50018: +$3,820.00 (inverted from loss). WR vs Dmitrii: 68.0%. Discovery Gating passed. Qualified for Qualification Stage.

### 3.3 EXP-DEV-003 (RQ3: Controlled Spatial / Action Slack)
- **Primary Hypothesis**: Exploiting vacant farm tiles on Days 11–12 with a secondary crop that receives dedicated watering and harvesting actions increases net profit without cannibalizing core strawberry operations.
- **Treatment**: Controlled additive crop schedule with dedicated worker action allocation.
- **Control**: Unmodified `ClosedLoopAgentV2` with identical worker hiring and cash expenditure.
- **Primary Metric**: Net incremental profit $\Delta \text{Profit} = \text{Added Revenue} - (\text{Seed Cost} + \text{Added Water/Harvest Action Cost})$.
- **Stop Rule**: If core strawberry yield drops by $\ge 1$ unit or net profit is negative, mark `FAILED`.

### 3.4 EXP-DEV-004 (RQ4: World Regime Downside Resilience)
- **Primary Hypothesis**: Enforcing a $1,000 cash floor at Day 9 dawn (Step 216) protects livestock acquisition on tight cash seeds (e.g. Seed 50081), raising $p_{05}$ margin.
- **Treatment**: Dynamic liquidity reservation rule ($\text{CashReserve} \ge \$1,000$ prior to Day 9 pasture stocking).
- **Control**: Base `ClosedLoopAgentV2` liquidity rule.
- **Primary Metric**: Seed 50081 margin, $p_{05}$ margin across 150 seeds.
- **Stop Rule**: If mean margin drops by $> \$30$ across the ensemble, liquidity reservation is too conservative.

### 3.5 EXP-DEV-005 (RQ5: Dmitrii Micro-Architectural Dissection)
- **Primary Hypothesis**: Integrating a 64-simulation Monte Carlo terminal planner at Steps 712–718 into `ClosedLoopAgentV2` extracts terminal worker value, closing the gap with Dmitrii on pure Strawberry worlds.
- **Treatment**: Monte Carlo terminal planner overlay at Steps 712–718. (Step 217 liquidity buffer is decoupled and tested strictly in EXP-DEV-004).
- **Control**: Base `ClosedLoopAgentV2` executing PASS at Steps 712–718.
- **Primary Metric**: Net cash gain at Steps 712–718.
- **Stop Rule**: If computational latency exceeds 800ms per step or terminal gain $< \$20$, mark `INCONCLUSIVE`.

---

## 4. Experiment Registry Maintenance Rules

1. Every newly executed script must log its run ID, exact git commit / code hash, timestamp, and results to this file.
2. Under no circumstances may an experiment be executed on Holdout seeds before the candidate is formally frozen.
3. Negative results must be reported with equal prominence to positive results.
