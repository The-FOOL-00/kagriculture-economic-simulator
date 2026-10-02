# Forensic Analysis: Kaito Fukami — 40/40 Early Floor | 39/46 Top-10 | v48 Fast Routes

**Source:** Kaggle Notebook / Model Submission `kaitofukami/40-40-early-floor-39-46-top-10-v48-fast-routes`  
**Author:** Kaito Fukami  
**Date:** September 2026  
**Reported Metric:** 3009.0 (Public Leaderboard Snapshot Peak)  
**Corpus Path:** `research/v47/elite_corpus/agents/kaitofukami_v48_3009/main.py`  
**License:** Apache-2.0 / MIT  

---

## 1. Modular Architecture of v48 (3009.0)

Kaito Fukami's `v48` represents the culmination of his route-memory lineage, packaging 12 internal Python modules into an encrypted Base85/Zlib payload that dynamically instantiates at runtime:

```python
_V48_MODULE_ORDER = [
    'scripts.v21_route_memory_search',
    'v19_terminal',
    'scripts.v19_terminal',
    'scripts.v22_market_impact',
    'scripts.v22_weed_repair',
    'v23.state_encoder',
    'v23.simulator',
    'v23.policy_library',
    'v23.planner',
    'v24.market_maker',
    'v44.gold_floor',
    'v48.fast_route_router'
]
```

### Module Roles:
1. `scripts.v22_weed_repair`: Autonomous per-unit state machine for clearing weed obstacles on planned build/plant coordinates.
2. `scripts.v21_route_memory_search`: Replay tape accessor and coordinate alignment.
3. `v23.planner`: Integration hub combining open-loop route replay with feedback decorators (`wrap_weed_repair` and `reorder_sell_slots`).
4. `v23.policy_library`: Market order reordering based on rival stock exposure and demand recovery times.
5. `v48.fast_route_router`: Observable event router selecting between 6 fast mono-crop / animal routes at steps 88/120.

---

## 2. Integration of Blocked-Action Repair in `v23.planner`

In `v48`, `scripts.v22_weed_repair` is not an optional add-on; it forms the foundation of the unit command pipeline:

```python
@dataclass(frozen=True)
class PlannerConfig:
    weed_replay_steps: int = 8
    rebalance_demand_alpha: float = 0.25

def build_sparse_planner(actions, config: PlannerConfig = PlannerConfig()):
    base = wrap_weed_repair(
        replay_policy(copy.deepcopy(actions)),
        copy.deepcopy(actions),
        replay_steps=config.weed_replay_steps,
    )
    ...
    def agent(obs, configuration=None):
        ...
        action = base(obs)
        result = reorder_sell_slots(obs, action, configuration, demand_alpha=alpha)
        return result
    return agent
```

### Architectural Pipeline:
1. **Raw Action Source:** `actions` (a pre-compiled list of 720 dictionary actions).
2. **Layer 1 (Weed Repair):** Wrapped by `wrap_weed_repair`. Intercepts `PLANT` and `BUILD_PASTURE` on `WEED`, replaces them with `DIG`, and offsets subsequent actions for the affected unit for 8 turns.
3. **Layer 2 (Market Optimization):** `reorder_sell_slots` takes the resulting physical action and reorders the `market` list to prioritize items with impending price collapse.

---

## 3. Why v48 Diverged from the 2945 Farm

In V47 benchmarking, we observed a stark performance contrast between `kaitofukami_v48_3009` and `thomastschinkel_2945`:
- **V44 vs 3009:** V44 defeated 3009 **100.0% of the time** (128W / 0L), winning by a mean margin of **+$25,235.38**.
- **V44 vs 2945:** 2945 defeated V44 **95.31% of the time** (122W / 6L), winning by **+$3,582.77**.
- **Head-to-head 2945 vs 3009:** 2945 crushed 3009 **100.0% of the time** (32W / 0L), winning by **+$28,062.88**.

### Causal Reason:
- 3009's high public score (3009.0) was achieved by exploiting uncompetitive public bots with fast mono-crop routes (`yarn_fast`, `farm_fast`). Against disciplined capital players like V44 and 2945, these routes suffer catastrophic price collapse.
- In contrast, 2945 uses Hayashi's `EXP240`/`V39` shop router with superior physical animal scaling and market front-running (`ORDERPRI2`).
- **However:** The failure of 3009's macro routing does **NOT** invalidate its micro weed repair component. The micro weed repair is independent of routing and operates strictly at the worker execution level.

---

## 4. Key Takeaways for V51 Implementation

1. **Exact Logic Extracted:** We have extracted the exact, full source of `scripts_v22_weed_repair.py` from `v48_3009`.
2. **Deterministic Parity:** When no weeds are encountered, `wrap_weed_repair` returns bit-identical actions to the underlying policy.
3. **Investigation Path:** We must test whether V49's 2945 chassis encounters weeds on planned `PLANT` or `BUILD_PASTURE` tiles, and whether repairing them provides measurable value.
