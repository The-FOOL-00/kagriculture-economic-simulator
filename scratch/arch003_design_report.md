# DESIGN & IMPLEMENTATION PREPARATION REPORT: EXP-ARCH-003_H1_TERMINAL_REPAIR

**Program**: Kagriculture Controlled Research Program  
**Track**: Architecture Track (Terminal Overlay Succession)  
**Document**: Design & Implementation Preparation Report  
**Date**: 2026-09-16  
**Author**: Senior Research Engineer (Antigravity)  
**Predecessor Experiment**: `experiments/EXP-ARCH-002_H1_DOMINANCE_TERMINAL/` (Permanently Frozen)  
**Successor Experiment**: `experiments/EXP-ARCH-003_H1_TERMINAL_REPAIR/` (Proposed)  
**Status**: **DESIGN ONLY — NO FILES MODIFIED — NO PROSPECTIVE SEEDS EXECUTED**

---

## EXECUTIVE SUMMARY & AUDIT CONTINUITY

The forensic audit of `EXP-ARCH-002_H1_DOMINANCE_TERMINAL` established three decisive, source-grounded structural conclusions:
1. **Runner Purity vs. Policy Isolation**: The non-zero score deltas in the original run were an artifact of double-calling `base_inst_h1` inside the runner instrumentation. The corrected re-execution under `run_arch002_h1_reexecution.py` confirmed 100% paired neutrality ($\bar{\Delta} = 0.00$, $\max|\Delta| = 0$, 500/500 seeds neutral) when the overlay abstained. Shadow simulation, state cloning, ledger isolation, and pre-entry action purity are completely sound.
2. **Structural Contradiction 1 (Acceptance Contradiction)**: Preregistered Decision D3 and Protocol Constraint P5 froze all market orders on steps 712–718 to the baseline's verbatim market orders. Because the baseline never places unfulfillable sell orders ($Q_{\text{ordered}}(p) \le S_{\text{baseline}}(p) \le S_{\text{candidate}}(p)$), candidate extra crop deposits could never create additional sold units: $\Delta_{\text{sold}}(p) \equiv 0$ for all $p \in \text{PRODUCTS\_9}$. However, `h1_dominance.py:155` simultaneously required $\exists p: \Delta_{\text{sold}}(p) > 0$. This structural contradiction caused 100% rejection (`ABSTAIN_ACCEPT`) across all 244 candidates evaluated in yarn-family routes.
3. **Structural Contradiction 2 (Prefix Dominance Blocks Rescheduling)**: Preregistered Decision D5 enforced rigid row-wise prefix dominance at every single turn $t \in [712, 718]$ on per-actor cumulative deposits ($D_{\text{candidate}}(t, a) \ge D_{\text{baseline}}(t, a)$). Because baseline workers in backbone routes already had scheduled intermediate drops, any proposal that redirected a worker to walk further, harvest a higher-yield bundle, and return later necessarily missed an intermediate drop, causing instant rejection mid-window ($D_{\text{candidate}}(t, a) < D_{\text{baseline}}(t, a)$). This caused 100% rejection (`ABSTAIN_DOMINANCE`) across all 37 improving backbone proposals in validation and 756/1000 games in the prospective cohort.
4. **Economic Inertia**: In the Kagriculture engine (`sim.py:319–338`), terminal reward is strictly `farm.money`. Physical commodities left in the shed at episode conclusion produce zero score. Therefore, reap-and-ferry without terminal market liquidation is economically inert.

This report establishes the complete scientific, theoretical, and architectural foundation for the successor experiment `EXP-ARCH-003_H1_TERMINAL_REPAIR`.

---

## PHASE 1 — RECONSTRUCT THE EXACT SCIENTIFIC OBJECTIVE

### 1. What was H1-ACT actually trying to accomplish?
H1-ACT was designed to test whether grafting a localized, dominance-gated terminal reap-and-ferry optimizer onto the frozen V54++ residual baseline could causally improve terminal score without introducing physical degradation or tail harm. Specifically, during the final 7 turns (steps 712–718), late agricultural tasks like `WATER` and `CARE` on immature crops have zero marginal value because the crops cannot mature before episode end (step 719). H1-ACT intended to detect these low-value or idle worker turns, redirect workers to harvest mature crops or collect fertilizer within reach, ferry those products to the shed, and deposit them so that they could be monetized at episode end.

### 2. What economic mechanism makes reap-and-ferry valuable?
In the Kagriculture engine (`sim.py`):
- Crops standing on tiles at step 718 yield 0 score.
- Crops held in worker inventories at step 718 yield 0 score.
- Crops sitting in the shed at step 718 yield 0 score.
- **Terminal score is strictly `farm.money`**.
The economic mechanism of reap-and-ferry is an arbitrage of worker opportunity cost: replacing late worker-turns that generate 0 return with turns that convert standing biological yield into physical inventory delivered to the shed, which is then liquidated on step 718 for liquid currency at prevailing market prices.

### 3. Why does the baseline need terminal liquidation for this to become reward-relevant?
The baseline policy (`candidates/compiled_v54_plus_residual.py` / `scripts.v19_terminal.py:190–240`) constructs its market orders at step 718 based on its own projected shed inventory:
```python
quantity = max(0, int(shed.get(item, 0) or 0))
```
The baseline never orders sales for crops it does not possess. If candidate schedules are constrained to execute baseline market orders verbatim (ARCH-002 D3/P5), any additional crops harvested and deposited by candidate workers sit unsold in the shed at step 718. Because physical inventory has zero score value, the economic delta $\Delta_{\text{money}}$ is identically $\$0.00$. Terminal market liquidation is the mandatory final step that realizes the economic value of the physical harvest.

