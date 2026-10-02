# V32 P10 — DECISION REPORT: RESIDUAL SEARCH OUTCOME & FINAL COMPETITION RECOMMENDATION
**Phase:** V32 P10  
**Date:** 2026-09-23  
**Status:** FORMAL RESEARCH PHASE COMPLETE — DECISION LOCKED  
**Author:** Kagriculture Autonomous Research Agent  

---

## 1. PRIMARY CONCLUSION: SUCCESS B ACHIEVED

```text
========================================================================================
PRIMARY CONCLUSION:
SUCCESS B CONFIRMED — NO TESTED RESIDUAL PRODUCES ROBUST ALPHA WITHOUT UNACCEPTABLE TAIL RISK.

DEFENSIBLE SCIENTIFIC DECISION:
1. PERMANENTLY FREEZE A7 AS THE LIVE COMPETITION INCUMBENT.
2. PERMANENTLY QUARANTINE RESIDUALS R01, R02, R02_B, R03, R05, R07.
3. RETAIN SLOT B (A7) AND SLOT A (V22R1) IN LIVE PLAY. NO SPECULATIVE OVERRIDES.
========================================================================================
```

Phase V32 P10 conducted an exhaustive, simulator-backed search for sparse, opponent/regime-conditioned residual overrides on top of the frozen `A7` incumbent.

In strict adherence to the competition promotion protocol (§4, §13, §31, §33, §40):
- A positive mean delta on discovery seeds is **NOT** sufficient for promotion when accompanied by severe tail risk.
- Every candidate residual tested either directly caused economic regression (`R01`, `R02`), collapsed into severe negative tail loss upon exposure to fresh seeds (`R02_B`), or proved completely redundant with A7's built-in execution (`R03`, `R05`, `R07`).
- Per §40, **SUCCESS B** is formally achieved: strong, reproducible evidence that no tested residual produces meaningful robust alpha, establishing the definitive justification to **FREEZE A7**.

---

## 2. FORMAL ANSWERS TO THE 17 COMPETITION DECISION QUESTIONS (§41)

### Q1: Where does A7 actually lose money?
**Answer:** A7 loses money in two specific situations:
1. **Endgame Physical Asset Recovery vs Monte Carlo Searchers (Dmitrii Gap):** On rare seeds (e.g. Seed `249677`), Dmitrii's 128-simulation Monte Carlo terminal search extracts carried inventory and sweeps residual pasture goods in steps 712–718, producing a -$1,167.00 loss for A7.
2. **Adverse Market Price Drops:** When an opponent dumps 12–24 units of perishable goods (Melon/Milk) 1 step prior to A7's scheduled sales, A7 incurs negative price slippage ($400–$1,000 margin compression).

### Q2: Are those losses systematic?
**Answer: NO.**
Across the 100-leg benchmark screen, A7 achieved a **98.0% win rate** (98 Wins / 2 Losses / 0 Ties). Losses occurred exclusively on a single seed (`249677`) against `E8_DMITRII`. Against `E1_V22R1`, `E0_V3`, `V54`, and `SYN_AGG`, A7 maintained a **100.0% win rate** (80-0). The losses are seed/archetype-specific tail events, not systematic macro deficiencies.

### Q3: Can observable opponent behavior identify the relevant regime?
**Answer: YES.**
The deterministic regime detector successfully classified turns into `OPPONENT_SELL_PRESSURE` (86.7%), `LOW_LIQUIDITY_STRESS` (7.5%), and `TERMINAL_WINDOW` (1.25%) using purely observable state variables (market inventory velocity, opponent tile layouts, public cash trends).

### Q4: Which residual candidates were tested?
**Answer:** Six distinct candidate mechanisms:
1. `R01`: `OPPONENT_SELL_PREEMPT` (Preempting opponent sales)
2. `R02`: `MARKET_QUANTITY_ADJUST` (Trimming sales during high market inventory)
3. `R02_B`: `OPPONENT_GLUT_TRIM` (Opponent-specific dump deferral)
4. `R03`: `LIQUIDITY_PROTECTION` (Low-cash capital expenditure guard)
5. `R05`: `LOCAL_LABOR_PATCH` (Low-cash worker hiring throttle)
6. `R07`: `TERMINAL_LOCAL_PATCH` (Terminal shed residual liquidation)

### Q5: Which candidate had the best evidence?
**Answer: `R02_B` (Opponent-Glut Trim).**
On historical development seeds (`249675`–`249684`), `R02_B` demonstrated +$9.30 mean delta, +$12.40 on active legs, and a minimal worst-case of -$12.00, outperforming all other candidates.

### Q6: What was its paired improvement versus A7?
**Answer:**
- Historical Dev Seeds: **+$9.30** mean paired delta (+$12.40 on active legs).
- Fresh Dev Seeds: **+$11.10** mean paired delta (+$18.50 on active legs).

### Q7: What was its worst downside?
**Answer: -$489.00 (FATAL TAIL RISK).**
On fresh development seed `249687` against `E0_V3`, deferring a melon sale by 1 step caused farm cash to fall short of the $1,000 threshold required for the Day 6 Quadrant 2 land expansion. The delayed expansion cascade delayed planting across an entire 24-step cycle, permanently destroying **-$489.00** in terminal cash. Under adversarial threshold perturbation, the loss expanded to **-$959.00**.

