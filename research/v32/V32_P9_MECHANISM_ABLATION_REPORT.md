# V32 P9 MECHANISM ABLATION REPORT: CAUSAL ECONOMIC LADDER

**Author**: Kagriculture V32 Research Program  
**Date**: 2026-09-23  
**Panel**: 10 Development Seeds (`249675–249684`) $\times$ 2 Seats = 20 Paired Legs per Stage  
**Opponent**: `E0_V3` (Standard Benchmark Control)  

---

## 1. EXECUTIVE SUMMARY

The P9 research phase systematically evaluated five candidate economic mechanisms layered sequentially on top of the protected A7 baseline. Every stage was tested under paired random seeds and identical simulator conditions to ensure rigorous causal attribution:

```
A7 Baseline (Protected 30-Wash Control)
    ↓
HMEH-0: A7 Preservation + Legality / Executor Scaffold
    ↓
HMEH-1: HMEH-0 + Adaptive Labor Controller
    ↓
HMEH-2: HMEH-1 + Shop-Conditioned Production
    ↓
HMEH-3: HMEH-2 + Market-Aware Selling (Batching / Price Holds)
    ↓
HMEH-4: HMEH-3 + Terminal Liquidation Search
```

---

## 2. MASTER ABLATION LADDER RESULTS (20 PAIRED LEGS PER STAGE)

| Stage | Mechanism Tested | Mean Cash | Median Cash | P25 Cash | P75 Cash | Mean Margin vs V3 | Win Rate | Paired Margin vs A7 |
|---|---|---|---|---|---|---|---|---|
| **A7** | Protected Baseline (30-Wash) | $92,134.90 | $84,601.50 | $69,126.00 | $107,741.00 | +$1,286.00 | **100.0%** (20/20) | $0.00 |
| **HMEH-0** | Baseline Preservation + Safety | $92,134.90 | $84,601.50 | $69,126.00 | $107,741.00 | +$1,286.00 | **100.0%** (20/20) | **+$0.00** |
| **HMEH-1** | Adaptive Labor (Chore Backlog) | $90,278.50 | $84,395.50 | $71,363.25 | $94,798.00 | +$1,095.65 | **100.0%** (20/20) | -$1,856.40 |
| **HMEH-2** | Shop-Conditioned Production | $90,278.50 | $84,395.50 | $71,363.25 | $94,798.00 | +$1,095.65 | **100.0%** (20/20) | -$1,856.40 |
| **HMEH-3** | Market-Aware Selling (Batches) | $92,788.95 | $96,603.00 | $74,009.00 | $99,278.00 | -$1,302.80 | **10.0%** (2/20) | +$654.05* |
| **HMEH-4** | Terminal Liquidation Search | $92,788.95 | $96,603.00 | $74,009.00 | $99,278.00 | -$1,302.80 | **10.0%** (2/20) | +$654.05* |

*\*Note: In HMEH-3/4, gross median cash rose to $96,603, but win rate collapsed to 10% because delayed selling allowed the opponent to front-run sales and crush market prices (see §5).*

---

## 3. SEED-BY-SEED PAIRED DELTA: A7 vs HMEH-0

