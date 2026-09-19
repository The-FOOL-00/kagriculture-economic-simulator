# PHASE 015: FUNCTIONAL VALIDATION REPORT
## Comprehensive Synthetic Battery for Asset-Holding Valuation Trigger & Autonomous Tranche Synthesizer

**Status**: 40/40 Functional Scenarios Passed + 5/5 Counterfactual Regression Cases Passed  
**Date**: September 2026  
**Execution Environment**: Python 3.14, Pytest 9.0.3, Clean Workspace  

---

### Executive Summary

In accordance with Phase 015 specifications, we constructed and executed an adversarial synthetic functional matrix comprising 40 distinct scenarios covering the two upstream architectural primitives:
1. **Capability A: Asset-Holding Valuation Trigger** (Scenarios 01–20)
2. **Capability B: Autonomous Tranche Order Synthesizer** (Scenarios 21–40)
3. **Exact Counterfactual Regression & Negative Controls** (Cases 41–45)

All 45 test cases executed deterministically with zero failures (`45 passed in 0.28s`), verifying that:
- Persistent economic opportunities are detected without relying on differential state deltas ($\Delta \text{cash} = 0, \Delta \text{shed} = 0$).
- Valid sequential market orders are autonomously synthesized when the baseline market queue is completely empty (`market == []`).
- Hard physical, feed, and liquidity constraints are enforced upstream prior to candidate generation.
- Exact counterfactual forward simulation approves genuine economic gains while negative controls (feed starvation, price depression, order duplication) are rejected or abstained from.

---

### Part 1: Asset-Holding Valuation Trigger (Scenarios 01–20)

| Scenario ID | Test Name | Scenario Description | Expected Trigger Behavior | Result |
| :--- | :--- | :--- | :--- | :--- |
| **01** | `test_scenario_01_favorable_price_trigger` | High Strawberry inventory (40 units) at favorable price ($150 vs $120 base). | Emits `E13` event, classifies as `FAVORABLE_MARKET_HOLDING_STATE`, tags `SELL_NOW`. | **PASS** |
| **02** | `test_scenario_02_unfavorable_price_abstain` | Strawberry inventory (20 units) at depressed price ($80 vs $120 base, ratio 0.67). | Valuation trigger abstains (`None`), preventing low-price liquidation. | **PASS** |
| **03** | `test_scenario_03_price_rising_realization_option` | Strawberry at $130 with positive price momentum (+5/turn). | Detects opportunity but tags realization option as `SELL_LATER` / `KEEP`. | **PASS** |
| **04** | `test_scenario_04_market_saturation_risk` | 50 units held where current market depth is only 10 units. | Classifies opportunity as `MARKET_SATURATION_RISK`, tags `SELL_PARTIAL`. | **PASS** |
| **05** | `test_scenario_05_persistent_state_deduplication` | Static state held over consecutive turns without price or inventory change. | Fires on step 200; deduplicates and abstains on step 201 (`PENDING`). | **PASS** |
| **06** | `test_scenario_06_terminal_holding_risk` | Turn 345 (within 15 turns of final horizon 360) with 15 Strawberries in shed. | Classifies as `TERMINAL_HOLDING_RISK`, tags realization option as `TERMINAL_LIQUIDATE`. | **PASS** |
| **07** | `test_scenario_07_liquidity_holding_conflict` | Cash ($20) below daily wage buffer ($40), 15 Strawberries held at $110. | Classifies as `LIQUIDITY_HOLDING_CONFLICT`, tags `SELL_NOW` to unlock working capital. | **PASS** |
| **08** | `test_scenario_08_hard_feed_dependency_reservation` | 15 Wheat in shed, herd of 2 cows requiring 3 wheat/day buffer (6 reserved). | Uncommitted quantity strictly computed as $15 - 6 = 9$ units. | **PASS** |
| **09** | `test_scenario_09_feed_reservation_exhaustion_abstain` | 6 Wheat in shed with herd of 2 cows requiring 6 wheat reserve. | Uncommitted quantity is 0; trigger returns `None` (abstains). | **PASS** |
| **10** | `test_scenario_10_opponent_pressure_trigger` | Observed rival worker carrying 10 Strawberries towards town market. | Tags opportunity with `OPPONENT_PRESSURE` risk indicator. | **PASS** |
| **11** | `test_scenario_11_dependency_coupled_holding_congestion` | Shed inventory at 48/50 capacity with crops ready to harvest in field. | Classifies as `DEPENDENCY_COUPLED_HOLDING`, tags `SELL_NOW` to relieve shed lock. | **PASS** |
| **12** | `test_scenario_12_multi_product_portfolio_evaluation` | Farm holds Melon, Strawberry, and Carrot simultaneously. | Evaluates all 3 products; ranks by expected realizable revenue. | **PASS** |
| **13** | `test_scenario_13_worker_cargo_trigger_when_shed_empty` | Shed is empty (0 units), but worker cargo holds 10 Strawberries. | Correctly aggregates worker backpack inventory into asset valuation. | **PASS** |
| **14** | `test_scenario_14_baseline_already_selling_defers` | Baseline action already contains `["SELL", "STRAWBERRY", 10]`. | Detects baseline market coverage and abstains (`BASELINE_ALREADY_SELLING`). | **PASS** |
| **15** | `test_scenario_15_empty_inventory_returns_none` | Shed and workers have 0 units of commodity. | Feature extraction detects 0 quantity; returns `None`. | **PASS** |
| **16** | `test_scenario_16_insufficient_volume_abstains` | 1 unit of Strawberry held ($q < q_{\text{min}} = 2$). | Abstains due to sub-minimal volume. | **PASS** |
| **17** | `test_scenario_17_fingerprint_reset_on_price_shift` | Price shifts from $125 to $155 between turns. | Fingerprint changes from `price_band=1.0` to `1.2`; deduplication resets. | **PASS** |
| **18** | `test_scenario_18_terminal_phase_shift_resets_fingerprint` | Step advances from 330 (`terminal_phase=0`) to 345 (`terminal_phase=1`). | Structural fingerprint changes; enables terminal opportunity emission. | **PASS** |
| **19** | `test_scenario_19_static_turn_350_emits_event` | Turn 350, zero state deltas ($\Delta \text{cash} = 0, \Delta \text{shed} = 0$). | Deterministically emits `EventType.E13_ASSET_HOLDING_STATE`. | **PASS** |
| **20** | `test_scenario_20_opportunity_metadata_completeness` | Opportunity emitted by analyzer across full state representation. | Verifies all required fields: fingerprint, uncommitted qty, options, estimated revenue. | **PASS** |

