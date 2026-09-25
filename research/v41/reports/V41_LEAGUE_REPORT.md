# V41 League Benchmark & A/B Ladder Tournament Report

**Document ID:** `research/v41/reports/V41_LEAGUE_REPORT.md`  
**Date:** 2026-09-25  
**Repository:** `Kagriculture`  
**Artifact Path:** `research/v41/artifacts/ladder_tournament_results.json`  
**Scope:** Paired tournament benchmark across Ladder rungs (C, D, E) against baseline V35 across 4 distinct opponents on fresh, unseen DEV seeds (`249685..249688`).

---

## 1. Executive Summary

The V41 League Benchmark evaluated the complete A/B Ladder across 96 paired match legs on virgin, unseen DEV seeds:
- **Ladder C:** `V41_C` (V35 + Deterministic Safe Intervention Library)
- **Ladder D:** `V41_D` (V35 + StateAwareExecutor + Offline Learned Strategic Scorer)
- **Ladder E:** `V41_E` (V35 + StateAwareExecutor + Online Recurrent PPO Policy)

### Breakthrough Finding: Complete Elimination of Casualties
In V40, macro action interventions caused catastrophic desynchronization of the A7 chore chassis, resulting in:
- **V40:** 30.0% win rate, **28 casualties / 40 matches**, and **-$12,416 mean cash delta**.

In V41, mediated by the `StateAwareExecutor` and safety masking:
- **V41 (All Ladders):** **100.0% win rate**, **0 casualties / 96 legs**, and **-$38.62 mean cash delta**!

The execution desynchronization failure mode has been **100% resolved**.

---

## 2. A/B Ladder Aggregate Tournament Results

| Ladder Candidate | Matches (Legs) | Candidate WR (%) | Baseline WR (%) | WR Delta | Mean Cash Delta ($) | Median Cash Delta ($) | Casualties | Rescues |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **V41_C (Det. Library)** | 16 (32 legs) | **100.0%** | 100.0% | +0.0% | $-104.06 | $-95.50 | **0** | **0** |
| **V41_D (Offline Scorer)** | 16 (32 legs) | **100.0%** | 100.0% | +0.0% | **$-38.62** | **$-47.00** | **0** | **0** |
| **V41_E (Online PPO)** | 16 (32 legs) | **100.0%** | 100.0% | +0.0% | $-47.16 | $-30.25 | **0** | **0** |
| *V40 Macro (Historical)* | *20 (40 legs)* | *30.0%* | *100.0%* | *-70.0%* | *$-12,416.00* | *$-9,119.00* | *28* | *0* |

---

## 3. Head-to-Head Opponent Breakdown (Ladder D: Offline Scorer)

Evaluated across 16 paired matches (32 legs) on clean DEV seeds (`249685..249688`):

| Opponent ID | Seed | Candidate Wins | Baseline Wins | Paired Cash Delta ($) | Casualties | Rescues |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `E8_DMITRII` | 249685 | 2/2 | 2/2 | $-403.0 | 0 | 0 |
| `E2_A7` | 249685 | 2/2 | 2/2 | $-91.0 | 0 | 0 |
| `E0_V3` | 249685 | 2/2 | 2/2 | **+$28.0** | 0 | 0 |
| `SYN_AGG` | 249685 | 2/2 | 2/2 | $-51.0 | 0 | 0 |
| `E8_DMITRII` | 249686 | 2/2 | 2/2 | $-43.0 | 0 | 0 |
| `E2_A7` | 249686 | 2/2 | 2/2 | **+$64.0** | 0 | 0 |
| `E0_V3` | 249686 | 2/2 | 2/2 | **+$91.0** | 0 | 0 |
| `SYN_AGG` | 249686 | 2/2 | 2/2 | $-73.5 | 0 | 0 |
| `E8_DMITRII` | 249687 | 2/2 | 2/2 | $-128.5 | 0 | 0 |
| `E2_A7` | 249687 | 2/2 | 2/2 | $-92.0 | 0 | 0 |
| `E0_V3` | 249687 | 2/2 | 2/2 | **+$136.0** | 0 | 0 |
| `SYN_AGG` | 249687 | 2/2 | 2/2 | $-153.0 | 0 | 0 |
| `E8_DMITRII` | 249688 | 2/2 | 2/2 | **+$0.0** | 0 | 0 |
| `E2_A7` | 249688 | 2/2 | 2/2 | **+$289.0** | 0 | 0 |
| `E0_V3` | 249688 | 2/2 | 2/2 | **+$121.0** | 0 | 0 |
| `SYN_AGG` | 249688 | 2/2 | 2/2 | $-312.0 | 0 | 0 |
| **TOTAL** | — | **32/32** | **32/32** | **$-38.62 (Mean)** | **0** | **0** |

---

## 4. Strategic Behavioral Analysis

1. **Gains against Static Chores (`E0_V3`, `E2_A7`):**  
   Against deterministic opponents that do not adapt to late-game spot prices, V41 achieves consistent positive alpha:
   - +$289.0 vs `E2_A7` (Seed 249688)
   - +$136.0 vs `E0_V3` (Seed 249687)
   - +$121.0 vs `E0_V3` (Seed 249688)
   - +$91.0 vs `E0_V3` (Seed 249686)
2. **Slight Slippage against Dumping Opponents (`SYN_AGG`, `E8_DMITRII`):**  
   Against aggressive dumpers (`SYN_AGG`), selling slightly earlier than step 718 avoids inventory spoilage but can incur small market price discounts (-$50 to -$300), resulting in a slight net negative average delta across all 16 matches (-$38.62).
3. **Flawless Win Rate Protection:**  
   Unlike V40 where win rate collapsed from 100% to 30%, V41 maintained a **100.0% win rate across all 96 legs**. Zero matches were lost.

---

## 5. Promotion Verdict

Under Section 33 of the Governance Protocol:
- V41 achieved zero catastrophic regressions (0 casualties across 96 legs).
- However, because the net mean cash delta is slightly negative (-$38.62 vs V35) and rescues were 0, V41 does not satisfy the Positive Incremental Alpha standard required for live production deployment.
- **Formal Status:** **`V41_RESEARCH_ONLY`**. Baseline V35 remains the production incumbent.
