# EXP-DEV-002 POSTMORTEM AUDIT: COMPARATIVE ANALYSIS TO EXP-DEV-001

**Experiment Identifiers**: `EXP-DEV-001` (Unhedged Dynamic Portfolio) vs `EXP-DEV-002` (Hedged Adaptive Portfolio)  
**Sample Cohort**: Identical 50 Discovery Seeds (`50000` to `50049`)  
**Evaluation Standard**: Paired Common Random Number (CRN) Counterfactual Analysis  
**Audit Date**: 2026-09-11  
**Auditor**: Antigravity Autonomous Pair Programmer (Comparative Audit Engine)  

---

## 1. Executive Summary

This audit performs an exact seed-by-seed comparison between `EXP-DEV-001` (which failed the lower-tail risk stop criterion due to an unhedged 13-tile Tomato substitution) and `EXP-DEV-002` (which introduced a 13-Strawberry bedrock floor and a 6-tile Tomato cap).

### Major Findings:
1. **Pervasive Identity (96.0% Invariant)**:
   - Across 48 of the 50 seeds, `EXP-DEV-001` and `EXP-DEV-002` produced **100.0% identical paired margins**.
   - 42 seeds produced exactly $0.00 (bedrock tie with `ClosedLoopAgentV2`).
   - 5 Carrot seeds produced identical gains (+192, +18, +146, +16, +22).
   - 1 Wheat seed produced an identical minor loss (-$11 on Seed 50017).
2. **The Two Divergent Seeds**:
   - The entire difference between the two experiments is localized to **Seed 50004** and **Seed 50018** (the only two seeds where Tomato mode was triggered).
   - **Seed 50018 (Demand Reversal World)**: Paired margin inverted from **-$2,388.00 to +$3,820.00** (a **+$6,208.00** positive swing), successfully removing catastrophic downside.
   - **Seed 50004 (Persistent Pizza World)**: Paired margin decreased from **+$15,264.00 to +$8,300.00** (a **-$6,964.00** reduction in captured surplus).
3. **Net Aggregate Tradeoff**:
   - The total margin sum across all 50 seeds was **+$13,259.00** in DEV-001 (mean +$265.18).
   - The total margin sum in DEV-002 was **+$12,503.00** (mean +$250.06).
   - DEV-002 generated **$756.00 less total cash** than DEV-001.
   - However, worst-case drawdown improved from **-$2,388.00 to -$11.00** (a 99.5% tail risk reduction).
   - **Conclusion**: DEV-002 successfully purchased catastrophic tail risk immunity at the cost of surrendering excess upside on persistent specialty worlds.

---

## 2. Seed-by-Seed Comparative Manifest (All 50 Discovery Seeds)

