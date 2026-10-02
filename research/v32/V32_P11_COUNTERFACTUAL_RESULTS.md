# V32 P11 — COUNTERFACTUAL REPORT: ISOLATED PHYSICAL & MARKET INTERVENTIONS
**Phase:** V32 P11  
**Date:** 2026-09-23  
**Status:** COMPLETE — COUNTERFACTUAL DIVERGENCES FULLY AUDITED  

---

## 1. Experimental Arms

We evaluated four isolated counterfactual treatments against the baseline A7 continuation:
1. **Arm 0 (Baseline A7):** Static route continuation + automated terminal liquidation (`SELL 1000` on 713–718).
2. **Arm 1 (Unconstrained Physical Search / Dmitrii Mirror):** Monte Carlo physical search optimizing `money + inventory_value` without cargo-stranding protection.
3. **Arm 2 (Cargo-Protected Physical-Only Search):** Bounded exact physical search with strict cargo protection (workers holding cargo $\ge \$10$ cannot detour). Market orders fixed to A7 baseline.
4. **Arm 3 (Physical Search + Terminal Market Monetization):** Cargo-protected physical search plus custom step-718 market liquidation for newly extracted goods.

---

## 2. Counterfactual Results (Seed 249677 vs Dmitrii)

| Step | Arm 0 (A7 Baseline) | Arm 1 (Unconstrained Search) | Arm 2 (Cargo-Protected) | Arm 3 (Physical + Market) |
| :---: | :---: | :---: | :---: | :---: |
| **712** | $89,992.00 | $89,992.00 | $89,992.00 | $89,992.00 |
| **713** | $90,187.00 | $90,058.00 (-$129) | $90,187.00 ($0) | $90,187.00 ($0) |
| **714** | $90,187.00 | $90,190.00 (+$3) | $90,187.00 ($0) | $90,187.00 ($0) |
| **715** | $90,187.00 | $90,190.00 (+$3) | $90,187.00 ($0) | $90,187.00 ($0) |
| **716** | $90,834.00 | $90,190.00 (-$644) | $90,834.00 ($0) | $90,834.00 ($0) |
| **717** | $91,153.00 | $90,820.00 (-$333) | $91,153.00 ($0) | $91,153.00 ($0) |
| **718** | $91,491.00 | $90,986.00 (-$505) | $91,491.00 ($0) | $91,491.00 ($0) |
| **719** | **$92,592.00** | **$92,381.00 (-$211)** | **$92,592.00 ($0)** | **$92,592.00 ($0)** |
| **Status** | **INCUMBENT** | **FATAL REGRESSION** | **FAIL-CLOSED ABSTAIN** | **FAIL-CLOSED ABSTAIN** |

---

## 3. Forensic Anatomy of the -$211.00 Arm 1 Regression

In Arm 1, the planner detoured Hand 5 (carrying 8 Milk, 4 Wool) and Hand 1 (carrying 6 Carrots, 2 Wheat) to harvest adjacent cows and pick up fertilizer. 

At Step 718:
- **Baseline A7 Carried:** 2 workers holding 9 items. All other high-value items were safely deposited in the shed and sold in the step 718 market.
- **Arm 1 Carried:** 6 workers holding **34 items** (12 Milk, 6 Carrots, 7 Wheat, 4 Wool, 1 Egg, 6 Fertilizer) in their pockets.
- Because step 718 is the final market turn, these 34 items could not be sold from the shed.
- At step 719, the match terminated. The 34 items yielded **$0.00 cash**, resulting in an irrevocable **-$211.00 cash destruction**.

---

## 4. Market Monetization Evaluation (EXP-P11-03)

In Arm 3, we evaluated whether recomputing market liquidation at step 718 could monetize additional physical value:
- In A7 baseline, step 718 market orders are already:
  `[['SELL', 'MILK', 1000], ['SELL', 'WHEAT', 1000], ['SELL', 'CARROT', 1000], ['SELL', 'TOMATO', 1000], ['SELL', 'STRAWBERRY', 1000], ['SELL', 'MELON', 1000], ['SELL', 'EGG', 1000], ['SELL', 'WOOL', 1000], ['SELL', 'FERTILIZER', 1000]]`
- A7 already submits `SELL 1000` for every single commodity in the game.
- Any item that physically reaches the shed at or before step 718 is **already 100% liquidated** by A7 baseline.
- Therefore, market monetization adds exactly **$0.00** incremental value.

---

## 5. Conclusion

- Physical rerouting without cargo protection causes severe tail regressions (-$211.00).
- Physical rerouting with cargo protection safely abstains ($0.00 delta) because baseline labor allocation is already saturated.
- Market monetization is completely redundant with A7's existing 100% liquidation policy.
