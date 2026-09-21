# V26 — MARKET-TIMING TRANSFER SPECIFICATION

## 1. Mechanism Identity & Purpose
* **Mechanism Family**: `DEPENDENCY_AWARE_MARKET_TIMING`
* **Scientific Status**: EXPERIMENTAL (Transferring from V22R1 to V25)
* **Objective**: Optimize the execution sequence of market orders within a single turn without altering total quantities, items, or same-asset causal dependencies.

---

## 2. Formal Economic Contract (§13)

### 2.1 Trigger: When is an Opportunity Proposed?
* **Condition**: The active baseline action contains $\ge 2$ market orders (`len(action['market']) >= 2`).
* **Predicate**: `transform_dependency_aware_market_timing(orders, econ_state) != orders`.
* **Economic Event**: The baseline has uncoupled liquidity-generating orders (e.g. `SELL` of harvested crops) scheduled behind capital expenditures (`HIRE`, `BUY_LAND`, `BUY_SEED`).

### 2.2 Candidate: What Mutation is Proposed?
* **Causal Partitioning**:
  - **Group A (Uncoupled Sells)**: `SELL` orders for commodities that do NOT have a corresponding `BUY_PRODUCT` in the same turn. Promoted to the front of the queue to provide liquidity before capital outlays.
  - **Group B (Coupled & Wash Orders)**: Commodities with both `BUY_PRODUCT` and `SELL` (e.g. wheat wash, arbitrage). Their relative order is strictly preserved (never inverting `BUY` before `SELL`).
  - **Group C (Capital Outlays)**: `HIRE`, `BUY_LAND`, `BUY_SEED`, `BUY_ANIMAL`.
* **Output Queue**: `candidate_orders = (Group A + Group B + Group C)[:10]`.
* **Integrity Invariants**:
  1. No order quantity is changed.
  2. No order item is changed.
  3. Total order count is conserved.

### 2.3 Objective: What is Being Optimized?
* **Pre-Impact Solvency & Price Execution**:
  In Kaggle environments, orders execute sequentially against the market and the rival player in lockstep index by index. Executing uncoupled `SELL` orders first raises liquid cash reserves, preventing order failures from transient intra-turn insolvency and securing sales before potential rival market dumping.

### 2.4 Counterfactual: What Continuation is Simulated?
* **Simulation Pipeline**:
  ```text
  Live State (Step t)
         │
         ▼
  Clone State via ShadowRolloutState
         │
         ▼
  Apply Candidate Action (Reordered Orders)
         │
         ▼
  Simulate Active Backbone Continuation (Horizon H = 4 to 8)
         │
         ▼
  Evaluate Delta: ΔWealth = Candidate Wealth - Baseline Wealth
  ```
* **Backbone-Aware Invariant**: The continuation policy is provided by the *active backbone* (`V25P3Continuation` or `V3Continuation`), ensuring cash balances and future route obligations reflect the active planner.

### 2.5 Safety Gates: When is the Intervention Rejected?
An intervention candidate is rejected if ANY of the following occur:
1. $\Delta \text{Wealth} < \text{floor}$ (economic non-inferiority).
2. Intermediate shed solvency is breached.
3. Feed deficit or animal escape occurs (`feed_security_ok == False`).
4. Spatial desynchronization occurs on non-spliced workers.
5. Macro regime shift is triggered unexpectedly.

### 2.6 Commit Rule: When is the Patch Authorized?
A candidate patch is committed to execution if and only if:
$$\Delta \text{Wealth} > 0 \quad \land \quad \text{Safety Certificate Issued}$$
Otherwise, the AEC abstains and plays the unaltered baseline action.

---

## 3. Strict Separation of Concerns
| Component | Responsibility | Backbone-Specific? |
| :--- | :--- | :---: |
| **`transform_dependency_aware_market_timing`** | Intra-turn order reordering logic | **NO** (Universal) |
| **`MarketOpportunityAnalyzer`** | Detects candidate trigger | **NO** (Universal) |
| **`WinModel` & Safety Gates** | Margin evaluation & risk checks | **NO** (Universal) |
| **`BackbonePolicy.create_continuation_policy`** | Cloned-state forward rollouts | **YES** (Adapter-bound) |
| **`BackbonePolicy.macro_fingerprint`** | Macro state & cash baseline | **YES** (Adapter-bound) |
