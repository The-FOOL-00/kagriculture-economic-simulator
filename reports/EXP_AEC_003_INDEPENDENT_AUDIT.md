# EXP-AEC-003 — Comprehensive Independent Post-Execution Forensic Audit

**Experiment Identifier:** `EXP-AEC-003`  
**Protocol:** `PREREG-EXP-AEC-003-20260917-FINAL`  
**Cohort Range:** Seeds `340250–340299` ($N=50$, 100 matches, 71,900 turns)  
**Baseline Backbone:** Frozen V3 (`submission_Vj_kc_v3.tar.gz`, SHA-256: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`)  
**Audit Protocol Commit:** `0a5efe03fe610bca9083cffd64658d31bf3c5536`  
**Auditor:** Independent Scientific Audit Agent  
**Audit Completion Date:** 2026-09-17  

---

## 1. Current Claimed Result vs. Audit Validation

The claimed prospective results for EXP-AEC-003 were audited directly against raw execution records:

| Evaluation Metric | Claimed by EXP-AEC-003 | Independently Audited Value | Status |
|---|---|---|---|
| **Cohort Seeds** | 340250–340299 ($N=50$) | **340250–340299 ($N=50$)** | **VERIFIED** |
| **Completed Matches** | 100 | **100** | **VERIFIED** |
| **Mean Paired Margin Delta** | +$57.36 | **+$57.3600** | **VERIFIED** |
| **Standard Deviation ($s$, ddof=1)** | $144.22 | **$144.2183** | **VERIFIED** |
| **Standard Error ($SE$)** | $20.40 | **$20.3956** | **VERIFIED** |
| **One-Sided Paired $t$-Test** | $t = 2.8124, p = 0.003527$ | **$t = 2.812378, p = 0.00352747$** | **VERIFIED** |
| **Directional Lower 95% Bound** | +$23.17 | **+$23.1658** | **VERIFIED** |
| **Two-Sided 95% Student-$t$ CI** | [+$16.37, +$98.35] | **[+$16.3736, +$98.3464]** | **VERIFIED** |
| **Median Paired Margin Delta** | +$18.50 | **+$18.5000** | **VERIFIED** |
| **5th Percentile ($P_{05}$)** | -$19.65 | **-$19.6500** | **VERIFIED** |
| **Minimum Margin Delta** | -$25.00 | **-$25.0000** (Seed 340250) | **VERIFIED** |
| **Maximum Margin Delta** | +$948.00 | **+$948.0000** (Seed 340296) | **VERIFIED** |
| **Tournament Win-Rate Delta** | +56.00 pp | **+56.00 pp** (Treat 75%, Ctrl 19%, Tie 6%) | **VERIFIED** |
| **Ties-Excluded Win Rate** | 79.79% | **79.79%** (75 / 94) | **VERIFIED** |
| **Total Committed Patches** | 140 | **140** | **VERIFIED** |
| **Active Seeds with Commits** | 45 / 50 | **45 / 50** | **VERIFIED** |
| **Safety Violations** | 0 | **0** | **VERIFIED** |
| **Quarantined Mechanism Commits** | 0 | **0** | **VERIFIED** |
| **Counterfactual Fidelity Adherence** | 100% VERIFIED | **100% VERIFIED (140/140)** | **VERIFIED** |
| **Holdout Seeds Touched (340050–340199)**| 0 | **0** | **VERIFIED** |

---

## 2. First Priority — Execution Purity Forensics

A forensic review of process trajectory logs, execution timestamps, and filesystem transitions reveals the exact truth regarding the recorded dual launch sequence:

### Chronological Reconstruction
1. **Initial Launch (Attempt 1)**: Initiated at `15:14:41.053 UTC` via `python experiments/EXP-AEC-003/run_experiment.py --execute-experiment`.
2. **Synchronous Crash (761 milliseconds)**: At step 433 of match 1 (`EXP-AEC-003_340250_A`), the runner attempted to log `committed_cand.counterfactual_fidelity`. Because `CandidateTelemetry` in `aec/integration/executor.py` does not store `counterfactual_fidelity` directly (it is certified on `SafetyCertificate` in `treat_agent.executor._certificates`), Python raised `AttributeError` and terminated with `Exit Code 1` at `15:14:43.814 UTC`.
3. **Purity Verification**:
   - Zero matches were completed. Zero seeds were completed.
   - Zero checkpoint data or raw results were committed.
   - The process exited synchronously. Zero Python processes or tasks remained alive.
4. **Environment Wipe & Manifest Restoration**:
   - The 5 header-only/partial files (`COMMITTED_PATCHES.csv`, `CONFIG.json`, `EXECUTION_LOG.txt`, `PAIRED_DELTAS.csv`, `TELEMETRY_EVENTS.csv`) were purged via `Remove-Item`.
   - `EXECUTION_MANIFEST.json` was restored from HEAD commit `0a5efe0` back to `FROZEN_NOT_LAUNCHED`.
   - `run_experiment.py` was corrected at lines 374–379 to inspect `SafetyCertificate`.
   - Preflight verification was run cleanly and passed.
5. **Clean Second Launch (Attempt 2 - Production Run)**:
   - Launched at `15:16:11.741 UTC` and completed at `15:18:36.349 UTC` (144.61 seconds).
   - Started from a completely clean state with no state inherited from Attempt 1.
   - All 50 seeds (100 matches) were executed by **Runner Version B**.

### Definitive Answers to Items A through K
- **A. Was the first execution actually started?** Yes.
- **B. Did it execute any prospective matches?** No. Crashed during turn 433 of match 1 before completion.
- **C. Was it still running when the runner was edited?** No. Exited with code 1 at 15:14:43, 56 seconds before line 374 was edited.
- **D. Was any Python process alive between launches?** No. Terminated synchronously; no background tasks remained.
- **E. Were any seeds/matches completed before the second launch?** No.
- **F. Were any files produced by attempt 1 NOT deleted?** No. All 5 partial files were purged.
- **G. Did the second launch start from a genuinely clean state?** Yes.
- **H. Could attempt 2 have inherited prior state?** No. Zero checkpoint or raw results existed.
- **I. Were any seeds executed twice?** No. All 50 seeds executed once each in attempt 2.
- **J. Were any matches executed twice?** No. All 100 matches completed exactly once in attempt 2.
- **K. Was there any mixing of runner versions?** No. All 100 matches in `RAW_RESULTS.json` were executed exclusively by Runner Version B.

---

## 3. Runner Immutability Audit

| Timeline Phase | Start Timestamp | SHA-256 Hash | Matches Executed | Notes |
|---|---|---|---|---|
| **Runner Version A** | `15:14:15 UTC` | `bd84e39440cbc68997000b528fe4d6ce2595ed4820e923caf032de8293e75d5e` | 0 | Crashed at 0.76s on match 1 (AttributeError) |
| **Runner Version B** | `15:15:39 UTC` | `9463d9bbc4c4357ed06793f911bea71d0697f68c6c15229db3e13cf758361cab` | 100 | Executed all 50 seeds (100 matches) to completion |

**Diff Verification:** The diff between Version A and Version B consists solely of 7 lines replacing `committed_cand.counterfactual_fidelity` with `committed_cert.counterfactual_fidelity`. Zero algorithmic, heuristic, simulator, or agent rules were modified.

---

## 4. Clean-Start Audit

Every execution artifact was audited for provenance:
- `RAW_RESULTS.json`: Began empty; populated incrementally seed-by-seed from 340250 to 340299.
- `CHECKPOINT.json`: Began non-existent; atomically written after each completed seed.
- `COMMITTED_PATCHES.csv`: Created fresh at 15:16:11; recorded exactly 140 rows.
- `TELEMETRY_EVENTS.csv`: Created fresh at 15:16:11; recorded 70,800 event steps.
- `PAIRED_DELTAS.csv`: Created fresh at 15:16:11; recorded exactly 50 seed deltas.
- `EXECUTION_LOG.txt`: Clean log beginning at `15:16:11.699 UTC`.
- `EXECUTION_MANIFEST.json`: Verified restored to `FROZEN_NOT_LAUNCHED` before launch, updated to `COMPLETED` at 15:18:37 UTC.

---

## 5. Match Completeness & CRN Mirror Symmetry

- **Cohort Boundaries:** Exactly 50 seeds (`340250` to `340299`).
- **Match Structure:** Exactly 2 matches per seed (Total = 100).
- **Seat Allocation:**
  - `Match_A`: Treatment Seat 0, Control Seat 1 (50 matches)
  - `Match_B`: Treatment Seat 1, Control Seat 0 (50 matches)
- **Anomalies:** 0 duplicates, 0 missing matches, 0 unexpected seeds.
- **Seat Symmetry:** In 44 of 50 seeds, margins are identical across seats. In the 6 asymmetric seeds (e.g. Seed 340292, Match A margin -$12,235, Match B margin +$12,199), the CRN mirror swap completely balances the structural map advantage, isolating the true paired delta ($\Delta = -\$18.00$).

---

## 6. Raw Result Reconstruction

Primary analysis was recalculated directly from raw step logs and game rewards:
- Mean: **+$57.3600**
- Sample Std: **$144.2183**
- Standard Error: **$20.3956**
- One-sided $t$-statistic: **$t = 2.812378$**
- One-sided $p$-value: **$p = 0.00352747$**
- Directional Lower 95% Bound: **+$23.1658**
- Two-Sided 95% CI: **[+$16.3736, +$98.3464]**
- Median: **+$18.5000**
- 5th Percentile: **-$19.6500**

All calculations match `SUMMARY.json` to 100% precision.

---

## 7. Win-Rate Reconstruction

From raw game results across 100 matches:
- **Treatment Wins:** 75 (75.0%)
- **Control Wins:** 19 (19.0%)
- **Ties:** 6 (6.0%)
- **Tournament Win-Rate Delta:** $+56.00$ percentage points
- **Ties-Excluded Win Rate:** $75 / 94 = 79.79\%$ (Delta: $+59.57$ pp)

---

## 8. Commit Ledger Forensics (140 Commits)

Audit of all 140 committed patches (`reports/EXP_AEC_003_COMMIT_FORENSICS.csv`):
- **Mechanism:** Exactly **140/140 (100%)** are `DEPENDENCY_AWARE_MARKET_TIMING`.
- **Action Mutations:**
  - Farmer action modifications: **0**
  - Worker action modifications: **0**
  - Market orders added or removed: **0**
  - Market orders reordered (multiset permutation): **140 (100%)**
- **Turn Distribution:**
  - Turn 361: 2 commits (1 seed $\times$ 2 matches)
  - Turn 433: 30 commits (15 seeds $\times$ 2 matches)
  - Turn 529: 2 commits (1 seed $\times$ 2 matches)
  - Turn 554: 8 commits (4 seeds $\times$ 2 matches)
  - Turn 577: 8 commits (4 seeds $\times$ 2 matches)
  - Turn 649: 90 commits (45 seeds $\times$ 2 matches)
- **Causal Nature:** On turns with multiple market orders, promoting uncoupled `SELL` orders ahead of capital expenditures (`HIRE`) or coupled same-asset trades eliminates sequential cash starvations and locks in peak pre-impact market prices.

---

## 9. Legacy Frontload Audit

- Search of the executed code path confirms that `FRONTLOAD_ORDERS` is marked `ScientificStatus.FALSIFIED` in `aec/config.py` and placed in `QUARANTINED_MECHANISMS`.
- No opportunity analyzer generates `FRONTLOAD_ORDERS` opportunities.
- In `run_experiment.py` (lines 356–360), an explicit fail-closed assertion aborts the run if `FRONTLOAD_ORDERS` is committed.
- Exactly **0 commits** were attributable to `FRONTLOAD_ORDERS`.

---

## 10. Treatment Isolation Audit

A side-by-side comparison of `AECTreatmentAgent` and `FrozenV3ControlAgent` confirms:
- Both agents execute the identical frozen V3 backbone code (`submission_Vj_kc_v3.tar.gz`).
- Treatment baseline call count equals exactly 71,900 with 0 duplicate calls.
- Treatment received zero changes to horizons, phase shutdowns, terminal logic, or worker routes.
- The only active difference was the 140 intra-turn market timing reorderings.

---

## 11. Counterfactual Fidelity Audit

- All 140 committed patches adhered strictly to `COUNTERFACTUAL_FIDELITY = VERIFIED`.
- In 140 out of 140 commits, predicted `delta_money` from the forward simulator matched realized `delta_money` with **$0.00 error**.
- The simulator demonstrated 100% predictive accuracy for all executed market mutations.

---

## 12. Negative and Positive Tail Audit

- **Top Positive Tail:**
  - Seed 340296 ($\Delta = +948.00$): Match A (+948), Match B (+948). Commits on Turn 649 reordered inventory sales ahead of capex, securing cash that allowed optimal end-game positioning.
  - Seed 340256 ($\Delta = +294.00$): Commits on Turn 433 and Turn 649 ($+\$21$ money, $+\$48$ margin).
  - Seed 340264 ($\Delta = +228.00$): Commits on Turn 529 ($+\$93$ money) and Turn 649 ($+\$70$ money).
- **Bottom Negative Tail:**
  - Seed 340250 ($\Delta = -25.00$): Match A (-25), Match B (-25). Commits on Turn 433 and 649 gained money ($+\$16$), but control's subsequent random map dynamics achieved slightly higher final yield.
  - Seed 340283 ($\Delta = -21.00$): Match A (-21), Match B (-21).
  - Seed 340278 ($\Delta = -21.00$): Match A (+101), Match B (-143).
- Tails represent genuine game variance under deterministic rules; no outliers were trimmed.

---

## 13. Activation Frequency Audit (45/50 Seeds)

- Why did 45/50 seeds commit? In 45/50 seeds, the V3 macro cycle reaches Turn 649 with multiple market orders where uncoupled sales are placed behind coupled/capex orders.
- The opportunity condition is deterministic and generic (`len(orders) >= 2 and reordered != orders`).
- The activation rate reflects genuine market order structural flaws in the baseline V3 bot.

---

## 14. Repeated Commit Analysis

- Commits per active seed: Min 2, Max 6, Mean 3.11, Median 2.
- Commits per active match: Min 1, Max 3, Mean 1.56.
- Temporal Spacing: Minimum spacing is 23 turns; most common spacing is 216 turns. Zero back-to-back turn commits. Each commit operated on fresh live game state.

---

## 15. No-Leakage Audit

- Scan of the codebase confirms zero references to cohort seeds `340250–340299` or holdout seeds `340050–340199`.
- Zero turn-specific conditional logic or product-specific hacks exist.
- Experiment logic is 100% general and prospective.

---

## 16. Holdout Audit

- Scan of all EXP-AEC-003 files confirms:
  - `RAW_RESULTS.json`: 0 holdout seeds
  - `CHECKPOINT.json`: 0 holdout seeds
  - `PAIRED_DELTAS.csv`: 0 holdout seeds
  - `COMMITTED_PATCHES.csv`: 0 holdout seeds
  - `TELEMETRY_EVENTS.csv`: 0 holdout seeds
  - `EXECUTION_LOG.txt`: 0 holdout seeds
- **Holdout Execution Count = 0**.

---

## 17. Determinism Audit

Independent replay of completed matches from `run_experiment.py`:
- **Seed 340250**: Replay Margin = -$25.00 (Exact match)
- **Seed 340264**: Replay AEC Score = 86,528, V3 Score = 86,300, Margin = +$228.00, Commits = 2 (Exact bit-for-bit match)
- **Seed 340296**: Replay AEC Score = 101,407, V3 Score = 100,459, Margin = +$948.00, Commits = 1 (Exact bit-for-bit match)
- Determinism is verified at 100%.

---

## 18. Statistical Independence Audit

- The unit of inference is strictly the 50 paired seeds ($df = 49$).
- Common random numbers and seat-swap symmetry guarantee paired delta independence.
- $t$-test and $p$-value calculations follow exact textbook formulas.

---

## 19. Bootstrap / Wilcoxon Audit

- **Wilcoxon Signed-Rank Test:** $W = 132.0, p = 1.3481 \times 10^{-5}$ (reproduced).
- **BCa Bootstrap (10k resamples, seed 12345678):** [+$31.36, +$129.85] (reproduced).
- Non-parametric tests confirm that statistical significance is not an artifact of normality assumptions or outlier distortion.

---

## 20. Top-10 Interpretation Audit

- The result proves causal superiority against frozen V3 on this 50-seed prospective distribution.
- The result **does not guarantee top-10 leaderboard standing**, nor does it establish performance against foreign opponent architectures.

---

## 21. Architecture Audit

- **Validated:** Economic IR, ActionBasketDependencyGraph, DependencyAwareMarketTiming, CounterfactualSimulator (market), SafetyCertificate, AECExecutor.
- **Tested / Passive (0 Commits):** TerminalLiquidation, PhaseShutdown.
- **Quarantined / Falsified:** FrontloadOrders, LocalWeedDig, DynamicShadowHarvest, CargoFerryPriority, OpponentPreemptSell, EmergencyFeedPurchase, TerminalHarvestSweep.
- **Untested / Unimplemented:** TownCycleArbitrage, multi-agent coordination.

---

## 22. Critical Decision

```
================================================================================
FINAL VERDICT: [ B. VALID WITH QUALIFICATIONS ]
================================================================================
```
The result is scientifically valid and accepted as genuine empirical evidence for AEC market timing. Qualifications are formally registered regarding the runner execution restart, the passivity of defense mechanisms, and competitive generalization boundaries.

---

## 23. Required Deliverables Manifest

1. `reports/EXP_AEC_003_INDEPENDENT_AUDIT.md` (This document)
2. `reports/EXP_AEC_003_EXECUTION_RECONSTRUCTION.md`
3. `reports/EXP_AEC_003_COMMIT_FORENSICS.csv`
4. `reports/EXP_AEC_003_STATISTICAL_REPRODUCTION.md`
5. `reports/EXP_AEC_003_ARCHITECTURE_INTERPRETATION.md`
6. `reports/EXP_AEC_003_AUDIT_DECISION.md`

---

## 24. Git Governance Record

- **Current Repository HEAD:** `0a5efe03fe610bca9083cffd64658d31bf3c5536`
- **Frozen Protocol Commit:** `0a5efe03fe610bca9083cffd64658d31bf3c5536`
- **V3 Backbone Tarball SHA-256:** `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`
- **Raw Results SHA-256:** `565c69dfc863a6dc24cc5a8fc57d1d0e82312a6589f7dd3841e954ada2a5c555`
- **Paired Deltas SHA-256:** `302c2e0166e62d0fbc9cae6ace76644a6f99f82e0765b79f0178093c1ccb959f`
- **Summary JSON SHA-256:** `7ab6b9a6ca893d6c47cb9557f61677b96ebaa12ccc611fa005cf39811263023f`
- **Committed Patches SHA-256:** `3d02571f61ab6a8c30bca70ae067aa8f3fbc71d5987aa69ec8c10acf89192cd9`
- **Telemetry Events SHA-256:** `ef492cbce5d744c85718c7936b7866df61265220472ddeb4f94dbbe037cecc13`
- **Execution Log SHA-256:** `daa1a76deb90b6ece912cf8fcabc02a317f35100eceac42a00ed97bd89db609c`
- **Runner Version B SHA-256:** `9463d9bbc4c4357ed06793f911bea71d0697f68c6c15229db3e13cf758361cab`

---

## 25. Stop Rule Enforcement

In strict compliance with governance rules:
- No further code tuning or mechanism modifications will be made.
- No rerun of EXP-AEC-003 or execution of EXP-AEC-004 will be attempted.
- Holdout seeds `340050–340199` remain strictly locked.
- All actions halt here awaiting explicit user review.

---

## 26. Most Important Principle

A positive result is not scientifically accepted because it is large; it is accepted because:
1. The execution purity was forensically verified with zero data carry-over.
2. The treatment was strictly isolated to intra-turn market reordering.
3. The counterfactual simulator exhibited 100% predictive accuracy.
4. The statistics were independently reproduced bit-for-bit.
5. The holdout was 100% untouched.
6. The causal mechanism is sound, verified, and falsifiable.
