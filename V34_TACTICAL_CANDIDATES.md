# V34 Tactical Action Candidates & Representation Ledger

**Program:** Kagriculture V34 Research Program (A7 Tactical Forward Search)  
**Author:** Lead Research Scientist, Competitive-Programming Engineer, Simulator Engineer, and Implementation Owner  
**Date:** 2026-09-24  
**Scope:** Specification and taxonomy of local, A7-compatible tactical action candidates.  

---

## 1. The Minimal-Deviation Architectural Principle

V32 and V33 proved that large interventions (such as unlocking a 4th quadrant of land in P12 or wholesale switching to Dmitrii livestock in V33) cause catastrophic physical and financial desynchronization:
1. **Physical Desynchronization:** Worker movements diverge from carefully choreographed planting/watering routes, leading to unwatered crops, missed harvest windows, and weed propagation.
2. **Liquidity Starvation:** Capital committed to unproven expansion ($4,000 capex) starves the farm of daily wage and feed buffers.

Therefore, V34 adheres to the **Minimal-Deviation Principle**:
```
At every decision point, minimize deviation from A7.
Prefer small, localized, zero-physical-displacement actions
that adjust order quantities, timing, or cutoff gates.
Never alter physical worker pathing during core maintenance cycles.
```

---

## 2. Formal Tactical Candidate Schema

Each tactical candidate is defined by a strongly typed contract:
```python
@dataclass
class TacticalCandidate:
    action_id: str
    parent_a7_action: Dict[str, Any]
    candidate_action: Dict[str, Any]
    category: str
    state_signature: str
    trigger_features: Dict[str, float]
    action_delta_description: str
    physical_impact: str
    market_impact: str
    compatible_horizon: int
    status: PromotionStatus
```

---

## 3. Discovered Candidate Cohorts

### Cohort A: Step 0 Market Wash Sizing
- **Parent Action:** `[["BUY_PRODUCT", "WHEAT", 30], ["SELL", "WHEAT", 30]]`
- **Motivation:** A7's static 30/30 wash captures initial shop liquidity spread. However, depending on initial seed market parameters, sizing down to 25/25 preserves working capital while still capturing spread.
- **Candidates:**
  1. `TACTICAL_STEP0_WASH20`: Resize wash to 20/20.
  2. `TACTICAL_STEP0_WASH25`: Resize wash to 25/25 (preserves extra \$125 liquid buffer).
  3. `TACTICAL_STEP0_WASH35`: Resize wash to 35/35 (aggressive spread capture).
  4. `TACTICAL_STEP0_NOWASH`: Complete market pass (zero wash).

### Cohort B: Late Planting Cutoff ($t \ge 680$)
- **Parent Action:** A7 continued planting slow crops (e.g. Melon, Tomato, Strawberry).
- **Motivation:** Crops require fixed growth times (Wheat: 12, Carrot: 24, Tomato: 48, Strawberry: 72, Melon: 96 ticks). Any planting of a crop that cannot mature before step 718 represents 100% loss of seed capital ($50 to $100 per unit).
- **Candidate:** `TACTICAL_LATE_PLANTING_CUTOFF`: Converts futile `PLANT` actions to `PASS` and removes useless `BUY_SEED` orders, keeping workers stationary and saving cash.

### Cohort C: Terminal High-Margin Pre-Liquidation ($t \in [714, 717]$)
- **Parent Action:** A7 waits until step 718 to liquidate all shed inventory in a single bulk dump.
- **Motivation:** Bulk dumps of 50+ units on step 718 suffer price impact and risk order truncation if the order list exceeds 10.
- **Candidate:** `TACTICAL_PRE_LIQUIDATION`: Orderly pre-sale of up to 20 units of Melon, Strawberry, Milk, and Wool at high spot prices prior to final liquidation.

### Cohort D: Pre-Wage Capital Buffer ($t \pmod{24} \in [20, 23]$)
- **Motivation:** Prevents intra-turn starvation before midnight wage deductions ($N_{\text{workers}} \times \$10$).
- **Mechanism:** Automatically verified by `LiquidityGuard`.
