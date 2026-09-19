# PHASE 015: AUTONOMOUS TRANCHE ORDER SYNTHESIZER SPECIFICATION

**Phase**: 015 — AEC Opportunity Engine + Candidate Synthesis Rescue  
**Component**: Capability B — Autonomous Tranche Order Synthesizer  
**Chassis Freeze Hash**: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`  
**Scientific Role**: Candidate Representation & Generative Market Action Rescue  
**Status**: SPECIFIED / IMPLEMENTED  

---

## 1. Problem Definition & Empirical Motivation

In Phase 014, the Bounded Economic Headroom Audit proved that **21.24% (2,185 states)** of positive headroom states were lost to **Candidate Representation Defects** (`Category D`, `NOT_REPRESENTED`).

### The Defect in Existing Market Generators
In the live foundation, market mechanisms (`DEPENDENCY_AWARE_MARKET_TIMING`) are designed exclusively to **perturb existing orders**:
```python
market_orders = baseline_action.get("market", [])
if len(market_orders) >= 2:
    reordered, _ = transform_dependency_aware_market_timing(market_orders, econ_state)
```
If the V3 backbone emits an empty market queue (`market: []`) — which occurs in >92% of turns because workers are traveling or tending fields — the generator has nothing to reorder. The compiler lacks the expressiveness to **synthesize a new market order from scratch**.

---

## 2. Core Architectural Design: Autonomous Order Synthesis

The **Autonomous Tranche Order Synthesizer** decouples candidate generation from the presence of baseline market actions. When an asset-holding opportunity is detected, the synthesizer autonomously formulates candidate market sell orders even when:
$$\text{baseline\_action}["\text{market}"] == [\;]$$

### 2.1 Synthesis Pipeline
```text
Asset-Holding Opportunity
       ↓
Inventory Realizability & Hard Dependency Screening
       ↓
Structural Quantity Anchor Selection
       ↓
Intra-Basket Sequential Order Construction
       ↓
Candidate CoupledPatch Formulation
       ↓
Candidate Funnel (Stages S1..S9)
       ↓
Exact Counterfactual Simulation (Stage S10)
       ↓
Safety Certificate Verification
       ↓
