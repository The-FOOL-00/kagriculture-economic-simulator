# V49 Historical Loss Counterfactual Analysis (Section 13)

## 1. Executive Summary

We evaluated **8 intervention regimes** across all **11 historical losses** of `V49_RETAIN` against `v44_economic_portfolio` to determine whether targeted patches to early liquidity, barn entrance coordination, or livestock composition / swap logic can rescue these matches.

The 8 regimes evaluated:
1. `V49 Baseline`: Unmodified baseline.
2. `Herd Patch`: Suppressing COWSWAP overlay at step 150 (retaining native Route 0 Cow purchase).
3. `Liquidity Patch`: Shadow float of +$1,400 injected at Step 1.
4. `Barn Patch`: Local shed-entrance priority coordination at steps 518–524.
5. `Herd + Barn`: Joint herd and barn intervention.
6. `Liquidity + Herd`: Joint liquidity and herd intervention.
7. `Liquidity + Barn`: Joint liquidity and barn intervention.
8. `Full Candidate`: All three interventions combined.

---

## 2. Quantitative Results Matrix

| Loss ID | Seed:Seat | Category | V49 Baseline | Herd Patch | Liquidity (+$1.4k) | Barn Patch | Full Candidate | Result / Classification |
|---|---|---|---|---|---|---|---|---|
| **L01** | `250416:0` | Barn/Macro | -$716.00 | -$1,850.00 | -$716.00 | -$716.00 | -$1,850.00 | **Worsened (-$1,134.00)** |
| **L02** | `250416:1` | Barn/Macro | -$716.00 | -$1,850.00 | -$716.00 | -$716.00 | -$1,850.00 | **Worsened (-$1,134.00)** |
| **L03** | `250428:0` | Late Crop/Timing | -$31.00 | -$31.00 | -$31.00 | -$31.00 | -$31.00 | **Inert ($0.00)** |
| **L04** | `250428:1` | Late Crop/Timing | -$160.00 | -$160.00 | -$160.00 | -$160.00 | -$160.00 | **Inert ($0.00)** |
| **L05** | `250433:0` | Route Branch | -$470.00 | -$470.00 | -$470.00 | -$470.00 | -$470.00 | **Inert ($0.00)** |
| **L06** | `250433:1` | Route Branch | -$470.00 | -$470.00 | -$470.00 | -$470.00 | -$470.00 | **Inert ($0.00)** |
| **L07** | `250436:0` | COWSWAP/Herd | -$1,405.00 | **+$2,449.00** | -$1,405.00 | -$1,405.00 | **+$2,449.00** | **RESCUED (+3,854.00)** |
| **L08** | `250436:1` | COWSWAP/Herd | -$1,405.00 | **+$2,449.00** | -$1,405.00 | -$1,405.00 | **+$2,449.00** | **RESCUED (+3,854.00)** |
| **L09** | `250439:0` | COWSWAP/Herd | -$1,407.00 | **+$1,418.00** | -$1,407.00 | -$1,407.00 | **+$1,418.00** | **RESCUED (+2,825.00)** |
| **L10** | `250439:1` | COWSWAP/Herd | -$1,407.00 | **+$1,418.00** | -$1,407.00 | -$1,407.00 | **+$1,418.00** | **RESCUED (+2,825.00)** |
| **L11** | `250497:1` | Route Branch | -$901.00 | -$901.00 | -$901.00 | -$901.00 | -$901.00 | **Inert ($0.00)** |

---

## 3. Causal Mechanics & Conclusions

1. **Liquidity is 100% Inert:**
   - In all 11 matches, the `Liquidity Patch` produced an exact **$0.00** change in terminal delta.
   - V49's action tapes are deterministic and static. V49 does not fail transactions due to early cash shortfall; rather, its purchases are pre-scheduled. Injecting extra capital sits idle in the bank and does not induce earlier purchases or altered crop rotations.

2. **Barn Congestion is 100% Inert:**
   - The `Barn Patch` produced an exact **$0.00** change across all 11 matches.
   - On Route 0, physical paths are pre-compiled to avoid simultaneous tile collisions at the shed door. In Seed 250416, the loss is driven by delivery timing and market price drops, not physical traffic jamming.

3. **Herd Patch (COWSWAP Suppression): High Impact, High Risk:**
   - The Herd Patch cleanly rescues **4 out of 11 losses** (L07, L08, L09, L10), flipping -$1,405 to +$2,449 (+$3,854) on Seed 250436 and -$1,407 to +$1,418 (+$2,825) on Seed 250439.
   - However, on Seed 250416 (L01 and L02), suppressing COWSWAP significantly deepens the loss from -$716 to -$1,850 (-$1,134 degradation).
   - Across discovery seeds (from `v52_interaction_matrix.json`), global COWSWAP suppression generates **30 casualties** with a mean delta of **-$7,369.70**.
   - Therefore, COWSWAP cannot be modified without inducing widespread catastrophic regressions across the broader meta.
