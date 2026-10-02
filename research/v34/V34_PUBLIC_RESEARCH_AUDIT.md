# V34 Public Research & Meta-Strategy Literature Audit

**Program:** Kagriculture V34 Research Program (A7 Tactical Forward Search)  
**Author:** Lead Research Scientist, Competitive-Programming Engineer, Simulator Engineer, and Implementation Owner  
**Date:** 2026-09-24  
**Scope:** Independent audit of public Kaggriculture strategies, beam search techniques, shop routers, and midgame switching claims.  

---

## 1. Executive Summary

A comprehensive audit of public codebases, notebooks, and community research was conducted to identify algorithmic mechanisms that could complement A7 without destabilizing its choreographed execution. The audited corpus includes:
1. Decompiled frontier competitor `E8_DMITRII` (2800+ LB rating).
2. Public 3090 notebook / fast action tapes (`public_3090`).
3. Declarative multi-quadrant farming research (`variant_v54_h3q4`).
4. Public rule-based expert framework (`okami001-Kaggriculture`).
5. Public shop router lineage (`yhay81/shop-router-0909`).
6. Public market wash lineage (`ahmedberatozer` V43 / V45).

---

## 2. Structured Evidence Ledger of External Claims

| Claim ID | Source & Author | Date / Version | Reported Score | Metric Type | Method Description | Evidence Level | Reproducibility | Relevance to V34 |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| **PUB-01** | `dmitrii_lb2800` (Dmitrii Gluzdov) | 2026-09-12 | 2800+ | Public LB Rating | Specialized livestock engine (coop + pasture scaling, automated animal feeding and milk/wool liquidation). | **HIGH** (Reproduced in local league) | 100% Deterministic | Shows resilience when crop markets crash; but cannot be spliced into an A7 crop farm midgame. |
| **PUB-02** | `public_3090` (Kaggle Public) | 2026-09-18 | 3090 | Historical Replay Fit | Compressed open-loop action tape optimized against fixed historical seed replays with town-demand sell ranking. | **LOW** (Severe Overfitting) | Fails in interactive play (0% win rate vs closed-loop opponents) | Confirms that pure open-loop replay memorization is fragile against interactive adversaries. |
| **PUB-03** | `variant_v54_h3q4` (lixingtao123) | 2026-09-16 | ~2530 | Self-Play Mean Cash (~$98k) | Commercial crop flood; unlocks 3-4 quadrants, mass-produces wheat and carrots with aggressive dump orders. | **MEDIUM** | 100% Deterministic | Generates massive volume, but suffers severe price collapse when matched against another crop-heavy agent. |
| **PUB-04** | `okami001-Kaggriculture` | 2026-09-14 | ~$85k | Simulation Cash | Pure rule-based heuristic with exact crop lifetime accounting and dynamic task assignment. | **MEDIUM** | 100% Deterministic | Demonstrates strict crop growth accounting (`CROP_GROWTH_TICKS`), validating V34's late planting cutoff. |
| **PUB-05** | `shop-router-0909` (yhay81) | 2026-09-09 | ~2400 | Replay Cash | Pre-computed action tapes partitioned by shop unlock sequences. | **LOW** (Regime Leakage) | Fragile | Proved that discrete route portfolios struggle with physical coordination during transitions. |
| **PUB-06** | Ahmed Berat Ozer (V43/V45) | 2026-09-15 | ~2600 | Live Leaderboard | Single-order step 0 wheat wash (50/50) to explore shop liquidity spread. | **HIGH** (Directly validated) | 100% Deterministic | Foundation of A7's 30/30 wash. Directly motivates V34's step 0 tactical wash sizing. |

---

## 3. Algorithmic Mechanisms Evaluated for V34 Tactical Search

### 1. Late Planting Cutoff (Derived from `okami001` / `CROP_GROWTH_TICKS`):
- **Mechanism:** In Kaggriculture, crops require fixed growth periods: Wheat (12), Carrot (24), Tomato (48), Strawberry (72), Melon (96). Planting a crop with $T_{\text{growth}} > (718 - t)$ is an economic deadweight loss.
- **V34 Integration:** Evaluated as `TACTICAL_LATE_PLANTING_CUTOFF`. Converts futile planting into `PASS` and removes useless seed purchases.

### 2. Step 0 Market Wash Sizing (Derived from `ahmedberatozer`):
- **Mechanism:** Capturing initial shop spreads depends on spot price conditions. A7's static 30/30 wash is not optimal for all seed initializations.
- **V34 Integration:** Evaluated as `TACTICAL_STEP0_WASH20` through `_WASH35`.

### 3. Rejection of Public Route-Switching Routers:
- **Conclusion:** Public routers (`shop-router-0909`) confirm that switching entire macro routes causes physical desynchronization and capital starvation. V34 explicitly rejects route switching and adopts single-action tactical overrides.
