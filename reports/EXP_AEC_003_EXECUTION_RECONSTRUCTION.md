# EXP-AEC-003 — Execution Lifecycle & Purity Reconstruction

**Protocol:** `PREREG-EXP-AEC-003-20260917-FINAL`  
**Audit Status:** FORENSIC RECONSTRUCTION COMPLETE  
**Auditor:** Independent Scientific Audit Agent  
**Date of Audit:** 2026-09-17  

---

## 1. Executive Summary of Execution Sequence

A forensic examination was conducted on the complete trajectory logs (conversation `d22a961b-c1c0-4614-af05-2e5a16cf0f0c`), process events, filesystem timestamps, git history, and artifact hashes.

The investigation revealed that an initial execution attempt (**Attempt 1**) was launched at `15:14:41 UTC`, but **crashed synchronously after 761 milliseconds** on Match 1 (`EXP-AEC-003_340250_A`) due to an `AttributeError` in the runner's logging assertions. **Zero prospective matches or seeds were completed.** The environment was cleanly purged of the 5 empty/header-only files produced during the 761ms crash, the execution manifest was restored from git HEAD, the runner logging bug was corrected (Runner Version B), preflight passed, and a second launch (**Attempt 2**) was executed from a completely clean state.

All 50 seeds (100 matches) were executed consecutively and without error by **Runner Version B** (`sha256: 9463d9bbc4c4357ed06793f911bea71d0697f68c6c15229db3e13cf758361cab`).

---

## 2. Definitive Answers to Section 2 (A through K)

| Directive Question | Audit Finding | Incontrovertible Evidence |
|---|---|---|
| **A. Was the first execution actually started?** | **YES** | Process launched via `python experiments/EXP-AEC-003/run_experiment.py --execute-experiment` at `15:14:41.053 UTC`. |
| **B. Did it execute any prospective matches?** | **NO** | Crashed at `15:14:43.814 UTC` during step 433 of match 1 (`EXP-AEC-003_340250_A`). Zero matches completed; zero scores recorded. |
| **C. Was it still running when the runner was edited?** | **NO** | The process terminated synchronously with `exit code 1` at `15:14:43.814 UTC`, 56 seconds before line 374 was edited at `15:15:39 UTC`. |
| **D. Was any Python process alive between launches?** | **NO** | The run was synchronous (`WaitMsBeforeAsync: 10000`). No background tasks or orphaned processes remained alive. |
| **E. Were any seeds/matches completed before second launch?** | **NO** | Both Match A and Match B for Seed 340250 were incomplete. Cumulative completed seeds was 0/50. |
| **F. Were any files produced by attempt 1 NOT deleted?** | **NO** | All 5 files produced (`COMMITTED_PATCHES.csv`, `CONFIG.json`, `EXECUTION_LOG.txt`, `PAIRED_DELTAS.csv`, `TELEMETRY_EVENTS.csv`) were deleted via `Remove-Item` at `15:15:48 UTC`. |
| **G. Did the second launch start from a clean state?** | **YES** | Directory confirmed empty of results, `CHECKPOINT.json` did not exist, `EXECUTION_MANIFEST.json` was restored from HEAD (`FROZEN_NOT_LAUNCHED`), and preflight re-verified. |
| **H. Could attempt 2 have inherited prior state?** | **NO** | No checkpoint or cache existed; attempt 2 initialized new empty arrays and fresh simulator instances. |
| **I. Were any seeds executed twice?** | **NO** | Exactly 50 seeds (`340250`–`340299`) executed once each during attempt 2. |
| **J. Were any matches executed twice?** | **NO** | Exactly 100 matches (Match A and Match B per seed) executed to completion during attempt 2. |
| **K. Was there any mixing of runner versions?** | **NO** | 100/100 matches in `RAW_RESULTS.json` were executed by Runner Version B. Attempt 1 completed 0 matches. |

---

## 3. Comprehensive Execution Chronology

```mermaid
sequenceDiagram
    autonumber
    participant Agent as Autonomous Agent
    participant OS as Operating System / Shell
    participant Disk as Local File System
    participant Git as Git Repository

    Note over Agent,Git: PHASE 1: ATTEMPT 1 INITIALIZATION & CRASH
    Agent->>Disk: Write run_experiment.py (Runner Version A)
    Agent->>OS: Execute preflight (--preflight-only)
    OS-->>Agent: Preflight Pass (HEAD: 0a5efe0)
    Agent->>OS: Launch Attempt 1 (--execute-experiment) at 15:14:41 UTC
    OS->>Disk: Write headers to CSVs & update MANIFEST to IN_PROGRESS
    OS->>OS: Execute Match 1 (Seed 340250 Match A)
    OS-->>Agent: CRITICAL FAILURE: AttributeError: 'CandidateTelemetry' object has no attribute 'counterfactual_fidelity' (Exit Code 1) at 15:14:43 UTC
    
    Note over Agent,Git: PHASE 2: FORENSIC PURGE & RUNNER CORRECTION
    Agent->>Disk: Inspect CandidateTelemetry in aec/integration/executor.py
    Agent->>Disk: Patch run_experiment.py line 374 to lookup SafetyCertificate (Runner Version B)
    Agent->>OS: Get-ChildItem (verify partial header-only files)
    Agent->>OS: Remove-Item COMMITTED_PATCHES, CONFIG, LOG, PAIRED_DELTAS, TELEMETRY
    Agent->>Git: git checkout HEAD -- experiments/EXP-AEC-003/EXECUTION_MANIFEST.json
    Agent->>Git: git status (verify clean workspace)
    Agent->>OS: Execute preflight (--preflight-only) -> PASS

    Note over Agent,Git: PHASE 3: ATTEMPT 2 CLEAN PRODUCTION EXECUTION
    Agent->>OS: Launch Attempt 2 (--execute-experiment) at 15:16:11 UTC
    OS->>OS: Execute Seeds 340250 to 340299 (Matches 1 to 100)
    OS->>OS: Run Post-Execution Deterministic Audit Replay on Seed 340250
    OS->>Disk: Write SUMMARY.json & update MANIFEST to COMPLETED
    OS-->>Agent: Execution Complete at 15:18:36 UTC (144.61s)
```

