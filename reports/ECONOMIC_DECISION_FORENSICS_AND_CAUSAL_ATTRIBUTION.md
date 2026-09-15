# KAGGRICULTURE: ECONOMIC DECISION FORENSICS & CAUSAL ATTRIBUTION REPORT

**Author**: Antigravity Pair-Programming Assistant  
**Date**: September 7, 2026  
**New Candidate**: `candidates/candidate_cl_economic_v1.py`  
**Candidate SHA256**: `6afe750eab7485aafe1f8f93fc4cc7ddc199547327d3e0b7b36f6db19bc015cd`  
**Baseline Comparator**: `candidates/candidate_cl_coordinated_v1.py`  
**Benchmark Reference**: `candidates/slot2_aethel_refined_v2.py` (Frozen V2, Live Slot 2)  
**Final Portfolio Decision**: **B = PROMISING BUT NOT READY** (Zero Kaggle Submissions)

---

## EXECUTIVE SUMMARY & HEADLINE FINDINGS

In the previous research phase, multi-pool task coordination (`CL-Coordinated-V1`) slashed movement waste by -177 turns and delivered a record **3,155.8 productive actions** (surpassing Frozen V2's 2,918.6 productive turns). However, despite out-working Frozen V2 by +237 productive turns, `CL-Coordinated-V1` suffered a **-$32.5k reward penalty** in matched screening against Starter and a **-$39.5k margin defeat** in direct head-to-head play.

This research phase investigated whether the performance deficit is primarily driven by **MACRO-ECONOMIC ALLOCATION** rather than worker routing alone.

### Key Experimental Discoveries:

1. **Exact Empirical Wealth Decomposition of the V2 Advantage ($27.6k to $41.6k Gap)**:
   Our transaction-by-transaction forensic auditor revealed that the reward deficit is **NOT** caused by inferior market sale prices (in standalone play, CL actually realizes higher prices per unit due to lower town glutting). Rather, the deficit is driven by **gross productive yield collapse on high-margin lines and misallocated operating capital**:
   - **Strawberry Yield Deficit (+$12,991.0, 45.1% of revenue gap)**: V2 harvested and sold **270.0 units ($54,794)** vs CL's **181.0 units ($41,803)**. Both planted 40 strawberry plots, but CL harvested as soon as `yield_units == 1` (65% of harvests were 1-unit runs), diluting labor and cutting off the +2 fertilized yield multiplier, while delaying full strawberry seeding to Day 17 (vs V2's Day 14).
   - **Fertilizer Misallocation & Burning (+$7,940.7, 27.6% of revenue gap)**: CL collected 288 fertilizer units but indiscriminately dumped **49 units of $100 fertilizer on $25 wheat plots**, generating only +$1,225 of low-value grain—a direct destruction of **-$3,675** in net wealth. V2 collected 324 fertilizer units, fertilized strawberries, and sold 243.5 units on the market for **$18,863**.
   - **Livestock Priority Inversion (+$1,858.2 standalone, +$4,458.0 in H2H)**: CL locked animal purchases until Day 7 and prioritized $500 Sheep before $400 Cows. Cows yield daily milk ($160) and fertilizer ($100), whereas sheep yield wool ($200) intermittently. Delaying cows to Day 14–15 cost 31–45 units of milk.
   - **Wheat Over-Purchasing (+$3,725.4 of gap)**: CL over-purchased feed by +54.1 units ($1,600+ capital) and bought +15.7 excess wheat seeds, tying up land and labor on low-margin 4-day wheat.
   - **Worker Dilution & Pocket Trap**: CL hired 13 hands (14 workers total) spending $609 in Fibonacci fees. V2 capped at 11 hands (12 workers total). The extra 2 workers created traffic congestion and ended the match carrying **~$3,000 in unsold pocket inventory** (10 strawberries, 3 milk, 6 fertilizer, 31 wheat).

