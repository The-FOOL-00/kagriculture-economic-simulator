# AEC V1.1 Pre-Fix Verification Audit

**Author:** Independent Scientific Audit Agent  
**Date:** 2026-09-17  
**Git HEAD:** `179dd2fb3151b9f89f479375db6a71b6debfaa64`  
**Frozen V3 Tarball SHA256:** `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`  
**Holdout Partition:** `340050–340199` (Status: **VIRGIN / UNTOUCHED**)  

---

## 1. Objective of Pre-Fix Verification
Before executing code modifications for the Development Fix Pass, this document confirms the exact codebase manifestations, mathematical mechanisms, and failure modes of the four blockers identified in [`reports/AEC_V1_1_ACTIVATION_INTEGRITY_AUDIT.md`](file:///c:/Users/Sundareswaran/Kagriculture/reports/AEC_V1_1_ACTIVATION_INTEGRITY_AUDIT.md).

---

## 2. Confirmation of Blocker 1: FRONTLOAD_ORDERS Positive Fixture Does Not Commit

### Current Code Behavior
In [`tests/aec/test_v1_1_activation.py:554-580`](file:///c:/Users/Sundareswaran/Kagriculture/tests/aec/test_v1_1_activation.py#L554-L580):
```python
def test_synthetic_frontload_positive(self, normal_opening_obs):
    base_act = {
        "farmer": ["PASS"], "hands": [],
        "market": [["BUY_SEED", "WHEAT", 1], ["SELL", "WHEAT", 5]]
    }
    obs = copy.deepcopy(normal_opening_obs)
    obs["private"]["shed"]["WHEAT"] = 10
    obs["farms"][0]["money"] = 150.0

    adapter = BackboneAdapter(agent_fn=lambda o, c: copy.deepcopy(base_act))
    executor = AECExecutor(backbone_adapter=adapter)
    action = executor.act(obs)

    opps = executor.opp_engine.detect_opportunities(...)
    assert len(frontload_opps) == 1
    patches = executor.patch_generator.generate_patches(...)
    assert len(patches) == 1
    assert patches[0].market_mutations == [["SELL", "WHEAT", 5], ["BUY_SEED", "WHEAT", 1]]
```

### Execution Proof
Running `executor.act(obs)` in this test fixture produces:
- `decision = "ABSTAIN"`
- `committed_mechanism = None`
- `abstain_reason = "NO_CANDIDATE_CERTIFIED_SUPERIOR"`
- `delta_margin = $0.0`, `delta_money = $0.0`
- `economic_rejection_reason = "Frontload produces identical monetary outcome: margin delta $0.0, cash delta $0.0"`

### Why It Is Scientifically Material
The test passed only because it asserted patch generation on intermediate objects (`opp_engine` and `patch_generator`), and never asserted `assert executor.latest_telemetry.decision == "COMMIT"`. The development report `TR-AEC-V1.1-20260917` claimed 4 positive synthetic mechanism commits, but in reality only 3 committed. `FRONTLOAD_ORDERS` has never successfully committed under AEC.

### Proposed Fix
1. Provide an opponent state with active sale pressure and rival sell orders in the simulation.
2. Ensure the order execution order creates genuine lockstep price slippage for the delayed baseline sell.
3. Assert all commit invariants: `decision == "COMMIT"`, `committed_mechanism == "FRONTLOAD_ORDERS"`, and `returned action == candidate action`.

---

## 3. Confirmation of Blocker 2: Ungrounded Labor Wage ($100/24) and Extrapolated Crop Valuation

### Current Code Behavior
In [`aec/evaluation/asset_value.py:31-33, 96, 155-159`](file:///c:/Users/Sundareswaran/Kagriculture/aec/evaluation/asset_value.py#L31-L33):
```python
# Derived from game hiring economics: $100 / day (24 turns) = $4.1667 per worker-step
LABOR_COST_PER_STEP: float = 100.0 / float(TURNS_PER_DAY)
...
opp_cost = self.labor_cost  # $4.1667
...
expected_yield = EXPECTED_CROP_YIELDS.get(crop, 4)
price = econ_state.market.current_prices.get(crop, BASE_PRICES.get(crop, 10))
seed_cost = CROP_SEED_PRICE.get(crop, 20)
crop_profit = max(0.0, float(expected_yield * price - seed_cost))
gross_benefit += crop_profit
...
net_val = gross_benefit - opp_cost  # $90.0 - $4.17 = +$85.83
```

### Why It Is Scientifically Material
1. **Ungrounded Constant:** In Kaggle Agriculture (`sim.hpp`, `config.py`), farmer labor is free, and hired hands follow a Fibonacci sequence ($1, $1, $2, $3, $5, $8, $13, $21, $34, $55, $89...). There is no $100 wage constant.
2. **100% Extrapolated Value:** The counterfactual simulation horizon ($H=18$) does not observe crop maturity (Wheat takes 48 steps). The $+85.83$ economic value is entirely extrapolated by an unverified static formula.
3. **No Biological or Operational Verification:** The valuation formula does not verify whether subsequent watering, harvesting, shed transport, or sale actions will actually take place, nor does it verify whether the terminal step (718) cuts off the harvest.

### Proposed Fix
1. Redesign `DownstreamAssetEvaluator` to ground opportunity cost in measurable terms:
   - Action displacement cost: Did the worker displace an idle `PASS`, a movement `MOVE`, or a chore `WATER/HARVEST`?
   - Replacement hire cost benchmark: `marginal_hire_cost = fib_hire_cost(hires_today) / 24.0`.
2. Fully separate `realized_delta` (observed in simulation rollout) from `projected_downstream_asset_value` in `EvaluationResult`.
3. Require explicit biological, operational, and terminal feasibility checks before assigning any projected value:
   $$\text{RemainingSteps} = \text{FINAL\_STEP} - (s_{\text{plant}} + \text{growth\_steps}) \ge 0$$
   If the crop cannot be harvested before game step 718, projected value is strictly $0.0$.

---

## 4. Confirmation of Blocker 3: Spatial Desynchronization in Open-Loop Continuation

### Current Code Behavior
In [`aec/counterfactual/simulator.py:318-328`](file:///c:/Users/Sundareswaran/Kagriculture/aec/counterfactual/simulator.py#L318-L328):
```python
# Baseline Rollout
baseline_rollout = simulate_rollout(
    econ_state=econ_state,
    initial_action=baseline_action,
    horizon=horizon,
    opp_model=opp_model,
    continuation_actions=continuation_trajectory,
)

# Candidate Rollout
cand_action = candidate_patch.apply(baseline_action)
candidate_rollout = simulate_rollout(
    econ_state=econ_state,
    initial_action=cand_action,
    horizon=horizon,
    opp_model=opp_model,
    continuation_actions=continuation_trajectory,
)
```

### Why It Is Scientifically Material
`continuation_trajectory` is extracted from the frozen V3 route tape.
If `baseline_action` at step 0 was `["NORTH"]` (moving from (4, 4) to (4, 3)), but `candidate_patch` mutated step 0 to `["DIG"]` at (4, 4):
- Baseline worker is at (4, 3) at step 1.
- Candidate worker is at (4, 4) at step 1.
- Continuation action at step 1 is `["EAST"]`.
  - Baseline moves to (5, 3).
  - Candidate moves to (5, 4).
The candidate worker's position is permanently offset from the route tape's expectations. All subsequent tile commands (`PLANT`, `WATER`, `HARVEST`) will execute on the **wrong coordinates**, creating severe false-positive or false-negative simulation artifacts.

### Proposed Fix
Implement a deterministic spatial consistency guard in `simulate_rollout`:
1. Track worker position evolution for both baseline and candidate rollouts.
2. If a candidate patch mutates a movement action or changes a worker's position relative to the baseline rollout:
   - Detect coordinate divergence.
   - For any subsequent continuation action targeting a tile or assuming baseline coordinates, mark `spatial_consistency_ok = False`.
   - Truncate candidate continuation or fail closed (`ABSTAIN`), preventing execution of stale spatial commands.

---

## 5. Confirmation of Blocker 4: Toy Market Price Rule in Simulator

### Current Code Behavior
In [`aec/counterfactual/simulator.py:136-137, 169-170`](file:///c:/Users/Sundareswaran/Kagriculture/aec/counterfactual/simulator.py#L136-L137):
```python
# Own order execution
rollout.market_inv[item] = rollout.market_inv.get(item, 10000) + actual_sell
rollout.market_prices[item] = max(1, price - actual_sell // 2)
...
# Opponent order execution
rollout.market_inv[item] = rollout.market_inv.get(item, 10000) + qty
rollout.market_prices[item] = max(1, price - qty // 2)
...
# Hire order execution
hire_cost = 100.0
```

### Why It Is Scientifically Material
1. The rule `price - actual_sell // 2` is completely fabricated. In Kaggle Agriculture (`sim.hpp`, `config.py`), price dynamics are governed by non-linear saturation curves (`linear`, `sqrt`, `log`, `sq`) with parameter vector `(base, I0=10000, T, below_func, above_func)`.
2. Hardcoding `hire_cost = 100.0` contradicts the engine's Fibonacci hire curve.
3. Market evaluation against a toy pricing function can accept patches that are detrimental under real game economics, or reject patches that are advantageous.

### Proposed Fix
1. Replace toy pricing with the official `compute_market_price(item, inventory)` from [`config.py:73-87`](file:///c:/Users/Sundareswaran/Kagriculture/config.py#L73-L87).
2. Execute market orders with authentic unit-by-unit or order-by-order inventory updating matching `sim.hpp:551-620`.
3. Replace hardcoded hire cost with `fib_hire_cost(rollout.hires_today)`.

---

## 6. Pre-Fix Verification Summary Table

| Blocker | Code Location | Verified Current State | Target Fix State |
|---|---|---|---|
| **1. Frontload Test Commit** | `tests/aec/test_v1_1_activation.py:554` | Fails commit; asserts only patch generation | Causal fixture with rival dump asserting `decision == COMMIT` |
| **2. Labor Wage & Asset Value** | `aec/evaluation/asset_value.py:32,158` | $100/day assumed wage; 100% extrapolated crop revenue | Grounded Fibonacci hire replacement cost; strict separation of realized vs projected value; biological/terminal feasibility cutoff |
| **3. Spatial Desynchronization** | `aec/counterfactual/simulator.py:321` | Blindly executes baseline route tape on diverged coordinates | Detects coordinate drift; marks uncertified / truncates continuation |
| **4. Toy Pricing Model** | `aec/counterfactual/simulator.py:137,170` | `price - qty // 2` toy formula; hardcoded $100 hire | Official `compute_market_price()` from `config.py`; authentic inventory impact |

Pre-fix inspection is complete and confirmed. All changes are authorized to proceed.
