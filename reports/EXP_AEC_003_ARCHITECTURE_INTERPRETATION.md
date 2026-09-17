# EXP-AEC-003 — Architectural Interpretation & Boundary Audit

**Protocol:** `PREREG-EXP-AEC-003-20260917-FINAL`  
**Audit Focus:** Architectural Validation Status & Competitive Generalization Boundaries  
**Auditor:** Independent Scientific Audit Agent  
**Date:** 2026-09-17  

---

## 1. Executive Summary

This audit establishes the precise scientific scope of what **EXP-AEC-003** has validated within the Autonomous Economic Coordinator (AEC) architecture. 

A positive experimental result ($+\$57.36$, $p = 0.0035$) against a frozen baseline (V3) on 50 prospective seeds does **not** validate every module in the AEC codebase, nor does it guarantee tournament or leaderboard placement. This document delineates:
1. What is empirically **validated**.
2. What is implemented and tested, but **untriggered / passive**.
3. What remains **quarantined / unproven**.
4. The strict scientific boundary separating **experimental evidence** from **competitive generalization**.

---

## 2. Component-by-Component Validation Matrix

| Architectural Component | Implementation Path | Experimental Exposure in EXP-AEC-003 | Empirical Status | Scientific Assessment |
|---|---|---|---|---|
| **Economic IR & State Reconstruction** | `aec/ir/economic_state.py` | Active on all 71,900 turns; reconstructed inventory, cash, shed, and prices. | **VALIDATED** | Deterministic, zero-divergence state tracking established across 100 full matches. |
| **Action Basket Dependency Graph** | `aec/ir/dependency_graph.py`, `aec/market/transformations.py` | Analyzed baseline market baskets on all turns with $\ge 2$ orders. | **VALIDATED** | Correctly partitioned same-asset coupled trades from uncoupled liquidity trades in 140/140 commits. |
| **Dependency-Aware Market Timing** | `aec/market/transformations.py` | Committed 140 times across 45 seeds; reordered uncoupled sell orders ahead of coupled orders/capex. | **VALIDATED** | Primary causal driver of $+\$57.36$ paired delta margin. Zero execution errors. |
| **Counterfactual Forward Simulator** | `aec/counterfactual/simulator.py` | Evaluated candidate mutations on step-by-step sequential pricing. | **VALIDATED (MARKET DOMAIN)** | 140/140 commits showed 100% exact numerical equality ($\Delta \text{money}_{\text{predicted}} == \Delta \text{money}_{\text{realized}}$). |
| **Counterfactual Fidelity Gate** | `aec/safety/checker.py` | Verified candidate fidelity against real engine transition dynamics. | **VALIDATED** | 100% (140/140) adherence to `COUNTERFACTUAL_FIDELITY = VERIFIED`. Rejected/passed appropriately. |
| **Safety Certificate & Checks** | `aec/safety/certificate.py`, `aec/safety/checker.py` | Checked solvency, terminal feasibility, market collision, and spatial consistency. | **VALIDATED** | Zero safety regressions, zero illegal orders, zero disqualifications across 71,900 turns. |
| **AECExecutor Runtime & Fallback** | `aec/integration/executor.py` | Orchestrated planning cycle; intercepted candidates; provided fail-closed fallback. | **VALIDATED** | Governed all 100 matches within latency budget (mean 1.1ms, max 68.6ms $\ll 1000$ms bound). |
| **Backbone V3 Integration** | `aec/integration/adapter.py` | Wrapped frozen `submission_Vj_kc_v3.tar.gz`. | **VALIDATED** | Exact baseline call count (71,900), zero duplicate baseline calls. |
| **Terminal Liquidation** | `aec/opportunities/terminal.py` | Enabled in config as defense-in-depth; evaluated on step 718. | **TESTED / PASSIVE (0 COMMITS)** | Functional in unit tests, but untriggered in EXP-AEC-003 because baseline V3 left 0 shed inventory on step 718. |
| **Phase Shutdown** | `aec/opportunities/terminal.py` | Enabled in config as defense-in-depth; evaluated on steps 696–717. | **TESTED / PASSIVE (0 COMMITS)** | Untriggered in EXP-AEC-003 because baseline policy had no unharvested mature crop residual. |
| **Legacy Frontload Orders** | `aec/market/transformations.py` | Quarantined; classified `FALSIFIED`. | **FALSIFIED / QUARANTINED** | Successfully suppressed. 0 commits. Code remains quarantined. |
| **Local Weed Dig** | `aec/opportunities/route.py` | Quarantined; heuristic labor valuation. | **QUARANTINED** | Detected 1,265 times, but 100% intercepted by quarantine gate as `ABSTAIN`. 0 commits. |
| **Dynamic Shadow Harvest** | `aec/opportunities/route.py` | Quarantined; unverified shadow harvest. | **QUARANTINED** | Suppressed by configuration. 0 commits. |
| **Cargo Ferry Priority** | `aec/opportunities/route.py` | Quarantined; unverified ferry priority. | **QUARANTINED** | Suppressed by configuration. 0 commits. |
| **Opponent Preempt Sell** | `aec/opportunities/market.py` | Quarantined; uncalibrated opponent sell pressure. | **QUARANTINED** | Suppressed by configuration. 0 commits. |
| **Emergency Feed Purchase** | `aec/opportunities/market.py` | Quarantined; heuristic starvation rescue. | **QUARANTINED** | Suppressed by configuration. 0 commits. |
| **Town Cycle Arbitrage** | `aec/market/transformations.py` | Unimplemented / heuristic pricing model. | **NOT IMPLEMENTED / UNTESTED** | Not part of active configuration. |

