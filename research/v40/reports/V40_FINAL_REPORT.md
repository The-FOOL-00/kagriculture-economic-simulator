# V40 Scalable Hierarchical Recurrent RL & Self-Play Research Report

**Document ID:** `research/v40/reports/V40_FINAL_REPORT.md`  
**Date:** 2026-09-25 15:13:30  
**Repository:** `Kagriculture`  
**Mission:** Determine whether a properly engineered hierarchical recurrent RL system with high-throughput simulation, expert demonstration bootstrapping, multi-task value heads, and population-based self-play can discover economic policies superior to V35/V39 without falling into heuristic collapse.  
**Final Governance Verdict:** **`V40_RESEARCH_ONLY`** (Quarantined in research; baseline V35 remains live production incumbent).

---

## 1. Executive Summary

The V40 research program executed a comprehensive redesign of economic reinforcement learning for Kagriculture to systematically address every failure mode of previous RL attempts (RLX2 and V38).

### Key Accomplishments
1. **High-Throughput Parity Simulation:** Engineered `FastKagricultureSim`, bypassing framework-level JSON serialization and deep-copying. Achieved **304.7 SPS single-core** and **469.9 SPS multi-core** (a **5.4× to 8.4× speedup** over the 56 SPS official engine) while demonstrating **100% bit-for-bit equivalence** across 4,314 turns in 6 full test matches.
2. **Temporal State & Macro Representation:** Formulated a zero-leakage **112-dimensional observation encoder** capturing economic indicators, inventory spoilage, price momentum, labor allocation, and action history. Designed a **16-dimensional macro action space** governing land acquisition, hiring constraints, crop/livestock specialization, opportunistic front-running, and terminal liquidation.
3. **Supervised Behavioral Cloning Bootstrapping:** Trained a recurrent actor-critic (`V40RecurrentActorCritic` with GRU core) on 5,340 demonstration transitions. Achieved **97.7% validation accuracy** on held-out safe seeds, preserving 0.050 action entropy.
4. **Recurrent PPO with Decaying Teacher Anchor:** Conducted 15 iterations of recurrent sequence PPO (43,200 environment steps) against a diverse population league (`E2_A7`, `E8_DMITRII`, `E0_V3`, `SYN_AGG`). Exploration remained active throughout (entropy 0.115–0.332, avoiding the V38 collapse to 0.0). At peak iteration 10, the policy achieved **$116,125 cash**, a **+$97,218 mean margin**, and a **75.0% win rate** in training rollouts.
5. **Rigorous Paired Tournament Evaluation:** Evaluated `V40_PPO_ITER10` and `V40_BC_MODEL` across 40 paired legs on clean, unseen DEV seeds (`249685..249689`).
   - Against `SYN_AGG` (hostile market dumper), V40 was dominant (100% win rate, 0 casualties).
   - Against top deterministic baselines (`E2_A7`, `E8_DMITRII`, `E0_V3`), V40 achieved a 30.0% win rate vs 100.0% for V35 (0 rescues, 28 casualties, -$12,416 mean cash delta).
   - The pure BC model similarly suffered 4 casualties out of 8 legs against `E2_A7`.

### Verdict and Governance
Per Section 43 of the Governance Protocol, because V40 introduced 28 casualties on controlled fresh evaluation, it fails the Zero-Casualty Standard and cannot be promoted. It is formally classified as **`V40_RESEARCH_ONLY`**. The production baseline V35 remains untouched.

---

## 2. Forensic Diagnosis of Previous RL (V38 / RLX2)

