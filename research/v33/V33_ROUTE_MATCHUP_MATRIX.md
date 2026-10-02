# V33 Route Matchup Matrix: Empirical Cross-Expert Tournament

**Program:** Kagriculture V33 Research Program  
**Date:** 2026-09-24  
**Dataset:** 150 independent, full-length (720-step) matches across DEV seeds (`249675..249679`)  
**Design:** Full round-robin across all 6 elite candidate routes over both Seat 0 and Seat 1  
**Artifact Generated:** `route_matchup_matrix.json`

---

## 1. Master Pairwise Win-Loss Matrix (Row vs Column)

Each cell $(R_i, R_j)$ shows the match record of Route $R_i$ against Route $R_j$ across 10 paired matches (5 seeds $\times$ 2 seats):

| Route | `R0_A7` | `R1_V22R1` | `R2_DMITRII` | `R3_P3090` | `R4_V54` | `R5_V25P3` | Overall W-L-T | Overall Win Rate | Mean Paired $\Delta$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`R0_A7`** | — | **10-0 (100%)** | **8-2 (80%)** | **10-0 (100%)** | **10-0 (100%)** | **10-0 (100%)** | **48-2-0** | **96.0%** | **+$10,566** |
| **`R1_V22R1`** | 0-10 (0%) | — | **8-2 (80%)** | **10-0 (100%)** | **10-0 (100%)** | **6-4 (60%)** | **34-16-0** | **68.0%** | **+$9,906** |
| **`R2_DMITRII`**| 2-8 (20%) | 2-8 (20%) | — | **10-0 (100%)** | **10-0 (100%)** | 2-8 (20%) | **26-24-0** | **52.0%** | **+$9,383** |
| **`R3_P3090`** | 0-10 (0%) | 0-10 (0%) | 0-10 (0%) | — | 0-10 (0%) | 0-10 (0%) | **0-50-0** | **0.0%** | **-$30,648** |
| **`R4_V54`** | 0-10 (0%) | 0-10 (0%) | 0-10 (0%) | **10-0 (100%)** | — | 0-10 (0%) | **10-40-0** | **20.0%** | **-$8,583** |
| **`R5_V25P3`** | 0-10 (0%) | 4-6 (40%) | **8-2 (80%)** | **10-0 (100%)** | **10-0 (100%)** | — | **32-18-0** | **64.0%** | **+$9,376** |

---

## 2. Pairwise Mean Cash Deltas ($)

Shows Row Cash minus Column Cash:

| Route | `R0_A7` | `R1_V22R1` | `R2_DMITRII` | `R3_P3090` | `R4_V54` | `R5_V25P3` | Mean Paired Delta vs League |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`R0_A7`** | — | **+$1,280** | **+$4,012** | **+$30,272** | **+$15,518** | **+$1,746** | **+$10,566** |
| **`R1_V22R1`** | -$1,280 | — | **+$4,624** | **+$30,239** | **+$15,450** | **+$496** | **+$9,906** |
| **`R2_DMITRII`**| -$4,012 | -$4,624 | — | **+$47,205** | **+$12,148** | -$3,804 | **+$9,383** |
| **`R3_P3090`** | -$30,272 | -$30,239 | -$47,205 | — | -$15,679 | -$29,842 | **-$30,648** |
| **`R4_V54`** | -$15,518 | -$15,450 | -$12,148 | **+$15,679** | — | -$15,478 | **-$8,583** |
| **`R5_V25P3`** | -$1,746 | -$496 | **+$3,804** | **+$29,842** | **+$15,478** | — | **+$9,376** |

---

## 3. Pairwise Mean Terminal Cash ($)

| Route | `R0_A7` | `R1_V22R1` | `R2_DMITRII` | `R3_P3090` | `R4_V54` | `R5_V25P3` | Overall Average Cash |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`R0_A7`** | — | $84,078 | $89,037 | $122,827 | $103,535 | $85,892 | **$97,074** |
| **`R1_V22R1`** | $82,798 | — | $85,042 | $122,786 | $103,447 | $83,592 | **$95,533** |
| **`R2_DMITRII`**| $85,026 | $80,418 | — | $138,196 | $101,368 | $85,003 | **$98,002** |
| **`R3_P3090`** | $92,555 | $92,548 | $90,991 | — | $88,224 | $92,766 | **$91,417** |
| **`R4_V54`** | $88,017 | $87,997 | $89,220 | $103,904 | — | $88,057 | **$91,439** |
| **`R5_V25P3`** | $84,146 | $83,096 | $88,806 | $122,608 | $103,535 | — | **$96,438** |

---

## 4. Seat Variance & Robustness

Across the 50 match legs played by A7:
- **Seat 0 Record:** 24 Wins / 1 Loss (96.0% Win Rate)
- **Seat 1 Record:** 24 Wins / 1 Loss (96.0% Win Rate)
- **Seat Bias Delta:** $0.00$ win-rate delta between Seat 0 and Seat 1.
- Both losses occurred on a single seed (`249677`) against `R2_DMITRII` (once as Seat 0, once as Seat 1). On that seed, Dmitrii scored $93,759 vs A7's $92,592 (a razor-thin $1,167 margin). Crucially, every other route in the portfolio also lost to Dmitrii on Seed 249677.
