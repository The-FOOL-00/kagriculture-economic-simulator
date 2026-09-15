# EXP-DEV-001 POSTMORTEM TIE AUDIT: THE 42-SEED INERTIA PHENOMENON

**Experiment Identifier**: `EXP-DEV-001`  
**Governing Treatment**: [`candidates/closed_loop_architecture/dev_001_dynamic_portfolio.py`](file:///c:/Users/Sundareswaran/Kagriculture/candidates/closed_loop_architecture/dev_001_dynamic_portfolio.py)  
**Baseline Control**: [`candidates/closed_loop_architecture/closed_loop_v2.py`](file:///c:/Users/Sundareswaran/Kagriculture/candidates/closed_loop_architecture/closed_loop_v2.py)  
**Investigation Script**: [`scratch/audit_all_50_seeds.py`](file:///c:/Users/Sundareswaran/Kagriculture/scratch/audit_all_50_seeds.py)  
**Auditor**: Antigravity Autonomous Pair Programmer  
**Date**: 2026-09-11  

---

## 1. The Core Empirical Finding

In the primary paired comparison against `ClosedLoopAgentV2`, candidate `dev_001_dynamic_portfolio` produced a paired margin of exactly:
$$\text{Margin}(s) = \$0.00 \quad \text{on 42 of 50 seeds (84.0%)}$$

A turn-by-turn action comparison between Candidate and `ClosedLoopAgentV2` was executed across all 50 seeds using bit-exact simulation in [`kagsim`](file:///c:/Users/Sundareswaran/Kagriculture/external_repos/kaggriculture-cppsim/sim/sim.hpp).

### Definitive Classification:
On all 42 tied seeds, the candidate treatment was:
> **Option 1: LITERALLY IDENTICAL TO V2.**

Across all 720 steps of both Match 0 and Match 1 for every single one of the 42 tied seeds:
- **Action Divergences**: **0 (Zero)**.
- **Farmer Actions**: 100% bit-exact match on every step.
- **Hand (Worker) Actions**: 100% bit-exact match on every step.
- **Market Orders**: 100% bit-exact match on every step.
- **Farm State & Cash**: 100% bit-exact match on every step.

The candidate did **not** perform different actions that accidentally balanced out economically; it emitted the exact identical action dictionary returned by `ClosedLoopAgentV2.act(obs)`.

---

## 2. Root-Cause Code Audit: Why Did 42 Seeds Fall Back to V2?

Inspection of [`dev_001_dynamic_portfolio.py`](file:///c:/Users/Sundareswaran/Kagriculture/candidates/closed_loop_architecture/dev_001_dynamic_portfolio.py) lines 61–109 reveals the structural mechanism that caused 84% of runs to be inert:

### 2.1 The Decision Hierarchy in `_determine_crop_mode`
```python
STRAWBERRY_SHOPS = {"SMOOTHIE_SHOP", "ICE_CREAM_SHOP", "BRUNCH_SPOT", "FARMERS_MARKET"}
CARROT_SHOPS = {"PET_CAFE"}
WHEAT_SHOPS = {"BAKERY"}
TOMATO_SHOPS = {"PIZZA_SHOP"}
YARN_SHOPS = {"YARN_STORE"}

def _determine_crop_mode(self, unlocked_shops: List[str]) -> str:
    if not unlocked_shops:
        return "STRAWBERRY"

    # Priority 1: Yarn worlds route to Yarn
    if any(s in YARN_SHOPS for s in unlocked_shops):
        return "YARN"

    # Priority 2: Strawberry shops lock in Strawberry Bedrock
    if any(s in STRAWBERRY_SHOPS for s in unlocked_shops):
        return "STRAWBERRY"

    # Priority 3: Pet Cafe -> CARROT
    if any(s in CARROT_SHOPS for s in unlocked_shops):
        return "CARROT"

    # Priority 4: Bakery -> WHEAT
    if any(s in WHEAT_SHOPS for s in unlocked_shops):
        return "WHEAT"

    # Priority 5: Pizza -> TOMATO
    if any(s in TOMATO_SHOPS for s in unlocked_shops):
        return "TOMATO"

    return "STRAWBERRY"
```

### 2.2 The Passthrough Fallback in `act()`
```python
# Lines 107-109:
if mode in ("STRAWBERRY", "YARN"):
    return action  # action is super().act(obs) = ClosedLoopAgentV2
```

### 2.3 Combinatorial Domain Saturation
In the Kaggriculture simulator, there are 8 distinct shop types:
1. `SMOOTHIE_SHOP` (Strawberry)
2. `ICE_CREAM_SHOP` (Strawberry)
3. `BRUNCH_SPOT` (Strawberry)
4. `FARMERS_MARKET` (Strawberry)
5. `YARN_STORE` (Yarn)
6. `PET_CAFE` (Carrot)
7. `BAKERY` (Wheat)
8. `PIZZA_SHOP` (Tomato)

Notice:
- `STRAWBERRY_SHOPS` comprises **4 out of 8 shop types** (50.0% of the shop space).
- `YARN_SHOPS` comprises **1 out of 8 shop types** (12.5% of the shop space).
- Together, Priority 1 (`YARN`) and Priority 2 (`STRAWBERRY`) cover **5 out of 8 shop types (62.5%)**!

At Step 72 (Day 3) and Step 144 (Day 6), `_determine_crop_mode` inspects the first 1 or 2 unlocked shops. Under uniform drawing from the 8 shop types:
- Probability that neither of the first 2 shops is in `YARN_SHOPS` or `STRAWBERRY_SHOPS`:
  $$P(\text{Neither}) = \left(\frac{3}{8}\right)^2 \approx 14.06\%$$
- Probability that at least one shop is Yarn or Strawberry:
  $$P(\text{Yarn or Strawberry}) = 1 - 0.1406 = 85.94\%$$

### 2.4 Empirical Mode Distribution Across the 50 Seeds
The empirical observation across the 50 Discovery seeds matches the theoretical probability almost perfectly:

| Mode Selected | Number of Seeds | Percentage | Behavior vs `ClosedLoopAgentV2` | Seed IDs |
| :--- | :---: | :---: | :--- | :--- |
| **`STRAWBERRY`** | **33** | 66.0% | **Literally identical to V2** | 50002, 50003, 50005, 50006, 50007, 50009, 50010, 50011, 50012, 50013, 50014, 50015, 50016, 50019, 50020, 50021, 50024, 50027, 50028, 50030, 50031, 50032, 50033, 50034, 50039, 50040, 50041, 50043, 50044, 50046, 50047, 50048, 50049 |
| **`YARN`** | **9** | 18.0% | **Literally identical to V2** | 50000, 50022, 50025, 50029, 50035, 50036, 50038, 50042, 50045 |
| **Subtotal Tied** | **42** | **84.0%** | **100% Bit-Exact Twin of V2** | — |
| **`CARROT`** | **5** | 10.0% | Diverged (sold carrots) | 50001 (+192), 50008 (+18), 50023 (+146), 50026 (+16), 50037 (+22) |
| **`TOMATO`** | **2** | 4.0% | Diverged (substituted 13 tomato plants) | 50004 (+15,264), 50018 (-2,388) |
| **`WHEAT`** | **1** | 2.0% | Diverged (sold wheat) | 50017 (-11) |
| **Total** | **50** | **100.0%** | — | — |

---

## 3. Did EXP-DEV-001 Actually Test Dynamic Portfolio Adaptation?

### The Core Diagnostic Verdict:
1. **The test was severely structurally inert**: Because the candidate designated `YARN` as a passthrough to V2 and treated any presence of a Strawberry shop as an immediate veto against specialty crop exploration, the dynamic mechanism was **completely inactive across 84% of the world distribution**.
2. **The dynamic mechanism was tested on only 8 seeds**:
   - 5 seeds explored Carrot mode (all 5 were small wins, +$16 to +$192).
   - 1 seed explored Wheat mode (small loss, -$11).
   - 2 seeds explored Tomato mode (extreme bimodal outcomes: +$15,264 and -$2,388).
3. **Implication for Development**:
   EXP-DEV-001 did not test a general dynamic portfolio agent across 50 diverse worlds; it tested a static strawberry bedrock that branched on exactly 8 worlds, where 2 worlds with double Pizza Shop unlocks determined the entire statistical outcome of the experiment.
