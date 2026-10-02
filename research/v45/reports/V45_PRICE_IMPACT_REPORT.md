# V45 Market Response & Price Impact Empirical Report

**Document ID:** `research/v45/reports/V45_PRICE_IMPACT_REPORT.md`  
**Date:** 2026-09-25  
**Repository:** `The-FOOL-00/kagriculture-economic-simulator`  
**Phase:** Phase 4 (Market Response & Price Impact Model)  
**Artifact Path:** `research/v45/artifacts/price_impact_model.json`  
**Gate Verdict:** **PASS (Non-linear Slippage & Depth Dynamics Quantified)**  

---

## 1. Executive Summary

Phase 4 quantifies the exact non-linear price impact, order slippage, and market depth of sell orders of varying quantities ($Q \in \{1, 2, 4, 8, 16, 25, 32\}$) across commodities and market liquidity regimes.

In Kagriculture, the market price engine executes per-unit lockstep pricing:
$$P(item, I) = \text{base} \pm \text{amp} \cdot f(|I_0 - I|)$$
Each incremental unit in a single order consumes depth, raising effective market inventory $I$ and depressing the spot price quoted for subsequent units in that order.

---

## 2. Empirical Slippage & Average Realized Price Table

### Commodity: STRAWBERRY (Base Price: $120, $I_0 = 10,000$)

| Order Qty ($Q$) | Scarcity Realized Price ($I=9980$) | Equilibrium Realized Price ($I=10000$) | Saturated Realized Price ($I=10050$) | Slippage vs Init Price (Equilibrium) | Post-Sale Price Drop |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | **$158.00** | **$120.00** | $24.00 | $0.00 | $1.00 |
| **2** | **$157.50** | **$119.00** | $23.00 | -$1.00 | $2.00 |
| **4** | **$156.50** | **$117.00** | $21.00 | -$3.00 | $4.00 |
| **8** | **$154.25** | **$113.12** | $17.12 | -$6.88 | $9.00 |
| **16** | **$149.31** | **$105.56** | $10.31 | -$14.44 | $21.00 |
| **25** | **$140.04** | **$96.96** | $6.96 | -$23.04 | $38.00 |
| **32** | **$132.31** | **$90.19** | $5.66 | -$29.81 | $55.00 |

### Commodity: MELON (Base Price: $250, $I_0 = 10,000$)

| Order Qty ($Q$) | Scarcity Realized Price | Equilibrium Realized Price | Saturated Realized Price | Slippage vs Init Price (Equilibrium) | Post-Sale Price Drop |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | **$277.00** | **$250.00** | $225.00 | $0.00 | $0.00 |
| **2** | **$276.50** | **$250.00** | $224.50 | $0.00 | $0.00 |
| **4** | **$276.00** | **$250.00** | $223.50 | $0.00 | $0.00 |
| **8** | **$275.00** | **$250.00** | $221.50 | $0.00 | $0.00 |
| **16** | **$272.19** | **$249.31** | $216.81 | -$0.69 | $2.00 |
| **25** | **$265.88** | **$248.08** | $211.08 | -$1.92 | $5.00 |
| **32** | **$262.28** | **$246.78** | $206.28 | -$3.22 | $8.00 |

---

## 3. Mathematical Implications for Adversarial Strategy

1. **The Asymmetry of Dumping:**
   * Selling 16 units of Strawberry into Equilibrium yields **$105.56/unit** ($1,689 total cash).
   * Selling the same 16 units into a Saturated market (post-opponent dump) yields only **$10.31/unit** ($165 total cash) — an immediate **$1,524 cash destruction**!
2. **The Tranche Advantage:**
   * Dumping 32 units in a single block incurs $29.81/unit slippage.
   * Splitting into two 16-unit tranches separated by a town shop drain tick ($t \pmod 4 == 0$) captures the recovery peak, increasing realized revenue by **+$615.00** on Strawberry alone.
3. **Melon Depth Invariance:**
   * Due to high base price ($250) and parameter shaping, Melon exhibits minimal slippage for $Q \le 8$ (slippage is $0.00). Melon can be sold in larger blocks without immediate price decay, provided the market is not already saturated by opponent liquidation.

---

## 4. Phase 4 Promotion Verdict

The empirical price impact model (`research/v45/artifacts/price_impact_model.json`) provides the exact quantitative basis for dynamic order sizing in Phase 5 and Phase 8. Phase 4 is **PASSED**.
