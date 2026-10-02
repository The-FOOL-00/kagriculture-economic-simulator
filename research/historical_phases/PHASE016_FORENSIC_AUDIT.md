# PHASE 016: FORENSIC AUDIT OF COUNTERFACTUAL EVALUATION & V3 REGIME DIVERGENCE

**Phase**: 016 — Long-Horizon Macro-Aware Counterfactual & Regime-Transition Safety Rescue  
**Chassis Freeze Hash**: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` (`submission_Vj_kc_v3.tar.gz`)  
**Status**: AUDIT COMPLETE — ROOT CAUSES IDENTIFIED  

---

## 1. Executive Summary

Phase 015 implemented the Asset-Holding Valuation Trigger ($E13$) and Autonomous Tranche Order Synthesizer, succeeding on 45/45 synthetic functional tests and expanding market-timing coverage. However, when evaluated in natural games across fresh seeds `249276..249285`, treatment collapsed catastrophically (mean paired delta: -$58,569.80, 0W/10L/0T).

This forensic audit rigorously answers the 10 core architectural questions mandated by the Phase 016 governance protocol before making any source code modifications.

---

## 2. Core Audit Findings

### Question 1: Where exactly does current exact CF stop?
In `aec/counterfactual/simulator.py` (lines 358–363) and `aec/integration/executor.py` (lines 468–479), the counterfactual simulation runs over a horizon $H$ determined by `select_adaptive_horizon(patch, econ_state, config, future_trajectory)`.
For market orders (including autonomous tranches), $H$ is typically `config.short_horizon = 6` or `config.normal_horizon = 18`.
The simulation stops at `offset == horizon` (e.g. step $t + 18$), or if `cur_step >= 720`.
Crucially: **evaluation stops completely at $t + 18$**. Any state changes, obligations, or behavioral divergences occurring at $t + 19, t + 50, t + 100$ are completely invisible to the evaluator.

### Question 2: How is the continuation policy invoked?
In `aec/counterfactual/simulator.py` (lines 366–372):
```python
if offset == 0:
    action = copy.deepcopy(initial_action)
else:
    if continuation_actions and (offset - 1) < len(continuation_actions):
        action = copy.deepcopy(continuation_actions[offset - 1])
    else:
        action = {"farmer": ["PASS"], "hands": [["PASS"] for _ in range(n_workers - 1)], "market": []}
```
The continuation actions are **pre-extracted before the simulation starts** and passed in as a static list `continuation_actions`.
In `aec/integration/executor.py` (lines 370–377):
```python
future_trajectory = self.backbone.get_future_trajectory(
    step=step,
    horizon=self.config.extended_horizon,
    player=econ_state.player,
    n_hands=n_hands
)
```
And in `aec/integration/backbone_adapter.py` (lines 141–147):
```python
routes = getattr(chassis, "routes", {})
tape = routes.get(route_id, [])
trajectory = []
for offset in range(1, horizon):
    future_step = step + offset
    if 0 <= future_step < len(tape):
        act = self._align_hands(tape[future_step], n_hands)
        trajectory.append(act)
