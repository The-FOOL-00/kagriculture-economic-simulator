# SEED PROVENANCE AUDIT: VIRGIN DISCOVERY PARTITION CERTIFICATION
**Experiment**: EXP-DEV-006 (Confirmed-Shop + Horizon-Gated Whole-Route Scheduler)
**Date**: 2026-09-14
**Auditor**: Muse Code powered by Meta Muse Spark (Zero-Leakage Governance)
**Selected Partition**: Seeds `248000` to `248049` ($N=50$ contiguous seeds)
**Certification Status**: **100% CERTIFIED VIRGIN — ZERO HISTORICAL SIMULATION OR RESULT EXPOSURE**

---

## 1. Executive Summary & Permanent Quarantines

### 1.1 Formal Protection of Reserved Partitions
The following partitions remain strictly quarantined and will never be touched, simulated, or inspected during EXP-DEV-006:
- **`214200–214249`**: Certified Virgin Final Holdout (`HOLDOUT-COHORT-V1`). Strictly quarantined; zero access, zero simulations.
- **`50050–50099`**: Active Qualification Partition. Reserved exclusively for formal qualification runs; zero access during Discovery.
- **`50000–50049`**: Historical Discovery Partition (EXP-DEV-001/002). Permanently decommissioned.
- **`50100–50149`**: Historical Benchmark Partition. Permanently rejected due to historical policy sweeps.
- **`50000–50499`**: Historical Sweep & Census Contaminated Region. Under blanket quarantine.
- **`245000–245049`**: EXP-DEV-003 Discovery Partition. Consumed; strictly excluded.
- **`246000–246049`**: EXP-DEV-004 Discovery Partition. Consumed (plus retrospective kill-test replay); strictly excluded.
- **`247000–247049`**: EXP-DEV-005 Discovery Partition. Consumed (plus horizon kill-test replay of 200 games); strictly excluded from fresh Discovery.

---

## 2. Exhaustive Provenance Audit of Candidate Partition `248000–248049`

An exhaustive provenance scan was executed across all workspace files (1644 `.py` files, all experiment result databases, research tables, replay manifests), full Git history (68 commits: pickaxe, regex, message grep), stride/loop arithmetic, and 163 IDE conversation stores (raw-byte scan incl. execution-context patterns).

### 2.1 Audit Results by Governance Dimension

| Governance Dimension | Scan Method | Hits in `248000–248049` | Result & Provenance Category |
| :--- | :--- | :---: | :--- |
| **Simulation Scripts (`.py`)** | Literal + word-boundary regex `\b248\d\d\d\b` over workspace | **0 execution refs** | Clean (2 static audit scripts list the range as an audit *target*; they import only os/re/subprocess, never execute games) |
| **Stride / Loop Arithmetic** | `range(a,b)` overlap + `base+i*step` reachability over 1644 `.py` files | **0 reachable** | Clean (26 naive pattern hits, ALL unreachable: loop bounds ≤100 vs required i≥14,530; max reachable value 2,683; only 2 files execute games at all, on seeds ≤2,683) |
| **Result Databases (`.json`)** | `"seed": N` extraction over experiments/results/scratch | **0** | Clean (executed seeds repo-wide: 500xx, 245xxx, 246xxx, 247xxx, 1000–2683 only) |
| **Result Tables (`.csv`)** | Exact value search | **0** | Clean (only float-formatting substring artifacts, e.g. `15.172500000000007`, in unrelated stats tables) |
| **Git Commit Messages** | `git log --all --grep` | **0** | Clean (Category None) |
| **Git Pickaxe Diffs** | `git log --all -S 248000 -- experiments/` | **2\*** | Clean (documentation-only provenance tables) |
| **Git Regex Diffs** | `git log --all -G"2480[0-4][0-9]"` | **0 seed matches** | Clean (only the 2 doc commits above) |
| **Conversation / Transcript Stores** | Raw-byte scan of 163 `.db` files + 6 execution-context patterns | **0 execution** | Clean (matches = audit-doc text, tool-call IDs `call_2480xxx`, UUID fragments, float artifacts, unrelated web/PDF bytes; zero `Game(248`, zero `Seed 2480xx | Delta`, zero outcome contexts) |
| **Quarantine Buffer (Holdout)** | Distance from Final Holdout `214200–214249` | **33,751 seeds** | Verified buffer >30,000 seeds |
| **Quarantine Buffer (DEV-005)** | Distance from consumed `247000–247049` | **951 seeds** | Contiguous non-overlapping block |

