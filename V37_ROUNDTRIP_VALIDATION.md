# V37 Archive Round-Trip Validation

## 1. Validation Chain

This audit verifies the end-to-end integrity pipeline:
$$\text{Frozen Candidate} \longrightarrow \text{Staging Directory} \longrightarrow \text{Archive Build} \longrightarrow \text{Extraction to Temp Dir} \longrightarrow \text{Execution}$$

---

## 2. Hash Invariance Across Pipeline

| Stage | Path / Target | SHA-256 Digest | Status |
| :--- | :--- | :--- | :---: |
| **Development Reference** | `candidates/v35_a7_opening/main.py` | `1959021bdb1aeff720732aec866f5c9f3c9fa0b259ee0ab25982bda367593249` | Frozen Reference |
| **A7 Chassis Embedded** | `candidates/v30_a7_standalone/main.py` | `51c1d25245f68dd8de66b355f2ad6ca1d79de8af02efed521a5a82f7be69ce3f` | Frozen Chassis |
| **Staged Production** | `submission_final_v35/main.py` | `92b29c3ce75f2306d9b61803457404032fcd4ca1129f19e1ad0107e018f35f44` | Staged Base |
| **Final Archive** | `final_submission/V35_FINAL_SUBMISSION.tar.gz` | `9d2db0c688e127ba3526008bbe08d09b28fbfe389d11a8fada16606ec1adc9fa` | Built Tarball |
| **Extracted from Archive**| `<tempdir>/main.py` | `92b29c3ce75f2306d9b61803457404032fcd4ca1129f19e1ad0107e018f35f44` | **BIT-IDENTICAL MATCH** |

---

## 3. Extracted Execution Test Results

Execution from pristine temporary directory outside workspace:
- **Seed**: `249677` (Safe dev seed)
- **Step 0 Intervention**: Verified `[['BUY_PRODUCT', 'WHEAT', 25], ['SELL', 'WHEAT', 25]]`
- **Steps Simulated**: 720 / 720
- **Terminal Cash**: $189,650.00
- **Process Return Code**: `0`

---

## 4. Round-Trip Verdict

**PASS**. The final archive extracts cleanly and the extracted artifact executes with bit-identical hash parity and 100% functional correctness.
