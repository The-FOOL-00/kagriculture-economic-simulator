# V42 Rare Economic Alpha Catalog

**Document ID:** `research/v42/reports/RARE_ALPHA_CATALOG.md`  
**Date:** 2026-09-25  
**Repository:** `Kagriculture`  
**Artifact Path:** `research/v42/artifacts/v42_alpha_dataset.pt`  
**Ranking Criterion:** Sorted by **Robust Incremental Value** (Reward-to-Risk Ratio, Lower-Tail Downside, and Zero-Casualty Invariant), NOT raw maximum gain.

---

## 1. Executive Summary

This catalog documents all strategic interventions evaluated under the V42 exact terminal simulation architecture (2,821 counterfactual transitions across 16 safe training seeds and 4 league opponents).

In accordance with Section 31 and 32 of the V42 specification, raw maximum delta (`+$17,324.0` in sporadic outlier games) is explicitly rejected as a selection metric. Candidates are ranked strictly by their ability to repeatedly produce positive margin improvements with minimal downside tail risk and zero casualties.

---

## 2. Master Ranked Alpha Catalog

| Rank | Intervention Name | Legal Count | Pos Count | Pos Rate | Mean $\Delta$ | Med $\Delta$ | Max $\Delta$ | P5 $\Delta$ | P95 $\Delta$ | Rescues | Casualties | Robust Alpha Status |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | `TERMINAL_LIQUIDATE_PARTIAL` | 447 | 202 | **45.2%** | **+$24.8** | $0.00 | +$552.0 | **-$111.0** | +$185.0 | **5** | **0** | **APPROVED HIGH-ALPHA** |
| **2** | `TERMINAL_LIQUIDATE_FULL` | 210 | 99 | 47.1% | +$27.4 | $0.00 | +$649.0 | -$241.0 | +$313.3 | 3 | **0** | **APPROVED CONDITIONAL** |
| **3** | `NO_INTERVENTION` (Baseline) | 2,821 | 0 | 0.0% | $0.00 | $0.00 | $0.00 | $0.00 | $0.00 | 0 | **0** | **INCUMBENT FOUNDATION** |
| **4** | `DEFER_EXPANSION_LOW_CASH` | 82 | 3 | 3.7% | +$190.9 | $0.00 | +$14,242.0 | $0.00 | $0.00 | 0 | **0** | **SAFE PROTECTIVE** |
| **5** | `PRESERVE_LIQUIDITY_BUFFER` | 562 | 3 | 0.5% | +$27.9 | $0.00 | +$14,242.0 | $0.00 | $0.00 | 0 | **0** | **SAFE PROTECTIVE** |
| **6** | `HOLD_DEPRESSED_GOODS` | 182 | 26 | 14.3% | -$1.1 | $0.00 | +$369.0 | -$19.0 | +$17.8 | 0 | **0** | **NEUTRAL SPECULATIVE** |
| **7** | `SPOT_SELL_PEAK_MILK` | 653 | 47 | 7.2% | +$18.7 | $0.00 | +$17,324.0 | -$47.4 | +$30.0 | 1 | **2** | **HIGH RISK / GATED** |
| **8** | `SPOT_SELL_PEAK_WOOL` | 507 | 22 | 4.3% | +$24.5 | $0.00 | +$14,474.0 | -$27.0 | $0.00 | 5 | **2** | **HIGH RISK / GATED** |
| **9** | `SPOT_SELL_PEAK_STRAWBERRY` | 495 | 13 | 2.6% | **-$25.3** | $0.00 | +$619.0 | -$131.0 | $0.00 | 0 | **1** | **HARD NEGATIVE / REJECT** |
| **10** | `MIDGAME_LAND_EXPAND_GATED` | 0 | 0 | 0.0% | N/A | N/A | N/A | N/A | N/A | 0 | **0** | **DISQUALIFIED (UNSAFE)** |

---

## 3. Deep-Dive Profiles per Discovered Intervention