*\* Git pickaxe hits: `68047be` (DEV-004 protocol freeze) and `af12b6f` (DEV-005 protocol freeze) list `248000–248049` in `SEED_PROVENANCE.md` as an unconsumed "Reserved Alternative". Documentation-only mentions, explicitly classified per governance §6. Zero simulations were executed.*

### 2.2 Explicit Classification of Documentation-Only Mentions (per §6)
The following files mention `248000–248049` WITHOUT executing any game on those seeds:
1. `experiments/EXP-DEV-004/SEED_PROVENANCE.md:53` — "Reserved Alternative" table row.
2. `experiments/EXP-DEV-005/SEED_PROVENANCE.md:54` — "Reserved Alternative" table row.
3. `scratch/audit_seed_ranges.py:9` — static virginity-audit target listing (no simulator import).
4. `scratch/fast_seed_audit.py:10` — static virginity-audit target listing (no simulator import).
5. Conversation-store copies of items 1–4 (audit-task text, e.g. "Check git diffs for seed 248000").

None of these constitute execution, result, strategy-selection, or parameter-sweep exposure: no game was simulated, no outcome was observed, and no decision was conditioned on these seeds.

---

## 3. Comparative Provenance Across Candidate Ranges

| Candidate Range | Script Hits | Result File Hits | Stride Overlaps | Prior Use / Exposure | Status |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **`245000–245049`** | 1 (`run_exp_dev_003.py`) | consumed | 0 | Consumed by EXP-DEV-003 | **RETIRED (DEV-003)** |
| **`246000–246049`** | 1 (`run_exp_dev_004.py`) | consumed | 0 | Consumed by EXP-DEV-004 & kill-test | **RETIRED (DEV-004)** |
| **`247000–247049`** | 2 (DEV-005 + killtest runners) | consumed | 0 | Consumed by EXP-DEV-005 & horizon kill-test | **RETIRED (DEV-005)** |
| **`248000–248049`** | **0 execution** | **0** | **0** | **Zero historical simulations** | **CERTIFIED VIRGIN (SELECTED)** |
| **`249000–249049`** | 0 execution | 0 | 0 | Zero historical simulations | Reserved Alternative |
| **`250000–250049`** | 0 execution | 0 | 0 | Zero historical simulations | Reserved Alternative |
| **`255000–255049`** | 0 execution | 0 | 0 | Zero historical simulations | Reserved Alternative |
| **`260000–260049`** | 0 execution | 0 | 0 | Zero historical simulations | Reserved Alternative |
| **`300000–300049`** | 0 execution | 0 | 0 | Zero historical simulations | Reserved Alternative |

---

## 4. Static Simulator Compatibility & Seed Validity

Pursuant to governance protocol, the simulator was audited **statically** without executing candidate seeds:
1. **Engine (`kagsim_py` port of kagsim 1.32.7)**: Config takes integer seed; range `248000–248049` fits with zero truncation.
2. **Deterministic RNG**: `(seed * 1000003) ^ day` construction. Zero modulo collisions or folding.
3. **Kaggle Environment Bounds**: Natural episode seeds draw from $0 \le \text{seed} < 2^{31} \approx 2.14 \times 10^9$. Seed `248000` is in the bottom $0.012\%$ of valid game seeds.

---

## 5. Certification Verdict

Candidate partition **`248000–248049`** ($N=50$) is formally certified as **100% VIRGIN** and authorized for use as the official Discovery partition for **EXP-DEV-006**.