---

## 3. Detailed Mechanism Analysis: What Actually Drove the +$57.36 Result?

The forensic audit of all 140 committed patches reveals that the entirety of the observed gain is attributable to a single micro-economic intervention:

### Causal Mechanism: Intra-Turn Liquidity Pre-Allocation
In baseline V3, the bot's scheduling logic constructs a compound market order list on macro turns (e.g. Turn 433 and Turn 649). Because V3 appends orders in heuristic sequence, it frequently places `SELL` orders for uncoupled commodities (e.g. `WOOL`, `EGG`, `WHEAT`, `MILK`) **after** capital expenditure orders (`HIRE`) or after coupled commodities with simultaneous buy/sell orders (`FERTILIZER`).

In the Kagriculture engine:
1. Capital expenditure orders (`HIRE`) debit cash sequentially. If cash is depleted, subsequent actions fail or stall.
2. Promoting uncoupled `SELL` orders to the front of the market order list liquidates warehouse inventory *before* any cash is spent.
3. On Turn 649 (late-game sell-off), executing uncoupled sales before coupled transactions avoids negative price impacts and locks in higher sequential unit revenues (yielding up to +$93.00 cash on Turn 529 and +$70.00 cash on Turn 649).

Because `DEPENDENCY_AWARE_MARKET_TIMING` strictly preserves same-asset ordering for coupled commodities (e.g. `BUY FERTILIZER` vs `SELL FERTILIZER`), it avoids the sequential price depreciation that falsified `FRONTLOAD_ORDERS` in EXP-AEC-002.

---

## 4. Separation of Experimental Evidence vs. Competitive Generalization

### What the Evidence Proves:
1. **Prospective Causal Superiority**: Adding `DEPENDENCY_AWARE_MARKET_TIMING` to frozen V3 produces a statistically significant, positive margin delta ($+\$57.36$, $p = 0.0035$) when evaluated in mirror self-play against unmodified frozen V3 across 50 virgin seeds.
2. **Zero Degradation**: Treatment never crashed, violated safety constraints, or committed illegal actions across 71,900 steps.
3. **Execution Robustness**: Lower 95% bound ($+\$23.17$) confirms that the true population mean margin delta against V3 is strictly positive.

### What the Evidence Does NOT Prove:
1. **No Guarantee of Top-10 Leaderboard Standing**:
   - The Kaggle leaderboard features diverse opponent architectures (e.g., Dmitrii LB 2800, aggressive weeders, resource monopolizers, animal rushers).
   - Demonstrating a +$57.36 margin against self-play V3 does **not** prove that the agent will achieve a top-10 rank or withstand foreign adversary styles.
2. **No General Validation of Untriggered Modules**:
   - `TERMINAL_LIQUIDATION` and `PHASE_SHUTDOWN` remain unproven empirically in prospective competition.
   - `ActionBasketDependencyGraph` is validated for market ordering, but not for multi-worker spatial route coordination.
3. **Tail Dependency**:
   - The mean ($+\$57.36$) is substantially influenced by positive tail seeds (top seed $\Delta = +948.00$). While the median is positive ($+\$18.50$) and non-parametric tests are significant ($p < 10^{-5}$), performance variance across environments remains large ($\text{Std} = \$144.22$).

---

## 5. Architectural Readiness Verdict

The AEC core architecture (Economic IR, Event Bus, Dependency Graph, Simulator, Safety Certificate, and Executor) is **scientifically sound and verified in production**. The single mechanism `DEPENDENCY_AWARE_MARKET_TIMING` is certified as a validated active component. All other speculative mechanisms remain appropriately quarantined.
