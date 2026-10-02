# V57 Structural Queue Alignment Counterfactual Matrix

## Executive Summary

The V57 program conducted an exhaustive evaluation of structural queue interventions (Class B: same turn, same commodities, same aggregate quantities, no new economic orders) aimed at altering the lockstep transaction queue pairing around Step 697 between `V49_Meta_Fusion` and `v44_economic_portfolio`.

The historical matrix evaluated 24 distinct structural interventions across all 4 legs of the two fresh loss worlds:
- **Seed 250621** (Seat 0 and Seat 1, baseline margin: -$82.00)
- **Seed 250617** (Seat 0 and Seat 1, baseline margin: -$862.00)

---

## 1. Counterfactual Results Matrix

| Intervention ID | Family | Description | 250621 Margin (S0/S1) | 250617 Margin (S0/S1) | Mean Delta vs V49 | Rescues | Regressions | Status |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **`Q0_baseline`** | Q0 | Exact V49 market action list | -$82.00 / -$82.00 | -$862.00 / -$862.00 | +$0.00 | 0/4 | 0/4 | Incumbent Baseline |
| **`Q6_step697_wool_first`** | Q6 | Step 697: Prioritize WOOL first | -$193.00 / -$193.00 | -$964.00 / -$964.00 | -$106.50 | 0/4 | 0/4 | Worsened (-$111 / -$102) |
| **`Q6_step697_wool_egg_milk_carrot`** | Q6 | Step 697: Reverse priority | -$179.00 / -$179.00 | -$961.00 / -$961.00 | -$98.00 | 0/4 | 0/4 | Worsened (-$97 / -$99) |
| **`Q6_step697_milk_wool_egg_carrot`** | Q6 | Step 697: MILK first, then WOOL | -$193.00 / -$193.00 | -$964.00 / -$964.00 | -$106.50 | 0/4 | 0/4 | Worsened (-$111 / -$102) |
| **`Q6_step697_carrot_wool_egg_milk`** | Q6 | Step 697: Move WOOL to index 1 | -$96.00 / -$96.00 | -$865.00 / -$865.00 | -$8.50 | 0/4 | 0/4 | Worsened (-$14 / -$3) |
| **`Q6_step697_egg_wool_carrot_milk`** | Q6 | Step 697: EGG first, then WOOL | -$179.00 / -$179.00 | -$958.00 / -$958.00 | -$96.50 | 0/4 | 0/4 | Worsened (-$97 / -$96) |
| **`Q1_step697_lead_pad1`** | Q1 | Step 697: Prepend `[]` | -$82.00 / -$82.00 | -$964.00 / -$964.00 | -$51.00 | 0/4 | 0/4 | Neutral / Worsened (-$102) |
| **`Q2_step697_pad_before_wool`** | Q2 | Step 697: Insert `[]` before WOOL | -$82.00 / -$82.00 | -$862.00 / -$862.00 | +$0.00 | 0/4 | 0/4 | Identical |
| **`Q3_step697_trailing_pad`** | Q3 | Step 697: Append `[]` | -$82.00 / -$82.00 | -$862.00 / -$862.00 | +$0.00 | 0/4 | 0/4 | Identical |
| **`Q4_step697_split_carrot`** | Q4 | Step 697: Split CARROT 33 into 16+17 | -$82.00 / -$82.00 | -$887.00 / -$887.00 | -$12.50 | 0/4 | 0/4 | Neutral / Worsened (-$25) |
| **`Q6_step694_wool_first`** | Q6 | Step 694: Prioritize WOOL first | -$388.00 / -$388.00 | -$862.00 / -$862.00 | -$153.00 | 0/4 | 0/4 | Severely Worsened (-$306) |
| **`Q6_step694_wool_egg_first`** | Q6 | Step 694: WOOL + EGG first | -$388.00 / -$388.00 | -$862.00 / -$862.00 | -$153.00 | 0/4 | 0/4 | Severely Worsened (-$306) |
| **`Q6_step694_egg_wool_first`** | Q6 | Step 694: EGG + WOOL first | -$388.00 / -$388.00 | -$862.00 / -$862.00 | -$153.00 | 0/4 | 0/4 | Severely Worsened (-$306) |
| **`Q1_step694_lead_pad1`** | Q1 | Step 694: Prepend 1 `[]` | -$388.00 / -$388.00 | -$862.00 / -$862.00 | -$153.00 | 0/4 | 0/4 | Severely Worsened (-$306) |
| **`Q1_step694_lead_pad2`** | Q1 | Step 694: Prepend 2 `[]` | -$408.00 / -$408.00 | -$862.00 / -$862.00 | -$163.00 | 0/4 | 0/4 | Severely Worsened (-$326) |
| **`Q2_step694_pad_before_wool`** | Q2 | Step 694: Insert `[]` before WOOL | -$82.00 / -$82.00 | -$862.00 / -$862.00 | +$0.00 | 0/4 | 0/4 | Identical |
| **`Q6_step693_milk_strawberry_first`** | Q6 | Step 693: Reorder sells | -$82.00 / -$82.00 | -$862.00 / -$862.00 | +$0.00 | 0/4 | 0/4 | Identical |
| **`Q6_step693_egg_milk_first`** | Q6 | Step 693: EGG + MILK first | -$79.00 / -$79.00 | -$862.00 / -$862.00 | +$1.50 | 0/4 | 0/4 | Insufficient (+$3 on -$82) |
| **`Q1_step693_lead_pad1`** | Q1 | Step 693: Prepend 1 `[]` | -$82.00 / -$82.00 | -$864.00 / -$864.00 | -$1.00 | 0/4 | 0/4 | Slight Degradation (-$2) |
| **`Q6_step718_wool_egg_wheat`** | Q6 | Step 718: Reorder terminal sells | -$82.00 / -$82.00 | -$862.00 / -$862.00 | +$0.00 | 0/4 | 0/4 | Identical |
| **`Q6_step718_wool_carrot_wheat`** | Q6 | Step 718: WOOL + CARROT first | -$84.00 / -$84.00 | -$864.00 / -$864.00 | -$2.00 | 0/4 | 0/4 | Slight Degradation (-$2) |
| **`Q6_step718_egg_wool_carrot`** | Q6 | Step 718: EGG + WOOL first | -$84.00 / -$84.00 | -$862.00 / -$862.00 | -$1.00 | 0/4 | 0/4 | Slight Degradation (-$2) |
| **`Q1_step718_lead_pad1`** | Q1 | Step 718: Prepend 1 `[]` | -$152.00 / -$152.00 | -$862.00 / -$862.00 | -$35.00 | 0/4 | 0/4 | Worsened (-$70 on 250621) |
| **`Q6_combo_694_697_wool_first`** | Q6 | Steps 694 & 697: Prioritize WOOL | -$499.00 / -$499.00 | -$964.00 / -$964.00 | -$259.50 | 0/4 | 0/4 | Catastrophic Degradation |