| Seed | EXP-DEV-001 | EXP-DEV-002 | Delta | Shop Pattern (Steps 72, 144) | Treatment Mode | Impact Category |
| :---: | :---: | :---: | :---: | :--- | :---: | :--- |
| **50000** | +0.00 | +0.00 | +0.00 | `PET_CAFE + YARN_STORE` | `YARN` | Bedrock tie preserved (+0.00) |
| **50001** | +192.00 | +192.00 | +0.00 | `PET_CAFE + PET_CAFE` | `CARROT` | Carrot gain retained (+0.00) |
| **50002** | +0.00 | +0.00 | +0.00 | `BRUNCH_SPOT + PIZZA_SHOP` | `STRAWBERRY` | Bedrock tie preserved (+0.00) |
| **50003** | +0.00 | +0.00 | +0.00 | `BRUNCH_SPOT + SMOOTHIE_SHOP` | `STRAWBERRY` | Bedrock tie preserved (+0.00) |
| **50004** | +15264.00 | +8300.00 | -6964.00 | `PIZZA_SHOP + PIZZA_SHOP` | `TOMATO` | **UPSIDE SURRENDERED / TRUNCATED** (-$6,964.00) |
| **50005** | +0.00 | +0.00 | +0.00 | `SMOOTHIE_SHOP + ICE_CREAM_SHOP` | `STRAWBERRY` | Bedrock tie preserved (+0.00) |
| **50006** | +0.00 | +0.00 | +0.00 | `ICE_CREAM_SHOP + PIZZA_SHOP` | `STRAWBERRY` | Bedrock tie preserved (+0.00) |
| **50007** | +0.00 | +0.00 | +0.00 | `FARMERS_MARKET + PET_CAFE` | `STRAWBERRY` | Bedrock tie preserved (+0.00) |
| **50008** | +18.00 | +18.00 | +0.00 | `BAKERY + PET_CAFE` | `CARROT` | Carrot gain retained (+0.00) |
| **50009** | +0.00 | +0.00 | +0.00 | `ICE_CREAM_SHOP + FARMERS_MARKET` | `STRAWBERRY` | Bedrock tie preserved (+0.00) |
| **50010** | +0.00 | +0.00 | +0.00 | `PET_CAFE + ICE_CREAM_SHOP` | `STRAWBERRY` | Bedrock tie preserved (+0.00) |
| **50011** | +0.00 | +0.00 | +0.00 | `PET_CAFE + FARMERS_MARKET` | `STRAWBERRY` | Bedrock tie preserved (+0.00) |
| **50012** | +0.00 | +0.00 | +0.00 | `SMOOTHIE_SHOP + PET_CAFE` | `STRAWBERRY` | Bedrock tie preserved (+0.00) |
| **50013** | +0.00 | +0.00 | +0.00 | `SMOOTHIE_SHOP + SMOOTHIE_SHOP` | `STRAWBERRY` | Bedrock tie preserved (+0.00) |
| **50014** | +0.00 | +0.00 | +0.00 | `PET_CAFE + SMOOTHIE_SHOP` | `STRAWBERRY` | Bedrock tie preserved (+0.00) |
| **50015** | +0.00 | +0.00 | +0.00 | `PET_CAFE + ICE_CREAM_SHOP` | `STRAWBERRY` | Bedrock tie preserved (+0.00) |
| **50016** | +0.00 | +0.00 | +0.00 | `ICE_CREAM_SHOP + BRUNCH_SPOT` | `STRAWBERRY` | Bedrock tie preserved (+0.00) |
| **50017** | -11.00 | -11.00 | +0.00 | `PIZZA_SHOP + BAKERY` | `WHEAT` | Minor wheat loss retained (+0.00) |
| **50018** | -2388.00 | +3820.00 | +6208.00 | `PIZZA_SHOP + PIZZA_SHOP` | `TOMATO` | **CATASTROPHIC RISK ELIMINATED** (+$6,208.00 swing) |
| **50019** | +0.00 | +0.00 | +0.00 | `BRUNCH_SPOT + BRUNCH_SPOT` | `STRAWBERRY` | Bedrock tie preserved (+0.00) |
| **50020** | +0.00 | +0.00 | +0.00 | `FARMERS_MARKET + ICE_CREAM_SHOP` | `STRAWBERRY` | Bedrock tie preserved (+0.00) |
| **50021** | +0.00 | +0.00 | +0.00 | `PET_CAFE + SMOOTHIE_SHOP` | `STRAWBERRY` | Bedrock tie preserved (+0.00) |
| **50022** | +0.00 | +0.00 | +0.00 | `YARN_STORE + PET_CAFE` | `YARN` | Bedrock tie preserved (+0.00) |
| **50023** | +146.00 | +146.00 | +0.00 | `PET_CAFE + PET_CAFE` | `CARROT` | Carrot gain retained (+0.00) |
| **50024** | +0.00 | +0.00 | +0.00 | `BAKERY + BRUNCH_SPOT` | `STRAWBERRY` | Bedrock tie preserved (+0.00) |
| **50025** | +0.00 | +0.00 | +0.00 | `YARN_STORE + SMOOTHIE_SHOP` | `YARN` | Bedrock tie preserved (+0.00) |
| **50026** | +16.00 | +16.00 | +0.00 | `PET_CAFE + PIZZA_SHOP` | `CARROT` | Carrot gain retained (+0.00) |
| **50027** | +0.00 | +0.00 | +0.00 | `ICE_CREAM_SHOP + FARMERS_MARKET` | `STRAWBERRY` | Bedrock tie preserved (+0.00) |
| **50028** | +0.00 | +0.00 | +0.00 | `BRUNCH_SPOT + FARMERS_MARKET` | `STRAWBERRY` | Bedrock tie preserved (+0.00) |
| **50029** | +0.00 | +0.00 | +0.00 | `BRUNCH_SPOT + YARN_STORE` | `YARN` | Bedrock tie preserved (+0.00) |
| **50030** | +0.00 | +0.00 | +0.00 | `FARMERS_MARKET + ICE_CREAM_SHOP` | `STRAWBERRY` | Bedrock tie preserved (+0.00) |
| **50031** | +0.00 | +0.00 | +0.00 | `PIZZA_SHOP + BRUNCH_SPOT` | `STRAWBERRY` | Bedrock tie preserved (+0.00) |
| **50032** | +0.00 | +0.00 | +0.00 | `PIZZA_SHOP + ICE_CREAM_SHOP` | `STRAWBERRY` | Bedrock tie preserved (+0.00) |
| **50033** | +0.00 | +0.00 | +0.00 | `BRUNCH_SPOT + PIZZA_SHOP` | `STRAWBERRY` | Bedrock tie preserved (+0.00) |
| **50034** | +0.00 | +0.00 | +0.00 | `BRUNCH_SPOT + BAKERY` | `STRAWBERRY` | Bedrock tie preserved (+0.00) |
| **50035** | +0.00 | +0.00 | +0.00 | `FARMERS_MARKET + YARN_STORE` | `YARN` | Bedrock tie preserved (+0.00) |
| **50036** | +0.00 | +0.00 | +0.00 | `YARN_STORE + SMOOTHIE_SHOP` | `YARN` | Bedrock tie preserved (+0.00) |
| **50037** | +22.00 | +22.00 | +0.00 | `PET_CAFE + PIZZA_SHOP` | `CARROT` | Carrot gain retained (+0.00) |
| **50038** | +0.00 | +0.00 | +0.00 | `YARN_STORE + SMOOTHIE_SHOP` | `YARN` | Bedrock tie preserved (+0.00) |
| **50039** | +0.00 | +0.00 | +0.00 | `ICE_CREAM_SHOP + PIZZA_SHOP` | `STRAWBERRY` | Bedrock tie preserved (+0.00) |
| **50040** | +0.00 | +0.00 | +0.00 | `BRUNCH_SPOT + BAKERY` | `STRAWBERRY` | Bedrock tie preserved (+0.00) |
| **50041** | +0.00 | +0.00 | +0.00 | `BRUNCH_SPOT + PIZZA_SHOP` | `STRAWBERRY` | Bedrock tie preserved (+0.00) |
| **50042** | +0.00 | +0.00 | +0.00 | `YARN_STORE + YARN_STORE` | `YARN` | Bedrock tie preserved (+0.00) |
| **50043** | +0.00 | +0.00 | +0.00 | `FARMERS_MARKET + BRUNCH_SPOT` | `STRAWBERRY` | Bedrock tie preserved (+0.00) |
| **50044** | +0.00 | +0.00 | +0.00 | `BAKERY + SMOOTHIE_SHOP` | `STRAWBERRY` | Bedrock tie preserved (+0.00) |
| **50045** | +0.00 | +0.00 | +0.00 | `ICE_CREAM_SHOP + YARN_STORE` | `YARN` | Bedrock tie preserved (+0.00) |
| **50046** | +0.00 | +0.00 | +0.00 | `FARMERS_MARKET + ICE_CREAM_SHOP` | `STRAWBERRY` | Bedrock tie preserved (+0.00) |
| **50047** | +0.00 | +0.00 | +0.00 | `BRUNCH_SPOT + PET_CAFE` | `STRAWBERRY` | Bedrock tie preserved (+0.00) |
| **50048** | +0.00 | +0.00 | +0.00 | `BRUNCH_SPOT + SMOOTHIE_SHOP` | `STRAWBERRY` | Bedrock tie preserved (+0.00) |
| **50049** | +0.00 | +0.00 | +0.00 | `PET_CAFE + ICE_CREAM_SHOP` | `STRAWBERRY` | Bedrock tie preserved (+0.00) |

