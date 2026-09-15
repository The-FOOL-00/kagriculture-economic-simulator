# Championship Deployment — Final Two-Agent Deployment Report

**Document ID**: `research/final_two_agent_deployment.md`  
**Protocol**: Championship Deployment — Compile, Verify, Then Submit Exactly Two Agents  
**Date**: 2026-09-10  
**Target Competition**: Kaggle `kaggriculture` (Featured, $50,000 USD)  
**User / Team**: `thefool00` (Team `Eldritch`)  
**Final Deployment Status**: **`DEPLOYED — BOTH COMPILED AGENTS ACTIVE`**  

---

## 1. Source Freeze

Before initiating compilation, the cryptographic integrity of the approved research source candidates was re-verified against frozen hashes:

| Agent Identifier | Source File Path | Frozen Reference SHA256 | Recomputed Pre-Compile SHA256 | Status |
| :--- | :--- | :--- | :--- | :---: |
| **V54++ Control** | `candidates/v54_plus_shop.py` | `592f0ba31b3b20b5a3aad409a753b5e6bdeb29a9eb2381342b1cd527509fa9e8` | `592f0ba31b3b20b5a3aad409a753b5e6bdeb29a9eb2381342b1cd527509fa9e8` | **PASS** |
| **V54++ Residual** | `candidates/v54_plus_residual.py` | `5b2d5080ba38287812d137a21c7b09071e1f66a10c32d7c3ec4bb61be4520e80` | `5b2d5080ba38287812d137a21c7b09071e1f66a10c32d7c3ec4bb61be4520e80` | **PASS** |

Neither file was modified, overwritten, or tuned.

---

## 2. Dependency Graph

