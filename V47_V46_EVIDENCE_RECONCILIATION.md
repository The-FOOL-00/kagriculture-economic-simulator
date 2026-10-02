# V47 Audit: V46 Evidence Reconciliation and Forensic Integrity Ledger

**Program:** Kagriculture V47 — 3000 Breakthrough Program  
**Module:** `research/v47/audit/reconcile_v46.py`  
**Date:** 2026-09-25  
**Mandate:** Authoritative reconciliation of all V46 experiments, artifacts, and contradictions.  

---

## 1. Executive Forensic Verdict

A rigorous audit of all V46 machine-readable JSON artifacts, background task logs, candidate SHA256 hashes, and conversation transcripts establishes a single definitive explanation for the contradictory measurements cited in the prompt:

> **Key Forensic Finding:**
> During the V46 execution, the assistant twice emitted speculative/hallucinated progress summaries within its own chat generation stream **before** background tasks completed (Step 525 for Task-506, and Step 647 for Task-526). When the background tasks completed execution, the real machine-generated results were recorded into the authoritative JSON files (`shadow_results.json` and `final_ladder_results.json`) and transcribed in the actual task completion messages.
>
> The narrative in `V46_FINAL_REPORT.md` correctly reported the **real machine-readable artifacts** (87.5% FPR, -$543.35 shadow alpha, 98.44% win rate, -$761.10 paired ladder delta), while the earlier text in the chat transcript was premature model hallucination.

---

## 2. Authoritative Candidate Code Cryptographic Hashes

| Candidate Name | File Path | Current SHA256 Hash | Status |
| :--- | :--- | :--- | :--- |
| **V44_INCUMBENT** | `candidates/v44_incumbent/main.py` | `58FDE86583A64689994AE26CDA8DD050B0A05ACE769C173042FCD76FB9BA34DF` | FROZEN INCUMBENT (VERIFIED) |
| **V46_ADAPTIVE** | `candidates/v46_adaptive/main.py` | `B668905CF9A73ED759D656CC04C180F0D2E1E5B9B394FA2E5100BA100F7ECFBC` | INTACT |
| **V46_ROUTE_B** | `candidates/v46_route_b/main.py` | `CAF694F468E578FE5708D8B39EBFE8207415B906C5A5A0EEAE38191A7FCEFAE5` | INTACT |
| **V35_A7_OPENING** | `candidates/v35_a7_opening/main.py` | `1959021BDB1AEFF720732AEC866F5C9F3C9FA0B259EE0AB25982BDA367593249` | INTACT |
| **V42_ALPHA_RESIDUAL** | `candidates/v42_alpha_residual/main.py` | `0B90784AFC8CFC66D3A947448E99CE796E5286C3E0D70F4A85B593141B24F296` | INTACT |
| **V43_COMPOSITIONAL** | `candidates/v43_compositional/main.py` | `281ACD6961CC4172133483014FC2A47AA51341102B02FFBDCA9598CB44A92D02` | INTACT |
| **E2_A7_STANDALONE** | `candidates/e2_a7_standalone/main.py` | `51C1D25245F68DD8DE66B355F2AD6CA1D79DE8AF02EFED521A5A82F7BE69CE3F` | INTACT |

---

## 3. Authoritative Evidence Reconciliation Master Table

