# LIVE CALL GRAPH & DEAD CODE ANALYSIS

## 1. High-Level Comparison of Entrypoints

| Agent | Entrypoint | Outer Safety Wrapper | Outer Strategic Wrapper | Core Pipeline |
| :--- | :--- | :--- | :--- | :--- |
| **V49** | `agent` | None (Direct in `candidates/v49_meta_fusion/main.py`) | `_V49_E402_OVERLAY` $\to$ `_V47_V44_OVERLAY` | Raw 2945 Chassis + V48 Selective Overrides + Dairy / Harvest |
| **Vj_kc_v27** | `agent` | `_v27_safety_agent` (exception catch, market[:10]) | None (Calls `step1009_...`) | 70-layer wrapper stack $\to$ HybridOpening $\to$ 2945 Chassis |
| **Vj_kc_v24** | `agent` | `_v24_safety_agent` (exception catch, market[:10]) | `pet_any_demand_agent` (_CA_MARGIN = -30.0) | 70-layer wrapper stack $\to$ HybridOpening $\to$ 2945 Chassis |

---

## 2. Active Call Graph Execution Sequence (V24 / Final Synthesis)

When `agent(observation, configuration)` is invoked each turn:

```text
[1] _v24_safety_agent(observation, configuration)
    │  - Exception try/catch
    │  - Sanitizes output format, ensures farmer, hands, and caps market[:10]
    ▼
[2] pet_any_demand_agent(observation, configuration)
    │  - Checks observation: if 10 <= day <= 23 and 'PET_CAFE' in town['unlocked_shops']
    │  - Temporarily sets _CA_MARGIN = -30.0 (biases towards CARROT)
    ▼
[3] Multi-Pass Fixed-Sell Closures (step1009 down through step965)
    │  - Iterative fixed-point passes of _s793_reorder(observation, action)
    │  - Moves profitable SELL orders ahead of spend turns
    ▼
[4] Step961..948 Asset Permutation & Preemption Wrappers
    │  - step953_move_dayhigh_animal_sales_before_first_spend_agent
    │  - step952_merge_dayhigh_animal_sale_into_first_sameitem_agent
    │  - step951_move_tail_crop_sale_before_first_spend_agent
    │  - step948_dayhigh_nonconsumable_crop_sale_agent
    ▼
[5] Step846..811 Final Day Orbit & Care Salvage Wrappers
    │  - step846_step717_idle_center_fertilizer_agent
    │  - step837, step836, step834 fixed anchor orbit agents
    │  - step814_day28_care_to_fertilizer_after_harvest_agent
    │  - step811_day28_care_to_harvest_agent
    ▼
[6] Step759..752 Market Queue Alignment & Lead Sell
    │  - step758_modelpx_lead_sell_agent (front-runs rival queue)
    │  - step752_guarded_same_side_market_compact_agent
    ▼
[7] Step731 Seed Float Trim
    │  - Trims BUY_SEED WHEAT & CARROT to exact remaining route needs
    ▼
[8] Step720 Lockstep Sell-Block Optimizer (_v44y_reorder)
    ▼
[9] Herdsafe Forecast Agent
    ▼
[10] V9 / Metav4 Production Layers
    │  - RACEPX gate, RACE market reservation, COURIER, CARROT, HERD
    ▼
[11] Dmitrii Gluzdov Wheat Maturation & HybridOpening (_CL_PARENT, _ALT_PARENT)
    │  - Installs temporary wheat route modifications on turns 0..91
    │  - Hand 1 plants/waters turn 5-6; hand 2 waters turn 29; hand 0 harvests/waters turn 84-91
    ▼
[12] Chassis.act(observation, configuration)
    │  - Hand align, weed repair (inert), sell lead
    │  - room_guard: keeps shed <= 99 at hour 23
    │  - dead_stock: sells stock route will never use
    ▼
[13] Route Tape Lookup (_ROUTES[route_id][step])
```

---

## 3. Dead Code & Inactive Wrappers Fingerprint

The codebase contains numerous historical exploratory layers that were wrapped into the execution chain but never trigger in realistic game play. Our empirical instrumentation on 719-step simulation verified the following inactive wrappers:

| Wrapper / Function | Reported Metric | Observed Calls | Observed Firing | Status |
| :--- | :--- | :--- | :--- | :--- |
| `_S738_sale_advance_agent` | `_S738_REPORT['changed']` | 1,437 | **0** | INERT |
| `_S744_fertilizer_netting_agent` | `_S744_REPORT['changed']` | 1,437 | **0** | INERT |
| `_S747_fertilizer_buyfirst_netting` | `_S747_REPORT['changed']` | 1,437 | **0** | INERT |
| `_S809_debt_aware_sale_advance` | `_S809_REPORT['changed']` | 1,437 | **0** | INERT |
| `_S823_finalday_highquote_collect` | `_S823_REPORT['swaps']` | 1,437 | **0** | INERT |
| `_S840_final_residual_compact` | `_S840_REPORT['changed']` | 1,437 | **0** | INERT |
| `_S850_step714_twohop_salvage` | `_S850_REPORT['starts']` | 1,437 | **0** | INERT |
| `_S936_step603_fertilizer_netting` | `_S936_REPORT['changed']` | 1,437 | **0** | INERT |
| `_S950_merge_appended_crop_sale` | `_S950_REPORT['changed']` | 1,437 | **0** | INERT |
| `_S961_plus_multibuy_permutation` | `_S961_REPORT['changed']` | 1,437 | **0** | INERT |
| `_UPGRADE_STATS` | `_UPGRADE_STATS['accepted']` | 2 | **0** | INERT |
| `_V219_REPORT` (historical tomato) | `_V219_REPORT['plants']` | 0 | **0** | DEAD HISTORICAL |
| `_V231_REPORT` (historical cattle) | `_V231_REPORT['cattle']` | 0 | **0** | DEAD HISTORICAL |
| `print('HP_TELEMETRY', ...)` | Stdout print at step 718 | 1 | **1** | **PROHIBITED DEBUG HOOK (MUST REMOVE)** |

### Note on Multi-Pass Closure Chain:
Passes `step1003` through `step1009` are 6 identical sequential repetitions of `_s793_reorder`. Across 719 steps, they execute in <0.05ms combined without side-effects or regressions, serving as an idempotent fixed-point safeguard.
