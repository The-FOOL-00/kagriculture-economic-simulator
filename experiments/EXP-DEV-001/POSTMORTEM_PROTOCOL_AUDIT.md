# EXP-DEV-001 POSTMORTEM PROTOCOL AUDIT

**Experiment Identifier**: `EXP-DEV-001`  
**Governing Document**: [`DEVELOPMENT_EXPERIMENT_PROTOCOL_V1.md`](file:///c:/Users/Sundareswaran/Kagriculture/DEVELOPMENT_EXPERIMENT_PROTOCOL_V1.md)  
**Freeze Ledger**: [`DEVELOPMENT_PROTOCOL_FREEZE.md`](file:///c:/Users/Sundareswaran/Kagriculture/DEVELOPMENT_PROTOCOL_FREEZE.md)  
**Auditor**: Antigravity Autonomous Pair Programmer (Forensic Audit Engine)  
**Date**: 2026-09-11  

---

## 1. Cryptographic Protocol & Git Freeze Verification

Prior to inspecting experimental execution, the cryptographic integrity of the governing protocol was verified against the repository record:

| Verification Item | Pre-Registered Standard | Observed Value | Audit Status |
| :--- | :--- | :--- | :---: |
| **Protocol File Path** | `DEVELOPMENT_EXPERIMENT_PROTOCOL_V1.md` | `DEVELOPMENT_EXPERIMENT_PROTOCOL_V1.md` | **PASS** |
| **Protocol SHA-256 Checksum** | `671e915eadd72adb710421b45e6a33ad533abd9d68ff67770b8dd412ff7381b3` | `671e915eadd72adb710421b45e6a33ad533abd9d68ff67770b8dd412ff7381b3` | **PASS (Bit-Exact)** |
| **Git Commit Identifier** | `a1ba5acb0d04689874ce1333892825f014eea924` | `a1ba5acb0d04689874ce1333892825f014eea924` | **PASS (Committed)** |
| **Working Tree Status** | Clean (0 uncommitted modifications) | Clean (`git status -s` = empty) | **PASS** |
| **Freeze Ledger Registration** | Recorded in `DEVELOPMENT_PROTOCOL_FREEZE.md` | Matches Section 1 freeze certificate | **PASS** |

> **Conclusion**: The protocol was cryptographically locked and committed prior to execution. No retroactive modifications to hypotheses, sample sizes, partitions, or stopping criteria occurred.

---

## 2. Specification Audit: Pre-Registered Protocol Elements vs. Executed Run

Each structural element of EXP-DEV-001 defined in Section 4.1 of [`DEVELOPMENT_EXPERIMENT_PROTOCOL_V1.md`](file:///c:/Users/Sundareswaran/Kagriculture/DEVELOPMENT_EXPERIMENT_PROTOCOL_V1.md#L68-L90) was audited against the executed runner ([`experiments/EXP-DEV-001/run_exp_dev_001.py`](file:///c:/Users/Sundareswaran/Kagriculture/experiments/EXP-DEV-001/run_exp_dev_001.py)):

### 2.1 Research Question & Formal Hypotheses
- **Protocol RQ1**: "Does conditioning crop planting on revealed town shops at Day 3 (Step 72) and Day 6 (Step 144) outperform the static 19S/0T Strawberry Bedrock without increasing downside tail variance?"
- **Formal Hypothesis ($H_1$)**: Dynamic switching to complementary crops achieves mean paired margin $\Delta \mu > +\$50.00$ over static 19S/0T in `ClosedLoopAgentV2`, with non-inferior 5th percentile downside risk ($p_{05}(\text{Candidate}) \ge p_{05}(\text{Control}) - \$50.00$).
- **Null Hypothesis ($H_0$)**: $\Delta \mu \le \$0.00$ or $p_{05}$ downside degrades by $> \$50.00$.
- **Audit Finding**: Accurately represented in candidate implementation and runner assertions.

### 2.2 Control and Treatment Definitions
- **Control A (Primary)**: `ClosedLoopAgentV2` (Static 19S/0T Strawberry Bedrock, SHA-256: `95b64439...`).
- **Control B**: Static `19S / 0T` bedrock.
- **Reference Benchmark**: `Dmitrii-LB2800` ([`extracted_agents/dmitrii_lb2800/main.py`](file:///c:/Users/Sundareswaran/Kagriculture/extracted_agents/dmitrii_lb2800/main.py)).
- **Candidate Treatment**: `dev_001_dynamic_portfolio` ([`candidates/closed_loop_architecture/dev_001_dynamic_portfolio.py`](file:///c:/Users/Sundareswaran/Kagriculture/candidates/closed_loop_architecture/dev_001_dynamic_portfolio.py)).
- **Audit Finding**: Controls and candidate resolved to their exact paths and cryptographic identities.

### 2.3 Primary Success Metric
- **Protocol Definition**: Mean Paired Margin vs `ClosedLoopAgentV2` in coins:
  $$\text{Margin}(s) = (\text{Cand}_0 - \text{Ctrl}_1) + (\text{Cand}_1 - \text{Ctrl}_0)$$
- **Audit Finding**: Executed runner used this exact formula across all 50 seeds (Match 0: Cand Seat 0 vs Ctrl Seat 1; Match 1: Ctrl Seat 0 vs Cand Seat 1).

### 2.4 Seed Partitions & Sample Size
- **Protocol Definition**:
  - Stage 1 Discovery: 50 seeds (`50000–50049`, 100 matches).
  - Stage 2 Qualification: 50 seeds (`50050–50099`, 100 matches).
  - Holdout: 50 seeds (`214200–214249`, 100 matches).
- **Audit Finding**:
  - Exactly 50 Discovery seeds were executed (`50000–50049`).
  - Qualification seeds (`50050–50099`) were **NOT** executed.
  - Virgin holdout seeds (`214200–214249`) were **NOT** executed and programmatic assertion `assert_not_holdout(seed)` was active.

### 2.5 Stop Criteria & Downside Thresholds
- **Protocol Stop Rule 1**: "If Discovery mean margin $< \$0.00$, mark `FAILED` and terminate."
- **Protocol Stop Rule 2**: "If worst single-seed loss $< -\$800.00$, mark `FAILED` (tail risk unacceptable)."
- **Audit Finding**:
  - **Threshold Origin Verification**: Both stop rules were present in the frozen protocol committed at `a1ba5acb...` before execution began. The $-\$800.00$ tail threshold was **NOT** retroactively invented or adjusted after observing Seed 50018.
  - **Application**: Worst single-seed loss was $-\$2,388.00$. Because $-\$2,388.00 < -\$800.00$, Stop Rule 2 was legitimately triggered.

---

## 3. Protocol Audit Verdict

| Category | Status | Notes |
| :--- | :---: | :--- |
| **Protocol Integrity** | **PASS** | Cryptographic hash bit-exact; git tree pristine. |
| **Execution Fidelity** | **PASS** | Matched pre-registered runner specifications. |
| **Stop Rule Pre-Registration** | **PASS** | $-\$800.00$ threshold confirmed in pre-experimental Git commit. |
| **Holdout Boundary** | **PASS** | Certified virgin holdout 100% untouched. |
| **OVERALL PROTOCOL VERDICT** | **VALID** | The execution strictly adhered to protocol governance. |
