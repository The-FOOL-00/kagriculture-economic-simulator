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
| **`EXP-V32-P8`** | **History Disambiguation & Strategic Macro-Policy Audit**: Sequence memory is necessary to disambiguate teacher actions across ambiguous states. | History Horizons $H \in \{0, 2, 4, 8, 16, 32\}$ + Counterfactual Swaps | `V32-P7-Prefix4` & `A7` Baseline | 240 Demonstration Seats | Development (249635–249649) | Conditional Entropy $H(A_t \mid t)$, Action Purity, Paired Mechanism Margins | Refuted: $H(A_t \mid t) = 0.0000$ bits across all 240 seats. Teacher is open-loop tape. Sequence memory closed (Hard NO-GO). A7 +$1,286 melon wash mechanism confirmed. Pivot to Hierarchical Macro-Economic Hybrid approved. | **CONFIRMED (STOP MEMORY / PIVOT MACRO)** |
| **`EXP-V32-P9`** | **Hierarchical Macro-Economic Hybrid (HMEH) Promotion**: 5-layer macro architecture matches or exceeds A7 while maintaining legality. | `HMEH-0` through `HMEH-4` | `A7` Incumbent Control | 120 Tournament Legs | Development (249675–249684) | Paired Margin ($), Win Rate, Legality (0 crashes/illegal) | HMEH-0 achieves 100% exact parity with A7 (+$0.00 delta across 120 legs). Adaptive labor and selling delays regressed. Release candidate frozen at `candidates/v32_hmeh_release/main.py`. | **CONFIRMED (HMEH-0 = A7)** |
| **`EXP-V32-P10`** | **Sparse Residual Override on Frozen A7**: Observable opponent/regime-conditioned residual overrides improve paired economics over A7 without downside tail risk. | Residuals `R01`, `R02`, `R02_B`, `R03`, `R05`, `R07` | `A7` Incumbent Control | 160 Tournament Legs | Development (249675–249684), Fresh (249685–249694) | Paired Margin ($), Median ($), Worst-Case Loss ($), Gate G1–G9 | Refuted: R01 (-$348.35) and R02 (-$32.35) regressed; R02_B achieved +$11.10 mean on fresh seeds but suffered -$489.00 tail loss; R03/R05/R07 redundant ($0.00). Success B confirmed: Freeze A7. | **CONFIRMED (SUCCESS B: FREEZE A7)** |
| **`EXP-V32-P11`** | **Bounded Physical Terminal Path Planning**: Exact bounded physical search during steps 712–718 recovers realizable value stranded in fields/worker pockets without modifying A7 elsewhere. | `candidates/v32_p11_terminal` (Physical Search B=16..128) | `A7` Incumbent Control | 120 Tournament Legs | Development (249675–249684), Fresh (249685–249694) | Paired Margin ($), Terminal Cash Delta, Stranded Inventory ($), Gate 1–12 | Refuted: The -$1,167 gap on seed 249677 was caused by mid-game price shocks (steps 614, 697, 709); A7 out-earned Dmitrii by +$184 in terminal window. A7 leaves $0.00 carried, $0.00 in shed, and only $10–$21 residual fertilizer on board. Unconstrained search caused -$211 regression. Cargo-protected search safely abstains ($0.00 delta across all 120 legs). Success B confirmed: Permanently Freeze A7 for final submission. | **CONFIRMED (SUCCESS B: PERMANENT FREEZE A7)** |
| **`EXP-V32-RLX2`** | **Strategic Macro RL & Exact Search**: A learned macroeconomic strategic policy (PPO / Exact Search / Hybrid) detecting when to follow A7 vs deviate can exceed A7 without low-level imitation. | `candidates/v32_rlx2` (RLX2-F0 to F11, S2 state, 10 macro actions, H=4) | `A7` Incumbent Control | 36 Tournament Legs (dev) + 132 Search Targets | Development (249675–249677), Train (249635–249637) | Paired Margin ($), Win Rate (%), Value Loss, Gate 1–8 | Exact counterfactual search (RLX2-F5) discovered up to +$11,179 alpha at Step 288 (45.5% positive targets). However, end-to-end neural execution (RLX2-F7) suffers sequential policy drift; uncoordinated deviations desynchronize A7's delicate chore tape, losing -$89,996.4 mean margin across 6 league opponents (11.1% WR). Gates 1–4 FAILED. Permanent NO-GO; A7 frozen for Slot B. | **FAILED (STOP RULE 82: PERMANENT FREEZE A7)** |

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

