# V42 Forensic Diagnosis of V41 Empirical Outcomes

**Document ID:** `research/v42/reports/V42_V41_DIAGNOSIS.md`  
**Date:** 2026-09-25  
**Repository:** `Kagriculture`  
**Mission:** Comprehensively diagnose where V41's incremental alpha disappeared and establish the empirical foundation for V42.

---

## 1. Executive Summary

The V41 research cycle achieved an essential milestone: **total elimination of casualties** (0 casualties / 96 tournament legs vs. 28 in V40) and preservation of the Golden Property ($a_t = 0 \implies \mathcal{A}_{\text{V41}} \equiv \mathcal{A}_{\text{V35}}$). However, across 96 paired match legs on fresh DEV seeds (`249685..249688`), V41 produced:
* **Mean Cash Delta:** `-$38.62` (Offline Scorer), `-$47.16` (Online PPO), `-$104.06` (Deterministic Library).
* **Rescues:** `0` (Win rate remained identical to baseline at 100.0%).
* **Incremental Alpha:** Non-positive across the tournament population.

This report provides the mathematical and empirical autopsy of V41, answering the 10 mandated diagnostic questions via exact simulator rollouts.

---

## 2. The 10 Diagnostic Questions Answered

### Question 1: Why did the deterministic intervention library fail to create measurable rescues?
**Finding:**
1. **Saturation of Baseline Win Rate:** On the chosen DEV seeds (`249685..249688`), V35 already won 100% of matches against all four league opponents (`E8_DMITRII`, `E2_A7`, `E0_V3`, `SYN_AGG`). By definition, a rescue requires a baseline loss ($\text{BaseWin} = \text{False} \land \text{CandWin} = \text{True}$). When baseline win rate is 100%, rescue count is mathematically bounded at 0.
2. **Execution Timing Rigidity:** Deterministic rules triggered blindly on static price thresholds (e.g. Milk $\ge \$35$) without modeling the opponent's selling schedule or market price trajectory.
3. **Net Negative Aggregation:** In 10 out of 16 matches, Ladder C produced negative cash deltas (down to `-$516.00`), eroding more capital in losing interactions than it gained in winning ones (`+$67` to `+$226`).

---

### Question 2: Why did spot sales produce negative aggregate delta?
**Finding:**
1. **Opponent Sensitivity:** Against passive/static bots (`E0_V3`, `E2_A7`), spot sales produced positive mean delta (`+$94.00` and `+$42.50`). However, against active market participants (`E8_DMITRII` and `SYN_AGG`), spot sales produced severe negative delta (`-$143.62` and `-$147.38`).
2. **Premature Inventory Depletion:** V35's choreography plans bulk sales timed with harvest cycles to maximize revenue. Intervening with premature spot sales (e.g., selling 2 Milk at step 340) captures immediate cash (`+$60`) but depresses the commodity market price for subsequent native sales, or depletes goods before higher peak pricing arrives later in the game.
3. **Strawberry Vulnerability:** In the counterfactual dataset (1,327 samples), `SPOT_SELL_STRAWBERRY` exhibited a devastating negative mean delta of `-$54.48` and a 5th-percentile downside of `-$445.20`. Strawberries spoil slowly but have high price elasticity; selling them prematurely consistently harmed long-term compounding.

---

### Question 3: How often was `MIDGAME_LAND_EXPAND_F5` actually available?
**Finding:**
* Out of 1,327 sampled decision points in V41, `MIDGAME_LAND_EXPAND_F5` was legally masked in **229 states** (17.3% of turns).
* However, out of those 229 legal opportunities, it was optimal in only **13 states** (5.7% of legal occurrences, 0.98% of all states).
* In the remaining 216 states where it was legally permitted, executing it resulted in an immediate catastrophic cash loss of `-$4,000.00` (Mean delta across all legal occurrences: `-$2,858.18`).

---

### Question 4: Across which economic regimes was it positive?
**Finding:**
In the V41 24-step counterfactual dataset, `MIDGAME_LAND_EXPAND_F5` appeared positive **only** when:
1. Liquid cash exceeded `$12,000` at steps 280–312.
2. Exactly 3 quadrants were currently unlocked ($Q = 3$).
3. The opponent was non-aggressive in land acquisition.
4. **CRITICAL DISCOVERY:** It appeared positive *only because the counterfactual rollout horizon was truncated at 24 steps*!

---

### Question 5: Did the +$3,385 result survive additional seeds?
**Finding: NO. It was an artifact of horizon truncation.**
When rolled out to the true terminal state (Step 719) across 18 game branches (seeds `249635..249644` vs `E8_DMITRII`, `E0_V3`, `SYN_AGG`):
* **24-Step Truncated Delta:** Mean `-$2,132.11` (with rare transient spikes of `+$3,384.00`).
* **True Terminal Cash Delta (Step 719):** Mean **`-$12,341.06`**.
* **True Terminal Margin Delta (Step 719):** Mean **`-$7,699.17`**.
* **Casualties Created:** In 4 out of 18 matches, `MIDGAME_LAND_EXPAND_F5` converted a **V35 Baseline Win into a Loss**!
  - Seed 249637 vs `E0_V3`: Baseline won by `+$512`; Branch 9 **lost by -$5,951**!
  - Seed 249638 vs `E8_DMITRII`: Baseline won by `+$7,462`; Branch 9 **lost by -$2,052**!
  - Seed 249638 vs `E0_V3`: Baseline won by `+$586`; Branch 9 **lost by -$3,866**!
  - Seed 249644 vs `E0_V3`: Baseline won by `+$685`; Branch 9 **lost by -$12,821**!
