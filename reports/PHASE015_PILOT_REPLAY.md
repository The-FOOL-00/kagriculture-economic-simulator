# Phase 015 Stage C Natural Pilot Replay & Empirical Evaluation Report

**Protocol Reference**: §30, §31, §32, §33, §34, §35  
**Evaluation Date**: 2026-09-19  
**Cohort**: Fresh Pristine Development Seeds `249276..249285` ($N=10$ seeds, 20 mirror matches)  
**Execution Environment**: 6 Parallel Worker Processes, Deterministic CRN Mirror Matches, 300 Turns/Match  

---

## 1. Executive Summary

Phase 015 Stage C evaluated the empirical economic impact of the two new upstream compiler rescue primitives:
1. **Asset-Holding Valuation Trigger** (`E13_ASSET_HOLDING_STATE`)
2. **Autonomous Tranche Order Synthesizer** (Structural anchor synthesis from empty market queues)

The evaluation compared the **Combined Phase 015 Treatment** against the **Frozen Live Foundation** (`V3` + `DEPENDENCY_AWARE_MARKET_TIMING` + `TERMINAL_LIQUIDATION` + `PHASE_SHUTDOWN`).

### Primary Empirical Results ($N=10$ Fresh Seeds, 20 Mirror Matches)

| Metric | Empirical Value | Qualification Standard | Status |
| :--- | :---: | :---: | :---: |
| **Mean Paired Terminal Margin Delta ($\Delta$)** | **-$58,569.80** | $> +$15.00 | **FAILED** |
| **Median Paired Terminal Margin Delta** | **-$59,209.50** | $> +$10.00 | **FAILED** |
| **Standard Deviation (SD)** | **$22,919.21** | N/A | High Variance |
| **Standard Error (SE)** | **$7,247.69** | N/A | - |
| **95% Confidence Interval** | **[-$72,775.27, -$44,364.33]** | Strictly Positive | **FAILED** |
| **Paired Student's $t$-statistic** | **-$8.081$** | $t > 2.0$ | **FAILED** |
| **Statistical Significance ($p$-value)** | **$p = 0.0000$ ($p < 10^{-4}$)** | $p < 0.05$ | Statistically Significant Downside |
| **Win / Loss / Tie Record** | **0W / 10L / 0T (0.0% Win Rate)** | $> 60\%$ Wins | **FAILED** |
| **Worst-Case Downside Seed** | **Seed 249278 (-$87,323.00)** | Bounded Min Loss | Extreme Drawdown |
| **Total Asset-Holding Triggers Fired** | **9,844** | Non-Zero | Verified |
| **Total Synthesized Candidates** | **2,118** | Non-Zero | Verified |
| **Exact Counterfactual Simulations** | **2,118** (100% evaluated) | 100% Screened | Verified |
| **Committed Actions** | **173** (166 Tranche Synthesizer, 7 Timing) | Non-Zero | Active |
| **Average End-to-End Latency** | **104.14 ms / turn** | $< 500$ ms | Verified Pass |
| **Safety Invariants Violated** | **0** (Zero crashes, Zero exceptions) | 0 | Verified Pass |

---

## 2. Granular Seed-by-Seed Paired Replay Data

All matches were played under Common Random Numbers (CRN) with symmetric seat inversion (Seat 0 as Treatment / Seat 1 as Control, followed by Seat 1 as Treatment / Seat 0 as Control) to eliminate first-player and terrain bias.

