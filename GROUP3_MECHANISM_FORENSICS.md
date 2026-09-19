# AEC PHASE 013: GROUP 3 MECHANISM FORENSIC AUDIT & ATTRIBUTION REPORT

**Author**: Antigravity AI Research Agent (Phase 013 Lead)  
**Date**: 2026-09-19  
**Chassis Freeze Hash**: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`  
**Scope**: Complete 12-Stage Forensic Reconstruction of Group 3 Mechanisms (`SHOP_ARBITRAGE`, `PRODUCTION_ARBITRAGE`, `TERMINAL_CONVERSION`, `EMERGENCY_FEED_PURCHASE`) Across Phase 010, Phase 010B, Phase 011, and Phase 012 Replays

---

## 1. Executive Forensic Summary Matrix

| Mechanism | First-Gen Thesis | Candidates | Exact Sims | Commits | Main Rejection Cause | Missing Economic Dimension |
| :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| **`SHOP_ARBITRAGE`** | Exploit 72-turn shop unlock interval price elasticity (+15–25% price rebound) | 2,118 | 1,056 | 0 | `NO_CANDIDATE_CERTIFIED_SUPERIOR`: Withholding inventory created working capital drag; delayed daily morning seed purchases ($t \equiv 0 \pmod{24}$); bulk dump caused market clearing price slippage. | Working capital opportunity cost, continuous daily reinvestment drag, sequential market execution (non-commutativity of `BUY`/`SELL`), market depth elasticity, shed capacity, executable terminal realization. |
| **`PRODUCTION_ARBITRAGE`** | Cash $\to$ input $\to$ produce $\to$ output $\to$ sell lifecycle profit maximization | 2,656 | 1,328 | 0 | `NO_CANDIDATE_CERTIFIED_SUPERIOR`: 100% redundant with frozen V3 macro scheduler; V3 already optimizes crop selection dynamically; candidate purchases diverted capital from ongoing superior crop cycles. | Marginal headroom detection vs V3 baseline trajectory, non-redundancy test against V3 capability, structural labor opportunity cost, coupled multi-turn worker routing/delivery. |
| **`TERMINAL_CONVERSION`** | Convert raw inventory into higher-value liquidizable assets in endgame window (steps 680–716) | 138 | 70 | 0 | `NO_CANDIDATE_CERTIFIED_SUPERIOR`: Dominated by direct `TERMINAL_LIQUIDATION`; detector emitted raw sales labeled as conversions; multi-step conversion delayed liquidation, risking step 718 deadline. | Comparative valuation against direct liquidation ($\Delta = \text{Net}_{\text{conv}} - \text{Direct}_{\text{liq}} > 0$), rigorous remaining runway proof, worker transit reservation, shed headroom constraints. |
| **`EMERGENCY_FEED_PURCHASE`** | Procure wheat when total stock is less than herd size ($\text{wheat} < \text{herd}$) | 518 | 260 | 0 | `NO_CANDIDATE_CERTIFIED_SUPERIOR`: Inconclusive / dormant in natural play; V3 baseline avoids catastrophic starvation; reactive trigger generated unneeded purchases without irreversible failure. | Irreversible failure condition ($\text{consecutive\_unfed} \ge 1 \to 2$ escape risk), multi-path alternative analysis (buy vs convert vs buffer), downstream liquidity conflict (seed purchase starvation). |

---

## 2. Upstream Event Trigger Exposure & Opportunity Discovery Analysis

A forensic inspection of `aec/events/detectors.py`, `aec/events/event_types.py`, and `aec/integration/executor.py` reveals critical architectural relationships for Group 3 mechanisms:

```
[OBSERVE] -> [Economic IR] -> [detect_events()]
                                     |
    +--------------------------------+--------------------------------+
    |                                |                                |
    v                                v                                v
[E4: Market Shift]          [E6: Shop Reveal]              [E7/E8: Cutoff/Endgame]
[E10: Town Cycle Phase]     [E9: Starvation Risk]          [E12: Resource Bottleneck]
    |                                |                                |
    +--------------------------------+--------------------------------+
                                     |
                         [has_events == False?]
                              /          \
                           (YES)         (NO)
                            /              \
            [NO_EVENT_FAST_PATH]     [OpportunityEngine.detect_opportunities()]
            (Emits baseline)                  |
                                     1. ShopArbitrageDetector
                                     2. ProductionArbitrageDetector
                                     3. TerminalConversionDetector
                                     4. ResourceOpportunityAnalyzer (Feed)