Commit / Abstain
```

---

## 3. Strict Inventory Realizability & Dependency Gating

Before proposing any sell action, the synthesizer validates **7 hard realizability preconditions**:

1. **Existence**: Commodity exists in physical inventory (`shed_inventory[item] > 0` or `worker.cargo[item] > 0`).
2. **Ownership**: Inventory belongs to the active player.
3. **Hard Feed Reservation**: If the farm owns livestock (`ANIMAL` count $> 0$), wheat required for feed security is strictly protected:
   $$Q_{\text{wheat\_reserved}} = N_{\text{animals}} \times \text{FeedRunwayTurns}$$
   $$Q_{\text{uncommitted\_wheat}} = \max(0, Q_{\text{shed\_wheat}} - Q_{\text{wheat\_reserved}})$$
   Wheat protected by feed security is **strictly un-sellable**.
4. **Hard Seed/Production Dependency**: Items required for scheduled mandatory planting or processing are preserved.
5. **Legality**: Item is an admissible game product (`PRODUCTS = (WHEAT, CARROT, TOMATO, STRAWBERRY, MELON, EGG, MILK, WOOL, FERTILIZER)`).
6. **Market Admissibility**: Current town market accepts the commodity.
7. **Order Limit Boundary**: Number of resulting market orders $\le 10$ (engine ceiling).

---

## 4. Structural Quantity Generation (Anti-Combinatorial Bounding)

Blindly enumerating every integer quantity ($q \in \{1, 2, \dots, Q_{\text{held}}\}$) would cause a catastrophic combinatorial explosion in simulation budget.

Instead, the synthesizer constructs candidates using **6 Structural Quantity Anchors**:

| Quantity Anchor | Formula / Definition | Economic Rationale |
| :--- | :--- | :--- |
| **$q_{\text{min}}$** | $\min(1, Q_{\text{uncommitted}})$ or $5$ | Minimal viable tranche; tests market price elasticity without committing capital. |
| **$q_{\text{dependency}}$** | $\lceil \text{CashDeficit} / P_{\text{live}} \rceil$ | Smallest parcel that raises necessary working capital to service pending obligations (wages, seeds). |
| **$q_{\text{storage}}$** | $\max(0, \text{shed\_units} - 80)$ | Storage-clearing tranche to relieve shed congestion before incoming harvest causes overflow discard. |
| **$q_{\text{depth}}$** | $\min(10, Q_{\text{uncommitted}})$ | Market-depth-compatible parcel; fits into a single atomic order without exceeding standard absorption limits. |
| **$q_{\text{terminal}}$** | If step $\ge 680$: $Q_{\text{uncommitted}}$ | Endgame liquidation tranche; prioritizes liquidation before step 718 deadline. |
| **$q_{\text{full}}$** | $Q_{\text{uncommitted}}$ | Complete uncommitted liquidation (partitioned into 10-unit atomic orders if $>10$). |

### Deduplication & Bounding
The raw anchor quantities are:
1. Clamped to $[1, Q_{\text{uncommitted}}]$.
2. Deduplicated (e.g. if $q_{\text{storage}} == q_{\text{min}}$, only one candidate is emitted).
3. Bounded to at most $4$ candidate quantities per commodity per step.

### Local Quantity Refinement (Post-Simulation Anchor Search)
If a primary candidate quantity $q^*$ achieves a positive exact margin delta ($\Delta_{\text{margin}} > 0$), the synthesizer performs a pre-decision local refinement:
$$q \in \{q^* - 1, \; q^*, \; q^* + 1\}$$
This ensures the selected tranche captures optimal clearing depth without over-saturating price elasticity.

---

## 5. Preservation of Sequential Market Semantics

The game engine evaluates market orders sequentially within the turn:
1. Each order executes in list order (`market[0]`, then `market[1]`, etc.).
2. Order execution updates price elasticity and town clearing depth dynamically.
3. Order non-commutativity: `SELL` before `BUY` provides cash for the buy; `BUY` before `SELL` requires existing cash.

The synthesizer strictly preserves sequential semantics:
- **Case 1 (Empty Baseline Market Queue)**:
  `market = [["SELL", item, q]]`
- **Case 2 (Baseline Emitted Buy Orders)**:
  The synthesizer inserts the `SELL` order **ahead of** the `BUY` orders:
  `market = [["SELL", item, q]] + baseline_market`
  This unlocks working capital to service the purchase while preserving all baseline buy orders.
- **Case 3 (Baseline Already Contains Sell Orders for Same Commodity)**:
  The synthesizer evaluates whether to merge quantities or stage tranches, ensuring no order exceeds 10 units and total orders $\le 10$.

---

## 6. Interaction with Validated Foundation Mechanisms

The synthesizer does NOT replace or disable foundation mechanisms:
1. **Dependency-Aware Market Timing**: Continues to optimize causal reordering of pre-existing baseline orders.
2. **Terminal Liquidation**: Continues to enforce final emergency liquidation at step 718. The synthesizer operates upstream ($t < 718$), discovering when *earlier* liquidation is mathematically superior to waiting for step 718.
3. **Phase Shutdown**: Continues to enforce late-stage seed purchase bans.

---

## 7. Telemetry & Causal Attribution

For every synthesized candidate, the compiler records full audit telemetry:
```json
{
  "candidate_synthesized": true,
  "candidate_family": "AUTONOMOUS_TRANCHE_ORDER_SYNTHESIZER",
  "candidate_quantity": 10,
  "candidate_reason": "DEPTH_COMPATIBLE_TRANCHE",
  "commodity": "STRAWBERRY",
  "baseline_queue_len": 0,
  "uncommitted_available": 45,
  "simulated_delta_margin": 142.50,
  "simulated_delta_cash": 1450.00,
  "safety_passed": true,
  "committed": true,
  "why_v3_did_not_do_this": "V3_PASSIVE_MARKET_QUEUE: Macro plan scheduled no market order while workers were traveling to plot (4,7)."
}
```

The causal field `why_v3_did_not_do_this` enforces that the compiler never claims credit for an action V3 would have executed anyway.
