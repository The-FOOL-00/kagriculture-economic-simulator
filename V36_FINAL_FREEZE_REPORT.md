# V36 Final Freeze Audit & Competitive Validation Report

**Phase:** PHASE 11 — FINAL FREEZE VERIFICATION  
**Candidate Name:** `V35_A7_OPENING`  
**Candidate Path:** `candidates/v35_a7_opening/main.py`  
**Execution Standard:** Zero Tolerance, Cleanroom Independent Harness, Ecosystem-Wide Validation  
**Final Competitive Decision:** **FREEZE_V35**  

---

## 1. Candidate Code Path & Architecture

* **Candidate File Path:** [`candidates/v35_a7_opening/main.py`](file:///c:/Users/Sundareswaran/Kagriculture/candidates/v35_a7_opening/main.py)
* **Underlying Engine:** Pure Python stdlib wrapper over untouched incumbent `candidates/v30_a7_standalone/main.py`.
* **Mechanism:**
  * At Step 0: Substitutes `[["BUY_PRODUCT", "WHEAT", 25], ["SELL", "WHEAT", 25]]` (25/25 wash) for A7's 30/30 wash.
  * Conserves critical Day 1 working capital ($5 \times 25 - 5 \times 10 = \$75$ gross float difference; prevents early order bouncing and cash starvation).
  * At Steps 1..718: Delegates 100% bit-identically to frozen A7 (`self.a7_agent.act(observation, configuration)`).
  * Fail-closed: Catches any exception and falls back immediately to base A7.

---

## 2. Exact Cryptographic SHA-256 Hashes

| Component / Artifact | File Path | Verified SHA-256 Digest | Status |
|:---|:---|:---|:---:|
| **Incumbent A7 Standalone** | `candidates/v30_a7_standalone/main.py` | `51c1d25245f68dd8de66b355f2ad6ca1d79de8af02efed521a5a82f7be69ce3f` | **UNMODIFIED** (Exact Match) |
| **Portfolio Champion V22R1** | `submission_aec_v22r1.tar.gz` | `6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5` | **UNMODIFIED** (Exact Match) |
| **Promoted Candidate V35** | `candidates/v35_a7_opening/main.py` | `1959021bdb1aeff720732aec866f5c9f3c9fa0b259ee0ab25982bda367593249` | **FROZEN** |

---

## 3. Primary Benchmark Reconstruction (Phase 1 & Phase 2)

Recomputed directly from all 240 terminal match logs in `benchmark_results.json`:

* **Matches Evaluated:** 120 paired matches (10 seeds $\times$ 6 opponents $\times$ 2 seats)
* **A7 Incumbent Benchmark:**
  * Pure Decisive Wins: 100
  * Pure Ties: 16
  * Pure Losses: 4
  * Tournament Points: **108.0 / 120 (90.00%)**
* **V35 Candidate Benchmark:**
  * Pure Decisive Wins: 117
  * Pure Ties: 0
  * Pure Losses: 3
  * Tournament Points: **117.0 / 120 (97.50%)**
* **Tournament Win Rate Delta:** **+7.50 percentage points (+9.0 tournament points)**
* **Rescued Non-Wins:** **17** (16 mirror ties $\to$ wins, 1 mirror loss $\to$ win)
* **Casualties (A7 Win $\to$ V35 Non-Win):** **EXACTLY 0**
* **Worst Paired Cash Delta:** **+$0.00** (Zero matches with lower cash than A7)
* **Mean Paired Cash Delta:** **+$60.19** (Median: **+$4.00**, Max: **+$3,339.00**)

---

## 4. Fresh Independent Cleanroom Benchmark (Phase 8)

Executed via `scripts/v36_independent_validation.py` without importing prior verdicts:

* **Matches Run:** 240 fresh matches in cleanroom environments
* **Independent A7 Win Rate:** 90.00% (108.0 / 120)
* **Independent V35 Win Rate:** 97.50% (117.0 / 120)
* **Independent Rescues:** 17
* **Independent Casualties:** 0
* **Independent Worst Paired Delta:** **+$0.00**
* **Independent Gate Verdicts:**
  * G1 (Superiority): **PASS**
  * G2 (Zero Casualties): **PASS**
  * G3 (Positive Rescues): **PASS**
  * G4 (Bounded Tail Risk): **PASS**
  * G5 (Both Seats Robust): **PASS** (Seat 0: 96.7%, Seat 1: 98.3%)
  * G6 (No Opponent Degradation): **PASS**
  * G7 (Bootstrap CI Positive): **PASS** (`[+4.17 pp, +11.25 pp]`)
* **Independent Verdict:** **FREEZE_V35**

---

## 5. Rescue & Casualty Transition Matrix

| A7 Baseline Outcome | V35 Candidate Outcome | Match Count | Classification | Strategic Detail |
|:---|:---|:---:|:---|:---|
| **WIN** | **WIN** | 100 | Preserved Win | 100% win retention; fee savings (+$0 to +$4 delta). |
| **TIE** | **WIN** | 16 | **Rescued Mirror Tie** | Step-0 symmetry broken vs `E2_A7` (+$17 delta). |
| **LOSS** | **WIN** | 1 | **Rescued Mirror Loss** | Seed 249681 vs `E2_A7` Seat 0 (+$3,338 delta). |
| **LOSS** | **LOSS** | 3 | Preserved Loss | Structural deficits vs `E8_DMITRII` (2) & `E2_A7` (1); deficit narrowed by +$4 to +$17. |
| **WIN** | **TIE** | **0** | **Casualty** | **None** |
| **WIN** | **LOSS** | **0** | **Casualty** | **None** |
| **TIE** | **LOSS** | **0** | **Casualty** | **None** |

---

## 6. Opening-Wash Response Curve & Safe Plateau (Phase 4)

Evaluated across 1,320 tournament matches ($W/W$ for $W \in [20, 30]$):

| Wash ($W/W$) | Win Rate | Rescues | Casualties | Mean Delta | Worst Paired Delta | Operational Regime |
|:---:|:---:|:---:|:---:|---:|---:|:---|
| 20/20 | 100.00% | 20 | 0 | +$61.41 | -$36,976.00 | **Severe Tail Risk Cliff** |
| 21/21 | 100.00% | 20 | 0 | +$61.74 | -$36,975.00 | **Severe Tail Risk Cliff** |
| 22/22 | 100.00% | 20 | 0 | +$60.41 | -$36,979.00 | **Severe Tail Risk Cliff** |
| 23/23 | 99.17% | 19 | 0 | +$109.93 | -$27,561.00 | **Severe Tail Risk Cliff** |
| 24/24 | 99.17% | 19 | 0 | +$108.60 | -$27,561.00 | **Severe Tail Risk Cliff** |
| **25/25** | **97.50%** | **17** | **0** | **+$60.19** | **+$0.00** | **SAFE PLATEAU (Optimal Operational Setpoint)** |
| **26/26** | **97.50%** | **17** | **0** | **+$58.69** | **+$0.00** | **SAFE PLATEAU** |
| **27/27** | **97.50%** | **17** | **0** | **+$59.19** | **+$0.00** | **SAFE PLATEAU** |
| **28/28** | **97.50%** | **17** | **0** | **+$57.69** | **+$0.00** | **SAFE PLATEAU** |
| **29/29** | **97.50%** | **17** | **0** | **+$57.52** | **+$0.00** | **SAFE PLATEAU** |
| 30/30 | 90.00% | 0 | 0 | +$0.00 | +$0.00 | Incumbent A7 Baseline (Mirror Lock) |

* **Empirical Confirmation:** The safe plateau spans $W \in [25, 29]$. $W=25$ sits securely on this zero-downside plateau and delivers the highest capital efficiency.

---

## 7. Broader Opponent Ecosystem Tournament (Phase 6)

Evaluated across 240 matches covering all 12 distinct opponent architectures in the repository:

| Opponent Implementation | Architectural Class | In 120-Leg BM? | A7 Win Rate | V35 Win Rate | Casualties | Rescues | Mean Delta | Worst Delta |
|:---|:---|:---:|:---:|:---:|:---:|:---:|---:|---:|
| `E0_V3` | Frozen Parent Base | YES | 100.0% | **100.0%** | **0** | 0 | +$4.00 | +$4.00 |
| `E1_V22R1` | Portfolio Champion | YES | 100.0% | **100.0%** | **0** | 0 | +$4.00 | +$4.00 |
| `E2_A7` | Mirror Incumbent | YES | 50.0% | **90.0%** | **0** | 8 | +$17.00 | +$17.00 |
| `E3_V25P3` | Older Route Family | **NO** | 100.0% | **100.0%** | **0** | 0 | +$17.00 | +$17.00 |
| `E4_A1` | Zero-Wash Ablation | **NO** | 100.0% | **100.0%** | **0** | 0 | +$4.00 | +$4.00 |
| `E5_A2` | 10/10 Small Wash | **NO** | 100.0% | **100.0%** | **0** | 0 | +$4.00 | +$4.00 |
| `E6_W72` | Step-72 Delayed Wash | **NO** | 10.0% | **10.0%** | **0** | 0 | +$1.00 | +$1.00 |
| `E7_W2015` | Asymmetric 20/15 Wash | **NO** | 10.0% | **10.0%** | **0** | 0 | +$9.00 | +$9.00 |
| `E8_DMITRII` | Frontier LB 2800+ | YES | 80.0% | **80.0%** | **0** | 0 | +$4.00 | +$4.00 |
| `V54` | Declarative Chassis | YES | 100.0% | **100.0%** | **0** | 0 | +$0.00 | +$0.00 |
| `SYN_AGG` | Hostile Market Dumper | YES | 100.0% | **100.0%** | **0** | 0 | +$0.00 | +$0.00 |
| `PASSIVE` | Passive Dummy | **NO** | 100.0% | **100.0%** | **0** | 0 | +$0.00 | +$0.00 |

* **Zero Casualties Across Entire Ecosystem:** In all 12 opponent families, V35 achieves zero casualties and non-negative cash deltas ($\ge +\$0.00$).

---

## 8. Leakage & Benchmark Contamination Audit (Phase 7)

* **Observable State at Step 0:** V35 inspects strictly `observation.get("step", 0)`.
* **Zero Seed Conditioning:** V35 never accesses `observation["seed"]` or `configuration["seed"]`.
* **Zero Opponent Conditioning:** V35 contains no opponent classifiers, identity checks, or heuristics.
* **Zero Learned Weights:** V35 contains 0 neural network weights, 0 regression arrays, and 0 label datasets.
* **State Isolation:** `_CONTROLLER.reset()` executes whenever `step <= 0`, guaranteeing bit-identical determinism and zero inter-episode memory leakage.

---

## 9. Rigorous Statistical Inference (Phase 9)

* **Sample Size ($N$):** 120 paired tournament matches
* **Bootstrap Resamples ($B$):** 10,000 resamples
* **Tournament Win Rate Delta ($\Delta WR$):** **+7.50 percentage points**
  * 95% Paired Bootstrap CI: **[+4.17 pp, +11.25 pp]** (strictly positive)
* **Decisive Win Rate Delta:** **+14.17 percentage points**
  * 95% Paired Bootstrap CI: **[+8.33 pp, +20.83 pp]**
* **Discordant Pair Analysis:**
  * Casualties ($b$): 0
  * Rescues ($c$): 17
* **McNemar Exact Binomial Test ($n=17, k=0, p=0.5$):**
  $$p = 1.526 \times 10^{-5}$$
  Statistically significant outperformance at $p < 0.00002$.

---

## 10. Runtime & Latency Benchmarks

* **Kaggle Latency Limit:** 1,000.0 ms per step
* **Observed V35 Step-0 Latency:** **0.026 ms**
* **Observed V35 Subsequent Step Latency:** **0.022 ms**
* **Safety Margin:** 38,000x within allowable per-step execution budget.
* **Full Match Execution Time:** ~0.35s per 720-step episode.

---

## 11. Test Suite Verification

* **Pytest Suite:** `tests/test_v35*.py`
* **Test Count:** 29 passed in 4.38s (0 failures, 0 warnings, 0 skipped).
* **Coverage:** Includes determinism, fail-closed safety, liquidity bounds, leakage quarantine, physical invariance, latency, and terminal state preservation.

---

## 12. Protected Holdout Integrity

* **Quarantine Verification:** None of the protected virgin holdouts were accessed or imported:
  * `214200–214249` (GATE0 virgin holdout): **UNTOUCHED**
  * `340090–340199` (Protected holdout remainder): **UNTOUCHED**
  * `249695–249734` (V32_CONFIRM holdout): **UNTOUCHED**
* **Quarantine Status:** 100% compliant with governance protocol.

---

## 13. Final Competitive Decision

$$\mathbf{DECISION: \quad FREEZE\_V35}$$

### Rationale:
1. Every preregistered promotion gate is satisfied with 0 casualties, non-negative worst delta ($0.00), and +7.50 pp tournament win rate improvement.
2. The independent cleanroom validation harness reproduced all findings from scratch.
3. Broader opponent validation proved universal safety across 12 distinct opponent families with zero casualties.
4. The opening wash sweep confirmed that 25/25 sits firmly on an invariant safe plateau ($25 \le W \le 29$).
5. No complexity or machine-learned components were added; the candidate preserves 100% downstream fidelity to A7.

V35 is formally **FROZEN** as the production competition candidate.
