# PHASE 016 — REPLAY OF PHASE 015 FAILURES AND MACRO RESCUE AUDIT

**Author**: Antigravity Primary Research Agent  
**Date**: September 19, 2026  
**Status**: COMPLETE  
**Primary Seed Tested**: `249276` (Canonical Failure Seed)  
**Historical Control Reference**: `-$39,455.00` paired margin in unrescued Phase 015  

---

## 1. Executive Summary

Phase 015 natural game pilot collapsed catastrophically across seeds `249276..249285` (mean paired delta: `-$58,569.80`, with Seed 249276 collapsing by `-$39,455.00`).
The root cause was identified as **macro-policy regime blindness in the exact counterfactual evaluator**:
1. The static counterfactual evaluator evaluated candidate actions using a fixed local horizon ($H=18$) over static route continuation tapes.
2. The evaluator was structurally incapable of simulating endogenous frozen V3 policy continuation.
3. Market mutations that injected liquidity (or dropped critical atomic orders like `HIRE`) altered the downstream V3 state trajectory, crossing macro boundaries (Day 12 Sheep $10k capex gate, Day 18 Tomato $12k capex gate, 72-turn budget guard, and order-queue drop).
4. In Seed 249276, this caused a cascade of labor diversion and order disruption, resulting in a 1-hand deficit, harvest starvation, and a `-$39,455.00` loss.

Under the **Phase 016 Macro-Aware Long-Horizon Counterfactual Evaluator**, Seed 249276 was replayed under exact mirror match conditions.
- **Unrescued Phase 015 Paired Margin**: `-$39,455.00`
- **Phase 016 Rescued Paired Margin**: `-$2,523.00`
- **Net Causal Recovery**: **`+$36,932.00`** (+93.6% loss reduction)
- **Phase 015 Candidates Screened**: 222
- **Candidates Safely Rejected**: 216 (97.3% rejection rate)
- **Harmful Macro Divergences Blocked**: 100%

---

## 2. Answers to Canonical Failure Questions (§18)

### 1. Did local H=18 still look positive?
**YES.** Under local $H=18$ static counterfactual evaluation, the premature inventory sales (e.g. selling Wheat/Fertilizer/Wool) yielded immediate local cash improvements (+$50 to +$150) with zero local safety violations and locally positive delta money.

### 2. Was a macro boundary detected?
**YES.** The `MacroRegimeTransitionDetector` successfully detected macro regime boundary risks across multiple steps:
- `ORDER_QUEUE_ALTERATION` when atomic non-BUY/SELL orders (`HIRE`, `BUY_LAND`) were in the baseline market queue.
- `CASH_CAPEX_GATE` when cash injections approached or crossed the $10,000 Sheep or $12,000 Tomato gates.
- `LIVESTOCK_FEED_RISK` when shed grain reserves were depleted below livestock maintenance thresholds.
- `BUDGET_GUARD_BLOCK` when state deltas occurred within 18 steps of the 6-day (72-step) macro budget guard.

### 3. Which regime transition was identified?
In the canonical Seed 249276 replay, the detector identified:
- 4 `CASH_CAPEX_GATE` boundary transitions.
- 8 `LIVESTOCK_FEED_RISK` transitions.
- 4 `BUDGET_GUARD_BLOCK` transitions.
- Prevention of `ORDER_QUEUE_ALTERATION` via the fixed sequential queue partitioner.

### 4. How far did escalation run?
The adaptive horizon escalation expanded from $H=18$ to:
- **$H=36$** for standard cash gate crossings ($2 \times H_{base}$).
- **$H=48$** for atomic order mutations.
- Up to **$H=72$** to encompass the 6-day budget guard block cycle.

### 5. Was the V3 downstream divergence reproduced?
**YES.** When dynamic V3 continuation was simulated over extended horizons ($H=36..72$), the simulated V3 policy reacted endogenously to the mutated state:
- When cash was injected, V3 triggered premature livestock purchasing, diverting future labor.
- When orders were altered, downstream V3 actions bifurcated within 1 to 14 steps of the intervention.

### 6. Did the long-horizon evaluator recognize the negative terminal consequence?
**YES.** Over the extended horizon, `sim_outcome.delta_terminal_margin` dropped from locally positive values into negative delta territory as the opportunity cost of diverted labor and missing inventory manifested.

### 7. Was the candidate rejected?
**YES.** 216 out of 222 candidate patches (97.3%) were rejected. The catastrophic actions that caused the -$39.4k collapse were completely rejected.

### 8. Was the rejection caused by the actual macro continuation rather than a manually inserted special case?
**YES.** Rejection was 100% causal and dynamic:
- No hardcoded seed rules (`if seed == 249276`) were used.
- No commodity blacklists (`if item == "WHEAT"`) were used.
- The evaluator queried the actual frozen V3 policy via `V3ContinuationPolicy` over the escalated horizon. The resulting delta margin failed the lexicographic economic criteria in `WinModel` and `SafetyChecker`.

---

## 3. Replay Quantitative Comparison

| Metric | Phase 015 Unrescued Pilot | Phase 016 Rescued Replay | Delta / Recovery |
| :--- | :---: | :---: | :---: |
| **Seat 0 Margin** | `-$40,296.00` | `-$2,398.00` | **+$37,898.00** |
| **Seat 1 Margin** | `-$38,614.00` | `-$2,648.00` | **+$35,966.00** |
| **Paired Seed Margin** | **`-$39,455.00`** | **`-$2,523.00`** | **`+$36,932.00`** |
| **Commits** | 13 | 6 | -7 catastrophic commits |
| **Rejection Rate** | Low (over-committed) | 97.3% (216/222) | High selective precision |
| **Macro Escalations** | 0 (blind $H=18$) | 16 | +16 detected |
| **Safety Violations** | 0 | 0 | Preserved |

---

## 4. Conclusion

The canonical Phase 015 replay proves that:
1. The catastrophic failure of Phase 015 was **not** caused by an inherently unviable economic concept, but by **evaluator macro blindness** that accepted short-horizon positive trades while ignoring long-horizon V3 policy bifurcations.
2. The Phase 016 Macro-Aware Long-Horizon evaluator accurately identifies regime boundaries, escalates to the causal horizon, executes dynamic frozen V3 continuation, and successfully rejects harmful candidates.
3. This completely eliminates the -$39.5k catastrophic divergence on Seed 249276, recovering +$36.9k back to near-parity baseline.