---

### Part 2: Autonomous Tranche Order Synthesizer (Scenarios 21–40)

| Scenario ID | Test Name | Scenario Description | Expected Synthesizer Behavior | Result |
| :--- | :--- | :--- | :--- | :--- |
| **21** | `test_scenario_21_synthesis_from_empty_market_queue` | Baseline market queue is empty `[]`. | Synthesizes valid candidate `CoupledPatch` containing market SELL order. | **PASS** |
| **22** | `test_scenario_22_minimal_tranche_anchor` | Synthesizing anchors for 15 units held. | Emits candidate with $q_{\text{min}} = 2$ units. | **PASS** |
| **23** | `test_scenario_23_depth_compatible_tranche` | 30 units held where current market depth is 10. | Emits candidate with $q_{\text{depth}} = 10$ units. | **PASS** |
| **24** | `test_scenario_24_full_liquidation_anchor` | 8 units held in favorable market. | Emits candidate with $q_{\text{full}} = 8$ units. | **PASS** |
| **25** | `test_scenario_25_storage_clearing_anchor` | Shed at 48/50 capacity (utilization 96%). | Computes storage-clearing tranche of $q_{\text{storage}} = 8$ units. | **PASS** |
| **26** | `test_scenario_26_liquidity_clearing_anchor` | Cash deficit of $200 at commodity price $50. | Computes liquidity-clearing tranche of $q_{\text{liq}} = 4$ units. | **PASS** |
| **27** | `test_scenario_27_terminal_liquidation_anchor` | Turn 345 with 12 units held. | Computes terminal liquidation tranche of $q_{\text{term}} = 10$ units. | **PASS** |
| **28** | `test_scenario_28_multi_order_partitioning` | Tranche quantity of 25 units. | Partitions into atomic orders: `[10, 10, 5]` respecting Kaggle max 10/order. | **PASS** |
| **29** | `test_scenario_29_order_limit_ceiling` | 8 baseline buy orders already in queue + 40 units synthesized. | Clamps total orders to engine ceiling of $\le 10$ market operations. | **PASS** |
| **30** | `test_scenario_30_sequential_sell_before_buy` | Baseline has `BUY_SEED` and `BUY_PRODUCT` orders. | Synthesizes SELL order *prepended* before BUY orders to unlock cash. | **PASS** |
| **31** | `test_scenario_31_preserves_existing_sells` | Baseline already selling Carrot; Strawberry tranche synthesized. | Preserves Carrot sale and appends Strawberry sale without interference. | **PASS** |
| **32** | `test_scenario_32_unadmissible_product_rejection` | Candidate requested for non-sellable item (e.g. `STRAWBERRY_SEED`). | Realizability filter strictly rejects non-commodity asset. | **PASS** |
| **33** | `test_scenario_33_zero_inventory_rejection` | Candidate requested for commodity with 0 uncommitted inventory. | Realizability filter returns empty candidate list. | **PASS** |
| **34** | `test_scenario_34_livestock_wheat_reservation_enforced` | 15 Wheat in shed with 2 animals (6 reserved). | Synthesizer clamps candidate quantities strictly to $\le 9$ units. | **PASS** |
| **35** | `test_scenario_35_partial_wheat_realizability` | 20 Wheat in shed with 2 animals (6 reserved). | Synthesizer successfully emits tranches for the uncommitted 14 units. | **PASS** |
| **36** | `test_scenario_36_causal_attribution_logging` | Baseline emitted `farmer: ["MOVE", "EAST"]`, `market: []`. | Logs `why_v3_did_not_do_this: "V3_WORKER_TRAVELING..."`. | **PASS** |
| **37** | `test_scenario_37_adaptive_horizon_selection` | Evaluates horizon for standard, storage, liquidity, and terminal classes. | Maps appropriately to 6, 12, 12, and 36 rollout turns. | **PASS** |
| **38** | `test_scenario_38_quantity_clamping_to_uncommitted` | Storage anchor suggests 15 units, but only 7 units are held. | Clamps tranche quantity strictly to 7 units. | **PASS** |
| **39** | `test_scenario_39_deduplication_of_overlapping_anchors` | Anchors $q_{\text{min}}=2, q_{\text{depth}}=2, q_{\text{liq}}=2$ converge on same integer. | Deduplicates redundant candidate quantities to unique structural tranches. | **PASS** |
| **40** | `test_scenario_40_structural_fingerprint_in_patch_metadata` | Patch compiled and passed to downstream funnel. | Carries `structural_fingerprint` in `patch.dependency_info` for feedback loop. | **PASS** |