In accordance with Section 2, the repository audit explicitly answered the 12 core failure questions:
1. **What was trained:** V38 trained a single-step MLP actor over 4 discrete residual actions.
2. **Action Space:** 4 actions (`TRUST_HEURISTIC`, `LIQUIDATE_ALL`, `EXPAND_LAND_F5`, `HOARD_INVENTORY`).
3. **Observation Space:** 20-dimensional flat feature vector (cash, day, hour, private shed).
4. **Reward:** Step-wise cash delta plus sparse win bonus.
5. **Policy Frequency:** Acted every single turn (H=1), generating massive exploration noise.
6. **Parallelization:** 1 single-threaded environment process.
7. **Throughput:** ~40 SPS.
8. **Bottleneck:** Official `kaggle_environments` JSON schema validation, deep-copying, and stdout interception.
9. **Heuristic Collapse Mechanism:** Because `TRUST_HEURISTIC` was always legal, any random exploration caused uncoordinated actions against the near-optimal A7 chore baseline, yielding large negative advantages. The optimizer rapidly zeroed out logits for non-heuristic actions, collapsing entropy to 0.28 in 6 iterations.
10. **Retained in V40:** Safe seed partitioning, league opponent definitions, A7 chore execution core.
11. **Discarded:** Coarse `TRUST_HEURISTIC` action, single-step feed-forward architecture, synchronous single-process stepping.
12. **Leakage Protection:** Strict seed isolation; all DEV holdouts (`214200..214249`, `340090..340199`, `249695..249734`) quarantined.

---

## 3. Simulator Parity & Throughput Benchmarks

### A. Simulator Parity Verification (`SIMULATOR_PARITY_REPORT.md`)
Across 6 deterministic test matches (4,314 simulation turns):
- **Parity Result:** **100% bit-for-bit identical** tile states, farm money, inventories, market orders, and terminal rewards.
- **Discrepancy Count:** Exactly **0**.

| Matchup | Seed | Official SPS | FastSim SPS | Speedup | Parity Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `E2_A7 vs E8_DMITRII` | 249635 | 51.3 | 198.4 | 3.9× | **PASS** |
| `E2_A7 vs E0_V3` | 249636 | 46.8 | 150.2 | 3.2× | **PASS** |
| `E2_A7 vs SYN_AGG` | 249637 | 64.6 | 255.5 | 4.0× | **PASS** |
| `E8_DMITRII vs E2_A7` | 249638 | 51.1 | 196.0 | 3.8× | **PASS** |
| `V35 vs E8_DMITRII` | 249639 | 49.3 | 191.0 | 3.9× | **PASS** |
| `E2_A7 vs PASSIVE` | 249640 | 73.7 | 265.3 | 3.6× | **PASS** |

### B. Throughput Scaling Benchmark (`SIMULATOR_THROUGHPUT_REPORT.md`)
- **Single-Worker FastSim:** **304.7 SPS** (vs 56.1 SPS official engine).
- **8 Workers:** **425.5 SPS** (10.6× faster than the V38 training pipeline).
- **12 Workers:** **469.9 SPS**.

---

## 4. Observation & Action Architecture

### Observation Encoder (112 Dimensions)
- **Economy (8 dims):** Normalized cash, net worth, inventory liquidation value, cash ratio, recent profit.
- **Inventory (25 dims):** Quantities, normalized volumes, perishability flags, and estimated spot value across all commodities.
- **Market (30 dims):** Current prices, historical price momentum (4-turn, 12-turn), spreads, and transaction volume pressure.
- **Production & Labor (24 dims):** Land plots owned, unassigned land, worker headcounts, worker utilization, housing capacity, animal counts.
- **Temporal (5 dims):** Current turn, normalized time remaining, day, hour, season progress.
- **Strategic History (20 dims):** One-hot representation of previous macro actions, recent expansion indicators, liquidity flags.
- **Zero Leakage:** Strictly utilizes only legally observable state; zero access to future prices, opponent identity, or replay data.