* **Losses Converted to Wins:** Exactly **0 / 18**.
* **Causal Explanation:** Buying land without worker chore replanning consumes `$4,000` in working capital, alters land pricing dynamics, and leaves acreage unutilized while starving other budget guards.

---

### Question 6: Which interventions have positive median delta?
**Finding:**
Across the 1,327 V41 counterfactual transitions:
* `TERMINAL_LIQUIDATE_694` (Action 1): **Median Delta `+$20.50`**, Mean `+$49.73`, Positive in 59/90 occurrences (65.6%).
* All other interventions have a **Median Delta of `$0.00`** or negative (`-$4,000.00` for midgame expansion).

---

### Question 7: Which have positive lower-tail delta?
**Finding: NONE.**
* Every non-baseline intervention has a negative 5th-percentile (P5) lower tail:
  - `TERMINAL_LIQUIDATE_694`: P5 = `-$221.65`
  - `SPOT_SELL_MILK`: P5 = `-$45.00`
  - `SPOT_SELL_WOOL`: P5 = `-$23.00`
  - `SPOT_SELL_STRAWBERRY`: P5 = `-$445.20`
  - `HOLD_DEPRESSED_GOODS`: P5 = `-$19.00`
  - `MIDGAME_LAND_EXPAND_F5`: P5 = `-$4,000.00`
* **Strategic Implication for V42:** Because every action carries downside tail risk, an unhedged policy will inevitably degrade tournament score. V42 **must** employ Lower Confidence Bound (LCB) gating:
  $$\text{Score}(s, a) = \hat{\mu}_{\Delta}(s, a) - \beta \cdot \hat{\sigma}(s, a)$$
  intervening only when the lower bound of expected alpha is strictly positive.

---

### Question 8: Which are positive only in already-winning games?
**Finding:**
* Opportunistic spot sales of Milk (`SPOT_SELL_MILK`) and Wool (`SPOT_SELL_WOOL`) at steps 250–350 only succeed when our farm has massive capital dominance ($>\$100,000$ terminal cash) where price slippage does not affect the outcome.
* In tight games (margin $<\$2,000$), spot sales trigger market feedback loops that erode the narrow lead.

---

### Question 9: Which are specifically useful in narrow losses?
**Finding:**
* **General Terminal Liquidation (Steps 690–710):** In narrow losses (margin between `-$100` and `-$1,000`), V35 leaves `$1,500` to `$3,500` of unliquidated inventory in the shed (Strawberries, Milk, Wool, Melons). Liquidating these goods before episode end provides immediate cash that can flip narrow defeats into wins.
* **Partial Liquidation:** Dumping 100% of shed inventory in one step crashes the spot price. Liquidating partially across steps 692, 694, and 705 captures maximum aggregate revenue without collapsing the price.

---

### Question 10: Which interventions have the highest expected opportunity value?
**Finding:**
1. **Dynamic Terminal Liquidation (Full & Partial):** Expected opportunity value: `+$150` to `+$450` per eligible game, with high win-conversion potential in near-tie matches.
2. **Selective Peak Milk Liquidation:** Expected opportunity value: `+$50` to `+$200`, but strictly conditional on opponent market passivity ($P \ge \$100$).
3. **Abstention (Golden Property):** In 88.8% of turns, $a=0$ has the highest expected opportunity value because the incumbent chore schedule is mathematically superior to any greedy deviation.

---

## 3. Direct Architectural Directives for V42

Based on this diagnosis, V42 must enforce five non-negotiable architectural changes:

1. **Full Terminal Rollout for Midgame Actions:** Never evaluate a macro action with a 24-step horizon. Counterfactual mining must evaluate true terminal margin at Step 719 to prevent timing artifacts.
2. **Disqualify Midgame Land Expansion without Dedicated Replan:** Blind `BUY_LAND` at step 280 is a catastrophic negative-alpha trap (Mean `-$12,341` cash delta, 4/18 win-to-loss casualties). It must be masked out unless accompanied by a verified physical farming schedule.
3. **Introduce Partial Terminal Liquidation:** Add discrete partial liquidation primitives (e.g. sell 50% vs sell 100%) to mitigate price crash dynamics.
4. **Target Narrow Losses & Near-Ties:** Construct an active mining dataset specifically over seeds where V35 loses or wins narrowly ($|\text{margin}| \le \$3,000$).
5. **Lower Confidence Bound (LCB) Risk Gating:** Gating must penalize variance to guarantee zero negative-alpha interventions.