### 3.6 EXP-V32-P11 (Bounded Physical Terminal Path Planning)
- **Primary Hypothesis**: During steps 712–718, a bounded exact physical search can identify legal worker/farmer action sequences that collect additional realizable value without interfering with required baseline liquidation, strictly improving final cash over A7.
- **Treatment**: `candidates/v32_p11_terminal` (Bounded Physical Terminal Planner, budgets 16–128).
- **Control**: Unmodified protected incumbent `A7` (`candidates/v30_a7_standalone/main.py`).
- **Primary Metric**: Paired terminal cash delta ($\text{Candidate} - \text{A7}$), stranded physical value at step 719 ($), Promotion Gates 1–12.
- **Stop Rule**: Stop immediately if the -$1,167 gap cannot be reproduced, physical search produces no value, candidate creates tail losses, or planner interferes with normal liquidation.
- **Empirical Outcome**:
  - The -$1,167 gap on seed 249677 was reproduced down to the cent, but forensic audit proved that A7 was already behind -$1,351 at step 712 due to mid-game price shocks, and A7 out-earned Dmitrii by +$184 in the terminal window ($2,600 vs $2,416).
  - A7 leaves $0.00 carried cargo and $0.00 in the shed across all seeds at step 719, with only $10–$21 of low-value residual fertilizer on the field.
  - Unconstrained physical search caused severe cargo-stranding losses (-$211.00).
  - Cargo-protected physical search safely abstains ($0.00 delta across all 120 tournament legs).
  - **Verdict**: SUCCESS B CONFIRMED. A7 is permanently frozen for final competition submission. Terminal search branch permanently closed.

### 3.7 EXP-V32-RLX2 (Strategic Macro Reinforcement Learning & Exact Search Program)
- **Primary Hypothesis**: By elevating the action abstraction from atomic farmer actions to 10 discrete macroeconomic strategic intents (with Action 0 = `FOLLOW_A7`) executed over $H=4$ ticks with a fail-closed safety enforcer, a learned policy (PPO, Exact Simulator Search, or Search-Initialized Hybrid) can discover profitable deviations from A7 during mid-game regime shifts without suffering the brittleness of low-level behavior cloning.
- **Treatments**:
  - `RLX2-F0`: Environment Vectorization & Throughput Benchmark (Single-core 134.8 SPS, 8 workers 454.9 SPS).
  - `RLX2-F1`: Macro Action-Space & Legal Mask Verification (100% verified, Action 0 bit-identical to A7).
  - `RLX2-F2`: PPO Baseline (MLP 128x128, S2 71-dim state, R1 delta reward). Value loss dropped 0.0644 -> 0.0026, but exploration collapse reduced cash from ~$120k to ~$1.2k.
  - `RLX2-F3`: Opponent League PPO (Uniform mixture over A7, V22R1, V3, Dmitrii, V54, SYN_AGG).
  - `RLX2-F4`: A7-Relative Potential-Shaped Reward Study (Preserves terminal optimization but increases credit assignment variance).
  - `RLX2-F5`: Exact Simulator Search Target Generation (132 points across seeds 249635..249637; 60 points / 45.5% strictly positive delta over A7; peak +$11,179.00 at Step 288 via `EXPAND_LAND`).
  - `RLX2-F6`: Supervised Strategic Target Pretraining (Cross-entropy loss 6.10 -> stable; verified policy initialization).
  - `RLX2-F7`: Search-Initialized PPO Hybrid (Pretrained on 132 targets; Iter 1 $109k, Iter 3 $101k, Iter 4 $93k; policy drift toward desynchronization).
  - `RLX2-F8`: Hybrid Iterative Loop Analysis (Confirmed that sequential interventions break open-loop chore continuity).
  - `RLX2-F9`: Multi-Seed Robustness Evaluation (Confirmed uniform failure mode across training and development seeds).
  - `RLX2-F10`: Adversarial Stress Testing (Stress on cash, price shocks, and opponent supply surges).
  - `RLX2-F11`: Independent Master Tournament Benchmark (36 mirrored legs across `V32_DEV_HIST` vs 6-opponent league: Mean $13,702.5 vs A7 $103,698.9, Paired $\Delta = -$89,996.4, WR 11.1%).
- **Control**: Unmodified protected incumbent `A7` (`candidates/v30_a7_standalone/main.py`, SHA-256 `51c1d25245f68dd8de66b355f2ad6ca1d79de8af02efed521a5a82f7be69ce3f`).
- **Primary Metric**: Paired terminal cash delta ($\text{Candidate} - \text{A7}$), Win Rate (%), Gate 1–8 compliance.
- **Stop Rule (Section 82)**: If PPO, Search, and Hybrid produce no robust gain over A7 on held-out development, freeze A7 permanently and conclude the research program without inventing further speculative RL branches.
- **Empirical Outcome**:
  - Exact counterfactual search proved that massive macroeconomic headroom exists in A7's mid-game (up to +$11,179.00).
  - However, end-to-end neural macro policies cannot maintain the strict micro-choreography required to monetize these deviations; sequential policy drift creates catastrophic compound errors (-$89,996.4 delta).
  - Promotion Gates 1, 2, 3, and 4 FAILED.
  - **Verdict**: NO-GO. A7 permanently frozen for final competition submission Slot B; V22R1 permanently frozen for Slot A. RL-X2 program permanently closed per Rule 82.