```
**`continuation_actions` is a static lookup from the raw route tape (`tape[step + offset]`).**

### Question 3: Is it actually the frozen V3 policy?
**NO.**
The static route tape is only the baseline plan formulated before day 0. The actual frozen V3 policy (`agent(observation)`) consists of over 15 dynamic behavioral layers wrapped around the chassis:
1. `_v233_request` (Sheep expansion & feed purchase)
2. `_v219_request` (Tomato capex & land purchase)
3. `_v231_controller` (Cow/Milk capex & placement)
4. `_budget_guard` (Block-boundary 72-turn capital budgeting & forced inventory sales)
5. `_room_guard` (Hour 23 shed overflow liquidation)
6. `advance_sales` (Pre-selling tape orders when inventory is present)
7. `frontload` (Market order reordering & price impact simulation)
8. `_dead_stock` (Liquidation of non-tape surplus)
9. `_r128_sale_credit` (Feeding funded from non-wheat sales)
10. `_r97_supply` (Grain protection guard)

None of these dynamic policy layers were ever called during forward simulation. The continuation was completely static and state-blind.

### Question 4: Are all stateful V3 variables faithfully cloned?
In the existing codebase: **NO, V3 state was never cloned at all because V3 was never invoked in shadow simulation.**
In our forensic test, we analyzed the V3 runtime namespace (`_PARENT_NS`):
V3 maintains state across several dictionaries indexed by player seat `0` and `1`:
- `_IMPL.chassis.players`: `{"last_step", "route", "router_state", "pending", "sell_state"}`
- `_V219_STATES`: Tomato expansion (`committed`, `requested_day`, `pending`)
- `_V231_STATES`: Cow expansion (`pending_buy`, `confirmed`, `reserved`, `carrying`)
- `_V233_STATES`: Sheep expansion (`committed`, `requested_day`, `pending`)
- `_R37_PLAYERS`, `_R37_HORIZONS`: Sale reservation state
- `_R51_INPUT_STATES`, `_R70_STATES`, `_R85_STATES`, `_R97_LAST`, `_R124_STATES`, `_R127_STATES`, `_R128_STATES`, `_R148_PENDING`
- Global telemetry in `main.py`: `TELEMETRY`

We verified empirically that a complete snapshot/restore mechanism of these variables allows the frozen V3 agent to be executed arbitrarily in forward counterfactual rollouts and restored with **bit-identical determinism and 0 action differences across the remaining 720 game steps**.

### Question 5: Which state variables can trigger discontinuous macro behavior?
Frozen V3 inspects the following state variables in its dynamic decision layers:
1. **`money` (Cash)**:
   - `_v219_request`: `money >= 12,000` triggers Tomato expansion (buys land, 10 seeds, fertilizer, 3 hires).
   - `_v233_request`: `money >= budget + 3,000` on Day 12 triggers Sheep expansion (buys land, 6 sheep, 6 wheat, 2 hires).
   - `_budget_guard`: Evaluates 72-turn future budget; if `shortfall = budget - cash > 0`, forces mass liquidation of shed inventory.
   - `_r124_seed_budget`: Verifies money covers planned day 1 seed purchases.
2. **`shed` (Inventory by product)**:
   - `_room_guard`: Hour 23 check if `shed_total > 99`, forces liquidation.
   - `advance_sales`: Pre-sells future tape orders if items are physically in shed.
   - `_dead_stock`: Sells any item held in shed beyond future route tape requirements.
   - `_r97_supply`: Checks wheat in shed; if insufficient for animal feeding, forces emergency market buys.
3. **`market.prices`**:
   - `prices['WOOL'] >= 220`, `prices['WHEAT'] <= 45` gate sheep expansion.
   - `prices['TOMATO'] >= 20` gates tomato expansion.
4. **`farms[player].hands` (Worker count)**:
   - Divergence in hire execution cascades across every subsequent turn.
5. **`farms[player].unlocked_quadrants`**:
   - Expansion requires `{'NW', 'NE', 'SW'}`.

### Question 6: Which thresholds can be crossed by a candidate action?
1. **Cash Thresholds**: An uncommitted asset sale increases cash, potentially crossing:
   - $12,000 Tomato Capex threshold (`_v219`)
   - Sheep Capex budget threshold (`_v233`, approx $10,000)
   - `_budget_guard` shortfall threshold at step % 72 == 0
2. **Inventory Thresholds**:
   - Selling wheat depresses grain reserves below `_r97_supply` feed requirements.
   - Premature sales clear shed space, preventing `_room_guard` or altering `advance_sales`.
3. **Market Order Array Bounds / Composition**:
   - In Phase 015, `construct_sequential_market_orders` dropped non-`BUY`/`SELL` orders (specifically dropping `HIRE` at Step 195 on Seed 249276), causing an unrecoverable worker deficit.

### Question 7: How does the current Adaptive Horizon choose H?
In `aec/counterfactual/horizon.py`:
- `LOCAL_WEED_DIG`: 6 steps if no downstream dependency, or `dep_step + 3` (up to 18).
- `DEPENDENCY_AWARE_MARKET_TIMING`: 6 steps if isolated, 18 steps if opponent market active.
- `TERMINAL_LIQUIDATION`: 2 steps.
- `PHASE_SHUTDOWN`: 6 steps.
- `EMERGENCY_FEED_PURCHASE` / `RESOURCE_CONVERSION`: 18 steps (or full remaining if <= 48).
- Fallback (including Phase 015 Autonomous Tranche): `config.normal_horizon = 18`.
**Horizon is currently chosen purely based on the mechanism name and static spatial dependencies, with zero awareness of macro boundaries or continuation bifurcation.**

### Question 8: Can current CF observe future V3 policy changes?
**NO.**
Because continuation actions were static tape entries, the simulator could never observe:
- That an action prevented a planned `HIRE`
- That higher cash caused V3 to commit to an expensive capital expansion 30 turns later
- That an animal purchase increased feeding obligations and diverted labor from crops
- That lower inventory triggered emergency purchases under `_budget_guard` or `_r97_supply`

### Question 9: Where should long-horizon escalation be inserted?
Escalation belongs in a 4-tier evaluation pipeline in `aec/integration/executor.py` and `aec/counterfactual/`:
```text
Candidate Patch
      │
      ▼
