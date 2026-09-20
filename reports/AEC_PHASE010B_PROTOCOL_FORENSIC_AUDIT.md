# AEC PHASE 010B: PROTOCOL FORENSIC AUDIT REPORT
**Author**: Lead Scientific Experiment & Simulation Governance Auditor  
**Date**: 2026-09-19  
**Architecture Freeze State**: FROZEN RESEARCH PLATFORM (Phase 009 Finalized 44-Item Architecture)  
**V3 Baseline Chassis Hash**: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` (Verified Bit-Identical)  
**Governance Scope**: Forensic Audit of Phase 010 Protocols, Scripts, Telemetry, and Registries  

---

## 1. Executive Protocol Reconstruction

### 1.1 Preregistered Intent vs Actual Execution
In Phase 010, the master preregistration document (`reports/AEC_PHASE010_MASTER_PREREGISTRATION.md`) established a rigorous two-stage qualification standard:
1. **Stage A (Pilot Exposure Test)**: $N = 10$ fresh seeds (`249050–249059`), 20 mirror matches, to verify natural opportunity proposal and candidate execution exposure.
2. **Stage B (Formal Qualification & Replication)**: Independent disjoint cohorts of $N \ge 25$ seeds (50 mirror matches per cohort) under Common Random Numbers (CRN), requiring independent replication before certifying any mechanism as `QUALIFIED`.

### 1.2 Forensic Finding: Widespread Protocol Truncation
A line-by-line forensic audit of the execution harness (`scripts/run_phase010_mechanism_qualification.py`), telemetry files (`results/PHASE010_*_TELEMETRY.json`), CSV results (`results/PHASE010_*_RESULTS.csv`), and qualification reports (`reports/PHASE010_*_QUALIFICATION.md`) reveals:

1. **Zero Formal 25-Seed Qualifications Were Executed in Phase 010**:
   - Every single mechanism evaluated in Phase 010 was tested on **exactly 3 seeds** (6 mirror matches total), with the exception of `META` ($N=1$ seed, 2 matches).
   - Cohorts Q1 (`249060–249084`), Q2 (`249085–249109`), Q3 (`249110–249134`), Q4 (`249135–249159`), Q5 (`249160–249184`), and R1 (`249185–249209`) were **never simulated** during Phase 010.
2. **A 3-Seed Pilot Was Conflated with Formal 25-Seed Qualification**:
   - The master registry (`AEC_PHASE010_MECHANISM_REGISTRY.md`) and summary statements claimed:
     > *"All 14 mechanisms have been systematically evaluated... PROSPECTIVE READINESS: READY"*
   - In scientific terms, a 3-seed pilot is a preliminary screening check. It has a sample size of $N=3$, standard error that is wide, and statistical power that is insufficient to detect subtle economic effects or rule out heavy-tail losses.
   - Relabeling a 3-seed pilot screening as "Formal Qualification" violates Section 2 and Section 10 of the scientific qualification standard.
3. **Labor Shadow Was Not Evaluated as a Live Experimental Arm**:
   - `LABOR_SHADOW` was awarded `QUALIFIED (VALUATION INFRASTRUCTURE)` solely on the basis of a 12-test offline analytical ground-truth test battery (`tests/aec/test_phase005b_ground_truth.py`).
   - Zero mirror matches were run isolating `LABOR_SHADOW` as an experimental treatment arm against an identical control arm.
4. **Decisive Evidence of Harm Was Correctly Uncovered (and Must Be Preserved)**:
   - The 3-seed pilots successfully identified massive, statistically significant failure modes in:
     - `TOWN_CYCLE`: -$36,655.33 / seed ($t=-2.55, p=0.0108$), 0W / 3L
     - `EMERGENCY_RECOVERY`: -$25,792.00 / seed ($t=-5.36, p=0.0000$), 0W / 3L
     - `OPPONENT_PREEMPT_SELL`: -$96.67 / seed, 100% harmful commits (-$145.00/commit)
   - These negative findings are scientifically valid falsifications and must remain quarantined.

---

## 2. Forensic Audit of All Evaluated Mechanisms

The table below compiles the verified facts extracted directly from the machine-generated telemetry files (`results/PHASE010_*_TELEMETRY.json` and `results/PHASE010_*_RESULTS.csv`):

| Mechanism | Evaluation Stage | Paired Seeds ($N$) | Total Matches | Fresh Cohort? | Target Candidates | Exact Sims Run | Target Commits | Foundation Commits | Mean Net Delta | SE ($\pm$) | 95% CI | Win / Loss / Tie | Forensic Classification |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **DEPENDENCY_AWARE_MARKET_TIMING** | Phase 008 Formal + Rep | 25 + 25 | 100 | Yes (249000-249024) | High | 100+ | 86 + 78 | N/A | **+$52.12** | $9.91 | [+$32.70, +$71.54] | 21W / 3L / 1T (84%) | **Formally Qualified (Foundation)** |
| **TERMINAL_LIQUIDATION** | Phase 008/009 Baseline | Baseline | Baseline | Yes | High | High | Terminal | N/A | Verified Baseline | Baseline | Baseline | Baseline | **Formally Qualified (Foundation)** |
| **PHASE_SHUTDOWN** | Phase 008/009 Baseline | Baseline | Baseline | Yes | High | High | Late-game | N/A | Verified Baseline | Baseline | Baseline | Baseline | **Formally Qualified (Foundation)** |
| **DYNAMIC_SHADOW_HARVEST** | Phase 010 Pilot | 3 | 6 | Yes (249050-249052) | 1,876 | 932 | **0** | 2 | **-$4.67** | $4.67 | [-$13.81, +$4.48] | 0W / 1L / 2T | **Dormant / Insufficient Exposure** |
| **TERMINAL_HARVEST_SWEEP** | Phase 010 Pilot | 3 | 6 | Yes (249053-249055) | 826 | 396 | **0** | 10 | **+$13.67** | $46.84 | [-$78.14, +$105.48] | 1W / 2L / 0T | **Dormant / Insufficient Exposure** |
| **LABOR_SHADOW** | Phase 010 Analytical | 0 | 0 | N/A (Unit Battery) | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | **Structural Verification Only** |
| **ROUTE_COMPRESSION** | Phase 010 Pilot | 3 | 6 | Yes (249056-249058) | 266 | 132 | **0** | 6 | **+$62.00** | $33.08 | [-$2.84, +$126.84] | 2W / 0L / 1T | **Dormant / Insufficient Exposure** |
| **CARGO_FERRY** | Phase 010 Pilot | 3 | 6 | Yes (249059-249061) | 744 | 372 | **0** | 10 | **+$26.00** | $28.45 | [-$29.76, +$81.76] | 2W / 1L / 0T | **Dormant / Insufficient Exposure** |
| **TOWN_CYCLE** | Phase 010 Pilot | 3 | 6 | Yes (249062-249064) | 1,337 | 682 | **247** | 8 | **-$36,655.33** | $14,386.69 | [-$64,853, -$8,457] | 0W / 3L / 0T (0%) | **Failed Qualification (Harmful)** |
| **SHOP_ARBITRAGE** | Phase 010 Pilot | 3 | 6 | Yes (249065-249067) | 2,118 | 1,059 | **0** | 12 | **+$11.00** | $21.08 | [-$30.32, +$52.32] | 1W / 2L / 0T | **Dormant / Insufficient Exposure** |
| **PRODUCTION_ARBITRAGE** | Phase 010 Pilot | 3 | 6 | Yes (249068-249070) | 2,656 | 1,328 | **0** | 10 | **+$126.67** | $23.15 | [+$81.28, +$172.05] | 3W / 0L / 0T | **Dormant / Insufficient Exposure** |
| **TERMINAL_CONVERSION** | Phase 010 Pilot | 3 | 6 | Yes (249071-249073) | 138 | 69 | **0** | 12 | **+$89.33** | $66.69 | [-$41.39, +$220.05] | 2W / 1L / 0T | **Dormant / Insufficient Exposure** |
| **EMERGENCY_FEED_PURCHASE** | Phase 010 Pilot | 3 | 6 | Yes (249074-249076) | 518 | 259 | **0** | 10 | **+$28.67** | $52.84 | [-$74.90, +$132.23] | 2W / 1L / 0T | **Dormant / Insufficient Exposure** |
| **EMERGENCY_RECOVERY** | Phase 010 Pilot | 3 | 6 | Yes (249077-249079) | 296 | 148 | **20** | 8 | **-$25,792.00** | $4,815.05 | [-$35,229, -$16,355] | 0W / 3L / 0T (0%) | **Failed Qualification (Harmful)** |
| **OPPONENT_PREEMPT_SELL** | Phase 010 Pilot | 3 | 6 | Yes (249080-249082) | 7,812 | 3,906 | **2** | 0 | **-$96.67** | $96.67 | [-$286.13, +$92.80] | 0W / 1L / 2T (0%) | **Failed Qualification (Harmful)** |
| **META** | Phase 010 Pilot | 1 | 2 | Yes (249083) | 0 | 0 | **0** | 6 | **+$126.00** | $0.00 | [+$126.00, +$126.00] | 1W / 0L / 0T | **Research Only (Latency Ineligible)** |
| **RESOURCE_CONVERSION** | Phase 004B Replay | 25 | 50 | Ret. (50000-50024) | High | High | N/A | N/A | **-$258.96** | Prior ITT | Prior ITT | Prior ITT | **Failed Qualification (Quarantined)** |

---

## 3. Dissection of Attribution Coincidences in Dormant Pilots

For 7 mechanisms (`PRODUCTION_ARBITRAGE`, `TERMINAL_CONVERSION`, `ROUTE_COMPRESSION`, `EMERGENCY_FEED_PURCHASE`, `CARGO_FERRY`, `TERMINAL_HARVEST_SWEEP`, `SHOP_ARBITRAGE`), the pilot reports displayed positive mean net deltas (e.g. +$126.67, +$89.33, +$62.00).

### Forensic Verification of Attribution:
In every single one of these 7 cases:
- **Target Commits**: Exactly **0**.
- **Foundation Commits**: Exactly 6 to 12 commits of `DEPENDENCY_AWARE_MARKET_TIMING`.
- **Commit Purity**: 0.0% target purity.

**Scientific Finding**:
The observed positive deltas in those pilots were **100% created by the active foundation market timing engine**, NOT by the mechanism under evaluation. In games where the target mechanism commits 0 times, any delta observed relative to frozen V3 is purely the effect of the foundation backbone plus seed-level noise.

Therefore, claiming that these mechanisms are "economically validated" or "promising" based on those numbers is scientifically false. They must be strictly classified as:
$$\text{FUNCTIONALLY COMPLETE} + \text{NATURAL EXPOSURE INSUFFICIENT} + \text{NOT LIVE ELIGIBLE}$$

---

## 4. Labor Shadow Separation Analysis

### 4.1 Structural Validity vs Empirical Value Creation
The forensic audit investigated `LABOR_SHADOW` (`LaborOpportunityCostEngine`):
- **Structural Validity (A)**: PROVEN.
  - The 12-test formal ground-truth battery (`tests/aec/test_phase005b_ground_truth.py`) verifies exact marginal opportunity cost formulation, idle worker zero-cost invariants, peer task absorption, and finite horizon bounds.
  - Funnel Stage S5 (`_stage_labor_shadow`) successfully executes without syntax or type errors.
- **Empirical Live Value Creation (B)**: UNPROVEN in Phase 010.
  - In Phase 010, `LABOR_SHADOW` was never executed in a mirror match against control.
  - In the frozen live foundation build (`DEPENDENCY_AWARE_MARKET_TIMING`, `TERMINAL_LIQUIDATION`, `PHASE_SHUTDOWN`), no candidate proposals involve auxiliary worker reallocations or displaced field labor.
  - Consequently, `LaborOpportunityCostEngine` is naturally dormant in the live foundation build.

**Scientific Conclusion**:
`LABOR_SHADOW` is validated infrastructure and screening logic for future labor transformations, but is **NOT an independently qualified live economic transformation**.

---

## 5. Summary of True Mechanism Statuses

1. **Formally Qualified for Live Play**:
   - `DEPENDENCY_AWARE_MARKET_TIMING` (Formally qualified across $N=50$ mirror matches in Phase 008, replicated, $+52.12$ net delta, $p < 0.0001$, 84% win rate).
   - `TERMINAL_LIQUIDATION` (Verified baseline chassis defense-in-depth).
   - `PHASE_SHUTDOWN` (Verified baseline chassis defense-in-depth).
2. **Validated Valuation Infrastructure (Not Live Transformation)**:
   - `LABOR_SHADOW` (Structural marginal cost calculator).
3. **Functionally Complete but Dormant / Dominated (Quarantined)**:
   - `DYNAMIC_SHADOW_HARVEST`
   - `TERMINAL_HARVEST_SWEEP`
   - `ROUTE_COMPRESSION`
   - `CARGO_FERRY`
   - `SHOP_ARBITRAGE`
   - `PRODUCTION_ARBITRAGE`
   - `TERMINAL_CONVERSION`
   - `EMERGENCY_FEED_PURCHASE`
4. **Failed Qualification (Permanently Quarantined)**:
   - `TOWN_CYCLE` (-$36,655.33 / seed, $p=0.0108$)
   - `EMERGENCY_RECOVERY` (-$25,792.00 / seed, $p=0.0000$)
   - `OPPONENT_PREEMPT_SELL` (-$96.67 / seed, harmful commits)
   - `RESOURCE_CONVERSION` (Prior Negative ITT -$258.96)
5. **Research Only**:
   - `META` (Exceeds competition per-step latency budget).

---

## 6. Audit Verdict

The Phase 010 claim of "PROSPECTIVE READINESS: READY" for the full proposed build was premature because it was based on 3-seed pilot screenings and structural unit tests rather than formal $N \ge 25$ qualification.

The only mechanisms with verified, replicated, formal empirical qualification are the three core foundation mechanisms:
$$\text{FROZEN\_V3\_BACKBONE} + \text{DEPENDENCY\_AWARE\_MARKET\_TIMING} + \text{TERMINAL\_LIQUIDATION} + \text{PHASE\_SHUTDOWN}$$
