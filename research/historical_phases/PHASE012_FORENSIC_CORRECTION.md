# PHASE 012A: GROUP 2 FORENSIC CORRECTION
## Comprehensive Evidence Reconciliation, Qualification-Status Audit, and Canonical Record Freeze

**Author**: Antigravity AI Research Agent (Phase 012 Lead)  
**Date**: 2026-09-19  
**Repository**: `The-FOOL-00/kagriculture-economic-simulator`  
**Chassis Freeze Hash**: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` (submission_Vj_kc_v3.tar.gz)  
**Empirical Control**: Frozen Live Foundation (`V3 + DEPENDENCY_AWARE_MARKET_TIMING + TERMINAL_LIQUIDATION + PHASE_SHUTDOWN`)  

---

## 1. What Was Originally Claimed

Following the execution of the Phase 012 Group 2 Mechanism Rescue campaign, preliminary reporting in `GROUP2_FINAL_REPORT.md` and related documents claimed:
1. **Match Count**: "Across 110 full 720-step mirror matches..."
2. **Qualification Status**: Characterized all four Group 2 mechanisms (`TOWN_CYCLE`, `EMERGENCY_RECOVERY`, `OPPONENT_PREEMPT_SELL`, `RESOURCE_CONVERSION`) as having "failed formal qualification," implying that all four had undergone and failed the 25-seed formal qualification cohort.
3. **Stage Conflation**: Presented the +112.40 pilot delta for `OPPONENT_PREEMPT_SELL` and its subsequent formal cohort delta (-58.76) without strict hierarchical separation, occasionally citing combined 35-seed metrics (-9.84 pts) rather than establishing the 25-seed formal cohort as the sole authoritative qualification verdict.
4. **Abstention Interpretation**: Characterized `RESOURCE_CONVERSION`'s 0 commits (0.00% commit rate across 13,360 evaluated candidates) as an empirical failure rather than the mathematically correct abstention of a margin-first valuation model in an environment where direct crop farming strictly dominates secondary processing.

---

## 2. What Raw Evidence Actually Shows

An exhaustive audit of Level 1 raw experiment artifacts located in `results/phase012/` reveals the exact ground truth:

### A. Artifact Inventory
- `TOWN_CYCLE_pilot_matches.csv` & `TOWN_CYCLE_pilot_summary.json` (10 seeds, 20 matches)
- `TOWN_CYCLE_custom_1_matches.csv` & `TOWN_CYCLE_custom_1_summary.json` (1 seed exploratory, 2 matches)
- `EMERGENCY_RECOVERY_pilot_matches.csv` & `EMERGENCY_RECOVERY_pilot_summary.json` (10 seeds, 20 matches)
- `EMERGENCY_RECOVERY_custom_1_matches.csv` & `EMERGENCY_RECOVERY_custom_1_summary.json` (1 seed exploratory, 2 matches)
- `OPPONENT_PREEMPT_SELL_pilot_matches.csv` & `OPPONENT_PREEMPT_SELL_pilot_summary.json` (10 seeds, 20 matches)
- `OPPONENT_PREEMPT_SELL_formal_q1_matches.csv` & `OPPONENT_PREEMPT_SELL_formal_q1_summary.json` (25 seeds, 50 matches)
- `RESOURCE_CONVERSION_pilot_matches.csv` & `RESOURCE_CONVERSION_pilot_summary.json` (10 seeds, 20 matches)

### B. Empirical Facts Reconstructed from Level 1 Artifacts
1. **Pilot Screening Was Run for 4 Mechanisms**: `TOWN_CYCLE`, `EMERGENCY_RECOVERY`, `OPPONENT_PREEMPT_SELL`, and `RESOURCE_CONVERSION` were each evaluated across the 10 fresh pilot seeds (`249171..249180`) under 2 mirror matches per seed ($10 \times 2 = 20$ matches each, 80 pilot matches total).
2. **Formal Qualification Was Run for Exactly ONE Mechanism**: Only `OPPONENT_PREEMPT_SELL` advanced to the 25-seed formal qualification cohort `formal_q1` (`249181..249205`), executing 50 mirror matches. `TOWN_CYCLE`, `EMERGENCY_RECOVERY`, and `RESOURCE_CONVERSION` were **never evaluated in a formal cohort**.
3. **Exact Qualification Match Total**: $80 \text{ (pilot)} + 50 \text{ (formal)} = \mathbf{130} \text{ mirror matches}$ across 65 mechanism-seed evaluations (35 unique seeds).
4. **Full Horizon Completion**: In all 130 qualification matches (and both 2-match exploratory runs), `total_steps` is exactly **719** transition steps (representing the complete horizon from step 0 to step 719). Zero early terminations, zero crashes, zero timeouts, and 100% simulator fidelity.

---

## 3. Discrepancies Discovered

### Discrepancy 1: The "110 Matches" Claim
* **Original Claim**: "Total matches executed: 110 full 720-step games (20 matches each for Town Cycle, Emergency Recovery, and Resource Conversion; 70 matches for Opponent Preemption)."
* **Forensic Reconstruction**:
  - Town Cycle Pilot: 20 matches
  - Emergency Recovery Pilot: 20 matches
  - Resource Conversion Pilot: 20 matches
  - Opponent Preemption Pilot: 20 matches
  - Opponent Preemption Formal Q1: 50 matches
  - Sum: $20 + 20 + 20 + 20 + 50 = \mathbf{130}$ qualification matches.
* **Causal Diagnosis**: The original author performed the addition $20 + 20 + 20 + 50 = 110$, which added the three 20-match pilots and the 50-match formal cohort, inadvertently omitting the 20 pilot matches of `OPPONENT_PREEMPT_SELL` from the sum while writing that Opponent Preemption had 70 matches.

### Discrepancy 2: Governance Status Conflation
* **Original Claim**: All four mechanisms "failed formal qualification."
* **Forensic Reality**: Three of the four mechanisms were quarantined or classified dormant after negative or neutral 10-seed pilot screenings. Only `OPPONENT_PREEMPT_SELL` actually completed and failed a formal qualification cohort. Describing the other three as formal qualification failures misrepresents governance protocol and statistical rigor.

### Discrepancy 3: Opponent Preemption Combined Metric vs. Formal Result
* **Original Reporting**: Highlighted a combined 35-seed delta of -9.84 pts.
* **Forensic Reality**: Under scientific governance, the pilot cohort is a screening gate, and the formal cohort is the authoritative test. The authoritative result for `OPPONENT_PREEMPT_SELL` is the 25-seed formal result: **Mean Paired $\Delta = -58.76$ pts**, Median = **-49.00 pts**, 8W / 16L / 1T ($t = -1.331, p = 0.1957$). Furthermore, exact mathematical recomputation of the combined 35 seeds $(-1469 + 1124)/35$ yields **-9.86 pts** (or -9.857), making -9.84 a minor reporting error.

### Discrepancy 4: Mischaracterization of 100% Conversion Abstention
* **Original Reporting**: Grouped `RESOURCE_CONVERSION` under generic failure terms.
* **Forensic Reality**: The second-generation margin-first valuation model evaluated 13,360 opportunities and abstained on 100% of them because the marginal value of worker labor in direct crop cultivation ($>\$40/\text{turn}$) consistently exceeded secondary processing margin ($+\$5\text{--}\$15$). Abstention was the mathematically correct, value-preserving decision, not an engine malfunction.

---

## 4. Corrections Made

1. **Updated Canonical Final Report (`GROUP2_FINAL_REPORT.md`)**:
   - Structured strictly into the 13 required canonical sections (§1–§13).
   - Replaced "110 matches" with the verified count of **130 qualification mirror matches** (80 pilot + 50 formal).
   - Strictly separated Pilot-Only results (`TOWN_CYCLE`, `EMERGENCY_RECOVERY`, `RESOURCE_CONVERSION`) from Formal Qualification results (`OPPONENT_PREEMPT_SELL`).
   - Recorded the exact Level 1 raw metrics and causal attributions.
2. **Corrected Rescue Replay Ledger (`GROUP2_RESCUE_REPLAY.md`)**:
   - Created a comprehensive master ledger detailing mechanism, cohort type, seed range, $N$, mirror match count, control, treatment, candidate count, exact sim count, commit count, paired deltas, and final status.
   - Preserved full seed-by-seed tables matching the raw CSV files.
3. **Corrected Mechanism Matrix (`GROUP2_MECHANISM_MATRIX.md`)**:
   - Added explicit governance columns: `Evidence Stage`, `Pilot / Formal`, `Cohort Size`, `Formal Qualification Completed?`, `Economic Evidence`, `Safety Evidence`, `Functional Status`, `Live Eligible?`, and `Quarantine / Dormant Reason`.
4. **Corrected Machine Manifest (`GROUP2_QUALIFICATION_MANIFEST.json`)**:
   - Updated schema to provide explicit `pilot` blocks and explicit `formal_qualification` blocks (`"performed": true/false`).
   - Removed fictitious formal qualification blocks for the three pilot-only mechanisms.
   - Enforced canonical taxonomy statuses (`FUNCTIONALLY COMPLETE / QUARANTINED` vs `FUNCTIONALLY COMPLETE / DORMANT`).

---

## 5. Exact Cohort Reconciliation

All seeds evaluated in Phase 012 were certified fresh development seeds, verified against governance rules (§0, §2):
* **Primary Holdout** (`340050..340199`): Strictly unvisited.
* **Gate 0.3 Holdout** (`214200..214249`): Strictly unvisited.
* **Prospective Tournament Cohort** (`340300..340349`): Strictly unvisited.
* **Retired Development Cohorts** (`50000..50024`, `249000..249049`, `249050..249110`, `249111..249170`): Zero re-use.

### Reconciled Seed Assignments
1. **Pilot Cohort (`pilot`)**:
   - Seeds: `249171`, `249172`, `249173`, `249174`, `249175`, `249176`, `249177`, `249178`, `249179`, `249180` (N=10 seeds).
   - Applied to: `TOWN_CYCLE`, `EMERGENCY_RECOVERY`, `OPPONENT_PREEMPT_SELL`, `RESOURCE_CONVERSION`.
2. **Formal Qualification Cohort (`formal_q1`)**:
   - Seeds: `249181` through `249205` inclusive (N=25 seeds).
   - Applied to: `OPPONENT_PREEMPT_SELL` only.

---

## 6. Exact Match-Count Reconciliation

| Mechanism | Pilot Seeds | Pilot Matches | Formal Seeds | Formal Matches | Total Unique Seeds | Total Matches |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`TOWN_CYCLE`** | 10 (`249171..80`) | 20 | 0 | 0 | 10 | 20 |
| **`EMERGENCY_RECOVERY`** | 10 (`249171..80`) | 20 | 0 | 0 | 10 | 20 |
| **`OPPONENT_PREEMPT_SELL`** | 10 (`249171..80`) | 20 | 25 (`249181..205`) | 50 | 35 | 70 |
| **`RESOURCE_CONVERSION`** | 10 (`249171..80`) | 20 | 0 | 0 | 10 | 20 |
| **TOTAL QUALIFICATION** | **40** (10 unique) | **80** | **25** (25 unique) | **50** | **35 unique** | **130** |

*Exploratory Runs on Disk*:
- `TOWN_CYCLE_custom_1`: Seed `249171` (2 matches, exploratory run before working-capital liquidity gating).
- `EMERGENCY_RECOVERY_custom_1`: Seed `249171` (2 matches, exploratory run before feed-invariant integration).
- Grand total match rows across all CSV files in `results/phase012/`: **134 matches**.

---

## 7. Qualification-Status Reconciliation

The scientific taxonomy for Phase 012 mechanisms is forensically reconciled as follows:

| Mechanism | Evidence Summary | Authoritative Stage | Canonical Status | Live Build Cleared? |
| :--- | :--- | :--- | :--- | :---: |
| **`TOWN_CYCLE`** | Mean $\Delta = -423.60$ pts, 3W / 7L / 0T ($t = -1.882$) | Pilot (N=10) | **FUNCTIONALLY COMPLETE / QUARANTINED** | **NO** |
| **`EMERGENCY_RECOVERY`** | Mean $\Delta = +0.00$ pts, 0W / 0L / 10T (100% ties) | Pilot (N=10) | **FUNCTIONALLY COMPLETE / DORMANT** | **NO** |
| **`OPPONENT_PREEMPT_SELL`** | Formal Q1: Mean $\Delta = -58.76$ pts, 8W / 16L / 1T ($t = -1.331$) | Formal Q1 (N=25) | **FUNCTIONALLY COMPLETE / QUARANTINED** | **NO** |
| **`RESOURCE_CONVERSION`** | Mean $\Delta = +0.00$ pts, 13,360 opps, 0 commits | Pilot (N=10) | **FUNCTIONALLY COMPLETE / DORMANT** | **NO** |

*Rationale for Status Distinctions*:
- `TOWN_CYCLE`: Quarantined due to observed economic harm (cash starvation during day-boundary seed purchases). Formal qualification was not pursued because the pilot was unambiguously negative.
- `EMERGENCY_RECOVERY`: Classified as **DORMANT** rather than failed. The rescue eliminated catastrophic herd starvation, but the mechanism produced zero incremental value because the baseline foundation was already safe.
- `OPPONENT_PREEMPT_SELL`: Passed the pilot screening hurdle (+112.40 pts) but failed formal qualification on the broader 25-seed cohort (-58.76 pts). Quarantined based on authoritative formal evidence.
- `RESOURCE_CONVERSION`: Classified as **DORMANT**. The valuation system executed flawlessly by abstaining on all conversions; secondary processing is structurally unviable compared to high-margin direct agriculture.

---

## 8. Control & Treatment Verification

### A. Empirical Control Verification
The control was verified bit-identically across all matches as:
$$\text{CONTROL} = \text{V3 Chassis} + \text{DEPENDENCY\_AWARE\_MARKET\_TIMING} + \text{TERMINAL\_LIQUIDATION} + \text{PHASE\_SHUTDOWN}$$
- V3 Chassis SHA256: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`.
- No Group 1 rescued mechanisms were enabled in the control.
- All 15 non-foundation mechanisms were confirmed quarantined in `ctrl_cfg.quarantined_mechanisms`.

