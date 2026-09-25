# V43 Multi-Objective Pareto Alpha Frontier Report

**Document ID:** `research/v43/reports/V43_ALPHA_FRONTIER.md`  
**Date:** 2026-09-25  
**Repository:** `Kagriculture`  
**Artifact Path:** `research/v43/artifacts/alpha_frontier.json`  
**Scope:** Multi-objective evaluation of all evaluated strategic candidates across expected return, downside tail risk, match rescue rate, and casualty invariants to identify the non-dominated Pareto frontier.

---

## 1. Executive Summary

In direct compliance with Section 25 of the V43 specification, candidate strategies must not be judged by single arbitrary scalar scores or high-variance outlier spikes.

Instead, every candidate strategy is evaluated across four orthogonal economic objectives:
1. **Expected Value:** Mean Cash Delta over V35 ($\mu_{\Delta}$).
2. **Median Robustness:** Median Cash Delta ($\text{Med}_{\Delta}$).
3. **Downside Tail Protection:** 5th-Percentile Lower Tail ($P5_{\Delta}$).
4. **Match Conversion Potential:** Rescues ($\text{LOSE} \to \text{WIN}$) with zero casualties.

### Governing Invariant:
Any candidate producing even a single casualty ($\text{Casualties} > 0$) is immediately disqualified from Pareto consideration.

---

## 2. Master Pareto Frontier Table

| Strategy Name | Strategy Archetype | Mean Cash $\Delta$ | Median Cash $\Delta$ | 5th-Percentile (P5) | Worst Observed Loss | Positive Rate (%) | Rescues | Casualties | Pareto Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`V43_3STEP_STAGGERED_FLUSH`** | **3-Step Staggered Composition** | **`+$74.20`** | **`+$42.00`** | `-$52.00` | `-$85.00` | **67.2%** | **2** | **0** | **PARETO DOMINANT (Max Return)** |
| **`V43_STAGGERED_30_70`** | **Conservative 2-Point Staggered** | **`+$57.50`** | **`+$28.00`** | **`-$41.30`** | **`-$65.00`** | **65.6%** | 0 | **0** | **PARETO DOMINANT (Min Risk)** |
| **`V39_TARGETED_FULL`** | 1-Step Heuristic Full Dump | `+$27.40` | `$0.00` | `-$241.00` | `-$516.00` | 47.1% | **3** | **0** | **PARETO DOMINANT (Max Rescues)** |
| **`V35_INCUMBENT`** | Baseline Chore Production | `$0.00` | `$0.00` | **`$0.00`** | **`$0.00`** | 0.0% | 0 | **0** | **PARETO DOMINANT (Base Anchor)** |
| `V43_STAGGERED_50_100` | 2-Point Staggered Flush | `+$66.03` | `+$37.00` | `-$66.70` | `-$98.00` | 62.5% | 1 | **0** | Dominated by 3-Step Flush |
| `V42_STAGGERED_50_50` | V42 Baseline 2-Point Staggered | `+$62.47` | `+$27.50` | `-$66.70` | `-$111.00` | 62.5% | 1 | **0** | Dominated by 3-Step Flush |
| `V43_STAGGERED_70_30` | Front-Loaded 2-Point Staggered | `+$57.41` | `+$8.00` | `-$86.40` | `-$142.00` | 68.8% | 1 | **0** | Sub-optimal tail risk |
| `V41_LAND_EXPAND` | Midgame Land Purchase (Unplanned) | `-$7,699.17` | `-$4,000.00` | `-$12,341.00` | `-$14,500.00` | 5.7% | 0 | **6** | **DISQUALIFIED (UNSAFE)** |

---

## 3. Deep-Dive on the Pareto Frontiers

```text
               Mean Cash Delta ($)
                      ▲
       +$80 ─         │                   ★ V43_3STEP_STAGGERED_FLUSH (+$74.20, P5: -$52, Res: 2)
                      │
       +$60 ─         │         ★ V43_STAGGERED_30_70 (+$57.50, P5: -$41.30, Res: 0)
                      │
       +$40 ─         │
                      │
       +$20 ─         │                               ★ V39_TARGETED_FULL (+$27.40, Res: 3)
                      │
        $0  ─ ★ V35   │
              ───────┼───────────────────────────────────────────────► Downside Risk (P5)
                    $0      -$50            -$100           -$250
```

### 1. The Maximum Return Frontier: `V43_3STEP_STAGGERED_FLUSH`
* **Schedule:** 40% at Step 694 $\to$ 60% of remainder at Step 705 $\to$ 100% of residual at Step 716.
* **Economic Mechanism:**
  - Initial 40% liquidation sells into uncrowded market depth before competitor dumping waves.
  - Secondary 60% liquidation captures the post-dump price rebound around Step 705.
  - Final flush clears any remaining agricultural goods before the episode closes at Step 718.
* **Performance:** Delivers **`+$74.20` mean delta**, **`+$42.00` median delta**, **2 rescues**, and **zero casualties**.

### 2. The Minimum Downside Risk Frontier: `V43_STAGGERED_30_70`
* **Schedule:** 30% at Step 694 $\to$ 70% at Step 705.
* **Economic Mechanism:**
  - By restricting the initial dump to only 30%, internal price impact is virtually zero.
  - Downside risk is cut to **`-$41.30`** (the tightest safety envelope of any active policy in the Kagriculture lineage).
  - Positive hit rate reaches **65.6%**.

---

## 4. Key Strategic Conclusions

1. **Compositional Staggering Dominates Single Dumps:**
   Single-step full dumps (`V39_TARGETED_FULL`) suffer severe downside tail risk (`-$241.00` P5) due to market impact. Composing multi-point partial liquidations raises mean return by up to **`+$46.80`** while improving downside protection by **$189.00**.
2. **Safety Invariant Preserved:**
   Every Pareto-approved candidate achieves **0 casualties across hundreds of branch evaluations**, adhering strictly to the Golden Property when not actively liquidating.
