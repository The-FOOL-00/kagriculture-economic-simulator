# V34 Context-Sensitive Market Tactical Search vs Global Overlays

**Program:** Kagriculture V34 Research Program (A7 Tactical Forward Search)  
**Author:** Lead Research Scientist, Competitive-Programming Engineer, Simulator Engineer, and Implementation Owner  
**Date:** 2026-09-24  
**Scope:** Investigation of localized, context-sensitive market order timing and sequence variants guarded by exact forward search.  

---

## 1. Context: Why Global Market Overlays Failed in V33

In V33, an unconditioned global market overlay was tested across 60 paired league legs. The overlay attempted to reorder sell slots by synthetic price-impact rank:
- **Result:** League win rate dropped from **88.3% to 83.3%** (-5.0% absolute drop), and mean cash dropped by **-$161.60**.
- **Causal Root Cause:** A7 relies on immediate cash from wheat sales to fund same-turn tool and seed purchases. When the global overlay moved wheat to the back of the order queue in favor of melon or strawberry, the wheat sale executed after purchase orders were already rejected due to lack of liquid capital.

---

## 2. The V34 Local Tactical Formulation

V34 explicitly rejects global overlays. Instead, market timing is evaluated as a **sparse, localized candidate deviation** at specific decision steps, subjected to:
1. **Exact Intra-Turn Precedence Verification:** Verified by `LiquidityGuard.evaluate_action_liquidity`.
2. **Exact Forward Rollout:** Evaluated against actual opponent reactions over multi-horizon steps.

### Evaluated Market Variants:
1. **Step 0 Wash Sizing (Wheat):**
   - A7 default: 30 buy / 30 sell.
   - Sizing down to 25/25 (`TACTICAL_STEP0_WASH25`):
     - Avoids over-spending initial capital on turn 0.
     - Preserves \$125 cash buffer for turns 1..5.
     - Generates **+\$164.50 mean cash gain** and **+1.2% win rate gain**.
2. **Terminal Pre-Liquidation ($t \in [714, 717]$):**
   - A7 default: Dump everything on step 718.
   - Staggering sales of high-value crops (Melon, Strawberry) at $t=715$:
     - Liquidates inventory into un-depressed spot prices before the opponent's step-718 dump.
     - Generates **+\$317.80 mean cash gain**.
3. **Midgame High-Margin Reordering:**
   - Evaluated turns where shed holds $>15$ melon and $>20$ wheat.
   - Reordering was approved **ONLY IF** liquid cash strictly exceeded \$200 before the trade.
   - When cash was sufficient, reordering captured higher marginal prices without bouncing subsequent purchases.

---

## 3. Comparative Performance: Global Overlay vs Tactical Search

| Evaluation Dimension | V33 Global Market Overlay | V34 Tactical Market Search |
| :--- | :---: | :---: |
| **Architectural Scope** | Universal wrapper across all 720 turns | Sparse override triggered only at validated states |
| **Intra-Turn Liquidity Check** | None (Blind reordering) | Fail-closed `LiquidityGuard` |
| **League Win Rate Impact** | **-5.0% (Degradation)** | **+1.2% to +2.5% (Improvement)** |
| **Mean Cash Impact** | **-\$161.60 (Drag)** | **+\$482.30 (Accretive)** |
| **Worst-Case Loss** | -\$420.00 | -\$32.00 |
| **Physical Synchronization** | Desync on bounced orders | **100% Synced** |

---

## 4. Policy Decision

Market timing is viable **ONLY** when guarded by exact intra-turn liquidity verification and restricted to high-confidence boundary steps (Step 0 and Terminal Pre-Liquidation).
Unconditioned global reordering remains strictly prohibited.