### B. Treatment Isolation Verification
In each experiment:
$$\text{TREATMENT} = \text{CONTROL} + \text{TARGET\_MECHANISM}$$
Verification of `commits_by_mech` in all match CSVs confirmed:
- In `TOWN_CYCLE` matches: Only `DEPENDENCY_AWARE_MARKET_TIMING` and `TOWN_CYCLE` committed.
- In `EMERGENCY_RECOVERY` matches: Only `DEPENDENCY_AWARE_MARKET_TIMING` and `EMERGENCY_RECOVERY` committed.
- In `OPPONENT_PREEMPT_SELL` matches: Only `DEPENDENCY_AWARE_MARKET_TIMING` and `OPPONENT_PREEMPT_SELL` committed.
- In `RESOURCE_CONVERSION` matches: Only `DEPENDENCY_AWARE_MARKET_TIMING` committed (target committed 0).
- Zero cross-mechanism activation occurred across all 130 matches.

---

## 9. Shared-Code & Economic-Evaluator Audit

### A. Feed Security Invariant Audit
- **Location**: `FeedSecurityEngine` is integrated in `aec/opportunities/town_cycle.py`, `aec/opportunities/emergency.py`, `aec/opportunities/preemption.py`, and `aec/opportunities/resource.py`.
- **Scope**: The feed invariant strictly inspects and restricts candidate generation within experimental treatment mechanisms.
- **Control Impact**: **ZERO**. The shared control foundation (`DEPENDENCY_AWARE_MARKET_TIMING`, `TERMINAL_LIQUIDATION`, `PHASE_SHUTDOWN`) does not call these opportunity modules. The control baseline was not retroactively modified.

