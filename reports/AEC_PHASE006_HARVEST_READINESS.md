# SPDX-License-Identifier: MIT
# AEC Phase 006: Coupled Trajectory-Preserving Patch Engine & Dynamic Shadow Harvest
## Formal Readiness Assessment & Scientific Classification

**Phase**: AEC Phase 006  
**Components**: 
- `CoupledPatchEngine` & `CoupledPatch` Architecture (`aec/patches/coupled_patch.py`, `aec/patches/coupled_patch_engine.py`)
- `DYNAMIC_SHADOW_HARVEST` & `TERMINAL_HARVEST_SWEEP` (`aec/patches/harvest_patch.py`, `aec/patches/generator.py`)  
**Evaluation Scope**: Exact C++ Simulator (`kagsim`) on Development Cohort `50000–50024`  
**Date**: September 2026  

---

### 1. Scientific Classification

In accordance with AEC Phase 006 Governance Directives (§39):

| Component / Layer | Formal Scientific Classification | Status Rationale |
| :--- | :---: | :--- |
| **`CoupledPatch` Architecture** | **OFFLINE VALIDATED** | Generic, mechanism-agnostic trajectory splicing engine validated across 33 unit/adversarial tests (`CP-01`–`CP-30`, `ADV-01`–`ADV-03`) and 429 repository tests. Fully enforces trajectory preservation contracts, empty worker inventory invariants, and fail-closed safety state machines. |
| **`DYNAMIC_SHADOW_HARVEST`** | **OFFLINE CANDIDATE VALIDATED** | Successfully eliminates the catastrophic uncoupled cargo desynchronization observed in Phase 005B (-$7,452.32 naive mean delta). Coupled patches deliver up to +$19,054.00 net game gains when conditions permit, and exact forward counterfactual gating rejects disruptive diversions with 100% fail-closed precision. Ready for full integrated offline candidate replay. |
| **`TERMINAL_HARVEST_SWEEP`** | **OFFLINE CANDIDATE VALIDATED** | Enforces exact simulator step 718 boundary semantics, requiring full liquidation into shed and market on or before step 718. Rejects unliquidated field or carried assets with `TERMINAL_RISK`. |
| **`RESOURCE_CONVERSION`** | **QUARANTINED** | Preserved in strict quarantine per Phase 004B/005/006 charter. Zero commits permitted. |

---

### 2. Scientific Governance & Compliance Verification

| Audit Item | Charter Requirement | Actual Measured State | Compliance Status |
| :--- | :--- | :--- | :---: |
| **Frozen V3 Chassis** | `SHA-256 == 845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` | `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` | **100% BYTE-IDENTICAL** |
| **Primary Holdout** | Seeds `340050–340199` untouched | 0 accesses, 0 simulations, 0 scans | **100% ISOLATED** |
| **Gate 0.3 Holdout** | Seeds `214200–214249` untouched | 0 accesses, 0 simulations, 0 scans | **100% ISOLATED** |
| **Prospective Cohort** | Seeds `340300–340349` untouched | 0 accesses, 0 simulations, 0 scans | **100% ISOLATED** |
| **Tournament Matches** | Zero prospective ladder runs allowed | 0 matches run | **100% ISOLATED** |
| **Development Cohort** | Seeds `50000–50024` only | 25 development seeds analyzed | **COMPLIANT** |
| **Mechanism Quarantine**| `RESOURCE_CONVERSION = QUARANTINED` | Unaltered; strictly quarantined | **COMPLIANT** |

---

### 3. Readiness Breakdown by Subsystem

#### 3.1 Reusable CoupledPatch Engine (`aec/patches/coupled_patch_engine.py`)
- **Precondition / Postcondition Verification**: Explicit typing ensures every patch verifies preconditions (crop ripeness, worker capability, shed capacity) and guarantees postconditions (empty worker backpack, synchronized waypoint, verified legal baseline continuation).
- **Trajectory Preservation Certificate**: Emits formal `TrajectoryPreservationCertificate` confirming zero cargo encumbrance and zero route disruption for the subsequent baseline command.
- **Fail-Closed State Machine**: Transitions through `PROPOSED -> FEASIBILITY_CHECK -> ROUTE_TO_TARGET -> EXECUTE_TARGET -> CARGO_RESOLUTION -> ROUTE_TO_RECONNECT_OR_DEPOSIT -> RECONNECT -> VERIFY_POSTCONDITION -> COUNTERFACTUAL -> SAFETY -> ECONOMIC_GATE -> COMMIT`. Any anomaly terminates closed (`INFEASIBLE`, `ROUTE_FAILURE`, `CARGO_UNRESOLVED`, `TERMINAL_RISK`, `ECONOMIC_FAILURE`).

#### 3.2 Dynamic Shadow Harvest (`aec/patches/harvest_patch.py`)
- **Idle Worker Priority**: Efficiently detects idle auxiliary hands (`PASS`/`WAIT`), building bounded detours that convert unused labor into liquidated shed cash.
- **Busy Worker Economic Screening**: Uses `LaborOpportunityCostEngine` to calculate displacement opportunity cost $OC$. Bypasses expensive forward simulation if gross harvest value $\le OC$.
- **Exact Forward Counterfactual Authority**: Employs exact forward simulation to evaluate candidate patches over their adaptive horizon. Rejects any patch where net terminal delta $\le 0.0$.

#### 3.3 Terminal Harvest Sweep (`aec/patches/harvest_patch.py`)
- **Step 718 Strict Realization**: Enforces strict C++ simulator step 718 liquidation. Rejects any patch requiring actions at step $\ge 719$.
- **Zero Biological Phantom Value**: Prohibits valuing unharvested field crops or carried items as liquid score.

---

### 4. Integration Roadmap & Next Architectural Phase

With the validation of the `CoupledPatch` primitive and `DYNAMIC_SHADOW_HARVEST`, the architectural prerequisites for the AEC are fully established.

**Direct Strategic Instruction (§44)**:
> "Do not automatically start another isolated mechanism. The goal after this phase is to produce the **first real integrated AEC candidate**. Once CoupledPatch + Harvest are validated, prioritize integration of the already-developed architecture:
> `V3 + Economic IR + Market Timing + Reconnect + MultiWorker + Labor Shadow + CoupledPatch + Dynamic Harvest + Terminal Harvest + Adaptive Horizon + Safety + Commit/Abstain`
> Then perform the first **full-system offline replay**."

Phase 007 should formally construct and replay the **Unified Integrated AEC System** across development seeds `50000–50024`.
