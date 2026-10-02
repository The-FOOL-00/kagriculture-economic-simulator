# AEC PHASE 012: GROUP 2 MECHANISM FORENSIC AUDIT & ATTRIBUTION REPORT

**Author**: Antigravity AI Research Agent (Phase 012 Lead)  
**Date**: 2026-09-19  
**Chassis Freeze Hash**: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`  
**Scope**: Complete 12-Stage Forensic Reconstruction of Group 2 Mechanisms (`TOWN_CYCLE`, `EMERGENCY_RECOVERY`, `OPPONENT_PREEMPT_SELL`, `RESOURCE_CONVERSION`) Across Phase 004, Phase 010, and Phase 010B Replays

---

## 1. Executive Forensic Summary Matrix

| Mechanism | Prior Candidates | Prior Exact Sims | Prior Commits | Prior Outcomes | Main Rejection Point | Main Failure Mode | Missing Economic Variable |
| :--- | :---: | :---: | :---: | :---: | :--- | :--- | :--- |
| **`TOWN_CYCLE`** | 1,337 | 682 | 247 | -$36,655.33 / seed ($t=-2.55, p=0.0108$) | `DELAY_SALE` deleted baseline SELL orders without checking working capital; starved cash on day-boundary turns ($t \equiv 0 \pmod{24}$); shed filled to 100 blocking field worker drops; delayed single-turn dump collapsed market clearing price elasticity. | Working capital obligations, mandatory future purchases, shed buffer preservation, sequential price elasticity of bulk dumping, inventory optionality. |
| **`EMERGENCY_RECOVERY`** | 296 | 148 | 20 | -$25,792.00 / seed ($t=-5.36, p=0.0000$) | Premature panic threshold; dumped entire shed inventory of high-value crops to pay wages baseline would naturally cover; inserted wheat purchase into shed that never physically fed starving animals; broke harvest-water-sell synchronization. | Irreversibility classification (reversible vs recoverable vs emerging vs hard failure), minimal surgical intervention, physical delivery to livestock, avoided damage metric. |
| **`OPPONENT_PREEMPT_SELL`** | 7,812 | 3,906 | 2 | -$96.67 / seed (-$145.00 / commit) | Point prophecy of rival dumping failed; preemptive selling dumped stock at low prices before town consumption peak, exhausting market depth; self-inflicted price depression hurt subsequent harvests. | Bounded uncertainty / scenario analysis, self-value dominance (opponent loss $\ne$ our gain), capacity/route preemption instead of premature market dumping. |
| **`RESOURCE_CONVERSION`** | 138 (term) / Phase 004 | 70 | 0 (0/50 wins) | -$258.96 ITT delta in Phase 004 | Working capital lockup in raw inputs; diverted workers from high-yield crops; delayed conversion outputs caused planting defaults; terminal conversion dominated by `TERMINAL_LIQUIDATION`. | Margin-first comparative valuation (`KEEP` vs `CONVERT` vs `BUY` vs `PRODUCE`), structural liquidity safety, marginal labor opportunity cost, realizable terminal runway. |

---

## 2. Global Architectural Defect: Event Trigger Exposure & Fast-Path Starvation (§29)

In auditing the compiler's upstream event detection pipeline (`aec/events/detectors.py` and `aec/integration/executor.py`), a critical structural flaw was uncovered:

```
[OBSERVE] -> [Economic IR]
                 |
                 v
       [detect_events()]  <--- ONLY detects E1 (Weed), E2 (Cash < $200), E3 (Shed >= 95),
                 |              E4 (Price shift > 25%), E5 (Opp supply >= 4), E6 (Step % 72 == 0),
                 |              E7 (Cutoffs 574, 622, 670), E8 (Step >= 670)
                 v
     [has_events == False?]
          /              \
       (YES)             (NO)
        /                  \
[NO_EVENT_FAST_PATH]     [OpportunityEngine.detect_opportunities()]
Emits baseline untouched!         |
                         Calls Emergency, Town Cycle, Resource Analyzers!
