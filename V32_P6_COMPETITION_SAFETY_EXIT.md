# V32 P6 — COMPETITION SAFETY EXIT VERIFICATION

## 1. FORMAL EXIT STATEMENT

Date (exit): 2026-09-23.
Phase: V32 P6 Step-2 Recovery & Semantic Action Stabilization.

All production competition assets, adapters, frozen baselines, and protected holdouts were verified bit-identical at the exit of Phase P6.
Zero submissions were created, packaged, or transmitted.
No protected confirmation holdouts were accessed or evaluated.

---

## 2. PRODUCTION ARTIFACT HASH AUDIT

| Artifact | Purpose | Expected SHA256 | Exit Verified SHA256 | Status |
|:---|:---|:---|:---|:---:|
| `submission_aec_v22r1.tar.gz` | Slot A Production | `6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5` | `6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5` | **UNCHANGED** |
| `submission_a7_v30.tar.gz` | Slot B Production | `4a07673072b6aef9346bf4c21ee5a5979b9da50fccc609fb731dcdbf8f016619` | `4a07673072b6aef9346bf4c21ee5a5979b9da50fccc609fb731dcdbf8f016619` | **UNCHANGED** |
| `submission_Vj_kc_v3.tar.gz` | Frozen V3 Benchmark | `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` | `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` | **UNCHANGED** |
| `candidates/v30_a7_standalone/main.py` | A7 Standalone Source | `51c1d25245f68dd8de66b355f2ad6ca1d79de8af02efed521a5a82f7be69ce3f` | `51c1d25245f68dd8de66b355f2ad6ca1d79de8af02efed521a5a82f7be69ce3f` | **UNCHANGED** |
| `results/v32_p4_arm1_balanced.npz` | P4 Canonical Baseline | `34587d45cd5ed4d91ed2cfd0423c0a2af41e9da8f6b14a769082f473089a7470` | `34587d45cd5ed4d91ed2cfd0423c0a2af41e9da8f6b14a769082f473089a7470` | **UNCHANGED** |
| `results/v32_p5_arm2_early_weighting.npz` | P5 Canonical Baseline | `8bfb219e27c01ca75662706e2329b3524b0a70183b069d2551a1d94a11884fe0` | `8bfb219e27c01ca75662706e2329b3524b0a70183b069d2551a1d94a11884fe0` | **UNCHANGED** |
| `results/v32_p2_norm.json` | Frozen Normalizer | Verified | Verified | **UNCHANGED** |
| `results/v32_p2_bc_legs.jsonl` | Frozen BC Dataset | Verified | Verified | **UNCHANGED** |

---

## 3. SEED QUARANTINE INTEGRITY

The following protected holdout cohorts were audited and confirmed virgin:
1. `214200–214249` (GATE0 virgin holdout): **0 touches**.
2. `340090–340199` (Protected tournament remainder): **0 touches**.
3. `249695–249734` (V32-CONFIRM / EXP-1): **0 touches**.
4. `249685–249694` (P3-CONFIRM / Virgin Dev Reserve): **0 touches**.

All evaluations were executed strictly within the registered development screen seeds: `249675–249684`.

---

## 4. FINAL VERIFICATION VERDICT: **PASS**

All safety protocols remained strictly intact throughout V32 P6.
Zero submission leakage.
Zero holdout contamination.
Zero simulator modifications.
Zero architecture modifications.
All 11 protocol invariants in `tests/test_v32_p6.py` verified and passing.
