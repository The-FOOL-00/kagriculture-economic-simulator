# SEED PROVENANCE AUDIT: VIRGIN DISCOVERY PARTITION CERTIFICATION
**Experiment**: EXP-DEV-004 (Joint Macro Production Scheduler)  
**Date**: 2026-09-14  
**Auditor**: Autonomous Verification Engine (Zero-Leakage Governance)  
**Selected Partition**: Seeds `246000` to `246049` ($N=50$ contiguous seeds)  
**Certification Status**: **100% CERTIFIED VIRGIN — ZERO HISTORICAL SIMULATION OR RESULT EXPOSURE**

---

## 1. Executive Summary & Permanent Quarantines

### 1.1 Formal Protection of Reserved Partitions
The following partitions remain strictly quarantined and will never be touched, simulated, or inspected during EXP-DEV-004:
- **`214200–214249`**: Certified Virgin Final Holdout (`HOLDOUT-COHORT-V1`). Strictly quarantined; zero access, zero simulations.
- **`50050–50099`**: Active Qualification Partition. Reserved exclusively for formal qualification runs; zero access during Discovery.
- **`50000–50049`**: Historical Discovery Partition (EXP-DEV-001/002). Permanently decommissioned.
- **`50100–50149`**: Historical Benchmark Partition. Permanently rejected due to historical policy sweeps.
- **`50000–50499`**: Historical Sweep & Census Contaminated Region. Under blanket quarantine.
- **`245000–245049`**: EXP-DEV-003 Discovery Partition. Consumed during DEV-003 execution; strictly excluded from EXP-DEV-004.

---

## 2. Exhaustive Provenance Audit of Candidate Partition `246000–246049`

An exhaustive provenance scan was executed across all 2,749 workspace files, full Git commit history (diffs and commit logs), simulation script ASTs, result databases, and system logs.

### 2.1 Audit Results by Governance Dimension

| Governance Dimension | Scan Method | Hits in `246000–246049` | Result & Provenance Category |
| :--- | :--- | :---: | :--- |
| **Simulation Scripts (`.py`)** | Static regex scan for explicit seed literals, lists, and ranges | **0** | Clean (Category None) |
| **Stride / Loop Arithmetic** | Range arithmetic `base + i*stride` and `range(start, end)` | **0** | Clean (Category None) |
| **Result Databases (`.json`)** | Exact JSON key/value search for `"seed": 2460xx` | **0** | Clean (Category None) |
| **Result Tables (`.csv`)** | CSV column header indexing and cell value search | **0** | Clean (Category None) |
| **Git Commit Messages** | `git log --all --grep=246000` | **0** | Clean (Category None) |
| **Git Pickaxe Diffs** | `git log --all -S 246000 --oneline` | **0** | Clean (Category None) |
| **Git Regex Diffs** | `git log --all -G"2460[0-4][0-9]"` | **0\*** | Clean (Word-boundary verified; 0 seed matches) |
| **Agent Transcripts** | Whole-text search in `<appDataDir>\brain\*\transcript.jsonl` | **0** | Clean (Category None) |
| **Quarantine Buffer (Holdout)**| Distance from Final Holdout `214200–214249` | **31,751 seeds** | Verified buffer >30,000 seeds |
| **Quarantine Buffer (DEV-003)**| Distance from DEV-003 Discovery `245000–245049` | **951 seeds** | Contiguous non-overlapping block |

*\* Note on Git Regex: Commit `fcf9fd0` contains episode ID `92460492`, which contains substring `246049`. Verified via AST and word boundary parsing to be a 8-digit Kaggle episode ID, not a seed.*

---

## 3. Comparative Provenance Across Candidate Ranges

| Candidate Range | Script Hits | Result File Hits | Stride Overlaps | Prior Use / Exposure | Status |
| :---: | :---: | :---: | :---: | :--- | :---: |
| **`245000–245049`** | 1 (`run_exp_dev_003.py`) | 5 files (`RAW_RESULTS.json`, etc.) | 0 | Consumed by EXP-DEV-003 | **RETIRED (DEV-003)** |
| **`246000–246049`** | **0** | **0** | **0** | **Zero historical use** | **CERTIFIED VIRGIN (SELECTED)** |
| **`247000–247049`** | 0 | 0 | 0 | Zero historical use | Reserved Alternative |
| **`248000–248049`** | 0 | 0 | 0 | Zero historical use | Reserved Alternative |
| **`249000–249049`** | 0 | 0 | 0 | Zero historical use | Reserved Alternative |
| **`250000–250049`** | 1 (`extract_all_executed_seeds.py`) | 0 | 0 | Listed in historical test script | Reserved Alternative |

---

## 4. Static Simulator Compatibility & Seed Validity

Pursuant to governance protocol, the simulator was audited **statically** without executing candidate seeds:
1. **C++ Engine (`sim/sim.hpp:153`)**: Config takes `uint64_t seed`. Range `246000–246049` fits into standard integer registers with zero truncation.
2. **Deterministic RNG Formula (`sim.hpp:730`)**: `PyRandom rng((cfg.seed * 1000003ull) ^ static_cast<uint64_t>(day))`. Zero modulo collisions or folding.
3. **Kaggle Environment Bounds (`kaggriculture.py:239`)**: Natural episode seeds draw from $0 \le \text{seed} < 2^{31} \approx 2.14 \times 10^9$. Seed `246000` is in the bottom $0.012\%$ of valid game seeds.

---

## 5. Certification Verdict

Candidate partition **`246000–246049`** ($N=50$) is formally certified as **100% VIRGIN** and authorized for use as the official Discovery partition for **EXP-DEV-004**.