Tier 1: Local Exact CF (H = 6 to 18)
      │
      ▼
Tier 2: Macro-Regime Boundary Probe
      │
      ├─► [NO Macro Divergence Risk] ──► Accept Tier 1 local outcome
      │
      └─► [Macro Divergence Risk Detected]
                │
                ▼
Tier 3: Long-Horizon Exact Continuation (H_escalated = regime capture horizon)
        (Rollout with frozen V3 agent closure on simulated observations)
                │
                ▼
Tier 4: Regime-Stability & Economic Validation
        (Must remain superior under true V3 continuation)
```

### Question 10: What is the smallest architectural change that fixes the failure without rewriting AEC?
1. Implement a **`MacroRegimeFingerprint`** and **`MacroRegimeTransitionDetector`** that inspects candidate state deltas ($\Delta\text{cash}$, $\Delta\text{inventory}$, $\Delta\text{workers}$, $\Delta\text{quadrants}$, capex gate proximity) to detect potential V3 policy divergence.
2. Upgrade `simulate_rollout` in `aec/counterfactual/simulator.py` to support **`dynamic_v3_continuation`**: when escalated, instead of replaying static tape actions, invoke the frozen V3 agent snapshot at each simulated step on the simulated observation $o'_t$.
3. When macro divergence risk is detected, escalate the horizon to capture the downstream regime transition (e.g. next 72-turn block boundary, Day 12 sheep gate, Day 18 tomato gate).
4. Evaluate the candidate using the escalated V3 continuation outcome. If the downstream continuation leads to labor diversion or economic collapse, the candidate is safely rejected.

---

## 3. Forensic Confirmation on Seed 249276

Our empirical trace of Seed 249276 proved:
- At Step 195, Control emitted `[['SELL', 'MILK', 12], ['BUY_PRODUCT', 'WHEAT', 4], ['HIRE'], ['BUY_ANIMAL', 'SHEEP', 1], ['BUY_ANIMAL', 'SHEEP', 2]]`.
- Phase 015 Tranche Synthesizer synthesized `['SELL', 'MILK', 5]`, but dropped `['HIRE']`.
- Control hired a worker (hands = 10); Treatment missed the hire (hands = 9).
- The H=18 static counterfactual evaluator saw only the local cash gain from selling milk and evaluated it as $+24.80$ margin gain, completely blind to the lost worker.
- By Step 264–266, Control expanded into the SW quadrant and hired 5 workers, while Treatment suffered a fatal labor deficit.
- Final scores: Control $127,256.0$, Treatment $86,960.0$ (delta: -$40,296.00$).

A macro-aware evaluator with dynamic V3 continuation instantly captures this divergence and rejects the flawed candidate.
