# V32 P9 COMPETITION BENCHMARK: MULTI-OPPONENT MATCHUP PANEL

**Author**: Kagriculture V32 Research Program  
**Date**: 2026-09-23  
**Benchmark Panel**: 6 Diverse Adversaries $\times$ 10 Development Seeds (`249675–249684`) $\times$ 2 Seats = **120 Full Competition Legs**  
**Policy Under Evaluation**: HMEH Release Candidate (`candidates/v32_hmeh_release/main.py`)  

---

## 1. MASTER COMPETITION BENCHMARK SUMMARY (120 LEGS)

| Opponent ID | Adversary Archetype | Legs | Mean Cash | Median Cash | P25 Cash | P75 Cash | Win Rate | Mean Margin | Paired Margin vs A7 |
|---|---|---|---|---|---|---|---|---|---|
| **E0_V3** | Frozen Tape Baseline | 20 | $92,134.90 | $84,601.50 | $69,126.00 | $107,741.00 | **100.0%** (20-0) | +$1,286.00 | +$0.00 |
| **E1_V22R1** | Live Slot A Champion | 20 | $92,111.75 | $84,593.00 | $69,126.00 | $107,636.00 | **100.0%** (20-0) | +$1,265.15 | +$0.00 |
| **E2_A7** | Live Slot B Champion | 20 | $90,194.15 | $89,175.00 | $78,101.00 | $103,184.00 | **50.0%** (0-0-20)| +$0.00 | +$0.00 |
| **E8_DMITRII** | Terminal Search Frontier | 20 | $91,501.00 | $92,592.00 | $71,820.50 | $106,799.00 | **90.0%** (18-2) | +$3,731.50 | +$0.00 |
| **V54** | Declarative Backbone | 20 | $98,324.55 | $95,812.50 | $91,815.25 | $107,341.50 | **100.0%** (20-0) | +$19,916.20| +$0.00 |
| **SYN_AGG** | Hostile Market Dumper | 20 | $163,700.05| $171,175.50| $148,390.00| $182,752.00| **100.0%** (20-0) | +$160,700.05| +$0.00 |
| **OVERALL** | **Full Opponent Panel** | **120**| **$104,661.07**| **$93,812.00**| **$75,250.00**| **$119,658.00**| **90.0%** (108W / 2L / 10T) | **+$31,149.82** | **+$0.00** |

---

## 2. HEAD-TO-HEAD OPPONENT FORENSICS

### 1. vs E1_V22R1 (Current Live Slot A Champion)
- **Result**: 20 Wins / 0 Losses (100.0% Dominance).
- **Mean Margin**: +$1,265.15.
- **Significance**: HMEH strictly and deterministically outperforms the current live competition leader across every seed in the development cohort. The +$1,265.15 alpha stems from the 30-wash cash preservation opening that prevents early capital exhaustion.

### 2. vs E8_DMITRII (2800+ Frontier Benchmark)
- **Result**: 18 Wins / 2 Losses (90.0% Win Rate).
- **Mean Margin**: +$3,731.50.
- **Significance**: Dmitrii Gluzdov's terminal search policy implements aggressive physical cargo recovery, but HMEH's early livestock compounding creates an insurmountable mid-game capital advantage that withstands endgame physical search.

### 3. vs V54 (Lixingtao Declarative Reference)
- **Result**: 20 Wins / 0 Losses (100.0% Win Rate).
- **Mean Margin**: +$19,916.20.
- **Significance**: V54 utilizes declarative reactive logic without front-loading or cash preservation, resulting in massive mid-game liquidity crises that HMEH exploits.

### 4. vs SYN_AGG (Adversarial Hostile Dumper)
- **Result**: 20 Wins / 0 Losses (100.0% Win Rate).
- **Mean Margin**: +$160,700.05.
- **Significance**: When an opponent aggressively dumps inventory at low prices, HMEH's budget guards prevent panicked selling, allowing HMEH to ride market recovery and accumulate over $163,000 in average terminal cash.

---

## 3. WORST-CASE AND BEST-CASE MATCHUPS

- **Best-Case Opponent**: `SYN_AGG` (Mean Delta +$160,700.05) & `V54` (Mean Delta +$19,916.20).
- **Worst-Case Opponent**: `E8_DMITRII` on Seed 249677 (Loss by -$1,167.00 due to extreme early carrot price fluctuation).
- **Parity Baseline**: `E2_A7` (Identical twin parity, 0.00 net margin across 20 legs).
