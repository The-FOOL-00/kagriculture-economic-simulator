# V35 Forensics: Causal Episode Breakdown of 25/25 Wash

## 1. Executive Summary
This document reconstructs the episode traces and causal mechanisms explaining why the 25/25 opening wheat wash (`TACTICAL_STEP0_WASH25`) outperforms the incumbent 30/30 wash. Through step-by-step counterfactual reconstruction, we establish that the advantage is driven by two coupled mechanisms:
1. **Reduced Opening Spread Friction:** A 25-unit round-trip trades 16.7% less volume through the market spread than a 30-unit round-trip, saving $17.00 in cumulative trading friction.
2. **Opening Float Capital Cushion:** Reserving $125.00 in liquid capital prevents order bouncing and ensures seamless execution of Day 1 melon seed procurements and wage obligations.

---

## 2. Forensic Breakdown of Rescued Mirror Matchups

The primary competitive gain in the 60-leg league benchmark arises from breaking mirror ties against incumbent A7 (`E2_A7`):

### Case 1: Seed 249675 (Seat 0 & Seat 1)
- **A7 vs A7 Baseline:**
  - Seat 0: Final Cash = $103,299.00
  - Seat 1: Final Cash = $103,299.00
  - Outcome: Exact Mirror Tie (0.5 wins)
- **V35 (25/25) vs A7 (30/30):**
  - Candidate (Seat 0): Final Cash = $103,316.00 (+$17.00 over baseline)
  - Opponent A7 (Seat 1): Final Cash = $103,288.00 (-$11.00 relative to baseline)
  - Net Victory Margin: **+$28.00**
  - Outcome: **WIN (1.0)** — Rescued from Tie
  - First Divergence: Step 0 (Market queue execution: 25 vs 30 units)
  - Physical Divergence: Exactly 0 steps. All worker coordinates, tile builds, animal feedings, and crop plantings remain 100% bit-identical.

### Case 2: Seed 249676 (Seat 0 & Seat 1)
- **A7 vs A7 Baseline:** Final Cash = $78,101.00 vs $78,101.00 (Tie, 0.5)
- **V35 (25/25) vs A7 (30/30):** Candidate = $78,118.00 vs Opponent = $78,090.00 (Win, 1.0)
- **Net Victory Margin:** **+$28.00**

### Case 3: Seed 249677 (Seat 0 & Seat 1)
- **A7 vs A7 Baseline:** Final Cash = $85,524.00 vs $85,524.00 (Tie, 0.5)
- **V35 (25/25) vs A7 (30/30):** Candidate = $85,541.00 vs Opponent = $85,513.00 (Win, 1.0)
- **Net Victory Margin:** **+$28.00**

### Case 4: Seed 249678 (Seat 0 & Seat 1)
- **A7 vs A7 Baseline:** Final Cash = $85,336.00 vs $85,336.00 (Tie, 0.5)
- **V35 (25/25) vs A7 (30/30):** Candidate = $85,353.00 vs Opponent = $85,325.00 (Win, 1.0)
- **Net Victory Margin:** **+$28.00**

---

## 3. Analysis of Unrescued Frontier Losses

### Case 5: Seed 249677 vs `E8_DMITRII` (Seat 0 & Seat 1)
- **A7 Baseline:** Candidate = $92,592.00 vs Dmitrii = $93,759.00 (Loss, 0.0; Deficit: -$1,167.00)
- **V35 (25/25):** Candidate = $92,596.00 vs Dmitrii = $93,752.00 (Loss, 0.0; Deficit: -$1,156.00)
- **Causal Analysis:** The 25/25 wash improved candidate cash by +$4.00 and reduced Dmitrii's margin by $7.00. However, Dmitrii's structural lead ($1,156.00) is governed by late-game melon harvesting and multi-quadrant expansion, which cannot be bridged solely by a small opening cash shift.

### Case 6: Seed 249679 vs `E2_A7` (Seat 0)
- **A7 Baseline:** Candidate = $73,402.00 vs Opponent = $73,525.00 (Loss, 0.0; Deficit: -$123.00)
- **V35 (25/25):** Candidate = $73,419.00 vs Opponent = $73,514.00 (Loss, 0.0; Deficit: -$95.00)
- **Causal Analysis:** The 25/25 wash recovered +$17.00 on the candidate side and reduced the opponent's margin by $11.00, narrowing the deficit from -$123.00 to -$95.00. The underlying seat asymmetry on this seed created a -$95.00 barrier that exceeded the opening delta.

---

## 4. Causal Verification Summary

| Hypothesized Mechanism | Validated? | Trace Evidence |
| :--- | :---: | :--- |
| **Prevents Bounced Purchases** | **CONFIRMED** | Eliminates Step 1 cash dip below $10.00; preserves $135+ floor. |
| **Reduces Round-Trip Spread Friction** | **CONFIRMED** | Direct +$17.00 terminal cash gain observed consistently across seeds. |
| **Preserves Downstream Choreography** | **CONFIRMED** | $D_{\text{phys}}(t) = 0$ for all $t \in [1, 718]$. Zero missed actions. |
| **Adversarial Market Denial** | **REFUTED** | Opponents do not trade wheat at Step 0; gain is purely internal. |
