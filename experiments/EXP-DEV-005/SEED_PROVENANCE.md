# SEED PROVENANCE AUDIT: VIRGIN DISCOVERY PARTITION CERTIFICATION
**Experiment**: EXP-DEV-005 (Confirmed-Shop Gated Whole-Route Scheduler)  
**Date**: 2026-09-14  
**Auditor**: Autonomous Verification Engine (Zero-Leakage Governance)  
**Selected Partition**: Seeds `247000` to `247049` ($N=50$ contiguous seeds)  
**Certification Status**: **100% CERTIFIED VIRGIN — ZERO HISTORICAL SIMULATION OR RESULT EXPOSURE**

---

## 1. Executive Summary & Permanent Quarantines

### 1.1 Formal Protection of Reserved Partitions
The following partitions remain strictly quarantined and will never be touched, simulated, or inspected during EXP-DEV-005:
- **`214200–214249`**: Certified Virgin Final Holdout (`HOLDOUT-COHORT-V1`). Strictly quarantined; zero access, zero simulations.
- **`50050–50099`**: Active Qualification Partition. Reserved exclusively for formal qualification runs; zero access during Discovery.
- **`50000–50049`**: Historical Discovery Partition (EXP-DEV-001/002). Permanently decommissioned.
- **`50100–50149`**: Historical Benchmark Partition. Permanently rejected due to historical policy sweeps.
- **`50000–50499`**: Historical Sweep & Census Contaminated Region. Under blanket quarantine.
- **`245000–245049`**: EXP-DEV-003 Discovery Partition. Consumed during DEV-003 execution; strictly excluded.
- **`246000–246049`**: EXP-DEV-004 Discovery Partition. Consumed during DEV-004 execution and DEV-005 retrospective kill-test; strictly excluded from fresh Discovery.

---

## 2. Exhaustive Provenance Audit of Candidate Partition `247000–247049`

An exhaustive provenance scan was executed across all workspace files, full Git commit history (diffs and commit logs), simulation script ASTs, result databases, and system logs.

### 2.1 Audit Results by Governance Dimension

| Governance Dimension | Scan Method | Hits in `247000–247049` | Result & Provenance Category |
| :--- | :--- | :---: | :--- |
| **Simulation Scripts (`.py`)** | Static regex scan for explicit seed literals, lists, and ranges | **0** | Clean (Category None) |
| **Stride / Loop Arithmetic** | Range arithmetic `base + i*stride` and `range(start, end)` | **0** | Clean (Category None) |
| **Result Databases (`.json`)** | Exact JSON key/value search for `"seed": 2470xx` | **0** | Clean (Category None) |
| **Result Tables (`.csv`)** | CSV column header indexing and cell value search | **0** | Clean (Category None) |
| **Git Commit Messages** | `git log --all --grep=247000` | **0** | Clean (Category None) |
| **Git Pickaxe Diffs** | `git log --all -S 247000 --oneline` | **1\*** | Clean (Table mention in DEV-004 protocol) |
| **Git Regex Diffs** | `git log --all -G"2470[0-4][0-9]"` | **0** | Clean (Word-boundary verified; 0 seed matches) |
| **Agent Transcripts** | Whole-text search in `<appDataDir>\brain\*\transcript.jsonl` | **0** | Clean (Category None) |
| **Quarantine Buffer (Holdout)**| Distance from Final Holdout `214200–214249` | **32,751 seeds** | Verified buffer >30,000 seeds |
| **Quarantine Buffer (DEV-004)**| Distance from DEV-004 Discovery `246000–246049` | **951 seeds** | Contiguous non-overlapping block |

*\* Note on Git Pickaxe: Commit `68047be` listed `247000–247049` in Section 3 of DEV-004 `SEED_PROVENANCE.md` as an unconsumed "Reserved Alternative". Zero simulations were executed.*

---

## 3. Comparative Provenance Across Candidate Ranges

| Candidate Range | Script Hits | Result File Hits | Stride Overlaps | Prior Use / Exposure | Status |
| :---: | :---: | :---: | :---: | :--- | :---: |
| **`245000–245049`** | 1 (`run_exp_dev_003.py`) | 5 files (`RAW_RESULTS.json`, etc.) | 0 | Consumed by EXP-DEV-003 | **RETIRED (DEV-003)** |
| **`246000–246049`** | 1 (`run_exp_dev_004.py`) | 6 files (`RAW_RESULTS.json`, etc.) | 0 | Consumed by EXP-DEV-004 & Kill-test | **RETIRED (DEV-004)** |
| **`247000–247049`** | **0** | **0** | **0** | **Zero historical simulations** | **CERTIFIED VIRGIN (SELECTED)** |
| **`248000–248049`** | 0 | 0 | 0 | Zero historical simulations | Reserved Alternative |
| **`249000–249049`** | 0 | 0 | 0 | Zero historical simulations | Reserved Alternative |

---

## 4. Static Simulator Compatibility & Seed Validity

Pursuant to governance protocol, the simulator was audited **statically** without executing candidate seeds:
1. **C++ Engine (`sim/sim.hpp:153`)**: Config takes `uint64_t seed`. Range `247000–247049` fits into standard integer registers with zero truncation.
2. **Deterministic RNG Formula (`sim.hpp:730`)**: `PyRandom rng((cfg.seed * 1000003ull) ^ static_cast<uint64_t>(day))`. Zero modulo collisions or folding.
3. **Kaggle Environment Bounds (`kaggriculture.py:239`)**: Natural episode seeds draw from $0 \le \text{seed} < 2^{31} \approx 2.14 \times 10^9$. Seed `247000` is in the bottom $0.012\%$ of valid game seeds.

---

## 5. Certification Verdict

Candidate partition **`247000–247049`** ($N=50$) is formally certified as **100% VIRGIN** and authorized for use as the official Discovery partition for **EXP-DEV-005**.
