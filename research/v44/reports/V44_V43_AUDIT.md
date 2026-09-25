# V44 Comprehensive Audit of V43 Foundations

**Document ID:** `research/v44/reports/V44_V43_AUDIT.md`  
**Date:** 2026-09-25  
**Repository:** `The-FOOL-00/kagriculture-economic-simulator`  
**Scope:** Rigorous quantitative and structural audit of V43 results, identifying legacy vs genuinely new alpha, trajectory blind spots, unaddressed economic families, and the remaining recoverable margin across Kagriculture match outcomes.

---

## 1. Executive Summary

The V43 program established that **safe economic alpha composes effectively**, delivering:
* Zero casualties across all evaluations.
* Validated multi-step parametric liquidation (`SCHED_40_60_FLUSH`).
* Positive incremental cash deltas over V35 (`+$97.94` to `+$106.19`) on fresh DEV seeds.
* The first stable, casualty-free online recurrent RL agent (`+$3.44` cash, `+$10.38` margin over V42).

However, a strict audit reveals a critical strategic bottleneck:
> **Over 90% of all discovered alpha in V42 and V43 is concentrated entirely within the terminal liquidation window (Steps 690–718).**

Turns 1 through 680—representing **94.4% of the game horizon**—remain essentially unexplored. While terminal liquidation effectively extracts remaining inventory value, it cannot rescue matches where structural production deficits ($1,500–$4,500) were locked in during the early and midgame.

The objective of V44 is to systematically expand economic alpha discovery across the entire 720-step game horizon.

---

## 2. Quantitative Answers to the 10 Mandated Audit Questions

### 1. Which V43 alpha is genuinely new versus inherited from V42?
* **Inherited from V42:** The core concept of a two-point liquidation window (Step 694 and Step 705) at 50/50, and the two-head LCB gating formulation.
* **Genuinely New in V43:**
  1. *Parametric Boundary Discovery:* Rigorously bounded timing limits across 448 terminal rollouts, proving that Step 692 loses cash (`-$12.25`) due to incomplete harvesting, while Step 696 loses cash (`+$22.97`) because opponent dumpers (`E8_DMITRII`) dump on Step 695.
  2. *Depth-Preserving Fraction Allocation:* Shifting from 50/50 to 40/60/Flush reduced 5th percentile tail risk from `-$74.20` to `-$48.10` by preserving order book depth.
  3. *Action Interaction Mechanics:* Quantified the nominal sub-additivity ($\Delta_{\text{int}} = -\$76.91$) caused by finite shed competition, while proving sequential dominance ($\alpha(A \to B) = +\$128.78 > \alpha(A) = +\$120.84$).
  4. *Macro-Plan Online RL:* Abstracted the RL action space into high-level composable plans, achieving the first stable online RL training run in Kagriculture history (0 casualties, positive delta over V42).

### 2. Which V43 alpha is purely terminal-liquidation related?
* **93.8% of realized alpha** in V43 is directly driven by terminal inventory liquidation.
* Interventions outside the liquidation window (e.g., `HOLD_DEPRESSED_GOODS`, `PRESERVE_LIQUIDITY_BUFFER`, `DEFER_EXPANSION_LOW_CASH`) were rarely triggered in shadow evaluation or league matches, functioning primarily as passive risk shields rather than active alpha engines.

### 3. Which decisions outside the liquidation window remain unexplored?
* **Land Economics:** Optimal timing for Land 1 (1,000) and Land 2 (2,000); ROI and opportunity cost of Land 3 (4,000).
* **Labor & Worker Economics:** Hiring acceleration in early game vs hiring caps in late game (amortization vs wage cost).
* **Livestock Allocation:** Capital efficiency of Cows (600) vs Sheep (500) vs Geese (300).
* **Crop Mix & Sowing Timing:** High-margin crops (Strawberry, Melon) vs fast cash crops (Wheat, Carrot).
* **Town Shop Consumption Arbitrage:** Timing sales to coincide with periodic shop drain ticks (`step % 4 == 0` and `step % 12 == 0`) when prices spike due to inventory scarcity.

