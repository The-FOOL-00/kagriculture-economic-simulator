# PHASE 021: CAPABILITY GAP MATRIX & RANKING

**Date**: 2026-09-20  
**Phase**: PHASE021 — AEC Capability, Action-Space & Dependency Completeness Audit  
**Chassis Ground Truth**: `sim.hpp`, `kagsim.cpp`  

---

## 1. Executive Summary

In accordance with Section 10, this document ranks candidate **capability gaps**—not mechanisms—across 6 rigorous dimensions:
1. **Recurrence** (frequency across observed census states)
2. **Breadth** (number of independent opportunity families affected)
3. **Economic Headroom** (net realizable delta under exact continuation)
4. **Representability Evidence** (whether the capability can be expressed without modifying V3)
5. **Safety & Collision Implications**
6. **Architectural Simplicity**

---

## 2. Capability Gap Ranking Matrix

| Rank | Capability Gap | Recurrence | Breadth | Net Realizable Headroom | Representability | Safety Profile | Implementation Feasibility (§11) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | **GAP-1: Auxiliary Worker Shed Deposit Sequence** | High (1,034 states) | 2 Families | **Negative** (Transit cost dominates) | Hard (Requires multi-step scheduler) | High collision & overflow risk | **FAIL (§11: Economically negative)** |
| **2** | **GAP-2: Biological Maturity Gate (`yield == max_yield`)** | Mod (1,034 states) | 1 Family | **$0.00** (Subsumed by baseline) | Easy (Can be checked from tile) | Safe | **FAIL (§11: Zero alpha over V3)** |
| **3** | **GAP-3: Intra-Agent Backbone Route Observability** | High (3,000+ states) | 3 Families | N/A (Diagnostic only) | **Impossible** without mutating V3 | Safe | **FAIL (§11: Violates V3 Freeze)** |
| **4** | **GAP-4: Direct Unit-to-Unit Inventory Transfer** | Mod (326 states) | 1 Family | None (Engine impossible) | **Impossible** (Engine has no unit trade) | Illegal | **FAIL (§11: Unsupported by engine)** |

---

## 3. Deep Analysis of Ranked Capability Gaps

### GAP-1: Auxiliary Worker Multi-Step Transit & Shed-Deposit Scheduler
- **Hypothesis**: If an auxiliary farmhand that harvests a crop could immediately route to the shed, execute `DROP`, and return, the cargo would not be trapped.
- **Physical Feasibility Audit**:
  - A farmhand on tile $(4, 9)$ requires 5 steps to reach shed tile $(4, 4)$, 1 step to `DROP`, and 5 steps to return to its watering circuit: **11 steps total**.
  - A farmhand’s total lifespan is **24 turns** (1 day).
  - Spending 11 out of 24 turns (45.8%) walking to the shed and back causes the farmhand to miss 11 watering actions.
  - Missing 11 watering actions causes 5–10 crops to wither or lose yield increments, forfeiting **$200 to $400 in lost crop production** to deposit 1–2 units of wheat ($35–$70).
- **Verdict**: **The physical transit cost makes auxiliary shed-deposit economically net-negative in all mid-game states**.

### GAP-2: Biological Maturity Gate
- **Hypothesis**: Gating harvest interventions so they only trigger when a crop has reached its maximum yield (`yield_units == max_yield`).
- **Physical Feasibility Audit**:
  - When a crop reaches `max_yield`, V3’s internal planner immediately routes the farmer to harvest it within 1–2 steps.
  - This was proven in Phase 010 (`PHASE010_DYNAMIC_HARVEST_QUALIFICATION.md`): Gated mature harvest interventions yielded $\Delta = \$0.00$ because V3 already harvests fully mature crops optimally.
- **Verdict**: **Zero incremental economic headroom over the V3 baseline**.

### GAP-3: Intra-Agent Backbone Route Observability
- **Hypothesis**: Allowing the AEC compiler to read V3’s internal `_proposals` route queue to avoid interrupting workers that have active watering duties.
- **Feasibility Audit**:
  - V3 is frozen inside `submission_Vj_kc_v3.tar.gz` (`SHA256: 845e0d10...`).
  - Accessing internal planner memory would require modifying or wrapping V3 internals, violating Section 1 (Hard Chassis Freeze).
- **Verdict**: **Forbidden by Chassis Immutability Invariants**.

### GAP-4: Direct Unit-to-Unit Inventory Transfer
- **Hypothesis**: Allowing a farmhand to hand harvested wheat directly to the farmer.
- **Feasibility Audit**:
  - In `sim.hpp`, there is no `OP_TRANSFER` opcode.
  - Unit inventories are strictly private and isolated.
- **Verdict**: **Physically impossible in the Kagriculture simulator**.

---

## 4. Final Scientific Evaluation under Section 11 & Section 13

Section 11 mandates:
> *"Implementation is forbidden unless the audit demonstrates: the capability is genuinely supported by the environment, needed by multiple independent states, representable without modifying V3, exactly simulatable, safe, non-tranche, and causally justified. If no capability meets those criteria: STOP."*

None of the audited capability gaps satisfy these criteria:
- GAP-1 is economically net-negative due to transit opportunity costs.
- GAP-2 produces zero incremental delta over the pristine V3 chassis.
- GAP-3 violates V3 chassis immutability.
- GAP-4 is impossible under the physics of the Kagriculture engine.

Therefore, under Section 13, the audit must terminate with:
```text
CAPABILITY AUDIT COMPLETE / NO ACTION-SPACE GAP
```
(or `CAPABILITY GAP IDENTIFIED / NO SAFE IMPLEMENTATION` for GAP-1/GAP-3).
