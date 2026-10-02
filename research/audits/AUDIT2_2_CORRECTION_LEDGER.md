# AUDIT 2.2: MASTER CORRECTION LEDGER
## Exhaustive Record of Corrections, Scope Narrowings, and Refinements Applied to Audit 2.1 Deliverables

**Audit Exercise**: Independent Forensic Audit 2.2 of the Audit 2.1 Deliverables Suite  
**Governing Standard**: Stop Rule #2, Stop Rule #6, Stop Rule #8, and Master Provenance Protocol  
**Date**: 2026-09-11  

---

## 1. Itemized Master Correction Table

| Correction ID | Original Audit 2.1 Statement | Report Location | Specific Flaw, Mismatch, or Overstatement | Corrected & Authoritative Wording for Audit 2.2 | Final Status |
|:---:|:---|:---|:---|:---|:---:|
| **CORR-2.2-01** | *"Active live submissions 56146971 and 56146947 match frozen standalone compiled scripts bit-for-bit."* | `CLEAN_EVIDENCE_BASE:73`, `CLAIM_LEDGER:45`, `REPRODUCTIONS:126` | Conflating local file hash verification with Kaggle production server receipt (Stop Rule #6). A local SHA256 hash proves local file integrity, but cannot prove what Kaggle's scoring server executed without server-side verification. | **"Local file integrity verified bit-for-bit: `candidates/compiled_v54_plus_shop.py` (SHA256: `f651ccd2...`) and `candidates/compiled_v54_plus_residual.py` (SHA256: `18402ec6...`) match frozen deployment report records. Official Kaggle server deployment identity is unverified due to missing server-side receipts (Tier B scoped strictly to local binaries)."** | **NARROWED (PROVENANCE SCOPED)** |
| **CORR-2.2-02** | *"TOST demonstrates equivalence within ±$50.00 coins (p = 0.0321)."* | `STATISTICAL_AUDIT:123`, `FINAL_VERDICT:25`, `CLEAN_EVIDENCE_BASE:99` | Presenting $\pm \$50$ as an established universal equivalence bound without explicitly noting that the margin was selected post-hoc from the observed 90% confidence interval ($[+\$2.08, +\$47.15]$), and that mean-score equivalence does not establish behavioral or strategic parity. | **"TOST establishes statistical equivalence in mean payoff within a post-hoc equivalence bound of ±$50.00 coins (p = 0.0321), but fails at tighter bounds (±$25.00, p = 0.4887). While $50 represents mean-score proximity (0.05% of game score), it does not establish behavioral identity or eliminate single-seed tail risks."** | **QUALIFIED (POST-HOC & SCOPE LABELED)** |
| **CORR-2.2-03** | Distribution Percentiles table: `p01=-623.8, p05=-344.9, p10=-177.3, p25=-58.0, p75=112.0, IQR=170.0`. | `STATISTICAL_AUDIT:81-89` | Secondary calculation mismatch. Recomputing directly from the raw 150 paired CRN observations yields: `p01=-533.6, p05=-198.5, p10=-126.2, p25=-84.0, p75=156.0, IQR=240.0`. | **"Empirical percentiles of the 150 paired differences: p01 = -$533.6, p05 = -$198.5, p10 = -$126.2, p25 = -$84.0, p50 (Median) = +$58.0, p75 = +$156.0, p90 = +$204.0, p95 = +$224.4, p99 = +$280.7. Interquartile Range (IQR) = $240.0."** | **CORRECTED (DATA RECOMPUTED)** |
| **CORR-2.2-04** | *"Trimmed Mean (5% cut each tail): +$33.72."* | `STATISTICAL_AUDIT:59` | Calculation mismatch. Trimming 5% from each tail of the raw 150 paired observations (cutting the 7 lowest and 7 highest seeds) yields `+$36.53`. | **"Sample Trimmed Mean (5% cut each tail, 136 seeds): +$36.53."** | **CORRECTED (DATA RECOMPUTED)** |
| **CORR-2.2-05** | Outlier sensitivity test metrics: `New Std: 153.22, New SE: 12.55, New 95% CI: [+$4.87, +$54.49], New p-value: 0.0195`. | `STATISTICAL_AUDIT:107-111` | Secondary calculation mismatch. Recomputing across the 149 seeds after deleting Seed 50081 (-$730.0) yields Mean = +$29.68, Std = 155.30 (not 153.22), SE = 12.72 (not 12.55), 95% CI = `[+$4.54, +$54.82]`, t-stat = 2.3333, p-value = 0.0210 (not 0.0195). | **"Outlier sensitivity test (trimming Seed 50081, N=149): Mean = +$29.68, Std = 155.30, SE = 12.72, 95% CI (Student's t, df=148) = [+$4.54, +$54.82], t = 2.3333, p = 0.0210."** | **CORRECTED (DATA RECOMPUTED)** |
| **CORR-2.2-06** | Table entries for control source file sizes: `candidates/v54_plus_shop.py` (24,196 bytes) and `candidates/v54_plus_residual.py` (24,534 bytes). | `REPRODUCTIONS:136-137` | Reporting transcription typo. While SHA256 hashes matched the files on disk exactly, the true file sizes on disk are 6,220 bytes and 5,667 bytes. | **"Control Source `candidates/v54_plus_shop.py`: 6,220 bytes, SHA256 `592f0ba3...`; Control Source `candidates/v54_plus_residual.py`: 5,667 bytes, SHA256 `5b2d5080...`."** | **CORRECTED (FILE SIZE TYPO)** |
| **CORR-2.2-07** | Scope of 19S/0T Strawberry finding: asserting dominance without explicitly bounding partition execution. | `CLAIM_LEDGER:51`, `REPRODUCTIONS:208` | Inspection of `crop_portfolio_sweep.py:188` proves the sweep was executed strictly on seeds 50000–50049 (Discovery set). It was never evaluated on Qualification (50050–50099) or Holdout (50100–50149). Win rate is 59.0%, and tomato outperforms on specific Pizza seeds. | **"Pure 19S/0T Strawberry Bedrock achieves the highest mean margin (+24.98), highest win rate (59.0%), and lowest downside risk (56.72) among the 12 evaluated static crop allocations strictly on the 50-seed Discovery partition. It does not strictly dominate on every individual seed, and has not been swept on Qualification or Holdout partitions."** | **NARROWED (PARTITION BOUNDED)** |
| **CORR-2.2-08** | Live tournament loss causal attribution: asserting crop-demand mismatch as established cause. | `FINAL_VERDICT:27`, `CLEAN_EVIDENCE_BASE:149` | Conflating strongly supported economic correlation with experimentally isolated counterfactual proof (Stop Rule #5). | **"Directly Observed Fact: Replay 107543042 revealed 2 Pizza, 3 Pet Cafe, 0 Brunch, 0 Ice Cream. Eldritch sold 0 Tomato, 12 Carrot ($71k) while ORiginators sold 152 Tomato, 69 Carrot ($126k). Strong Mechanistic Inference: Specialization mismatch between static strawberry production and town shop demand was the primary economic driver of the score gap. Counterfactual Proof: Unverified (dynamic adaptive replay rerun was not executed)."** | **RECLASSIFIED (EPISTEMIC SEPARATION)** |

---

## 2. Definitive Re-Affirmation of Confirmed Retractions (Tier F)

Audit 2.2 independently re-verifies and permanently affirms all seven retractions inherited through Audit 2 and Audit 2.1:

1. **F1: Day-11 Tomato +$3,942 Specialization Alpha**:
   - **Ground Truth**: Cherry-picked outlier on Seed 50042.
   - **Evidence**: 6-seed True Pizza ensemble average was -$5,382.67; all 18 parameter combinations in `scratch/true_pizza_sweep_results.json` produced negative mean deltas vs V2.
2. **F2: Flawed Shop Transition Model (`shop_transition_model.py`)**:
   - **Ground Truth**: Fabricated or incomplete demand lists for 6 out of 8 town shops.
   - **Evidence**: Direct comparison against C++ `sim.hpp:127-137` and Python `kg.SHOPS`. All downstream Markov decision models and VoI derivations remain discarded.
3. **F3: The "No Agricultural Slack Exists" Proof**:
   - **Ground Truth**: Experiment was methodologically invalid.
   - **Evidence**: `run_additive_investigation.py:154-193` never scheduled watering or harvesting for vacant crops (crops rotted to weeds per `sim.hpp:725`), and hired workers daily for 18 days. The existence of profitable slack remains an open hypothesis.
4. **F4: Step 696 Market Order Truncation as Root Causality**:
   - **Ground Truth**: Step 696 was an observational symptom, not the root cause.
   - **Evidence**: Seed 50081 timeline proves cash diverged at Step 164, a fatal sheep purchase failure occurred at Step 217 ($950 vs $954), Tile (1, 4) diverged for 460 turns, and V2 was already down by -$292 before Step 696. Wheat was sold at Step 712 anyway.
5. **F5: Claim of "Confirmed Global Superiority" for CLOSED_LOOP_V2**:
   - **Ground Truth**: Statistically unproven.
   - **Evidence**: Two-sided paired t-test yields $p = 0.0727 > 0.05$; Student's t 95% CI `[-$2.29, +$51.52]` spans zero. V2 is a parity anchor, not a proven superior champion.
6. **F6: The "$800 Dawn Hiring Collapse" Narrative**:
   - **Ground Truth**: Factual disproof from official tournament replay data.
   - **Evidence**: `episode_107543042.json` proves Eldritch had $9,847 cash on Day 12 dawn, hired 9 hands, and paid $88 in Fibonacci hiring costs. Narrative was manufactured by a dictionary parser bug in `scratch/reconstruct_live_losses.py:66` (`units` vs `hands`).
7. **F7: "100.0% Bit-for-Bit Physical Agronomy Identity"**:
   - **Ground Truth**: Disproven by empirical divergence and source code analysis.
   - **Evidence**: Seed 50081 diverged physically for 460 turns due to runtime cash feedback failing a sheep purchase; Dmitrii-LB2800 executes a 64-simulation Monte Carlo terminal planner (`policy.py:12-45`) at steps 712–718 while V2 executes PASS.