```

### Forensic Deficiencies in Event Triggering:
1. **Production Arbitrage Starvation**: Production decisions primarily occur at day boundaries ($t \equiv 0 \pmod{24}$, step 0, 24, 48, ...). While $t \equiv 0 \pmod{72}$ triggers `E6_SHOP_INFORMATION_REVEAL`, non-72 day boundaries (steps 24, 48, 96, 120, ...) relied on serendipitous cash or capacity alarms. In their absence, `NO_EVENT_FAST_PATH` bypassed `ProductionArbitrageDetector`.
2. **Shop Arbitrage Temporal Alignment**: First-generation `ShopArbitrageDetector` checked `steps_to_unlock <= 12`. However, town consumption ticks occur every 4 steps (`step % 4 == 0`), whereas the shop inventory reset occurs every 72 steps. Conflating shop unlock with consumption cycles created mismatched anticipation windows.
3. **Emergency Feed Disconnect**: In `ResourceOpportunityAnalyzer`, emergency feed triggered whenever `total_wheat < animals_requiring_feed`. This is a static snapshot rather than a trajectory projection. In reality, animals only consume feed when a worker physically feeds them, and they only escape if unfed across two consecutive day boundaries (`consecutive_unfed >= 2`).

---

## 3. Deep 12-Stage Forensic Reconstruction by Mechanism

### A. Shop Arbitrage (`SHOP_ARBITRAGE`)

1. **Detector Trigger**:
   - `ShopArbitrageDetector.detect()` in `aec/opportunities/arbitrage.py`.
   - Calculated `next_unlock = ((step // 72) + 1) * 72` and fired when `1 <= steps_to_unlock <= 12`.
2. **Opportunity Formulation**:
   - Assumed a fixed $+20\%$ price rebound on `WHEAT`, `CARROT`, `TOMATO`.
   - Estimated relevance as `margin * 5.0`.
3. **Economic Interpretation**:
   - Treated the $+20\%$ nominal price increase as pure profit.
   - Completely ignored working capital opportunity cost, worker transit time, shed capacity, and market clearing price slippage.
4. **Dependency Analysis**:
   - Lacked any resource dependency modeling. Did not check whether holding inventory prevented daily seed purchases or cash flow obligations.
5. **Patch Generation**:
   - Flawed implementation in `aec/patches/generator.py`:
     ```python
     elif fam in ("SHOP_ARBITRAGE", "PRODUCTION_ARBITRAGE"):
         orders = copy.deepcopy(baseline_action.get("market", []))
         input_item = getattr(opp, "input_item", "") or getattr(opp, "item", "")
         if input_item and len(orders) < 10:
             orders.append(["BUY_SEED", input_item.replace("_SEED", ""), 1])
     ```
     Instead of compiling a market timing transformation or arbitrage sequence, it merely appended a single `BUY_SEED` order!
6. **Route / Trajectory Mutation**:
   - None. Zero physical worker movement or delivery.
7. **Reconnect**:
   - None required due to lack of worker mutations.
8. **Exact Counterfactual Simulation**:
   - In exact simulation, adding an arbitrary `BUY_SEED` order drained capital without any planned harvest/sale trajectory, resulting in immediate delta degradation.
9. **Economic Delta**:
   - Net delta was consistently negative or non-superior to baseline continuation.
10. **Safety Decision**:
    - Passed basic safety if cash was sufficient to buy the seed, but failed economic superiority check.
11. **Final Commit Gate**:
    - 0 commits out of 1,056 simulations.
12. **Downstream Economic Collapse**:
    - The first-generation formulation completely failed to implement actual arbitrage.

---

### B. Production Arbitrage (`PRODUCTION_ARBITRAGE`)

1. **Detector Trigger**:
   - `ProductionArbitrageDetector.detect()` in `aec/opportunities/arbitrage.py`.
   - Iterated over all crops in `CROP_SEED_PRICE`, estimated `net_profit = gross - seed_cost - 10.0`, and emitted opportunities if `net_profit >= 50.0`.
2. **Opportunity Formulation**:
   - Proposed planting crops whenever the theoretical gross revenue exceeded seed cost $+ \$10$.
3. **Economic Interpretation**:
   - Duplicated a rudimentary static crop profitability calculator.
   - Failed to recognize that V3 already selects the mathematically optimal crop portfolio based on growth cycles, soil state, and market depth.
4. **Dependency Analysis**:
   - Ignored land availability, worker location, watering requirements, and existing crop pipelines.
5. **Patch Generation**:
   - Similar to `SHOP_ARBITRAGE`, it merely appended `["BUY_SEED", crop, 1]` to baseline market orders.
6. **Route / Trajectory Mutation**:
   - None. The worker was not assigned to till, plant, water, or harvest!
7. **Reconnect**:
   - None.
8. **Exact Counterfactual Simulation**:
   - The simulator simulated buying an extra seed. Because no worker was routed to plant it, the seed sat unused in inventory, wasting working capital.
9. **Economic Delta**:
   - 100% of candidates lost money relative to baseline continuation.
10. **Safety Decision**:
    - Fails economic superiority gate.
11. **Final Commit Gate**:
    - 0 commits out of 1,328 simulations.
12. **Downstream Economic Collapse**:
    - The mechanism was functionally incomplete and completely redundant with the V3 macro scheduler.

---

### C. Terminal Conversion (`TERMINAL_CONVERSION`)

1. **Detector Trigger**:
   - `TerminalConversionDetector.detect()` in `aec/opportunities/terminal_conversion.py`.
   - Fired in steps 680–716 when `wheat_count >= 2`.
2. **Opportunity Formulation**:
   - Literally emitted `output_item="MONEY"`, stating `"Terminal liquidation conversion of {wheat_count} wheat"`.
3. **Economic Interpretation**:
   - Confounded conversion with direct liquidation. It did not transform wheat into flour, bread, or animal feed; it merely proposed selling the raw wheat!
4. **Dependency Analysis**:
   - Failed to evaluate whether converting raw goods into processed goods was possible before step 718.
5. **Patch Generation**:
   - `generator.py` inserted `["SELL", in_item, in_units]` into market orders.
6. **Route / Trajectory Mutation**:
   - None.
7. **Reconnect**:
   - None.
8. **Exact Counterfactual Simulation**:
   - The simulator compared selling wheat at step 690 vs the baseline selling it during terminal liquidation at step 718. Selling early produced no incremental value (and often worse prices before endgame absorption).
9. **Economic Delta**:
   - $\Delta \le 0$ relative to the validated foundation (`TERMINAL_LIQUIDATION`).
10. **Safety Decision**:
    - Neutral or rejected for lack of economic surplus.
11. **Final Commit Gate**:
    - 0 commits out of 70 simulations.
12. **Downstream Economic Collapse**:
    - `TERMINAL_CONVERSION` was a mislabeled, premature liquidation duplicate.

---

### D. Emergency Feed Purchase (`EMERGENCY_FEED_PURCHASE`)

1. **Detector Trigger**:
   - `ResourceOpportunityAnalyzer.analyze()` in `aec/opportunities/resource.py`.
   - Checked if `animals_requiring_feed > 0 and total_wheat < animals_requiring_feed`.
2. **Opportunity Formulation**:
   - Emitted `EMERGENCY_FEED_PURCHASE` with `deficit = animals_requiring_feed - total_wheat`.
3. **Economic Interpretation**:
   - Assumed any inventory shortfall was an immediate emergency, even if animals were already fed today or had 2 full days before escape risk.
4. **Dependency Analysis**:
   - Ignored alternative feed sources (e.g. harvesting mature wheat in the field, converting existing carried wheat, or purchasing hay).
   - Did not check if purchasing feed at step $t$ depleted cash required for morning seed purchases.
5. **Patch Generation**:
   - Inserted `["BUY_PRODUCT", "WHEAT", deficit]` into market orders and attempted multi-worker coordination to pick up and feed.
6. **Route / Trajectory Mutation**:
   - Successfully created worker tasks (`PICKUP` and `FEED`) when auxiliary hands were available.
7. **Reconnect**:
   - Integrated with `MultiWorkerLogisticsCoordinator`.
8. **Exact Counterfactual Simulation**:
   - In synthetic tests with starving animals, it succeeded.
   - In natural tournament matches, the V3 baseline never allowed animals to starve. The candidate was evaluated against a baseline that was already safe, meaning the emergency purchase incurred unnecessary capital and labor cost with zero benefit.
9. **Economic Delta**:
   - $\Delta = 0$ or negative in natural play.
10. **Safety Decision**:
    - Passed safety checks, but rejected by `WinModel` because baseline continuation had identical animal survival without the cost.
11. **Final Commit Gate**:
    - 0 commits in natural tournament matches.
12. **Downstream Economic Collapse**:
    - Correctly abstained in clean matches, but lacked causal differentiation between imminent catastrophe and harmless buffer fluctuations.

---

## 4. Root Causal Conclusions & Guidelines for Second-Generation Rescue

1. **Local Spread $\ne$ Global Value**:
   - Gross price margins must be discounted by working capital drag, worker opportunity cost, and market depth elasticity.
2. **Do Not Rebuild the Backbone Macro Scheduler**:
   - `PRODUCTION_ARBITRAGE` must search strictly for **marginal headroom** (unforeseen market shocks, idle worker slots, newly matured inputs) that V3 cannot exploit from its current state.
3. **True Transformation vs Liquidation**:
   - `TERMINAL_CONVERSION` must model actual commodity transformation and prove $\text{Net Conversion Value} > \text{Direct Liquidation Value}$ within the strict remaining runway.
4. **Causal Irreversibility Standard**:
   - `EMERGENCY_FEED_PURCHASE` must activate only when the baseline continuation leads to an irreversible loss (animal escape `consecutive_unfed >= 2`), and the purchase preserves net economic value without causing crop cycle starvation.
