# V32 P6 — COMPETITION SAFETY & ASSET INTEGRITY AUDIT (ENTRY)

## 1. MANDATE & SCOPE

In strict compliance with Section 4 and Section 37 of the **V32 P6 Protocol**, this document certifies the bit-level integrity and inviolability of all frozen production competition agents, baseline checkpoints, simulator environments, seed registries, and protected holdouts prior to conducting any diagnostic, masking, training, or evaluation procedures in Phase V32 P6.

---

## 2. PRODUCTION AGENT & BASELINE DIGEST VERIFICATION

Every production asset, adapter, and frozen baseline checkpoint has been verified via SHA-256 cryptographic hashing:

| Component | Target File | SHA-256 Digest | Status |
|:---|:---|:---:|:---:|
| **Slot A (Production)** | `submission_aec_v22r1.tar.gz` | `6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5` | **FROZEN / UNCHANGED** |
| **Slot B (Production)** | `submission_a7_v30.tar.gz` | `4a07673072b6aef9346bf4c21ee5a5979b9da50fccc609fb731dcdbf8f016619` | **FROZEN / UNCHANGED** |
| **V3 Champion Reference** | `submission_Vj_kc_v3.tar.gz` | `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` | **FROZEN / UNCHANGED** |
| **A7 Standalone Policy** | `candidates/v30_a7_standalone/main.py` | `51c1d25245f68dd8de66b355f2ad6ca1d79de8af02efed521a5a82f7be69ce3f` | **FROZEN / UNCHANGED** |
| **P4 Arm 1 Checkpoint** | `results/v32_p4_arm1_balanced.npz` | `34587d45cd5ed4d91ed2cfd0423c0a2af41e9da8f6b14a769082f473089a7470` | **FROZEN / UNCHANGED** |
| **P5 Arm 2 Checkpoint** | `results/v32_p5_arm2_early_weighting.npz` | `dc939b295e9c5ca4614a62ec83dcaec34e7a72bbc38846124e0d0ec6d3eacbed` | **FROZEN / UNCHANGED** |
| **Feature Normalizer** | `results/v32_p2_norm.json` | `50e189874cb6e4695b28d6c7017fc8a5d3f23d46797825ebbc6f9cf5e054baeb` | **FROZEN / UNCHANGED** |
| **P3/P4/P5 Action Schema** | `V32_P3_ACTION_SCHEMA.json` | `2aa2ef5a1f11c34a2e8cfa10e6a9f5d34199c15d4879d2bfd4e138a0b0d39e3c` | **FROZEN / UNCHANGED** |

Verification via `v32_common.assert_frozen()` returned **PASSED**.

---

## 3. SEED REGISTRY GOVERNANCE & HOLDOUT BOUNDARIES

Strict partitioning of evaluation cohorts remains enforceably frozen:

- **Development Screen Cohort (Permitted for P6 screen & diagnostics)**:
  `249675 – 249684` (10 development seeds $\times$ 6 opponents $\times$ 2 seats = 120 legs).
- **Protected Primary Confirmation Cohort (STRICTLY FROZEN)**:
  `249685 – 249694` (10 virgin seeds). Access is prohibited.
- **Protected Secondary Confirmation Cohort (STRICTLY FROZEN)**:
  `249695 – 249734` (40 virgin seeds). Access is prohibited.
- **Protected V29 Benchmark Cohort (STRICTLY FROZEN)**:
  `214200 – 214249` (50 virgin seeds). Access is prohibited.
- **Protected Full Holdout Registry (STRICTLY FROZEN)**:
  `340090 – 340199` (110 virgin seeds). Access is prohibited.

Zero reads, touches, or evaluations have occurred on any protected seed.

---

## 4. COMPETITION SUBMISSION & LEADERBOARD RULES

- **Submission Ban**: No submission tarball may be built or dispatched to Kaggle.
- **Slot Invariance**: Neither Slot A nor Slot B may be modified, replaced, or repointed.
- **Leaderboard Probing**: No leaderboard probing of any kind is permitted.
- **PPO Gate Status**: `PPO 1M SLOPE GATE: CLOSED`.

---

## 5. ENTRY SAFETY CERTIFICATION

All entry safety gates are satisfied. The research workspace is certified safe to proceed with Task 1 through Task 5 of Phase V32 P6.
