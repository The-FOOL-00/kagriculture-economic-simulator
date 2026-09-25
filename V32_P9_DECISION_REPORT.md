# V32 P9 DECISION REPORT: HMEH PROMOTION & COMPETITION VERDICT

**Author**: Kagriculture V32 Research Program  
**Date**: 2026-09-23  
**Status**: FORMAL RESEARCH PHASE COMPLETE — DECISION LOCKED  

---

## 1. EXECUTIVE SUMMARY & DECISION

Phase V32 P9 evaluated whether an adaptive, state-grounded macroeconomic architecture—**Hierarchical Macro-Economic Hybrid (HMEH)**—could materially outperform our proven competition benchmarks (`A7` and `V22R1`) while preserving A7's Step-0 30-wash capital mechanism.

### Key Conclusions:
1. **The HMEH Architecture is Proven and Structurally Sound**:
   - The 5-layer pipeline (`Observation -> Economic State -> Macro Replanner -> Strategic Intent -> Chore Executor -> Legality Filter -> Simulator`) completed 120 full competition legs across 6 diverse opponent archetypes with **0 crashes, 0 unexpected illegal actions, and 0 frozen dependency modifications** (Passing Gates A & B).
2. **A7 Baseline Preservation is 100.0% Exact**:
   - `HMEH-0` replicates A7's exact trajectory, achieving identical terminal rewards down to the cent ($59,603.00 on Seed 249675, $80,884.00 on Seed 249676, $142,499.00 on Seed 249677), preserving the +$1,286.00 alpha over V3.
3. **Counterfactual Evaluation of Proposed Adaptive Mechanisms**:
   - **Adaptive Labor Throttling (HMEH-1)**: **REFUTED**. Throttling late-game hand hiring caused net regressions (-$2,096 to -$2,918 per seed) because hands are required for parallel endgame crop and livestock harvest sweeps.
   - **Shop-Conditioned Production (HMEH-2)**: **NEUTRAL / REGRESSIVE**. The underlying teacher already branches at Step 144 based on `YARN_STORE`; manual crop diversions at Day 3 delayed melon compounding.
   - **Market-Aware Selling / Batching (HMEH-3)**: **DANGEROUS / REFUTED**. Holding sales into 24-lot batches allowed opponents to front-run the market, causing HMEH's win rate against V3 to collapse from 100% to 10%. Continuous immediate selling (`sell_lead: True`) is game-theoretically dominant.
   - **Terminal Liquidation Search (HMEH-4)**: **REDUNDANT**. Detailed inventory forensics revealed that A7 already liquidates 100% of shed and hand cargo at Step 718.
4. **Final Architecture Decision**:
   - All speculative adaptive overrides (labor throttling, sale delays) are **REMOVED**.
   - The production candidate **`candidates/v32_hmeh_release/main.py`** retains the exact, battle-tested A7 engine wrapped inside the robust HMEH legality and fallback harness.

---

## 2. FORMAL ANSWERS TO THE 12 COMPETITION DECISION QUESTIONS

### 1. Does HMEH materially outperform A7?
**No.** HMEH matches A7 at exact parity ($0.00 paired delta on identical seeds). Speculative adaptive labor and selling mechanisms regressed against A7. A7 remains our most optimal and proven policy mechanism.

### 2. Does HMEH materially outperform V22R1?
**Yes.** Across 20 paired evaluation legs on the development panel, HMEH strictly and consistently outperforms V22R1:
- **Win Rate vs V22R1**: **100.0%** (20 Wins / 0 Losses).
- **Mean Margin vs V22R1**: **+$1,265.15**.
- **Median Cash vs V22R1**: $84,593.00 vs $83,328.00.

### 3. Which mechanism contributes the most?
The **Step-0 30/30 Wheat Wash** ($30 \times 25$ round trip) contributes 100% of the active alpha over V3 (+$1,286.00), preventing early-game cash exhaustion and funding additional livestock and crops.

### 4. Which mechanism contributes nothing and should be removed?
- **Labor Throttling**: Removed (caused -$2,000+ loss from unharvested crops).
- **Market Sale Batching / Delay**: Removed (caused opponent front-running and 90% loss rate).

### 5. Is the gain robust across opponents?
**Yes.** Against the 6-opponent benchmark panel:
- vs `E0_V3`: 100% Win Rate (+$1,286.00 margin)
- vs `E1_V22R1`: 100% Win Rate (+$1,265.15 margin)
- vs `E8_DMITRII`: 90% Win Rate (+$3,731.50 margin)
- vs `V54`: 100% Win Rate (+$19,916.20 margin)
- vs `SYN_AGG`: 100% Win Rate (+$160,700.05 margin)
Overall panel win rate: **90.0%** (108 Wins / 2 Losses / 10 Ties).

### 6. What is the worst-case failure mode?
Adverse early market price shocks on rare seeds (e.g. Seed 249677 against Dmitrii Gluzdov), where carrot price collapse caused a -$1,167.00 loss.

### 7. How much of A7's proven mechanism is preserved?
**100.0%**. The Step-0 wash, the opening 5-hand pasture setup, the Day 6 shop branching, and the Step 718 terminal liquidation are completely preserved.

### 8. Is the candidate safe enough for controlled live submission?
**Yes.** `candidates/v32_hmeh_release/main.py` is standalone, has zero external dependencies, satisfies all legality gates, and passes 100% of freeze integrity tests.

### 9. What evidence would justify a live submission?
Controlled live A/B evaluation against the current live pool to verify that the release candidate matches or exceeds Slot B (`A7`).

### 10. What remains unknown?
The exact distribution of unseen competition opponents in the top tier (3000+ LB) whose policies may differ from the public Dmitrii / V54 baselines.

### 11. How much time remains until 2026-09-30?
Exactly **7 days** (Current local time: September 23, 2026).

### 12. What is the highest-value next action before the deadline?
Maintain **Slot A (V22R1)** and **Slot B (A7)** in live play. Conduct controlled single-slot validation of `candidates/v32_hmeh_release/main.py` only if Slot B exhibits live drift. Do not make unvalidated heuristic changes.

---

## 3. MASTER EVALUATION SUMMARY

```
================================================================================
Policy              Opponent      Seeds   Mean Cash    Median Cash  Win%    Delta vs A7
--------------------------------------------------------------------------------
HMEH-0 (RC)         E0_V3         10 (20) $ 92,134.90  $ 84,601.50  100.0%  +$0.00
HMEH-0 (RC)         E1_V22R1      10 (20) $ 92,111.75  $ 84,593.00  100.0%  +$0.00
HMEH-0 (RC)         E2_A7         10 (20) $ 90,194.15  $ 89,175.00   50.0%  +$0.00
HMEH-0 (RC)         E8_DMITRII    10 (20) $ 91,501.00  $ 92,592.00   90.0%  +$0.00
HMEH-0 (RC)         V54           10 (20) $ 98,324.55  $ 95,812.50  100.0%  +$0.00
HMEH-0 (RC)         SYN_AGG       10 (20) $163,700.05  $171,175.50  100.0%  +$0.00
--------------------------------------------------------------------------------
OVERALL BENCHMARK   6 OPPONENTS   120 legs $104,661.07 $ 93,812.00   90.0%  +$0.00
================================================================================
```

---

## 4. SIGN-OFF

- **Phase V32 P9 Status**: **SUCCESSFULLY CONCLUDED**.
- **Frozen Dependencies**: **100% UNTOUCHED (0 DRIFT)**.
- **Protected Holdouts**: **100% VIRGIN & UNTOUCHED**.
- **Release Candidate**: **DELIVERED AT `candidates/v32_hmeh_release/main.py`**.
