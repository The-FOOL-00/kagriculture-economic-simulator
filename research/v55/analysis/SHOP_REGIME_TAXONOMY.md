# V55 Shop-Regime Economic Taxonomy

## Executive Summary

Town shops in `kaggriculture-1.32.7` unlock periodically at Steps 72, 144, 216, 288, 360, 432, 504, and 576 up to `MAX_SHOP_INSTANCES = 8`.
Shops are drawn with replacement from a discrete catalog of 8 shop types.
Each shop instance consumes from `market["inventory"]` every `townShopSellInterval = 4` steps:
- **Single-product shops** consume **2 units per tick** (0.50 units/turn).
- **Multi-product shops** consume **1 unit per tick** of each commodity (0.25 units/turn).
- Town Center consumes 1 unit of all 8 core commodities every `townCenterSellInterval = 24` steps.

This report establishes the empirical taxonomy of revealed shop configurations across 32 benchmark seeds (`250400–250431`) and quantifies the economic exposure of the sovereign incumbent **`V49_Meta_Fusion`**.

---

## 1. Shop Catalog and Commodity Consumption Mechanics

| Shop Name | Products Demanded | Consumption Rate | Total Demand Horizon (500 steps) | Economic Role |
| :--- | :--- | :---: | :---: | :--- |
| `YARN_STORE` | `['WOOL']` | 2 units / 4 steps | 250 units | **Single-commodity absorber**: Drives extreme Wool scarcity. |
| `PET_CAFE` | `['CARROT']` | 2 units / 4 steps | 250 units | **Single-commodity absorber**: Drains Carrot surplus. |
| `PIZZA_SHOP` | `['MILK', 'TOMATO', 'WHEAT']` | 1 unit / 4 steps each | 125 units each | **Multi-product driver**: Primary engine of dairy demand. |
| `ICE_CREAM_SHOP`| `['STRAWBERRY', 'MILK', 'WHEAT']`| 1 unit / 4 steps each | 125 units each | **Multi-product driver**: Absorbs Milk, Berries, and Wheat. |
| `SMOOTHIE_SHOP` | `['STRAWBERRY', 'MILK']` | 1 unit / 4 steps each | 125 units each | **Multi-product driver**: Dual high-value product sink. |
| `BAKERY` | `['EGG', 'WHEAT']` | 1 unit / 4 steps each | 125 units each | **Multi-product driver**: Steady egg/wheat consumer. |
| `BRUNCH_SPOT` | `['EGG', 'WHEAT', 'STRAWBERRY']` | 1 unit / 4 steps each | 125 units each | **Multi-product driver**: Triple-commodity sink. |
| `FARMERS_MARKET`| `['WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY']` | 1 unit / 4 steps each | 125 units each | **Broad agricultural sink**: Drains crop inventories. |

*Note on Melons:* **Zero** town shops demand `MELON`. Melons are consumed exclusively by the Town Center (1 unit per 24 steps = ~30 units per match). Uncontrolled melon overproduction causes irreversible price collapse.

---

## 2. Empirical Shop-Regime Taxonomy

Based on the distribution of revealed shops across 32 sampled seeds, environments cluster into 4 distinct economic regimes:

| Regime ID | Identifying Characteristic | Frequency | Mean V49 Margin | Margin Min | Margin Max | Supply/Demand Constrained |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **`HIGH_WOOL_REGIME`** | $\ge 2$ `YARN_STORE` instances | 28.1% (9/32) | **+$5,588.3** | +$1,419.0 | +$10,691.0 | **Supply-Constrained**: V49's 4 sheep cannot produce enough wool to saturate demand; Wool price stays pegged near cap ($200+). |
| **`HIGH_MILK_REGIME`** | $\ge 3$ Dairy Shops (`PIZZA`, `ICE_CREAM`, `SMOOTHIE`)| 40.6% (13/32) | **+$2,769.2** | -$716.0 | +$13,586.0 | **Demand-Saturated**: High total milk demand, but milk price is volatile depending on whether opponent floods the dairy market. |
| **`HIGH_EGG_REGIME`** | $\ge 3$ Poultry Shops (`BAKERY`, `BRUNCH_SPOT`) | 18.8% (6/32) | **+$2,752.5** | -$31.0 | +$5,566.0 | **Balanced**: Steady high absorption of eggs and wheat; highly stable margin for V49. |
| **`HIGH_CARROT_REGIME`**| $\ge 3$ Crop Shops (`PET_CAFE`, `FARMERS_MARKET`) | 12.5% (4/32) | **+$2,733.0** | +$1,310.0 | +$4,185.0 | **Crop-Absorptive**: Carrot demand reaches 375+ units; supports stable crop cashflow. |

---

## 3. Structural Regime Analysis

### 3.1 The High-Wool Margin Premium
In `HIGH_WOOL_REGIME`, V49 achieves its highest profitability (mean margin **+$5,588.3**, +$2,819.1 higher than Dairy regimes).
* **Causal Mechanism:** Because `YARN_STORE` consumes 2 units every 4 turns, 2 Yarn Stores consume **1.0 unit of Wool per turn**.
* With market initial inventory $I_0 = 10$, market inventory drops to 0 within 20 turns of unlock.
* Wool prices rise to their theoretical ceiling. V49 shears 4 sheep every 3 turns, generating constant ultra-premium revenue without any storage bottleneck.

### 3.2 The High-Milk Volatility Trap
In `HIGH_MILK_REGIME`, V49 margin exhibits severe tail risk (min margin -$716.0 vs max +$13,586.0).
* In games where the opponent (such as V44 on Seed 250436) also invests in cows, both agents dump milk into the market simultaneously.
* Despite town shops consuming milk, duplicate dairy sellers keep milk inventory high enough that prices fluctuate between $105 and $125.
* Attempting to withhold milk in the shed to wait for higher prices saturates the 100-item shed capacity, causing field workers to discard harvested strawberries and melons into the void (`del inv[item]` with `take = 0`), creating catastrophic multi-thousand-dollar losses.

---

## 4. Key Takeaways for V55

1. **Town shops consume from the market, not from the player:** A player cannot "sell directly" to a shop; town demand affects price only through market inventory exhaustion.
2. **Shed capacity (100 items) is the hard economic ceiling:** Because V49 produces dozens of units of crops (melons, strawberries, wheat), preserving inventory buffers for specific shop types causes systemic shed gridlock.
3. **No post-reveal pivot is required in High-Wool or High-Egg regimes:** V49's baseline herd (6 cows, 4 sheep, 2 geese) is already Pareto-optimal across these regimes.