---

### Part 3: Exact Counterfactual Evaluation & Negative Controls (Cases 41–45)

| Case ID | Test Name | Invariant Under Test | Simulated Behavior & Verdict | Result |
| :--- | :--- | :--- | :--- | :--- |
| **41** | `test_autonomous_tranche_positive_counterfactual_trajectory` | End-to-end positive trajectory from empty baseline queue. | Counterfactual forward rollout shows $\Delta \text{money} > 0, \Delta \text{terminal\_margin} > 0$; WinModel approves; Safety passes; patch commits. | **PASS** |
| **42** | `test_negative_control_feed_starvation_rejected_by_counterfactual` | Counterfactual rejection of feed-violating candidate. | Rollout detects escaped livestock and unfed days; `fidelity = FAILED`; `SafetyChecker` rejects candidate. | **PASS** |
| **43** | `test_negative_control_depressed_price_abstains` | Valuation preservation under collapsed market price ($50 vs $120). | Trigger abstains upstream; baseline executes without asset dumping. | **PASS** |
| **44** | `test_negative_control_baseline_already_satisfies_optimal_sale` | Elimination of candidate spam when baseline is already selling. | Synthesizer detects baseline order and abstains; existing order preserved. | **PASS** |
| **45** | `test_sequential_market_order_lockstep` | Sequential market clearing execution order. | SELL order executed before BUY order; proceeds from sale provide solvency for purchase. | **PASS** |

---

### Verification Summary

```text
============================= test session starts =============================
platform win32 -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: C:\Users\Sundareswaran\Kagriculture
collected 45 items

tests/aec/test_phase015_functional_matrix.py ........................................ [ 88%]
tests/aec/test_phase015_counterfactual.py .....                                       [100%]

============================= 45 passed in 0.28s ==============================
```

All non-negotiable functional requirements for Phase 015 synthetic validation are met.