---

## 3. Structural Breakdown & Attribution

### 3.1 Where Risk Was Removed
- **Seed 50018**: In `EXP-DEV-001`, the unhedged substitution of 13 Tomato tiles resulted in a -$2,388.00 collapse when late Strawberry shops rendered strawberries far more valuable.
- In `EXP-DEV-002`, capping tomato substitution to 6 tiles retained 13 mature Strawberry plants (yielding 52 harvests).
- This eliminated the entire -$2,388.00 loss and produced a **+$3,820.00 win**.
- Across the whole 50-seed set, the worst single-seed loss was reduced from **-$2,388.00 to -$11.00** (Seed 50017).

### 3.2 Where Upside Was Retained vs Surrendered
- **Seed 50004**: This world featured persistent Tomato demand throughout the game (4 Pizza Shops).
- In `EXP-DEV-001`, the farm captured **+$15,264.00** with 13 tomato plants.
- In `EXP-DEV-002`, with 6 tomato plants, the farm captured **+$8,300.00**.
- The agent retained **54.4% of the peak upside** while deploying only **46.1% of the crop capacity** (6 / 13 tiles), reflecting favorable market pricing on smaller sell batches.
- The surrendered upside was **-$6,964.00**.

### 3.3 Where Performance Changed Little
- Exactly **48 out of 50 seeds (96.0%)** showed zero change in paired margin between DEV-001 and DEV-002.
- The Carrot adaptation logic (which occurs on Days 18–26 and strictly preserves feed reserve + 10 wheat) was already safe in DEV-001 and remained untouched in DEV-002.
- The Strawberry Bedrock core (84% of worlds) was 100% preserved.

### 3.4 Summary Macro Comparison

| Dimension | EXP-DEV-001 (Unhedged) | EXP-DEV-002 (Hedged) | Net Difference |
| :--- | :---: | :---: | :---: |
| **Total Cumulative Margin ($)** | +$13,259.00 | +$12,503.00 | -$756.00 (-5.7%) |
| **Mean Margin ($\Delta \mu$)** | +$265.18 | +$250.06 | -$15.12 |
| **Worst Single-Seed Loss** | **-$2,388.00** | **-$11.00** | **+$2,377.00 (+99.5%)** |
| **Stop Criterion ($< -\$800$)** | **BREACHED (Failed)** | **PASSED** | **GATING ACHIEVED** |
| **Seeds with Losses** | 2 seeds (4.0%) | 1 seed (2.0%) | -1 loss seed |
| **Seeds with Divergence** | 8 seeds | 8 seeds | 0 (Identical activation) |

---

## 4. Verification Conclusion

The comparison confirms that `EXP-DEV-002` operates exactly as designed by financial hedging theory:
- It surrenders high-variance upside in rare persistent worlds to purchase tail protection against severe losses in demand reversal worlds.
- The improvement is not a broad distribution shift; it is **strictly concentrated in truncating the negative tail of the two Tomato-active worlds**.