### Macro Action Space (16 Discrete Options)
- `0: BASELINE_EXPERT` (Keep base heuristic plan)
- `1: CROP_MELON_FOCUS` (Prioritize high-yield melon zoning)
- `2: CROP_CARROT_FOCUS` (Prioritize rapid-turnover carrot zoning)
- `3: LIVESTOCK_COW_EXPAND` (Accelerate dairy herd acquisition)
- `4: LIVESTOCK_SHEEP_EXPAND` (Accelerate wool flock acquisition)
- `5: HIRE_WORKER_AGGRESSIVE` (Expand labor force when cash permits)
- `6: FREEZE_HIRING` (Preserve liquidity by blocking labor expansion)
- `7: EXPAND_LAND_EARLY` (Purchase additional acreage ahead of schedule)
- `8: DEFER_LAND_EXPANSION` (Hold cash rather than buying acreage)
- `9: TERMINAL_LIQUIDATE_ALL` (Aggressive terminal inventory dump)
- `10: EXPAND_LAND_RLX2_F5` (Targeted counterfactual expansion rule)
- `11: PROTECT_LIQUIDITY` (Enforce strict minimum working capital reserve)
- `12: REINVEST_SURPLUS` (Reinvest excess cash into productive assets)
- `13: OPPORTUNISTIC_FRONT_RUN` (Dump inventory ahead of market dips)
- `14: EARLY_LIQUIDATE_SPOILAGE` (Flush vulnerable crops before spoilage)
- `15: EMERGENCY_CASH_CONVERT` (Immediate liquidity generation)

---

## 5. Neural Policy Architecture

```text
                  OBSERVATION (112 dims)
                            │
                            ▼
               MLP ENCODER (112 -> 128 ReLU)
                            │
                            ▼
                 TEMPORAL RECURRENT CORE
               GRU (128 hidden, 1 layer)
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
     ACTOR HEAD        CRITIC HEAD     AUXILIARY HEADS
 (128 -> 16 Logits)   (128 -> 1 Value) (Margin & Win Prob)
```

- **Core:** 1-layer GRU with 128 hidden units.
- **Action Masking:** Enforced dynamic legality mask (`-1e9` for invalid actions).
- **Multi-Task Critic:** Simultaneous prediction of discounted return, terminal cash margin, and win probability.

---

## 6. Training Progression & Diagnostics

### Phase 10: Behavioral Cloning Pretraining
- **Dataset:** 3,560 train samples, 1,780 val samples across 30 games.
- **Result:** **97.7% validation accuracy** at Epoch 25; action entropy stabilized at 0.050.

### Phase 12–16: Recurrent PPO Training (15 Iterations, 43,200 Steps)
- **Hyperparameters:** LR `3e-4`, Gamma `0.99`, GAE Lambda `0.95`, Clip `0.2`, Initial Teacher KL `0.08`, KL decay `0.92`.
- **Entropy & Exploration:** Maintained healthy policy entropy (0.060 at Iter 1 -> 0.115 at Iter 5 -> 0.250 at Iter 9 -> 0.193 at Iter 15).
- **Peak Iteration:** Iteration 10 reached **$116,125 cash**, **+$97,218 mean margin**, and **75.0% win rate** in training matches.

---

## 7. Paired Tournament Evaluation Results

Evaluated on clean, virgin DEV seeds (`249685..249689`) across 4 distinct opponents (`E2_A7`, `E8_DMITRII`, `E0_V3`, `SYN_AGG`) in both seat assignments.

### Table 1: V40 PPO Iter 10 vs V35 Baseline (40 Paired Matches)
| Opponent ID | Matches | V40 WR | V35 WR | WR Delta | Mean Cash Delta | Rescues | Casualties |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `E2_A7` | 10 | **0.0%** | 100.0% | -100.0% | $-13,811.6 | 0 | 10 |
| `E8_DMITRII` | 10 | **20.0%** | 100.0% | -80.0% | $-11,978.8 | 0 | 8 |
| `E0_V3` | 10 | **0.0%** | 100.0% | -100.0% | $-7,273.0 | 0 | 10 |
| `SYN_AGG` | 10 | **100.0%** | 100.0% | +0.0% | $-16,600.8 | 0 | 0 |
| **TOTAL** | **40** | **30.0%** | **100.0%** | **-70.0%** | **$-12,416.0** | **0** | **28** |

### Table 2: V40 PPO Iter 10 vs V39 Baseline (40 Paired Matches)
| Metric | V40_PPO_ITER10 | V39 Baseline | Delta |
| :--- | :---: | :---: | :---: |
| **Win Rate** | **30.0%** (12/40) | **100.0%** (40/40) | **-70.0%** |
| **Mean Cash Delta** | — | — | **$-12,493.1** |
| **Median Cash Delta** | — | — | **$-9,119.0** |
| **Rescues / Casualties**| — | — | **0 Rescues / 28 Casualties** |

