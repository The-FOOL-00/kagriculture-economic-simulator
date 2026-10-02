# KAGGRICULTURE — INDEPENDENT FULL REPOSITORY RECONSTRUCTION
## Comprehensive Adversarial Audit, Evidence Reconstruction, and Scientific Ledger
**Author**: Independent Adversarial Research Auditor (Second-Model Audit)  
**Date**: 2026-09-15  
**Audit Standard**: Read-Only Forensic Verification against Primary Source Code, Git History, Cryptographic Checksums, Machine Replays, Simulation Ports, and Raw Artifacts.  
**Operational Directives Enforced**: ZERO modifications to source code, experiment results, Git history, or protocols; ZERO Kaggle submissions; ZERO executions on experimental seeds or holdouts; ZERO new candidate generation.

---

# TABLE OF CONTENTS
1. [Executive Summary](#1-executive-summary)
2. [Repository Map](#2-repository-map)
3. [Frozen Artifacts](#3-frozen-artifacts)
4. [Live Kaggle Status](#4-live-kaggle-status)
5. [Holdout / Quarantine Status](#5-holdout--quarantine-status)
6. [Governance History](#6-governance-history)
7. [Baseline and Dmitrii History](#7-baseline-and-dmitrii-history)
8. [Complete Experiment Timeline](#8-complete-experiment-timeline)
9. [EXP-DEV-001 — Dynamic Crop Portfolio](#9-exp-dev-001--dynamic-crop-portfolio)
10. [EXP-DEV-002 — Hedged Adaptive Portfolio](#10-exp-dev-002--hedged-adaptive-portfolio)
11. [EXP-DEV-003 — Conditional Opportunity-Value Specialization](#11-exp-dev-003--conditional-opportunity-value-specialization)
12. [EXP-DEV-004 — Joint Macro Production Scheduler & Gate 4 Erratum](#12-exp-dev-004--joint-macro-production-scheduler--gate-4-erratum)
13. [EXP-DEV-005 KILLTEST — Hysteresis Commitment Guard](#13-exp-dev-005-killtest--hysteresis-commitment-guard)
14. [EXP-DEV-005 — Confirmed-Shop Gated Scheduler](#14-exp-dev-005--confirmed-shop-gated-scheduler)
15. [DEV-006 HORIZON KILLTEST — Retrospective Horizon-Gate Verification](#15-dev-006-horizon-killtest--retrospective-horizon-gate-verification)
16. [DEV-006 DISCOVERY — Horizon Guard Evaluation on Fresh Seeds](#16-dev-006-discovery--horizon-guard-evaluation-on-fresh-seeds)
17. [DEV-006 QUALIFICATION — Stage 2 Confirmation on Reserved Cohort](#17-dev-006-qualification--stage-2-confirmation-on-reserved-cohort)
18. [DEV-007 CURRENT PROTOCOL — Mechanism Exposure Study](#18-dev-007-current-protocol--mechanism-exposure-study)
19. [Dmitrii Architecture Decomposition](#19-dmitrii-architecture-decomposition)
20. [Earlier Dmitrii Analysis vs Newly Discovered Information](#20-earlier-dmitrii-analysis-vs-newly-discovered-information)
21. [Current ARCH-001 Status](#21-current-arch-001-status)
22. [Rejected Hypotheses](#22-rejected-hypotheses)
23. [Surviving Hypotheses](#23-surviving-hypotheses)
24. [Evidence Hierarchy](#24-evidence-hierarchy)
25. [Frozen Ranges / Artifacts Table](#25-frozen-ranges--artifacts-table)
26. [Open Questions](#26-open-questions)
27. [Recommended Next Decision Point](#27-recommended-next-decision-point)
28. [Current State of Knowledge](#28-current-state-of-knowledge)
29. [Current Frozen State](#29-current-frozen-state)
30. [Current Experiments in Flight](#30-current-experiments-in-flight)
31. [Next Decision Required](#31-next-decision-required)

---

# 1. EXECUTIVE SUMMARY

An exhaustive, forensic, read-only audit of the entire `Kagriculture` repository was conducted to establish an uncompromised, independent source of truth for all research history, experimental iterations, governance decisions, live competition submissions, and architectural findings.

### Key Forensic Findings:
1. **Physical & Cryptographic Integrity**:
   Every critical frozen artifact specified in the audit mandate was rehashed directly from disk. **All 5 critical artifacts match their authoritative SHA-256 checksums bit-for-bit**:
   - `compiled_v54_plus_residual.py`: `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb` [PASS]
   - `compiled_v54_plus_shop.py`: `f651ccd220e701968bc33579812d8917da63f5b0582f2fd0d363fa6a16ffd8b8` [PASS]
   - `dev_005_confirmed_shop_scheduler.py`: `f52b168619e47bea6a052faff890fc84804cb39b47392d247139967f910e2a78` [PASS]
   - `dev_006_horizon_guard_scheduler.py`: `06db94e59e2c271b5490aad78fdb760bd8a250f28ec4407de2d2f6be0644f5eb` [PASS]
   - `EXP-DEV-007 PROTOCOL.md`: `d10ee1857b380ee1254a29bf9fc1a49e33c10783b9e49ef1e68beb75bab80cff` [PASS]
   Neither live submission candidate has ever been modified since deployment on 2026-09-10.

2. **Live Kaggle Baseline**:
   Our active live Kaggle portfolio consists of two standalone compiled agents deployed under a strict freeze covenant:
   - **Submission 56146971 (Slot 1, Challenger)**: `compiled_v54_plus_residual.py` (V54++ macro foundation + aggressive residual sell preemption: `preempt_money_deficit = 2000.0`, `preempt_minimum_delta = 4.0`, `preempt_maximum_batch = 12`). Live record: 43W / 42L (50.6% WR), Mean Margin: +$2,647.27, Mean Cash: $89,089.21.
   - **Submission 56146947 (Slot 2, Control Baseline)**: `compiled_v54_plus_shop.py` (V54++ macro foundation + minimal shop controller). Live record: 42W / 34L (55.3% WR), Mean Margin: +$2,933.79, Mean Cash: $81,295.95.
   - Total observed live tournament matches across both submissions: **161 matches (85W / 76L / 0T, 52.8% WR)**.
   - **Current Best Frozen Live Fallback**: **Submission 56146971**.

3. **Holdout & Quarantine Governance**:
   - The certified virgin final holdout partition **Seeds 214200–214249 ($N=50$)** is **100% untouched and pristine** (0 simulations across project history).
   - The historical partition **Seeds 50150–50199** was disqualified and permanently quarantined in Gate 0.2 due to historical contamination (simulated in the 500-seed Phase 3 shop census, live tournament match 107564294, and exploratory script `test_phase16_generalization.py`).
   - The benchmark partition **Seeds 50100–50149** is classified as an *Audited Benchmark Partition* (loss characteristics known from Audit 2).

4. **Experimental Progression & Major Milestones**:
   - **EXP-DEV-001**: Failed. Worst loss -$2,388 on Seed 50018 breached the -$800 tail limit. Proved that unhedged crop replacement based on premature Day 3/6 shop signals exposes the farm to catastrophic opportunity costs if late town shops pivot to Strawberry.
   - **EXP-DEV-002**: Protocol ambiguity stopped execution; Protocol Amendment V1.1 established hedged adaptation. While Discovery passed, Qualification on 50050–50099 **FAILED confirmatory significance** ($t=1.1772, p=0.2391$). Mean margin collapsed to +$2.00; Tomato mode activated 0 times; DEV-002 was action-identical to DEV-001 ($0.00 delta) on all 50 seeds. Formally retired.
   - **EXP-DEV-003**: Tested on fresh virgin seeds 245000–245049. **FAILED decisively** (0W / 4L / 46T, Mean: -$835.32, Worst loss: -$14,696.00). Proved that overriding crop plantings without recompiling worker movement routes causes harvest delays, premature vine death at step 552, 7 days of barren land, and catastrophic cash forfeiture.
   - **EXP-DEV-004**: Tested whole-route macro scheduling on virgin seeds 246000–246049 (14W / 16L / 20T, Mean: +$912.78, Worst loss: -$8,111.00). **Gate 4 Erratum confirmed**: True lifetime activation was 40/50 (80%), not 52%. 23 terminally specialized, 3 re-specialized, 14 reverted, 10 always-baseline (bit-exact $0.00 delta). The 14 terminal-baseline seeds had specialized earlier, accumulating friction.
   - **EXP-DEV-005 KILLTEST**: Tested commitment hysteresis on 16 DEV-004 losses + 4 positive controls. **REJECTED (MIXED_UNSAFE)**. Recovered only 20.56% of losses (<50% threshold) and worsened 7 loss seeds. Positive control Seed 246048 collapsed from +$14,143 win to -$11,577 loss (-$25,720 swing). Proved mid-flight reversal was an *adaptive reaction*, not the disease. The root disease was speculative early commitment at Step 72 before matching shop confirmation.
   - **EXP-DEV-005**: Implemented confirmed-shop gating on virgin seeds 247000–247049. **Confirmed positive mechanism**: Loss rate collapsed from 30% to 4% (5W / 2L / 43T, 96% safe), paired mean +$797.76. Saved 13 of 15 DEV-004 disaster seeds (+$47,210 saved). The only 2 losses occurred on late entries at Step 288 (Day 12), exposing the horizon cliff.
   - **DEV-006 HORIZON KILLTEST**: Evaluated H=500 guard (no new specialization if remaining steps < 500) on 247000–247049 via clean-room simulator port. **Recovered 100% of the late-entry losses** (Seeds 247025 and 247034 converted to $0.00 ties, recovering +$7,237.00). **Critical factual correction**: Refuted the myth that step 288 bought sheep ($0 livestock capital spent). The late switch skipped the step-313 sheep from LIVE tape and bought 1,895 units of wheat-product feed with no matching sheep flock.
   - **DEV-006 DISCOVERY**: Tested on fresh virgin seeds 248000–248049. Replicated loss elimination: eliminated both fresh late-entry losses (-$8,282 and -$6,528 -> $0.00), resulting in +$290.90 mean, 2W / 0L / 48T. Replicated mechanism (4/4 cross-cohort loss elimination), but statistically non-significant ($p=0.168$) and carried 100% by two wins.
   - **DEV-006 QUALIFICATION**: Tested on reserved cohort 50050–50099 (N=50). **INCONCLUSIVE**. The H=500 guard fired 0 times (0/200 games) because no seed attempted late entry; DEV-006 was bit-for-bit identical to DEV-005 on all 50 seeds (+517.58 mean, 3W / 0L / 47T, $t=1.7586, p=0.0849$). Missed statistical gate ($t > 1.96$); mechanism was untested.
   - **EXP-DEV-007**: Frozen prospective protocol (`d10ee185`, commit `db1c7ebe`) on cohort 310000–310499 (N=500, 2000 games). Designed to evaluate unconditional performance (E1), trigger incidence (E2), and conditional mechanism effect (E3). **STRICTLY UNEXECUTED**.

5. **Dmitrii Decompilation & Architectural Reality (EXP-ARCH-001)**:
   The completed decomposition of all 13 tapes in Dmitrii LB2800's `actions.json` across 719 turns disproves the myth that Dmitrii runs "13 distinct strategic economies."
   - **Dmitrii runs exactly ONE agronomic economy**: Day 0 melon+livestock blast (94.7% cash deployed), 16–17 head herd with daily care/feed, identical planting tables across all tapes, land purchase at Days 6 and 11, and late carrots on days 24–27.
   - The "13 strategies" are 12 execution/routing permutations around this single economy, chosen once at Step 144 based strictly on early YARN shop reveals (49 of 64 shop pairs share the default Strategy 0).
   - All 13 strategies are forcibly converged to a shared harvest/liquidation tail (Strategy 2) at Step 648.
   - Real-time control consists of two local bounded repairs: a same-day weed digging queue (`repair_weeds`) and one-turn sale advances (`advance_sales`), followed by a 7-turn shadow optimizer (steps 712–718) constrained by row-wise physical unit dominance.
   - **Architectural Principle Confirmed**: Dmitrii's competitive power is explained by the conjunction **$E = B + C + D$**: Robust macro plan with limited switching ($B$) + local reactive repair ($C$) + short-horizon shadow optimization ($D$).

---

# 2. REPOSITORY MAP

The repository structure reflects the layered history of the research program, spanning early legacy tournament sweeps, post-submission causal audits, closed-loop development candidates, and governance registries:

```
c:\Users\Sundareswaran\Kagriculture\
├── candidates/                          # Production, baseline, and experimental agent scripts
│   ├── closed_loop_architecture/        # Modular closed-loop candidates (DEV-001 through DEV-006)
│   │   ├── dev_001_dynamic_portfolio.py
│   │   ├── dev_002_hedged_portfolio.py
│   │   ├── dev_003_conditional_specialization.py
│   │   ├── dev_004_joint_macro_scheduler.py
│   │   ├── dev_005_confirmed_shop_scheduler.py   [FROZEN: f52b1686]
│   │   ├── dev_006_horizon_guard_scheduler.py    [FROZEN: 06db94e5]
│   │   ├── closed_loop_agent.py / closed_loop_v2.py
│   │   └── action_arbitrator.py / liquidity_controller.py
│   ├── compiled_v54_plus_residual.py    # [FROZEN LIVE CHALLENGER: 18402ec6, Sub 56146971]
│   ├── compiled_v54_plus_shop.py        # [FROZEN LIVE CONTROL:    f651ccd2, Sub 56146947]
│   ├── declarative_backbone/            # Declarative agent compiler and parameters
│   └── slot1..slot5 / apex / aethel     # Historical submission candidates
├── experiments/                         # Formal development experiment directories
│   ├── EXP-DEV-001/                     # Dynamic Portfolio Discovery (FAILED)
│   ├── EXP-DEV-002/                     # Hedged Portfolio Discovery & Qualification (RETIRED)
│   ├── EXP-DEV-003/                     # Conditional Specialization Discovery (FAILED)
│   ├── EXP-DEV-004/                     # Joint Macro Scheduler Discovery & Gate 4 Erratum
│   ├── EXP-DEV-005_KILLTEST/            # Retrospective Hysteresis Mechanism Kill-Test (REJECTED)
│   ├── EXP-DEV-005/                     # Confirmed-Shop Gated Scheduler Discovery (POSITIVE)
│   ├── EXP-DEV-006_HORIZON_KILLTEST/    # Retrospective Horizon Guard Kill-Test (REPLICATED)
│   ├── EXP-DEV-006/                     # Fresh Discovery & Qualification (INCONCLUSIVE)
│   │   └── QUALIFICATION/               # Stage 2 Confirmation on 50050–50099
│   ├── EXP-DEV-007_MECHANISM_EXPOSURE/  # Frozen Prospective Protocol (UNEXECUTED)
│   └── EXP-ARCH-001_DMITRII_POLICY_DECOMPOSITION/ # Complete 13-Tape Decompilation Deliverables
├── extracted_agents/                    # Decompiled competitor architectures
│   └── dmitrii_lb2800/                  # Dmitrii LB2800 extracted source
│       ├── main.py / policy.py / router_parent.py
│       ├── actions.json                 # 13 precomputed macro strategy tapes (719 turns)
│       └── terminal_planner.py / unit_model.py
├── engine/                              # Economic accounting and oracle models
├── external_repos/                      # External C++ simulator codebases
│   └── kaggriculture-cppsim/            # kagsim engine implementation (sim/sim.hpp)
├── research/                            # Chronological post-submission research reports (R1–R14)
├── reports/                             # Specialized forensic audits, tournament reports
├── results/                             # Intermediate simulation outputs and census databases
├── scratch/                             # Diagnostic harnesses, verification probes, replay tools
└── temporary/                           # Temporary working buffers
```

### Directory Classification Status:
| Directory | Epistemic Status | Governance Directive |
| :--- | :---: | :--- |
| `candidates/compiled_v54_plus_*.py` | **FROZEN LIVE** | Strict freeze. Never modify or recompile. |
| `candidates/closed_loop_architecture/` | **ACTIVE / EXPERIMENTAL** | Historical candidates frozen under Git; read-only. |
| `experiments/EXP-DEV-001..006/` | **FROZEN COMPLETED** | Historical records immutable. Results recorded. |
| `experiments/EXP-DEV-007_*/` | **FROZEN PROSPECTIVE** | Protocol frozen under commit `db1c7eb`. Zero execution. |
| `experiments/EXP-ARCH-001_*/` | **COMPLETED ARCHITECTURE** | Tape decoder and transferability matrix delivered. |
| `extracted_agents/dmitrii_lb2800/` | **HISTORICAL BENCHMARK** | Reference benchmark agent. Strictly read-only. |
| `research/` & `reports/` | **HISTORICAL LITERATURE** | Audited post-submission literature (Grades A to H). |
| `scratch/` | **DIAGNOSTIC / VERIFICATION** | Read-only audit probes and reproduction scripts. |
| `temporary/` | **TEMPORARY** | Ephemeral scratch directory. |

---

# 3. FROZEN ARTIFACTS

To prevent silent bit-drift, configuration creep, or accidental tampering, every critical artifact specified in the audit mandate was hashed directly from disk using SHA-256 via PowerShell:

```powershell
Get-FileHash -Algorithm SHA256 <FilePath>
```

### Cryptographic Hash Ledger:

| Artifact Name | Exact File Path | Expected SHA-256 | Recomputed Disk SHA-256 | Verification Verdict |
| :--- | :--- | :--- | :--- | :---: |
| **V54++ Residual** | `candidates/compiled_v54_plus_residual.py` | `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb` | `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb` | **MATCH (BIT-EXACT)** |
| **V54++ Shop** | `candidates/compiled_v54_plus_shop.py` | `f651ccd220e701968bc33579812d8917da63f5b0582f2fd0d363fa6a16ffd8b8` | `f651ccd220e701968bc33579812d8917da63f5b0582f2fd0d363fa6a16ffd8b8` | **MATCH (BIT-EXACT)** |
| **DEV-005 Candidate** | `candidates/closed_loop_architecture/dev_005_confirmed_shop_scheduler.py` | `f52b168619e47bea6a052faff890fc84804cb39b47392d247139967f910e2a78` | `f52b168619e47bea6a052faff890fc84804cb39b47392d247139967f910e2a78` | **MATCH (BIT-EXACT)** |
| **DEV-006 Candidate** | `candidates/closed_loop_architecture/dev_006_horizon_guard_scheduler.py` | `06db94e59e2c271b5490aad78fdb760bd8a250f28ec4407de2d2f6be0644f5eb` | `06db94e59e2c271b5490aad78fdb760bd8a250f28ec4407de2d2f6be0644f5eb` | **MATCH (BIT-EXACT)** |
| **DEV-007 Protocol** | `experiments/EXP-DEV-007_MECHANISM_EXPOSURE/PROTOCOL.md` | `d10ee1857b380ee1254a29bf9fc1a49e33c10783b9e49ef1e68beb75bab80cff` | `d10ee1857b380ee1254a29bf9fc1a49e33c10783b9e49ef1e68beb75bab80cff` | **MATCH (BIT-EXACT)** |

**Verification Outcome**: Exactly **0 discrepancies detected**. All hashes match the frozen records.

---

# 4. LIVE KAGGLE STATUS

### 4.1 Known Live Submissions

The production team deployed two standalone compiled agents to the live Kaggle ladder on September 10, 2026:

1. **Submission `56146971` (Active Slot 1 — Experimental Challenger)**:
   - **Agent Name**: `compiled_v54_plus_residual.py`
   - **Upload Timestamp**: `2026-09-10 15:14:36 UTC`
   - **Cryptographic SHA-256**: `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb`
   - **Kaggle Status**: `COMPLETE` (Initial Score: 600.0)
   - **Live Telemetry (Replay Manifest Audit, 85 matches)**:
     - Record: **43 Wins / 42 Losses / 0 Ties (50.6% Win Rate)**
     - Our Mean Cash: **$89,089.21**
     - Opponent Mean Cash: **$86,441.94**
     - Mean Paired Margin: **+$2,647.27**
     - Live Rating: ~`1499.1` Elo (Rank 2368 / 9001)

2. **Submission `56146947` (Active Slot 2 — Control Baseline)**:
   - **Agent Name**: `compiled_v54_plus_shop.py`
   - **Upload Timestamp**: `2026-09-10 15:13:16 UTC`
   - **Cryptographic SHA-256**: `f651ccd220e701968bc33579812d8917da63f5b0582f2fd0d363fa6a16ffd8b8`
   - **Kaggle Status**: `COMPLETE` (Initial Score: 600.0)
   - **Live Telemetry (Replay Manifest Audit, 76 matches)**:
     - Record: **42 Wins / 34 Losses / 0 Ties (55.3% Win Rate)**
     - Our Mean Cash: **$81,295.95**
     - Opponent Mean Cash: **$78,362.16**
     - Mean Paired Margin: **+$2,933.79**
     - Live Rating: ~`1453.0` Elo

### 4.2 Aggregate Tournament Distribution (161 Matches)
- **Overall Record**: **85 Wins / 76 Losses / 0 Ties (52.80% Win Rate)**
- **Mean Net Margin**: **+$2,782.52**
- **Worst Match Loss**: **-$55,096.00** (Episode 107543042 vs Opponent `56120608`)
- **Best Match Win**: **+$136,314.00** (vs Opponent `55648629`)
- **Severe Tail Risk**:
  - $P(\text{Loss} > \$10,000) = 13.0\%$ (21 matches)
  - $P(\text{Loss} > \$20,000) = 5.6\%$ (9 matches)

### 4.3 Code Differences Between Submissions
A strict `git diff --no-index` between `compiled_v54_plus_shop.py` and `compiled_v54_plus_residual.py` reveals that **the two files are 100% byte-for-byte identical except for 10 lines configuring the residual controller**:

```diff
--- candidates/compiled_v54_plus_shop.py
+++ candidates/compiled_v54_plus_residual.py
@@ -4388,7 +4392,11 @@
-_CONFIG = copy.deepcopy(_V54_CONFIG)
+_CONFIG_DICT = copy.deepcopy(dict(_V54_CONFIG.__dict__))
+_CONFIG_DICT["preempt_money_deficit"] = 2000.0
+_CONFIG_DICT["preempt_minimum_delta"] = 4.0
+_CONFIG_DICT["preempt_maximum_batch"] = 12
+_CONFIG = _V51ResidualConfig(**_CONFIG_DICT)
```
There are **zero algorithmic differences**, zero pathing differences, and zero route table differences. Submission 56146971 simply enables aggressive market order preemption when a cash deficit $\ge 2,000$ coins is detected.

### 4.4 Mutation Verification & Epistemic Status
- Git history (`git log --stat`) confirms that both compiled files were committed in `a7af701` and have **NEVER been touched, modified, or recompiled since deployment**.
- **Nature of Evidence**: Live ladder outcomes are **OBSERVATIONAL**, as match pairings and opponent actions are exogenous. However, the internal 50-seed pre-deployment holdout validation (Report R1) provides **CAUSAL EVIDENCE** of residual alpha (+1,984 margin over control).
- **Current Frozen Live Fallback**: **Submission 56146971**.

---

# 5. HOLDOUT / QUARANTINE GOVERNANCE

### 5.1 Certified Virgin Final Holdout: Seeds 214200–214249
- **Designation Date**: 2026-09-11 (Development Gate 0.3)
- **Sample Size**: **50 Seeds** (100 paired CRN matches)
- **Covenant**: Under Section 8 of the Development Protocol, this partition is reserved exclusively for the final pre-deployment qualification of a frozen candidate. It must never be inspected, simulated, or used for tuning.
- **Virginity Proof**:
  1. A global AST and string search across all workspace files (`.py`, `.json`, `.csv`, `.md`, `.log`) verified **0 simulation entries**.
  2. All test runners (`run_exp_dev_001.py` through `run_exp_dev_006.py`) enforce a mandatory runtime assertion:
     ```python
     def assert_not_holdout(seed):
         if 214200 <= seed <= 214249:
             raise AssertionError(f"FATAL: Attempted execution of protected holdout seed {seed}!")
     ```
  3. All appearances of the string `214200` in historical logs were audited and verified to be nanosecond execution timestamps (e.g. `9.34421420097351`) or hash substrings.
  4. **Status**: **100% PRISTINE AND VIRGIN (0 EXECUTIONS)**.

### 5.2 Disqualified & Permanently Quarantined Partitions
1. **Seeds 50150–50199 (Permanently Quarantined)**:
   - **Reason for Disqualification**: In Development Gate 0.2, an exhaustive audit uncovered pervasive contamination. All 50 seeds were simulated in the 500-seed Phase 3 macro census (`results/phase3_shop_census_500seeds.json`); Seed 50186 was an official live tournament loss seed (`episode_107564294.json`); and Seeds 50155 and 50161 were used for strategy selection in `scratch/test_phase16_generalization.py`.
   - **Status**: **CONTAMINATED / PERMANENTLY RETIRED**.
2. **Seeds 60000–60049 (Quarantined)**: Contaminated by historical hyper-parameter sweeps (`parameter_and_lookahead_sweeps.py`).
3. **Seeds 50100–50149 (Audited Benchmark Partition)**: Evaluated in Audit 2/2.1/2.2 for baseline characterization. Retained as an audited historical benchmark; not virgin.

---

# 6. GOVERNANCE HISTORY (DEVELOPMENT GATES 0.1, 0.2, 0.3)

Prior to launching development experiments `EXP-DEV-001` through `EXP-DEV-006`, the research program underwent three strict governance integrity gates:

### Gate 0.1 — Pre-Experiment Integrity Audit (2026-09-11 17:02 UTC)
- **Purpose**: World-regime audit, claim ledger construction, and protocol verification.
- **Findings**: Uncovered nine critical defects documented in `DEVELOPMENT_GATE_0_1_CORRECTION_LEDGER.md`:
  - Identified that Seeds 50100–50149 were known from Audit 2 (Correction `CORR-0.1-09`), mandating that they be classified as an *Audited Benchmark Partition* and requiring a fresh holdout for final deployment.
  - Applied `CORR-0.1-05`, decoupling `EXP-DEV-005` into pure Monte Carlo terminal closure to remove the Step 217 cash buffer confounder.
- **Verdict**: **CLEARED WITH CORRECTIONS**.

### Gate 0.2 — Preregistration & Baseline Provenance Audit (2026-09-11 17:22 UTC)
- **Purpose**: Verify pre-registration integrity and holdout virginity.
- **Critical Discovery**: Provenance check on the proposed holdout cohort (Seeds 50150–50199) found **0% virginity** due to historical census and live match contamination.
- **Verdict**: **FAILED (BLOCKED)** on holdout virginity. Mandated the immediate abandonment of 50150–50199 and the establishment of a certified virgin holdout partition.

### Gate 0.3 — Final Holdout Certification & Leakage Threat Model (2026-09-11 17:47 UTC)
- **Purpose**: Formal certification of a virgin holdout and zero-leakage sandbox validation.
- **Achievements**:
  1. Formally established **Seeds 214200–214249** as `HOLDOUT-COHORT-V1` in `DEVELOPMENT_HOLDOUT_REGISTRY.md`.
  2. Built and validated the **14-Vector Leakage Containment Sandbox**, verifying AST interception of forbidden attributes (`seed`, `engine`, `future`, `target`, etc.).
  3. Prospective protocol frozen under Git commit `a1ba5acb0d04689874ce1333892825f014eea924`.
- **Verdict**: **FULLY CLEARED (PROSPECTIVE FREEZE ACTIVE)**.

---

# 7. BASELINE AND DMITRII HISTORY

### 7.1 150-Seed V2 vs Dmitrii Statistics
An extensive 150-seed paired Common Random Numbers (CRN) tournament (300 matches, balanced seating) was conducted across Discovery (50000–50049), Qualification (50050–50099), and Holdout (50100–50149). The raw JSON dataset (`scratch/v2_dmitrii_margin_scan.json`) was independently audited and recomputed:

| Partition | Sample ($N$) | Mean Margin | Median | Std Dev | Std Error | 95% Confidence Interval | $t$-statistic | $p$-value | Win Rate | Min (Worst Loss) | Max (Best Win) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Discovery** | 50 | +$39.12 | +$76.00 | $157.61 | $22.29 | [-$5.67, +$83.91] | 1.7551 | 0.0855 | 62.0% (31W–19L) | -$400.00 | +$326.00 |
| **Qualification** | 50 | +$11.40 | -$13.00 | $190.74 | $26.97 | [-$42.81, +$65.61] | 0.4226 | 0.6744 | 48.0% (24W–26L) | -$730.00 | +$244.00 |
| **Holdout** | 50 | +$23.32 | +$57.00 | $151.44 | $21.42 | [-$19.72, +$66.36] | 1.0889 | 0.2815 | 54.0% (27W–23L) | -$452.00 | +$316.00 |
| **Combined** | **150** | **+$24.61** | **+$58.00** | **$166.75** | **$13.61** | **[-$2.29, +$51.52]** | **1.8078** | **0.0727** | **54.67% (82W–68L)** | **-$730.00** | **+$326.00** |

- **Bootstrap 95% CI (100,000 resamples)**: `[-$2.56, +$50.57]`
- **Cohen's $d$**: `0.1476` (negligible effect size)
- **Worst 5 Paired Seeds**: Seed 50081 (-$730.0), Seed 50078 (-$612.0), Seed 50112 (-$452.0), Seed 50022 (-$400.0), Seed 50014 (-$358.0).
- **TOST Equivalence Testing**:
  - Bound $[-\$25, +\$25]$: $p = 0.4887 \to$ **NOT EQUIVALENT**
  - Bound $[-\$50, +\$50]$: $p = 0.0321 \to$ **STATISTICALLY EQUIVALENT**
- **Epistemic Classification**: **STATISTICAL PARITY SUPPORTED; SUPERIORITY NOT PROVEN**. Because the 95% confidence interval spans zero ($p = 0.0727 > 0.05$), claiming "proven global superiority" is statistically invalid.

### 7.2 The $800 Dawn Hiring Collapse Myth & The Parser Error
Early reports (e.g. `research/live_loss_counterforensics_report.md`) asserted that our live tournament losses occurred because agents entered Day 10–12 with $< \$800$ cash, triggering an "800 dawn hiring collapse" that cut the workforce in half.
- **Forensic Audit (`EXP-HIST-08` / `DEVELOPMENT_EVIDENCE_LEDGER.md:51`)**: A direct inspection of the raw replay telemetry for Match 107543042 proved this narrative was completely false.
- **The Bug**: The analysis script `reconstruct_live_losses.py` contained a dictionary parsing bug confusing `units` (which include livestock) with `hands` (workers), and miscalculated Fibonacci hiring costs.
- **The Empirical Reality**: On Day 12 morning, Eldritch had **$9,847 cash**, successfully hired **9 hands**, and paid **$88 Fibonacci hiring costs**.
- **Verdict**: **RETRACTED AND PERMANENTLY BANNED**.

### 7.3 MAX_ORDERS = 10 Engine Enforcement
Both the C++ simulator engine (`kagsim`) and the Kaggle environment enforce a strict ceiling:
$$\text{MAX\_ORDERS} = 10$$
Submitting more than 10 market orders in a single turn results in silent truncation of order slots 10+. Both `dmitrii_lb2800/router_parent.py` (lines 22, 220) and our production agents enforce `action["market"] = action["market"][:MAX_ORDERS]`.

### 7.4 Physical Agronomy Divergence Between V2 and Dmitrii
- Early audit reports claimed that `CLOSED_LOOP_V2` and `Dmitrii-LB2800` execute "100.0% bit-for-bit identical physical agronomy across all 30 days."
- **Refutation (`AUDIT2_REPRODUCTIONS.md:25`, `DEVELOPMENT_EVIDENCE_LEDGER.md:52`)**: Turn-by-turn simulation on Seed 50081 (V2's worst loss of -$730) proved this was false.
  - At Step 217, an early runtime market price difference produced a minor $4 cash deficit ($497 < $500), causing V2's scheduled sheep purchase to fail.
  - Because the sheep was never purchased, Tile (1, 4) remained an empty pasture on V2 for **460 consecutive turns** (from Step 259 to 719).
  - Furthermore, Dmitrii executes a dynamic 7-turn Monte Carlo shadow optimizer at Steps 712–717 (`terminal_planner.py`), while V2 executes static precomputed actions.
- **Conclusion**: Physical agronomy is **NOT identical**. Runtime cash feedback triggers animal purchase failures and long-term physical desynchronization.

---

# 8. COMPLETE EXPERIMENT TIMELINE

| Experiment ID | Date (UTC) | Protocol / Hash | Commit | Cohort / Seeds | Sample ($N$) | Primary Comparison | Result / Metrics | Statistical & Tail Status | Decision | Why / What Was Learned |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- | :--- | :--- | :---: | :--- |
| **Gate 0.1** | 2026-09-11 17:02 | Gate 0.1 Audit | — | — | — | Pre-experiment integrity audit | Cleared 9 corrections; identified holdout partition hygiene | Audited Benchmark status formalized | **CLEARED** | Set pre-registration standards. |
| **Gate 0.2** | 2026-09-11 17:22 | Gate 0.2 Audit | — | 50150–50199 | 50 | Holdout provenance audit | Found 0% virginity on proposed holdout (census contamination) | Failed holdout integrity | **BLOCKED** | Disqualified 50150–50199; prevented holdout leakage. |
| **Gate 0.3** | 2026-09-11 17:47 | Gate 0.3 Audit | `a1ba5ac` | 214200–214249 | 50 | Final holdout certification | Certified virgin holdout `HOLDOUT-COHORT-V1`; 14-vector sandbox | Zero contamination verified | **CLEARED** | Locked final holdout; prospective freeze active. |
| **EXP-DEV-001** | 2026-09-11 18:09 | Protocol V1.0 | `a1ba5ac` | Discovery 50000–50049 | 50 | Dynamic Portfolio vs V2 & Dmitrii | Mean: +$265.18, 42T / 6W / 2L; worst loss -$2,388 (Seed 50018) | $p=0.3963$; 10% trimmed mean +$0.40; breached -$800 stop limit | **FAILED** | Early crop substitution creates huge tail risk under late shop shifts. |
| **EXP-DEV-002** | 2026-09-11 20:21 | Protocol V1.1 (`735ad84`) | `b2a4f45` | Qual 50050–50099 | 50 | Hedged Portfolio vs V2 & Dmitrii | Mean: +$2.00, 43T / 5W / 2L; worst loss -$26.00; 0 Tomato activations | $t=1.1772, p=0.2391$; missed $t>1.96$ gate; identical to DEV-001 | **RETIRED** | Tail safe, but alpha vanished; Tomato mode had 0% exposure. |
| **EXP-DEV-003** | 2026-09-14 18:36 | Protocol V1.2 (`f94f9b7`) | `62cc332` | Discovery 245000–245049 | 50 | Opportunity Specialization vs V54++ | Mean: -$835.32, 46T / 0W / 4L; worst loss -$14,696.00 (Seed 245045) | $t=-1.91, p=0.062$; left-tail collapse; 0% win rate | **FAILED** | Crop substitution without whole-route worker re-pathing causes vine rot. |
| **EXP-DEV-004** | 2026-09-14 19:42 | Protocol V1.3 (`68047be`) | `68047be` | Discovery 246000–246049 | 50 | Joint Macro Scheduler vs V54++ | Mean: +$912.78, 20T / 14W / 16L; worst loss -$8,111.00; Gate 4 Erratum | 40/50 ever specialized; 14 harmful reversals; 10 always-baseline | **INVESTIGATE** | Reversals after Step 72 commitment caused heavy capital mismatch losses. |
| **EXP-DEV-005 KILLTEST**| 2026-09-14 20:31 | Killtest Suite | `3347128` | Retrospective 246000–246049 | 20 | Hysteresis Guard on DEV-004 losses | Recovered 20.56% of losses (<50% bar); worsened 7 seeds; Seed 246048 lost -$25.7k | Certified MIXED_UNSAFE; hypothesis rejected | **REJECTED** | Reversal was an adaptive exit; root flaw was premature commitment at Step 72. |
| **EXP-DEV-005** | 2026-09-14 21:19 | Protocol V1.4 (`af12b6f`) | `af12b6f` | Discovery 247000–247049 | 50 | Confirmed-Shop Gated Scheduler vs V54++ | Mean: +$797.76, 43T / 5W / 2L; worst loss -$5,393; saved 13 disaster seeds | Loss rate collapsed 30% -> 4%; $t=1.78, p=0.0817$; Step 288 cliff | **POSITIVE** | Shop confirmation cures premature speculation; late entries at 288 lose. |
| **DEV-006 KILLTEST** | 2026-09-14 22:42 | Horizon Killtest | `b7b4863` | Retrospective 247000–247049 | 50 | H=500 Guard on DEV-005 losses | Recovered 100% of late losses (+$7,237 saved); Seeds 247025/034 -> $0.00 | 48/48 other seeds bit-identical; sheep myth refuted | **REPLICATED** | H=500 eliminates late-entry cascade; 288 switch had $0 livestock outlay. |
| **DEV-006 DISCOVERY** | 2026-09-14 23:12 | Protocol V1.5 (`e52a057`) | `8bc8248` | Discovery 248000–248049 | 50 | Horizon-Gated Scheduler vs V54++ | Mean: +$290.90, 48T / 2W / 0L; min $0.00; converted -$8.2k & -$6.5k -> $0.00 | $t=1.40, p=0.168$; 4/4 late losses eliminated across cohorts | **STAGE QUAL** | Mechanism replicated on fresh seeds; mean carried by 2 wins; p>0.05. |
| **DEV-006 QUAL** | 2026-09-14 23:36 | Qual Protocol (`1484e00`) | `36c9f77` | Stage 2 Qual 50050–50099 | 50 | Frozen DEV-006 vs V54++ | Mean: +$517.58, 47T / 3W / 0L; min $0.00; guard fired 0 times (DEV-006==DEV-005) | $t=1.7586, p=0.0849$; Gate A & B NOT PASS; Gate C & D PASS | **INCONCLUSIVE** | Guard had 0 exposure; not qualified, not failed; cannot tune H. |
| **EXP-DEV-007** | 2026-09-15 09:12 | Protocol V1.0 (`d10ee18`) | `db1c7eb` | Frozen Cohort 310000–310499 | 500 | Mechanism Exposure (DEV-006 vs Base & DEV-005) | Prospective 2000-game design; evaluates E1 (perf), E2 (inc), E3 (effect) | Strictly unexecuted; frozen before execution | **UNEXECUTED** | Awaiting execution. Characterizes H=500 naturally without post-hoc selection. |
| **EXP-ARCH-001** | 2026-09-15 10:48 | Arch Decomp Suite | `d6ddc36` | Dmitrii LB2800 extracted tapes | 13 tapes | 13 Strategy Tapes x 719 turns | Proved 1 macro economy x 12 executions; Step 144 route; 648 convergence | Proved $E = B + C + D$; transferability matrix delivered | **DELIVERED** | Architecture understood; no new candidate written. |

---

# 9. EXP-DEV-001 — DYNAMIC CROP PORTFOLIO

- **Protocol & Commit**: `DEVELOPMENT_EXPERIMENT_PROTOCOL_V1.md`, Commit `a1ba5acb0d`
- **Candidate Treatment**: `candidates/closed_loop_architecture/dev_001_dynamic_portfolio.py`
- **Baseline Controls**: `ClosedLoopAgentV2` (Primary) and `Dmitrii-LB2800` (Reference)
- **Evaluation Partition**: Discovery (Seeds `50000–50049`, $N=50$ seeds, 100 paired matches)
- **Primary Hypothesis**: Evaluating revealed town shops on Day 3 (Step 72) and Day 6 (Step 144) to select between Strawberry Bedrock and targeted complementary crops yields positive paired margin over static 19S/0T without increasing downside tail risk.
- **Results**:
  - vs `ClosedLoopAgentV2`: Mean Margin: **+$265.18**, Median: **$0.00**, Std Dev: $2,191.06, Std Error: $309.86, $t=0.8558, p=0.3963$, 95% CI: `[-$357.51, +$887.87]`. Win Record: **6 Wins / 2 Losses / 42 Ties** (12.0% Win Rate, 84.0% Tie Rate).
  - vs `Dmitrii-LB2800`: Mean Margin: **+$291.10**, Median: +$121.00, Win Rate: **66.0% (33W–17L)**.
  - Worst Single-Seed Loss: **-$2,388.00** (Seed 50018).
  - Best Single-Seed Win: **+$15,264.00** (Seed 50004).
- **Causal Forensics of Seed 50018 and Seed 50004**:
  - **Seed 50018 (-$2,388)**: The agent unlocked `PIZZA_SHOP` at Steps 72 and 144 without Strawberry shops, triggering `TOMATO` mode. On Day 11, it replaced 13 core strawberry plants with tomatoes. Subsequently, late town shop unlocks on Days 12, 15, and 18 heavily favored Strawberry (`SMOOTHIE_SHOP`, `FARMERS_MARKET`). Forfeiting 13 mature strawberries during a late strawberry demand boom produced a massive cash shortfall.
  - **Seed 50004 (+$15,264)**: Mirror image. The town shops confirmed massive Tomato demand throughout the game, allowing the 13 Tomato plants to realize enormous premium cashflow.
- **Marginal Shop-Probability Correction**:
  - Drawing at least one Yarn or Strawberry shop across Days 3 and 6 has an analytical probability of:
    $$P(\text{Yarn} \cup \text{Strawberry}) = 1 - \left(\frac{6}{8}\right) \times \left(\frac{5}{8}\right) = 1 - \frac{30}{64} = \frac{34}{64} \approx 53.1\% \quad (\text{if without replacement})$$
    With replacement (as in `sim.hpp`), $P = 1 - (6/8)^2 = 1 - 36/64 = 28/64 = 43.75\%$ per shop category.
  - In `dev_001`, Priority 1 (`YARN`) and Priority 2 (`STRAWBERRY`) both defaulted back to `ClosedLoopAgentV2`. Consequently, the treatment was completely inert on **42 of 50 seeds (84.0%)**, producing exact $0.00 ties.
- **Outlier Dominance**:
  - The positive mean (+$265.18) was 100% dependent on the single outlier Seed 50004 (+15,264). Excluding Seed 50004, the mean margin turned negative (**-$40.92**). The 10% trimmed mean was **+$0.40**.
- **Final Decision**: **FAILED (RETAIN FAILURE)**. The worst loss of -$2,388.00 severely violated the pre-registered -$800.00 stop ceiling. Decommissioned.

---

# 10. EXP-DEV-002 — HEDGED ADAPTIVE PORTFOLIO

- **Protocol Ambiguity & Injunction**:
  - In preflight testing, an audit revealed that Protocol V1.0 had registered `EXP-DEV-002` as a "Shop Value of Information (VoI) Quantification" experiment using an unbuilt `dev_002_shop_voi_evaluator`, directly conflicting with the user directive to test a "Hedged Adaptive Portfolio".
  - In strict compliance with Governance Rule 10, execution was **HALTED (0 seeds simulated)**, and `EXP-DEV-002_PROTOCOL_AMBIGUITY.md` was issued.
- **Protocol Amendment V1.1**:
  - The research team authored and committed `DEVELOPMENT_EXPERIMENT_PROTOCOL_V1_1.md` (SHA-256: `735ad844b7`), formally registering `dev_002_hedged_portfolio.py` (SHA-256: `cdd19cc8d2`).
  - **Preregistered Hedging Parameters**:
    - `bedrock_strawberry_floor = 13` mature plants guaranteed.
    - `tomato_substitution_cap = 6` tiles maximum converted.
    - `commitment_deadline_step = 144` (Day 6).
    - `base_liquidity_reserve = 500.0` cash floor.
- **Discovery Results (Seeds 50000–50049)**:
  - Mean Margin: **+$69.14** (or +$250.06 in unhedged post-hoc drafts), Median: $0.00.
  - Worst Loss: **-$26.00** (a 99% tail risk reduction vs DEV-001's -$2,388).
  - Passed Discovery gating to advance to Qualification.
- **Post-Hoc Exploratory Cap Sweep (Non-Preregistered)**:
  - An exploratory sweep across substitution caps (Caps 2, 4, 6, 8, 10, 12) showed Cap 6 maximized risk-adjusted margin on Discovery seeds. This was exploratory data analysis, not confirmatory evidence.
- **Qualification Results (Seeds 50050–50099, N=50)**:
  - Evaluated on the previously unseen Stage 2 Qualification cohort against `ClosedLoopAgentV2`:
  - Mean Margin: **+$2.00 coins** (95% CI: `[-$1.41, +$5.41]`).
  - Median Margin: **+$0.00 coins**; 10% Trimmed Mean: **+$0.00 coins**.
  - Student's $t$-statistic: **$t = 1.1772$**; Two-Sided $p$-value: **$p = 0.2391$**.
  - Record: **5 Wins / 2 Losses / 43 Ties** (10% WR, 4% LR, 86% TR).
  - Worst Loss: **-$26.00**; Best Win: **+$74.00**.
  - vs `Dmitrii-LB2800`: Mean Margin: +$24.88, Record: 25W / 25L (50.0% WR).
- **Causal Forensic Diagnosis — Why Tomato Mode Never Activated**:
  - On the 50 Qualification seeds, **$\Delta(\text{DEV-002} - \text{DEV-001}) = \$0.00$ bit-exact on every single seed**.
  - In `dev_002`, `TOMATO` mode required `PIZZA_SHOP` at Step 72/144 with zero Strawberry, Yarn, Pet Cafe, or Bakery shops.
  - Exactly 16 Qualification seeds drew `PIZZA_SHOP` by Step 144. In 13 seeds, a Strawberry shop was also drawn (selecting Strawberry); in 2 seeds Bakery was drawn (selecting Wheat); in 1 seed Pet Cafe was drawn (selecting Carrot). Exactly **0 seeds** drew exclusive Pizza shops.
  - Because Tomato mode never activated, the 6-tile Tomato cap and 13-strawberry floor were never exercised.
- **Final Decision**: **QUALIFICATION FAIL — FORMALLY RETIRED**. Failed primary confirmatory significance criterion ($t > 1.96, p < 0.05$).

---

# 11. EXP-DEV-003 — CONDITIONAL OPPORTUNITY-VALUE SPECIALIZATION

- **Candidate-Range Rejection & Seed Provenance**:
  - To preserve holdout integrity, contaminated ranges (50150–50199, 60000–60049) and consumed ranges (50000–50099) were rejected.
  - Certified virgin range **245000–245049 ($N=50$)** was selected and audited (0 prior workspace hits, 0 Git references).
- **Protocol & Treatment**:
  - Protocol V1.2 (SHA-256: `f94f9b71`), Candidate `dev_003_conditional_specialization.py` (SHA-256: `0b152cfa`).
  - Tested opportunity-value gating over `compiled_v54_plus_residual.py` baseline (Sub 56146971), calculating net projected marginal cash surplus ($\tau = 1,500.0$, $L_{\min} = 100.0$).
- **Results**:
  - Paired Mean Delta: **-$835.32** ($t = -1.910, p = 0.062, 95\%\text{ CI } [-\$1,714.21, +\$43.57]$).
  - Head-to-Head Win Record: **0 Wins / 4 Losses / 46 Ties (0.0% Win Rate)**.
  - Worst Loss: **-$14,696.00** (Seed 245045); Total Net Deficit: **-$41,766.00**.
  - Active Seeds: Fired on 5 seeds (10.0%). In 1 seed (245025), it fired after Day 11 (tie). In the other 4 activating seeds, it suffered catastrophic losses (-$3.6k to -$14.7k).
- **Causal Mechanism — Lifespan & Pathing Desynchronization**:
  - V54++'s macro route is tightly calibrated around Strawberry's 2-day repeat harvest cycle.
  - When DEV-003 substituted 4 tiles with Tomato on Day 11, worker movement schedules were not re-routed. Workers arrived late for tomato harvests.
  - As governed by `sim.hpp` lines 717–726, after completing 4 harvest cycles, tomato lifespan expired at Step 552 (Day 23). The plants died and turned to weeds.
  - For the remaining **7 days of the game**, the 4 tiles sat completely barren, producing zero revenue while baseline harvested 269 strawberries.
- **Core Lesson**: **Crop substitution without whole-route spatial/worker re-planning is catastrophic**.

---

# 12. EXP-DEV-004 — JOINT MACRO PRODUCTION SCHEDULER & GATE 4 ERRATUM

- **Concept & Candidate Architecture**:
  - Protocol V1.3 (`68047be`), Candidate `dev_004_joint_macro_scheduler.py`.
  - Abandoned ad-hoc tile swapping in favor of a **Joint Macro Production Scheduler** selecting among pre-compiled, fully synchronized whole routes (`BASELINE_BACKBONE`, `YARN_SPECIALIZED`, `BAKERY_SPECIALIZED`, `PET_SPECIALIZED`, `SMOOTHIE_SPECIALIZED`, `PIZZA_ADAPTIVE`).
  - Enforced physical feasibility constraints (labor hours, maturation horizon, shed capacity), market absorption limits, liquidity floor ($L_{\min} = 100$), and switching threshold ($\tau = 1,500$).
- **Evaluation Partition**: Virgin Seeds `246000–246049` ($N=50$, 100 paired matches vs Sub 56146971).
- **Results**:
  - Paired Mean Delta: **+$912.78** ($t = 1.63, p = 0.109, 95\%\text{ CI } [-\$213.78, +\$2,039.34]$).
  - Record: **14 Wins / 16 Losses / 20 Ties** (28.0% WR, 32.0% LR, 40.0% TR).
  - Worst Loss: **-$8,111.00**; Best Win: **+$14,143.00**; Total Net Surplus: +$45,639.00.

### 12.1 The Gate 4 Erratum (Authoritative Data Reconciliation)
In the original `FINAL_REPORT.md`, the authors reported: *"Activation Rate: 52.0% (26 of 50 seeds had planning overrides; 24 seeds preserved baseline invariant)."*
- **Forensic Audit (`ERRATUM_GATE4.md`)**:
  - In `run_exp_dev_004.py`, the variable `cand0.active_plan` was sampled exclusively at the end of the simulation (step 719).
  - This masked **14 seeds** that activated `YARN_SPECIALIZED` at Step 72, diverged physically at Step 74 (selling 1 wheat instead of 2), and subsequently reverted to `BASELINE_BACKBONE` at Step 144 or 216!
- **The Corrected, Authoritative Breakdown**:
  - **40 of 50 seeds (80.0%) EVER specialized** at $\ge 1$ planning checkpoint.
  - **23 seeds terminally specialized** (persisted to step 719).
  - **3 seeds re-specialized** after an intermediate reversion.
  - **14 seeds reverted** from specialized back to `BASELINE_BACKBONE` and stayed there.
  - **Exactly 10 seeds were genuinely always-baseline** throughout all 4 checkpoints.
  - For all 10 always-baseline seeds, candidate behavior was **100% bit-for-bit identical to baseline**, yielding exact **+$0.00 delta**.
  - All 14 terminal-baseline seeds had specialized earlier, suffering capital desynchronization losses (-$904 to -$3,885).

---

# 13. EXP-DEV-005 KILLTEST — HYSTERESIS COMMITMENT GUARD

- **Context & Hypothesis**:
  - The research team hypothesized that DEV-004's 16 losses were caused by "indecisive mid-flight route reversion" (switching back to baseline after sinking capital into specialized assets).
  - Proposed intervention: `HYSTERESIS_COMMITMENT_GUARD`, which locked the agent into its specialized route once committed at Step 72, blocking automatic reversion to baseline.
  - Preregistered threshold: Must recover $\ge 50.0\%$ of DEV-004's loss magnitude ($21,599.25).
- **Retrospective Test Setup**:
  - Evaluated on the 16 original DEV-004 loss seeds + 4 positive control winning seeds on partition `246000–246049`.
- **Results (`experiments/EXP-DEV-005_KILLTEST/VERDICT.md`)**:
  - Recovered only **+$9,673.50 (20.56%)** of the loss magnitude, decisively failing the $\ge 50.0\%$ threshold.
  - On **7 of the 13 reversal loss seeds**, forcing commitment *doubled* the losses (-$16,946.50 in new damage). For example, Seed 246022 collapsed from -$3.8k to -$8.2k; Seed 246030 collapsed from -$2.6k to -$6.6k.
  - **Destruction of Positive Controls**: On Seed 246048, the guard blocked an adaptive reversion, transforming a **+$14,143.00 win** into an **-$11,577.00 loss** (a single-seed damage of **-$25,720.00**).
- **Causal Conclusion**: **HYPOTHESIS DECISIVELY REJECTED (MIXED_UNSAFE)**.
  - Mid-flight route reversal was NOT the root disease; it was an **adaptive reaction terminating further accumulation of unsellable sheep**.
  - The true root disease was **premature speculative commitment at Step 72** on a single shop reveal before matching shop existence was confirmed.

---

# 14. EXP-DEV-005 — CONFIRMED-SHOP GATED SCHEDULER

- **Concept & Candidate Architecture**:
  - Protocol V1.4 (`af12b6f`), Candidate `dev_005_confirmed_shop_scheduler.py` (SHA-256: `f52b1686`).
  - Replaced speculative commitment with **Confirmed-Shop Gating**: whole-route specialization is strictly blocked (`REJECT_UNCONFIRMED`) unless the required commercial shop (`YARN_STORE`, `BAKERY`, etc.) is already observed in `town.unlocked_shops` at checkpoint step $t$.
- **Evaluation Partition**: Fresh virgin Seeds `247000–247049` ($N=50$, 100 paired CRN matches vs Sub 56146971).
- **Results (`experiments/EXP-DEV-005/FINAL_REPORT.md`)**:
  - Paired Mean Delta: **+$797.76** ($t = 1.78, p = 0.0817, 95\%\text{ CI } [-\$103.84, +\$1,699.36]$).
  - Head-to-Head Record: **5 Wins / 2 Losses / 43 Ties (96.0% Win/Tie Safety Rate)**.
  - Loss Count collapsed from 15 in DEV-004 to **2 in DEV-005 (an 86.7% risk reduction)**.
  - Minimum Delta: **-$5,393.00** (Seed 247034); Maximum Delta: **+$13,064.00** (Seed 247017).
  - Avoided **13 DEV-004 disaster seeds**, saving **+$47,210.00** in premature commitment losses.
  - Head-to-head seed preference vs DEV-004: DEV-005 preferred on 15 seeds vs DEV-004 on 8 seeds.
- **The Horizon Discovery (Seeds 247025 and 247034)**:
  - Both residual losses occurred on seeds where `YARN_STORE` unlocked late at **Step 288 (Day 12)**.
  - Entering specialization with only 432 steps remaining produced losses of -$1,844.00 and -$5,393.00, formulating the **H=500 Horizon Hypothesis**: late-entry specialization after Day 9 lacks sufficient runway.

---

# 15. DEV-006 HORIZON KILLTEST — RETROSPECTIVE HORIZON-GATE VERIFICATION

- **Clean-Room Python Simulator Port**:
  - Because the Windows C++ binary `kagsim.pyd` could not load on Linux environments, the engineering team constructed a validated pure-Python port (`kagsim_py 0.4.0.port1`, `ENGINE_VERSION 1.32.7`).
  - Parity verification: 47,520 of 47,520 golden actions matched exact C++ traces; DEV-005 replay produced 100 of 100 bit-identical match outcomes.
- **Treatment Purity**:
  - Candidate `dev_006_horizon_guard_scheduler.py` (SHA-256: `06db94e5`) was constructed with exact one-factor isolation over DEV-005: adds `HORIZON_GUARD_THRESHOLD = 500`, rejecting transitions from baseline to specialized if remaining steps $< 500$ (`REJECT_HORIZON`).
- **Retrospective Kill-Test Results (Partition 247000–247049)**:
  - Evaluated on the 50 retrospective DEV-005 seeds:
  - Exactly **48 of 50 seeds were bit-for-bit identical ($0.00 difference)**.
  - Exactly the **2 late-entry loss seeds were converted to $0.00 ties**:
    - Seed 247025: -$1,844.00 $\to$ **$0.00** (+$1,844.00 recovered)
    - Seed 247034: -$5,393.00 $\to$ **$0.00** (+$5,393.00 recovered)
  - Total recovered surplus: **+$7,237.00**; Zero damage to positive controls.

### 15.1 Critical Factual Correction: The Sheep Purchase Refutation
In `EXP-DEV-005/FORENSIC_AUDIT.md`, the authors asserted that Step 288 losses occurred because "buying sheep at Step 288 incurs immediate cash outflow that cannot amortize before game end."
- **Authoritative Tape Audit (`EXP-DEV-006_HORIZON_KILLTEST/FORENSIC_AUDIT.md:133`)**:
  - An inspection of the frozen tape schedules revealed that **no sheep purchases are proposed at or after tape-step 288 on EITHER tape!**
  - In `_V56_YARN_ROUTE`, the final sheep purchase occurs at Step 265.
  - In `_V55_LIVE_ROUTE` (Backbone), sheep purchases occur at Steps 1, 195, and 313.
  - A switcher at Step 288 spends **$0.00 on livestock capital**! In fact, switching to the YARN suffix causes the agent to **skip the baseline's Step 313 sheep purchase**!
- **The Real Causal Cascade at Step 288**:
  - The agent adopted the YARN operating suffix against a cow-heavy herd (9 cows, 4 sheep), buying **1,895 units of wheat-product feed** with no matching sheep flock.
  - **Seed 247025 Loss Mechanism**: Dominated by **own-farm operating mismatch** (-$4,310 own-farm effect vs counterfactual).
  - **Seed 247034 Loss Mechanism**: Dominated by **market-price / opponent interaction** (+630 own farm, but feed buying moved shared market prices to boost the backbone opponent's sales by +$6,023!).
- **Conclusion**: H=500 is a valid empirical filter blocking the cascade, but the theoretical explanation of "unamortized livestock capital" is refuted.

---

# 16. DEV-006 DISCOVERY — HORIZON GUARD EVALUATION ON FRESH SEEDS

- **Protocol & Partition**:
  - Protocol V1.5 (`e52a057`), Freeze commit `8bc8248`.
  - Evaluated on certified virgin seeds **248000–248049 ($N=50$, 100 paired CRN matches)** against Sub 56146971.
- **Results (`experiments/EXP-DEV-006/FINAL_REPORT.md`)**:
  - Paired Mean Delta: **+$290.90** ($t = 1.40, p = 0.168, 95\%\text{ CI } [-\$126.79, +\$708.59]$).
  - Head-to-Head Record: **2 Wins / 0 Losses / 48 Ties** (4.0% WR, 0.0% LR, 96.0% TR).
  - Worst Seed Delta: **$0.00**; Maximum Win: **+$8,738.00**.
  - DEV-005 Diagnostic Arm: Mean -$5.30, 2W / 2L / 46T (Min: -$8,282.00).
- **Replication of the Mechanism**:
  - In the DEV-005 arm, exactly 2 seeds attempted first-time Step 288 entry:
    - Seed 248007: lost -$8,282.00 in DEV-005 $\to$ converted to **$0.00 tie** in DEV-006.
    - Seed 248009: lost -$6,528.00 in DEV-005 $\to$ converted to **$0.00 tie** in DEV-006.
  - Exactly **48 of 48 other seeds were bit-identical**.
  - Combined cross-cohort evidence: **4 of 4 observed late-entry losses eliminated**, 0 prevented wins, 0 new losses.
- **Outlier Sensitivity & Caution**:
  - Top-1 win accounted for 60.1% of total surplus; top-2 wins accounted for 100%.
  - 10% trimmed mean: **$0.00**; Median: **$0.00**; $p = 0.168$ (not statistically significant).
  - **Verdict**: **MECHANISM REPRODUCTION CONFIRMED; GENERALIZED ECONOMIC ADVANTAGE UNPROVEN**.

---

# 17. DEV-006 QUALIFICATION — STAGE 2 CONFIRMATION ON RESERVED COHORT

- **Protocol & Partition**:
  - Qualification Protocol (`1484e00`), Freeze commit `36c9f77`.
  - Evaluated on Stage-2 reserved cohort **Seeds 50050–50099 ($N=50$, 200 games total)** against Sub 56146971 and diagnostic DEV-005.
  - **Disclosed Caveat**: Partition 50050–50099 was previously simulated in EXP-DEV-002 under an unrelated treatment (`dev_002_hedged_portfolio`). It was virgin with respect to DEV-005/DEV-006.
- **Results (`experiments/EXP-DEV-006/QUALIFICATION/QUALIFICATION_FINAL_REPORT.md`)**:
  - Paired Mean Delta: **+$517.58** ($t = 1.7586, p = 0.084898, 95\%\text{ CI } [-\$73.882, +\$1,109.042]$).
  - Record: **3 Wins / 0 Losses / 47 Ties** (6.0% WR, 0.0% LR, 94.0% TR).
  - Worst Loss: **$0.00**; Best Win: **+$9,881.00**.
  - 10% Trimmed Mean: **$0.00**; Median: **$0.00**.
- **The Inactive Guard (Zero Exposure)**:
  - **The H=500 guard fired exactly ZERO times on ZERO seeds** (`QUALIFICATION_HORIZON_GUARD_EVENTS.csv` was empty).
  - All 68 Step-288 specializations were maintenance of pre-existing Step-216 routes. Zero seeds attempted first-time entry at Step 288.
  - Consequently, **DEV-006 was behaviorally identical to DEV-005 on all 50 seeds**.
- **Predeclared Gate Evaluation**:
  - **Gate A (Statistical Significance: $t > 1.96, p < 0.05$)**: **NOT PASS** ($t = 1.7586, p = 0.0849$).
  - **Gate B (Mechanism Demonstration: fewer late failures than DEV-005)**: **NOT PASS** (0 vs 0; guard was inert).
  - **Gate C (Tail Risk: min $\ge -\$800$)**: **PASS** (min $0.00).
  - **Gate D (Integrity & Parity)**: **PASS** (100% hash and parity match).
- **Final Decision**: **INCONCLUSIVE**.
  - This is NOT qualification (Gate A missed).
  - This is NOT failure (Gate C passed, zero harm, zero losses).
  - This is NOT evidence to retune or sweep H.
  - Outcome: The cohort did not present the failure mode the guard exists to fix.

---

# 18. DEV-007 CURRENT PROTOCOL — MECHANISM EXPOSURE STUDY

- **Protocol Specification**:
  - Protocol Document: `experiments/EXP-DEV-007_MECHANISM_EXPOSURE/PROTOCOL.md`
  - Recomputed SHA-256: `d10ee1857b380ee1254a29bf9fc1a49e33c10783b9e49ef1e68beb75bab80cff` [MATCH]
  - Freeze Git Commit: `db1c7ebe6e676460d89e457b88959d6e07dd097d`
  - **Execution State**: **STRICTLY UNEXECUTED (0 seeds simulated)**.
- **Proposed Cohort**:
  - Seeds **310000–310499 inclusive ($N=500$ seeds, 2,000 matches)**.
  - Selected by deterministic round-number anchoring strictly above all historical and reserved ranges (minimum distance: 9,951 seeds above 300049; 95,751 seeds above final holdout).
- **Exact Trigger Predicate (Frozen Definition)**:
  A qualifying late-entry exposure occurs in the DEV-005 diagnostic arm at checkpoint step $s$ iff:
  1. $s \in \{72, 144, 216, 288\}$.
  2. $\text{best\_delta} \ge \tau$ ($1,500.0$ coins).
  3. $\text{money} \ge L_{\min}$ ($100.0$ coins).
  4. Required commercial shop is unlocked in `town.unlocked_shops`.
  5. $720 - s < 500$ (holds iff $s = 288$).
  6. `active_plan == "BASELINE_BACKBONE"` at checkpoint entry (transition event, including re-entry after reversion).
- **Three Estimands**:
  - **Estimand 1 (Unconditional Performance)**: DEV-006 minus baseline across all 500 seeds.
  - **Estimand 2 (Trigger Incidence)**: $k / N$ natural occurrence rate with Clopper-Pearson 95% CI.
  - **Estimand 3 (Conditional Mechanism Effect)**: DEV-006 minus DEV-005 paired contrast strictly among the $k$ exposed seeds.
- **Mandatory Auditor Injunction**:
  - Do NOT execute DEV-007.
  - Do NOT design or run a test runner.
  - Do NOT alter the frozen protocol.

---

# 19. DMITRII ARCHITECTURE DECOMPOSITION

The complete static decompilation of `extracted_agents/dmitrii_lb2800/` conducted in `EXP-ARCH-001` decoded all 13 strategy tapes in `actions.json` across 719 turns:

### 19.1 The Three Operating Regimes
1. **Steps 0–143 (Days 0–5) — Shared Opening**:
   - Executes **Tape 0 on 100% of games**. All other tapes are byte-dead here.
   - **Day 0 Blast**: Buys 12 Melon + 7 Wheat seeds and plants all 19; buys 2 Cows + 2 Sheep; builds 4 Pastures; buys 31 Wheat as feed. Deploys **$2,842 of $3,000 starting cash (94.7%)**.
   - Hires 3–5 hands/day at dawn; collects fertilizer daily; first sale is Fertilizer at Step 30.
2. **Steps 144–647 (Days 6–26) — Selected Continuation**:
   - The selected strategy tape executes for exactly 504 steps.
   - Evaluated exactly **ONCE at Step 144** based on the first two revealed shops.
   - **49 of 64 shop pairs select Strategy 0 (Default)**. Only shop pairs containing `YARN_STORE` branch into Strategies 1–12.
   - All 13 tapes share an identical planting schedule (Melon 12 $\to$ Wheat ~163 $\to$ Strawberry 33 $\to$ Carrot 31) and 16–17 head of livestock.
3. **Steps 648–718 (Days 27–29) — Forced Terminal Convergence**:
   - At Step 648 dawn, **ALL games converge to Tape 2**. All other tapes are dead here.
   - Drips shift to bulk market clearings ($1,000$ unit lots) from Step 685.

### 19.2 Real-Time Control & Reactive Overlays
Dmitrii is not pure precomputation. It executes two local reactive repairs and a terminal optimizer:
1. **Weed Repair Queue (`repair_weeds`)**:
   When a scheduled `PLANT` or `BUILD` is blocked by a weed, the agent immediately prepends a `DIG` action to that worker's queue. Sunk work is preserved; queues are wiped at dawn.
2. **One-Turn Advance Sales (`advance_sales`)**:
   Checks whether next turn's scheduled `SELL` orders can be pulled into the current turn (requiring stock coverage, price $\ge 2$, excluding Wheat/Fertilizer). Relieves shed pressure and captures transient price peaks. Next turn's order is subtracted.
3. **7-Turn Shadow Terminal Optimizer (`terminal_planner.py`, Steps 712–718)**:
   Runs a bounded forward search simulating physical worker paths for the final 7 turns. Adopts alternative worker routes **only if they achieve row-wise physical unit dominance** over the baseline tape and satisfy 10+ strict safety guards (no-stealing, cash feasibility, inventory non-negativity).

---

# 20. EARLIER DMITRII ANALYSIS VS NEWLY DISCOVERED INFORMATION

| Dimension | Earlier Analysis Belief | Verified Fact (EXP-ARCH-001 Reconstruction) | Correction & Impact |
| :--- | :--- | :--- | :--- |
| **Strategy Space** | "Dmitrii has 13 distinct macro economic strategies." | **Dmitrii runs exactly ONE agronomic economy** with 12 execution/routing variants. | Planting schedules, herd sizes (16–17), and land purchases are identical across all 13 tapes. |
| **Shop Routing** | "Complex multi-shop adaptive router." | **YARN-only router.** 49 of 64 shop pairs play Strategy 0 default. | Non-YARN shops are completely ignored at Step 144. |
| **Terminal Execution**| "Each strategy runs its own specialized terminal liquidation." | **Forced convergence to Tape 2 at Step 648**. | All strategies converge to a single validated harvest/clearing tail. |
| **Precomputation vs Reactive** | "Dmitrii is purely precomputed open-loop tapes." | **Hybrid architecture ($E = B + C + D$)**. | Live weed repair queue, 1-turn sale advances, and 7-turn shadow optimizer adapt to live state. |
| **Terminal Optimizer** | "Global replanner." | **Strictly bounded 7-turn optimizer with unit dominance**. | Simulates 7 turns with fixed market models; rejects any re-routing that fails physical dominance. |

---

# 21. CURRENT ARCH-001 STATUS

- **Status**: **COMPLETE & COMMITTED** (`d6ddc36`, 2026-09-15 10:48 UTC).
- **All 11 Mandated Deliverables Delivered**:
  1. `README.md`: Overview of the 13-tape decompilation.
  2. `SOURCE_MAP.md`: Function-by-function mapping of `extracted_agents/dmitrii_lb2800/`.
  3. `STRATEGY_TAPE_DECODER.md`: Complete schedule and narrative breakdown of all 13 tapes.
  4. `STRATEGY_SUMMARY.csv`: Metrics table across all 13 tapes (spend, hires, animals, crops).
  5. `STRATEGY_COMPARISON.md`: Pairwise diff analysis and L1 distance metrics.
  6. `SHOP_ROUTER_ANALYSIS.md`: 64-entry shop-pair routing matrix.
  7. `REACTIVE_OVERLAY_ANALYSIS.md`: Algorithmic analysis of weed repairs and sales advances.
  8. `TERMINAL_PLANNER_ANALYSIS.md`: Simulation model and dominance guard decomposition.
  9. `TRANSFERABILITY_MATRIX.md`: Evaluation of Dmitrii mechanisms against our architectures.
  10. `HYPOTHESES.md`: 20 categorized, independently testable transfer hypotheses (H1–H20).
  11. `FINAL_ARCHITECTURE_REPORT.md`: Authoritative synthesis confirming hypothesis $E = B + C + D$.
- **Strict Compliance**: Zero candidates created; zero source code modified; awaiting independent review.

---

# 22. REJECTED HYPOTHESES

| Hypothesis ID | Original Claim / Description | Reason for Rejection | Definitive Evidence Artifact |
| :--- | :--- | :--- | :--- |
| **`HYP-REJ-01`** | Unhedged dynamic crop substitution based on Days 3/6 shop signals adds value. | Breached -$800 tail limit (-$2,388 on Seed 50018); mean dependent on single outlier. | `experiments/EXP-DEV-001/FINAL_REPORT.md` |
| **`HYP-REJ-02`** | Day-11 Tomato specialization in Pizza worlds yields +$3,942 cash alpha. | Cherry-picked single seed (50042); 6-seed ensemble averaged -$5,382.67; 18/18 sweeps lost. | `scratch/true_pizza_sweep_results.json` |
| **`HYP-REJ-03`** | "No exploitable resource slack exists anywhere in V2." | Experiment was completely broken in code (unwatered crops rotted; daily hiring). | `research/slack_capacity_real_option_report.md` |
| **`HYP-REJ-04`** | Live losses were caused by an "$800 dawn hiring collapse". | Replay parser bug (`units` vs `hands`). Eldritch had $9.8k cash, hired 9 hands, paid $88. | `DEVELOPMENT_EVIDENCE_LEDGER.md:51` |
| **`HYP-REJ-05`** | Step 696 order truncation was the causal root of V2's worst losses against Dmitrii. | Forcing orders worsened losses on 3 of 7 seeds; cash diverged hundreds of turns earlier. | `scratch/test_step696_causal.py` |
| **`HYP-REJ-06`** | Mid-flight route reversal caused DEV-004 losses (Commitment Hysteresis Hypothesis). | Hysteresis recovered only 20.56% of losses; worsened 7 seeds; ruined positive control 246048. | `experiments/EXP-DEV-005_KILLTEST/VERDICT.md` |
| **`HYP-REJ-07`** | Ad-hoc crop swapping on compiled macro routes is viable. | Crop substitution without worker re-pathing causes harvest failure and vine rot (-$14.7k loss).| `experiments/EXP-DEV-003/FINAL_REPORT.md` |
| **`HYP-REJ-08`** | Step 288 losses occurred because the agent bought sheep that couldn't amortize. | Frozen tape audit proved 0 sheep proposed or bought at/after 288; $0 livestock outlay. | `experiments/EXP-DEV-006_HORIZON_KILLTEST/FORENSIC_AUDIT.md` |
| **`HYP-REJ-09`** | V2 and Dmitrii execute 100.0% bit-for-bit identical physical agronomy. | Diverged physically for 460 turns on Seed 50081 (missed sheep); terminal MC planners differ. | `AUDIT2_REPRODUCTIONS.md:25` |
| **`HYP-REJ-10`** | V2 has statistically confirmed global superiority over Dmitrii. | 95% Confidence Interval spans zero `[-$2.29, +$51.52]` ($p = 0.0727$). | `scratch/audit2_1_recompute_v2_stats.py` |

---

# 23. SURVIVING HYPOTHESES

| Hypothesis ID | Statement | Current Supporting Evidence | Required Next Test / Status |
| :--- | :--- | :--- | :--- |
| **`HYP-SURV-01`** | **Residual Market Preemption Alpha**: Preempting market sales on cash deficits maintains alpha over passive controls. | Supported by holdout (+1,984 margin) and live leaderboard (+46 Elo over control). | Maintained in frozen live submission 56146971. |
| **`HYP-SURV-02`** | **Confirmed-Shop Gating Safety**: Delaying physical route commitment until matching shops unlock eliminates premature speculation failures. | Supported by EXP-DEV-005 (loss rate collapsed from 30% to 4%; saved 13 disaster seeds). | Proven in Discovery; incorporated into DEV-005/006. |
| **`HYP-SURV-03`** | **H=500 Late-Entry Horizon Guard**: Rejecting new route specialization with $<500$ steps remaining eliminates late-entry cascade losses. | Supported by 4/4 loss eliminations across DEV-006 Killtest and Discovery. | Inconclusive in Qualification; subject of EXP-DEV-007. |
| **`HYP-SURV-04`** | **Static 19S/0T Strawberry Dominance**: Pure strawberry strictly dominates all static hybrid crop mixtures (17S/2T, 15S/4T) under open-loop play. | Supported by 100-match portfolio grid (19S/0T ranked #1 on mean cash, margin, and risk). | Established agronomic bedrock. |
| **`HYP-SURV-05`** | **Hybrid Architecture Superiority ($E = B + C + D$)**: Robust macro plan + local reactive repair + short-horizon shadow optimization outperforms repeated global replanning. | Supported by full tape and controller decompilation of Dmitrii LB2800 in EXP-ARCH-001. | Architectural foundation for future transfer experiments. |
| **`HYP-SURV-06`** | **Dominance-Gated Terminal Optimization (H1)**: A 7-turn shadow optimizer adopting routes only under unit dominance converts stranded terminal cargo safely. | Observed in Dmitrii `terminal_planner.py`; zero downside risk under row-wise dominance. | Interface-clean; candidate for isolated transfer study. |

---

# 24. EVIDENCE HIERARCHY

All findings across the Kaggriculture program are classified into six rigorous epistemic tiers:

```
[TIER 1: PROVEN / IMMUTABLE FACTS]
  ├── Cryptographic Artifact Hashes (Bit-Exact on Disk)
  ├── Live Deployment Logs & Manifests (Submissions 56146971, 56146947)
  ├── 14-Vector Leakage Containment & AST Security
  └── MAX_ORDERS = 10 Engine Truncation Law

[TIER 2: STRONGLY SUPPORTED EMPIRICAL TRUTHS]
  ├── Residual Market Preemption Alpha (Holdout +1984, Live +46 Elo)
  ├── Confirmed-Shop Gating Risk Reduction (EXP-DEV-005: 86.7% loss reduction)
  ├── 19S/0T Strawberry Dominance Over Static Mixtures
  └── Disproof of Sheep Outlay at Step 288 ($0.0 spent)

[TIER 3: PROMISING BUT UNQUALIFIED MECHANISMS]
  ├── H=500 Horizon Guard (4/4 losses eliminated, but p=0.085/0.168, inert in Qual)
  └── Whole-Route Macro Scheduling (Upside preserved, but needs horizon gate)

[TIER 4: INCONCLUSIVE / UNTESTED RESULTS]
  ├── DEV-006 Qualification Outcome (Guard had 0 exposure; t=1.76)
  └── DEV-007 Prospective Exposure (Unexecuted, N=500 cohort frozen)

[TIER 5: ARCHITECTURAL HYPOTHESES]
  ├── Dmitrii E = B + C + D Decomposition
  └── Dominance-Gated Terminal Reaper / Advance-Sales Overlays (H1–H4)

[TIER 6: REFUTED / RETRACTED NARRATIVES]
  ├── $800 Dawn Hiring Collapse Myth (Parser bug)
  ├── Tomato Specialization +$3,942 Alpha (Cherry-picked outlier)
  ├── "No Slack Exists" Theorem (Bugged script)
  ├── Step 696 Order Truncation as Loss Root Cause (Counterfactual disproof)
  ├── Hysteresis Commitment Guard (Worsened 7 seeds, destroyed positive control)
  └── 100% Bit-for-Bit Physical Agronomy Identity (Refuted on Seed 50081)
```

---

# 25. FROZEN RANGES / ARTIFACTS TABLE

| Seed Cohort | Size ($N$) | Epistemic Status | Governing Document / Reason | Permitted Access |
| :--- | :---: | :---: | :--- | :---: |
| **`214200–214249`** | 50 | **VIRGIN FINAL HOLDOUT** | `DEVELOPMENT_HOLDOUT_REGISTRY.md` — Reserved for final release | **STRICTLY QUARANTINED (0 SIMS)** |
| **`310000–310499`** | 500 | **FROZEN PROSPECTIVE COHORT** | `EXP-DEV-007 PROTOCOL.md` — Pre-registered exposure study | **LOCKED UNTIL DEV-007 EXECUTION** |
| **`50050–50099`** | 50 | **CONSUMED QUALIFICATION** | Consumed by EXP-DEV-002 and EXP-DEV-006 Qualification | **DO NOT REUSE WITHOUT PROTOCOL** |
| **`50000–50049`** | 50 | **CONSUMED DISCOVERY** | Consumed by EXP-DEV-001 and EXP-DEV-002 Discovery | **EXHAUSTED DISCOVERY** |
| **`50100–50149`** | 50 | **AUDITED BENCHMARK** | Consumed by Audit 2 150-seed baseline scan | **BENCHMARK REFERENCE ONLY** |
| **`50150–50199`** | 50 | **PERMANENTLY CONTAMINATED** | Compromised by Phase 3 census & live match 107564294 | **PERMANENTLY BANNED** |
| **`60000–60049`** | 50 | **SWEEP CONTAMINATED** | Compromised by legacy hyper-parameter sweeps | **PERMANENTLY BANNED** |
| **`245000–245049`** | 50 | **CONSUMED DEV-003** | Consumed by EXP-DEV-003 Discovery | **EXHAUSTED DISCOVERY** |
| **`246000–246049`** | 50 | **CONSUMED DEV-004** | Consumed by EXP-DEV-004 Discovery & DEV-005 Killtest | **EXHAUSTED DISCOVERY** |
| **`247000–247049`** | 50 | **CONSUMED DEV-005** | Consumed by EXP-DEV-005 Discovery & DEV-006 Killtest | **EXHAUSTED DISCOVERY** |
| **`248000–248049`** | 50 | **CONSUMED DEV-006** | Consumed by EXP-DEV-006 Discovery | **EXHAUSTED DISCOVERY** |

---

# 26. OPEN QUESTIONS

The research program faces two completely independent, unconfounded questions:

### QUESTION A: Does the frozen DEV-006 H=500 mechanism materially matter?
- **Current State**: The H=500 guard eliminated 4/4 late-entry losses across retrospective and Discovery cohorts, but faced zero trigger exposures during Qualification on 50050–50099 ($t=1.76, p=0.085$).
- **Unresolved Aspect**: What is the true natural incidence rate of the late-entry trigger across a large unbiased sample, and what is its conditional effect?
- **Mechanism Addressing This**: **EXP-DEV-007** (500 seeds, prospective exposure protocol).

### QUESTION B: Is our whole-route switching architecture fundamentally sub-optimal?
- **Current State**: EXP-ARCH-001 proved that Dmitrii does not execute multiple macroeconomic routes. Dmitrii runs ONE agronomic economy, branches only on early YARN, converges at Step 648, and relies on local reactive repairs + a 7-turn shadow optimizer.
- **Unresolved Aspect**: Are our repeated checkpoint re-evaluations (Steps 72, 144, 216, 288) and complex route switching adding unnecessary cascade risk, when a single early macro choice + local repairs would achieve higher stability?
- **Mechanism Addressing This**: **Transfer Hypotheses H1–H4** from EXP-ARCH-001.

**CRITICAL MANDATE**: **DO NOT MERGE QUESTION A AND QUESTION B**. Question A is an empirical validation of an existing frozen candidate; Question B is a macroeconomic architectural investigation.

---

# 27. RECOMMENDED NEXT DECISION POINT

The program is at an architectural fork. The research director must make an explicit decision between two independent pathways:

1. **Option 1: Execute DEV-007 to Close Question A**:
   - Run the pre-registered `EXP-DEV-007_MECHANISM_EXPOSURE` protocol on cohort 310000–310499 ($N=500$, 2000 games).
   - Characterize the true incidence of the Step-288 trigger (Estimand 2) and evaluate conditional/unconditional performance (Estimands 1 and 3).
   - If H=500 proves beneficial and generalizable, DEV-006 can be formally staged for holdout qualification. If inert or weak, retire H=500.

2. **Option 2: Freeze DEV Track and Pursue Architectural Transfer (Question B)**:
   - Recognize that DEV-006 represents incremental patching of a multi-route scheduler.
   - Author a new, prospective pre-registered experiment protocol (`EXP-ARCH-002`) testing isolated Dmitrii transfer candidates on fresh seeds:
     - Candidate H1: Dominance-gated 712–718 terminal reaper grafted onto V54++ baseline.
     - Candidate H2: Advance/subtract one-turn sales overlay vs V54 residual preemption.
     - Candidate H4: Fertilizer collection and drip-sale overlay.

---

# CURRENT STATE OF KNOWLEDGE

### 1. PROVEN / STRONGLY SUPPORTED
- Standalone compilation of live submissions (`56146971` and `56146947`) with zero behavioral drift ($0 / 72,000$ action divergence) [GRADE A].
- Residual market preemption delivers positive alpha over passive controls in holdout (+1,984 margin) and live play (+46 Elo) [GRADE A].
- Confirmed-shop gating eliminates premature speculative commitment, collapsing whole-route loss rate from 30% to 4% [GRADE A].
- Pure 19S/0T Strawberry Bedrock strictly dominates all static hybrid crop allocations [GRADE A].
- MAX_ORDERS = 10 is strictly enforced by the simulation engine [GRADE A].
- Step 288 late-switch losses involved $0.00 livestock capital outlay (sheep purchase myth refuted) [GRADE A].
- Dmitrii runs ONE macro agronomic economy with 12 execution variants and forced 648 convergence [GRADE A].

### 2. PROMISING BUT UNPROVEN
- H=500 late-entry horizon guard: eliminated 4/4 observed late-entry losses across cohorts, but missed statistical significance in Discovery ($p=0.168$) and faced zero exposure in Qualification ($p=0.085$) [GRADE B/C].
- Whole-route macro scheduling (DEV-005/006): captures large upside (+5.4k to +13k wins), but requires confirmation gating and runway protection.
- Dominance-gated 712–718 terminal reaper (H1) and advance/subtract sales (H2) as interface-clean alpha transfers.

### 3. REJECTED / RETIRED
- Unhedged dynamic crop substitution (EXP-DEV-001) [FAILED].
- Hedged adaptive crop substitution without whole-route pathing (EXP-DEV-002) [RETIRED].
- Ad-hoc crop swapping on compiled routes (EXP-DEV-003) [FAILED].
- Commitment hysteresis to prevent route reversions (EXP-DEV-005 KILLTEST) [REJECTED / MIXED_UNSAFE].
- $800 dawn hiring collapse narrative (parser bug) [RETRACTED].
- Pizza-world +$3,942 tomato alpha (cherry-picked outlier) [RETRACTED].
- "No resource slack exists in V2" (bugged script) [RETRACTED].
- Step 696 order truncation as loss root cause [REFUTED].
- 100% bit-for-bit physical agronomy identity between V2 and Dmitrii [REFUTED].
- V2 proven global statistical superiority over Dmitrii ($p > 0.05$) [OVERCLAIMED].

### 4. UNKNOWN / NEEDS EXPERIMENT
- Natural population incidence of the Step-288 trigger across large seed distributions (subject of DEV-007).
- Unconditional expected value impact of DEV-006 over baseline across N=500 seeds (subject of DEV-007).
- Whether single-checkpoint routing {144} outperforms multi-checkpoint scheduling {72, 144, 216, 288} in closed-loop play (H5).
- Whether dominance-gated terminal harvesting recovers stranded inventory on V54++ baseline (H1).

---

# CURRENT FROZEN STATE

- **Frozen Live Kaggle Challenger**: `candidates/compiled_v54_plus_residual.py` (Submission `56146971`, SHA-256: `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb`).
- **Frozen Live Kaggle Control**: `candidates/compiled_v54_plus_shop.py` (Submission `56146947`, SHA-256: `f651ccd220e701968bc33579812d8917da63f5b0582f2fd0d363fa6a16ffd8b8`).
- **Frozen Diagnostic Candidate**: `candidates/closed_loop_architecture/dev_005_confirmed_shop_scheduler.py` (SHA-256: `f52b168619e47bea6a052faff890fc84804cb39b47392d247139967f910e2a78`).
- **Frozen Stage 2 Candidate**: `candidates/closed_loop_architecture/dev_006_horizon_guard_scheduler.py` (SHA-256: `06db94e59e2c271b5490aad78fdb760bd8a250f28ec4407de2d2f6be0644f5eb`).
- **Frozen Prospective Protocol**: `experiments/EXP-DEV-007_MECHANISM_EXPOSURE/PROTOCOL.md` (SHA-256: `d10ee1857b380ee1254a29bf9fc1a49e33c10783b9e49ef1e68beb75bab80cff`, Git commit `db1c7ebe`).
- **Certified Virgin Holdout**: Seeds `214200–214249` ($N=50$, strictly quarantined, 0 simulations).

---

# CURRENT EXPERIMENTS IN FLIGHT

1. **EXP-DEV-007_MECHANISM_EXPOSURE**:
   - Status: **FROZEN & PENDING EXECUTION** (Pre-registration freeze committed under `db1c7ebe`).
   - Planned Cohort: Seeds `310000–310499` ($N=500$, 2000 games).
   - Execution State: **0 simulations launched; no runner constructed**.
2. **EXP-ARCH-001_DMITRII_POLICY_DECOMPOSITION**:
   - Status: **COMPLETED & COMMITTED** (Git commit `d6ddc36`).
   - Deliverables: All 11 analysis reports and transfer matrices delivered in repository.

---

# NEXT DECISION REQUIRED

The research team must decide:

> **DO WE EXECUTE EXP-DEV-007 (N=500 exposure study to resolve Question A on the DEV track), OR DO WE PIVOT TO PROSPECTIVE ARCHITECTURAL TRANSFERS (Question B, testing H1 dominance reaper / H2 advance sales from EXP-ARCH-001)?**

*Execution is halted in compliance with all safety and governance mandates. Awaiting user determination.*
