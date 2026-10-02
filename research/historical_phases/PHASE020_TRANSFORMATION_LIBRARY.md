# PHASE020 — BOUNDED DIAGNOSTIC TRANSFORMATION LIBRARY (§10, §11, §12, §13)

**Phase**: PHASE020  
**Title**: Prospective Headroom Reorientation & New Opportunity Family Discovery  
**Date**: 2026-09-20  
**Module**: `aec/opportunities/diagnostic_transformations.py`  
**Test Suite**: `tests/aec/test_phase020_transformations.py` (4/4 passed)

---

## 1. Overview & Purpose

Phase 020 shifts from ad-hoc mechanism construction to a rigorous diagnostic transformation library. Rather than attempting to patch or rescue the quarantined Autonomous Tranche Order Synthesizer, this library formalizes 12 bounded, interpretable transformation primitives across 9 orthogonal opportunity families.

Every diagnostic transformation is designed to:
1. Probe whether actionable economic headroom exists under Phase 016 dynamic V3 continuation.
2. Maintain strict safety, feasibility, and CoupledPatch invariants.
3. Completely isolate and tag any early inventory sales as `TRANCHE_RELATED` (§11).

---

## 2. The 12 Bounded Diagnostic Primitives (§12)

| Primitive | Family | Description | Action Mutation |
| :--- | :--- | :--- | :--- |
| `SHIFT_ACTION_EARLIER` | Market timing | Advance scheduled non-produce purchase (feed/seed) when cash is available | Add BUY order from continuation into current market |
| `SHIFT_ACTION_LATER` | Market timing | Postpone non-urgent market order to avoid unfavorable clearing | Remove or defer market order |
| `SWAP_ACTION_ORDER` | Market timing | Reorder intra-turn market orders (Group A sells before Group B buys) | Permute `action["market"]` list |
| `REMOVE_REDUNDANT_ACTION` | Worker allocation | Replace redundant passes, duplicate till, or wasteful movement | Prune no-op / replace with productive task |
| `REASSIGN_WORKER` | Worker allocation | Reallocate target tile work from farmer to co-located/closer farmhand | Mutate worker task assignments |
| `REORDER_WORK` | Route/spatial | Reorder sequential tasks in worker route to minimize travel distance | Permute multi-step route queue |
| `ALTER_ROUTE` | Route/spatial | Detour worker around obstacles, congestion, or mutual tile collision | Cardinal step substitution |
| `ALTER_PRODUCTION_TIMING`| Production timing | Advance or synchronize planting on prepared tilled soil | Replace PASS/MOVE with PLANT on valid plot |
| `ALTER_MARKET_TIMING` | Market timing | Orthogonal price elasticity or volume adjustments (non-tranche) | Adjust order quantities on non-produce |
| `PRESERVE_RESOURCE` | Liquidity/capital | Defer discretionary capex (land/structures) when working capital buffer < $2k | Suppress discretionary capex orders |
| `ALLOCATE_RESOURCE_DIFFERENTLY` | Resource conversion | Target high-margin crop planting or fertilizer allocation | Mutate seed/fertilizer distribution |
| `COORDINATE_WORKERS` | Multi-worker | Parallelize simultaneous harvest or synchronized till-and-plant | Multi-worker simultaneous task execution |

---

## 3. Strict Non-Tranche Quarantine Protocol (§11)

> [!IMPORTANT]
> **Definitive Rule (§11)**: Any candidate transformation whose core action is *"sell currently held produce earlier"* must be explicitly marked:
> ```python
> candidate.is_tranche_related = True
> ```
> and **EXCLUDED** from the primary Phase 020 search ranking.

This guarantees that Phase 020 does NOT rediscover Phase 015 under a different disguise. Any tranche probe generated during discovery is evaluated solely as a forensic control to confirm the continued validity of the quarantine.

---

## 4. Safety & Invariant Verification (§13)

Every transformation emitted by `DiagnosticTransformationGenerator` satisfies:
1. **Legality**: All moves are within grid boundaries ($0 \le x < 10, 0 \le y < 10$) and use valid move vectors (`"NORTH"`, `"SOUTH"`, `"EAST"`, `"WEST"`, `"PASS"`).
2. **Worker Feasibility**: Only existing workers are mutated; farmer and farmhands obey role constraints.
3. **Resource Feasibility**: Purchases verify cash solvency; planting verifies seed availability or liquidity.
4. **Feed Security**: No transformation starves livestock or violates the wheat safety buffer.
5. **CoupledPatch Semantics**: All candidates wrap into valid `CoupledPatch` instances compatible with the AEC execution pipeline.

---

## 5. Two-Stage Discovery Architecture (§14)

```text
Turn State (econ_state, baseline_action)
                ↓
    Diagnostic Candidate Generation
                ↓
    [Stage 1: Cheap Local Probe]
    O(1) wealth/cash/labor heuristic signal
                ↓
    [Stage 2: Phase 016 Exact Evaluator]
    - Macro regime boundary check (MacroRegimeTransitionDetector)
    - Dynamic V3 continuation if escalated
    - Exact terminal margin delta calculation
    - State isolation & restoration
                ↓
    Survival Classification (H0..H5)
```