### B. Economic Evaluator (`win_model.py`) Audit
- **Modifications in Group 2**: Added explicit evaluation hurdles for `TOWN_CYCLE`, `EMERGENCY_RECOVERY`, `OPPONENT_PREEMPT_SELL`, and `RESOURCE_CONVERSION`.
- **Dependency Path**: The three foundation mechanisms possess their own dedicated branches earlier in `WinModel.evaluate_candidate()` (lines 236–260) and were completely untouched by Group 2 edits.
- **Evaluation Consistency**: Counterfactual simulation economics and forward rewards remained identical between control and treatment runs.

---

## 10. Final Canonical Interpretation & Freeze

Phase 012 achieved its core engineering and scientific objectives:
1. **Engineering Rescue**: Completely repaired first-generation bugs, eliminated livestock starvation, and established 100% crash-free simulation fidelity across tens of thousands of candidate evaluations.
2. **Empirical Reality**: Demonstrated that none of the four Group 2 mechanisms provides incremental economic value over the frozen live foundation.
3. **Live Build Integrity**: The live competition configuration remains strictly frozen:
   $$\text{Live Build} = \text{V3 Chassis} + \text{DEPENDENCY\_AWARE\_MARKET\_TIMING} + \text{TERMINAL\_LIQUIDATION} + \text{PHASE\_SHUTDOWN}$$
4. **Phase Transition**: Phase 012 is officially complete, forensically reconciled, and frozen. Phase 013 (Group 3) will proceed strictly from this trustworthy baseline.
