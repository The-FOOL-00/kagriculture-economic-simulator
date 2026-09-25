# V39 Failure Taxonomy — Systematic Categorization of Live V35 Failure Modes

## 1. Failure Taxonomy Classification Matrix (N = 6 Losses)
Every live loss of the frozen V35 candidate has been clustered into its underlying causal mechanism:

| Mechanism Class | Primary Episode IDs | Count | % of Losses | Mean Deficit | Median Deficit | Worst Deficit | Common Step Range | Observable Signature |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **`TERMINAL_LIQUIDATION_OMISSION`** | `113183263`, `113171441`, `113164394`, `113166778` | **4** | **66.67%** | **-$1,505.5** | **-$1,492.0** | -$2,247.0 | Step 694–698 (Day 28 Hr 22 – Day 29 Hr 02) | Shed has $\ge 4$ Milk, $\ge 15$ Strawberry, or $\ge 2$ Wool at Step 694, but market order omits them until Step 696/698. |
| **`TERMINAL_HIRE_BURN`** | `113164394` (secondary in others) | **1** | **16.67%** | **-$1,988.0** | **-$1,988.0** | -$1,988.0 | Step 697–699 (Day 29 Hr 01 – Hr 23) | Market order issues `['HIRE']` on Day 29, incurring Fibonacci hiring fees without payback. |
| **`LAND_TIMING_SE`** | `113177277` | **1** | **16.67%** | **-$11,630.0** | **-$11,630.0** | -$11,630.0 | Step 260–290 (Day 11 Hr 20 – Day 12 Hr 02) | Opponent triggers SE land purchase 20+ steps earlier due to alternative seed/crop mix. |
| **`SEAT_TIEBREAKER_ASYMMETRY`** | `113153701` | **1** | **16.67%** | **-$640.0** | **-$640.0** | -$640.0 | Step 400–719 | Bit-identical self-play where Seat 1 receives market execution priority on identical orders. |

*(Note: Percentages sum to >100% due to overlapping secondary factors in Episode 113164394).*

---

## 2. Deep Mechanism Profiles

### Class A: `TERMINAL_LIQUIDATION_OMISSION` (Dominant Mode — 66.7% of Losses)
- **Description**:
  In A7 / V35, the static route tape inherited from V3 schedules a partial market sale at Step 694 (`WHEAT`, `CARROT`, `EGG`), but omits high-value animal and fruit products (`MILK`, `STRAWBERRY`, `WOOL`). These products remain sitting in the shed until Step 696 or Step 698.
- **Economic Impact**:
  Top competition agents (e.g., `Yassine Chritt`, `Lisan al-Gaib`) execute a full-shed liquidation at Step 694. When they sell their Strawberry and Milk first, market supply increases, driving prices down. By the time V35 sells its Strawberry and Milk at Step 696, it suffers severe price degradation, losing between **$800 and $1,500** in realized revenue.
- **Physical Signature**:
  At `step == 694`, `len(private['shed']['MILK']) > 0` or `len(private['shed']['STRAWBERRY']) > 0`, but the planned tape market action does not include `SELL MILK` or `SELL STRAWBERRY`.

---

### Class B: `TERMINAL_HIRE_BURN`
- **Description**:
  The static tape includes hardcoded `['HIRE']` market commands on Day 29 (Step 697, 698, 699).
- **Economic Impact**:
  Each hire costs substantial money (Fibonacci scaling: $144 to $377 per hire). Because the game terminates at Step 719, workers hired on Day 29 cannot cultivate or harvest any crops. This directly wastes **$300 to $650** of cash in the final turns.
- **Physical Signature**:
  At `step >= 696`, any `['HIRE']` command in `action['market']` is pure capital destruction.

---

### Class C: `LAND_TIMING_SE`
- **Description**:
  In Episode `113177277`, the opponent (`Adhiraj Jagtap`) purchased the final Southeast quadrant at Step 267, whereas V35 waited until Step 290.
- **Economic Impact**:
  23 turns earlier land development yielded an extra planting rotation, generating a +$11.6k compounding advantage.
- **Recoverability Assessment**:
  Adhiraj's early SE unlock required a completely different early capital trajectory (retaining wheat seeds and skipping initial buffer). Changing this would require broad structural modifications that risk destabilizing V35's 79.3% baseline win rate.

---

### Class D: `SEAT_TIEBREAKER_ASYMMETRY`
- **Description**:
  In validation self-play (`113153701`), two bit-identical instances of V35 play against each other on Seed 0. Seat 1 won by $640 solely because of tie-breaking resolution in simultaneous market fills.
- **Recoverability Assessment**:
  Inherent environmental parity limit; not an actionable defect.
