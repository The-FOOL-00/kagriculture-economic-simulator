# V37 Final Bundle Report

## 1. Final Decision

`READY_FOR_MANUAL_SUBMISSION`

---

## 2. Frozen Candidate

- **Path**: `candidates/v35_a7_opening/main.py`
- **Hash**: `1959021bdb1aeff720732aec866f5c9f3c9fa0b259ee0ab25982bda367593249`
- **Strategy summary**: Preserves 100% of A7 downstream behavior ($D(t) \to 0$ for steps 1..718); overrides Step-0 wheat wash from 30/30 to 25/25, preserving ~$125 in critical early liquidity and eliminating mirror deadlocks. No learned selector, no RL, no runtime search, no seed conditioning, no opponent conditioning, no changes to protected incumbents.

---

## 3. Submission Artifact

- **Filename**: `V35_FINAL_SUBMISSION.tar.gz`
- **Path**: `c:\Users\Sundareswaran\Kagriculture\final_submission\V35_FINAL_SUBMISSION.tar.gz`
- **Format**: POSIX `tar.gz` (gzip-compressed tarball)
- **Size**: 146,597 bytes (143.2 KiB)
- **SHA-256**: `9d2db0c688e127ba3526008bbe08d09b28fbfe389d11a8fada16606ec1adc9fa`

---

## 4. Archive Contents

Exact file list inside `V35_FINAL_SUBMISSION.tar.gz`:
```text
main.py
```
- Staged source file size: 418,508 bytes
- Staged source SHA-256: `92b29c3ce75f2306d9b61803457404032fcd4ca1129f19e1ad0107e018f35f44`

---

## 5. Dependency Closure

Exact runtime dependencies:
- **Python Standard Library**: `__future__`, `copy`, `typing` (embedded execution engine uses stdlib only)
- **External Packages**: 0
- **Repository-Local Modules**: 0 (Self-contained embedding of A7 standalone engine)
- **Filesystem Access**: 0 (No file reads, writes, or relative path lookups at runtime)

---

## 6. Cleanroom Execution

**PASS**.
- Executed from `submission_final_v35/` in an isolated environment without repository on `PYTHONPATH`.
- Successfully initialized controller, generated `[['BUY_PRODUCT', 'WHEAT', 25], ['SELL', 'WHEAT', 25]]` at Step 0, and completed full 720-step episode under `kaggle_environments` with $144,114.00 cash and zero errors.

---

## 7. Round-Trip Archive Validation

**PASS**.
- Extracted `V35_FINAL_SUBMISSION.tar.gz` into a temporary directory outside the workspace.
- Extracted `main.py` SHA-256 matches staging hash bit-for-bit: `92b29c3ce75f2306d9b61803457404032fcd4ca1129f19e1ad0107e018f35f44`.
- Extracted agent executed cleanly in a full episode on safe dev seed `249677`, achieving $189,650.00 reward and zero errors.

---

## 8. Determinism

**PASS**.
- Executed two independent full 720-step episodes on safe dev seed `249676`.
- Computed identical end-to-end SHA-256 action sequence digests (`6c8bebb9620ebe4c58ca976d044c3c2763869ae98d93040064e30ee096232c01`).
- Step-by-step action mismatches: `0 / 720`.
- Terminal cash: $148,390.00 in both runs.

---

## 9. Runtime

Measured performance over 2,500 invocations:
- **Import / Startup Cost**: 415.25 ms
- **Step 0 Latency (Mean)**: 0.0247 ms (Max: 0.1326 ms, P99: 0.0751 ms)
- **Subsequent Steps Latency (Mean)**: 0.0178 ms (Max: 0.1992 ms, P99: 0.0300 ms)
- **Budget Consumed**: <0.003% of Kaggle's 1,000 ms per-step limit
- **Peak Memory**: ~19.6 MB

---

## 10. Integrity

- **A7 Hash**: `51c1d25245f68dd8de66b355f2ad6ca1d79de8af02efed521a5a82f7be69ce3f` (**MATCH**)
- **V22R1 Hash**: `6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5` (**MATCH**)
- **V35 Hash**: `1959021bdb1aeff720732aec866f5c9f3c9fa0b259ee0ab25982bda367593249` (**MATCH**)
- `git diff -- candidates/v30_a7_standalone/main.py`: EMPTY
- `git diff -- submission_aec_v22r1.tar.gz`: EMPTY
- `git diff -- candidates/v35_a7_opening/main.py`: EMPTY

---

## 11. Holdout Protection

**CONFIRMED**.
The protected virgin holdout ranges were strictly quarantined and never touched, accessed, enumerated, or used during packaging or verification:
- `214200–214249` (Untouched)
- `340090–340199` (Untouched)
- `249695–249734` (Untouched)

---

## 12. Safety Scan

**PASS**.
- Comprehensive static scan revealed 0 API keys, 0 secrets, 0 credentials, 0 private keys, 0 user paths, 0 holdout references, and 0 hidden files.

---

## 13. External Submission

`NOT PERFORMED`
- No Kaggle submission commands were executed.
- No network requests to competition endpoints were made.
- The assistant has halted at local artifact generation.

---

## 14. Manual Submission Instructions

Upload the following local bundle file to the Kaggle competition:

**File to upload**:
`final_submission/V35_FINAL_SUBMISSION.tar.gz`

**CLI Command for manual upload**:
```bash
kaggle competitions submit kaggriculture -f final_submission/V35_FINAL_SUBMISSION.tar.gz -m "V35: A7 opening 25/25 wheat wash intervention (deterministic, zero-drift)"
```
*(You may also submit the extracted standalone script `submission_final_v35/main.py` directly if preferred).*
