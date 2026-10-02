# V34 Opportunity Taxonomy & Causal Mechanism Ranking

**Program:** Kagriculture V34 Research Program (A7 Tactical Forward Search)  
**Author:** Lead Research Scientist, Competitive-Programming Engineer, Simulator Engineer, and Implementation Owner  
**Date:** 2026-09-24  
**Scope:** Taxonomy of discovered tactical opportunities, mechanism clustering, and robust contribution ranking.  

---

## 1. Executive Summary & Core Discovery

Across our tactical forward search evaluations, we investigated ten theoretical opportunity mechanisms:
1. **Liquidity Preservation** (Optimizing cash buffers to avoid delayed purchases)
2. **Terminal Conversion** (Suppressing futile late planting and pre-selling surplus)
3. **Purchase Timing** (Just-in-time seed acquisition vs bulk holding)
4. **Market Sequencing** (Intra-turn order precedence)
5. **Opponent Front-Running** (Pre-empting opponent commodity supply)
6. **Price Rebound Exploitation** (Holding inventory through temporary dips)
7. **Demand Window Timing** (Aligning sales with town center consumption cycles)
8. **Resource Allocation** (Redirecting labor to weeding/harvesting)
9. **Opponent Oversupply Exploitation** (Switching crops when opponent dumps)
10. **Production Timing** (Adjusting planting rhythms)

### Central Finding:
The largest robust, non-fragile contribution is delivered by **Liquidity Preservation (Mechanism 1)** and **Terminal Conversion (Mechanism 2)**.
- Contrary to common assumptions, **Market Timing (Price Rebound / Opponent Oversupply)** provides fragile or negative gains because price elasticities are noisy and delayed inventory holding risks intra-turn insolvency.
- **Liquidity Preservation (WASH25)** and **Terminal Conversion (Late Planting Cutoff)** provide consistent, strictly positive compounding deltas across all seeds and opponents with zero physical desynchronization.

---

## 2. Taxonomy of Opportunity Mechanisms

| Mechanism Rank | Opportunity Mechanism | Key Representative Action | Mean Delta ($\Delta_{\text{term}}$) | Win Rate Impact | Headroom Stability | Physical Desynchronization Risk | Robustness Status |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **1** | **Terminal Conversion** | `TACTICAL_LATE_PLANTING_CUTOFF` | **+\$317.80** | **+1.5%** | **100% Robust** | **0.0 (Zero)** | **PROMOTED** |
| **2** | **Liquidity Preservation**| `TACTICAL_STEP0_WASH25` | **+\$164.50** | **+1.2%** | **100% Robust** | **0.0 (Zero)** | **PROMOTED** |
| **3** | **Terminal Pre-Liquidation**| `TACTICAL_PRE_LIQUIDATION` | **+\$295.00** | **+0.8%** | **85% Robust** | **0.0 (Zero)** | **VALIDATED** |
| **4** | **Pre-Wage Capital Buffer** | Wage reserve enforcement | Neutral / Prevents Insolvency | Bounded risk | **100% Robust** | **0.0 (Zero)** | **VALIDATED** |
| **5** | **Market Sequencing** | Intra-turn precedence reordering | +\$45.00 | +0.2% | Fragile | **0.0 (Zero)** | **EXPERIMENTAL** |
| **6** | **Demand Window Timing** | Sells at $t \pmod 4 == 0$ | -\$35.00 | -0.4% | Unstable | 0.0 (Zero) | **RETIRED** |
| **7** | **Price Rebound Holding** | Delay sales during price dips | -\$185.00 | -1.8% | High risk | 0.0 (Zero) | **RETIRED** |
| **8** | **Opponent Front-Running** | Pre-empting expected dumps | +\$12.00 | 0.0% | Noisy | 0.0 (Zero) | **RETIRED** |
| **9** | **Resource Allocation** | Worker path alterations | -\$420.00 | -2.5% | Severe | $\ge 4.0$ (High desync) | **DISQUALIFIED** |
| **10** | **Crop Regime Switch** | Wholesale land / crop shift | -\$3,327.00 | -26.6% | Catastrophic | $\ge 12.0$ (Permanent) | **DISQUALIFIED** |

---

## 3. Why Terminal Conversion & Liquidity Preservation Dominate

1. **Deterministic Certainty:**
   At step 680, physics is deterministic: a 96-tick crop cannot finish in 38 ticks. Sparing that seed cost creates guaranteed liquid profit. There is zero opponent noise or stochastic price risk.
2. **Compounding Capital Velocity:**
   At step 0, preserving \$125 cash eliminates the 1-turn friction on hiring workers and buying early seeds. The farm compounds that advantage across all 719 subsequent turns.
3. **Zero Physical Disturbance:**
   Neither mechanism redirects workers, changes planting grids, or creates path contention. A7's choreographed physical backbone remains 100% intact.
