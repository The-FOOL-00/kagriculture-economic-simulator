# PHASE 016: MACRO-AWARE LONG-HORIZON COUNTERFACTUAL SPECIFICATION

**Phase**: 016 — Long-Horizon Macro-Aware Counterfactual & Regime-Transition Safety Rescue  
**Status**: SPECIFICATION FROZEN  
**Target Subsystems**: `aec/counterfactual/`, `aec/integration/`, `aec/market/`  

---

## 1. Architectural Overview

The core objective of Phase 016 is to resolve the fundamental decision-theoretic gap exposed by Phase 015:
> *A local exact counterfactual ($H=18$) can correctly verify that an intervention is locally positive and safe, yet the action can destabilize the long-run trajectory because it induces a regime shift in the frozen adaptive continuation policy.*

To fix this without resorting to an intractable global $H=120$ on all candidates, Phase 016 introduces a **4-Tier Tiered Evaluation Architecture**:

```text
                     Candidate Action A'
                             │
                             ▼
                ┌─────────────────────────┐
                │ Tier 1: Local Exact CF  │
                │     (H_local = 6..18)   │
                └────────────┬────────────┘
                             │
                             ▼
                ┌─────────────────────────┐
                │ Tier 2: Macro Regime    │
                │     Boundary Probe      │
                └────────────┬────────────┘
                             │
             ┌───────────────┴───────────────┐
             │                               │
             ▼ [No Regime Risk]              ▼ [Regime Risk Detected]
    ┌─────────────────┐             ┌─────────────────────────┐
    │  Accept Local   │             │ Tier 3: Escalated Exact │
    │  Tier 1 Outcome │             │ Continuation with True  │
    └────────┬────────┘             │ Frozen V3 Continuation  │
             │                      │   (H_escalated = H_cap) │
             │                      └────────────┬────────────┘
             │                                   │
             │                                   ▼
             │                      ┌─────────────────────────┐
             │                      │ Tier 4: Regime-Stability│
             │                      │   Economic Validation   │
             │                      └────────────┬────────────┘
             │                                   │
             └───────────────┬───────────────────┘
                             │
                             ▼
                ┌─────────────────────────┐
                │ Hard Safety Certificate │
                └────────────┬────────────┘
                             │
                             ▼
                     Commit or Abstain
```

---

## 2. Component Specifications

### 2.1 Macro State Fingerprint (`MacroRegimeFingerprint`)
A compact, deterministic data structure characterizing the macro regime of a game state:
```python
@dataclass(frozen=True)
class MacroRegimeFingerprint:
    step: int
    day: int
    cash: float
    cash_bracket: int               # 0: <$500, 1: $500-2k, 2: $2k-8k, 3: $8k-12k, 4: >=$12k
    quadrants_count: int            # Number of unlocked quadrants (1..4)
    hands_count: int                # Number of hired hands
    has_animals: bool               # Any cows/sheep/geese in tiles/shed/hands
    animal_counts: Tuple[Tuple[str, int], ...]
    wheat_in_shed: int              # Critical for feeding obligations
    fertilizer_in_shed: int         # Critical for plant tending
    total_shed_units: int           # Shed capacity monitoring (0..100)
    unlocked_shops: Tuple[str, ...]
    next_block_step: int            # Next step % 72 == 0
    next_day_end_step: int          # Next step % 24 == 23
```

### 2.2 Macro Regime Transition Detector (`MacroRegimeTransitionDetector`)
Receives baseline state $S$ and candidate mutated state $S'$:
1. Computes fingerprints: $F(S)$ and $F(S')$.
2. Detects policy divergence risk:
   - **Cash Capex Boundary Risk**: Candidate crosses into bracket 3 ($\ge \$8\text{k}$) or bracket 4 ($\ge \$12\text{k}$) within proximity of Day 12 (`step 288`) or Day 18 (`step 432`).
   - **Block Boundary Shortfall Risk**: Candidate alters cash or inventory when `step % 72` is within 12 turns.
   - **Storage Guard Overflow Risk**: Candidate changes shed contents within 6 turns of Hour 23 (`step % 24 == 23`).
   - **Order Queue Truncation / Mutation Risk**: Candidate drops, displaces, or reorders atomic non-market orders (`HIRE`, `BUY_LAND`).
   - **Feed Deficit Risk**: Candidate alters wheat stock when farm holds livestock.
3. If risk detected, outputs:
   - `requires_escalation: bool = True`
   - `reason: str`
   - `regime_capture_horizon: int`: Smallest horizon that encompasses the transition and its immediate consequences.

### 2.3 Dynamic Frozen V3 Continuation Policy (`V3ContinuationPolicy`)
When Tier 3 is triggered:
- The evaluator snapshots the live V3 agent state.
- In forward rollout, at each step $t + \text{offset}$:
  - Construct a valid Kaggle `observation` dict from the forward rollout state.
  - Pass the observation to the cloned V3 agent closure.
  - V3 computes its true endogenous action $a'_{t+\text{offset}}$ in response to the mutated state $S'_{t+\text{offset}}$.
  - The forward simulator executes $a'_{t+\text{offset}}$, updating farm tiles, cash, shed, and worker positions.
- Guarantees:
  - Both baseline and candidate use the **exact same frozen V3 decision logic**.
  - All internal state mutations remain strictly sandboxed in the shadow rollout.
  - Zero state leaks to the live game agent.

### 2.4 Causal Attribution Decomposition
Every evaluated candidate records:
1. **Direct Intervention Effect**: Immediate $\Delta\text{cash}$, $\Delta\text{inventory}$ at turn $t$.
2. **Induced Macro Divergence Turn**: First step $t_{\text{div}}$ where candidate V3 action $\ne$ baseline V3 action.
3. **Induced Continuation Delta**: Total economic and labor divergence between candidate continuation and baseline continuation.
4. **Terminal Economic Effect**: Final net margin delta.

---

## 3. Governance and Scientific Control Invariants

1. **Frozen V3 Unchanged**: SHA-256 `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` remains byte-for-byte immutable.
2. **Phase 015 Quarantined**: Autonomous Tranche and Valuation Trigger remain quarantined from standard live configuration.
3. **Fail-Closed Safety**: Any candidate with desynchronization, solvency breach, or feed deficit fails closed immediately.
