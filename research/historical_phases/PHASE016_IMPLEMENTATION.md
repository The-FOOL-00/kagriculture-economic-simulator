# PHASE 016 — IMPLEMENTATION REPORT

**Author**: Antigravity Primary Implementation Agent  
**Date**: September 19, 2026  
**Status**: IMPLEMENTED & VERIFIED  
**V3 Chassis SHA256**: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` (Byte-for-byte unchanged)  

---

## 1. Overview and Architecture Motivation

Phase 015 identified a critical architectural limitation in the exact counterfactual simulator:
The simulator evaluated candidate economic transformations over a short local horizon ($H=18$) using static route continuation tapes. Because the continuation tape was static, the evaluator was completely blind to downstream policy regime bifurcations in the frozen V3 chassis. When a local candidate action altered farm state (injecting cash, mutating market order queues, or depleting feed reserves), it crossed hidden V3 macro thresholds (the Day 12 $10k Sheep capex gate, Day 18 $12k Tomato capex gate, 72-turn budget guard, and shed storage room guard). This triggered premature livestock purchases or dropped vital atomic orders (`HIRE`), diverting labor and crashing long-run farm economics tens to hundreds of turns later.

Phase 016 implements the **Macro-Aware Long-Horizon Counterfactual Safety Layer**, upgrading the AEC evaluator into a 4-tier causally adaptive evaluation engine:
1. **Tier 1 — Local Exact Counterfactual**: Invariant baseline simulation at local horizon ($H=18$) for rapid screening.
2. **Tier 2 — Macro-Regime Boundary Detection**: Pre-simulation probing of candidate state deltas ($\Delta\text{cash}$, $\Delta\text{shed}$, $\Delta\text{animals}$, atomic orders) to detect threshold crossings.
3. **Tier 3 — Long-Horizon Dynamic V3 Continuation**: Dynamic forward rollout of the true frozen V3 policy (`V3ContinuationPolicy`) with guaranteed state isolation (`snapshot_v3_state` / `restore_v3_state`) when macro boundaries are crossed.
4. **Tier 4 — Regime-Stability Decision**: Evaluates true terminal margin and strategic win score under the induced policy trajectory; rejects any candidate inducing negative macro divergence.

---

## 2. Detailed Files Added and Changed

### A. Files Added

1. **`aec/counterfactual/macro_detector.py`** (370 lines)
   - `MacroRegimeType`: Enumerates V3 macro regimes (`CASH_CAPEX_GATE`, `BUDGET_GUARD_BLOCK`, `DAY_END_ROOM_GUARD`, `ORDER_QUEUE_ALTERATION`, `LIVESTOCK_FEED_RISK`, `TERMINAL_TRANSITION`).
   - `MacroRegimeFingerprint`: Compact deterministic state fingerprint capturing cash brackets, quadrant counts, worker counts, livestock census, grain reserves, shed inventory, and macro cycle milestones.
   - `MacroBoundaryProbeResult`: Structured result reporting escalation requirement, regime type, causal rationale, recommended horizon, and earliest expected divergence step.
   - `MacroRegimeTransitionDetector`: Probes candidate transformations prior to expensive simulation. Detects cash gate crossings ($500, $600, $1k, $2k, $5k, $7.5k, $10k, $12k), atomic order drops, shed saturation near day ends, and feed security risks.

2. **`aec/counterfactual/v3_continuation.py`** (180 lines)
   - `snapshot_v3_state(agent_fn)`: Deep-copies all mutable internal dictionaries in the frozen V3 namespace (`_IMPL.chassis.players`, `_V219_STATES`, `_V231_STATES`, `_V233_STATES`, `TELEMETRY`, etc.) or direct chassis state.
   - `restore_v3_state(agent_fn, snap)`: Restores 100% bit-identical state across all internal V3 controllers, preventing shadow rollout mutations from leaking into the live game.
   - `build_simulated_observation(rollout, player)`: Reconstructs a full Kaggle-compliant observation dictionary from internal `ShadowRolloutState`.
   - `V3ContinuationPolicy`: Dynamic policy wrapper executing frozen V3 decisions on simulated observations during forward counterfactual rollouts.

3. **`tests/aec/test_phase016_macro_regime.py`** (330 lines)
   - Comprehensive synthetic regression suite validating Tests A through H (no boundary, boundary crossing, delayed consequence, false positive, terminal boundary, order alteration, determinism, and state isolation).

4. **`scripts/run_phase016_canonical_replay.py`** (185 lines)
   - Mirror match canonical replay harness on Seed 249276 comparing unrescued Phase 015 against Phase 016.

5. **`scripts/run_phase016_pilot.py`** (286 lines)
   - Fresh natural game pilot harness across seeds `249286..249295` (N=10 seeds, 20 mirror matches) with strict governance guards.

---

### B. Files Modified

1. **`aec/market/tranche_synthesizer.py`**
   - **Fix**: Updated `construct_sequential_market_orders()` so that non-BUY/SELL atomic orders (`HIRE`, `BUY_LAND`, `BUY_ANIMAL`) in the baseline order queue are strictly preserved in their original queue slots rather than dropped. This fixed the critical Seed 249276 Step 195 hand-loss bug.

2. **`aec/counterfactual/horizon.py`**
   - **Enhancement**: Extended `select_adaptive_horizon()` with optional `macro_probe_result: Optional[MacroBoundaryProbeResult]`. When the macro detector flags a regime crossing, the horizon causally expands to the recommended regime capture horizon ($H=36..120$) capped by remaining turns.

3. **`aec/counterfactual/simulator.py`**
   - **Enhancement**: Extended `SimulationOutcome` with `first_divergence_turn`, `macro_regime_type`, `macro_diverged`, `direct_intervention_delta_money`, and `macro_induced_delta_margin`.
   - Updated `simulate_rollout()` to dynamically query `v3_continuation_policy.step_action()` during forward rollout when `macro_escalated=True`, logging the exact step where candidate and baseline V3 actions diverge.

4. **`aec/integration/executor.py`**
   - **Integration**: Instantiated `self.macro_detector = MacroRegimeTransitionDetector()`.
   - Inside `act()`: Probes each candidate patch via `probe_candidate()`, escalates horizon if indicated, executes dynamic V3 simulation, records macro telemetry in `CandidateTelemetry` and `AECTelemetry`, and enforces lexicographic rejection of macro-inferior candidates.

---

## 3. Scientific Invariants and Verification

1. **Frozen V3 Integrity**:
   - Chassis tarball SHA256 verified: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`.
   - Zero lines of frozen V3 source code altered or monkey-patched.

2. **Zero State Leakage**:
   - `snapshot_v3_state` and `restore_v3_state` rigorously tested across multi-step mutating rollouts.
   - Guaranteed bit-identical state restoration confirmed by Test H.

3. **Generalization (No Special Cases)**:
   - Zero hardcoded seed checks (`seed == 249276`).
   - Zero commodity-specific blacklists (`crop == "WHEAT"`).
   - Rejections are 100% causal, derived from true frozen V3 dynamic continuation rollouts.