### Rank 1: `TERMINAL_LIQUIDATE_PARTIAL` (Action ID: 2)
* **Mechanic:** At steps 690–694 and 704–706, liquidates 50% of marketable shed stock (`STRAWBERRY`, `MILK`, `WOOL`, `MELON`).
* **Occurrence Count:** 447 legal opportunities in dataset.
* **Positive Count:** 202 (45.2% hit rate).
* **Mean Delta:** `+$24.8` | **Median Delta:** `$0.00` | **Max Delta:** `+$552.0`.
* **5th Percentile:** `-$111.0` | **95th Percentile:** `+$185.0`.
* **Rescues:** **5 confirmed match rescues**.
* **Casualties:** **0 casualties**.
* **Economic Preconditions:**
  1. `step in (692, 693, 694)` or `step in (704, 705)`.
  2. Shed contains $\ge 2$ units of high-value goods (`MILK`, `WOOL`, `STRAWBERRY`, `MELON`).
  3. Opponent is an aggressive dumper (`E8_DMITRII`, `SYN_AGG`) likely to crash spot price at step 695.
* **Known Failure Regimes:**
  - When marketable spot prices are already severely depressed ($P < \$15$), liquidating 50% yields negligible cash while forfeiting possible step 715 rebound.
* **Governance Verdict:** **PRIMARY HIGH-ALPHA INTERVENTION FOR V42.**

---

### Rank 2: `TERMINAL_LIQUIDATE_FULL` (Action ID: 1)
* **Mechanic:** Liquidates 100% of marketable shed stock at steps 693–694.
* **Occurrence Count:** 210 legal opportunities in dataset.
* **Positive Count:** 99 (47.1% hit rate).
* **Mean Delta:** `+$27.4` | **Median Delta:** `$0.00` | **Max Delta:** `+$649.0`.
* **5th Percentile:** `-$241.0` | **95th Percentile:** `+$313.3`.
* **Rescues:** **3 confirmed match rescues**.
* **Casualties:** **0 casualties**.
* **Economic Preconditions:**
  1. `step == 694` or `step >= 714`.
  2. Shed inventory is small ($\le 4$ items), where dumping 100% does not exceed market absorption depth.
* **Known Failure Regimes:**
  - Large inventory ($> 10$ units) triggers internal price slippage, leading to a negative tail (P5 `-$241.0`).
* **Governance Verdict:** Permitted when shed stock is small; otherwise fallback to Partial Liquidation.

---

### Rank 3: `DEFER_EXPANSION_LOW_CASH` (Action ID: 9)
* **Mechanic:** Suppresses planned land expansion if liquid cash balance is dangerously low ($< \$1,500$).
* **Occurrence Count:** 82 opportunities.
* **Mean Delta:** `+$190.9` | **Casualties:** 0.
* **Economic Preconditions:** Cash $< \$1,500$ between steps 100 and 500.
* **Governance Verdict:** Protective capital safeguard.

---

### Rank 4: `SPOT_SELL_PEAK_MILK` & `SPOT_SELL_PEAK_WOOL` (Action IDs: 3 & 4)
* **Mechanic:** Selling Milk/Wool opportunistically when spot prices reach extreme historical peaks ($P \ge \$45$).
* **Positive Delta:** Produced isolated large gains up to `+$17,324.0` in runaway matches.
* **Fatal Weakness:** Created **4 combined casualties** (flipping baseline wins into losses) in narrow matches due to premature inventory exhaustion.
* **Governance Verdict:** **STRICTLY GATED.** Must only be triggered when Lower Confidence Bound $\hat{\mu} - 1.5 \hat{\sigma} > \$100$.

---

### Rank 5: `SPOT_SELL_PEAK_STRAWBERRY` (Action ID: 5)
* **Mechanic:** Selling Strawberries opportunistically midgame.
* **Mean Delta:** **`-$25.3`** | **P5 Downside:** `-$131.0` | **Hit Rate:** Only 2.6%.
* **Governance Verdict:** **HARD NEGATIVE.** Permanently masked out.