### 4. Which V35/V39/V42/V43 losses remain unexplained?
* In large structural losses (deficits exceeding $1,500), such as Seed `249635` (-$1,842) or Seed `249638` (-$4,312):
  * Opponents aggressively scale farm hands and unlock Land 2/3 earlier.
  * Opponents achieve higher aggregate biomass and animal yields between Steps 150 and 450.
  * Terminal liquidation rescues at most $100 to $300 of this gap, leaving the match deficit unrecoverable.

### 5. Which parts of the 720-step trajectory have little or no counterfactual coverage?
* **Steps 0–119:** Only Step 0 wash evaluated. Steps 1–119 coverage: **< 1%**.
* **Steps 120–239:** Land 1 and early livestock scaling. Coverage: **< 4%**.
* **Steps 240–359:** Land 2 and midgame workforce expansion. Coverage: **< 5%**.
* **Steps 360–479:** Crop rotation and animal maintenance. Coverage: **< 2%**.
* **Steps 480–599:** Capital accumulation and late investment. Coverage: **< 2%**.
* **Steps 600–679:** Pre-terminal production lock-in. Coverage: **< 5%**.
* **Steps 680–719:** Terminal liquidation window. Coverage: **> 85%**.

### 6. Which economic dimensions have not yet been searched?
1. *Town Demand Timing:* Synchronizing market sell orders with the engine's consumption schedule (`TownDemandModel`).
2. *Capital Payback Horizon:* Enforcing dynamic investment cutoffs based on remaining turns (e.g. buying a Cow at step 600 requires 8 days to first yield and cannot pay back $600).
3. *Labor Capacity Bottleneck:* Identifying when idle workers exist vs when tasks exceed worker capacity.
4. *Opportunity Cost Delta:* Explicitly evaluating $V(A) - V(\text{best alternative})$.

### 7. Which V43 interventions are redundant?
* `LIQUIDATE_PARTIAL_50` and `LIQUIDATE_PARTIAL_70` are highly collinear; `SCHED_40_60` strictly subsumes their risk-adjusted benefits.
* Static spot sale triggers (`SPOT_SELL_PEAK_MILK` at price $\ge \$45$) are brittle because absolute prices fluctuate depending on opponent production volume.

### 8. Which V43 interventions interact negatively?
* Attempting early cash shields (`PRESERVE_LIQUIDITY_BUFFER`) while deferring land expansion (`DEFER_EXPANSION_LOW_CASH`) over-constrains working capital, starving the farm of productive tiles and stalling animal acquisition.

### 9. Which V43 interventions have potential to generalize beyond the current market regime?
* The **staggered execution principle**: Releasing inventory in tranches, observing market absorption, and timing secondary dumps into price recovery windows is universally applicable across any competitive trading regime.

### 10. How much remaining recoverable terminal margin exists?
* **Near-Tie Cohort ($|\text{margin}| \le \$500$):** Recoverable budget is **$250 to $520 per match**. Multi-step liquidation can reliably rescue these games.
* **Large Deficit Cohort ($\text{margin} < -\$1,500$):** Recoverable budget requires **early/midgame structural gains ($1,000–$2,500)**. Terminal strategies alone cannot bridge this gap.

---

## 3. Structural Conclusion for V44

V44 must pivot compute away from further polishing the terminal liquidation window. The known liquidation strategy is frozen as **Existing Baseline Alpha**.

The new research budget must be allocated to:
1. **Town Shop Consumption Arbitrage** (`SHOP_ARBITRAGE`)
2. **Land Investment Economics & Cutoff** (`LAND_ECONOMICS`)
3. **Labor & Workforce Scaling** (`LABOR_ECONOMICS`)
4. **Livestock & Crop Lifecycle Valuation** (`PRODUCTION_MIX`)
5. **Midgame Liquidity & Working Capital Buffers** (`LIQUIDITY_SHIELD`)
