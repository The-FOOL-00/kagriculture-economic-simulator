# V44 Baseline Loss Forensics & Recoverable Alpha Budget Report

**Document ID:** `research/v44/reports/V44_LOSS_FORENSICS.md`  
**Date:** 2026-09-25  
**Repository:** `The-FOOL-00/kagriculture-economic-simulator`  
**Artifact Path:** `research/v44/artifacts/loss_catalog.json`  
**Scope:** In-depth forensic reconstruction of V43 baseline losses across DEV training and audit seeds (`249635..249663`) against 4 league opponents (`E8_DMITRII`, `E2_A7`, `E0_V3`, `SYN_AGG`) in both seats.

---

## 1. Executive Summary

Across 64 tournament-scale match legs evaluated in our baseline audit, V43 demonstrated overwhelming dominance, winning **61 out of 64 legs (95.3% win rate)** with 0 casualties.

Only 3 match legs resulted in a negative terminal margin:
1. **Near-Tie Loss:** Seed `249657` vs `E2_A7` (Seat 0): Terminal deficit of **-$34.00**.
2. **Structural Deficit Loss:** Seed `249659` vs `E8_DMITRII` (Seat 0): Terminal deficit of **-$1,101.00**.
3. **Structural Deficit Loss:** Seed `249659` vs `E8_DMITRII` (Seat 1): Terminal deficit of **-$1,101.00**.

This forensic investigation reconstructs the exact **Alpha Entry Points** where these deficits originated, quantifies the recoverable margin budget, and identifies the non-terminal economic mechanisms required to rescue them.

---

## 2. Loss Catalog & Forensic Decomposition

| Seed | Opponent | Seat | Terminal Margin | Alpha Entry Point | Largest Deficit Expansion Interval | Max Interval Drop | Recoverable Budget | Recoverable % | Classification |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **249657** | `E2_A7` | 0 | **-$34.0** | **Step 440** | Steps 695–696 | $54.0 | **$34.0** | **100.0%** | `HIGHLY_RECOVERABLE` |
| **249659** | `E8_DMITRII` | 0 | **-$1,101.0** | **Step 180** | Steps 600–620 | $340.0 | **$515.1** | **46.8%** | `PARTIALLY_RECOVERABLE` |
| **249659** | `E8_DMITRII` | 1 | **-$1,101.0** | **Step 180** | Steps 600–620 | $340.0 | **$515.1** | **46.8%** | `PARTIALLY_RECOVERABLE` |

---

## 3. Deep Forensic Reconstructions

### Case 1: Seed 249657 vs `E2_A7` (Seat 0) — The Near-Tie Deficit
* **Terminal Margin:** -$34.00 (My Cash: $23,410 | Opp Cash: $23,444)
* **Alpha Entry Point:** **Step 440 (Phase 4)**. Up to Step 440, the margin fluctuated within $\pm \$15$.
* **Divergence Mechanism:** At Step 440, `E2_A7` performed an unmonitored tomato harvest and sold into an active Town Center demand tick (`step % 12 == 0`).
* **Deficit Expansion:** Between Steps 695 and 696, opponent liquidated residual shed commodities while V43 held back tranches.
* **Recoverability:** **100% Recoverable ($34.00 budget)**. Shifting 1 unit of milk/strawberry sale into the Step 440 town consumption tick flips this match into a clear win.

### Case 2: Seed 249659 vs `E8_DMITRII` (Seat 0 & 1) — Structural Midgame Deficit
* **Terminal Margin:** -$1,101.00 (My Cash: $18,920 | Opp Cash: $20,021)
* **Alpha Entry Point:** **Step 180 (Phase 2)**.
* **Divergence Mechanism:**
  * At Step 180, `E8_DMITRII` aggressively hired 4 additional farm hands (Fibonacci cost: $1, $1, $2, $3 = $7 total) and purchased an extra Cow, scaling early milk production.
  * In contrast, V43's baseline A7 delayed hiring, creating a permanent workforce capacity deficit.
  * Between Steps 600 and 620 (Phase 6), `E8_DMITRII` reached full shed saturation and sold into town shop ticks, expanding the deficit by $340.
* **Recoverability:** **46.8% Recoverable ($515.10 budget)**. Terminal liquidation alone cannot close an $1,100 gap. Rescuing this match requires **early workforce expansion** at Step 180 and **investment payback capping** before Step 600.

---

## 4. Recoverable Alpha Budget Summary

The total recoverable deficit across all audited baseline losses is **$1,064.20**:
1. **Near-Tie Deficits ($34.00):** 100% recoverable via small town shop arbitrage adjustments in Phase 4.
2. **Structural Midgame Deficits ($1,030.20):** Recoverable via early labor scaling in Phase 2 and pre-terminal investment cutoffs in Phase 6.

This proves that **new non-terminal alpha families are required** to unlock the remaining recoverable margin in Kagriculture.