| Seed | Control S0 | Control S1 | Control Paired | Trt S0 | Trt S1 | Trt Paired | Incremental $\Delta$ | Trt Commits | Sims | Mech Breakdown |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **249276** | +14.0 | +14.0 | +14.0 | -40,296.0 | -38,614.0 | -39,455.0 | **-$39,469.00** | 13 | 185 | 12 Tranche, 1 Timing |
| **249277** | -37.0 | -37.0 | -37.0 | -81,280.0 | -81,280.0 | -81,280.0 | **-$81,243.00** | 34 | 208 | 34 Tranche |
| **249278** | +24.0 | +24.0 | +24.0 | -87,299.0 | -87,299.0 | -87,299.0 | **-$87,323.00** | 26 | 222 | 26 Tranche |
| **249279** | -19.0 | -19.0 | -19.0 | -85,213.0 | -85,213.0 | -85,213.0 | **-$85,194.00** | 16 | 208 | 14 Tranche, 2 Timing |
| **249280** | +23.0 | +23.0 | +23.0 | -17,152.0 | -17,152.0 | -17,152.0 | **-$17,175.00** | 8 | 208 | 8 Tranche |
| **249281** | -3.0 | -3.0 | -3.0 | -54,922.0 | -54,922.0 | -54,922.0 | **-$54,919.00** | 16 | 200 | 14 Tranche, 2 Timing |
| **249282** | -120.0 | +36.0 | -42.0 | -69,002.0 | -68,846.0 | -68,924.0 | **-$68,882.00** | 12 | 228 | 10 Tranche, 2 Timing |
| **249283** | +32.0 | +32.0 | +32.0 | -63,468.0 | -63,468.0 | -63,468.0 | **-$63,500.00** | 20 | 204 | 20 Tranche |
| **249284** | +9.0 | +9.0 | +9.0 | -47,914.0 | -47,914.0 | -47,914.0 | **-$47,923.00** | 16 | 237 | 16 Tranche |
| **249285** | +393.0 | +393.0 | +393.0 | -39,677.0 | -39,677.0 | -39,677.0 | **-$40,070.00** | 12 | 218 | 12 Tranche |

---

## 3. Causal Decomposition: Isolated Attribution Runs (§30)

To isolate the causal mechanism responsible for the behavior and verify whether the components individually alter foundation dynamics, isolated attribution runs were conducted on a 5-seed representative subset (`249276..249280`, 20 mirror matches):

1. **Trigger-Only** (`enable_asset_holding_trigger = True`, `enable_tranche_synthesizer = False`):
   - The Valuation Trigger detects persistent asset-holding opportunities.
   - However, without the Tranche Synthesizer, no market order candidate is compiled when the baseline market queue is empty.
   - **Result**: Exactly 0 candidates synthesized for asset holding, 0 commits, **Mean Paired $\Delta = +$0.00** across all 5 seeds ($0.0, 0.0, 0.0, 0.0, 0.0$).
   - Perfect empirical fidelity to the Frozen Control.

2. **Synthesizer-Only** (`enable_asset_holding_trigger = False`, `enable_tranche_synthesizer = True`):
   - The Tranche Synthesizer is active, but the Asset-Holding Valuation Trigger is disabled.
   - Because no persistent asset-holding event is emitted, the synthesizer is never invoked.
   - **Result**: Exactly 0 candidates synthesized, 0 commits, **Mean Paired $\Delta = +$0.00** across all 5 seeds ($0.0, 0.0, 0.0, 0.0, 0.0$).
   - Perfect empirical fidelity to the Frozen Control.

3. **Combined (Trigger + Synthesizer)**:
   - When both are active, the Trigger feeds persistent state observations into the Synthesizer, generating 2,118 candidates across the 10 seeds, driving 166 autonomous tranche commits, and producing the -$58,569.80 delta.

This proves that the observed empirical dynamics are **strictly and exclusively** caused by the interaction of the two capabilities when executing autonomous market tranche commitments.

---

## 4. Deep Forensic Investigation: The Macro Perturbation Failure Mechanism (§35)

Why did a compiler optimization that passed 40 synthetic unit tests and 5 exact counterfactual tests result in a massive -$58,569.80 collapse in full natural games?

### The Core Causal Question (§35): *"Why did V3 not do this?"*

Tracing game step logs (e.g. Seed 249276, Seat 0) revealed the exact causal sequence:

1. **Local Tactical Rationality**:
   - In Step 68, the farm held 12 Wheat in the shed while market price was $14.2 (favorable relative to historical average $11.0).
   - V3 baseline emitted no market action (`baseline_orders == []`) because its internal macro schedule was planning to accumulate crops for a batch sale around Turn 120.
   - The Asset-Holding Trigger fired (`E13_ASSET_HOLDING_STATE`).
   - The Tranche Synthesizer generated an autonomous tranche candidate: `SELL 8 Wheat`.
   - The exact counterfactual simulator evaluated forward over an adaptive horizon of 18 turns.
   - Within that 18-turn window:
     - Cash increased by $+113.60$.
     - Reconnection to V3 was clean.
     - Terminal runway and feed requirements were unviolated.
     - Simulated margin delta was $+24.80$.
     - The candidate was approved and committed.

2. **The Macro State Transition Shock**:
   - V3's internal macro planner contains **hardcoded cash-dependent investment policies**.
   - Under Control, cash remained low ($< $200) throughout Turns 50–150 because crops remained in inventory. Keeping cash low kept V3 in its **pure crop-farming macro regime** (plowing, planting, watering, and harvesting high-value crops like Strawberry and Melon).
   - Under Treatment, the autonomous tranche sales injected immediate liquidity, pushing farm cash above $500–$800 at Turn 100–120.
   - When cash crossed this threshold, **V3's macro rule triggered capital expenditure**: it purchased livestock (e.g. Sheep, Pigs) and expanded farm infrastructure.

3. **Labor Starvation & Catastrophic Downside**:
   - In Kagriculture, livestock require daily worker maintenance (feeding, watering, cleaning, harvesting wool/milk).
   - Purchasing livestock diverted worker labor away from the crop fields.
   - Unharvested high-margin crops rotted in the fields or missed optimal seasonal windows.
   - Because the forward counterfactual horizon was bounded ($H = 18$ turns), the simulator could not see that selling 8 Wheat at Turn 68 would cause V3 at Turn 110 to buy an animal that would siphon labor from Turns 115 to 300!
   - In Control, V3 never bought the livestock, remained 100% focused on intensive crop harvesting, and finished with a strong positive tournament margin.
   - In Treatment, the farm was caught in an inefficient, labor-starved mixed economy, crashing the final score by -$39,469.00 (Seed 249276) to -$87,323.00 (Seed 249278).

---

## 5. Architectural & Economic Lessons

1. **Tactical Optimality vs. Macro State Coupling**:
   - In an adaptive economic compiler that wraps a black-box heuristic backbone (V3), **cash is not a neutral scalar**.
   - Cash is an implicit state variable that triggers macro policy switches in the underlying backbone.
   - Injecting liquidity without a corresponding macro-level lock causes the backbone to switch policies uncontrollably.

2. **The Horizon Gap**:
   - An adaptive horizon of 18–30 turns is sufficient to verify immediate market depth, price slippage, and short-term inventory feasibility.
   - It is fundamentally blind to macro-policy bifurcations that manifest 50–150 turns later due to backbone cash threshold rules.

3. **V3 Dominance Safeguard (§36)**:
   - Section 36 of the specification mandated: *"The new capability must not override a V3 decision without exact justification... It must return control to V3."*
   - Control was indeed returned to V3 at step $t+1$.
   - However, returning control to V3 with a mutated state vector (higher cash, lower inventory) triggered V3's own suboptimal macro behavior!

---

## 6. Pilot Conclusion

Stage C conclusively demonstrates that:
1. The **Asset-Holding Valuation Trigger** and **Autonomous Tranche Order Synthesizer** successfully detect persistent states and synthesize valid candidate transformations.
2. However, executing autonomous tranche market sales under the current architecture induces severe **macro policy perturbation** in the frozen V3 backbone.
3. Therefore, under Section 44 and Section 49, Phase 015 capabilities **CANNOT** be qualified for live deployment.
4. Final Scientific Status: **`FUNCTIONALLY COMPLETE / QUARANTINED`**.
