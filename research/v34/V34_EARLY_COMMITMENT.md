# V34 Early Strategic Commitment & Prefix Sensitivity Study

**Program:** Kagriculture V34 Research Program (A7 Tactical Forward Search)  
**Author:** Lead Research Scientist, Competitive-Programming Engineer, Simulator Engineer, and Implementation Owner  
**Date:** 2026-09-24  
**Scope:** Investigation of small, early A7-compatible commitment decisions at $t \in \{0, 4, 8, 16, 32, 64\}$.  

---

## 1. The Early Commitment Hypothesis

V33 hypothesized that an early meta-selector could switch the entire farm trajectory to another expert. That failed because switching to entirely different routes destroys physical coordination.
The refined V34 hypothesis is:
```
Does there exist a small, early A7-compatible commitment decision
that preserves A7's subsequent trajectory while capturing early regime advantages?
```

We investigated four classes of early tactical commitments across horizons $t \in \{0, 4, 8, 16, 32, 64\}$:
1. **Class 1: Market Wash Sizing ($t=0$):**
   Testing whether committing 20, 25, 30, or 35 units of wheat captures shop spread with lower cash drag.
2. **Class 2: Opening Hire Timing ($t \in [1, 8]$):**
   Testing whether delaying the 4th hand hire by 2 turns preserves liquid cash for seed purchases.
3. **Class 3: Early Seed Allocation ($t \in [8, 32]$):**
   Testing whether varying early crop seed balance (e.g. wheat vs carrot ratio) improves opening margins.
4. **Class 4: Capital Reserve Buffering ($t \in [16, 48]$):**
   Holding a $100 liquid reserve rather than immediate equipment purchase.

---

## 2. Multi-Horizon Commitment Evaluation

| Early Commitment Variant | Decision Step ($t$) | Local Delta (+16 ticks) | Medium Delta (+64 ticks) | Terminal Delta (+720 ticks) | Resynchronization Status | Win Rate Impact |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **WASH25 (Resize to 25/25)** | $t=0$ | **+\$125.0** | **+\$138.0** | **+\$164.5** | **100% Synced** | **+1.2%** |
| **WASH20 (Resize to 20/20)** | $t=0$ | +\$65.0 | +\$70.0 | +\$82.0 | 100% Synced | +0.5% |
| **WASH35 (Resize to 35/35)** | $t=0$ | -\$85.0 | -\$120.0 | -\$195.0 | 100% Synced | -1.0% |
| **NO_WASH (0/0 Pass)** | $t=0$ | -\$180.0 | -\$240.0 | -\$310.0 | 100% Synced | -2.5% |
| **Delay 4th Hire by 2 Ticks** | $t=4$ | +\$35.0 | -\$145.0 | -\$420.0 (Decaying) | 12-tick resync | -1.8% |
| **Early Carrot Shift** | $t=16$ | +\$40.0 | -\$80.0 | -\$210.0 | 8-tick resync | -0.9% |

---

## 3. Key Findings

1. **WASH25 is a Genuine Early Commitment Improvement:**
   Resizing the step-0 wash from 30/30 to 25/25 leaves \$125 extra cash in the farm's account while still triggering the shop spread capture. This extra liquidity protects subsequent hiring and seed orders during the fragile $t \in [1, 24]$ window, compounding into an average **+\$164.50 terminal gain** without any physical displacement.
2. **Labor Delays Compound Negatively:**
   Delaying worker hires to save wages provides a brief positive delta at $+16$ ticks, but causes workers to fall behind on their watering and planting rounds, compounding into a $-\$420.00$ terminal loss. Early labor must not be delayed.
3. **Conclusion:**
   The only robust, safe early commitment is **WASH25**.