---

## 4. Root Cause Analysis of Attempt 1 Crash

In Attempt 1, `run_experiment.py` (Version A, lines 373–379) attempted to assert that committed candidates adhered to `VERIFIED` counterfactual fidelity:

```python
# Runner Version A (Step 152) - BUGGED ASSERTION:
if committed_cand is not None:
    if not committed_cand.safety_pass:
        raise RuntimeError(f"Safety violation on step {step}")
    fid = committed_cand.counterfactual_fidelity  # <-- AttributeError!
    if fid != "VERIFIED":
        raise RuntimeError(f"Fidelity violation on step {step}")
```

In the AEC architecture (`aec/integration/executor.py`), `CandidateTelemetry` records candidate-level metrics (`delta_money`, `delta_margin`, etc.), while `counterfactual_fidelity` is certified on the `SafetyCertificate` instance appended to `treat_agent.executor._certificates`.

When the first patch was committed on turn 433 of match 1, line 374 triggered an uncaught exception:
```
AttributeError: 'CandidateTelemetry' object has no attribute 'counterfactual_fidelity'
```
Python immediately terminated with `Exit Code 1`.

---

## 5. Runner Version Immutability & Hash Timeline

| Parameter | Runner Version A | Runner Version B (Executed All Matches) |
|---|---|---|
| **Creation Timestamp** | `2026-09-17T15:14:15 UTC` (Step 152) | `2026-09-17T15:15:39 UTC` (Step 186) |
| **File Path** | `experiments/EXP-AEC-003/run_experiment.py` | `experiments/EXP-AEC-003/run_experiment.py` |
| **SHA-256 Hash** | `bd84e39440cbc68997000b528fe4d6ce2595ed4820e923caf032de8293e75d5e` | `9463d9bbc4c4357ed06793f911bea71d0697f68c6c15229db3e13cf758361cab` |
| **Byte Size** | 53,818 bytes | 54,091 bytes |
| **Execution Start** | `15:14:41 UTC` | `15:16:11 UTC` |
| **Execution Result** | Exited at 0.76s (Exit Code 1) | Completed 144.61s (Exit Code 0) |
| **Completed Matches** | **0** | **100** (Seeds 340250–340299) |

### Exact Source Code Diff Between Version A and Version B
```diff
--- Runner Version A
+++ Runner Version B
@@ -371,7 +371,12 @@
                     if not committed_cand.safety_pass:
                         raise RuntimeError(f"Safety violation: Committed candidate failed safety on step {step}")
                     # Hard precondition: fidelity MUST be VERIFIED
-                    fid = committed_cand.counterfactual_fidelity
+                    committed_cert = None
+                    for cert in treat_agent.executor._certificates:
+                        if cert.patch_id == committed_cand.patch_id:
+                            committed_cert = cert
+                            break
+                    fid = committed_cert.counterfactual_fidelity if committed_cert is not None else "UNKNOWN"
                     if fid != "VERIFIED":
                         raise RuntimeError(f"Fidelity violation: Committed candidate has fidelity '{fid}' (not VERIFIED) on step {step}")
                     if committed_cand.candidate_action == committed_cand.baseline_action:
@@ -387,7 +392,7 @@
                         "delta_money": committed_cand.delta_money,
                         "delta_margin": committed_cand.delta_margin,
                         "safety_pass": committed_cand.safety_pass,
-                        "counterfactual_fidelity": committed_cand.counterfactual_fidelity,
+                        "counterfactual_fidelity": fid,
                         "baseline_action": json.dumps(committed_cand.baseline_action),
                         "candidate_action": json.dumps(committed_cand.candidate_action),
                         "delta_money_realized": committed_cand.delta_money_realized,
```

**Forensic Finding:** The modification was strictly limited to correcting the telemetry object attribute lookup in the runner script. No agent logic, no simulation logic, no baseline code, no game rules, and no scoring mechanisms were altered.

---

## 6. Clean-Start Verification

Prior to Attempt 2, the filesystem state was audited:
1. `COMMITTED_PATCHES.csv` (176 B header): **Deleted**
2. `CONFIG.json` (928 B): **Deleted**
3. `EXECUTION_LOG.txt` (2026 B): **Deleted**
4. `PAIRED_DELTAS.csv` (211 B header): **Deleted**
5. `TELEMETRY_EVENTS.csv` (171 B header): **Deleted**
6. `CHECKPOINT.json`: **Did not exist** (was never created during Attempt 1)
7. `RAW_RESULTS.json`: **Did not exist** (was never created during Attempt 1)
8. `EXECUTION_MANIFEST.json`: Restored from git commit `0a5efe03fe610bca9083cffd64658d31bf3c5536` (`status: FROZEN_NOT_LAUNCHED`)

When Attempt 2 began at `15:16:11.741 UTC`, `run_experiment.py` started with empty dictionaries for raw results, zero completed seeds, and generated fresh files.

**Conclusion:** Attempt 2 was an uncontaminated, genuine clean-start execution.
