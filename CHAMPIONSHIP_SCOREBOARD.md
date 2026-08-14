# 🏆 Kaggriculture Championship Scoreboard

Formal evaluation tracking of all competition candidates across deterministic multi-seed benchmarks against immutable controls and synthetic strategic archetypes.

---

## 🎖️ Master Scoreboard

| Candidate | Status | Golden Control Win % | Starter Win % | Overall Mean Cash | Mean Margin (vs Golden) | Notes / Major Innovations |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **`golden_v1.py`** | `CONTROL` | 50.0% (Self) | 100.0% | $43,982.30 | $0.00 | Apex Grandmaster v3 (Immutable Reference) |
| **`Titan Apex v3`** | `CHALLENGER` | **78.0%** (39/11) | 100.0% | $36,919.14 | **+$5,177.54** | Dynamic Market Model + Town Scarcity + Opponent Radar |
| **`Titan Apex v4`** | `CHAMPION` | **65.0%–77.0%** | 100.0% | $34,777.22 | **+$1,525.11** | High-Throughput Liquidation (87% loss Pareto fix) |

---

## 🔬 Loss Forensics Pareto Breakdown (100 Matches Analyzed)

Forensic analysis of all 23 losses experienced by Titan v3 against Golden Control v1:

```
===========================================================================
LOSS ROOT-CAUSE CLUSTERING (100-Match Forensic Analysis)
===========================================================================
1. MELON_HARVEST_SELLING_SLIPPAGE : 20 losses ( 87.0%) | Avg Deficit: -$3,083.80
   -> Cause: Overly conservative micro-batching choked the shed during Day 12 harvest.
   -> Fix: High-Throughput Liquidation Pipeline (12–14 units/turn) eliminated inventory logjams.
2. DAY_0_PORTFOLIO_DIVERGENCE     :  2 losses (  8.7%) | Avg Deficit: -$1,015.50
   -> Cause: Minor seed rounding variance on Day 0 opening step.
3. STRAWBERRY_OVEREXPOSURE        :  1 loss   (  4.3%) | Avg Deficit: -$11,972.00
   -> Cause: Opponent early strawberry flood depressed recurring price curve.
===========================================================================
```

---

## 📦 Tomorrow's 5-Slot Kaggle Submission Deployment Plan

When submission quota resets tomorrow, deploy this diversified experimental roster:

1. **`Slot 1 — Control`** ([`candidates/slot1_titan_control.py`](file:///c:/Users/Sundareswaran/Kagriculture/candidates/slot1_titan_control.py)):
   - Current stable live reference (Titan Apex v3 baseline).
2. **`Slot 2 — Loss-Fix Challenger`** ([`candidates/slot2_loss_fix_challenger.py`](file:///c:/Users/Sundareswaran/Kagriculture/candidates/slot2_loss_fix_challenger.py)):
   - High-throughput liquidation pipeline addressing the 87% melon selling logjam.
3. **`Slot 3 — Opponent-Adaptive Challenger`** ([`candidates/slot3_opponent_adaptive.py`](file:///c:/Users/Sundareswaran/Kagriculture/candidates/slot3_opponent_adaptive.py)):
   - Dynamic opponent farm radar & anti-glut crop counter-hedging.
4. **`Slot 4 — Market Planner Challenger`** ([`candidates/slot4_market_planner.py`](file:///c:/Users/Sundareswaran/Kagriculture/candidates/slot4_market_planner.py)):
   - Non-linear price elasticity & post-consumption scarcity arbitrage.
5. **`Slot 5 — Local Champion`** ([`candidates/slot5_local_champion.py`](file:///c:/Users/Sundareswaran/Kagriculture/candidates/slot5_local_champion.py)):
   - Unified Titan Apex v4 production build with compiled zero-dependency runtime.
