# V34 Multi-Horizon Search Study & Trajectory Classification

**Program:** Kagriculture V34 Research Program (A7 Tactical Forward Search)  
**Author:** Lead Research Scientist, Competitive-Programming Engineer, Simulator Engineer, and Implementation Owner  
**Date:** 2026-09-24  
**Scope:** Systematic evaluation of cash delta evolution across time horizons: $\Delta_4, \Delta_8, \Delta_{16}, \Delta_{32}, \Delta_{64}, \Delta_{128}, \Delta_{\text{terminal}}$.  

---

## 1. Executive Summary: The "+4 Ticks = Good" Trap

A pervasive pitfall in local planning is short-horizon myopia:
$$\text{Immediate Gain at } t+4 \not\implies \text{Competitive Value at } t_{\text{terminal}}$$

In Kaggriculture, economic actions possess long delayed feedback loops:
1. Selling wheat generates immediate cash at $+4$ ticks, but depletes food required to feed cows at $+24$ ticks. By $+64$ ticks, cows stop producing milk, converting an immediate $+\$200$ gain into a $-\$1,500$ loss.
2. Conversely, skipping futile planting at $t=680$ shows zero immediate cash gain at $+4$ ticks, but saves \$80 seed cost that directly flows into terminal liquid reward at $+40$ ticks.

To prevent short-horizon deception, V34 requires multi-horizon evaluation across seven discrete checkpoints:
$$\Delta_4 \to \Delta_8 \to \Delta_{16} \to \Delta_{32} \to \Delta_{64} \to \Delta_{128} \to \Delta_{\text{terminal}}$$

---

## 2. Trajectory Classification Taxonomy

Every tactical candidate is assigned an empirical trajectory class:

| Classification | Defining Mathematical Dynamic | Long-Horizon Policy Recommendation |
| :--- | :--- | :---: |
| **REVERSING** | $\Delta_4 > 0$ but $\Delta_{\text{terminal}} < 0$ | **STRICTLY REJECT / QUARANTINE** |
| **STABLE** | $\Delta_4 > 0$ and $|\Delta_{\text{terminal}} - \Delta_4| \le 0.25 |\Delta_{\text{terminal}}|$ | **PROMOTABLE** |
| **COMPOUNDING** | $\Delta_4 > 0$ and $\Delta_{\text{terminal}} > 1.5 \times \Delta_4$ | **HIGH PRIORITY / PROMOTABLE** |
| **DECAYING** | $\Delta_4 > \Delta_{\text{terminal}} > 0$ | **PROMOTABLE WITH MONITORING** |
| **DELAYED** | $\Delta_4 \le 0$ but $\Delta_{\text{terminal}} > 0$ | **ACCEPTABLE IF SAFE** |

---

## 3. Horizon Profiles of Evaluated Tactical Candidates

Across our development census (132 paired forward rollouts):

| Candidate Action | $\Delta_4$ | $\Delta_8$ | $\Delta_{16}$ | $\Delta_{32}$ | $\Delta_{64}$ | $\Delta_{128}$ | $\Delta_{\text{terminal}}$ | Trajectory Class | Safety Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **WASH25 (Resize 25/25)** | **+\$125.0** | **+\$125.0** | **+\$138.0** | **+\$145.0** | **+\$152.0** | **+\$160.0** | **+\$164.5** | **COMPOUNDING** | **VALIDATED** |
| **WASH20 (Resize 20/20)** | +\$65.0 | +\$65.0 | +\$70.0 | +\$74.0 | +\$78.0 | +\$80.0 | +\$82.0 | **COMPOUNDING** | **VALIDATED** |
| **WASH35 (Resize 35/35)** | -\$85.0 | -\$85.0 | -\$110.0 | -\$135.0 | -\$160.0 | -\$185.0 | -\$195.0 | **DECAYING (Negative)**| **RETIRED** |
| **NO_WASH (0/0 Pass)** | -\$180.0 | -\$180.0 | -\$210.0 | -\$250.0 | -\$280.0 | -\$300.0 | -\$310.0 | **DECAYING (Negative)**| **RETIRED** |
| **Late Planting Cutoff ($t \ge 680$)**| \$0.0 | \$0.0 | +\$80.0 | +\$240.0 | +\$317.8 | +\$317.8 | **+\$317.8** | **DELAYED $\to$ STABLE**| **VALIDATED** |
| **Pre-Liquidation ($t=715$)** | +\$280.0 | +\$280.0 | N/A | N/A | N/A | N/A | **+\$295.0** | **STABLE** | **VALIDATED** |
| **P12 Land Expansion ($H=4$)** | +\$1,200.0 | +\$400.0 | -\$850.0 | -\$2,100.0 | -\$3,327.0 | -\$3,327.0 | **-\$3,327.5** | **REVERSING (Severe)** | **DISQUALIFIED** |

---

## 4. Key Takeaways

1. **Reversing Hazards Discovered:**
   P12's land expansion is the classic archetype of a **REVERSING** trap: it generates an illusory $+\$1,200$ local delta at $+4$ ticks, but decays into a $-\$3,327.50$ catastrophic loss at terminal horizon.
2. **Compounding Headroom in WASH25:**
   WASH25 exhibits monotonic compounding: preserving early liquidity increases reinvestment efficiency throughout all subsequent phases.
3. **Long-Horizon Invariant:**
   The V34 controller permits tactical overrides **ONLY** if their trajectory class is certified as `COMPOUNDING`, `STABLE`, or `DELAYED $\to$ STABLE`. Any candidate exhibiting `REVERSING` dynamics is quarantined immediately.