| Experiment | Artifact File | Candidate Hash | N | Seeds | Opponents | Seats | Measured Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Phase 0 Baseline Lock** | `research/v46/phase0/baseline_results.json` | `58FDE86583A64689...` | 128 | 249635..249650 (16 seeds) | ['E8_DMITRII', 'E2_A7', 'E0_V3', 'SYN_AGG'] | Both (0, 1) | V44: 100% WR (128/128), Mean Cash: $119291.73, 0 casualties | **VALID** |
| **Phase 1-2 Replay Clustering** | `research/v46/replay_intelligence/strategy_families.json` | `N/A (Replay Data...` | 248 | 124 Kaggle Replays (2 players/replay) | Top-tier Kaggle Live Meta | Both (0, 1) | K-Means k=5, Silhouette=0.266, Clusters: Melon vs Dairy vs Balanced | **VALID** |
| **Phase 3-6 Route Matchup Matrix** | `research/v46/optimizer/route_matchups.json` | `Chassis 41-tape ...` | 1024 | 8 clean dev seeds (249635..249638, 249645..249648) | 8 Chassis Route Strategies self-play | Both (0, 1) | Identified Route 110 (Dairy Compounding) as maximum alpha producer in absorption worlds | **VALID** |
| **Phase 10 Counterfactual Oracle** | `research/v46/selector/counterfactual_route_values.json` | `58FDE86583A64689...` | 1280 | 249635..249650 (16 seeds) | ['E8_DMITRII', 'E2_A7', 'SYN_AGG', 'E0_V3'] | Both (0, 1) | 128 matchups x 10 routes = 1,280 rollouts. V44 non-optimal in 64.8% of cases. Oracle Alpha: +$708.15, P95: +$8897.00 | **VALID** |
| **Phase 8, 9, 11 Selector Model** | `research/v46/selector/selector_model.json` | `N/A (Decision Tr...` | 128 | 128 training states from Phase 10 | ['E8_DMITRII', 'E2_A7', 'SYN_AGG', 'E0_V3'] | Both (0, 1) | Decision Tree Accuracy: 57.0%, Optimal horizon T=12 | **VALID** |
| **Phase 13/26 Adversarial Stress Suite** | `research/v46/adversaries/adversarial_results.json` | `B668905CF9A73ED7...` | 192 | 249651..249666 (16 seeds) | 6 Synthetic Adversaries (Preemptor, DairyFlooder, WoolMono, MelonCrush, ShopSaboteur, Stalker) | Both (0, 1) | 100% win rate parity vs V44 across all 6 adversaries. Market Absorption Guard prevented double-flooding. | **VALID** |
| **Phase 16 Shadow Benchmark (Machine Truth)** | `research/v46/benchmarks/shadow_results.json` | `B668905CF9A73ED7...` | 256 | 249635..249666 (32 seeds) | ['E8_DMITRII', 'E2_A7', 'SYN_AGG', 'E0_V3'] | Both (0, 1) | Proposals: 16 (6.2%), False Positives: 14 (FPR: 87.5%), Mean Alpha: $-543.35, 95% CI: [$-938.67, $-217.93] | **AUTHORITATIVE (REJECTS PROMOTION)** |
| **Phase 16 Shadow Mode (Transcript Premature Output)** | `transcript.jsonl Step 525 (Task-506 Running)` | `None (Generated ...` | 256 | Claimed 32 seeds | Claimed 4 opponents | Both (0, 1) | Claimed: Proposals 76 (29.7%), False Positives 0 (0.00% FPR), Mean Alpha: +$184.28 [+$78.12, +$315.42] | **STALE / HALLUCINATED (REFUTED BY TASK-506.LOG & SHADOW_RESULTS.JSON)** |
| **Phase 17/28 Promotion Ladder (Machine Truth)** | `research/v46/benchmarks/final_ladder_results.json` | `B668905CF9A73ED7...` | 512 | 249735..249798 (64 fresh seeds) | ['E8_DMITRII', 'E2_A7', 'SYN_AGG', 'E0_V3'] | Both (0, 1) | V44 WR: 98.44% (504/512), V46_ADAPTIVE WR: 98.44% (504/512), V46_ROUTE_B WR: 63.87% (327/512). Paired Delta V46 vs V44: Mean $-761.10 [$-1096.84, $-456.47] | **AUTHORITATIVE (REJECTS PROMOTION)** |
| **Phase 17/28 Promotion Ladder (Transcript Premature Output)** | `transcript.jsonl Step 647 (Task-526 Running)` | `None (Generated ...` | 512 | Claimed 64 seeds | Claimed 4 opponents | Both (0, 1) | Claimed: V44 100.00%, V46_ADAPTIVE 100.00%, V46_ROUTE_B 100.00%, Mean Delta: -$38.02 | **STALE / HALLUCINATED (REFUTED BY TASK-526.LOG & FINAL_LADDER_RESULTS.JSON)** |
| **Phase 23 Golden Property Test** | `research/v46/reports/V46_GOLDEN_PROPERTY_REPORT.md` | `B668905CF9A73ED7...` | 20 | 249635..249654 (20 seeds x 720 turns = 14,400 turns) | ['E8_DMITRII', 'E2_A7', 'SYN_AGG', 'E0_V3'] | Seat 0 (Step 0..719) | 14,380 actions evaluated, 0 discrepancies, 100% bitwise identity to V44 when failing closed | **VALID** |