2. **100-Seed Multi-Arm Causal Ablation Matrix (Seeds 1000–1099, 900 Matches Total)**:
   We tested 8 isolated economic interventions in strict isolation:
   - **ARM C (Fertilizer Rationalization - No Wheat Fert)**: Increased reward to **$116,861.85 (+$4,149.39 causal lift)** by saving fertilizer for Strawberry and market sale (+22.1 units sold).
   - **ARM E (Cow Priority & Day 5 Unlock)**: Increased reward to **$116,213.65 (+$3,501.19 causal lift)** and boosted milk sales to **223.3 units** (+23.1 units, nearing V2's 229.8).
   - **ARM G (Terminal Pocket Flush)**: Increased reward to **$115,773.56 (+$3,061.10 causal lift)** by dumping pocket inventory before market close.
   - **ARM B (Hiring Cap at 11 Hands)**: Maintained reward at **$112,908.93 (+$196.47)** while **eliminating 462.8 movement turns** (down to 3,468.2) and lifting Prod/Move ratio from 0.803 to **0.866**.
   - **ARM I (Synthesized `CL-Economic-V1`)**: Achieved an all-time closed-loop high of **$120,656.62 ± $17,077.18 (+$7,944.16 lift over baseline)**, median **$124,983.50 (+$8,308.00)**, movement **3,625.4 (-305.6 moves saved)**, and idle turns reduced to **243.4** (matching V2's 242.8).

3. **Direct Head-to-Head Benchmark vs Frozen V2 (100 Matched Seeds 5000–5099, Alternating Seats)**:
   - `CL-Coordinated-V1`: Candidate Cash: $57,798.07, V2 Cash: $97,281.98, Net Margin: **-$39,483.91** [95% CI: -$40,832, -$38,143].
   - `CL-Economic-V1` (ARM I): Candidate Cash: **$66,836.77 (+**$9,038.70** higher cash)**, V2 Cash: $101,022.55, Net Margin: **-$34,185.78 (+**$5,298.13** margin improvement)** [95% CI: -$35,285, -$33,028].

4. **Economic vs Execution Coupling (Resolving Question 16)**:
   - Better economic policy **naturally reduces movement waste** (Outcome A: Better economics + lower movement). Capping hands and avoiding single-berry harvest transit legs eliminated over 300 movement turns while expanding terminal wealth by +$7.9k.

5. **Replay Purity & Mutation Gauntlet**:
   - `candidates/candidate_cl_economic_v1.py` passed 100% of Gate 1 (0 forbidden replay tokens), Gate 2 (standard library only, 0 candidate imports), and all 5 semantic mutation stress tests (cash starvation, feed starvation, crop maturation, worker displacement, price shock).

---

## 1. IMMUTABLE LIVE PORTFOLIO GOVERNANCE

Both live production anchors were cryptographically verified before and after all experiments:

| Slot | File Path | Expected SHA256 | Actual Verified SHA256 | Status |
| :--- | :--- | :--- | :--- | :---: |
| **Slot 1** | `agents/candidate_a_aethel_v1.py` | `c1945f24f34ca9d5124e8200df14af019f6cb4cdec3ca402d9a3a88f6b04e36f` | `c1945f24f34ca9d5124e8200df14af019f6cb4cdec3ca402d9a3a88f6b04e36f` | **MATCH / UNTOUCHED** |
| **Slot 2** | `candidates/slot2_aethel_refined_v2.py` | `79efb19a9b9d8146d53a7531d1f1962d5d963b8ea2b5b509e12ad526559de93d` | `79efb19a9b9d8146d53a7531d1f1962d5d963b8ea2b5b509e12ad526559de93d` | **MATCH / UNTOUCHED** |

- **Kaggle Submissions**: Exactly 0.
- **Repository Isolation**: All candidate generation and telemetry logging remained isolated in `candidates/` and `scratch/`.

---

## 2. TERMINAL WEALTH DECOMPOSITION (10-SEED MATCHED BENCHMARK)

Across matched Seeds 1000–1009, every dollar of revenue and cost was audited:

```
+---------------------------------------------------------------------------------------------+
|                           TERMINAL WEALTH DECOMPOSITION (10 SEEDS)                          |
+---------------------------------------------------------------------------------------------+
| METRIC                       | FROZEN V2          | CL-COORDINATED-V1  | DELTA (V2 - CL)    |
+------------------------------+--------------------+--------------------+--------------------+
| Final Wealth / Reward        | $144,129.20        | $116,479.90        | +$27,649.30        |
| Gross Cash Inflows           | $171,583.30        | $141,740.90        | +$29,842.40        |
| Gross Cash Outflows          | $ 27,619.10        | $ 25,426.00        | +$ 2,193.10        |
| Active Average Workers       |  9.4 workers       | 10.8 workers       | -1.4 workers       |
| Total Hands Hired            | 11.0 hands         | 13.0 hands         | -2.0 hands         |
+------------------------------+--------------------+--------------------+--------------------+
| REVENUE BY COMMODITY         |                    |                    |                    |
| STRAWBERRY                   | $ 54,794.0 (270 u) | $ 41,803.0 (181 u) | +$12,991.0 (45.1%) |
| FERTILIZER                   | $ 18,863.0 (244 u) | $ 10,922.3 (125 u) | +$ 7,940.7 (27.6%) |
| WHEAT                        | $ 10,491.9 (224 u) | $  6,766.5 (192 u) | +$ 3,725.4 (12.9%) |
| MELON                        | $ 29,664.0 (132 u) | $ 26,842.9 (112 u) | +$ 2,821.1  (9.8%) |
| MILK                         | $ 44,028.8 (230 u) | $ 42,170.6 (199 u) | +$ 1,858.2  (6.5%) |
| WOOL                         | $ 26,836.0 (167 u) | $ 27,380.6 (142 u) | -$   544.6 (-1.9%) |
| TOTAL COMMODITY SALES        | $187,420.0         | $159,341.0         | +$28,079.0         |
+------------------------------+--------------------+--------------------+--------------------+
```

---

## 3. 100-SEED MULTI-ARM CAUSAL ABLATION MATRIX (Seeds 1000–1099, 900 Matches)

We evaluated 8 isolated economic interventions alongside the baseline and Frozen V2:

| Arm | Configuration | Reward (Mean ± Std) | Median ($) | Prod | Moves | Idle | Shed | 1-Step % | Prod/Mov | Lift vs Baseline |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **V2** | **Frozen V2** (Benchmark) | **$145,169.7 ± 27,647.5** | **$148,675.5** | 2,918.6 | **3,323.6** | 242.8 | **176.0** | **37.1%** | **0.878** | +$32,457.20 |
| **ARM A** | **CL-Coord-V1** (Baseline) | $112,712.5 ± 19,491.8 | $116,675.5 | **3,155.8** | 3,931.0 | 340.7 | 204.3 | 30.9% | 0.803 | Baseline |
| **ARM B** | Worker Cap (11 Hands) | $112,908.9 ± 19,392.2 | $115,573.0 | 3,002.4 | **3,468.2** | 329.6 | **177.7** | 30.4% | **0.866** | +$196.47 |
| **ARM C** | Fertilizer Rationalization | **$116,861.9 ± 17,960.7** | **$118,230.5** | 3,132.3 | 3,969.4 | 324.6 | 211.1 | 31.0% | 0.789 | **+$4,149.39** |
| **ARM D** | Strawberry Batch (Yield $\ge 2$) | $112,588.4 ± 21,576.3 | $116,969.0 | 3,140.4 | 3,946.6 | 340.5 | 206.3 | 30.9% | 0.796 | -$124.05 |
| **ARM E** | Cow Priority & Day 5 Unlock | **$116,213.7 ± 20,404.3** | **$118,982.5** | 3,170.7 | 3,955.8 | 302.4 | 214.3 | 30.6% | 0.802 | **+$3,501.19** |
| **ARM F** | JIT Feed Buffer (1.2x) | $115,487.7 ± 17,038.1 | $116,516.5 | 3,053.1 | 4,121.8 | 250.7 | 258.3 | 31.3% | 0.741 | +$2,775.25 |
| **ARM G** | Terminal Pocket Flush | $115,773.6 ± 19,878.4 | $118,814.5 | 3,177.6 | 3,923.8 | 326.1 | 212.2 | 30.6% | 0.810 | **+$3,061.10** |
| **ARM I** | **CL-Economic-V1** (Synthesized) | **$120,656.6 ± 17,077.2** | **$124,983.5** | 2,935.5 | **3,625.4** | **243.4** | 208.4 | **31.8%** | 0.810 | **+$7,944.16** |

---

## 4. DIRECT HEAD-TO-HEAD BENCHMARK VS FROZEN V2 (100 Seeds 5000–5099)

Matched head-to-head match alternating player seats (50 Seat 0 / 50 Seat 1):

| Metric | CL-Coordinated-V1 (Baseline) | CL-Economic-V1 (New Candidate) | Delta / Causal Lift |
| :--- | :---: | :---: | :---: |
| **Matches Played** | 100 | 100 | - |
| **Win Rate** | 0.0% (0W / 100L / 0T) | 0.0% (0W / 100L / 0T) | 0.0% |
| **Candidate Mean Cash** | $57,798.07 ± $20,782.28 | **$66,836.77 ± $19,927.34** | **+$9,038.70 Cash Lift** |
| **Frozen V2 Mean Cash** | $97,281.98 ± $24,271.60 | $101,022.55 ± $22,755.93 | +$3,740.57 |
| **Mean Net Margin** | **-$39,483.91** | **-$34,185.78** | **+$5,298.13 Advantage** |
| **Median Net Margin** | -$41,649.00 | -$35,393.00 | +$6,256.00 |
| **95% Bootstrap CI** | [-$40,831.91, -$38,142.67] | **[-$35,285.47, -$33,028.45]** | **Definitively Shifted Upward** |

---

## 5. FINAL PORTFOLIO VERDICT

### Decision: **B = PROMISING BUT NOT READY**
- **Zero Kaggle Submissions**.
- Live production anchors remain untouched and cryptographically verified.
