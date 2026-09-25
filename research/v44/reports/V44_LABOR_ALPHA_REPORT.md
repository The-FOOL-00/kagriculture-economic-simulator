# V44 Labor Economics & Workforce Scaling Report

**Document ID:** `research/v44/reports/V44_LABOR_ALPHA_REPORT.md`  
**Date:** 2026-09-25  
**Repository:** `The-FOOL-00/kagriculture-economic-simulator`  
**Scope:** Systematic investigation of farm hand hiring curves, early workforce acceleration, and late-game hiring cutoffs across full terminal rollouts.

---

## 1. Executive Summary

In Kagriculture, farm hand hiring cost follows a Fibonacci progression based on the number of hands hired *on that specific day*:
$$\text{Cost}(n) = \text{mult} \cdot \text{Fib}(n)$$
where $\text{mult} = 1$, yielding costs of $1, $1, $2, $3, $5, $8, $13, $21, $34... per hire.

Because hiring costs reset each day (every 24 steps), A7 exploits this by hiring 3–5 hands at the start of almost every day, accumulating over 270 total hand-hire actions across a 720-step match.

In V44, we tested two fundamental labor hypotheses:
1. **`HIRE_EARLY_SURGE`:** Accelerating early hiring on Days 2 and 3 (Steps 24 and 48) to scale planting and watering throughput faster.
2. **`CAP_LATE_HIRING`:** Capping all hiring after Step 550 to prevent spending wages on workers who will only be active for the final 170 steps.

---

## 2. Experimental Data Table

| Candidate Strategy | Intervention Description | Mean Cash $\Delta$ | Median Cash $\Delta$ | Casualties | Rescues | Win Rate (%) | Verdict |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **`HIRE_EARLY_SURGE`** | Hire +2 hands at steps 24 & 48 | -$6.00 | -$8.00 | **0** | 0 | 91.7% | Slightly Sub-optimal |
| **`CAP_LATE_HIRING`** | Suppress all HIRE ops step $\ge 550$ | **-$7,076.92**| **-$5,337.00**| **14** | 0 | 33.3% | **REJECTED (Catastrophic)** |
| **`COMPOSITE_EARLY_SURGE`**| Early surge + V43 terminal flush | +$88.08 | +$49.00 | **0** | 1 | 95.8% | Safe, but dominated by Market Alpha |

---

## 3. Forensic Analysis: Why Late Hiring Cannot Be Capped

The catastrophic loss observed in `CAP_LATE_HIRING` (`-$7,076.92`, 14 casualties) reveals an essential mechanical property of Kagriculture:
1. In the late game (Steps 550–718), the farm has unlocked Quadrants 1, 2, and 3, containing dozens of ongoing tomato and strawberry crops, plus cows, sheep, and geese.
2. Hands perform discrete atomic tasks: watering, weeding, feeding animals, and harvesting.
3. Because the map spans a large grid, travel time reduces the effective productivity per hand.
4. Capping the workforce at Step 550 causes severe task congestion: mature strawberries rot on the vine, cows go unfed (halving milk yield), and shed inventory drops precipitously.
5. The marginal cost of hiring a few extra hands each day ($1–$5) is negligible compared to the loss of a single unharvested strawberry ($120) or milk ($160).

---

## 4. Final Strategic Conclusion

* **Do Not Restrict Hiring:** A7's daily Fibonacci hiring schedule is economically optimal and should remain untouched.
* **Labor is Not the Alpha Bottleneck:** The farm's labor capacity is already operating near saturation. Alpha must be sought in **Market Timing and Town Arbitrage**, not labor manipulation.
