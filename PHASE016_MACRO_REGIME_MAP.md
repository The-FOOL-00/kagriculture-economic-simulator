# PHASE 016: V3 MACRO REGIME MAP & BOUNDARY TAXONOMY

**Phase**: 016 — Long-Horizon Macro-Aware Counterfactual & Regime-Transition Safety Rescue  
**Chassis Freeze Hash**: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` (`submission_Vj_kc_v3.tar.gz`)  
**Source of Truth**: Frozen V3 Source Code (`main.py`, `parent_v43.py`, C++ engine semantics)  

---

## 1. Executive Summary

This document establishes the official **Macro Regime Map** of the frozen V3 baseline chassis. Every entry is directly derived from the frozen V3 source code and empirically verified. 

In Kagriculture, an action's economic consequence is not confined to its immediate execution: changes to state variables ($\Delta\text{cash}$, $\Delta\text{inventory}$, $\Delta\text{workers}$) can trigger or inhibit hardcoded policy switches in V3's dynamic decision layers tens or hundreds of steps later.

---

## 2. V3 Macro Regime Table

| Regime Name | Source Component | Trigger Conditions | Observable State Monitored | V3 Policy Response | Downstream Economic Consequence | Escalation Required |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Budget Guard Regime** | `Chassis._budget_guard` (lines 750–800) | `step % 72 == 0` (Days 0, 3, 6, 9, 12, 15, 18, 21, 24, 27) | `money`, `shed`, `prices`, planned tape capex over $[t, t+72)$ | If $\text{shortfall} = \text{budget} - \text{cash} > 0$, adds forced emergency `SELL` orders (highest price first); moves sells before buys | Forces immediate liquidation of stored goods; alters future inventory and pricing | **YES** |
| **Sheep Expansion Regime** | `_v233_request` / `_v233_eligible` (lines 1940–2000) | Day 12 (`step == 288`), hour $\le 1$, quadrants `{'NW', 'NE', 'SW'}`, `YARN_STORE >= 2`, $\text{Wool} \ge 220$, $\text{Wheat} \le 45$ | `money >= budget + 3000` (approx. $\$10,000 - \$11,000$), tiles, shed sheep | Emits `[['BUY_LAND'], ['BUY_ANIMAL', 'SHEEP', 6], ['BUY_PRODUCT', 'WHEAT', 6], ['HIRE'], ['HIRE']]` | Expands into SE quadrant; acquires 6 sheep; diverts 2 workers from crop farming to sheep maintenance | **YES** |
| **Tomato Capex Regime** | `_v219_request` / `_v219_qualifies` (lines 1240–1330) | Day 18 (`step == 432`), hour $\le 3$, quadrants `{'NW', 'NE', 'SW'}`, $\ge 3$ pizza/farmers shops, $\text{Tomato} \ge 20$ | `money >= 12000`, tomato seeds/shed/tiles == 0 | Emits `[['BUY_LAND'], ['BUY_SEED', 'TOMATO', 10], ['BUY_PRODUCT', 'FERTILIZER', Q], ['HIRE' x count]]` | Buys land; purchases 10 tomato seeds; hires 1–3 additional field hands; commits to intensive multi-day watering tour | **YES** |
| **Cow/Milk Adaptation Regime** | `_v231_controller` (lines 1530–1620) | Steps 216..227, $\ge 3$ shops unlocked, $\ge 2$ milk shops, no yarn store, $\text{Milk} \ge \text{Wool}$, cows $\ge 4$ | `market` animal orders, `shed`, `inventories` | Replaces `SHEEP` order with `COW` order; updates worker pickup/place routines to cows; manages milk sales | Switches animal husbandry path from wool to dairy | **YES** |
| **Day-End Storage Guard** | `Chassis._room_guard` (lines 800–850) | Hour 23 (`step % 24 == 23`) | Total projected shed inventory $> 99$ after worker drop | Adds forced `SELL` orders for items without future planned sales, then highest price | Prevents inventory destruction from shed overflow | **YES** |
| **Sale-Advance Regime** | `advance_sales` (`main.py` lines 180–240) | Step $\% 24 \ne 23$, step $< 718$, shed holds `PREMIUM` items | Shed inventory of `STRAWBERRY`, `WOOL`, `EGG`, `MILK`, `MELON`, `CARROT`, `TOMATO` | Pre-sells future tape sales (from $t+1, t+2$) immediately to capture pre-impact pricing | Shifts sale timing forward; alters cash and shed state for subsequent steps | **YES** |
| **Market Frontloading** | `frontload` (`main.py` lines 120–170) | Step has $\ge 2$ market orders | `money`, `shed_total`, `market.inventory`, hires | Reorders `SELL` orders ahead of `BUY` orders if solo simulation confirms full execution | Captures superior clearing prices before opponent orders execute | **NO** (handled locally) |
| **Terminal Liquidation** | `Chassis._terminal_liquidation` (lines 895–905) | Step $\ge 718$ | All shed inventory | Replaces all market orders with mass `SELL` of entire shed | Converts all remaining assets to cash for final scoring | **YES** |
| **Grain Supply Guard** | `_r97_supply` / `_r97_budget` (lines 2740–2850) | Animals on farm requiring feeding | `shed['WHEAT']`, prices | Reserves wheat; inserts `BUY_PRODUCT WHEAT` if grain stock is below threshold | Protects livestock from starvation; consumes cash and market order slots | **YES** |
| **Seed Budget Regime** | `_r124_seed_budget` / `_r148_seed_prefund` (lines 2880–2920, 3260–3300) | Day 1 opening / seed purchase turns | `money`, `shed` | Ensures cash reserve is preserved for essential planting seeds; forces pre-funding if deficit | Preserves early crop planting schedule | **YES** |

---

## 3. Discontinuity Trigger Analysis

### 3.1 The Cash-Induced Policy Bifurcation
The most severe failure mode observed in Phase 015 is the **Cash-Induced Capital Expenditure Trap**:
```text
Candidate Tranche Sale
         │
         ▼
