# V35 Repository Audit: Incumbents, Assets, and Isolation

## 1. Incumbent Cryptographic Integrity Audit

The protected tournament incumbents were cryptographically verified using SHA-256 hashing.

| Artifact | Path | Expected SHA-256 | Observed SHA-256 | Audit Status |
| :--- | :--- | :--- | :--- | :--- |
| **A7 Standalone** | `candidates/v30_a7_standalone/main.py` | `51c1d25245f68dd8de66b355f2ad6ca1d79de8af02efed521a5a82f7be69ce3f` | `51c1d25245f68dd8de66b355f2ad6ca1d79de8af02efed521a5a82f7be69ce3f` | **PASS (100% Match)** |
| **V22R1 Submission** | `submission_aec_v22r1.tar.gz` | `6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5` | `6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5` | **PASS (100% Match)** |

**Finding:** Both files are 100% unaltered, preserving baseline competition integrity.

---

## 2. Seed Cohort Isolation & Quarantine Verification

The repository contains designated seed partitions to prevent evaluation leakage and test set contamination:

- **Development Cohort (Permitted for Sweeps & Tuning):**
  - Cohort 1: `249675, 249676, 249677, 249678, 249679`
  - Cohort 2: `249680, 249681, 249682, 249683, 249684`
  - Cohort 3: `249685, 249686, 249687, 249688, 249689`
- **Virgin Holdout Cohort (Strictly Quarantined — DO NOT ACCESS):**
  - Range A: `214200 – 214249` (50 seeds)
  - Range B: `340090 – 340199` (110 seeds)
  - Range C: `249695 – 249734` (40 seeds)

**Verification:** No V35 script or candidate references, trains upon, or accesses any seed within the quarantined ranges.

---

## 3. Directory Structure & Environment Verification

- **Workspace Root:** `c:\Users\Sundareswaran\Kagriculture`
- **Active Runtime Environment:** Python 3.14.3, `kaggle-environments` 1.32.7, `pytest` 9.0.3, Windows PowerShell.
- **CPU Resource Allocation:** 8 physical/logical cores via `multiprocessing.Pool`.
- **Target Candidate Directory:** `candidates/v35_a7_opening/` created and dedicated exclusively to V35 files.
- **League Opponent Chassis:** Opponent loaders in `candidates/v32_rlx2/opponents.py` confirmed operational and isolated:
  - `E2_A7`: Incumbent A7 agent (`E9_AST` wrapper)
  - `E1_V22R1`: Slot A portfolio champion
  - `E0_V3`: Frozen V3 baseline
  - `E8_DMITRII`: Frontier competitor (2800+ LB)
  - `V54`: Declarative reference implementation
  - `SYN_AGG`: Synthetic hostile market dumper
