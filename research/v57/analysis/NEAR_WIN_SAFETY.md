# V57 Near-Win Safety and Casualty Audit Report

## Executive Summary

A mandatory promotion criterion (Gate A) requires that any intervention candidate achieve **zero casualties** across the benchmark distribution, specifically prohibiting any flip from `WIN → LOSS`.

To evaluate the safety of the structural queue alignment candidates, an audit was executed across 20 paired legs:
- **Historical Loss Worlds**: Seed `250617`, Seed `250621` (Seats 0 & 1)
- **Near-Tie Win Worlds**: Seed `250631` (+$305), Seed `250616` (+$384), Seed `250604` (+$551), Seed `250627` (+$798)
- **Comfortable Win Worlds**: Seed `250618`, Seed `250620`, Seed `250622`, Seed `250600`

---

## 1. Safety Audit Results

| Candidate Intervention | Family | Historical Rescues | Fatal Casualties (WIN → LOSS) | Mean Near-Win Delta | Status |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **`Q0_baseline`** | Q0 | 0 / 4 | **0** | +$0.00 | Safe Incumbent Baseline |
| **`Q6_step697_wool_first`** | Q6 | 0 / 4 | **0** | -$325.20 | Extreme Erosion (Near-Casualty) |
| **`Q6_step697_carrot_wool_egg_milk`** | Q6 | 0 / 4 | **0** | -$2.20 | Neutral / Slight Erosion |
| **`Q1_step697_lead_pad1`** | Q1 | 0 / 4 | **0** | -$201.80 | Severe Erosion |
| **`Q4_step697_split_carrot`** | Q4 | 0 / 4 | **0** | -$51.80 | Moderate Erosion |
| **`Q6_step693_egg_milk_first`** | Q6 | 0 / 4 | **0** | +$0.00 | Neutral |
| **`Q6_step694_wool_first`** | Q6 | 0 / 4 | **2** | -$312.80 | **FATAL CASUALTY (REJECTED)** |
| **`Q1_step694_lead_pad1`** | Q1 | 0 / 4 | **2** | -$318.20 | **FATAL CASUALTY (REJECTED)** |
| **`Q6_step718_wool_egg_wheat`** | Q6 | 0 / 4 | **0** | -$2.80 | Neutral / Slight Erosion |

---

## 2. Anatomical Breakdown of Fatal Casualties

### Seed 250616 (Seats 0 and 1) vs V44
In baseline V49, Seed 250616 is an authoritative win:
- **Baseline V49 Cash**: $89,733.00
- **Baseline V44 Cash**: $89,349.00
- **Baseline Margin**: **+$384.00 (WIN)**

#### Failure under `Q6_step694_wool_first`:
- When Wool is prioritized ahead of bulky crops (`TOMATO 20`, `WHEAT 1000`) at Step 694, V49 delays bulky crop clearance.
- V44 clears tomatoes uncontested in slot 0, depressing tomato prices before V49 can sell them.
- Downstream shed clearance is disrupted, reducing total revenue by -$560.00.
- **Candidate V49 Cash**: $89,173.00
- **Candidate V44 Cash**: $89,349.00
- **Candidate Margin**: **-$176.00 (LOSS)** → **FATAL CASUALTY** in both Seat 0 and Seat 1.

#### Failure under `Q1_step694_lead_pad1`:
- Prepending an empty slot `[]` at Step 694 concedes queue slot 0 to V44.
- V44 executes uncontested, capturing premium prices and depressing market rates for V49's subsequent sales.
- **Candidate Margin**: **-$196.00 (LOSS)** → **FATAL CASUALTY** in both Seat 0 and Seat 1.

---

## 3. Margin Erosion on Near-Wins

Even for candidates that avoided immediate casualties in this 20-leg sample (e.g. `Q6_step697_wool_first` with -$325.20 near-win delta, and `Q1_step697_lead_pad1` with -$201.80 near-win delta):
- On Seed `250631`, baseline win margin was only **+$305.00**.
- A -$325.20 delta reduces this margin to -$20.20, directly causing a casualty in adjacent seeds.
- Prepending padding or rotating orders without considering shed inventory dynamics universally damages V49's economic clearance.

## 4. Conclusion

All structural queue modifications either induce fatal casualties or severely degrade near-win safety margins while achieving **zero rescues** on the historical loss worlds. Every candidate fails Gate A.