### 4. What properties was ARCH-002 trying to protect with dominance?
ARCH-002's dominance predicate (`dominates()`, D5) was constructed to enforce conservative safety invariants:
- **Zero Physical Degradation**: Candidate shed capacity overflow must be zero (`overflow_units == 0`), preventing loss of resources.
- **Preserve Intermediate Market Commitments**: Pre-market shed inventory and cumulative sold units at each step $t \in [712, 718]$ must weakly dominate baseline (`pre_market_shed >= baseline`, `sold >= baseline`), ensuring baseline scheduled sales on 712–717 never fail due to inventory shortage.
- **Preserve Worker Commitments**: Cumulative per-actor deposits at each intermediate step must weakly dominate baseline (`dep[actor] >= baseline_dep[actor]`).
- **Strict Value Gain**: Candidate stock value at frozen entry prices must strictly exceed baseline (`stock_value(candidate) > stock_value(baseline)`).
- **Anti-Cannibalization / No-Steal**: No worker may steal an acquisition planned by another worker (`no_steal_pass`).

### 5. Which of those protections are essential scientific requirements?
1. **Zero Shed Capacity Overflow (`overflow_units == 0`)**: Hard physical constraint; overflow permanently deletes items.
2. **Intermediate Market Solvency**: Any market order scheduled by the baseline during steps 712–717 must remain 100% executable under candidate inventory.
3. **Strict Economic Improvement**: Candidate terminal currency must strictly exceed baseline terminal currency ($\Delta_{\text{money}} > 0$).
4. **No-Steal Coordination Invariant**: Multi-actor consistency; one worker cannot invalidate another worker's planned acquisition.
5. **Pre-Entry Action Purity (P-PURE)**: 100% bit-identity on steps 0–711.
6. **Fail-Closed Safety**: Any unexpected state, observation mismatch, or unmodeled market op immediately aborts to live baseline.

### 6. Which were merely conservative implementation choices?
1. **Rigid Intermediate Row-Wise Prefix Dominance**: Requiring $D_{\text{candidate}}(t, a) \ge D_{\text{baseline}}(t, a)$ at *every intermediate turn* $t \in [712, 718]$. This prevented temporary rescheduling deficits where a worker delays a small drop to deliver a larger drop later.
2. **Verbatim Step-718 Market Passthrough (D3)**: Imposed out of fear of market-maker confounds, but it severed the link between physical harvesting and terminal coin reward.
3. **Acceptance Conjunction on Frozen Sold Units**: Requiring `some sold_delta > 0` while freezing market orders verbatim, creating a mathematical impossibility.

### 7. Which ARCH-002 restrictions made the treatment economically inert?
- Decision D3 (verbatim market passthrough on step 718).
- Decision D5 (row-wise intermediate prefix dominance on per-actor deposits).
- Protocol Constraint P5 (markets frozen verbatim across entire window).

### 8. Which restrictions should remain in ARCH-003?
- **P5 (steps 712–717)**: Market orders on steps 712–717 remain 100% frozen to baseline verbatim.
- **D1 (Worker Whitelist)**: Whitelist `{N, S, E, W, HARVEST, COLLECT_FERTILIZER, DROP, PASS}` with DROP-only (no PLACE).
- **D2 (Entry Step)**: $E = 712$ (7-turn window 712–718).
- **D4 (Search Budget)**: 128 simulations, 1 pass, $\le 8$ proposals/worker, frozen entry prices.
- **D6 (Determinism)**: Strict `>` everywhere, integer inclusion, total ordering on proposals.
- **D7 (Entry Guards & Abstention)**: G0–G7 guards, fail-safe abandon-to-baseline, frozen reason enum.
- **D8 (Baseline Identity)**: `candidates/compiled_v54_plus_residual.py` (SHA-256 `18402ec6...`).
- **G4 (BUY Coverage Gate)**: `money_at_E >= 125 * U`.
- **R8 / P6 (Fertilizer Boundary)**: `COLLECT_FERTILIZER` restricted to animal tiles flagged at entry step $E$.
- **No-Steal Gate (`no_steal_pass`)**: Multi-actor acquisition collision protection.

### 9. Which restrictions need a formal scientific replacement?
1. **Replacement for D3 (Step-718 Market Rule)**:
   *Old*: Verbatim baseline market passthrough downstream of outer `terminal_market`.
   *New Invariant (Deterministic Step-718 Market Liquidation)*:
   On step 718, candidate market orders are generated by applying the frozen baseline `terminal_market(obs, action, rule="collision", replace=True)` logic to the candidate's post-harvest, post-drop simulated physical state at step 718.
2. **Replacement for D5 (Dominance Predicate)**:
   *Old*: Row-wise prefix dominance on every row 712–718 for shed, sold, and per-actor deposits.
   *New Invariant (Terminal Dominance with Intermediate Solvency Guard)*:
   - **Terminal Dominance (Step 718)**: Candidate terminal pre-market shed inventory weakly dominates baseline for all products ($S_{\text{cand}}(718, p) \ge S_{\text{base}}(718, p)$); candidate total deposited units weakly dominates baseline ($\sum_a D_{\text{cand}}(718, a, p) \ge \sum_a D_{\text{base}}(718, a, p)$); candidate terminal sold units weakly dominates baseline ($\text{sold}_{\text{cand}}(718, p) \ge \text{sold}_{\text{base}}(718, p)$).
   - **Intermediate Market Solvency Invariant (Steps 712–717)**:
     At every intermediate step $t \in [712, 717]$, for every product $p \in \text{PRODUCTS\_9}$, candidate pre-market shed inventory must satisfy 100% of baseline scheduled sell orders:
     $$S_{\text{cand, pre-market}}(t, p) \ge Q_{\text{base, sell-ordered}}(t, p)$$
     and candidate money must satisfy baseline scheduled BUY orders.
   - **Zero Overflow Invariant**:
     $\text{overflow\_units} \equiv 0$ across all simulated turns.
3. **Replacement for Acceptance Conjunction**:
   *Old*: `changed and deposited_gain and all(sold_delta >= 0) and any(sold_delta > 0)`.
   *New Invariant (Terminal Economic Acceptance)*:
   $$\text{accepted} = \text{worker\_changed} \land (\Delta_{\text{money}} > 0) \land (\forall p: \Delta_{\text{sold}}(p) \ge 0) \land (\exists p: \Delta_{\text{sold}}(p) > 0) \land (\text{overflow} == 0)$$
   where $\Delta_{\text{money}} = \text{money}_{\text{cand}}(718) - \text{money}_{\text{base}}(718)$ evaluated under the engine's exact market execution rules.