### Q8: How often did it activate?
**Answer:**
- Historical Dev Panel: 17 activations across 20 legs (0.85 acts/leg).
- Fresh Dev Panel: 36 activations across 40 legs (0.90 acts/leg).

### Q9: How many false positives occurred?
**Answer:**
On fresh development seeds, 10 out of 24 activated legs (41.7%) produced negative paired deltas, directly contradicting the G5 robustness requirement ($\ge 60\%$ positive rate).

### Q10: Did it generalize across fresh seeds?
**Answer: NO.**
While the mean remained slightly positive (+11.10), the variance exploded, and the lower tail plunged from -$12.00 to -$489.00. The mechanism failed generalization.

### Q11: Did it generalize across opponents?
**Answer: NO.**
Against `E8_DMITRII`, the delta was flat ($0.00 across 90% of legs); gains occurred almost entirely against `E0_V3`, but so did the -$489.00 catastrophe.

### Q12: Did any two residuals interact negatively?
**Answer:** Not applicable. Multi-residual composition was formally blocked under §21 because zero candidates independently passed all gates.

### Q13: What residuals are permanently quarantined?
**Answer: ALL TESTED CANDIDATES ARE PERMANENTLY QUARANTINED:**
- `R01`: QUARANTINED (Regression -$348.35)
- `R02`: QUARANTINED (Regression -$32.35)
- `R02_B`: QUARANTINED (Catastrophic tail failure -$489.00 / -$959.00)
- `R03`: QUARANTINED (Redundant $0.00)
- `R05`: QUARANTINED (Redundant 0 activations)
- `R07`: QUARANTINED (Redundant 0 activations; A7 already liquidates 100% of shed)

### Q14: Does the best residual justify controlled live validation?
**Answer: NO (HARD NO-GO).**
A residual that exposes the incumbent to -$489 to -$959 tail losses on standard seeds fails Gate G4 and violates the cardinal competition rule: **"Never sacrifice the incumbent for upside."**

### Q15: Does A7 remain the incumbent?
**Answer: YES, ABSOLUTELY.**
A7 remains our protected, unbeaten competition champion ($104,661 mean cash, 98% panel win rate, +$1,265 alpha over V22R1, +$1,286 over V3).

### Q16: What is the exact remaining score gap that the research can still plausibly attack?
**Answer:**
The remaining gap on the development panel is **+$1,167.00 on Seed 249677 vs Dmitrii**. Closing this gap requires a true dynamic, closed-loop physical Monte Carlo path planner (such as Dmitrii's 128-simulation search) to sweep unharvested pasture/coop goods in steps 712–718. It cannot be resolved by market order tweaking.

### Q17: What should NOT be attempted before the competition deadline (2026-09-30)?
**Answer: MANDATORY PROHIBITION LIST (FINAL DAYS):**
- $\times$ Do NOT deploy any sales-deferral or market-batching heuristic (proven harmful in P9 and P10).
- $\times$ Do NOT attempt labor throttling.
- $\times$ Do NOT alter the Step-0 30/30 wheat wash opening.
- $\times$ Do NOT retrain neural models or reopen imitation learning.
- $\times$ Do NOT destabilize live Slot B (`A7`) with unvalidated micro-overrides.

---

## 3. MASTER QUARANTINE LEDGER (§38)

```
========================================================================================
ID     Hypothesis               Result       Failure Cause             Status
----------------------------------------------------------------------------------------
R01    Opponent Sell Preempt    -$348.35     Disrupts downstream chore QUARANTINED
                                             flow & depresses price
R02    Glut Sell Trimming       -$32.35      Strangles cash flow and   QUARANTINED
                                             strands shed inventory
R02_B  Opponent Dump Trim       -$489.00     Delayed land expansion    QUARANTINED
                                (Tail Loss)  cascading crop wipeout
R03    Low-Cash Discretionary   $0.00        A7 already avoids such    QUARANTINED (REDUNDANT)
       Expense Guard                         purchases natively
R05    Low-Cash Labor Throttle  0 acts       A7 never schedules        QUARANTINED (REDUNDANT)
                                             irrational hires
R07    Terminal Residual Shed   0 acts       A7 already liquidates     QUARANTINED (REDUNDANT)
       Liquidation                           100% of shed goods
========================================================================================
```

---

## 4. FINAL COMPETITION SUBMISSION RECOMMENDATION

1. **Slot A:** Maintain **`V22R1`** (`submission_aec_v22r1.tar.gz`, Rating ~1880 Elo).
2. **Slot B:** Maintain **`A7`** (`candidates/v30_a7_standalone/main.py`, Rating ~1859 Elo, +$1,286 proven alpha over V3).
3. **Production Candidate (`candidates/v32_hmeh_release/main.py`):** Holds exact bit-for-bit parity with A7 wrapped in defensive legality guards. Ready as a 1-to-1 drop-in replacement if Slot B exhibits runtime drift.
4. **All Holdouts (`214200–214249`, `340090–340199`, `249695–249734`):** **100% VIRGIN & UNTOUCHED**.
5. **Program Status:** **V32 RESEARCH PROGRAM COMPLETE & LOCKED FOR COMPETITION FREEZE**.
