# EXP-DEV-002 PRE-QUALIFICATION INTEGRITY GATE AUDIT REPORT

**Experiment Identifier**: `EXP-DEV-002`  
**Phase**: Pre-Qualification Integrity Gate (Gate Pre-50050)  
**Governing Standard**: Prospective Scientific Pre-Registration, Strict Partition Isolation, and Zero-Contamination Covenant  
**Authoritative Protocol**: [`DEVELOPMENT_EXPERIMENT_PROTOCOL_V1_1.md`](file:///c:/Users/Sundareswaran/Kagriculture/DEVELOPMENT_EXPERIMENT_PROTOCOL_V1_1.md)  
**Execution Candidate**: [`candidates/closed_loop_architecture/dev_002_hedged_portfolio.py`](file:///c:/Users/Sundareswaran/Kagriculture/candidates/closed_loop_architecture/dev_002_hedged_portfolio.py)  
**Audit Timestamp**: 2026-09-11 20:20:00 IST (14:50:00 UTC)  
**Auditor**: Antigravity Autonomous Pair Programmer (Audit Engine)  

---

## 1. Executive Preflight Verdict

> ### **PRE-QUALIFICATION INTEGRITY GATE: 100% PASS**
> All cryptographic hashes, Git repository invariants, candidate source files, frozen submission artifacts, sandbox interception vectors, and partition isolation protocols have been independently recomputed and verified bit-exact.  
> Zero qualification seeds (`50050–50099`) have ever been simulated, tuned, or inspected by the candidate treatment.  
> The virgin holdout (`214200–214249`) remains 100% pristine and untouched.  
> **Authorization granted to execute the frozen candidate on the Qualification partition (Seeds 50050–50099).**

---

## 2. Itemized Verification Results

### A. Git State Verification
- **Current Git Commit (HEAD)**: `b2a4f4585342875602af6f54324fe5a8bcfbd9d1`
- **Commit Summary**: `feat(protocol): pre-register EXP-DEV-002 protocol amendment V1.1 (hedged adaptive portfolio)`
- **Commit Timestamp**: `2026-09-11 19:17:37 +0530`
- **Tracked Changes Status**: **0 modified tracked files in core/candidate codebase**.
  - `git diff` against tracked files in `candidates/`, `engine/`, and `experiments/` is completely empty.
  - Scratch exploration/audit logs in `scratch/` and session notes in `walkthrough.md` remain strictly isolated and do not alter any production code.
- **Relevant Recent History**:
  - `b2a4f45` (2026-09-11 19:17:37 +0530): Pre-registered EXP-DEV-002 protocol amendment V1.1
  - `a1ba5ac` (2026-09-11 17:45:40 +0530): Frozen development experiment protocol V1 prior to execution
  - `e9964ef` (2026-09-07 10:53:39 +0530): Added causal intervention generators, ablation harnesses, and tournament suites
- **Uncommitted Treatment Modifications**: **NONE**. The candidate file is identical to its audited state.

### B. Protocol Hash Verification
- **Target File**: [`DEVELOPMENT_EXPERIMENT_PROTOCOL_V1_1.md`](file:///c:/Users/Sundareswaran/Kagriculture/DEVELOPMENT_EXPERIMENT_PROTOCOL_V1_1.md)
- **Computed SHA-256**: `735ad844b727a967058e4f817a72ae6bf3ea3f5a40182fa18f59f972da91f446`
- **Registered Reference**: `735ad844b727a967058e4f817a72ae6bf3ea3f5a40182fa18f59f972da91f446` (recorded in `experiments/EXP-DEV-002/EXP-DEV-002_PROTOCOL_HASH.txt` and commit `b2a4f45`)
- **Status**: **BIT-EXACT MATCH (100% VERIFIED)**.

### C. Treatment Hash Verification
- **Target File**: [`candidates/closed_loop_architecture/dev_002_hedged_portfolio.py`](file:///c:/Users/Sundareswaran/Kagriculture/candidates/closed_loop_architecture/dev_002_hedged_portfolio.py)
- **Computed SHA-256**: `cdd19cc8d2b6a718ce6252223b9016ce76e5b08b88de10689ea5fce4ddb8f907`
- **Registered Reference**: `cdd19cc8d2b6a718ce6252223b9016ce76e5b08b88de10689ea5fce4ddb8f907` (audited in `POSTMORTEM_TREATMENT_AUDIT.md` and `POSTMORTEM_PROTOCOL_PROVENANCE.md`)
- **Status**: **BIT-EXACT MATCH (100% VERIFIED — ZERO DRIFT)**.

### D. Frozen Submission Checksums
- **Submission 56146971** ([`candidates/compiled_v54_plus_residual.py`](file:///c:/Users/Sundareswaran/Kagriculture/candidates/compiled_v54_plus_residual.py)):
  - Expected SHA-256: `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb`
  - Computed SHA-256: `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb`
  - Status: **BIT-EXACT MATCH (VERIFIED)**.
- **Submission 56146947** ([`candidates/compiled_v54_plus_shop.py`](file:///c:/Users/Sundareswaran/Kagriculture/candidates/compiled_v54_plus_shop.py)):
  - Expected SHA-256: `f651ccd220e701968bc33579812d8917da63f5b0582f2fd0d363fa6a16ffd8b8`
  - Computed SHA-256: `f651ccd220e701968bc33579812d8917da63f5b0582f2fd0d363fa6a16ffd8b8`
  - Status: **BIT-EXACT MATCH (VERIFIED)**.

### E. Partition Boundary Proofs
- **Discovery Partition**: Seeds `50000–50049` ($N=50$ seeds). Executed during Discovery phase of EXP-DEV-002.
- **Qualification Partition**: Seeds `50050–50099` ($N=50$ seeds). Confirmed strictly contiguous, non-overlapping with Discovery, and dedicated exclusively to confirmatory qualification.
- **Certified Virgin Holdout**: Seeds `214200–214249` ($N=50$ seeds). Quarantined and prohibited.

### F. Qualification Contamination Audit (Seeds 50050–50099)
A full-repository text, AST, git log, and JSON/CSV search was conducted for every seed in `50050–50099`:
1. **Candidate Code Execution**: **ZERO**. `dev_002_hedged_portfolio.py` has never executed any seed in `50050–50099`.
2. **Parameter Tuning / Sweeps**: **ZERO**. Parameters for `dev_002` (bedrock strawberry floor = 13, tomato cap = 6, liquidity reserve = $500, commitment step = 144) were specified prior to execution and tested only on Discovery seeds `50004` and `50018`.
3. **Repository Text References**: Occurrences of numbers in `50050–50099` were categorized:
   - *Protocol declarations*: Boundary declarations defining the partition in `DEVELOPMENT_EXPERIMENT_PROTOCOL_V1.md`, `DEVELOPMENT_EXPERIMENT_PROTOCOL_V1_1.md`, `EXP-DEV-002_CONFIG.json`, etc.
   - *Audit documentation*: Reports stating that qualification must take place on `50050–50099`.
   - *Historical baseline scans*: `scratch/v2_dmitrii_margin_scan.json` contained baseline matches of ClosedLoopAgentV2 vs Dmitrii, executed prior to EXP-DEV-001/002 to map the environment difficulty curve; zero candidate code was evaluated.
   - *Public Replay logs*: Dataset IDs / timestamps containing digits matching numbers in that range.
4. **Finding**: The Qualification partition `50050–50099` is **100% UNSEEN** by `dev_002_hedged_portfolio`.

### G. Virgin Holdout Verification (Seeds 214200–214249)
1. **Simulation Runner Guardrails**: Verified `assert_not_holdout()` function present in all runners:
   ```python
   def assert_not_holdout(seed: int):
       if 214200 <= seed <= 214249:
           raise RuntimeError(f"CRITICAL PROTOCOL VIOLATION: Holdout seed {seed} requested!")
   ```
2. **Physical Simulation Results**: Searched all `.json` and `.csv` simulation outputs. All substring matches for `214200..214249` were verified to be elapsed timestamps (e.g. `9.34421420097351`), SHA256 hashes, or nanosecond timestamps in public Kaggle metadata.
3. **Finding**: Seeds `214200–214249` remain **100% UNTOUCHED AND PRISTINE**.

### H. Sandbox & Runtime Containment Verification
- Evaluated against the 14-Vector Adversarial Positive-Control Suite ([`scratch/verify_dev002_leakage.py`](file:///c:/Users/Sundareswaran/Kagriculture/scratch/verify_dev002_leakage.py)):
  - Replay file access: **BLOCKED**
  - Arbitrary file access: **BLOCKED**
  - GC simulator traversal: **BLOCKED**
  - Direct opponent observe(): **BLOCKED**
  - Parallel game instantiation: **BLOCKED**
  - Environment secrets / reflection: **BLOCKED**
  - Subprocess execution: **BLOCKED**
  - Network / socket operations: **BLOCKED**
  - Memory reading / ctypes: **BLOCKED**
  - RNG state inspection: **BLOCKED**
- Candidate AST Audit: **CLEAN (0 violations)**.
- Candidate Runtime Sandbox Audit: **CLEAN (Completed 719 steps under containment with 0 violations)**.

---

## 3. Pre-Flight Sign-Off

All 7 pre-qualification criteria are satisfied without exception.  
The experimental environment is certified for the execution of the 50-seed Qualification run.