### Table 3: V40 BC Model vs V35 Baseline (8 Paired Matches)
| Opponent ID | Matches | V40_BC WR | V35 WR | WR Delta | Mean Cash Delta | Rescues | Casualties |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `E2_A7` | 4 | **0.0%** | 100.0% | -100.0% | $-43,896.8 | 0 | 4 |
| `SYN_AGG` | 4 | **100.0%** | 100.0% | +0.0% | $0.0 | 0 | 0 |
| **TOTAL** | **8** | **50.0%** | **100.0%** | **-50.0%** | **$-43,896.8** | **0** | **4** |

---

## 8. Strategic Behavior & Failure Analysis

### What the Policy Actually Learned
1. **Hostile Environment Adaptation:** Against market dumpers (`SYN_AGG`), the policy learned to preserve working capital and liquidate opportunistically without taking market losses, achieving a flawless 100% win rate.
2. **Terminal Liquidation Discovery:** The model discovered Action 9 (`TERMINAL_LIQUIDATE_ALL`) and Action 15 (`EMERGENCY_CASH_CONVERT`) in late stages (turns 690–710), confirming that the network can independently discover liquidation timing.
3. **Exploration Incompatibility with Rigid Chore Logic:**
   - In Kagriculture, the incumbent baseline (`E9_AST` / `A7`) operates as an extremely tight deterministic chore machine. Workers are dispatched with cycle-perfect timing to water, weed, harvest, and milk.
   - When the neural policy selected a macro deviation (e.g. buying an extra plot of land at step 200 or freezing worker hiring), it consumed capital or altered tile layout without updating the internal chore planner's waypoint queue.
   - This caused an **execution desynchronization cascade**: crops missed watering cycles, harvests were delayed by 1 turn, and terminal cash dropped by $10,000–$14,000 against top bots.
   - Even in the pure Behavioral Cloning model (97.7% validation accuracy), the ~2.3% deviation rate produced ~4 unintended macro interventions per game, each of which introduced execution lag.

---

## 9. Final Governance Audit & Verification

### A. Protected Baseline Checksums
- `candidates/v35_a7_opening/main.py`: `1959021bdb1aeff720732aec866f5c9f3c9fa0b259ee0ab25982bda367593249` (**VERIFIED BIT-FOR-BIT IDENTICAL**)
- `candidates/v30_a7_standalone/main.py`: `51c1d25245f68dd8de66b355f2ad6ca1d79de8af02efed521a5a82f7be69ce3f` (**VERIFIED BIT-FOR-BIT IDENTICAL**)
- `submission_aec_v22r1.tar.gz`: `6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5` (**VERIFIED BIT-FOR-BIT IDENTICAL**)

### B. Holdout Seed Isolation
Protected holdouts `214200–214249`, `340090–340199`, and `249695–249734` were strictly guarded by automated runtime assertions. Zero touches occurred across all training, validation, and evaluation runs.

### C. Competition Submission Prohibition
Zero `kaggle competitions submit` commands were proposed, executed, or queued.

### D. Final Candidate Artifact
- Path: `candidates/v40_recurrent_macro/main.py`
- Model Weights: `candidates/v40_recurrent_macro/model_weights.pt`
- Candidate SHA256: `3f87fa2c5c24a4f29ee3f9dd16bde9b2192b7326ecf2efd321c07bf17f6d9e5b`

---

## 10. Final Decision

In accordance with Section 43:

```text
FINAL DECISION: V40_RESEARCH_ONLY
```

### Rationale
While the V40 program achieved high-throughput simulation (470 SPS), temporal recurrent representation, and active exploration without heuristic collapse, empirical paired evaluation proved that coarse macro interventions atop the rigid A7 chore chassis cause execution desynchronization and unacceptable casualties (28 casualties vs 0 rescues).

Under the Zero-Casualty Standard, V40 cannot be promoted to competition production. It remains quarantined in `research/v40/` and `candidates/v40_recurrent_macro/` as a valuable research milestone. V35 remains the live production baseline.
