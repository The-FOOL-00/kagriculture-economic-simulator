# AEC Phase 002C: Targeted Architectural Remediation Report
**Mechanisms Remediated:** `RESOURCE_CONVERSION` & `EMERGENCY_FEED_PURCHASE`  
**Phase:** Phase 002C Targeted Architectural Remediation  
**Status:** **QUARANTINED** (Strictly Non-Prospective)  
**Lead Architect & Remediation Engineer:** Principal AEC Architect  
**Date:** 2026-09-17  

---

## 1. Executive Summary

Phase 002B deterministic historical micro-validation uncovered two real architectural defects:
1. **Defect #1:** `RESOURCE_CONVERSION` was architecturally modeled in the DAG but not operationally executable, generating metadata without concrete physical actions (`worker_mutations = {}`, `market_mutations = None`), resulting in 0 commits across 101,551 evaluated candidates.
2. **Defect #2:** `EMERGENCY_FEED_PURCHASE` suffered from terminal blindness, placing a wheat buy order at step 697 under active `E8_TERMINAL_TRANSITION` that drained cash without generating harvest yields, collapsing Seed 50004 margin from `+$1,280` to `-$2,108` (`-$3,388` delta).

Phase 002C successfully designed and implemented principled architectural remediations for both defects.

---

## 2. Remediation of Defect #1: Physical Conversion Compiler

### 2.1 Root Cause Analysis
In [`aec/patches/generator.py`](file:///c:/Users/Sundareswaran/Kagriculture/aec/patches/generator.py), the patch synthesis branch for `RESOURCE_CONVERSION` attached `conversion_metadata` but failed to synthesize discrete actions for the agent. When submitted to the counterfactual simulator, `patch.apply(baseline_action)` produced an action identical to baseline, returning `delta_money = 0.0`. Consequently, `WinModel` correctly evaluated the patch as non-superior, causing 100% of candidates to fail closed with `NO_CANDIDATE_CERTIFIED_SUPERIOR`.

### 2.2 Principled Architectural Remediation
Rather than bypassing simulation or forcing commits based on symbolic arithmetic, we built a physical action compiler:

1. **`ConversionExecutionPlan` Data Model ([`aec/resource/conversions.py`](file:///c:/Users/Sundareswaran/Kagriculture/aec/resource/conversions.py)):**
   - Introduced formal execution representation:
     ```python
     @dataclass
     class ConversionExecutionPlan:
         plan_id: str
         conversion_id: str
         target_commodity: str
         required_inputs: Dict[str, int]
         produced_outputs: Dict[str, int]
         prerequisites: List[str]
         worker_id: Optional[int]
         target_location: Optional[Tuple[int, int]]
         market_actions: List[List[Any]]
         worker_actions: List[str]
         reconnect_required: bool
         start_step: int
         estimated_duration: int
         net_value_est: float
         is_executable: bool
         infeasibility_reason: Optional[str]
     ```
2. **Exact Action Synthesis (`synthesize_execution_plan`):**
   - Maps conversion recipes to physical game operations from C++ `sim.hpp`:
     - Input acquisition: Emits concrete market buy orders (`["BUY_PRODUCT", "WHEAT", 1]`, `["BUY_SEED", "CARROT", 1]`).
     - Feed delivery: Worker acquires wheat from shed (`["PICKUP", "WHEAT", 1]`) and feeds animal (`["FEED"]`).
     - Worker routing: If worker is distant from animal or shed, sets `reconnect_required = True` and computes directional moves.
3. **Route Reconnection Integration:**
   - In [`aec/patches/generator.py`](file:///c:/Users/Sundareswaran/Kagriculture/aec/patches/generator.py), when `plan.reconnect_required` is True, invokes `AEC-RECONNECT` (`ReconnectionEngine.reconnect`) with a formal `ReconnectRequest`.
   - If route recovery fails or creates spacetime conflicts: fails closed and abstains.
   - If route recovery succeeds: attaches `reconnect_result` and `spliced_continuation` to `CoupledPatch`.

---

## 3. Remediation of Defect #2: Terminal Feed Feasibility & Safety

### 3.1 Root Cause Analysis
At Step 697 (23 turns before final step 720), the feed security monitor observed `total_wheat < animals` and emitted an emergency buy order. Because `max(patch.expected_horizon, config.normal_horizon)` was $18$, the forward simulation evaluated steps $697 \to 715$, cutting off prior to step 718 (terminal liquidation) and step 720 (episode conclusion). Over those 18 steps, the simulation did not see the terminal cash penalty, and committed the purchase. In reality, on day 29, animals cannot refresh yields before step 718, and wheat bought sat uselessly in the shed, draining cash and pushing out terminal market orders.

### 3.2 Principled Architectural Remediation
We strictly rejected hardcoded step heuristics (`step >= 697` or `step >= 720 - X`) and implemented a temporal-causal feasibility engine:

1. **Terminal Feed Feasibility Engine ([`aec/opportunities/resource.py`](file:///c:/Users/Sundareswaran/Kagriculture/aec/opportunities/resource.py)):**
   - Formally models the complete physical chain:
     $$\text{PURCHASE} \to \text{ARRIVAL} \to \text{FEED} \to \text{DAY ROLLOVER} \to \text{HARVEST} \to \text{SHED DEPOSIT} \to \text{MARKET SELL}$$
   - Evaluates exact step constraints relative to engine action cutoff (Step 718):
     - Minimum physical delay for purchase + feed is 2 steps.
     - Final-day purchases are provably non-realizable: products refresh at step 720, after step 718 action cutoff.
     - Multi-day chains require at least `turns_to_day_end + 3` steps before step 718 to allow day rollover, harvest, and sale.
   - Starvation preservation: Unfed animals only escape if unfed across TWO consecutive day boundaries (`consecutive_dry >= 2`). If no escape occurs during the episode, and no harvest can be realized, the purchase is suppressed.
2. **Formal Safety Invariant (`terminal_purpose_consistency_check` in [`aec/safety/checks.py`](file:///c:/Users/Sundareswaran/Kagriculture/aec/safety/checks.py)):**
   - Added invariant `terminal_purpose_ok` to `SafetyChecker` and `SafetyCertificate`.
   - Verifies that emergency feed purchases preserve net terminal margin and possess realizable downstream purpose before step 718.
   - Fails closed if the purchase degrades terminal liquidity.
3. **Adaptive Horizon Terminal Escalation ([`aec/counterfactual/horizon.py`](file:///c:/Users/Sundareswaran/Kagriculture/aec/counterfactual/horizon.py)):**
   - When near terminal (`remaining <= 48`), escalates simulation horizon to `FULL` (`remaining` turns).
   - Simulates all the way through terminal liquidation (step 718) and episode end (step 720), preventing truncation artifacts.

---

## 4. Verification and Governance Conformance

- **Adversarial Test Suite:** 18 new tests implemented in [`tests/aec/test_resource_remediation_adversarial.py`](file:///c:/Users/Sundareswaran/Kagriculture/tests/aec/test_resource_remediation_adversarial.py) (18/18 passed).
- **Regression Suite:** 275/275 tests passed in 0.78s (`pytest tests/ -q`).
- **Holdout Partition Integrity:** Seeds `340050–340199` and `214200–214249` recorded 0 accesses.
- **Frozen V3 Chassis Integrity:** `submission_Vj_kc_v3.tar.gz` verified byte-identical (`845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`).
- **Quarantine Invariance:** Both mechanisms remain strictly quarantined in `aec/config.py`.
