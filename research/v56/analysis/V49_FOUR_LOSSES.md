# V49 Four Losses Forensic Investigation

## Executive Summary

On the established 576-leg fresh evaluation suite (32 fresh seeds `[250600..250631]` $\times$ 2 seats $\times$ 9 established opponents), sovereign incumbent **`V49_Meta_Fusion`** achieves **572 Wins, 0 Draws, and exactly 4 Losses** (**99.31% Win Rate**).

All 4 losses occur exclusively against **`V44_Economic_Portfolio`** across 2 specific seeds, manifesting identically in **both seats**:
1. **Loss 1 (L1)**: Seed `250617`, Seat 0 vs V44 (Margin: **-$862.00**)
2. **Loss 2 (L2)**: Seed `250617`, Seat 1 vs V44 (Margin: **-$862.00**)
3. **Loss 3 (L3)**: Seed `250621`, Seat 0 vs V44 (Margin: **-$82.00**)
4. **Loss 4 (L4)**: Seed `250621`, Seat 1 vs V44 (Margin: **-$82.00**)

Against all other 8 opponents (`dmitrii_lb2800`, `tetsutani_pasture`, `kaitofukami_v48_3009`, `indarkarhana_top10`, `saiteja_mega_3000`, `DAIRY_FLOOD`, `WOOL_FLOOD`, `TERMINAL_DUMPER`), V49 achieves a flawless **512 Wins / 0 Losses (100.0% Win Rate)**.

---

## 1. Authoritative Loss Inventory

| Loss ID | Seed | Seat | Opponent | Opp Seat | V49 Final Cash | Opp Final Cash | Final Margin | Decisive Flip Step | Pre-Flip Lead | Primary Economic Cause |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **L1** | 250617 | 0 | V44 | 1 | $115,527.00 | $116,389.00 | **-$862.00** | Step 705 | +$162.00 (Step 704) | Terminal strawberry/milk drop delta (+22 strawberries sold by V44) |
| **L2** | 250617 | 1 | V44 | 0 | $115,527.00 | $116,389.00 | **-$862.00** | Step 705 | +$162.00 (Step 704) | Symmetric mirrored execution against V44 |
| **L3** | 250621 | 0 | V44 | 1 | $116,047.00 | $116,129.00 | **-$82.00** | Step 698 | +$18.00 (Step 697) | Step 697 market order priority (V44 sold Wool before Egg/Milk, netting +$144) |
| **L4** | 250621 | 1 | V44 | 0 | $116,047.00 | $116,129.00 | **-$82.00** | Step 698 | +$18.00 (Step 697) | Symmetric mirrored execution against V44 |

---

## 2. Production & Asset Composition Profiles

### 2.1 Terminal Animals
* **Seed 250617 (L1 & L2)**: Both V49 and V44 end with identical herds:
  - 5 Geese, 6 Cows, 6 Sheep (Exact parity: 17 total animals).
* **Seed 250621 (L3 & L4)**: Both V49 and V44 end with identical herds:
  - 3 Geese, 9 Cows, 5 Sheep (Exact parity: 17 total animals).

### 2.2 Terminal Inventory & Liquidation
* **Terminal Shed Inventories**: Exactly `{}` (empty) for both players across all 4 matches.
* **Terminal Worker Inventories**: Exactly `[]` (empty) for both players across all 4 matches.
* **Liquidation Rate**: 100.0% complete liquidation. Zero unsold inventory stranded in backpacks or sheds.

### 2.3 Commodity Revenue Breakdown (Seed 250621)

| Commodity | V49 Quantity | V49 Revenue | V44 Quantity | V44 Revenue | Revenue Delta (V49 - V44) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Wheat** | 18,312 | $730,700.00 | 18,283 | $729,055.00 | **+$1,645.00** |
| **Fertilizer** | 10,347 | $110,716.00 | 10,347 | $110,716.00 | $0.00 |
| **Wool** | 6,220 | $793,398.00 | 6,203 | $792,176.00 | **+$1,222.00** |
| **Melon** | 6,072 | $735,102.00 | 6,072 | $735,102.00 | $0.00 |
| **Egg** | 8,099 | $370,951.00 | 8,097 | $370,844.00 | **+$107.00** |
| **Strawberry** | 6,381 | $100,057.00 | 6,330 | $96,315.00 | **+$3,742.00** |
| **Tomato** | 6,070 | $589,306.00 | 6,070 | $589,306.00 | $0.00 |
| **Carrot** | 17,048 | $494,508.00 | 17,048 | $494,508.00 | $0.00 |
| **Milk** | 8,308 | $2,152,832.00 | 8,320 | $2,155,533.00 | **-$2,701.00** |
| **TOTAL GROSS**| — | **$6,077,570.00** | — | **$6,073,649.00** | **+$3,921.00** |

**Crucial Finding**: V49 generated **+$3,921.00 MORE gross revenue** than V44!
V49 out-earned V44 on Wheat, Wool, Eggs, and Strawberries. The -$82 margin was caused by V49 spending $518 more on input capex/seed churn than V44.

---

## 3. Decisive Flip Moments

### 3.1 Seed 250621: The $144 Market Order Inversion (Step 697)
* Through Step 695, V49 led by **+$522.00**.
* At Step 697, V49 led by **+$18.00** ($105,289 vs $105,271).
* Both players submitted a batch of market sales:
  - **V49 Queue**: `['CARROT', 33]`, `['EGG', 8]`, `['MILK', 1]`, `['WOOL', 3]`
  - **V44 Queue**: `['CARROT', 33]`, `['WOOL', 3]`, `['EGG', 8]`, `['MILK', 1]`
* Under lockstep market processing (`_process_market`), V44 executed `WOOL` at queue index 1, receiving pre-depressed prices. V49 executed `WOOL` at index 3.
* On Step 698, V44 earned $1,110 while V49 earned $966 ($144 difference), flipping margin from +$18 to -$126.
* Over the final 20 turns, V49 recovered $44 of the deficit, finishing at **-$82.00**.

### 3.2 Seed 250617: The Late Strawberry Drop Timing (Step 704–707)
* Through Step 704, V49 led by **+$162.00** ($111,003 vs $110,841).
* At Step 705–707, V44 completed a final pass of strawberry and milk collections, selling 22 more units of strawberries and 1 more unit of milk, capturing +$4,351 in cash.
* V49's workers completed their harvest on wheat fields instead, leaving V49 -$862 behind at terminal.