| Seed | Seat | A7 Terminal Cash | HMEH-0 Terminal Cash | Paired Delta | Match Status |
|---|---|---|---|---|---|
| 249675 | 0 | $59,603.00 | $59,603.00 | +$0.00 | Exact Parity |
| 249675 | 1 | $59,603.00 | $59,603.00 | +$0.00 | Exact Parity |
| 249676 | 0 | $80,884.00 | $80,884.00 | +$0.00 | Exact Parity |
| 249676 | 1 | $80,884.00 | $80,884.00 | +$0.00 | Exact Parity |
| 249677 | 0 | $142,499.00 | $142,499.00 | +$0.00 | Exact Parity |
| 249677 | 1 | $142,499.00 | $142,499.00 | +$0.00 | Exact Parity |
| 249678 | 0 | $66,200.00 | $66,200.00 | +$0.00 | Exact Parity |
| 249678 | 1 | $66,200.00 | $66,200.00 | +$0.00 | Exact Parity |
| 249679 | 0 | $71,274.00 | $71,274.00 | +$0.00 | Exact Parity |
| 249679 | 1 | $71,393.00 | $71,393.00 | +$0.00 | Exact Parity |
| 249680 | 0 | $107,741.00 | $107,741.00 | +$0.00 | Exact Parity |
| 249680 | 1 | $107,741.00 | $107,741.00 | +$0.00 | Exact Parity |
| 249681 | 0 | $88,319.00 | $88,319.00 | +$0.00 | Exact Parity |
| 249681 | 1 | $88,622.00 | $88,622.00 | +$0.00 | Exact Parity |
| 249682 | 0 | $69,126.00 | $69,126.00 | +$0.00 | Exact Parity |
| 249682 | 1 | $69,126.00 | $69,126.00 | +$0.00 | Exact Parity |
| 249683 | 0 | $96,756.00 | $96,756.00 | +$0.00 | Exact Parity |
| 249683 | 1 | $96,756.00 | $96,756.00 | +$0.00 | Exact Parity |
| 249684 | 0 | $138,736.00 | $138,736.00 | +$0.00 | Exact Parity |
| 249684 | 1 | $138,736.00 | $138,736.00 | +$0.00 | Exact Parity |

**Conclusion**: HMEH-0 passes Gate P9-02 with **100.0% exact bit-for-bit baseline fidelity**.

---

## 4. EXP-V32-P9-03: ADAPTIVE LABOR FORENSIC ANALYSIS

### Hypothesis
Static labor hiring schedules cause avoidable wage drain during low-activity periods.

### Counterfactual Experiment
Throttling daily hiring on Days 28–29 (step $\ge 672$) from 10 hands down to 4 hands (enough to service livestock):
- **Seed 249675**: Baseline = $59,603.00 $\to$ Throttled = $56,685.00 (**-$2,918.00**)
- **Seed 249676**: Baseline = $80,884.00 $\to$ Throttled = $78,788.00 (**-$2,096.00**)

### Root Cause
In Kaggle Environments, hands are hired on 1-day contracts expiring at hour 23. While no new crops can grow on Day 28–29, late-game hands perform massive parallel harvest sweeps across 10–20 mature plants and pastures, transporting cargo to the shed for liquidation. Throttling hands stranded valuable crops in the field, losing more revenue than the Fibonacci wage cost saved.

**Verdict**: **HYPOTHESIS REFUTED**. Static late-game hiring is economically productive; adaptive hiring throttles cause net capital regression.

---

## 5. EXP-V32-P9-05: MARKET-AWARE SELLING FORENSIC ANALYSIS

### Hypothesis
Batching sales into larger lots (18–24 units) and holding inventory when spot prices dip preserves market value and prevents slippage.

### Results
- Median cash increased from $84,601.50 to $96,603.00 (+14.2% gross revenue on favorable seeds).
- **Win Rate collapsed from 100.0% to 10.0% (2W / 18L)**.
- Mean margin dropped from +$1,286.00 to **-$1,302.80**.

### Causal Mechanism
Because the market clears orders sequentially and town consumption absorbs supply every 4 steps, holding inventory allowed the opponent to sell first at high spot prices. The opponent's sales depressed market prices right before HMEH's batched orders hit the market, resulting in severe negative slippage and opponent runaway scores.

**Verdict**: **HYPOTHESIS REFUTED**. Continuous immediate selling (`sell_lead: True`) is game-theoretically dominant over inventory holding in 2-player closed-loop play.

---

## 6. EXP-V32-P9-06: TERMINAL LIQUIDATION AUDIT

### Hypothesis
A bounded terminal search at steps 712–718 will recover stranded inventory from the shed and fields.

### Physical Inventory Audit at Step 718 (A7 Baseline)
- **Shed Cargo**: 0 units across all 10 seeds (100.0% liquidated).
- **Hand Cargo**: 0 units across all 10 seeds (100.0% deposited).
- **Unharvested Board Yield**: 0 to 1 unit (immature late crops).

**Verdict**: A7's built-in terminal liquidation already liquidates 99.9% of reachable assets. Additional search yields negligible incremental value.
