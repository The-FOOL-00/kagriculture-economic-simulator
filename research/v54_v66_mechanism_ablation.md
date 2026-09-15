# Mechanism Ablation Analysis: V54 & V66

**Harness:** Multi-core parallel benchmark across 20 identical seeds (2000–2019) against O0 (IDLE), O4 (V54), and O5 (V66).  
**Baseline V54 Mean Performance:** $167,180 (vs IDLE) | $83,595 (vs V54) | $80,212 (vs V66).

---

## 1. Quantitative Ablation Scoreboard

| Mechanism Ablated | vs IDLE Reward | $\Delta$ vs IDLE | vs V54 Reward | $\Delta$ vs V54 | Win% vs V54 | vs V66 Reward | $\Delta$ vs V66 | Win% vs V66 | Causal Severity |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **BASELINE (Full V54)** | **167,180** | **+0** | **83,595** | **+0** | 0.0% | **80,212** | **+0** | 15.0% | Baseline |
| **M1: No Early Wheat** | **62,702** | **-104,479** | **44,162** | **-39,433** | 0.0% | **43,142** | **-37,070** | 0.0% | **VERIFIED (CRITICAL)** |
| **M2: No Strawberry Wave** | **110,851** | **-56,330** | **49,902** | **-33,693** | 0.0% | **48,735** | **-31,477** | 0.0% | **VERIFIED (CRITICAL)** |
| **M3: No Accelerated Labor** | **1,306** | **-165,874** | **254** | **-83,341** | 0.0% | **712** | **-79,499** | 0.0% | **VERIFIED (CRITICAL)** |
| **M4: No Early Livestock** | **20,194** | **-146,986** | **15,723** | **-67,872** | 0.0% | **10,412** | **-69,800** | 0.0% | **VERIFIED (CRITICAL)** |
| **M6: No Batch Selling** | **18,162** | **-149,018** | **9,707** | **-73,888** | 0.0% | **10,594** | **-69,617** | 0.0% | **VERIFIED (CRITICAL)** |
| **M7: No Early Selling** | **1,204** | **-165,976** | **100** | **-83,495** | 0.0% | **104** | **-80,107** | 0.0% | **VERIFIED (CRITICAL)** |
| **M8: No Terminal Liquidation** | **141,713** | **-25,467** | **73,104** | **-10,491** | 0.0% | **70,771** | **-9,441** | 0.0% | **VERIFIED (MAJOR)** |
| **M9: No Market-Aware Selling** | **2,173** | **-165,008** | **446** | **-83,149** | 0.0% | **415** | **-79,797** | 0.0% | **VERIFIED (CRITICAL)** |

---

## 2. In-Depth Mechanism Deconstruction

### M1: Early Wheat Production ($\Delta = -\$104,479$ Solo, $-\$39,433$ vs V54)
* **Mechanism:** Planting 187 wheat seeds across Days 0–5.
* **Causal Effect:** When early wheat is disabled, V54's solo score collapses from **$167,180$ to $62,702$**—almost identical to the EXP-A Declarative Backbone's $62,387$!
* **Why It Matters:** Without on-farm wheat, animals starve unless feed is purchased at $25–$42/unit at market, depleting early working capital and eliminating 386 units of surplus wheat sales ($15.5k pure margin).

### M2: Strawberry Wave ($\Delta = -\$56,330$ Solo, $-\$33,693$ vs V54)
* **Mechanism:** Planting 38 recurring strawberries starting at step 128 (Day 5).
* **Causal Effect:** Strawberries yield recurring harvests every 2 days once mature with zero replanting costs, generating $55,128 in gross revenue. Removing them leaves land idle and caps late-game cash accumulation.

### M3 & M7: Workforce Density & Early Cash Flow ($\Delta = -\$165,000+$)
* **Mechanism:** 5 opening workers on Day 0 and immediate crop monetization starting Day 3.
* **Causal Effect:** Capping labor to 3 workers or delaying sales past Day 10 causes instantaneous farm bankruptcy. A farm cannot maintain animals, water plants, and clear weeds without at least 5 workers on Day 0 and 8 on Day 6.

### M6: Market Batch Selling ($\Delta = -\$149,018$)
* **Mechanism:** Aggregating sales into batches of 12–30 units.
* **Causal Effect:** Engine enforces a strict limit of 10 market orders per turn. Selling 1 unit per order caps output to 10 units/turn, causing shed overflow (100 capacity) and catastrophic inventory loss.

### M8: Terminal Liquidation ($\Delta = -\$25,467$ Solo, $-\$10,491$ vs V54)
* **Mechanism:** Emptying the shed at Step 670 and halting unproductive late plantings.
* **Causal Effect:** Converts all remaining finished goods into cash before turn 720. Accounts for ~$25k in terminal value.

### M9: Market-Aware Responsive Selling ($\Delta = -\$165,008$)
* **Mechanism:** Reacting to shed inventory build-up and market prices rather than blindly selling on rigid intervals.
* **Causal Effect:** Rigid interval selling overflows the shed and dumps goods during price troughs, devastating economic throughput.
