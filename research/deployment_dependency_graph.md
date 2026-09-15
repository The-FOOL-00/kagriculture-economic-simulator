# Championship Deployment Dependency Graph & Call Trace

**Document ID**: `research/deployment_dependency_graph.md`  
**Protocol**: Championship Deployment Phase 2 — Dependency Auditing  
**Target Candidates**: `candidates/v54_plus_shop.py` (V54++) & `candidates/v54_plus_residual.py` (V54++ Residual)  

---

## 1. Full Runtime Call Graph Architecture

The following graph diagrams the entire execution path from Kaggle observation input to final submitted action dictionary:

```
                                [Kaggle Observation & Config]
                                              │
                                              ▼
                                       agent(obs, config)
                                              │
                          ┌───────────────────┴───────────────────┐
                          │  1. Shop-State Controller (S2 Model)   │
                          │     _select_route(step, shops)        │
                          │     - Step 72: YARN_STORE -> "yarn"   │
                          │     - Step 144: YARN_STORE -> "yarn"  │
                          │     - Step 144: BAKERY+YARN -> "bakery"│
                          │     - Default: "backbone"             │
                          └───────────────────┬───────────────────┘
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    ▼                         ▼                         ▼
            _POLICY_BACKBONE            _POLICY_YARN             _POLICY_BAKERY
       (_v51_build_policy:           (_v51_build_policy:       (_v51_build_policy:
       _V56_BACKBONE_ROUTE,          _V56_YARN_ROUTE,          _V58_BAKERY_YARN_ROUTE,
       _CONFIG)                      _CONFIG)                  _CONFIG)
                    │                         │                         │
                    └─────────────────────────┼─────────────────────────┘
                                              ▼
                                     Raw Policy Action
                                              │
                        ┌─────────────────────┴─────────────────────┐
                        ▼                                           ▼
             [Overlay 1: Step 0–719]                     [Overlay 2: Step 0–719]
             Strawberry Seed Trim                        Hour-23 Shed Guard
             _v60_seed_trim(obs, action)                 _v60_shed_guard(obs, action, cap)
                        │                                           │
                        └─────────────────────┬─────────────────────┘
                                              ▼
                                 [Overlay 3: Step 713–716]
                                 Loaded Unit Home Recall
                                 _route_loaded_units(obs, action, step)
                                              │
                                              ▼
                                 [Overlay 4: Step 717–718]
                                 Terminal Convergence
                                 _TERMINAL_UNITS(obs, action, step)
                                              │
                                              ▼
                                   [Overlay 5: Step 718]
                                   Terminal Liquidation
                                   _TERMINAL_MARKET(obs, action, rule="collision")
                                              │
                                              ▼
                                    [Final Action Dict]
```

---

## 2. Comprehensive Dependency Inventory

| Module / Component | Origin File | Embedded Artifacts / Internal Submodules | Exact Symbols Required at Runtime |
| :--- | :--- | :--- | :--- |
| **V51 Base Hybrid Engine** | `candidate_v62_composite_bakery_yarn.py` | `_V51_BASE_SOURCE` (compressed b85 zlib blob) | `_v51_build_policy` (aliased from `v50.hybrid.build_route_value_hybrid`), `_V51ResidualConfig` (aliased from `v49.residual_controller.ResidualConfig`), `_v51_safe_action` |
| **Residual Controller Engine (v49)** | `_V51_BASE_SOURCE` -> `v49.residual_controller` | Market Preemption & Liquidity Engine | `ResidualConfig`, `terminal_market`, `monetizable_terminal_units`, `_move_toward`, `_shed_access`, `SELLABLE` |
| **V62 Route Definitions** | `candidate_v62_composite_bakery_yarn.py` | Static 719-step offline proposal tapes | `_V56_BACKBONE_ROUTE` (719 turns), `_V56_YARN_ROUTE` (719 turns), `_V58_BAKERY_YARN_ROUTE` (719 turns) |
| **V62 Configuration Base** | `candidate_v62_composite_bakery_yarn.py` | Baseline parameter object | `_V54_CONFIG` (`ResidualConfig` instance) |
| **V62 Tactical Overlays** | `candidate_v62_composite_bakery_yarn.py` | Observation sanitizers and guards | `_v60_seed_trim`, `_v60_shed_guard`, `_v56_visible_configuration` |
| **V66 Terminal Overlays** | `candidate_v66_meta_closed_loop.py` | Endgame realization algorithms | `_route_loaded_units`, `_TERMINAL_UNITS`, `_TERMINAL_MARKET` |
| **Shop State Controller** | `candidates/v54_plus_shop.py` | Pure public observation S2 branch gate | `_SHOP_STATE`, `_select_route(step, shops)` |

---

## 3. Provenance of Inlined Submodules

1. **Why `_V51_BASE_SOURCE` is self-contained**:
   - `candidate_v62_composite_bakery_yarn.py` already contains the full, standalone `_V51_BASE_SOURCE` b85/zlib string (lines 15–1785).
   - When evaluated, it defines and exports the exact `v49` and `v50` namespaces required by `_v51_build_policy`.
2. **Why `external_repos/lixingtao123-Kaggriculture` is redundant**:
   - The policy builder `mod_v54._v51_build_policy` called in `candidates/v54_plus_shop.py` is identical to `mod_v62._v51_build_policy`. Both load the exact same `_V51_BASE_SOURCE`.
3. **Why `external_repos/kaggriculture-v66-agent/candidate_v66_meta_closed_loop.py` is easily inlined**:
   - `candidate_v66_meta_closed_loop.py` exports `_route_loaded_units`, `_TERMINAL_UNITS`, and `_TERMINAL_MARKET`.
   - `_TERMINAL_UNITS` and `_TERMINAL_MARKET` are direct functions from `v49.residual_controller` (already inside `_V51_BASE_SOURCE`).
   - `_route_loaded_units` is a 40-line Python helper that uses `_SHED_ACCESS`, `_MOVE_TOWARD`, and `_SELLABLE`.

---

## 4. Compilation Target Specification

To make both candidates 100% standalone, zero-dependency, and Kaggle-safe:
- The compiled files will contain `_V51_BASE_SOURCE` directly.
- The compiled files will define `_V56_BACKBONE_ROUTE`, `_V56_YARN_ROUTE`, `_V58_BAKERY_YARN_ROUTE`, `_v60_seed_trim`, `_v60_shed_guard`, `_v56_visible_configuration`.
- The compiled files will define `_route_loaded_units`, `_TERMINAL_UNITS`, `_TERMINAL_MARKET`.
- The compiled files will define `_select_route` and `agent(obs, configuration)`.
- **Zero** `__file__`, **zero** `importlib.util`, **zero** `os.path.join(BASE_DIR, ...)`, **zero** external file reads.
