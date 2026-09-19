# PHASE 015: ASSET-HOLDING VALUATION TRIGGER SPECIFICATION

**Phase**: 015 — AEC Opportunity Engine + Candidate Synthesis Rescue  
**Component**: Capability A — Asset-Holding Valuation Trigger  
**Chassis Freeze Hash**: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`  
**Scientific Role**: Upstream Compiler Opportunity Detection Rescue  
**Status**: SPECIFIED / IMPLEMENTED  

---

## 1. Problem Definition & Empirical Motivation

In Phase 014, the Bounded Economic Headroom Audit across 35 pristine development seeds (50,330 turns) demonstrated that **80.72% of turns exhibit measurable positive economic headroom** (mean +$196.87 USD, median +$27.00 USD, max +$17,730.00 USD).

Crucially, **78.43% (8,066 states)** of all positive headroom states were lost directly to **Detector Blindness** (`Category C`, `NOT_DETECTED`). 

### The Root Cause of Detector Blindness
The existing `EventDetector` and `OpportunityEngine` evaluate game turns exclusively through **differential changes** between consecutive ticks:
- `E2_CASH_DEVIATION`: $\Delta\text{cash} > \$200$
- `E3_SHED_CAPACITY_RISK`: $\text{shed\_stock} \ge 95$
- `E4_MARKET_REGIME_SHIFT`: $|\text{liquidity} - 1.0| \ge 0.25$
- `E5_OPPONENT_SUPPLY_SHOCK`: $\Delta\text{supply} \ge 4$

When a farm holds 30–80 units of mature high-value crops (Strawberries, Melons) in the shed during a prolonged favorable price regime ($P_{\text{live}} \ge 1.20 \times P_{\text{base}}$), the state is static:
$$\Delta\text{cash} = 0, \quad \Delta\text{shed} = 0, \quad \Delta\text{inventory} = 0$$
Consequently, **zero events fire**. In `AECExecutor`, line 324 triggers the `NO_EVENT_FAST_PATH`, returning control immediately to the baseline without ever probing the economic value of liquidating that held inventory.

---

## 2. Core Architectural Design: State-Level Opportunity Detection

The **Asset-Holding Valuation Trigger** fundamentally shifts the Opportunity Engine from being purely *event-driven* (differential changes) to being *dual-mode*:
1. **Differential Events** (something changed this turn)
2. **Persistent Economic States** (something is currently economically valuable)

### 2.1 Inputs to the Trigger
The trigger ingests the complete current state:
```text
CURRENT ASSET STATE
  + CURRENT MARKET STATE
  + FUTURE REALIZATION OPTIONS
  + DEPENDENCY CLOSURE
  + TERMINAL RUNWAY
  + WORKING CAPITAL LIQUIDITY
  + OPPONENT PRESSURE SIGNALS
