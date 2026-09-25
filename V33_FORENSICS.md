# V33 Economic Forensics & Failure Taxonomy Report

**Program:** Kagriculture V33 Research Program  
**Date:** 2026-09-24  
**Scope:** Forensic analysis of economic mechanisms (cash, liquidity, production, market impact) and systematic failure classification under the V33 Failure Taxonomy.

---

## 1. Economic Forensics: Why A7 Dominates the Portfolio

### A. Capital Velocity & Labor Utilization
- **A7 Monoculture:** Hires 4 workers at Step 0, concentrates them exclusively in Quadrant 0, and operates a tight, continuous sowing-harvest cycle. Zero idle worker turns between steps 48 and 680.
- **Alternative Routes ($R1, R4, R5$):** Attempt multi-quadrant land expansion ($R4$) or balanced zoning ($R5$). Land purchase costs ($\$1,000–\$3,000$) siphon working capital away from seed replanting and fertilizer, slowing asset velocity during the critical early inflection curve ($t \in [48, 200]$).

### B. Liquidity & Cash Drag
- In the paired tournament, A7 maintained an average liquid cash reserve of **$\$4,820$** during midgame cycles.
- Spliced or switched policies experienced cash starvation (liquid reserves dropping to $<\$200$), causing worker idling and rejected seed purchase orders.

### C. Price Impact Dynamics
- In a 2-player game where both farms produce agricultural commodities, local price elasticity is severe.
- When A7 sells wheat, the price drops from $\$25$ to $\$18–\$20$. However, because A7's cost of production is near-zero (labor is a sunk capex of $\$2,000$), selling at $\$18$ still yields positive gross margin.
- Switching to livestock ($R2$) in response to a crop price drop fails because animal capex ($\$5,000+$ for barn/cows) requires a 200+ step payback period that cannot be amortized if started after $t=48$.

---

## 2. Failure Taxonomy Classification (F1 – F15)

Every evaluated sub-branch and external hypothesis is classified below:

| Failure Code | Name | Evaluated Component | Empirical Evidence | Verdict |
| :---: | :--- | :--- | :--- | :---: |
| **F1** | No Route Complementarity | Full Route Portfolio ($R1..R5$) vs $R0\_A7$ | $R0\_A7$ achieved 48/50 wins (96.0%) in round-robin; 0 non-transitive cycles. | **CONFIRMED** |
| **F2** | Complementarity Not Observable Early | $R2\_DMITRII$ Counter-strategy | Favorable payoff occurs only on Seed 249677; observables at $t \le 16$ are indistinguishable. | **CONFIRMED** |
| **F4** | Unsafe Transition Boundary | Midgame Splicing ($t \ge 144$) | Switching causes $-\$3,292$ to $-\$8,433$ capital destruction due to conflicting farm layouts. | **CONFIRMED** |
| **F5** | Local Gain / Long Horizon Loss | Sell Reordering (Market Timing) | Intra-turn liquidity delay starves subsequent farm purchases ($-\$161.60$ paired delta). | **CONFIRMED** |
| **F6** | Public Route Replay-Specific | Public 3090 ($R3$) | Scored 0/50 wins (0.0%, $-\$30,648$ delta) against interactive opponents. | **CONFIRMED** |
| **F7** | Market Regime Unstable | Price-Impact Sell Ordering | Degraded win rate from 88.3% to 83.3% across the 6-opponent league. | **CONFIRMED** |
| **F9** | Too Much Switching | Multi-Switching ($k \ge 2$) | Sinks win rate to 28.3% ($-\$7,927$ mean loss) via repeated coordination resets. | **CONFIRMED** |
| **F11**| Route Family Redundant | $R1\_V22R1$ and $R5\_V25P3$ | 0/15 positive counterfactual deltas when branched from A7. | **CONFIRMED** |
| **F14**| Tail Risk | Unconditional Switching | Introduces catastrophic downside tail of $-\$8,433.00$ on Seed 249675. | **CONFIRMED** |

---

## 3. Forensic Conclusion

The central premise of V33—that an elite route portfolio with complementary non-transitive matchup strengths could replace A7—has been **rigorously falsified**:
1. No complementary route portfolio exists in the available population. A7 is a universally dominant expert.
2. Market timing overlays produce intra-turn liquidity drag and degrade win rates.
3. Midgame meta resets cannot overcome physical asset lock-in.

The V33 selective controller successfully prevented degradation by **abstaining**, but cannot extract genuine outperformance from non-existent complementarity.
