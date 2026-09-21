# V26 — BASELINE FREEZE & ARCHITECTURAL ANCHOR

## 1. Executive Purpose
This document establishes the formal cryptographic freeze and boundary isolation for **V26 (Backbone-Aware AEC Re-Architecture & Transfer to V25)**. 

Per Section 0 of the V26 Protocol:
- `submission_aec_v22r1.tar.gz` is frozen and remains the active competition submission.
- Git tag `v22r1` (commit `33763a8f58b17bc3a32735c2a322883b78ed3778`) is immutable.
- All V26 research is isolated on the dedicated research branch `research/v26-backbone-aware-aec`.
- Neither V22R1 nor the frozen V3 payload may be altered in any manner.

---

## 2. Cryptographic Artifact Ledger

| Artifact Identifier | Local File Path | SHA-256 Digest | Status |
| :--- | :--- | :--- | :--- |
| **V22R1 Final Submitted Archive** | `submission_aec_v22r1.tar.gz` | `6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5` | **FROZEN / PROTECTED** |
| **V3 Frozen Baseline Tarball** | `submission_Vj_kc_v3.tar.gz` | `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` | **FROZEN / REFERENCE** |
| **V25 P3 Unified Macro Planner** | `candidates/v25_p3_unified.py` | `13292582c8cc796bc11ccebff9684fbec45cfb97d936fb9e85e4e9bb4dbea179` | **PROMOTED RESEARCH BASELINE** |

> Correction (2026-09-21): the worktree file is byte-identical to blob `e4eb8a4:candidates/v25_p3_unified.py` (`cmp` clean, 4142 bytes); the previously recorded digest was erroneous and is superseded by the value above, which also matches the `backbone_hash` recorded in tournament checkpoints.
| **V26 Research Branch Base** | Git Commit `33763a8` | `33763a8f58b17bc3a32735c2a322883b78ed3778` | **TAG: v22r1** |

---

## 3. Active Branch & Environment Isolation

1. **Active Branch**: `research/v26-backbone-aware-aec`
2. **Base Commit**: `33763a8f58b17bc3a32735c2a322883b78ed3778` (Tag `v22r1`)
3. **Workspace Path**: `c:\Users\Sundareswaran\Kagriculture`
4. **Engine Version**: `1.32.7` (Kaggle Environments)
5. **CRN Cohort Reservation**:
   - `249000..249469`: Historical dev, discovery, and confirmation (CONSUMED)
   - `214200..214249`, `340050..340199`, `340300..340349`: Sealed Holdouts (100% UNTOUCHED)
   - `249470..249489`: Reserved for V26 First Transfer Study (VIRGIN)

---

## 4. Architectural Target & Separation of Concerns

```text
                   BACKBONE
                      │
               Backbone Adapter
                      │
                      ▼
               Economic State IR
                      │
          ┌───────────┴───────────┐
          │                       │
   Opportunity Model       Backbone Forecast
          │                       │
          └───────────┬───────────┘
                      ▼
             Candidate Generator
                      ▼
             Exact CF Simulator
                      │
             Active Backbone
             Continuation
                      ▼
             Macro Regime Check
                      ▼
               Safety Gates
                      ▼
             Commit / Abstain
                      ▼
                 Executor
```

**Core Principle**: The AEC proposes economic interventions; the active backbone determines what the world would look like if the intervention were not made.
