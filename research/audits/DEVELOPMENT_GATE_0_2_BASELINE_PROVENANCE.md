# DEVELOPMENT GATE 0.2 — BASELINE PROVENANCE AUDIT
## Verification of Simulator Integrity, Agent Artifacts, Paired CRN Protocols, and Baseline Catalog Accuracy

**Gate Protocol**: Development Gate 0.2 Final Experiment-Readiness Audit  
**Governing Standard**: Section 11 & Section 25 Baseline Protection Rules  
**Audit Target**: [`DEVELOPMENT_BASELINE_MAP.md`](file:///c:/Users/Sundareswaran/Kagriculture/DEVELOPMENT_BASELINE_MAP.md) and all referenced baseline code/data  
**Date**: 2026-09-11  
**Auditor**: Antigravity Autonomous Pair Programmer (Audit Engine)  
**Status**: **FORMAL AUDIT REPORT — DEFECTS IDENTIFIED**

---

## 1. Executive Summary & Verification Scorecard

The integrity of future strategy development depends upon an immutable, scientifically grounded baseline. In this audit, we verified all six baseline agents, their execution scripts, the simulator version, the Common Random Number (CRN) pairing protocol, and the statistical metrics published in [`DEVELOPMENT_BASELINE_MAP.md`](file:///c:/Users/Sundareswaran/Kagriculture/DEVELOPMENT_BASELINE_MAP.md).

### **BASELINE AUDIT SCORECARD**:

| Baseline Governance Invariant | Requirement | Empirical Audit Finding | Status |
| :--- | :--- | :--- | :---: |
| **Simulator Version** | Audited C++ `sim.hpp` / `kagsim` | Bit-exact match with competition engine axioms. | **VERIFIED (100%)** |
| **Agent Source Integrity** | Valid physical paths for all catalog agents | Path for `Dmitrii-LB2800` is dead (`agent.py` does not exist). | **DEFECT DETECTED** |
| **Paired Seed Protocol** | Symmetric Seat 0 & Seat 1 evaluation | 150 seeds, 300 matches, summed net margin. | **VERIFIED (100%)** |
| **Baseline Statistics** | Mean, median, SE, CI, $t$-test matching raw JSON | Recomputed metrics match raw data to 4 decimal places. | **VERIFIED (100%)** |
| **Holdout Cleanliness** | No contaminated holdout in baseline qualification | Proposed fresh holdout (50150–50199) is contaminated. | **CONTAMINATED** |
| **Future Info Isolation** | Zero future information in baseline execution | Hindsight post-match shop scan in `run_margin_scan.py`. | **SCOPED HEURISTIC** |
| **Frozen Live Controls** | Untouched SHA256 hashes on submissions | 56146947 and 56146971 match frozen hashes bit-for-bit. | **VERIFIED (100%)** |

---

## 2. Simulator Integrity & Engine Parity

### 2.1 Simulator Binary Verification
All baseline benchmarks were executed using the compiled Python C-extension `kagsim`, compiled directly from:
`external_repos/kaggriculture-cppsim/sim/sim.hpp`

Physical verification confirms:
1. **Town Shop Cadence**: Exactly 8 town shops drawn uniform with replacement at days 3, 6, 9, 12, 15, 18, 21, 24 (`sim.hpp:127-137`).
2. **Order Truncation Invariant**: `if (orders.size() > 10) orders.resize(10)` (`sim.hpp:512`).
3. **Shed Capacity Bound**: Hard limit of 100 units; automatic discard of excess harvested goods (`sim.hpp:147, 584`).
4. **Weed PRNG Coupling**: Coupled to common seed generator; seed determinism bit-exact.

The development baseline uses exclusively the audited C++ simulator.

---

## 3. Physical Artifact Verification Across Baseline Agents

Every agent referenced in Table 2 of `DEVELOPMENT_BASELINE_MAP.md` was physically audited for existence, file hash, and entry point validity:

```python
# Verification script executed in repository root:
files = [
    'candidates/closed_loop_architecture/closed_loop_v2.py',
    'extracted_agents/dmitrii_lb2800/agent.py',              # Catalog entry
    'scratch/crop_portfolio_sweep.py',
    'scratch/crop_portfolio_sweep_results.json',
    'candidates/compiled_v54_plus_shop.py',
    'candidates/compiled_v54_plus_residual.py',
    'scratch/run_margin_scan.py',
    'scratch/audit2_1_recompute_v2_stats.py'
]
```

### 3.1 Verification Results:

1. **`ClosedLoopAgentV2`**:
   - Path: `candidates/closed_loop_architecture/closed_loop_v2.py`
   - SHA256: `95b644391a8c72506e788ee5981ee85fef109bca36f45535560b4fc7c2a71f0a`
   - Status: **VERIFIED**. Fully self-contained class with `act()` interface.

2. **`Dmitrii-LB2800` (Catalog Path Defect)**:
   - Listed Path: `extracted_agents/dmitrii_lb2800/agent.py`
   - File Status: **MISSING (File does not exist)**.
   - Physical Directory Listing:
     - `extracted_agents/dmitrii_lb2800/main.py` (1,083 bytes, SHA256 `60155b9a...`)
     - `extracted_agents/dmitrii_lb2800/policy.py` (10,470 bytes)
     - `extracted_agents/dmitrii_lb2800/router_parent.py` (9,365 bytes)
     - `extracted_agents/dmitrii_lb2800/terminal_planner.py` (25,147 bytes)
   - Benchmark Execution Script Reality: In `scratch/run_margin_scan.py:24`, Dmitrii is imported as:
     `importlib.util.spec_from_file_location("dmitrii_agent", os.path.join(DMITRII_DIR, "main.py"))`
   - **Audit Finding**: The benchmark execution scripts correctly used `main.py`, but `DEVELOPMENT_BASELINE_MAP.md:27` recorded an erroneous filename (`agent.py`). This is a documentation defect requiring immediate correction.

3. **`19S / 0T Bedrock Baseline`**:
   - Paths: `scratch/crop_portfolio_sweep.py` & `scratch/crop_portfolio_sweep_results.json`
   - Results SHA256: `25010ff261e9c49280d4681665a587d55f483c6c06a86e921d723fa8c9bb710b`
   - Status: **VERIFIED**. 12-grid factorial sweep on 50 Discovery seeds (100 matches vs Dmitrii) established 19S/0T as highest cash ($97,026.17) and margin (+$24.98).

4. **`V54++ Control` (Submission 56146947)**:
   - Path: `candidates/compiled_v54_plus_shop.py`
   - SHA256: `f651ccd220e701968bc33579812d8917da63f5b0582f2fd0d363fa6a16ffd8b8`
   - Status: **VERIFIED**. Bit-exact match with frozen deployment artifact.

5. **`V54++ Residual` (Submission 56146971)**:
   - Path: `candidates/compiled_v54_plus_residual.py`
   - SHA256: `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb`
   - Status: **VERIFIED**. Bit-exact match with frozen deployment artifact.

---

## 4. Paired Common Random Numbers (CRN) & Statistical Provenance

The primary head-to-head baseline comparing `ClosedLoopAgentV2` against `Dmitrii-LB2800` across 150 seeds was audited for mathematical and statistical fidelity against `scratch/v2_dmitrii_margin_scan.json` and `scratch/audit2_1_recompute_v2_stats.py`.

### 4.1 Recomputed Metrics vs. Published Baseline:

| Metric | Published in Baseline Map | Recomputed from Raw JSON | Discrepancy | Provenance Status |
| :--- | :---: | :---: | :---: | :---: |
| **Sample Mean Margin** | **+$24.6133** | **+$24.6133** | $0.0000$ | **Exact** |
| **Sample Median Margin** | **+$58.0000** | **+$58.0000** | $0.0000$ | **Exact** |
| **Sample Standard Deviation** | **166.7481** | **166.7481** | $0.0000$ | **Exact** |
| **Standard Error (SE)** | **13.6149** | **13.6149** | $0.0000$ | **Exact** |
| **Paired Win Rate** | **54.67% (82W - 68L)** | **54.67% (82W - 68L)** | $0.00\%$ | **Exact** |
| **Two-Sided $t$-statistic** | **$1.8078$** | **$1.8078$** | $0.0000$ | **Exact** |
| **Two-Sided $p$-value** | **$0.0727$** | **$0.0727$** | $0.0000$ | **Exact** |
| **Student's $t$ 95% CI** | **`[-$2.29, +$51.52]`** | **`[-$2.29, +$51.52]`** | $0.00$ | **Exact** |
| **Worst Paired Loss** | **-$730.00 (Seed 50081)** | **-$730.00 (Seed 50081)** | $0.00$ | **Exact** |
| **Best Paired Win** | **+$326.00 (Seed 50020)** | **+$326.00 (Seed 50020)** | $0.00$ | **Exact** |

The statistical summary in `DEVELOPMENT_BASELINE_MAP.md` is 100% reproducible from raw simulation output.

---

## 5. Seed Partition & Holdout Cleanliness Audit

### 5.1 Partition Mapping:
- **Discovery (50000–50049)**: 50 seeds, mean margin $+\$39.12$. Legitimate exploratory partition.
- **Qualification (50050–50099)**: 50 seeds, mean margin $+\$11.40$. Legitimate confirmatory partition.
- **Audited Holdout (50100–50149)**: 50 seeds, mean margin $+\$23.32$. Correctly classified in Gate 0.1 as an "Audited Benchmark Partition".

### 5.2 The Fresh Holdout Defect in `DEVELOPMENT_BASELINE_MAP.md`:
Line 111 of `DEVELOPMENT_BASELINE_MAP.md` asserts:
> *"Any new candidate agent developed in this phase must achieve confirmatory validation on an untouched **Fresh Virgin Holdout (Seeds 50150–50199)** before final deployment."*

As demonstrated in [`DEVELOPMENT_GATE_0_2_HOLDOUT_PROVENANCE.md`](file:///c:/Users/Sundareswaran/Kagriculture/DEVELOPMENT_GATE_0_2_HOLDOUT_PROVENANCE.md), this statement is **factually false**:
- Seeds 50155 and 50161 were evaluated for strategy selection in `scratch/test_phase16_generalization.py`.
- Seed 50186 was evaluated in live tournament match 107564294.
- All 50 seeds were simulated in `scratch/census_phase3_500seeds.py`.

The baseline catalog cannot claim that Seeds 50150–50199 are virgin.

---

## 6. Information Horizon & Post-Match Hindsight in Baseline Scripts

We audited `scratch/run_margin_scan.py` to ensure that baseline margin generation did not inadvertently leak future state to the playing agents:
1. **Simulation Loop Isolation**:
   ```python
   while not g.done:
       obs_v2 = g.observe(v2_seat)
       obs_dm = g.observe(dm_seat)
       act_v2 = v2_agent.act(obs_v2)
       act_dm = dmitrii_fn(obs_dm)
       g.step(acts[0], acts[1])
   ```
   Neither `v2_agent` nor `dmitrii_fn` is passed future steps or simulator references by `run_margin_scan.py`.
2. **Post-Match Regime Tagging**:
   At lines 50–71 of `run_margin_scan.py`, after the match concludes, `obs_final = g.observe(0)` is inspected to classify the match into `Pizza`, `Pizza+Straw`, or `Straw`.
   As noted in Correction `CORR-0.1-08`, this classification is post-match hindsight and contained a typo (`"YARN_SHOP"` instead of `"YARN_STORE"`). This affects only analyst grouping, not agent policy decisions during the match.

---

## 7. Required Baseline Catalog Corrections

Before Gate 0.2 can clear:
1. **Correct Dmitrii Source Path**: Modify `DEVELOPMENT_BASELINE_MAP.md:27` to replace `extracted_agents/dmitrii_lb2800/agent.py` with `extracted_agents/dmitrii_lb2800/main.py`.
2. **Replace Contaminated Holdout Designation**: Update `DEVELOPMENT_BASELINE_MAP.md:111` to remove references to Seeds 50150–50199 as a virgin holdout, and replace with a certified virgin partition (e.g. Seeds 60000–60049).

---

## 8. Gate Decision Impact

While the mathematical metrics and simulator execution are sound, the catalog contains a broken agent source path and an invalid virgin holdout designation.

**VERDICT: DEFECTS IDENTIFIED — GATE 0.2 BLOCKED**
