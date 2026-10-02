# PHASE 015: FORENSIC RECONSTRUCTION & COMPILER PATH ANALYSIS

**Phase**: 015 — AEC Opportunity Engine + Candidate Synthesis Rescue  
**Chassis Freeze Hash**: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`  
**Focus**: End-to-End Compiler Trajectory Reconstruction & Headroom Loss Forensics  
**Status**: COMPLETE  

---

## 1. Executive Summary & Objective

In Phase 014, the Bounded Economic Headroom Audit probed **12,742 states** across 35 pristine development seeds (`249241..249275`) and identified **10,285 positive headroom states (80.72%)** with a mean headroom of **+$196.87 USD** and a maximum of **+$17,730.00 USD**.

Despite the presence of this massive economic potential in the game state, the frozen live foundation captured virtually none of it.

This forensic audit reconstructs the exact turn-by-turn execution path through the AEC compiler:
```text
OBSERVATION → ECONOMIC IR → EVENT DETECTOR → OPPORTUNITY ENGINE → 
CANDIDATE FUNNEL → COUPLEDPATCH → COUNTERFACTUAL SIMULATOR → SAFETY → DECISION
```
and proves precisely where and why Phase 014's positive states vanished.

---

## 2. Layer-by-Layer Causal Breakdown

Every positive headroom state discovered by the bounded oracle was mapped to its terminating compiler layer:

```text
ORACLE POSITIVE STATES (10,285 states = 100.0%)
  │
  ├── 1. EVENT DETECTOR / OPPORTUNITY ENGINE
  │     └── NOT_DETECTED (Category C): 8,066 states (78.43%) ──► [PRIMARY BOTTLENECK]
  │
  ├── 2. CANDIDATE GENERATOR / FUNNEL
  │     └── NOT_REPRESENTED (Category D): 2,185 states (21.24%) ──► [SECONDARY BOTTLENECK]
  │
  ├── 3. SAFETY CHECKER
  │     └── SAFETY_REJECTED: 16 states (0.16%)
  │
  ├── 4. COUNTERFACTUAL SIMULATOR
  │     └── COUNTERFACTUAL_REJECTED: 14 states (0.14%)
  │
  ├── 5. STATIC PRUNING GATES
  │     └── FILTERED: 2 states (0.02%)
  │
  └── 6. FOUNDATION COMMITTED
        └── NONE_AEC_COMMITTED: 2 states (0.02%)
```

### Key Takeaway:
**99.67% (10,251 out of 10,285 states)** of all missed economic headroom was lost in the **top two layers** of the compiler:
1. The detector failed to see the opportunity (78.43%).
2. The generator failed to represent the candidate action (21.24%).

The downstream compilation layers (`CoupledPatch`, `ReconnectionEngine`, `CounterfactualSimulator`, `SafetyChecker`) operated with **>99.9% fidelity and reliability**.

---

## 3. Forensic Trace: Where Positive States Disappear

We trace a canonical Phase 014 positive-headroom turn through each step of the compiler pipeline.

### Scenario: Seed `249241`, Step `312`
- **State**: Farm holds **55 units of Strawberry** in the shed.
- **Market**: Strawberry market price is **$142.00** ($+42\%$ above base $100.00).
- **Workers**: Worker 0 is traveling to plot `(7, 2)` to plant carrots. Hand 0 is hoeing.
- **V3 Baseline Action**: `{"farmer": ["MOVE", "EAST"], "hands": [["USE_TOOL"]], "market": []}`
- **Oracle Result**: Selling 10 Strawberries this turn produces **+$185.00 USD** terminal margin gain.

### Trace Through Compiler Layers:

```text
1. OBSERVATION:
   Ingests raw state (turn 312, cash $4,120, shed inventory: 55 Strawberry, 10 Wheat).

2. ECONOMIC IR:
   Constructs EconomicState. Correctly records 55 Strawberry in shed, price $142.00.

