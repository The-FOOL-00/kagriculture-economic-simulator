# PHASE020 — CANDIDATE MECHANISM SPECIFICATION (§33)

**Mechanism Name**: `MULTIWORKER_HARVEST_SYNCHRONIZATION`  
**Opportunity Family**: `MULTI_WORKER`  
**Phase**: PHASE020  
**Date**: 2026-09-20  
**Status**: PREREGISTERED FOR ISOLATED PILOT  

---

## 1. Scientific Hypothesis

> **Hypothesis**: In multi-worker states ($N \ge 2$, turns 226..709), when mature crop plots are unharvested and farmhands are either idle or performing non-critical transit, synchronizing an adjacent or co-located farmhand to harvest the plot frees the tile earlier for the next production cycle, generating positive terminal margin advantage ($> +$25.00) without distorting cash gates or starving livestock.

---

## 2. State Trigger Conditions

The mechanism triggers at step $t$ if and only if all of the following conditions hold:
1. **Multi-Worker Presence**: Total workers $N \ge 2$ (farmer + at least 1 farmhand).
2. **Mature Plot Available**: There exists at least one tile $(x, y)$ on the farm where:
   - `tile.get("kind") == "PLANT"` or `tile.get("crop") is not None`
   - Growth stage indicates maturity (`growth_stage >= 2` or `yield_units > 0`).
3. **Worker Proximity**: A farmhand $w_i$ ($i \ge 1$) is on tile $(x, y)$ or adjacent ($\text{Manhattan} \le 1$).
4. **Non-Disruptive Farmer Role**: The farmer is NOT already executing `["HARVEST"]` on this exact tile.
5. **No Tranche / No Early Sell**: The action contains **zero** market sell modifications.

---

## 3. Transformation Definition

The candidate patch mutates the baseline joint action:
1. If farmhand $w_i$ is at $(x, y)$:
   `action["hands"][i-1] = ["HARVEST"]`
2. If farmhand $w_i$ is adjacent to $(x, y)$:
   `action["hands"][i-1] = [direction_to_tile]`
   followed by harvest in subsequent turn (or direct harvest if engine allows).
3. The farmer's baseline action is preserved unchanged.
4. Market orders are preserved unchanged.

---

## 4. Candidate Representation & Architecture Integration

- **Class**: `CoupledPatch`
- **Mechanism Family**: `MULTIWORKER_HARVEST_SYNCHRONIZATION`
- **Category**: `LABOR`
- **Worker IDs**: `[i]` (the assigned farmhand)
- **Actions**: `[mutated_joint_action]`

---

## 5. Safety Invariants

Before evaluation or commit, the candidate must verify:
1. **Worker Legality**: Farmhand index $i \ge 1$ exists.
2. **No Collision**: The farmhand's move/harvest does not create an edge-swap or vertex collision with farmer or other farmhands.
3. **Shed Capacity**: Adding harvested produce will not cause shed overflow.
4. **Feed Security**: Livestock wheat buffer is undisturbed.

---

## 6. Exact Counterfactual Procedure

- **Simulator**: `CounterfactualSimulator.evaluate(...)`
- **Macro Detector**: `MacroRegimeTransitionDetector.probe_candidate(...)`
- **Horizon**: Adaptive $H=24$ turns.
- **Dynamic V3 Continuation**: If macro escalated, run dynamic V3 continuation policy with complete state restoration.
- **Economic Hurdle**: Committed only if:
  $$\Delta_{\text{terminal\_margin}} \ge \$15.00$$
  and intermediate solvency and feed security certificates are verified.

---

## 7. Preregistered Pilot Criteria (§35)

- **Pilot Cohort**: Seeds `249366..249375` (10 fresh seeds, 20 CRN mirror matches).
- **Control**: Live qualified foundation (`build_robust_qualified_config()`).
- **Success Criteria for Promotion**:
  1. Mean paired treatment delta $> \$0.00$.
  2. Win/Loss/Tie record demonstrates non-inferiority ($W \ge L$).
  3. Zero safety violations.
  4. Zero foundation displacements (strictly protected by Phase 018 reservation).
  5. Latency overhead $< 15\text{ms/step}$.
