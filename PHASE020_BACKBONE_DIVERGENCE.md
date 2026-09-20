# PHASE020 — BACKBONE DIVERGENCE ANALYSIS (§27)

**Phase**: PHASE020  
**Title**: Prospective Headroom Reorientation & New Opportunity Family Discovery  
**Date**: 2026-09-20  
**Chassis**: Frozen V3 (`845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`)  
**Evaluator**: Phase 016 Macro-Aware Exact Continuation  

---

## 1. Backbone Divergence Taxonomy (§27)

For every candidate evaluated in the prospective census, the baseline V3 action was compared with the patched alternative action to classify the exact divergence tier:

| Divergence Tier | Description | Probes | Mean LH Delta | Positive Count | Positive Rate | Macro Esc % | Survivability Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **D0** | No economically meaningful divergence | 0 | $0.00 | 0 | 0.0% | 0.0% | N/A |
| **D1** | Timing-only (Cardinal route shifts) | 31,804 | -$18.85 | 1,536 | 4.8% | 20.2% | **ELIMINATED** (Disrupts V3 paths) |
| **D2** | Order sequence change (Market permutation) | 58 | -$60.03 | 0 | 0.0% | 34.5% | **ELIMINATED** (Zero positive signal) |
| **D3** | Worker allocation change (Multi-worker sync) | **3,784** | **+$15.54** | **1,360** | **35.9%** | **21.6%** | **SURVIVED (Robust Positive Core)** |
| **D4** | Market action change (Tranche sales) | 5,364 | -$74.20 | 1,062 | 19.8% | 66.8% | **QUARANTINED** (Severe Macro Penalties) |
| **D5** | Production policy change (Terminal salvage) | 160 | +$44.45 | 140 | 87.5% | 0.0% | **SURVIVED** (Late-game runway salvage) |
| **D6** | Multi-system divergence | 0 | $0.00 | 0 | 0.0% | 0.0% | N/A |

---

## 2. Forensic Analysis of Divergence Tiers

### Why D3 (Worker Allocation) Survives
D3 transformations reassign immediate physical labor commands (e.g., instructing a co-located farmhand to execute `["HARVEST"]` on a mature tile rather than waiting for the farmer).
- **No Cash Gate Perturbation**: Cash remains unchanged at step 0. No V3 macro capex thresholds (Sheep $10k, Tomato $12k) are falsely crossed.
- **No Livestock Starvation**: Wheat inventory in the shed is not depleted; livestock feed security remains 100% intact.
- **Tight Downstream Alignment**: The V3 continuation policy seamlessly incorporates the cleared tile, replanting immediately without macro bifurcation.

### Why D4 (Market Action / Tranche) Collapses
D4 attempts to generate cash at step 0 by selling inventory from the shed.
- **Massive Continuation Deficit**: 66.8% of candidates trigger macro escalation. Even when local signal is +$80, downstream continuation delta drops by -$120 to -$350.
- **Starvation & Opportunity Cost**: Depleting inventory leaves animals unfed and deprives subsequent turns of higher-value processing.

### Why D1 (Route Timing) Fails
D1 alters movement directions. In a grid environment with obstacle collisions and planned paths, arbitrary cardinal detours increase total travel time and delay critical field milestones.
