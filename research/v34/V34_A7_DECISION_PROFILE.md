# V34 A7 Decision Profile & Empirical Choreography Analysis

**Program:** Kagriculture V34 Research Program (A7 Tactical Forward Search)  
**Author:** Lead Research Scientist, Competitive-Programming Engineer, Simulator Engineer, and Implementation Owner  
**Date:** 2026-09-24  
**Dataset:** `a7_decision_trace.jsonl` (7,190 observed decision points across 10 complete 720-step matches)  
**Evaluated Cohort:** DEV seeds (`249675..249676`), Seat 0 and Seat 1, against League Opponents (`E8_DMITRII`, `E1_V22R1`, `V54`, `SYN_AGG`)  

---

## 1. Executive Summary & Core Architectural Discoveries

Through observational tracing of 7,190 steps, A7's behavioral profile was characterized across physical choreography, capital allocation, market interactions, and timing sensitivities:

1. **Bimodal Action Structure:**
   - **41.9% of steps (3,010 / 7,190):** Pure physical maintenance (`NONE` market activity). Workers move, till, water, harvest, feed, or dig weeds with 100% duty cycle.
   - **58.1% of steps (4,180 / 7,190):** Market active steps, comprising `SELL_LOT` (36.2%), `BUY_SEED` (16.5%), `BUY_PRODUCT` (4.6%), and `HIRE` (0.8%).
2. **Extreme Liquidity Sensitivity:**
   - Across the trace, A7's liquid cash dropped to a **minimum of \$4.00**.
   - Working capital is managed with zero margin for error in the early-to-mid game ($t \in [10, 120]$). Any external intervention that delays cash realization by even a single turn risks bouncing hire orders, seed purchases, or daily wages.
3. **Five Distinct Strategic Phases:**
   - **Phase 0: Opening Hire & Setup ($t \in [0, 47]$):** Step 0 wheat wash (30/30), rapid hiring of 4 hands, initial seed purchases.
   - **Phase 1: Early Crop Scaling ($t \in [48, 239]$):** Dense single-quadrant monoculture planting, strict daily watering routines, zero land expansion capex.
   - **Phase 2: Midgame Production ($t \in [240, 479]$):** High harvest cadence, high inventory velocity, regular sales of crops.
   - **Phase 3: Late Harvest Conversion ($t \in [480, 679]$):** Sowing cutoff transitions; planting decreases as terminal horizon nears.
   - **Phase 4: Terminal Liquidation ($t \in [680, 719]$):** Complete farm liquidation, selling all shed inventories by step 718.

---

## 2. Quantitative Event & Phase Distribution

| Strategic Phase | Step Range | Total Steps Traced | % of Total | Dominant Action Types | Observed Cash Range |
| :--- | :---: | :---: | :---: | :--- | :---: |
| **Phase 0: Opening Hire** | 0 – 47 | 480 | 6.7% | `WASH30`, `HIRE`, `BUY_SEED` | \$4 – \$3,150 |
| **Phase 1: Crop Scaling** | 48 – 239 | 1,920 | 26.7% | `PLANT`, `WATER`, `SELL_LOT` | \$15 – \$18,400 |
| **Phase 2: Mid Production** | 240 – 479 | 2,400 | 33.4% | `HARVEST`, `SELL_LOT`, `BUY_SEED` | \$2,400 – \$65,200 |
| **Phase 3: Late Harvest** | 480 – 679 | 2,000 | 27.8% | `HARVEST`, `SELL_LOT` | \$25,000 – \$118,500 |
| **Phase 4: Terminal Dump** | 680 – 718 | 390 | 5.4% | `SELL_LOT`, `TERMINAL_DUMP` | \$85,000 – \$143,329 |
| **TOTAL** | **0 – 718** | **7,190** | **100.0%** | — | **\$4.00 – \$143,329.00** |

---

## 3. Market Interaction Taxonomy

A7 issues market actions in exactly four distinct modes:
1. **The Step 0 Wheat Wash:**
   `[["BUY_PRODUCT", "WHEAT", 30], ["SELL", "WHEAT", 30]]`
   - Purpose: Explores early shop mechanics and captures spread without moving inventory outside the shed.
2. **Scheduled Lot Sells:**
   - Frequency: Every 1 to 4 steps when inventory exceeds batch thresholds.
   - Sensitivity: Sells high-velocity staples first, ensuring liquidity is replenished before downstream orders execute.
3. **Emergency Budget Guard Sells:**
   - Triggers at step $t \pmod{72} == 0$.
   - Sells surplus shed stock to cover projected 72-tick operational expenses.
4. **Terminal Liquidation Dump:**
   - Triggers at $t \ge 718$. Sells 100% of remaining shed contents.

---

## 4. Key Implications for V34 Tactical Search

1. **Do Not Touch the 41.9% Maintenance Steps:**
   When A7 is moving, watering, or harvesting, changing physical movement paths creates severe resynchronization drag ($D_{\text{resync}} > 0$).
2. **Focus Forward Search on Economic Decision Points:**
   The highest exploitable leverage exists during market-active turns:
   - **Point A:** Step 0 wash sizing (evaluating 20, 25, 30, 35 units based on initial spot prices).
   - **Point B:** High-inventory sell ordering and timing (when multiple commodities are in shed).
   - **Point C:** Seed purchase timing (bulk vs just-in-time seed acquisition).
   - **Point D:** Late-game planting cutoff (avoiding seed expenditure on crops that cannot mature before $t=719$).
3. **Liquidity Guard Invariant:**
   Liquid cash must NEVER be allowed to drop below \$50.00 during early turns. Any tactical candidate that breaches this floor is immediately disqualified.
