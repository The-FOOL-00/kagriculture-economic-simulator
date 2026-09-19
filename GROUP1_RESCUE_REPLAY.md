# AEC PHASE 011: GROUP 1 MECHANISM RESCUE DEVELOPMENT REPLAY & STATISTICAL QUALIFICATION

**Author**: Antigravity AI Research Agent (Phase 011 Lead)  
**Date**: 2026-09-19  
**Chassis Freeze Hash**: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` (Verified Bit-Identical)  
**Governance Scope**: Zero touches of protected cohorts (`340050–340199`, `214200–214249`, `340300–340349`), zero re-use of retired cohorts (`50000–50024`, `249000–249049`), zero re-use of consumed Phase 010/010B cohorts (`249050–249110`).  
**Certified Fresh Development Block**: `249111..249120` (N=10 seeds, 20 mirror matches per mechanism)  
**Harness**: `scripts/run_phase011_group1_qualification.py` (Common Random Numbers mirror matching with multiprocessing)

---

## 1. Executive Qualification Summary Matrix

| Mechanism Family | Evaluation Cohort | N Seeds (Matches) | Mean Paired Delta | SE | 95% Confidence Interval | Median | W / L / T | Win Rate | Target Candidates | Commits | Commit Rate | Final Scientific Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **DYNAMIC_SHADOW_HARVEST** | Fresh `249111..249120` | 10 (20) | -1,030.65 | 454.77 | [-2059.33, -1.97] | -594.50 | 0W / 10L / 0T | 0.0% | 51,245 | 238 | 0.46% | **FUNCTIONALLY COMPLETE / QUARANTINED** |
| **TERMINAL_HARVEST_SWEEP** | Fresh `249111..249120` | 10 (20) | -906.60 | 401.55 | [-1814.90, +1.70] | -499.50 | 2W / 7L / 1T | 20.0% | 3,662 | 160 | 4.37% | **FUNCTIONALLY COMPLETE / QUARANTINED** |
| **ROUTE_COMPRESSION** | Fresh `249111..249120` | 10 (20) | -162,361.65 | 4,803.71 | [-173227.65, -151495.65] | -162,913.50 | 0W / 10L / 0T | 0.0% | 26,932 | 4,445 | 16.50% | **FAILED / QUARANTINED** |
| **CARGO_FERRY** | Fresh `249111..249120` | 10 (20) | -850.65 | 231.27 | [-1373.79, -327.51] | -674.50 | 0W / 10L / 0T | 0.0% | 34,645 | 510 | 1.47% | **FUNCTIONALLY COMPLETE / QUARANTINED** |

---

## 2. Experimental Methodology & Governance Covenant

### 2.1 Single-Mechanism Isolation Protocol
To prevent confounding interactions and isolate causal mechanism impact:
$$\text{CONTROL} = \text{Frozen Live Foundation Build (AEC Foundation with Quarantined Group 1)}$$
$$\text{TREATMENT} = \text{CONTROL} + \text{Exactly One Rescued Mechanism}$$

### 2.2 Common Random Numbers (CRN) Paired Mirror Protocol
Every seed is evaluated in mirror seats to eliminate first-player or spatial bias:
- **Match A**: Treatment = Seat 0 (Player 0), Control = Seat 1 (Player 1)
- **Match B**: Treatment = Seat 1 (Player 1), Control = Seat 0 (Player 0)
- **Paired Net Seed Margin**:
  $$\Delta_{\text{seed}} = \frac{\text{Margin}_{\text{Match A}} + \text{Margin}_{\text{Match B}}}{2} = \frac{(R_{0,A} - R_{1,A}) + (R_{1,B} - R_{0,B})}{2}$$

### 2.3 Strict Attribution & Funnel Accounting
Every candidate lifecycle event is explicitly tracked:
$$\text{Candidates Generated} \longrightarrow \text{Labor Screened} \longrightarrow \text{Patch Reconnected} \longrightarrow \text{Counterfactual Simulated} \longrightarrow \text{Safety Checked} \longrightarrow \text{Committed / Abstained}$$

---

## 3. Per-Mechanism Empirical Results

### 3.1 DYNAMIC_SHADOW_HARVEST
- **Control Type**: Live Foundation Build
- **Cohort**: Fresh Dev `249111..249120` ($N=10$ seeds, 20 mirror matches)
- **Runtime**: 1,162.1s (116.2s per seed)
- **Target Candidates**: 51,245 (across 10/10 active seeds)
- **Target Commits**: 238 (across 9/10 committing seeds)
- **Commit Rate**: 0.46%
- **Mean Paired Delta**: -1,030.65 pts
- **Standard Error**: 454.77 pts
- **95% Confidence Interval**: [-2,059.33, -1.97] ($t = -2.27, p = 0.049$)
- **Median Paired Delta**: -594.50 pts
- **Min / Max Delta**: -5,011.5 pts / -85.0 pts
- **Win / Loss / Tie**: 0 Wins / 10 Losses / 0 Ties (0.0% Win Rate)
- **Safety Violations**: 0
- **Fidelity Rate**: 1.0 (100% verified)

#### Per-Seed Breakdown:
| Seed | Seat 0 Margin | Seat 1 Margin | Net Paired Delta | Target Commits | Foundation Commits | Duration |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 249111 | -577.0 | -577.0 | -577.0 | 34 | 0 | 406.7s |
| 249112 | -342.0 | -342.0 | -342.0 | 16 | 0 | 411.8s |
| 249113 | -1,294.0 | -1,018.0 | -1,156.0 | 34 | 4 | 408.2s |
| 249114 | -1,043.0 | -1,043.0 | -1,043.0 | 22 | 2 | 431.0s |
| 249115 | -85.0 | -85.0 | -85.0 | 0 | 0 | 421.7s |
| 249116 | -13,208.0 | +3,185.0 | -5,011.5 | 28 | 2 | 410.2s |
| 249117 | -253.0 | -253.0 | -253.0 | 10 | 2 | 472.3s |
| 249118 | +362.0 | -1,586.0 | -612.0 | 38 | 2 | 441.4s |
| 249119 | -459.0 | -459.0 | -459.0 | 18 | 2 | 334.5s |
| 249120 | -768.0 | -768.0 | -768.0 | 38 | 2 | 332.9s |

---

### 3.2 TERMINAL_HARVEST_SWEEP
- **Control Type**: Live Foundation Build
- **Cohort**: Fresh Dev `249111..249120` ($N=10$ seeds, 20 mirror matches)
- **Runtime**: 889.1s (88.9s per seed)
- **Target Candidates**: 3,662 (across 10/10 active seeds)
- **Target Commits**: 160 (across 10/10 committing seeds)
- **Commit Rate**: 4.37%
- **Mean Paired Delta**: -906.60 pts
- **Standard Error**: 401.55 pts
- **95% Confidence Interval**: [-1,814.90, +1.70] ($t = -2.26, p = 0.050$)
- **Median Paired Delta**: -499.50 pts
- **Min / Max Delta**: -3,810.0 pts / +93.0 pts
- **Win / Loss / Tie**: 2 Wins / 7 Losses / 1 Tie (20.0% Win Rate)
- **Safety Violations**: 0
- **Fidelity Rate**: 1.0 (100% verified)

#### Per-Seed Breakdown:
| Seed | Seat 0 Margin | Seat 1 Margin | Net Paired Delta | Target Commits | Foundation Commits | Duration |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 249111 | -871.0 | -871.0 | -871.0 | 28 | 2 | 308.8s |
| 249112 | +0.0 | +0.0 | +0.0 | 4 | 4 | 316.8s |
| 249113 | -901.0 | -625.0 | -763.0 | 32 | 6 | 311.3s |
| 249114 | +8.0 | +8.0 | +8.0 | 4 | 2 | 336.7s |
| 249115 | +93.0 | +93.0 | +93.0 | 4 | 4 | 315.0s |
| 249116 | -7,288.0 | +2,324.0 | -2,482.0 | 24 | 4 | 313.4s |
| 249117 | -3,810.0 | -3,810.0 | -3,810.0 | 36 | 4 | 355.9s |
| 249118 | +738.0 | -1,210.0 | -236.0 | 10 | 2 | 341.7s |
| 249119 | -771.0 | -771.0 | -771.0 | 8 | 2 | 261.0s |
| 249120 | -234.0 | -234.0 | -234.0 | 10 | 2 | 263.7s |

---

### 3.3 ROUTE_COMPRESSION
- **Control Type**: Live Foundation Build
- **Cohort**: Fresh Dev `249111..249120` ($N=10$ seeds, 20 mirror matches)
- **Runtime**: 656.0s (65.6s per seed)
- **Target Candidates**: 26,932 (across 10/10 active seeds)
- **Target Commits**: 4,445 (across 10/10 committing seeds)
- **Commit Rate**: 16.50%
- **Mean Paired Delta**: -162,361.65 pts
- **Standard Error**: 4,803.71 pts
- **95% Confidence Interval**: [-173,227.65, -151,495.65] ($t = -33.80, p < 10^{-8}$)
- **Median Paired Delta**: -162,913.50 pts
- **Min / Max Delta**: -180,658.0 pts / -130,856.0 pts
- **Win / Loss / Tie**: 0 Wins / 10 Losses / 0 Ties (0.0% Win Rate)
- **Safety Violations**: 0
- **Fidelity Rate**: 1.0 (100% verified)

#### Per-Seed Breakdown:
| Seed | Seat 0 Margin | Seat 1 Margin | Net Paired Delta | Target Commits | Foundation Commits | Duration |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 249111 | -177,738.0 | -177,738.0 | -177,738.0 | 468 | 0 | 231.0s |
| 249112 | -164,167.0 | -164,167.0 | -164,167.0 | 486 | 0 | 229.1s |
| 249113 | -125,390.0 | -136,322.0 | -130,856.0 | 409 | 0 | 237.8s |
| 249114 | -145,799.0 | -145,997.0 | -145,898.0 | 460 | 0 | 258.1s |
| 249115 | -173,378.0 | -173,378.0 | -173,378.0 | 486 | 0 | 231.6s |
| 249116 | -181,615.0 | -141,362.0 | -161,488.5 | 472 | 1 | 242.3s |
| 249117 | -156,422.0 | -156,422.0 | -156,422.0 | 448 | 0 | 265.1s |
| 249118 | -161,660.0 | -161,660.0 | -161,660.0 | 408 | 0 | 249.4s |
| 249119 | -171,351.0 | -171,351.0 | -171,351.0 | 374 | 0 | 194.7s |
| 249120 | -180,658.0 | -180,658.0 | -180,658.0 | 434 | 0 | 179.9s |

---

### 3.4 CARGO_FERRY
- **Control Type**: Live Foundation Build
- **Cohort**: Fresh Dev `249111..249120` ($N=10$ seeds, 20 mirror matches)
- **Runtime**: 1,129.8s (113.0s per seed)
- **Target Candidates**: 34,645 (across 10/10 active seeds)
- **Target Commits**: 510 (across 10/10 committing seeds)
- **Commit Rate**: 1.47%
- **Mean Paired Delta**: -850.65 pts
- **Standard Error**: 231.27 pts
- **95% Confidence Interval**: [-1,373.79, -327.51] ($t = -3.68, p = 0.005$)
- **Median Paired Delta**: -674.50 pts
- **Min / Max Delta**: -2,310.0 pts / -68.0 pts
- **Win / Loss / Tie**: 0 Wins / 10 Losses / 0 Ties (0.0% Win Rate)
- **Safety Violations**: 0
- **Fidelity Rate**: 1.0 (100% verified)

#### Per-Seed Breakdown:
| Seed | Seat 0 Margin | Seat 1 Margin | Net Paired Delta | Target Commits | Foundation Commits | Duration |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 249111 | -239.0 | -239.0 | -239.0 | 18 | 0 | 404.2s |
| 249112 | -1,850.0 | -1,850.0 | -1,850.0 | 64 | 0 | 397.0s |
| 249113 | -795.0 | -519.0 | -657.0 | 18 | 2 | 405.5s |
| 249114 | -692.0 | -692.0 | -692.0 | 46 | 2 | 411.5s |
| 249115 | -201.0 | -201.0 | -201.0 | 64 | 0 | 401.8s |
| 249116 | -3,319.0 | +3,183.0 | -68.0 | 18 | 0 | 413.2s |
| 249117 | -510.0 | -510.0 | -510.0 | 58 | 0 | 455.5s |
| 249118 | +165.0 | -1,800.0 | -817.5 | 60 | 2 | 431.9s |
| 249119 | -2,310.0 | -2,310.0 | -2,310.0 | 104 | 2 | 305.7s |
| 249120 | -1,162.0 | -1,162.0 | -1,162.0 | 60 | 2 | 311.8s |

---

## 4. Candidate-to-Commit Funnel Analysis

| Metric | DYNAMIC_SHADOW_HARVEST | TERMINAL_HARVEST_SWEEP | ROUTE_COMPRESSION | CARGO_FERRY |
| :--- | :---: | :---: | :---: | :---: |
| **Generated Candidates** | 51,245 | 3,662 | 26,932 | 34,645 |
| **Rejection: Labor Opportunity Cost** | 38,412 (75.0%) | 1,840 (50.2%) | 0 (0.0%) | 22,510 (65.0%) |
| **Rejection: Spatial / Reconnect Safety** | 4,210 (8.2%) | 420 (11.5%) | 1,210 (4.5%) | 3,140 (9.1%) |
| **Rejection: Economic Infeeder / Net Delta $\le 0$** | 8,385 (16.4%) | 1,242 (33.9%) | 21,277 (79.0%) | 8,485 (24.5%) |
| **Safety Certificate Violations** | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| **Final Commits** | 238 (0.46%) | 160 (4.37%) | 4,445 (16.50%) | 510 (1.47%) |
| **Active Seeds** | 10 / 10 | 10 / 10 | 10 / 10 | 10 / 10 |
| **Committing Seeds** | 9 / 10 | 10 / 10 | 10 / 10 | 10 / 10 |

---

## 5. Scientific Diagnosis & Governance Status

1. **DYNAMIC_SHADOW_HARVEST**: Rescued formulation achieves 100% functional correctness, spatial synchronization, and in-flight trajectory execution. However, empirical evaluation confirms that diverting workers away from V3's synchronized farming routines causes an average net loss of -1,030.65 points. Status: **FUNCTIONALLY COMPLETE / QUARANTINED**.
2. **TERMINAL_HARVEST_SWEEP**: Demonstrates localized feasibility with 2 winning seeds (+8.0 and +93.0 pts) and 1 tie (+0.0 pts), but an overall mean paired delta of -906.60 pts due to runway consumption against V3's terminal liquidation schedules. Status: **FUNCTIONALLY COMPLETE / QUARANTINED**.
3. **ROUTE_COMPRESSION**: Path substitution to the shed disrupts task-critical watering and planting cycles, resulting in severe economic damage (-162,361.65 pts). Status: **FAILED / QUARANTINED**.
4. **CARGO_FERRY**: Helper workers carry significant alternative opportunity costs that consistently exceed the marginal value of primary worker transport relief (-850.65 pts). Status: **FUNCTIONALLY COMPLETE / QUARANTINED**.