The runtime dependency analysis ([`research/deployment_dependency_graph.md`](file:///c:/Users/Sundareswaran/Kagriculture/research/deployment_dependency_graph.md)) established that:
- The base hybrid execution engine (`_V51_BASE_SOURCE`) defines the `v49.residual_controller` and `v50.hybrid` execution namespaces.
- The 719-step macro route tables (`_V56_BACKBONE_ROUTE`, `_V56_YARN_ROUTE`, `_V58_BAKERY_YARN_ROUTE`) are static data structures.
- Tactical overlays (`_v60_seed_trim`, `_v60_shed_guard`, `_v56_visible_configuration`) originate from `candidate_v62_composite_bakery_yarn.py`.
- Terminal realization overlays (`_route_loaded_units`, `_TERMINAL_UNITS`, `_TERMINAL_MARKET`) originate from `candidate_v66_meta_closed_loop.py`.
- The S2 Shop Controller (`_select_route`) is a pure public observation state machine.

All dependencies were unified into self-contained single-file artifacts, completely eliminating reliance on `__file__`, `external_repos/`, or runtime filesystem reads.

---

## 3. Compilation Method

Compilation was executed by [`scratch/compile_v54_championship.py`](file:///c:/Users/Sundareswaran/Kagriculture/scratch/compile_v54_championship.py) (SHA256: `9214e6dd37865414ada385782d6638b28baada08ef31997550887752cf8dd10b`):
1. **Base Inlining**: Extracted the full standalone V51/V62 base engine, routes, and tactical overlays up to line 4324 of `candidate_v62_composite_bakery_yarn.py`.
2. **Terminal Inlining**: Inlined the V66 terminal realization routines (`_align`, `_route_loaded_units`, `_TERMINAL_UNITS`, `_TERMINAL_MARKET`).
3. **Policy & Configuration Assembly**:
   - For Control: Instantiated `_CONFIG = copy.deepcopy(_V54_CONFIG)`.
   - For Residual: Instantiated `_CONFIG = _V51ResidualConfig(**_CONFIG_DICT)` with preemption overrides `preempt_money_deficit = 2000.0`, `preempt_minimum_delta = 4.0`, `preempt_maximum_batch = 12`.
4. **Header & Compatibility**: Added explicit standard-library imports (`__future__`, `copy`, `typing`) and top-level `agent(obs, configuration)` / `kaggle_agent` entrypoints.

---

## 4. Semantic Equivalence

Full audit documented in [`research/compiled_semantic_equivalence.md`](file:///c:/Users/Sundareswaran/Kagriculture/research/compiled_semantic_equivalence.md):
- **Routes**: `_V56_BACKBONE_ROUTE`, `_V56_YARN_ROUTE`, and `_V58_BAKERY_YARN_ROUTE` are 100% item-by-item identical.
- **Config**: Control configuration matches original `_V54_CONFIG` 100%. Residual configuration matches original residual `_CONFIG` 100%.
- **Shop Selection**: Evaluated across 10 distinct step/shop permutations; produced 100% identical branch selections.
- **Diff between Compiled Control & Residual**: Contains strictly and exclusively the preemption parameter adjustments.

---

## 5. Turn-by-Turn Equivalence

Evaluated by [`scratch/verify_behavioral_equivalence_50seeds.py`](file:///c:/Users/Sundareswaran/Kagriculture/scratch/verify_behavioral_equivalence_50seeds.py) across **50 fresh unobserved seeds (960,001–960,050)** for both candidates (100 episodes total):
- **Farmer Actions**: 100% identical on every single turn ($72,000 / 72,000$ turns).
- **Hand Actions**: 100% identical on every single turn ($72,000 / 72,000$ turns).
- **Market Orders**: 100% identical on every single turn ($72,000 / 72,000$ turns).
- **Final Rewards**: Identical to the exact penny ($r_\text{orig} == r_\text{comp}$) on all 50 seeds.
- **Mismatches**: **0 mismatches recorded** in [`research/compiled_behavior_mismatches.csv`](file:///c:/Users/Sundareswaran/Kagriculture/research/compiled_behavior_mismatches.csv).

---

## 6. Isolated Kaggle Execution

Evaluated by [`scratch/verify_isolated_and_determinism.py`](file:///c:/Users/Sundareswaran/Kagriculture/scratch/verify_isolated_and_determinism.py):
- Created isolated temporary execution containers containing strictly `main.py`.
- Removed all repository roots and `external_repos/` from `sys.path`.
- Executed via raw Kaggle environment runner: `env.run(["main.py", "starter"])`.
- Tested across 5 fresh seeds (970,001–970,005):
  - Completed 720 turns with status `DONE`.
  - Zero exceptions, zero missing module errors, zero `__file__` errors.
  - Active first actions and standard economic scaling ($r \in [\$119,592, \$200,580]$).

---

## 7. Determinism

Evaluated across 10 repeated seeds (970,010–970,019):
- Both compiled agents executed each seed twice.
- Turn-by-turn action telemetry was hashed with SHA256.
- 10/10 seeds yielded identical turn-by-turn telemetry hashes and identical final rewards ($h_1 == h_2, r_1 == r_2$).

---

## 8. Compiled Hashes

| Target Agent | Deployed File | Deployed SHA256 Checksum |
| :--- | :--- | :--- |
| **Submission 1 (Control)** | `candidates/compiled_v54_plus_shop.py` | `f651ccd220e701968bc33579812d8917da63f5b0582f2fd0d363fa6a16ffd8b8` |
| **Submission 2 (Residual)** | `candidates/compiled_v54_plus_residual.py` | `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb` |

Recorded in [`research/compiled_deployment_manifest.md`](file:///c:/Users/Sundareswaran/Kagriculture/research/compiled_deployment_manifest.md).

---

## 9. Current Kaggle State

- **Competition**: `kaggriculture` (Featured, $50,000 USD)
- **Deadline**: 2026-09-30 23:59:00 UTC
- **User / Team**: `thefool00` (Team `Eldritch`)
- **Daily Submissions Consumed**: 2 of 5 (3 remaining today)

---

## 10. Submission 1 (Control Baseline)

- **Agent Name**: V54++ Control Standalone
- **Submission Ref ID**: `56146947`
- **File**: `compiled_v54_plus_shop.py`
- **Timestamp (UTC)**: `2026-09-10 15:13:16.067000`
- **Validation Status**: `SubmissionStatus.COMPLETE`
- **Initial Rating / Score**: `600.0`
- **Error Description**: None

---

## 11. Submission 2 (Validated Improvement)

- **Agent Name**: V54++ Residual Standalone
- **Submission Ref ID**: `56146971`
- **File**: `compiled_v54_plus_residual.py`
- **Timestamp (UTC)**: `2026-09-10 15:14:36.043000`
- **Validation Status**: `SubmissionStatus.COMPLETE`
- **Initial Rating / Score**: `600.0`
- **Error Description**: None

---

## 12. Active Slot Verification

Confirmed via fresh Kaggle API query:

```
Ref: 56146971 | File: compiled_v54_plus_residual.py  | Status: SubmissionStatus.COMPLETE | Score: 600.0 | Date: 2026-09-10 15:14:36 UTC
Ref: 56146947 | File: compiled_v54_plus_shop.py      | Status: SubmissionStatus.COMPLETE | Score: 600.0 | Date: 2026-09-10 15:13:16 UTC
Ref: 56099752 | File: compiled_research_b_only_v2.py | Status: SubmissionStatus.COMPLETE | Score: 727.0 | Date: 2026-09-08 13:53:27 UTC (RETIRED)
Ref: 55958978 | File: submission_slot2_aethel_refined_v2.tar.gz | Status: COMPLETE       | Score: 869.1 | Date: 2026-09-02 09:41:40 UTC (RETIRED)
```

- **Active Slot 1 (Newest / Experimental)**: `compiled_v54_plus_residual.py` (Ref `56146971`) — **ACTIVE**
- **Active Slot 2 (Control / Baseline)**: `compiled_v54_plus_shop.py` (Ref `56146947`) — **ACTIVE**
- Old submissions (`compiled_research_b_only_v2.py` and `submission_slot2_aethel_refined_v2.tar.gz`) have been retired into inactive history.
- Exactly the two intended championship agents occupy the two active ladder slots.

---

## 13. Final Status

### **DEPLOYED — BOTH COMPILED AGENTS ACTIVE**

*Under Phase 19 Anti-Chasing Invariants: Zero rerolls, zero third-bot submissions, zero tuning on initial matches. Live monitoring proceeds under [`research/live_monitoring_protocol.md`](file:///c:/Users/Sundareswaran/Kagriculture/research/live_monitoring_protocol.md).*
