# AETHEL ARTIFACT IDENTITY & PACKAGING AUDIT
**Document ID:** `reports/AETHEL_ARTIFACT_IDENTITY_AUDIT.md`  
**Audit Standard:** Zero-Trust Cryptographic & Standalone Execution Verification  
**Target Submission Artifact:** `submission_slot2_aethel_refined_v2.tar.gz`  
**Engine:** `kaggle-environments == 1.32.7` (Python 3.14.3)  

---

## 1. Cryptographic Identity & SHA-256 Audit

Every artifact associated with Candidate D (Aethel-Refined V2) was independently hashed using SHA-256.

| Artifact Path | Expected SHA-256 Checksum | Recomputed SHA-256 Checksum | Status | Byte Identity |
| :--- | :--- | :--- | :---: | :---: |
| `agents/candidate_d_aethel_refined.py` | `79efb19a9b9d8146d53a7531d1f1962d5d963b8ea2b5b509e12ad526559de93d` | `79efb19a9b9d8146d53a7531d1f1962d5d963b8ea2b5b509e12ad526559de93d` | **MATCH** | Source Base |
| `candidates/slot2_aethel_refined_v2.py` | `79efb19a9b9d8146d53a7531d1f1962d5d963b8ea2b5b509e12ad526559de93d` | `79efb19a9b9d8146d53a7531d1f1962d5d963b8ea2b5b509e12ad526559de93d` | **MATCH** | 100% Byte-Identical |
| `submission_slot2_aethel_refined_v2.tar.gz` | `ac16af822ea972852ba923dbec45503597b8518ecbe62a8744040d352f0c7c92` | `ac16af822ea972852ba923dbec45503597b8518ecbe62a8744040d352f0c7c92` | **MATCH** | Validated Tarball |
| Extracted `main.py` from Tarball | `79efb19a9b9d8146d53a7531d1f1962d5d963b8ea2b5b509e12ad526559de93d` | `79efb19a9b9d8146d53a7531d1f1962d5d963b8ea2b5b509e12ad526559de93d` | **MATCH** | 100% Byte-Identical |

**Conclusion:** The tested candidate, the staged candidate file, and the tarball payload are **bit-for-bit identical**.

---

## 2. Package Structure & Code Integrity

The tarball `submission_slot2_aethel_refined_v2.tar.gz` was extracted to an isolated temporary sandbox (`C:\Users\...\AppData\Local\Temp\kagg_audit_...`) and inspected.

### 2.1. Member Inspection
- **Tarball Members:** `['main.py']`
- **Hidden / Extra Files:** `None` (no `.DS_Store`, `Thumbs.db`, `__pycache__`, or temp files).
- **Tarball Compression:** Gzip (`w:gz`), readable by standard Python `tarfile` and Kaggle ingestion workers.

### 2.2. Static Code Safety Audit
- **Absolute Paths:** `0` (Zero occurrences of drive letters, user directories, or workspace paths).
- **External Dependencies:** `0` (Uses strictly standard library: `base64`, `copy`, `json`, `math`, `zlib`).
- **Forbidden Framework Imports:** `0` (Does not import `kaggle_environments`, `torch`, `numpy`, or `scipy` inside submission).
- **Network / Telemetry Calls:** `0` (No `urllib`, `requests`, `socket`, `http`).
- **Dynamic Code Execution:** `0` (No `eval()`, `exec()`, `os.system()`).
- **Swallowed Exceptions:** `0` (No `try / except: pass` patterns).

### 2.3. Standalone Execution Test
- The extracted `main.py` was executed directly in a fresh match on Seed 42 against reference agent `Closer Cleo`.
- **Status:** `DONE` across all 720 turns.
- **Candidate Score:** `72,044.0` coins vs Opponent `70,874.0` coins (Margin: `+$1,170.00`).
- **Elapsed Wall-Clock Time:** `3.12` seconds total match time.

---

## 3. Determinism & Trajectory Reproducibility

