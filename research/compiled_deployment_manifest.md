# Championship Compiled Deployment Manifest

**Document ID**: `research/compiled_deployment_manifest.md`  
**Timestamp**: 2026-09-10T20:41:00+05:30  
**Environment**: Python 3.14.0 (64-bit), `kaggle-environments` 1.32.7  
**Compiler Script**: `scratch/compile_v54_championship.py`  
**Compiler SHA256**: `9214e6dd37865414ada385782d6638b28baada08ef31997550887752cf8dd10b`  

---

## 1. Cryptographic Lineage & Checksums

### Artifact 1: V54++ Control (Frozen Baseline Champion)
- **Source File**: `candidates/v54_plus_shop.py`
- **Source SHA256**: `592f0ba31b3b20b5a3aad409a753b5e6bdeb29a9eb2381342b1cd527509fa9e8`
- **Compiled File**: `candidates/compiled_v54_plus_shop.py`
- **Compiled SHA256**: `f651ccd220e701968bc33579812d8917da63f5b0582f2fd0d363fa6a16ffd8b8`
- **Identity**: V54++ Control Standalone
- **50-Seed Behavioral Equivalence**: **PASS (0 Mismatches)**
- **Isolated Raw Execution**: **PASS (5/5 Seeds, Status DONE)**
- **Determinism**: **PASS (10/10 Seeds)**

### Artifact 2: V54++ Residual (Independently Validated Candidate)
- **Source File**: `candidates/v54_plus_residual.py`
- **Source SHA256**: `5b2d5080ba38287812d137a21c7b09071e1f66a10c32d7c3ec4bb61be4520e80`
- **Compiled File**: `candidates/compiled_v54_plus_residual.py`
- **Compiled SHA256**: `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb`
- **Identity**: V54++ Residual Standalone
- **Verified Parameter Overrides**:
  - `preempt_money_deficit = 2000.0`
  - `preempt_minimum_delta = 4.0`
  - `preempt_maximum_batch = 12`
- **50-Seed Behavioral Equivalence**: **PASS (0 Mismatches)**
- **Isolated Raw Execution**: **PASS (5/5 Seeds, Status DONE)**
- **Determinism**: **PASS (10/10 Seeds)**

---

## 2. Invariance Verification

- **Macro Route**: Byte-for-byte identical (`_V56_BACKBONE_ROUTE`, `_V56_YARN_ROUTE`, `_V58_BAKERY_YARN_ROUTE`).
- **Tactical Overlays**: Strawberry seed trim, shed guard, terminal loaded units, home convergence, and terminal liquidation.
- **Shop Logic**: Pure public observation S2 model.
- **Zero External Dependencies**: Standalone single-file Python modules executable by raw Kaggle runner.