---

## PHASE 2 — FULL H1 / H2 / H3 / H4 TAXONOMY

In the repository codebase and governing documentation (`01_ISOLATION_AUDIT.md`, `02_PREREGISTRATION.md`, `h1_*.py`), the "H" prefix is used with two distinct meanings:
1. **Scientific Hypotheses** (H1-ACT, H1-OVERALL)
2. **Transplant Hazards / Adaptations** (H1, H2, H3, H4) from Dmitrii's standalone agent to the V54++ residual architecture.

The authoritative mapping is established below:

| Label | Exact Definition | Code / Document Location | Scientific Role | Activated in ARCH-002? | Relevant to ARCH-003? | Changing it creates a new factor? |
|---|---|---|---|---|---|---|
| **H1-ACT** | Conditional paired contrast ($\text{H1} - \text{baseline}$) among activation-exposed episodes has positive mean with zero exposed-seed harm and min delta $\ge 0$. | `02_PREREGISTRATION.md` §2; `h1_telemetry.py` | Primary Falsifiable Scientific Hypothesis | **No** (0.00% exposure; untestable Pattern C) | **Yes** (Primary hypothesis to be tested in ARCH-003) | **No** (Core target of investigation) |
| **H1-OVERALL** | Unconditional paired mean contrast ($\text{H1} - \text{baseline}$) across all $N=500$ seeds is statistically distinguishable from zero. | `02_PREREGISTRATION.md` §2, §15, §19 | Secondary Overall Estimand | **No** (Paired neutral due to 0 adoptions) | **Yes** (Unconditional randomized estimand) | **No** (Standard CRN contrast) |
| **H1 (Sparse Markets)** | Adaptation admitting sparse market order lists `[["SELL", p, q], ...]` as-is without coercing into Dmitrii's dense 9-product fixed clearing shape (`_fixed_market`). | `02_PREREGISTRATION.md` §8.2/H1; `h1_dominance.py:9`; `01_ISOLATION_AUDIT.md` §18 | Implementation Adaptation & Schema Guard | **Yes** (Evaluated in all games; permitted sparse market passthrough) | **Yes** (Must be retained; V54++ uses sparse markets) | **Yes** (Changing it would break baseline compatibility) |
| **H2 (BUY Orders & Sale-Timing Prohibition)** | (1) Modeled engine `BUY_PRODUCT` WHEAT with Entry-Money Coverage Gate ($125 \times U$) to ensure opponent price independence; FERTILIZER buys fail closed.<br>(2) Prohibition on advance/subtract sales or preemption overlays. | `02_PREREGISTRATION.md` §5/P5, §8.2/H2; `h1_dominance.py:10,179,206`; `h1_const.py:35` | Safety Gate (determinism) & Protocol Boundary (no macro sale-timing) | **Yes** (G4 gate evaluated; yarn BUYs modeled; P5 enforced) | **Yes** (G4 gate and 712–717 verbatim market emission retained) | **Yes** (Allowing 712–717 market changes would create macro sale-timing confound) |
| **H3 (Ledger Cloning & Exact Reuse)** | Shadow clones readable controller ledgers at $E$ (`due`, `pending`, `opponent_supply`, `last_market_net`, etc.) and reuses exact unbound residual controller methods (`_repay`, `_update_flow`, etc.) without state leakage. | `02_PREREGISTRATION.md` §8.2/H3; `h1_baseline.py:2,72–100`; `h1_shadow.py:287` | Implementation Safety & State Isolation | **Yes** (Active in every step-712 call; verified 100% leak-free) | **Yes** (Must be retained unchanged; guarantees zero state leakage) | **Yes** (Tampering with live ledgers would violate one-factor isolation) |
| **H4 (Fronting & Fertilizer Scope Boundary)** | (1) Deterministic simulation of money/flow-dependent fronting.<br>(2) Scope boundary (R8/P6): `COLLECT_FERTILIZER` permitted ONLY on tiles flagged available at step $E$; no general fertilizer program. | `02_PREREGISTRATION.md` §5/P6, §8.2/H4; `h1_shadow.py:2,251–267`; `01_ISOLATION_AUDIT.md` §18.3 | Implementation Fidelity & Scope Boundary | **Yes** (Fronting mirrored; fertilizer collection tracked in telemetry) | **Yes** (Must be retained unchanged; confines H1 to terminal reap-and-ferry) | **Yes** (Expanding fertilizer policy would introduce multi-turn macro agricultural confound) |

---

## PHASE 3 — COMPARISON OF THE FOUR REPAIR ARCHITECTURES

The four repair architectures identified in the forensic report are compared neutrally below without ranking, scoring, or preference claims:

| Dimension | Option A: Physical Stock Acceptance | Option B: Terminal Dominance + Stock Acceptance | Option C: Terminal Market Liquidation Alone | Option D: Full Terminal Synthesis (Safe Dominance + Liquidation + Economic Acceptance) |
|---|---|---|---|---|
| **Exact Code Changes** | Modify `h1_dominance.py:acceptance()`: replace `some_positive on sold_delta` with `deposited_gain > 0` or `stock_value_gain > 0`. | Modify `h1_dominance.py:dominates()`: remove row-wise prefix checks; check step-718 shed/deposits.<br>Modify `h1_dominance.py:acceptance()` to check stock gain. | Modify `h1_shadow.py:simulate_schedule`: compute step-718 market via `terminal_market`.<br>Modify `h1_agent.py:_emit`: emit computed step-718 market. | Modify `h1_dominance.py:dominates()`: Terminal Dominance + Intermediate Market Solvency Guard.<br>Modify `h1_shadow.py` & `h1_agent.py`: Step-718 market liquidation.<br>Modify `acceptance()`: $\Delta_{\text{money}} > 0 \land \Delta_{\text{sold}} > 0$. |
| **Exact Protocol Changes** | Amend `02_PREREGISTRATION.md` §8.1(5) acceptance definition. Retain D3 (verbatim markets 712–718) and D5 (prefix dominance). | Amend `02_PREREGISTRATION.md` §8.1(1) (dominance) and §8.1(5) (acceptance). Retain D3. | Amend `02_PREREGISTRATION.md` §0/D3 (step-718 market rule). Retain D5 (row-wise prefix dominance). | Amend `02_PREREGISTRATION.md` §0/D3 (step-718 liquidation) and §0/D5 (intermediate solvency dominance + economic acceptance). |
| **Scientific Question Tested** | Does adopting reap-and-ferry routes that increase terminal shed inventory under frozen verbatim markets improve terminal score? | Does adopting reap-and-ferry routes under relaxed terminal dominance and frozen verbatim markets improve terminal score? | Does allowing step-718 market liquidation make reap-and-ferry effective when restricted by strict row-wise prefix dominance? | Does an isolated terminal optimizer that reschedules late worker actions, preserves intermediate market solvency, and liquidates inventory at step 718 improve terminal score without tail harm? |
| **ARCH-002 Invariants Retained** | D1 (whitelist), D2 ($E=712$), D3 (verbatim markets 712–718), D4 (search), D5 (prefix dominance), D6, D7, D8, G0–G7, P5, H1–H4. | D1, D2, D3 (verbatim markets 712–718), D4, D6, D7, D8, G0–G7, P5, H1–H4. | D1, D2, D4, D5 (row-wise prefix dominance), D6, D7, D8, G0–G7, P5 (712–717 verbatim), H1–H4. | D1, D2, D4, D6, D7, D8, G0–G7, P5 (712–717 verbatim), G4 ($125 \times U$), zero overflow, H1–H4. |
| **ARCH-002 Invariants Changed** | Acceptance conjunction definition only. | Row-wise prefix dominance (D5) $\to$ terminal dominance.<br>Acceptance conjunction $\to$ physical stock. | D3 (step-718 market rule: verbatim $\to$ liquidation). | D3 (step-718 market rule $\to$ liquidation).<br>D5 (row-wise prefix dominance $\to$ intermediate solvency dominance).<br>Acceptance conjunction $\to$ terminal economic gain. |
| **New Confounders Introduced** | None. | None in market space; worker movement changes uncoupled from coin reward. | Candidate emits non-baseline market orders at step 718 (alters terminal clearing prices and town inventory). | Candidate reschedules intermediate drops AND emits non-baseline market orders at step 718. |
| **Activation Feasibility** | Constrained: Backbone routes remain 100% blocked by prefix dominance. Yarn routes (~24.4%) become activatable. | High: Both backbone and yarn routes can find physical stock gains under terminal dominance. | Partial: Yarn routes (~24.4%) become activatable with $\Delta_{\text{sold}} > 0$. Backbone routes (~75.6%) remain 100% blocked by prefix dominance. | Complete: Both backbone routes (~75.6%) and yarn routes (~24.4%) become activatable when economically superior. |
| **Economic Meaningfulness** | Zero: Extra shed inventory produces $\$0.00$ terminal score. Reward delta remains identically 0.00. | Zero: Extra shed inventory remains unsold; terminal score delta remains identically 0.00. | Meaningful for yarn routes; zero for backbone routes (which remain unactivated). | Fully aligned: Harvested crops are liquidated into liquid currency, directly matching engine score. |
| **Identifiable as H1 Repair?** | Yes (one-line acceptance bug fix). | Partial (changes dominance and acceptance, but leaves economic mechanism disabled). | Yes (one-boundary market repair, but leaves majority mechanism blocked). | Yes (full realization of the intended Dmitrii terminal optimizer transplant). |
| **Classification** | Single-factor bug fix (economically inert). | Multi-factor boundary adjustment (economically inert). | Single-factor boundary adjustment (partial activation). | Coordinated multi-factor boundary adjustment (active & reward-aligned). |

---

## PHASE 4 — DETERMINE THE MINIMAL SCIENTIFIC REPAIR

### A. Step-718 Market Liquidation
- **Determination**: Step-718 market liquidation MUST be permitted.
- **Source Proof**: In `sim.py:319–338`, the engine ends the game at step 718. Final evaluation is `st.farms[p].money`. Crops remaining in `shed` have 0 economic value. In `compiled_v54_plus_residual.py`, the baseline places sell orders sized exactly to its own shed:
  $$Q_{\text{ordered}}(p) = \max(0, \text{shed}(p))$$
  Under verbatim baseline market passthrough, $\Delta_{\text{sold}}(p) \equiv 0$. Physical reap-and-ferry is mathematically incapable of generating reward without step-718 liquidation.
- **Allowed Market Orders at Step 718**:
  - ONLY `SELL` orders: `["SELL", item, quantity]`.
  - Item must be in `PRODUCTS_9`.
  - Quantity must satisfy $1 \le \text{quantity} \le S_{\text{cand, post-drop}}(718, \text{item})$.
  - Maximum 10 orders (`PIN_MAX_ORDERS = 10`).
  - ZERO `BUY` orders, zero `PLACE`, zero speculative orders.
- **Frozen Market Behavior**:
  - Steps 712–717 markets remain 100% frozen to baseline verbatim (P5 retained).
- **Computation Algorithm**:
  Liquidation is computed by applying the frozen baseline `terminal_market(obs, action, rule="collision", replace=True)` (`scripts.v19_terminal.py:190–240`) to the candidate's post-unit simulated state at step 718.
- **Deterministic Verification**:
  Verified by bit-identical assertion between shadow-simulated step-718 market action and live-emitted step-718 market action.