3. EVENT DETECTOR (aec/events/detectors.py):
   Evaluates differential rules:
   - Cash deviation: cash = $4,120 >= $200 (E2: False)
   - Shed alarm: shed_units = 65 < 95 (E3: False)
   - Market regime shift: abs(liquidity - 1.0) = 0.18 < 0.25 (E4: False)
   - Opponent supply shock: supply = 0 (E5: False)
   - Milestone ticks: 312 % 72 = 24 != 0 (E6: False)
   => Result: events = [] (ZERO EVENTS DETECTED)

4. AEC EXECUTOR FAST-PATH (aec/integration/executor.py, line 324):
   if not self.event_bus.has_events:
       telemetry.decision = "BACKBONE"
       telemetry.abstain_reason = "NO_EVENT_FAST_PATH"
       return baseline_action
   => RESULT: EXECUTION ABORTED. Zero opportunities searched. Zero candidates created.
   => State lost to Category C (NOT_DETECTED).
```

### What Happened If an Event Did Fire?
Suppose turn 312 occurred on step 288 (a shop reveal boundary where event `E6` fires):
```text
3. EVENT DETECTOR:
   events = [Event(E6_SHOP_INFORMATION_REVEAL)]

4. OPPORTUNITY ENGINE (aec/opportunities/__init__.py):
   Calls MarketOpportunityAnalyzer.analyze():
   market_orders = baseline_action.get("market", []) # []
   if len(market_orders) >= 2:
       ...
   => market_orders has length 0 (< 2).
   => OpportunityEngine returns ZERO market opportunities!

5. CANDIDATE GENERATOR (aec/patches/generator.py):
   Even if an opportunity was synthesized by a custom detector:
   PatchGenerator only has:
   elif fam == "DEPENDENCY_AWARE_MARKET_TIMING":
       current_orders = baseline_action.get("market", []) # []
       reordered, _ = transform(current_orders, ...)
       if reordered != current_orders:
           ...
   => reordered == [] == current_orders.
   => PatchGenerator emits ZERO candidate patches!
   => State lost to Category D (NOT_REPRESENTED).
```

---

## 4. Before / After Architecture Comparison

| Compiler Layer | Before (Phase 014 Live Foundation) | After (Phase 015 Rescue) |
| :--- | :--- | :--- |
| **Event Detection** | Purely differential ($\Delta\text{cash} > 200$, $\text{shed} \ge 95$). Blind to static holding states. | **Persistent-State Aware**: Detects uncommitted held inventory in favorable price regimes ($E13$). |
| **Fast-Path Guard** | Aborts when differential events $= []$. | Triggers on $E13$ persistent states; preserves fast-path only when truly inert. |
| **Opportunity Proposal** | `MarketOpportunityAnalyzer` requires $\ge 2$ pre-existing baseline market orders. | `AssetHoldingValuationTrigger` proposes autonomous realization opportunities for any uncommitted held asset. |
| **Candidate Synthesis** | `PatchGenerator` only reorders existing orders (`DEPENDENCY_AWARE_MARKET_TIMING`). | `AutonomousTrancheOrderSynthesizer` generates new depth-compatible sell orders even when baseline market is `[]`. |
| **Quantity Selection** | N/A (copies baseline quantities). | 6 structural quantity anchors ($q_{\text{min}}, q_{\text{dep}}, q_{\text{storage}}, q_{\text{depth}}, q_{\text{terminal}}, q_{\text{full}}$). |
| **Downstream Execution** | `CoupledPatch` + `ReconnectionEngine` (100% verified). | Reuses identical validated `CoupledPatch` and reconnect pipeline without modifications. |
| **Counterfactual Evaluation** | `CounterfactualSimulator` (100% verified). | Reuses identical validated 18-step exact simulation without heuristic shortcuts. |
| **Safety Certification** | `SafetyChecker` (100% verified). | Reuses identical multi-predicate safety defense-in-depth. |

---

## 5. Forensic Conclusion

The missing headroom in the AEC is **not** an optimization error, a simulation flaw, or an execution failure. It is entirely an **upstream visibility and expressiveness gap**:
1. **The compiler was blind**: It did not look at passive inventory holding states.
2. **The compiler was mute**: It could not express a market order unless V3 had already expressed one.

Phase 015 repairs both gaps directly at their structural roots.