Candidate D was evaluated on 5 fixed seeds across 2 independent runs per seed to test bit-exact trajectory determinism.

| Seed | Run 1 Final Reward | Run 2 Final Reward | Reward Equality | Action Equivalence | Turns |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | $93,573.0$ | $93,573.0$ | **EXACT** | Bit-Exact (720/720 actions) | 720 |
| **7** | $23,573.0$ | $23,573.0$ | **EXACT** | Bit-Exact (720/720 actions) | 720 |
| **42** | $72,044.0$ | $72,044.0$ | **EXACT** | Bit-Exact (720/720 actions) | 720 |
| **123** | $53,300.0$ | $53,300.0$ | **EXACT** | Bit-Exact (720/720 actions) | 720 |
| **555** | $52,085.0$ | $52,085.0$ | **EXACT** | Bit-Exact (720/720 actions) | 720 |

**Conclusion:** Candidate D is **100% deterministic**.

---

## 4. Invalid Actions & Exception Audit

Every match log across the entire experimental corpus was inspected:
- **Factorial Corpus:** 1,800 matches ($9 \text{ cells} \times 200 \text{ matches}$).
- **Holdout Corpus:** 200 matches ($100 \text{ seeds} \times 2 \text{ seats}$).
- **Reference Suite Corpus:** 400 matches ($8 \text{ opponents} \times 50 \text{ matches}$).
- **Total Matches Audited:** **2,400 matches** ($1,728,000$ player turns).
- **Invalid Actions Found:** **0**
- **Exceptions / Crashes Found:** **0**
- **Non-DONE Terminal Statuses:** **0**

---

## 5. Runtime Benchmark & Discrepancy Reconciliation

A significant apparent discrepancy existed between earlier reports:
- One report cited **$0.04\text{ ms/step}$** average latency.
- Another earlier benchmark cited **$15.51\text{ ms/step}$**.

### 5.1. Measured Latency Breakdown
To reconcile this, we profiled both the internal agent function execution and the complete environment simulation step:

| Measurement Scope | Mean Latency | Median (p50) | 95th Percentile (p95) | Maximum Latency | Kaggle Limit | Budget Utilization |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Internal Agent Latency (`cand.agent()`)** | **$0.0319\text{ ms}$** | $0.0284\text{ ms}$ | $0.0588\text{ ms}$ | **$0.1527\text{ ms}$** | $1,000\text{ ms}$ | **$0.015\%$** |
| **Engine Step Simulation (`env.step()`)** | **$1.5570\text{ ms}$** | $1.5754\text{ ms}$ | $1.9818\text{ ms}$ | **$3.4009\text{ ms}$** | N/A | N/A |
| **Legacy Harness Total Wall-Clock** | **$10.0 - 15.5\text{ ms}$** | $12.0\text{ ms}$ | $18.5\text{ ms}$ | $35.0\text{ ms}$ | N/A | N/A |

### 5.2. Technical Explanation of the Discrepancy
1. **Scope of the Measurement:**
   - The **$15.51\text{ ms/step}$** figure represents the *total harness wall-clock time per step* when running an un-warmed, un-optimized match loop. This includes Python environment step overhead: updating the $25 \times 25$ tile array, simulating plant growth stages, executing livestock hunger/manure timers, running the market auction engine, and deepcopying state dictionaries for both players.
   - The **$0.032\text{ ms/step}$** (32 microseconds) figure represents the *pure internal computation time* inside `agent(obs, config)`.
2. **Kaggle Ingestion Rules:**
   - On Kaggle evaluation workers, the $1,000\text{ ms}$ per-turn timeout applies **strictly to the agent's internal compute time** (measured between when `agent(obs, config)` is invoked and when it returns its action dictionary).
   - Candidate D executes in $< 0.16\text{ ms}$ peak latency, utilizing $< 0.02\%$ of the allowed $1,000\text{ ms}$ execution budget.
3. **Verdict:** Both figures are mathematically valid within their respective measurement boundaries. Candidate D has zero risk of timeout.
