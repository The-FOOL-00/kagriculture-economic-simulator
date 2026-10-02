# V33 Early Information Study: Observable Signal Horizons vs Opportunity Cost

**Program:** Kagriculture V33 Research Program  
**Date:** 2026-09-24  
**Question:** *How early can observable information distinguish favorable strategic routes, and what is the economic cost of delaying commitment?*  
**Evaluation Horizons:** $t \in \{0, 4, 8, 16, 32, 64, 96, 128\}$  
**Artifact Generated:** `early_info_results.json`

---

## 1. Information-vs-Commitment Frontier

Across 72 canonical match trajectories, we evaluated the observable environment signal (spot market prices, visible worker hiring, land purchases, and public orders) against capital commitment:

| Horizon ($t$) | Feature Variance | Mean Committed Cash ($) | Liquid Capital Remaining ($) | Irreversibility & Opportunity Cost |
| :---: | :---: | :---: | :---: | :--- |
| **$t=0$** | 0.00 | $0.00 | $3,000.00 (100%) | **ZERO:** Identical starting conditions; zero observable distinction. |
| **$t=4$** | 164,440.78 | $2,146.30 | $853.70 (28.5%) | **LOW:** First transaction window; opening worker hiring initiated. |
| **$t=8$** | 158,994.98 | $2,177.60 | $822.40 (27.4%) | **LOW:** First crop beds sown; early shop orders processed. |
| **$t=16$** | 148,128.28 | $2,242.60 | $757.40 (25.2%) | **OPTIMAL WINDOW:** Maximum divergence in opponent hiring and animal capex. |
| **$t=32$** | 141,907.89 | $2,289.90 | $710.10 (23.7%) | **MODERATE:** Fencing and seed purchases locked in. |
| **$t=64$** | 135,799.25 | $2,349.60 | $650.40 (21.7%) | **HIGH (IRREVERSIBLE):** First harvest cycle maturing; switching paths causes stalling. |
| **$t=96$** | 130,448.87 | $2,372.80 | $627.20 (20.9%) | **PROHIBITIVE:** Asset layout completely fixed. |
| **$t=128$** | 139,170.03 | $2,360.20 | $639.80 (21.3%) | **PROHIBITIVE:** Full operational path lock. |

---

## 2. Key Scientific Findings

1. **The Capital Lockup Window ($t \le 16$):**
   - By step 4, aggressive routes commit over **70% of initial starting cash** ($2,146) to worker hiring and critical tool purchases.
   - By step 16, liquid cash falls to ~$757. Delaying route selection beyond $t=16$ forces the farm to idle or execute uncoordinated hybrid actions that drain working capital.
2. **The Observable Signal Window:**
   - At $t=0$, no observable feature distinguishes opponents or game regimes (all prices start at equilibrium, all boards start empty).
   - Between $t=4$ and $t=16$, observable divergence peaks: whether the opponent hires 4 workers (`HIRE4`) vs 1–2 workers, whether they purchase cows/sheep, and early spot price movements on wheat/fertilizer.
3. **The Optimal Commitment Point:**
   - Any early branch selection mechanism must make its decision within the window $t \in [4, 16]$. Waiting until $t \ge 64$ completely destroys the economic viability of the secondary route.
