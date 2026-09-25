# V32 P10 — COMPETITION BENCHMARK REPORT: MASTER COMPARISON & POLICY GAP
**Phase:** V32 P10  
**Date:** 2026-09-23  
**Status:** COMPLETE — MASTER BENCHMARK LOCKED  
**Author:** Kagriculture Autonomous Research Agent  

---

## 1. PRIMARY COMPARISON TABLE (§30 MASTER BENCHMARK)

The table below presents the master empirical comparison of all evaluated policies, wrappers, and residual candidates against the frozen reference incumbent (`A7`) across the standardized development panel:

| Policy | Mean Cash | Median Cash | P25 Cash | P75 Cash | Min Cash | W | L | T | Paired Δ vs A7 | Activations | Decision Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`A7` (Incumbent Control)** | **$104,661.07** | **$93,812.00** | **$75,250.00** | **$119,658.00** | **$59,603.00** | **108** | **2** | **10** | **$0.00 (ref)** | — | **PROTECTED INCUMBENT** |
| **`P10_BASELINE_WRAPPER`** | **$104,661.07** | **$93,812.00** | **$75,250.00** | **$119,658.00** | **$59,603.00** | **108** | **2** | **10** | **+$0.00** | 0 | **PASS (100% Exact Parity)** |
| **`R01` (Sell Preempt)** | $104,312.72 | $93,514.00 | $74,800.00 | $119,300.00 | $58,547.00 | 104 | 6 | 10 | **-$348.35** | 193 | **QUARANTINED (Regression)** |
| **`R02` (Glut Trim)** | $104,628.72 | $93,808.50 | $75,100.00 | $119,658.00 | $59,357.00 | 107 | 3 | 10 | **-$32.35** | 238 | **QUARANTINED (Regression)** |
| **`R02_B` (Opp-Glut Trim)** | $104,670.37 | $93,812.00 | $75,250.00 | $119,658.00 | $59,591.00 | 108 | 2 | 10 | **+$9.30\*** | 17 | **QUARANTINED (Tail Risk -\$489)** |
| **`R03` (Liquidity Guard)** | $104,661.07 | $93,812.00 | $75,250.00 | $119,658.00 | $59,603.00 | 108 | 2 | 10 | **+$0.00** | 40 | **QUARANTINED (Redundant)** |
| **`R05` (Labor Guard)** | $104,661.07 | $93,812.00 | $75,250.00 | $119,658.00 | $59,603.00 | 108 | 2 | 10 | **+$0.00** | 0 | **QUARANTINED (Redundant)** |
| **`R07` (Terminal Patch)** | $104,661.07 | $93,812.00 | $75,250.00 | $119,658.00 | $59,603.00 | 108 | 2 | 10 | **+$0.00** | 0 | **QUARANTINED (Redundant)** |

*\*Note on R02_B: While achieving +$9.30 on dev seeds, fresh-seed validation on seeds 249685–249694 produced an intolerable -$489.00 tail loss, failing Gate G4.*

---

## 2. HEAD-TO-HEAD OPPONENT BREAKDOWN (INCUMBENT A7 / P10-BASELINE)

```
========================================================================================
Opponent ID    Archetype           Legs   Mean Cash     Median Cash    Win%    Delta vs A7
----------------------------------------------------------------------------------------
E0_V3          Frozen Tape          20   $ 92,134.90   $ 84,601.50   100.0%    +$0.00
E1_V22R1       Live Slot A          20   $ 92,111.75   $ 84,593.00   100.0%    +$0.00
E2_A7          Mirror               20   $ 90,194.15   $ 89,175.00    50.0%    +$0.00
E8_DMITRII     MC Terminal Search   20   $ 91,501.00   $ 92,592.00    90.0%    +$0.00
V54            Declarative Ref      20   $ 98,324.55   $ 95,812.50   100.0%    +$0.00
SYN_AGG        Hostile Dumper       20   $163,700.05   $171,175.50   100.0%    +$0.00
----------------------------------------------------------------------------------------
OVERALL        Master Panel        120   $104,661.07   $ 93,812.00    90.0%    +$0.00
========================================================================================
```

---

## 3. BENCHMARK CONCLUSIONS

1. **A7 Remains the Unbeaten Competition Backbone:**
   - Outperforms `V22R1` (Slot A) by +$1,265.15 mean margin with 100% win rate (20-0).
   - Outperforms `V3` by +$1,286.00 mean margin with 100% win rate (20-0).
   - Defeats `E8_DMITRII` (2800+ LB frontier benchmark) with 90% win rate (18-2).
   - Crushes `V54` (+$19,916 margin) and `SYN_AGG` (+$160,700 margin).
2. **P10 Baseline Wrapper Fidelity:**
   - The P10 harness reproduces A7 down to the exact dollar across all 120 legs ($0.00 paired delta), confirming 100% wrapper safety.
3. **Residual Gating Verdict:**
   - Zero candidate residuals demonstrated robust, positive alpha without severe tail risk.
   - A7 represents the empirical performance ceiling among tested policy variants.