### B. Dominance Condition Replacement
- **Determination**: Rigid row-wise prefix dominance MUST be replaced.
- **Source Proof**: In validation seed 248001 (backbone route), the baseline worker drops 1 crop at step 714. An improving candidate redirects the worker to harvest 3 crops and drop them at step 716. At step 714, candidate deposits are 0, baseline deposits are 1. Rigid row-wise prefix dominance rejects the candidate at step 714 ($0 < 1$), despite the candidate finishing with $+2$ net units. In ARCH-002, 37/37 improving backbone proposals were rejected for this exact reason.
- **Proposed Invariant: Terminal Dominance with Intermediate Market Solvency Guard**:
  An intermediate deposit deficit is economically harmless IF AND ONLY IF it does not cause any intermediate baseline market order to fail.
  Therefore, the new invariant consists of three conjuncts:
  1. **Zero Overflow**: $\text{overflow\_units} \equiv 0$ across all steps 712–718.
  2. **Intermediate Market Solvency Invariant (Steps 712–717)**:
     For every intermediate turn $t \in [712, 717]$ and every product $p \in \text{PRODUCTS\_9}$:
     $$S_{\text{cand, pre-market}}(t, p) \ge Q_{\text{base, sell-ordered}}(t, p)$$
     and candidate money at step $t$ must cover all baseline scheduled BUY orders.
  3. **Terminal Weak Dominance (Step 718)**:
     - $S_{\text{cand, pre-market}}(718, p) \ge S_{\text{base, pre-market}}(718, p) \quad \forall p$
     - $\sum_{\text{actor}} D_{\text{cand}}(718, \text{actor}, p) \ge \sum_{\text{actor}} D_{\text{base}}(718, \text{actor}, p) \quad \forall p$
     - $\text{sold}_{\text{cand}}(718, p) \ge \text{sold}_{\text{base}}(718, p) \quad \forall p$
- **Safety Interpretation**:
  Intermediate deposits have only one causal channel to affect game outcome: fulfilling intermediate market sales. If the candidate shed has sufficient inventory to satisfy 100% of baseline intermediate sales, delaying a deposit has zero adverse effect on intermediate state. Enforcing terminal dominance at step 718 guarantees that the candidate ends with equal or superior inventory, deposits, and sales.

### C. Acceptance Criterion Alignment
Acceptance must directly measure the true engine objective:
$$\text{accepted} = \text{worker\_changed} \land (\Delta_{\text{money}} > 0) \land (\forall p: \Delta_{\text{sold}}(p) \ge 0) \land (\exists p: \Delta_{\text{sold}}(p) > 0) \land (\text{overflow} == 0)$$
where $\Delta_{\text{money}} = \text{money}_{\text{cand}}(718) - \text{money}_{\text{base}}(718)$.
Evaluating strict money gain ensures that the candidate is adopted IF AND ONLY IF it delivers strictly higher liquid score to the agent.

---

## PHASE 5 — SEARCH / PROPOSAL GENERATOR REVIEW

Inspection of `h1_search.py:proposals()` and `plan_terminal()`:

1. **Route Generation**: Generates valid Manhattan walks from worker position to mature crops / flagged fertilizer tiles, appends operation (`HARVEST` or `COLLECT_FERTILIZER`), appends walk to nearest shed-access tile, appends `DROP`, and pads with `PASS` up to horizon (step 718). This structure is physically sound and capable of executing terminal reap-and-ferry.
2. **Optimization Objective**: Proposals are ranked by `(value - obligation, offset, route)`. `value` is evaluated at frozen entry prices. This correctly prioritizes bundles with highest gross value minus baseline worker obligations.
3. **Accounting for Terminal Liquidation**: In ARCH-002, `stock_value` evaluated $\sum (\text{sold} + \text{shed}) \times \text{price}$. With step-718 market liquidation, the candidate's deposited crops are converted into `sold` and `money`. The proposal generator's physical bundle value remains a monotonic proxy for terminal coin liquidation value.
4. **Obligation Calculation**: Lines 99–102:
   ```python
   obligation = sum(prices.get(item, 0) * (count - prefix.get(item, 0))
                    for item, count in future.items())
   ```
   Measures the value of deposits the baseline worker was already scheduled to make between `offset` and step 718. Retaining `value - obligation` ensures the optimizer only selects routes that deliver *strictly more value* than the worker's default path.
5. **Direct-Return Logic**: Lines 168–172 reserve two carry-closure variants (workers already holding cargo walk directly to shed and drop). This remains vital to ensure cargo in backpacks at step $E$ is not abandoned.
6. **No-Steal Coordination**: Lines 79–84 and `no_steal_pass` prevent multi-worker collisions on the same tile/op. This remains strictly necessary.
7. **Route Length / Horizon Logic**: Checked via `distance <= horizon - offset`. Ensures routes never exceed step 718.
8. **Search Budget Adequacy**: 128 simulations across 1 pass and $\le 8$ proposals/worker evaluated in 15–35 ms per seat. Budget is adequate and safe.
9. **No-Tuning Rule**: **The proposal generator structure, simulation budget (128), and proposal caps ($\le 8$) MUST REMAIN FROZEN**. Adjusting search budgets or proposal counts would introduce an uncontrolled exploratory confound.

---

## PHASE 6 — SHADOW SIMULATION REDESIGN

### 1. Engine Order of Operations at Step 718
Derived directly from `sim.py:319–338`:
```
Step 718 Execution Order:
  1. Worker Commands Execution (apply_unit_actions):
     - Movements update worker coordinates (pos_x, pos_y).
     - DROP operations by workers on shed-access tiles transfer cargo from inv to shed.
     - HARVEST / COLLECT_FERTILIZER collect crops into worker backpack inv.
     - Excess items exceeding SHED_CAPACITY (100) trigger OVERFLOW destruction.
  2. Market Execution (process_market):
     - Scheduled market orders execute against current shed stock and public inventory.
     - SELL orders deduct units from shed, add quote currency to farm.money, increment sold counters.
     - BUY orders deduct money, add units to shed.
  3. Town Consumption (town_consume):
     - Public shop inventory decrements based on town demand.
  4. Plant Decay (decay_plants):
     - Standing unharvested plants decay.
  5. Episode Conclusion:
     - step >= episode_steps - 2 (718 >= 718) -> st.done = True.
     - Terminal reward evaluated as farm.money.
```

### 2. Redesigned Shadow Simulation Flow
In `EXP-ARCH-003_H1_TERMINAL_REPAIR`, `simulate_schedule` in `h1_shadow.py` will execute as follows:
```
For offset, t in enumerate(range(712, 719)):
    1. Apply worker commands from candidate schedule.
    2. Record pre_market_shed.
    3. If t < 718:
         - Market orders = baseline_schedule[offset]["market"] (verbatim passthrough).
         - Check Intermediate Market Solvency: pre_market_shed >= baseline sell orders.
       If t == 718:
         - Generate Candidate Liquidation Market Orders via terminal_market(obs_718, candidate_pre_market_shed).
         - Market orders = candidate liquidation orders.
    4. Execute market orders (updates sold, shed, and money).
    5. Apply plant decay.
    6. Record row state: {pre_market_shed, post_market_shed, deposited_by_actor, sold, money}.
```

