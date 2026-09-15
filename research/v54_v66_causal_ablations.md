# Macro Intervention Ablations Report (Section 6)

Evaluates V54-derived variants isolating each macro difference from V66.
Evaluated across 20 common seeds (101-120) with symmetric seats vs IDLE (solo) and vs canonical V54.

| Variant | Mechanism | Solo Delta vs V54 | Competitive Margin vs V54 | 95% Bootstrap CI | Win Rate | Classification |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **A1** | A1: Batch Seed Schedule | $-1,759 | $-539 | [$-614, $-406] | 5.0% | **NEGATIVE** |
| **A2** | A2: Step 0 Wheat Front-Run | $-1,218 | $-170 | [$-185, $-156] | 0.0% | **NEGATIVE** |
| **A3** | A3: Strawberry Seed Trim (_v60_seed_trim) | $-1,159 | $+0 | [$+0, $+0] | 0.0% | **NEUTRAL / MINOR** |
| **A4** | A4: Day 2 Cow Buy Timing | $-2,466 | $-2,948 | [$-3,981, $-2,079] | 0.0% | **NEGATIVE** |
| **A7** | A7: Shed Guard (_v60_shed_guard) | $-1,159 | $+0 | [$+0, $+0] | 0.0% | **NEUTRAL / MINOR** |
| **A8** | A8: Terminal Schedule (_route_loaded_units + market) | $-879 | $+6 | [$+6, $+6] | 100.0% | **NEUTRAL / MINOR** |
| **A_BACKBONE** | A_BACKBONE: Full V56 Backbone Route (e103819410) | $-3,368 | $+714 | [$+426, $+1,022] | 80.0% | **CAUSAL IMPROVEMENT** |