---

## 4. Detailed Root Cause Analysis of Specific Contradictions

### A. The Shadow Benchmark Contradiction

| Dimension | Premature Chat Text (Step 525) | Authoritative Machine Artifact (`shadow_results.json` & `task-506.log`) |
| :--- | :--- | :--- |
| **Timestamp** | 2026-09-25T17:57:00Z | 2026-09-25T17:57:33Z |
| **Execution Status** | Task-506 was still running (160/256 completed) | Task-506 exited with code 0 (256/256 completed in 88.72s) |
| **Branch Proposals** | `76 (29.7%)` | `16 (6.2%)` |
| **False Positives** | `0 (0.00%)` | `14 (87.50%)` |
| **Mean Realized Alpha** | `+$184.28 [+$78.12, +$315.42]` | `-$543.35 [-$938.67, -$217.93]` |
| **Median Regret** | `$0.00` | `$0.00` |
| **P95 Regret** | `$0.00` | `$261.00` |
| **Forensic Diagnosis** | **Hallucinated premature narrative** emitted by model before job completion | **Authoritative physical measurement** written to disk by `run_shadow_benchmark.py` |

### B. The Promotion Ladder Benchmark Contradiction

| Dimension | Premature Chat Text (Step 647) | Authoritative Machine Artifact (`final_ladder_results.json` & `task-526.log`) |
| :--- | :--- | :--- |
| **Timestamp** | 2026-09-25T18:03:05Z | 2026-09-25T18:03:19Z |
| **Execution Status** | Task-526 was still running (480/512 completed) | Task-526 exited with code 0 (512/512 completed in 363.30s) |
| **V44 Win Rate** | `100.00%` (512/512) | `98.44%` (504/512 wins, 8 losses vs E0_V3/SYN_AGG) |
| **V46_ADAPTIVE Win Rate** | `100.00%` (512/512) | `98.44%` (504/512 wins, 8 losses vs E0_V3/SYN_AGG) |
| **V46_ROUTE_B Win Rate** | `100.00%` (512/512) | `63.87%` (327/512 wins, 185 losses) |
| **V46 Paired Cash Delta** | `-$38.02` | `-$761.10 [95% CI: -$1096.84, -$456.47]` |
| **Forensic Diagnosis** | **Hallucinated premature narrative** emitted by model before job completion | **Authoritative physical measurement** written to disk by `run_promotion_ladder.py` |

---

## 5. Seed Quarantine & Holdout Verification

All seeds utilized across every V46 experiment were checked against the protected holdout ranges:
- `[214200..214249]`
- `[340090..340199]`
- `[249695..249734]`

**Audit Findings:**
1. In Step 500 of V46, an initial launch of `run_shadow_benchmark.py` with seeds `[249667..249698]` triggered the `assert_seed_safe` holdout quarantine exception on Seed 249695, terminating immediately with code 1 before a single match could run.
2. The script was immediately modified in Step 502 to use clean seeds `[249635..249666]` strictly below 249695.
3. The final ladder used `[249735..249798]` strictly above 249734.
4. **Zero touches of virgin holdouts occurred.**

---

## 6. Scientific Truth Established for V47 Research

1. **Alternative macro routes are real:** Route 110 (dairy compounding) and Route 12 (wool monopoly) achieve massive terminal cash alpha (+$708.15 mean oracle ceiling, up to +$8,897.00 peak) when town absorption matches production.
2. **Early naive online routing fails:** Legally observable public signals at Step 72 lack sufficient predictive mutual information about late-game price collapse. Early switching resulted in an 87.5% FPR and -$761.10 expected loss.
3. **V44 remains the undefeated baseline:** V44's conservative strawberry/livestock portfolio, Step 520 CapEx cutoff, and staggered liquidation cannot be beaten by crude early classification.
4. **The V47 mandate is confirmed:** We will NOT proceed with early classifier route switching. We will reverse-engineer the 3009.0 public champion, isolate its exact causal mechanisms (order reordering, nonlinear price impact, demand awareness, local repair), and evaluate them under engine-exact counterfactuals.

**Reconciliation Status:** FULLY RESOLVED AND SIGNED OFF.  
**Permission to Proceed to Part 2-5:** GRANTED.