### 3.8 EXP-V32-P12 (Sparse Options & Physical Resynchronization Architecture)
- **Primary Hypothesis**: Strategic deviations from A7 yield large local economic headroom (+11.1k in RL-X2 exact search), but continuous control desynchronizes worker choreography. By capturing these opportunities as sparse, short ($H=4$ ticks) exact options with a mandatory return to A7 and an explicit physical resynchronization gate ($D_{\text{resync}} = 0$), the agent can capture local alpha without destabilizing physical choreography.
- **Treatments**:
  - `P12-01`: Search Alpha Reproduction & Classification (100% of 60 RL-X2 positive targets reproduced; 100% achieved $D_{\text{resync}} = 0$ within 28 ticks).
  - `P12-02`: Single-Option Bounded Controller ($H=4$, forced return to A7; produced +$7,227.20/leg on training seeds).
  - `P12-03`: Sparsity & Spacing Ablation ($F_0, F_1, F_2, F_3$; spacing 24, 48, 72 ticks; verified $F_1$ max 1 option is strictly optimal; stacking options adds $0.00 marginal value).
  - `P12-04`: Horizon Ablation ($H \in \{2, 4, 6, 8\}$; $H=4$ optimal; $H=8$ causes worker displacement and -$51,790.00 collapse).
  - `P12-05`: Exact Search-Gated Architecture on Fresh Seeds (`P12_Search_Gated`).
  - `P12-06`: Supervised Option Selector (`P12_Supervised_Selector`, 2-layer MLP, 100.0% precision, 0.0% false positives, 0.12 ms latency).
  - `P12-07`: PPO Macro Option Selector (`P12_PPO_Selector`, collapsed to absorbing $a=0$ `FOLLOW_A7`, delta = +$0.00).
  - `P12-08`: Multi-Seed Selector Training (Seeds 42, 137, 2026; 100% precision replicated).
  - `P12-09`: Adversarial Boundary Perturbation Audit (10/10 stress tests passed with 100% fail-safe abstention to A7).
  - `P12-10`: Independent Master Benchmark (180 match legs across fresh DEV seeds 249677–249681, all 6 league opponents, seats 0 and 1).
- **Control**: Unmodified protected incumbent `A7` (`candidates/v30_a7_standalone/main.py`, SHA-256 `51c1d25245f68dd8de66b355f2ad6ca1d79de8af02efed521a5a82f7be69ce3f`).
- **Primary Metric**: Paired terminal cash delta ($\text{Candidate} - \text{A7}$), tail risk ($\text{Min } \Delta$), physical resynchronization distance ($D_{\text{resync}}$), Gates G1–G12.
- **Stop Rule (Sections 69 & 71)**: If options produce negative delta on fresh seeds or unacceptable tail losses ($\Delta < -\$1,000$), freeze A7 permanently and do not promote options.
- **Empirical Outcome**:
  - **Physical Choreography Invariant Proved:** 4-tick bounded options with mandatory A7 return achieved 100% resynchronization ($D_{\text{resync}} = 0$) within 28 ticks, completely solving the worker desynchronization failure mode of RL-X2.
  - **Competitive Market Saturation Failure Mode Discovered:** While `EXPAND_LAND` is massive (+14.8k) vs non-farming opponents (`SYN_AGG`, `DMITRII`), on fresh DEV seeds facing agricultural competitors (`V54`, `V3`, `V22R1`, `A7`), the $4,000 irreversible land capex locked up liquidity while competitors flooded the town bakery. Spot wheat prices collapsed below $25, causing late-game liquidity failure.
  - **Benchmark Metrics:** `P12_Search_Gated` and `P12_Supervised_Selector` achieved Mean Cash $101,004.63 vs A7 $104,332.17 (Paired $\Delta = -\$3,327.53$), with a catastrophic tail loss of **-$26,853.00** on Seed 249679. League win rate dropped from 83.3% to 56.7%.
  - **Gate Status:** Fails Gate G3 (Tail Safety: -$26.8k vs -$1.0k threshold), Gate G5 (Fresh Seed Generalization: negative mean delta), Gate G6 (Opponent Generalization: net negative against 5/6 opponents).
  - **Verdict:** NO-GO. FREEZE A7 AS LIVE INCUMBENT FOR SLOT B. V22R1 FROZEN FOR SLOT A. P12 branch preserved as modular research artifact; research program concluded.

---

## 4. Experiment Registry Maintenance Rules

1. Every newly executed script must log its run ID, exact git commit / code hash, timestamp, and results to this file.
2. Under no circumstances may an experiment be executed on Holdout seeds before the candidate is formally frozen.
3. Negative results must be reported with equal prominence to positive results.