+$150 - $500 Immediate Liquidity Injection
         │
         ▼
Cash enters [$10,000 - $12,000] Range at Step 288 (Day 12) or Step 432 (Day 18)
         │
         ▼
V3 Macro Gate Passes: `farm['money'] >= budget + 3000` (Sheep) or `>= 12000` (Tomato)
         │
         ▼
V3 purchases Land ($4,000) + Livestock/Seeds + Hires 2-3 Workers
         │
         ▼
Worker Obligations Multiply: Feeding, Watering, Pasturing, Milking
         │
         ▼
Workers diverted from high-value crop harvesting (Melon, Strawberry)
         │
         ▼
Mass crop rot / lost harvest revenue
         │
         ▼
Terminal Score Crashes by -$40,000 to -$87,000 USD
```

### 3.2 The Market Order Slot Starvation Failure
A secondary failure mode discovered during audit is **Market Queue Truncation**:
- V3 relies on specific atomic order types (`HIRE`, `BUY_LAND`, `BUY_ANIMAL`).
- In Phase 015, order synthesis partitioned orders into `startswith("BUY")` and `== "SELL"`, silently dropping `HIRE` (Step 195 on Seed 249276).
- Dropping a `HIRE` permanently reduces the farm's workforce by 1 hand for all future turns, causing compounding labor starvation.

---

## 4. Architectural Requirements for Escalation

To prevent these failure modes, the AEC evaluation pipeline must satisfy:
1. **Regime Boundary Probing**: Before committing any candidate, check if candidate state $S'$ differs from baseline $S$ in cash, shed inventory, or worker allocations in proximity to any active regime boundary.
2. **Escalated Continuation Horizon**: If proximity or threshold crossing is detected, escalate horizon $H$ to encompass the boundary (e.g. next 72-turn block boundary, or Day 12/Day 18 gates).
3. **Dynamic Frozen V3 Continuation**: Simulate the continuation using the actual frozen V3 agent closure on simulated observations, not static route tapes.
4. **Causal Attribution Decomposition**: Record direct intervention value vs macro-induced V3 continuation delta.