### 3. Verification and Rollback
- If candidate fails Intermediate Market Solvency at any step $t < 718$, candidate is immediately marked non-dominating.
- If candidate triggers overflow at any step, candidate is immediately rejected.
- At step 718, live agent emits candidate worker commands and candidate liquidation market orders.

---

## PHASE 7 — MICRO-VALIDATION BEFORE PROSPECTIVE EXECUTION

Prior to prospective execution, the following 8 deterministic validation tests must be implemented and evaluated strictly on non-prospective fixtures and consumed seeds:

- **TEST 1 — Acceptance Reachability (Consumed Seed 248012)**:
  - *Context*: Seed 248012 (yarn route) failed in ARCH-002 with `ABSTAIN_ACCEPT` because `some_positive on sold_delta` was false under verbatim markets.
  - *Requirement*: Under ARCH-003 step-718 market liquidation, the candidate must successfully convert harvested crops into sold units ($\Delta_{\text{sold}} > 0$) and positive currency delta ($\Delta_{\text{money}} > 0$), resulting in `OK_ACTIVATED`.
- **TEST 2 — Backbone Repair Reachability (Consumed Seed 248001)**:
  - *Context*: Seed 248001 (backbone route) failed in ARCH-002 because an intermediate drop rescheduling violated row-wise prefix dominance.
  - *Requirement*: Under ARCH-003 Intermediate Solvency Dominance, the candidate's temporary intermediate deposit deficit must pass solvency (zero intermediate sales missed) and terminal dominance, successfully activating.
- **TEST 3 — Step-718 Liquidation Parity**:
  - *Requirement*: The market orders generated by shadow simulation at step 718 must bit-identically match the market orders emitted by `agent.act()` at step 718.
- **TEST 4 — Reward Parity**:
  - *Requirement*: Terminal money computed by the shadow simulator must bit-identically match terminal money produced by the engine port (`kagsim_py`) when executing the identical action sequence.
- **TEST 5 — No-Steal Invariant**:
  - *Requirement*: Multi-actor synthetic fixture where a candidate proposal targets a cell/op already scheduled by another worker must be rejected by `no_steal_pass`.
- **TEST 6 — Activation Handshake & Fail-Closed Safety**:
  - *Requirement*: Out-of-window calls ($t < 712$), missing observation keys, configuration discrepancies, BUY coverage deficits, or non-consecutive steps must immediately abort to baseline live execution with zero state corruption.
- **TEST 7 — Pure Passthrough Invariant**:
  - *Requirement*: On seeds or states where no candidate passes dominance/acceptance, H1 must return baseline actions with 100% bit-identity across all turns.
- **TEST 8 — Isolation and Contamination Checks**:
  - *Requirement*: Assert zero modification to pre-entry steps 0–711; assert steps 712–717 markets are verbatim baseline; assert no fertilizer collection on unflagged tiles; assert no checkpoint $\le 288$ or $H=500$ logic is reachable.

---

## PHASE 8 — SUCCESSOR EXPERIMENT PROTOCOL DRAFT

Below is the complete, self-contained draft text of `experiments/EXP-ARCH-003_H1_TERMINAL_REPAIR/02_PREREGISTRATION.md`:

```markdown
# EXP-ARCH-003 H1 — PREREGISTRATION PROTOCOL: TERMINAL REPAIR

**Experiment**: `EXP-ARCH-003_H1_TERMINAL_REPAIR`
**Document**: `02_PREREGISTRATION.md`
**Date**: 2026-09-16
**Status**: DRAFT PREREGISTRATION — Execution gated by formal freeze commit.
**Authority**: Successor to `EXP-ARCH-002_H1_DOMINANCE_TERMINAL/` (frozen post-forensic).
**Governance**: Zero-Leakage; One-Factor Architectural Isolation; Questions A (DEV-007) and B (ARCH-003) remain strictly disjoint.
**Objective**: Test whether the repaired, dominance-gated reap-and-ferry terminal optimizer with step-718 market liquidation causally improves terminal score on the frozen V54++ residual baseline without tail harm.

## §0. Decision Freeze Table (D1–D8)

| ID | Decision | Frozen Selection | Specification |
|---|---|---|---|
| D1 | Worker-command whitelist | Unit ops {N, S, E, W, HARVEST, COLLECT_FERTILIZER, DROP, PASS}; DROP-only (no PLACE); COLLECT restricted to tiles flagged available at E. | §5, §7 |
| D2 | Entry step E | **E = 712** (7-turn window 712–718). | §6 |
| D3 | Step-718 market rule | **Deterministic Step-718 Market Liquidation**: Recomputed from candidate's simulated post-drop shed state at step 718 using frozen baseline `terminal_market(rule="collision", replace=True)`. Steps 712–717 markets remain 100% verbatim baseline passthrough. | §5, §8 |
| D4 | Candidate search budget | 128 simulations, 1 pass, <= 8 proposals/worker; carry-closure + top-6 singles + top-3xtop-3 pairs; 2 direct reserves; frozen integer entry prices. | §7, §11 |
| D5 | Dominance predicate | **Terminal Dominance with Intermediate Solvency Guard**: (1) Zero overflow; (2) Intermediate market solvency on 712–717 (pre-market shed >= baseline scheduled sell orders); (3) Terminal weak dominance at step 718 on shed, total deposits, and sold units; (4) Strict terminal money gain ($\Delta_{\text{money}} > 0$); (5) No-steal gate; (6) Acceptance conjunction. | §8 |
| D6 | Tolerances / tie-breaking | Strict `>` everywhere; integer inclusion; frozen proposal rank keys; last strictly improving wins; fixed worker/offset enumeration order. | §9 |
| D7 | Abstention procedure | G0–G7 entry guards + stepwise re-verification + fail-safe abandon-to-baseline + frozen reason enum + per-seedxseat telemetry. | §10 |
| D8 | Baseline identity | **`candidates/compiled_v54_plus_residual.py`** (SHA-256 `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb`). | §3 |

## §1. Research Question
Does grafting a repaired terminal optimizer—featuring step-718 market liquidation, intermediate market solvency dominance, and strict terminal coin gain acceptance—onto the frozen V54++ residual baseline improve expected terminal money without introducing tail degradation?

## §2. Falsifiable Hypotheses
- **H1-ACT**: Among prospectively defined activation-exposed episodes (plan accepted and activated in >= 1 seat), the conditional paired contrast (H1 - baseline) has positive mean ($\bar{\Delta}_{\text{exposed}} > 0$) with zero exposed-seed harm ($\min(\Delta_i) \ge 0$ on exposed seeds) and zero H1-attributable catastrophic damage.
  - *Falsification Criteria*: $k \le 2$ (mechanism inactive / untestable, Pattern C); conditional mean $\le 0$; any exposed-seed harm ($\Delta_i < 0$); or confirmed H1 execution failure.
- **H1-OVERALL**: The unconditional paired mean contrast over all $N=500$ seeds is statistically distinguishable from zero ($\alpha = 0.05$, two-sided test).

## §3. Baseline Specification
- **File**: `candidates/compiled_v54_plus_residual.py`
- **SHA-256**: `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb`
- **Status**: Read-only, bit-identical frozen live submission 56146971.

## §4. Experimental Design & Prospective Cohort
- **Cohort**: Seeds `330000–330499` inclusive ($N = 500$ seeds).
- **Design**: Common Random Numbers (CRN), 2 games per seed:
  - Game a: Seat 0 = Treatment (ARCH-003), Seat 1 = Baseline (V54++)
  - Game b: Seat 0 = Baseline (V54++), Seat 1 = Treatment (ARCH-003)
- **Total Games**: Exactly 1,000 games.
- **Paired Estimand**: $\Delta_i = 0.5 \times (\text{Score}_{\text{treatment}, i, a} - \text{Score}_{\text{baseline}, i, a} + \text{Score}_{\text{treatment}, i, b} - \text{Score}_{\text{baseline}, i, b})$.

## §5. Safety Invariants & Boundary Constraints
- **P-PURE**: Steps 0–711 bit-identical between treatment and baseline instances.
- **P5**: Steps 712–717 market orders emitted verbatim from live baseline.
- **D3**: Step 718 market orders generated via frozen baseline `terminal_market` on candidate's simulated shed.
- **G4**: Entry-money coverage gate: `money_at_E >= 125 * U`.
- **R8 / P6**: `COLLECT_FERTILIZER` restricted to tiles flagged at step $E$.

## §6. Mechanism Exposure & Diagnostic Reporting
- Per-game reason codes: `OK_ACTIVATED`, `ABSTAIN_DOMINANCE`, `ABSTAIN_ACCEPT`, `ABSTAIN_SOLVENCY`, `ABSTAIN_NO_GAIN`, `ABSTAIN_NOSTEAL`, `ABSTAIN_BUY_COVERAGE`, `ABSTAIN_CONFIG`, `ABANDON_MISMATCH_T`.
- Telemetry records: planning time (ms), simulations evaluated, changed workers, sold unit delta, terminal money delta.

## §7. Quarantine & Governance
- Final Holdout `214200–214249`: Strictly virgin, uninspected, untouched.
- DEV-007 Cohort `310000–310499`: Strictly virgin, untouched.
- ARCH-002 Cohort `320000–320499`: Permanently consumed.
- Zero network calls; zero remote Kaggle submissions.
```

---

## PHASE 9 — FRESH COHORT GOVERNANCE & VERIFICATION

### 1. Cohort Specification
- **Proposed Cohort**: Seeds `330000–330499` inclusive ($N = 500$ seeds, 1,000 games under CRN).

### 2. Disjointness Verification Against All Protected Blocks
| Partition Name | Seed Range | Disjointness Status | Proof |
|---|---|---|---|
| **Virgin Final Holdout** | `214200–214249` ($N=50$) | **DISJOINT** | $330000 > 214249$ |
| **DEV-007 Reserved Cohort** | `310000–310499` ($N=500$) | **DISJOINT** | $330000 > 310499$ |
| **DEV-007 Fallback 1** | `410000–410499` ($N=500$) | **DISJOINT** | $330499 < 410000$ |
| **DEV-007 Fallback 2** | `510000–510499` ($N=500$) | **DISJOINT** | $330499 < 510000$ |
| **ARCH-002 Consumed Cohort** | `320000–320499` ($N=500$) | **DISJOINT** | $330000 > 320499$ |
| **DEV-006 Consumed Cohort** | `248000–248049` ($N=50$) | **DISJOINT** | $330000 > 248049$ |
| **DEV-005 Consumed Cohort** | `247000–247049` ($N=50$) | **DISJOINT** | $330000 > 247049$ |
| **Historical Named Reserved** | `249000–260049`, `300000–300049` | **DISJOINT** | $330000 > 300049$ |
| **Historical Benchmarks / Sweeps**| `50000–50499`, `60000–60049` | **DISJOINT** | $330000 > 60049$ |

### 3. Repository Search Audit
A full ripgrep search across the entire repository confirmed **zero occurrences** of seed 330000 or any seed in the 330000–330499 block. The proposed cohort is 100% virgin, unexecuted, unscouted, and uninspected.

---

## PHASE 10 — IMPLEMENTATION PLAN

### 1. Proposed File Structure
Directory: `experiments/EXP-ARCH-003_H1_TERMINAL_REPAIR/`