```

### Forensic Consequences for Group 2:
1. **Starvation of Emergency Recovery**: If livestock was starving at step 100, but cash was $250 and shed had 10 items, `detect_events` emitted **zero events**. As a result, `NO_EVENT_FAST_PATH` returned baseline immediately, and `EmergencyRecoveryDetector` was completely bypassed until cash dipped below $200 or the animal died.
2. **Phase Mismatch in Town Cycle**: `E6_SHOP_INFORMATION_REVEAL` fired strictly AT step 72 (`step % 72 == 0`), not during the anticipation window (steps 64–71) when cycle timing transformations must be planned.
3. **Resource Deficit Invisibility**: Upstream event detection possessed no trigger for feed stock depletion or input shortages for active production structures.

This proves that **Group 2 mechanisms were exposed inconsistently**, firing only as accidental side-effects of unrelated cash or market events.

---

## 3. Detailed 12-Stage Forensic Reconstruction by Mechanism

### A. Town / Cycle Intelligence (`TOWN_CYCLE`)

1. **Detector Trigger**:
   - `TownCycleSignalDetector.detect()` in `aec/opportunities/town_cycle.py`.
   - Extracted 72-step shop interval phase. Fired `DELAY_SALE` when `1 <= steps_to_tick <= 3` and expected absorption $> 0$.
2. **Opportunity Formulation**:
   - Proposed omitting baseline `SELL` orders to capture a projected +$3/unit price bump.
3. **Economic Interpretation**:
   - Valued only the immediate expected unit price increase ($\Delta p \times q$). Ignored working capital, seed purchasing deadlines, and shed buffer capacity.
4. **Dependency Analysis**:
   - Treated market orders as independent of field operations, failing to recognize that liquidating crops funds the continuous purchase of seeds on day transitions ($t \equiv 0 \pmod{24}$).
5. **Patch Generation**:
   - `PatchGenerator` filtered out baseline `SELL` orders from the action basket.
6. **Route / Trajectory Mutation**:
   - None (market order omission only).
7. **Reconnect**:
   - Not applicable for pure market order deletion.
8. **Exact Counterfactual Simulation**:
   - During rollout, delayed sale produced zero cash on turn $t$. Baseline agent executed seed purchases, while candidate failed due to cash deficit.
9. **Economic Delta**:
   - Evaluated over short horizons ($H=6$), where the withheld sale looked neutral or marginally favorable if the bump occurred inside $H$.
10. **Safety Decision**:
    - `SafetyChecker` passed the patch because cash remained non-negative on turn $t$ (omitting a sell order does not cause immediate debt).
11. **Final Commit Gate**:
    - High commit rate (247 commits across 6 matches; 18.5% commit rate).
12. **Downstream Economic Collapse**:
    - Withheld cash prevented seed purchases; fields remained unplanted for full 24-turn cycles.
    - Shed reached 100 items; workers carrying harvested crops could not deposit, freezing harvesting.
    - Delayed lump-sum dumping exceeded town market depth, triggering massive price elasticity slippage. Net loss: **-$36,655.33 / seed**.

---

### B. Emergency Recovery (`EMERGENCY_RECOVERY`)

1. **Detector Trigger**:
   - `EmergencyRecoveryDetector.detect()` in `aec/opportunities/emergency.py`.
   - Triggered when `cash < wages_due_tonight` with `steps_to_night <= 6`, or `turns_to_starve <= 12`.
2. **Opportunity Formulation**:
   - Emitted `EMERGENCY_FEED` or `EMERGENCY_LIQUIDATE` with estimated relevance equal to full asset cost.
3. **Economic Interpretation**:
   - Treated normal operational liquidity dips as existential threats, failing to test whether baseline planned sales would naturally resolve the deficit.
4. **Dependency Analysis**:
   - Assumed buying wheat to shed solved animal starvation, ignoring the physical worker transportation dependency (worker must pick up wheat and deliver to pasture/coop).
5. **Patch Generation**:
   - Insolvency: dumped all shed inventory of top commodity (`orders.insert(0, ["SELL", p, shed[p]])`).
   - Starvation: inserted `["BUY_PRODUCT", "WHEAT", 1]`.
6. **Route / Trajectory Mutation**:
   - None; no worker was routed to feed the animal!
7. **Reconnect**:
   - Control was not cleanly transitioned back to backbone.
8. **Exact Counterfactual Simulation**:
   - Evaluated over short horizon ($H=6$). The emergency liquidation generated immediate cash, creating an artificial local surplus over baseline.
9. **Economic Delta**:
   - False positive: $\Delta_{\text{cash}} > 0$ locally, masking the destruction of optimized batch marketing.
10. **Safety Decision**:
    - Safety passed (high cash).
11. **Final Commit Gate**:
    - 20 commits across 6 matches.
12. **Downstream Economic Collapse**:
    - Dumping shed inventory saturated market clearing depth at depressed prices.
    - Buying wheat depleted cash while animals continued to starve because workers never delivered the feed.
    - Baseline harvest-water-sell synchronization was destroyed. Net loss: **-$25,792.00 / seed**.

---

### C. Opponent Preemption (`OPPONENT_PREEMPT_SELL`)

1. **Detector Trigger**:
   - `OpponentPreemptionDetector.detect()` in `aec/opportunities/preemption.py`.
   - Triggered whenever `pressure_state.sale_pressure[product] >= 0.5`.
2. **Opportunity Formulation**:
   - Projected that rival would dump within 1–2 turns, reducing price by 20%. Emitted preemption opportunity.
3. **Economic Interpretation**:
   - Treated uncertain rival intention as deterministic fact ("point prophecy").
4. **Dependency Analysis**:
   - Did not evaluate the opportunity cost of selling inventory before peak town absorption ticks.
5. **Patch Generation**:
   - Inserted immediate `["SELL", product, qty]` into market basket.
6. **Route / Trajectory Mutation**:
   - None.
7. **Reconnect**:
   - N/A.
8. **Exact Counterfactual Simulation**:
   - Baseline continuation held inventory; candidate dumped inventory immediately.
9. **Economic Delta**:
   - When rival did not dump, baseline captured higher prices later, while candidate locked in low price and saturated market.
10. **Safety Decision**:
    - Passed safety.
11. **Final Commit Gate**:
    - 2 commits on seed 249082; abstained on other seeds.
12. **Downstream Economic Collapse**:
    - On seed 249082, the 2 commits caused -$290.00 loss (-$145/commit). Rival held inventory; candidate dumped prematurely, depressing price for its own future harvests.

---

### D. Resource Conversion (`RESOURCE_CONVERSION`)

1. **Detector Trigger**:
   - `ConversionDiscoveryEngine.discover_conversion_paths()` in `aec/resource/conversions.py`.
2. **Opportunity Formulation**:
   - Proposed multi-step conversion chains (e.g. wheat $\to$ flour/egg/animal products).
3. **Economic Interpretation**:
   - Evaluated gross margin ($\text{Price}_{\text{target}} - \text{Price}_{\text{source}}$) without deducting worker opportunity cost or working-capital time value.
4. **Dependency Analysis**:
   - Failed to model the worker opportunity cost: diverting a worker for 3 turns to transport and process inputs meant unwatered crops and missed harvest deadlines.
5. **Patch Generation**:
   - Multi-action worker paths to fetch inputs and operate structures.
6. **Route / Trajectory Mutation**:
   - Heavy worker diversion away from agricultural quadrants.
7. **Reconnect**:
   - Waypoints frequently failed due to long duration ($>12$ turns).
8. **Exact Counterfactual Simulation**:
   - Phase 004 simulations demonstrated continuous capital depletion and worker displacement.
9. **Economic Delta**:
   - Consistently negative ($\Delta < -$250).
10. **Safety Decision**:
    - Frequently tripped working capital safety thresholds.
11. **Final Commit Gate**:
    - 0 commits in Phase 010 (terminal conversion); 50/50 losses in Phase 004.
12. **Downstream Economic Collapse**:
    - Capital lockup in non-liquid intermediate goods led to inability to buy high-value seeds; terminal conversion was dominated by direct raw liquidation.

---

## 4. Root-Cause Summary & Causal Diagnosis

The forensic evidence demonstrates that the failures of Group 2 mechanisms were **not caused by a flawed architectural destination**, but by **pathological first-generation formulation errors**:
1. **Isolated Action Valuation**: Valuing the immediate trade or conversion rather than the complete multi-turn economic state transition.
2. **Liquidity & Obligation Blindness**: Omitting mandatory future seed purchases, wages, and feed from market timing decisions.
3. **Panic vs. Damage Avoidance**: Treating normal operational fluctuations as emergencies and responding with macro-destructive inventory dumping.
4. **Point Prophecy vs. Bounded Uncertainty**: Formulating opponent preemption around fragile predictions of rival actions rather than robust self-value dominance.
5. **Gross Margin vs. Net Opportunity Cost**: Calculating conversion profitability without deducting the shadow value of diverted labor.

These five root causes define the exact structural boundaries for the Phase 012 Second-Generation Rescue.
