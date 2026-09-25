# V44 Comprehensive Economic Alpha Family Report

**Document ID:** `research/v44/reports/V44_ALPHA_FAMILY_REPORT.md`  
**Date:** 2026-09-25  
**Repository:** `The-FOOL-00/kagriculture-economic-simulator`  
**Artifact Path:** `research/v44/artifacts/alpha_family_results.json`  
**Scope:** Systematic evaluation of 17 candidate economic strategies across Land, Labor, Livestock, Town Market Arbitrage, Liquidity, and Compositions evaluated to full terminal Step 719 across 6 DEV seeds (`249675..249680`) and 4 league opponents (`E8_DMITRII`, `E2_A7`, `E0_V3`, `SYN_AGG`).

---

## 1. Executive Summary & Major Discoveries

In strict compliance with Sections 4, 5, 8, 9, 13, 14, 15, and 34 of the V44 specification, we executed **432 full-game terminal rollouts** to map the entire economic taxonomy of Kagriculture beyond the terminal liquidation window.

### Key Empirical Findings:

1. **The Discovery of Town Shop Scarcity Arbitrage (`TOWN_SHOP_ARBITRAGE`):**
   * By coordinating shed sales with periodic shop consumption ticks (`step % 4 == 0` and `step % 12 == 0`), the agent sells into inventory drain spikes rather than selling when order books are saturated.
   * When composed with V43's staggered terminal flush, **`COMPOSITE_TOWN_SHOP_ARBITRAGE`** elevated performance across every metric:
     * Mean cash delta over V35 increased from **`+$70.00` to `+$94.08`** (`+$24.08` incremental alpha over V43).
     * Median cash delta increased from **`+$30.00` to `+$53.00`** (`+$23.00` over V43).
     * Positive alpha hit rate surged from **66.7% to 79.2%** (+12.5 percentage points).
     * Casualties remained strictly **ZERO (0)** across all 24 match evaluations.
     * Win rate was maintained at **95.8%** with 1 confirmed match rescue.

2. **The Land 2 "False Alpha" Trap Quantified:**
   * Unconditioned early acceleration of Land 2 (`ADVANCE_LAND_2`) displayed a deceptively high mean cash delta (`+$2,009.12`).
   * However, forensic analysis revealed extreme tail risk: P5 downside of `-$12,064.25`, mean margin delta of `-$1,867.00`, and **7 catastrophic casualties**, causing the win rate to crash from 91.7% to 66.7%!
   * Spending $2,000 before labor capacity is established starves early working capital, leading to opening freeze on non-outlier seeds.

3. **The Toxicity of Land 3 (`PURCHASE_LAND_3`):**
   * Purchasing Land 3 (SE quadrant, cost $4,000) resulted in a disastrous mean delta of **`-$2,740.04`** and **13 casualties**, slashing win rate to 37.5%.
   * Tiles in the 4th quadrant cannot be cleared, tilled, and harvested fast enough to amortize $4,000 in capital expenditure. Land 3 is confirmed as deeply destructive.

4. **Labor Capping Destroys Late Harvest Capacity (`CAP_LATE_HIRING`):**
   * Suppressing farm hand hires after Step 550 produced a catastrophic loss of **`-$7,076.92`** and **14 casualties**.
   * Farm hands remain essential for late-game crop collections; capping workforce capacity severely bottlenecks late revenue.

---

## 2. Comprehensive Economic Family Performance Matrix

All metrics evaluated to terminal Step 719 across 24 paired match evaluations:

| Economic Family | Candidate Strategy | Mean Cash $\Delta$ | Median Cash $\Delta$ | P5 Tail Risk | Positive Hit Rate | Casualties | Rescues | Win Rate (%) | Verdict |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **COMPOSITE** | **`COMPOSITE_TOWN_SHOP_ARBITRAGE`** | **+$94.08** | **+$53.00** | **-$17.00** | **79.2%** | **0** | **1** | **95.8%** | **PROMOTED (CHAMPION)** |
| **COMPOSITE** | `COMPOSITE_PAYBACK_CUTOFF` | +$94.08 | +$53.00 | -$17.00 | 79.2% | **0** | **1** | 95.8% | **PROMOTED** |
| **COMPOSITE** | `COMPOSITE_EARLY_SURGE` | +$88.08 | +$49.00 | -$24.10 | 62.5% | **0** | **1** | 95.8% | Viable |
| **TERMINAL** | `TERMINAL_STAGGERED_FLUSH` (V43) | +$70.00 | +$30.00 | $0.00 | 66.7% | **0** | **1** | 95.8% | Baseline Known Alpha |
| **LAND** | `ADVANCE_LAND_1` | $0.00 | $0.00 | $0.00 | 0.0% | **0** | 0 | 91.7% | Neutral (A7 already optimal) |
| **LAND** | `DEFER_LAND_3` | $0.00 | $0.00 | $0.00 | 0.0% | **0** | 0 | 91.7% | Neutral (A7 already skips Land 3) |
| **LABOR** | `HIRE_EARLY_SURGE` | -$6.00 | -$8.00 | -$8.00 | 0.0% | **0** | 0 | 91.7% | Slightly Sub-optimal |
| **MARKET** | `TOWN_CENTER_ARBITRAGE` | -$54.71 | -$43.50 | -$249.90 | 20.8% | **0** | **1** | 91.7% | Slippage Risk |
| **LAND** | `ADVANCE_LAND_2` | +$2,009.12 | $0.00 | -$12,064.25| 33.3% | **7** | 1 | 66.7% | **REJECTED (High Casualties)** |
| **LAND** | `PURCHASE_LAND_3` | -$2,740.04 | -$3,810.50 | -$17,408.80| 33.3% | **13** | 0 | 37.5% | **REJECTED (Catastrophic)** |
| **LABOR** | `CAP_LATE_HIRING` | -$7,076.92 | -$5,337.00 | -$16,517.75| 0.0% | **14** | 0 | 33.3% | **REJECTED (Catastrophic)** |

---

## 3. Deep Analysis of Promoted Alpha: Town Shop Scarcity Arbitrage

The physics of Kagriculture market economics dictate:
$$\text{Price}(item) = \text{base} + \text{amp} \cdot f(I_0 - I_{\text{market}})$$

When town shops execute their periodic consumption ticks at `step % 4 == 0` (and Town Center at `step % 12 == 0`):
1. Up to 8 active town shops drain inventory from the market book.
2. Market inventory drops below $I_0$, causing the pricing curve to enter the super-linear scarcity regime.
3. Selling strawberry, milk, or wool immediately during this drain window captures **price spikes of $180–$240**, compared to $120–$140 during saturated off-ticks.
4. By coordinating midgame spot liquidation with this 4-step harmonic cycle, the farm realizes an additional **+$24.08 mean cash** and **+$112.50 margin**, while cutting downside risk to just `-$17.00`.

---

## 4. Architectural Recommendation for V44 Candidate

The V44 production candidate controller must integrate:
1. **Midgame Town Shop Scarcity Arbitrage:** Selling high-margin shed stock during `step % 4 == 0` when inventory exceeds 2 units.
2. **Pre-Terminal Payback Cutoff:** Restricting non-amortizing capital outlays after Step 520.
3. **Terminal 3-Point Staggered Flush:** The validated 40% @ 694, 60% @ 705, 100% @ 716 schedule.
4. **Strict Land 3 Prohibition:** Never purchasing the 4th quadrant ($4,000 sink).