| File Path | Role | Origin / Action | Summary of Function-Level Changes |
|---|---|---|---|
| `01_ISOLATION_AUDIT.md` | Successor Boundary Audit | NEW | Authoritative isolation boundary document for ARCH-003. |
| `02_PREREGISTRATION.md` | Governing Protocol | NEW | Protocol drafted in Phase 8; frozen prior to execution. |
| `03_IMPLEMENTATION_VALIDATION_REPORT.md` | Pre-Execution Validation | NEW | Documents execution of 8 micro-validation tests on consumed seeds. |
| `04_FREEZE_RECORD.md` | Implementation Freeze | NEW | Records frozen Git commit and file hashes before runner freeze. |
| `05_RUNNER_FREEZE_RECORD.md` | Runner Freeze | NEW | Records frozen runner script and runner validation tests. |
| `h1_const.py` | Constants & Pins | COPY from ARCH-002 | Retain constants; update experiment name string. |
| `h1_units.py` | Unit Model Shim | COPY from ARCH-002 | Unchanged bit-identical shim to `unit_model.py`. |
| `h1_baseline.py` | Frozen Baseline Access | COPY from ARCH-002 | Unchanged bit-identical loader for `compiled_v54_plus_residual.py`. |
| `h1_dominance.py` | Dominance & Acceptance | MODIFY | (1) Replace row-wise prefix dominance with `dominates()` implementing Intermediate Solvency Guard + Terminal Dominance;<br>(2) Update `acceptance()` to evaluate strict terminal money gain $\Delta_{\text{money}} > 0 \land \Delta_{\text{sold}} > 0$. |
| `h1_shadow.py` | Shadow Simulator | MODIFY | In `simulate_schedule()`, compute step-718 candidate market orders via `fb.terminal_market` on candidate post-unit shed state. |
| `h1_search.py` | Proposal Generator & Search | COPY from ARCH-002 | Budget (128/1/8) and proposal logic frozen unchanged. |
| `h1_telemetry.py` | Reason Enum & Schema | MODIFY | Add `ABSTAIN_SOLVENCY` reason code if needed; retain schema. |
| `h1_agent.py` | Agent Wrapper & Guards | MODIFY | In `_emit()`, emit computed candidate liquidation orders on step 718; emit live baseline markets verbatim on 712–717. |
| `run_arch003_execution.py` | Clean CRN Runner | NEW | Derived from `run_arch002_h1_reexecution.py` (twin instance, zero double-calling, clean CRN). |
| `tests/test_arch003_validation.py` | Micro-Validation Suite | NEW | Implements Tests 1 through 8 on consumed seeds. |

### 2. Dependency Graph
```
h1_const.py <---+
                |
h1_units.py <---+---+
                    |
h1_baseline.py <----+---+
                        |
h1_dominance.py <-------+---+
                            |
h1_shadow.py <--------------+---+
                                |
h1_search.py <------------------+---+
                                    |
h1_telemetry.py <-------------------+---+
                                        |
h1_agent.py <---------------------------+
                                        |
run_arch003_execution.py <---------------+
```

---

## PHASE 11 — GOVERNANCE HARD STOP

```
================================================================================
STATUS:
DESIGN ONLY — NO FILES MODIFIED — NO PROSPECTIVE SEEDS EXECUTED
================================================================================
```

### 1. Files That Must Remain Permanently Frozen
The following historical artifacts are permanently frozen and must NEVER be modified:
- `experiments/EXP-ARCH-002_H1_DOMINANCE_TERMINAL/01_ISOLATION_AUDIT.md`
- `experiments/EXP-ARCH-002_H1_DOMINANCE_TERMINAL/02_PREREGISTRATION.md`
- `experiments/EXP-ARCH-002_H1_DOMINANCE_TERMINAL/03_IMPLEMENTATION_VALIDATION_REPORT.md`
- `experiments/EXP-ARCH-002_H1_DOMINANCE_TERMINAL/04_FREEZE_RECORD.md`
- `experiments/EXP-ARCH-002_H1_DOMINANCE_TERMINAL/05_RUNNER_FREEZE_RECORD.md`
- `experiments/EXP-ARCH-002_H1_DOMINANCE_TERMINAL/06_EXECUTION_AND_FORENSIC_REPORT.md`
- `experiments/EXP-ARCH-002_H1_DOMINANCE_TERMINAL/07_REEXECUTION_ELIGIBILITY_AUDIT.md`
- `experiments/EXP-ARCH-002_H1_DOMINANCE_TERMINAL/08_REEXECUTION_FREEZE_RECORD.md`
- `candidates/compiled_v54_plus_residual.py` (Baseline V54++)
- `candidates/closed_loop_architecture/dev_005_confirmed_shop_scheduler.py`
- `candidates/closed_loop_architecture/dev_006_horizon_guard_scheduler.py`
- `extracted_agents/dmitrii_lb2800/unit_model.py`

### 2. Cohorts That Must Remain Strictly Protected
- **Final Holdout**: `214200–214249` (VIRGIN, PROTECTED)
- **DEV-007 Reserved Cohort**: `310000–310499` (VIRGIN, PROTECTED)
- **DEV-007 Fallbacks**: `410000–410499`, `510000–510499` (VIRGIN, PROTECTED)
- **ARCH-002 Cohort**: `320000–320499` (PERMANENTLY CONSUMED)

### 3. Files Permitted to be Created Next (Upon Implementation Authorization)
- `experiments/EXP-ARCH-003_H1_TERMINAL_REPAIR/01_ISOLATION_AUDIT.md`
- `experiments/EXP-ARCH-003_H1_TERMINAL_REPAIR/02_PREREGISTRATION.md`
- `experiments/EXP-ARCH-003_H1_TERMINAL_REPAIR/h1_*.py`
- `experiments/EXP-ARCH-003_H1_TERMINAL_REPAIR/tests/`

### 4. Validation Experiments That Are Allowed
- Offline deterministic unit tests on consumed seeds (`248000–248049`) and synthetic test fixtures.
- Bit-identical micro-transition tests against the engine port (`kagsim_py`).

### 5. Prospective Experiments Forbidden Until Formal Freeze
- **Execution of cohort `330000–330499` is STRICTLY FORBIDDEN** until:
  1. All implementation modules pass the complete 8-item micro-validation suite.
  2. `03_IMPLEMENTATION_VALIDATION_REPORT.md` is committed.
  3. `04_FREEZE_RECORD.md` is committed and sealed with an immutable Git commit hash.
  4. Execution runner validation passes and `05_RUNNER_FREEZE_RECORD.md` is sealed.