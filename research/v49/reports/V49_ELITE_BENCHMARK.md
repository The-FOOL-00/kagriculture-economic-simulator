# V49 — Elite Ladder Benchmark Report

**Evaluation Suite**: 1,536 Paired Legs (768 Matches with Alternating Seats)  
**Baseline**: Frozen V48 (`candidates/v48_challenger/main.py`)  
**Challenger**: V49 Meta Fusion (`candidates/v49_meta_fusion/main.py`)  
**Quarantine Protocol**: Hard assertions enforced (Holdouts `214200–214249`, `340090–340199`, `249695–249734` untouched).

---

## 1. Executive Summary: Elite Meta Gate Clearance

Per **Section 39 (Elite Meta Gate)**:
- Requirement: $\ge 256$ paired legs per major family.
- Win Rate Threshold: $\ge 70.0\%$ win rate against each major family.
- Failure Constraint: No catastrophic family ($\text{casualties} = 0$).

### Result: **PASSED DECISIVELY**
Across all six elite opponent families, V49 achieved a minimum win rate of **95.70%** (vs V44) and **100.0%** against all other five elite families, with an aggregate win rate of **99.28%**, **+$76.81** overall mean delta, and **exactly 0 casualties**.

---

## 2. Comprehensive Opponent Family Breakdown

| Opponent Family | Paired Legs | V48 Win Rate | V49 Win Rate | Mean $\Delta$ ($) | Median $\Delta$ ($) | 95% CI ($) | Rescues | Casualties | Active Legs | Active Mean $\Delta$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **V44 Incumbent** | 256 | 94.92% | **95.70%** | +$90.86 | +$160.00 | [$0.00, +$160.00] | **2** | **0** | 150 | +$155.07 |
| **dmitrii_lb2800** | 256 | 100.0% | **100.0%** | +$89.30 | +$160.00 | [$0.00, +$160.00] | 0 | **0** | 146 | +$156.58 |
| **tetsutani_pasture** | 256 | 100.0% | **100.0%** | +$88.36 | +$140.00 | [$0.00, +$160.00] | 0 | **0** | 146 | +$154.93 |
| **kaitofukami_v48_3009** | 256 | 100.0% | **100.0%** | +$53.09 | $0.00 | [$0.00, +$160.00] | 0 | **0** | 88 | +$154.43 |
| **indarkarhana_top10** | 256 | 100.0% | **100.0%** | +$85.55 | +$120.00 | [$0.00, +$160.00] | 0 | **0** | 143 | +$153.15 |
| **saiteja_mega_3000** | 256 | 100.0% | **100.0%** | +$53.71 | $0.00 | [$0.00, +$160.00] | 0 | **0** | 92 | +$149.46 |
| **TOTAL / OVERALL** | **1,536** | **99.15%** | **99.28%** | **+$76.81** | **+$120.00** | **[$0.00, +$160.00]** | **2** | **0** | **765** | **+$154.12** |

---

## 3. Analysis of Head-to-Head Alpha

### 1. Zero Risk Profile (Zero Casualties Across 1,536 Legs)
In 1,536 paired legs, V49 never produced a negative cash delta relative to V48 ($\text{P10} \ge \$0.00$, $\min \Delta = \$0.00$). The intervention operates solely as an efficiency ratchet: in legs where late seeds would have been wasted, cash is salvaged; in all other legs, actions remain bit-for-bit identical to V48.

### 2. Concrete Head-to-Head Win Rate Expansion (+2 Rescues vs V44)
In matches against the strong V44 portfolio baseline, two games that V48 narrowly lost were converted into outright wins by V49:
- In both matches, V48 lost by less than $100 coins due to cash tied up in dead wheat/carrot seed inventory at step 719.
- V49's `E402` seed cap clamped the unplantable seed purchases on steps 624–672, preserving +$160 coins in liquid cash at terminal evaluation, flipping both losses into decisive victories.
- As a result, V49's win rate against V44 improved from **94.92%** to **95.70%**.

### 3. Active Cohort Performance
Across the 1,536 legs, the late seed cap actively triggered in 765 legs (49.8% activation rate). When active, the mean margin improvement was **+$154.12** (median **+$160.00**), representing 8 to 16 avoided redundant seed purchases.

---

## 4. Promotion Gate Status

- **Promotion Gate A (Single Patch, 128 legs)**:
  - Required: 0 casualties, mean $\Delta \ge +\$75$, median $\ge \$0$, 95% CI lower $> \$0$.
  - Result: **PASSED** (Mean $\Delta = +\$85.27$, 0 casualties).
- **Promotion Gate B (Integrated Candidate, 256 legs)**:
  - Required: 0 casualties, mean $\Delta \ge +\$150$ (active) / $\ge +\$75$ (total), win rate $\ge \text{V48}$.
  - Result: **PASSED** (Active mean $\Delta = +\$155.07$, Win rate $95.70\% > 94.92\%$).
- **Promotion Gate C (Elite Challenger, 512+ legs)**:
  - Evaluated: 1,536 legs across 6 distinct elite families.
  - Required: 0 casualties, win rate $\ge \text{V48}$, 95% CI lower $\ge \$0$, P10 $\ge -\$300$.
  - Result: **PASSED DECISIVELY** (0 casualties, WR $99.28\% \ge 99.15\%$, P10 = $0.00$).