---

## 2. Mathematical and Forensic Analysis of Findings

1. **Zero Rescues (0 / 4 across all 24 candidates)**:
   Not a single structural queue alignment transformation rescued either of the two loss worlds.
2. **Why Moving Bulky Goods Down Causes Severe Regressions**:
   At Step 694 and Step 697, V49's baseline market order structure places high-volume crops (`WHEAT`, `CARROT`, `TOMATO`) in the leading queue slots (indices 0 and 1). When an intervention reorders the list to prioritize high-value livestock goods (`WOOL` or `MILK`), the high-volume crops are pushed to later slots.
   - In `_process_market`, if the opponent executes their crop sale in slot 0 while V49 executes livestock in slot 0, the opponent claims the pre-depression crop price.
   - When V49 reaches the crop sale in subsequent slots, crop prices are already depressed by the opponent's prior clearance.
   - Furthermore, delayed bulky clearance prevents shed space from being liberated prior to the end-of-turn worker drop off, triggering capacity overflows and inventory loss.
3. **Leading Padding Induces Opponent Monopolization**:
   Prepending empty slots `[]` (Q1) causes V49 to forfeit slot 0 entirely. The opponent executes slot 0 alone without lockstep price contention, capturing superior pricing and leaving V49 to sell into an already-depressed market in slot 1.
4. **Conclusion**:
   V49's existing market order list structure is strictly superior to all structural variants. There is no positive structural queue alpha.
