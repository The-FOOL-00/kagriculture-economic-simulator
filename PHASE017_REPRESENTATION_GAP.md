# PHASE 017 — CANDIDATE REPRESENTATION GAP AUDIT

**Project**: Kagriculture Adaptive Economic Compiler (AEC)  
**Phase**: PHASE 017 — Residual Alpha, Overblocking & Opportunity-Representation Audit  
**Author**: Primary Implementation & Research Agent  
**Date**: September 19, 2026  
**Chassis SHA256**: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` (Verified Byte-Identical)  

---

## 1. Executive Summary

Phase 014 identified that the AEC was fundamentally blind to certain economic headroom because its candidate generator could not represent autonomous market liquidation when the baseline queue was passive. Phase 015 implemented `AutonomousTrancheOrderSynthesizer`, enabling the compiler to emit synthetic market sell orders.

However, Phase 016 revealed that even with macro-divergence blocked (recovering 98.5% of Phase 015's catastrophic losses), the net economic delta of Phase 015 mechanisms remains slightly negative on average (`-$884.20`, 1W-9L-0T).

This audit investigates the **Candidate Representation Gap**:
> *Does the remaining negative gap originate from bad underlying economics, evaluator overblocking, or a defect in the candidate generation space itself?*

Based on structural code analysis and empirical telemetry, this report demonstrates that **Candidate Representation and Funnel Crowding Defects** represent a primary structural bottleneck in the current AEC architecture.

---

## 2. Forensic Analysis of the 8 Representation Dimensions (§20)

### 2.1 Quantity Representation Defect (Coarse Structural Anchors)
In `aec/market/tranche_synthesizer.py` (lines 110–174), candidate quantities are generated via rigid structural anchors:
1. $q_{\text{min}} = 1$ or $5$
2. $q_{\text{liquidity}} = \text{cash\_deficit} / \text{price}$
3. $q_{\text{storage}} = \text{shed\_total} - 75$
4. $q_{\text{depth}} = \min(10, \text{uncommitted})$
5. $q_{\text{full}} = \text{uncommitted}$

**Causal Breakdown**:
- $q_{\text{min}} = 1$ generates trivial direct revenue ($+\$20\text{--}\$60$), insufficient to overcome market bid-ask spreads or justify evaluation cost.
- $q_{\text{full}}$ and $q_{\text{depth}} = 10$ inject substantial lump-sum cash ($+\$500\text{--}\$2,500$). When the farm is at $\$9,200$, injecting $+\$1,200$ crosses V3's $\$10,000$ Sheep Capex threshold, immediately tripping Tier 2 macro escalation and causing subsequent rejection by the long-horizon evaluator.
- **The Defect**: The generator lacks **Macro-Boundary-Aware Quantity Truncation**. It cannot solve for $q^* = \max q$ subject to $\text{Cash} + q \cdot P < \text{MacroBoundaryThreshold}$. As a result, viable partial sales are rejected because the generator only proposes full or coarse tranches that cross macro boundaries.

### 2.2 Temporal Representation Defect (Impulsive vs. Scheduled Execution)
The `ASSET_HOLDING_VALUATION_TRIGGER` evaluates inventory on every single turn where uncommitted inventory exists:
- It fires impulsively at turn $t_0$ as soon as goods appear in the shed.
- However, V3 already contains an endogenous forward plan to liquidate goods on specific days (e.g. Day 12, Day 18, or near block boundaries).
- Selling 3 turns before V3's native schedule generates almost zero net differential revenue, while incurring price depression and market friction.
- **The Defect**: The candidate generator cannot represent **Deferred or Scheduled Market Execution** ($a_{t+k}$). It only evaluates immediate single-turn interventions ($a_t$).

### 2.3 Multi-Step Staged Representation Defect (Lump-Sum vs. Tranche Stream)
- In the Kaggle market mechanics, dumping a large parcel in a single turn causes severe downward price elasticity.
- Furthermore, injecting lump-sum cash in a single step causes sudden macro-policy regime shifts in V3.
- An optimal economic policy would liquidate $N$ units as a smooth stream of smaller tranches over 3–5 consecutive turns:
  $$\vec{a}_{\text{market}} = [q_t, q_{t+1}, q_{t+2}, \dots]$$
- **The Defect**: `AutonomousTrancheOrderSynthesizer` generates strictly single-step orders (`actions=[{"market": [...]}]`). It cannot represent multi-step staged liquidations.

### 2.4 Spatial Coordination & Cargo Decoupling
- Goods in Kagriculture exist in two physical locations: the shed and worker cargo backpacks.
- `AutonomousTrancheOrderSynthesizer` can only sell goods currently resting in the shed (`econ_state.farm.shed_inventory`).
- When workers harvest crops, goods sit in worker backpacks until the worker navigates to the shed and executes `DROP`.
- **The Defect**: The market generator is decoupled from spatial movement. It cannot emit a coupled action: `[Worker 0: MOVE to Shed -> DROP] + [Market: SELL]`. Inventory remains locked in transit.

### 2.5 Market + Production Coupling Defect
- In agricultural economics, selling surplus is rarely an end in itself; its purpose is capital reallocation (liquidity conversion to purchase seeds, fertilizer, or land).
- Current tranche synthesis generates pure `SELL` orders.
- It cannot couple a sell order with an immediate value-accretive purchase (e.g. `SELL Wheat -> BUY Strawberry Seeds` in the same turn).

### 2.6 Opponent Pressure Coupling Defect
- Opponent dumping alters clearing prices.
- When an opponent approaches a market saturation event, the optimal action is pre-emptive clearing.
- The current tranche generator computes revenue using static current prices ($P_t$), ignoring the anticipated opponent supply schedule.

### 2.7 Funnel Crowding Defect (Inter-Mechanism Interference)
A critical discovery made during the Phase 017 forensic audit (specifically on Seed 249288):
- On Seed 249288, Treatment scored `$146,840.00` while Control scored `$148,325.00` (paired delta: `-$1,561.00`).
- Treatment had **0 commits**.
- Control had **1 commit**: at Step 649, Control committed `DEPENDENCY_AWARE_MARKET_TIMING`, yielding $+\$1,485.00$.
- **Why did Treatment miss this commit?**
  - In Treatment, `AUTONOMOUS_TRANCHE_ORDER_SYNTHESIZER` was enabled.
  - At Step 649, the tranche synthesizer generated multiple candidate sell orders across different commodities and structural anchors.
  - Because `AECConfig.max_candidates = 8` and `max_simulations = 8`, the tranche candidates **crowded out** `DEPENDENCY_AWARE_MARKET_TIMING` during candidate sorting and pruning.
  - The tranche candidates were subsequently rejected by macro safety / long continuation.
  - Result: Treatment fell back to pure baseline, completely missing the lucrative market timing reorder that Control successfully captured!

---

## 3. Taxonomy of Representation Limitations

| Representation Dimension | Current Architecture Capability | Ideal Economic Capability | Impact on Residual Gap |
| :--- | :--- | :--- | :---: |
| **Quantity Granularity** | Coarse anchors (1, 5, 10, full) | Boundary-safe continuous / fine-grid ($q^*$) | **HIGH** (causes avoidable macro trips) |
| **Temporal Horizon** | Immediate execution ($t$) | Scheduled / deferred execution ($t+k$) | **MEDIUM** (premature trading) |
| **Multi-Step Staging** | Single-turn impulse ($H=1$) | Multi-turn smooth tranche stream | **HIGH** (price impact & macro shock) |
| **Spatial / Cargo Coupling** | Shed inventory only | Coupled worker drop + shed sale | **MEDIUM** (unexploited backpack stock) |
| **Production Coupling** | Pure sale | Coupled Sell + Seed/Fertilizer Purchase | **MEDIUM** (idle working capital) |
| **Opponent Coupling** | Static pricing | Dynamic clearing depth optimization | **LOW** (secondary in non-saturation turns) |
| **Funnel Partitioning** | Global competitive sort (crowding) | Tiered mechanism reservation budgets | **CRITICAL** (suppresses baseline alpha) |

---

## 4. Architectural Recommendations

1. **Mechanism Reservation in Candidate Funnel**:
   - The candidate funnel must never allow an experimental mechanism (such as Tranche Synthesis) to crowd out verified foundation mechanisms (`DEPENDENCY_AWARE_MARKET_TIMING`, `TERMINAL_LIQUIDATION`).
   - Dedicated evaluation slots must be reserved for foundation mechanisms.
2. **Boundary-Safe Quantity Clamping**:
   - Before emitting a candidate tranche $q$, clamp $q$ to ensure the projected cash injection does not cross the nearest V3 capex threshold:
     $$q_{\text{safe}} = \min\left(q, \left\lfloor \frac{\text{CashGate} - \text{Cash} - \epsilon}{P} \right\rfloor\right)$$
3. **Multi-Turn Tranche Coupling**:
   - Support `CoupledPatch` structures where market actions are scheduled across multiple turns.
