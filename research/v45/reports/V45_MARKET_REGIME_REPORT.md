# V45 Market Regime Taxonomy & Transition Dynamics Report

**Document ID:** `research/v45/reports/V45_MARKET_REGIME_REPORT.md`  
**Date:** 2026-09-25  
**Repository:** `The-FOOL-00/kagriculture-economic-simulator`  
**Phase:** Phase 4 (Market Regimes)  
**Artifact Path:** `research/v45/artifacts/market_regimes.json`  
**Compliance Standard:** Full Trajectory Dynamic Regime Classification  

---

## 1. Executive Summary

Market conditions in Kagriculture are non-stationary and fluctuate between five distinct regimes driven by the interaction between Town Consumption cycles, player production accumulation, and strategic liquidation timing.

This report establishes the formalized **5-Regime Taxonomy** implemented in `research/v45/artifacts/market_regimes.json` and details the transition rules governing real-time regime inference.

---

## 2. The 5-Regime Taxonomy

```text
               ┌────────────────────────────────────────────────────────┐
               │              REGIME 1: PRE-COLLAPSE EQUILIBRIUM        │
               │   (Prices >= Base, Low Volume, Rising Opponent Assets) │
               └──────────────────────────┬─────────────────────────────┘
                                          │
                        Opponent Dump Detected (P_dump >= 0.60)
                                          │
                                          ▼
               ┌────────────────────────────────────────────────────────┐
               │              REGIME 2: ACTIVE COLLAPSE / DUMP          │
               │        (I_mkt > I0, Prices Saturated, Severe Slippage) │
               └──────────────────────────┬─────────────────────────────┘
                                          │
                         Town Shop Drain Tick (step % 4 == 0)
                                          │
                                          ▼
               ┌────────────────────────────────────────────────────────┐
               │              REGIME 3: SHOP DRAIN SCARCITY SPIKE       │
               │         (I_mkt < I0, Super-Linear Scarcity Peak)       │
               └──────────────────────────┬─────────────────────────────┘
                                          │
                                 Step >= 690 Arrives
                                          │
                                          ▼
               ┌────────────────────────────────────────────────────────┐
               │              REGIME 4: TERMINAL PRE-EMPTION            │
               │      (Steps 690..694, Imminent Step 696 Wave Dump)     │
               └──────────────────────────┬─────────────────────────────┘
                                          │
                                 Step >= 704 Recovery
                                          │
                                          ▼
               ┌────────────────────────────────────────────────────────┐
               │              REGIME 5: TERMINAL STAGGERED RECOVERY     │
               │       (Steps 704..706, 716+ Residual Value Absorption) │
               └────────────────────────────────────────────────────────┘
```

### Regime Details:

1. **Regime 1: Pre-Collapse Equilibrium**
   * *State Definition:* Prices within $\pm 10\%$ of base price, market inventory $I_{\text{market}} \approx I_0$, low recent trading volume.
   * *Opponent Status:* Opponent shed accumulating; predictive pressure rising.
   * *Strategic Response:* If high opponent dump probability ($\hat{P}(\text{dump}_8) \ge 0.60$), execute pre-emptive liquidation tranches before order book decay.

2. **Regime 2: Active Collapse / Saturated Market**
   * *State Definition:* Market inventory $I_{\text{market}} \gg I_0$, price collapsed below $0.85 \times \text{base}$.
   * *Strategic Response:* **STRICT WITHHOLDING / HOLD**. Never sell into this regime. Selling 16 units of Strawberry here yields only $10.31/unit vs $120.00/unit in Equilibrium. Allow town consumption to absorb excess stock.

3. **Regime 3: Shop Drain Scarcity Spike**
   * *State Definition:* Step $t \pmod 4 == 0$. Active town shops have drained inventory. $I_{\text{market}} < I_0$.
   * *Strategic Response:* **SCARCITY ARBITRAGE**. Sell small tranches ($\le 2$ to $4$ units) into the peak price amp zone ($150–$240).

4. **Regime 4: Terminal Pre-emption Window (Steps 690–694)**
   * *State Definition:* Episode horizon closing. Opponents structurally initiate full liquidation between Steps 695 and 696.
   * *Strategic Response:* Liquidate 50% of marketable shed inventory across all high-value goods at step 693–694. Captures peak un-degraded order book depth.

5. **Regime 5: Terminal Staggered Recovery (Steps 704–706 & 716+)**
   * *State Definition:* Residual episode steps after initial liquidation absorption.
   * *Strategic Response:* At steps 704–705, liquidate 50% of remaining stock to capture secondary demand recovery. At step 716+, flush 100% of residual inventory.

---

## 3. Governance Integration

Runtime controllers in V45 dynamically evaluate regime membership at every step $t$. Transitions are causal and strictly deterministic.
