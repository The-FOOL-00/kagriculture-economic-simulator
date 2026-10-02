# V45 Market Rescue Mining & Near-Tie Forensic Report

**Document ID:** `research/v45/reports/V45_MARKET_RESCUE_REPORT.md`  
**Date:** 2026-09-25  
**Repository:** `The-FOOL-00/kagriculture-economic-simulator`  
**Phase:** Phase 6 (Market Rescue Mining)  
**Artifact Path:** `research/v45/artifacts/market_rescue_library.json`  
**Scope:** Forensic analysis of baseline losses, near-ties, and margin dynamics under adversarial market strategies.  

---

## 1. Executive Summary

Phase 6 searches for rescue opportunities where candidate market strategies can convert baseline losses or narrow near-ties into decisive victories.

Across our 128-leg tournament benchmark, the baseline incumbent V44 demonstrated **complete dominance**:
* **Total Baseline Wins:** 128 out of 128 legs (**100.0% Win Rate**).
* **Baseline Losses:** **0** losses.
* **Baseline Ties:** **0** ties.
* **Inherited Rescue over V35:** 1 confirmed rescue (Seed 249657 vs `E2_A7` in Seat 0, converted from a -$374 deficit in V35 to a +$16 win in V44).

---

## 2. Cohort Stratification & Margin Breakdown

Because V44 suffered 0 losses, empirical cohorts were defined by winning margin quantiles:

### Cohort A: High-Margin Comfortable Wins (Margin $\ge \$1,500$)
* Represents 75% of all match legs (P25 quantile is +$1,519.0).
* In these games, internal A7 farm productivity dwarfs opponent output, resulting in margins between $2,000 and $190,000.
* Market intervention variations here produce negligible impact on matchup outcome.

### Cohort B: Near-Ties / Critical Margin Buffer (Margin $< \$300$)
* Represents the bottom 6% of matchups.
* Key Matchup: **Seed 249657 vs `E2_A7` (Seat 0)**:
  * V44 Cash: $133,581 | Opponent Cash: $133,565
  * Terminal Margin: **+$16.00**
* On this critical seed, any deviation from V44's exact 50/50 liquidation schedule (such as selling 60% early, capping depth, or triggering dynamic pre-emption) destroys $50–$100 in realized cash due to slippage, instantly flipping the match from a win to a **casualty**.

---

## 3. Rescue Library Catalog

As cataloged in `research/v45/artifacts/market_rescue_library.json`:
* **New LOSE $\to$ WIN Conversions:** Exactly **0** (no baseline losses exist in the DEV evaluation suite).
* **LOSE $\to$ TIE Conversions:** 0.
* **Casualty Risk:** Highly acute. Multiple tested strategies (`TRANCHE_60_40`, `DEPTH_CAPPED_15`, `PREEMPT_691_692`, `DYNAMIC_PREEMPT`) converted the +$16 win on Seed 249657 into a loss.

---

## 4. Scientific Verdict

The rescue mining audit confirms that V44's existing liquidation profile already extracts all readily available rescue value on this benchmark suite. Further active market intervention does not yield positive rescue alpha.