```

### 2.2 Structural Features (No Arbitrary Dollar Holding Costs)
The trigger does NOT impose an ad-hoc heuristic formula like $\text{holding\_cost} = Q \times \$X/\text{turn}$. Such heuristics distort the decision landscape. Instead, the trigger exposes clean **structural features** to the exact simulator:
- `commodity`: Product held in shed or carried by worker (e.g. `STRAWBERRY`, `MELON`, `CARROT`)
- `quantity_held`: Total physical units in storage or cargo
- `uncommitted_quantity`: $Q_{\text{held}} - Q_{\text{reserved}}$ (deducting feed requirements, e.g. wheat reserved for animals)
- `current_price` vs `base_price`: Relative price ratio $P_{\text{live}} / P_{\text{base}}$
- `price_trajectory`: Short-term trend (rising, stable, declining)
- `storage_utilization`: $\text{shed\_total} / 100$
- `terminal_runway`: Turns remaining until final step ($718 - t$)
- `liquidity_status`: Cash available vs upcoming wage/seed liabilities
- `opponent_pressure`: Proximity of rival cargo carriers to town market
- `realization_options`: Bounded set of candidate realization modes:
  - `SELL_NOW`: Immediate market order tranche
  - `SELL_PARTIAL`: Partial depth-compatible tranche
  - `SELL_LATER`: Retain asset awaiting anticipated price spike
  - `TERMINAL_LIQUIDATE`: Complete endgame shed dump
  - `REPOSITION`: Transfer cargo from worker to shed

The trigger does NOT decide the final action. It declares:
> *"This persistent asset holding state contains structural economic potential and warrants candidate synthesis and exact counterfactual evaluation."*

---

## 3. The 6 Asset-Holding Opportunity Classes

The trigger must recognize at least 6 structural opportunity classes:

### Class A: Favourable Market Holding State (`FAVOURABLE_MARKET_HOLDING`)
- **Condition**: Uncommitted inventory $\ge 5$ units held in shed; current market price $P_{\text{live}} \ge 1.15 \times P_{\text{base}}$ (or in upper quartile).
- **Economic Potential**: Stranded capital can be converted to liquid wealth or reinvestment capital at premium clearing rates.

### Class B: Terminal Holding Risk (`TERMINAL_HOLDING_RISK`)
- **Condition**: Step $\ge 650$ with uncommitted shed inventory $> 0$.
- **Economic Potential**: As $t \to 718$, market clearing capacity is bounded (max 10 orders/turn, price elasticity per turn). Waiting until step 718 risks leaving assets unsold or suffering steep multi-unit price depression. Frontloading tranches at steps 650–710 maximizes terminal NPV.

### Class C: Liquidity Holding Conflict (`LIQUIDITY_HOLDING_CONFLICT`)
- **Condition**: Farm cash $<\$300$ (or below required daily wages), but uncommitted inventory exists in shed.
- **Economic Potential**: Liquidating a small tranche avoids wage default or unlocks seed purchases for high-yield planting.

### Class D: Market Saturation Risk (`MARKET_SATURATION_RISK`)
- **Condition**: Farm holds large inventory, and field crops will mature shortly (or historical price trajectory shows imminent decline).
- **Economic Potential**: Selling current inventory before new supply gluts the market secures higher realized margins.

### Class E: Opponent Pressure (`OPPONENT_PRESSURE`)
- **Condition**: Rival worker observed carrying substantial cargo within 1–3 steps of town.
- **Economic Potential**: Rival will dump supply, depressing town clearing price. Executing our sell order this turn captures depth before rival preemption.

### Class F: Dependency-Coupled Holding (`DEPENDENCY_COUPLED_HOLDING`)
- **Condition**: Farm holds inventory exceeding hard downstream obligations (e.g. 15 wheat held, but only 2 animals need 1 wheat/day each).
- **Economic Potential**: Excess stock beyond feed security can be safely liquidated without risking animal starvation.

---

## 4. Persistence & Anti-Spam Control

If a state triggers every turn simply because inventory remains valuable, the compiler risks candidate spam and wasted simulation latency.

### 4.1 Structural State Fingerprinting
We define an immutable `AssetHoldingFingerprint`:
$$\text{Fingerprint} = \text{Hash}\left(\text{commodity}, \text{qty\_band}, \text{price\_band}, \text{terminal\_phase}, \text{dependency\_status}, \text{opponent\_level}\right)$$
where:
- `qty_band`: $\lfloor Q_{\text{held}} / 10 \rfloor$
- `price_band`: $\lfloor (P_{\text{live}} / P_{\text{base}}) / 0.05 \rfloor$ (5% bins)
- `terminal_phase`: `EARLY` ($t < 400$), `MID` ($400 \le t < 650$), `LATE` ($650 \le t < 710$), `TERMINAL` ($t \ge 710$)
- `dependency_status`: `FEED_CONSTRAINED` vs `UNCONSTRAINED`
- `opponent_level`: `LOW` vs `HIGH`

### 4.2 Opportunity Lifecycle
Every opportunity transitions through formal states:
```text
OPPORTUNITY_OPEN ──► PENDING ──► CANDIDATE_GENERATED ──► COMMITTED
       │                                                    │
       └──────────────► INVALIDATED ◄───────────────────────┘
```
- If a candidate generated from fingerprint $F$ was evaluated by exact simulation and rejected as economically non-superior, and the state fingerprint remains identical in the next tick ($F_{t+1} = F_t$), the trigger suppresses duplicate simulation.
- If $P_{\text{live}}$ shifts to a new band, or inventory quantity changes, or terminal phase transitions, fingerprint changes ($F_{t+1} \neq F_t$), immediately resetting the lifecycle and permitting fresh evaluation.

---

## 5. Event Bus Integration & Fast-Path Preservation

To integrate seamlessly with `AECExecutor` without breaking existing fast-path optimizations:
1. `EventType.E13_ASSET_HOLDING_STATE` is added to `aec/events/event_types.py`.
2. `detect_events` in `aec/events/detectors.py` evaluates persistent holding states when `enable_asset_holding_trigger` is active.
3. If an asset holding state is present, `E13_ASSET_HOLDING_STATE` is published to the `EventBus`.
4. `AECExecutor`'s `if not self.event_bus.has_events:` guard continues to function perfectly: when a holding state exists, an event is present, and the compiler enters the opportunity pipeline.
5. If zero events and zero holding states exist, the `NO_EVENT_FAST_PATH` continues to return baseline in sub-millisecond time.

---

## 6. Telemetry Specification

The trigger outputs detailed telemetry per step:
```json
{
  "asset_triggered": true,
  "asset_trigger_reason": "FAVOURABLE_MARKET_HOLDING: STRAWBERRY (qty=45, price=145.0, base=100.0, ratio=1.45)",
  "asset_state_fingerprint": "STRAWBERRY_q4_p29_MID_UNCONSTRAINED_LOW",
  "commodity": "STRAWBERRY",
  "quantity_held": 45,
  "uncommitted_quantity": 45,
  "price_live": 145.0,
  "realization_options": ["SELL_NOW", "SELL_PARTIAL", "SELL_LATER"]
}
```
