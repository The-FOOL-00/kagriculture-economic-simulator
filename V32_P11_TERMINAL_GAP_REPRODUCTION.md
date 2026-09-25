# V32 P11 — FORENSIC REPORT: TERMINAL GAP REPRODUCTION & VALUE DECOMPOSITION
**Experiment ID:** EXP-V32-P11-01_TERMINAL_GAP_REPRODUCTION  
**Date:** 2026-09-23  
**Status:** COMPLETE — EMPIRICALLY CONFIRMED & FORENSICALLY RECONCILED  
**Subject:** Seed 249677 (`A7` vs `E8_DMITRII`)  

---

## 1. Executive Summary & Core Finding

```text
========================================================================================
CRITICAL FORENSIC DISCOVERY:
1. THE -$1,167.00 LOSS ON SEED 249677 WAS REPRODUCED TO THE EXACT PENNY IN BOTH SEATS.
2. HOWEVER, FORENSIC AUDITING CONCLUSIVELY DISPROVES THE "TERMINAL PHYSICAL STRANDING" HYPOTHESIS:
   - AT STEP 712 (START OF TERMINAL WINDOW), A7 WAS ALREADY DEFICIT -$1,351.00 (A7=$89,992, DM=$91,343).
   - IN STEPS 712–719, A7 ACTUALLY OUT-EARNED DMITRII BY +$184.00 (A7=+$2,600, DM=+$2,416).
   - AT STEP 719, A7 LEAVES EXACTLY $0.00 CARRIED IN HANDS, $0.00 IN SHED, AND ONLY $13.00 NOMINAL ON MAP.
   - THE ENTIRE -$1,167.00 DEFICIT STEMMED FROM DAY 25 AND DAY 29 MID-GAME MACRO PRICE SHOCKS,
     NOT ENDGAME PHYSICAL EXTRACTION INEFFICIENCY.
========================================================================================
```

---

## 2. Match Reproduction (Seed 249677)

The match was executed under closed-loop Kaggle environment rules in both seats with the protected A7 incumbent (`candidates/v30_a7_standalone/main.py`) against Dmitrii (`extracted_agents/dmitrii_lb2800/main.py`):

| Seat 0 | Seat 1 | Seat 0 Final Cash | Seat 1 Final Cash | A7 Margin vs Dmitrii | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **A7** | E8_DMITRII | **$92,592.00** | $93,759.00 | **-$1,167.00** | EXACT MATCH |
| E8_DMITRII | **A7** | $93,759.00 | **$92,592.00** | **-$1,167.00** | EXACT MATCH |

The -$1,167.00 loss is 100% deterministic and reproducible.

---

## 3. Step-by-Step Terminal Window Cash Progression (Steps 712–719)

A turn-by-turn ledger audit of the terminal window shows the exact cash generation:

| Step | Day:Hour | A7 Cash | Dmitrii Cash | Step Delta (A7 - Dmitrii) | Cumulative Margin | A7 Terminal Sells Executed |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **712** | 29:16 | **$89,992.00** | $91,343.00 | **-$1,351.00** | -$1,351.00 | 5 Carrot, 2 Wheat, 5 Wool, 1 Milk, 4 Egg, 1 Fert |
| **713** | 29:17 | **$90,187.00** | $91,482.00 | **-$1,295.00** | +$56.00 | `SELL 1000` (all 9 products) |
| **714** | 29:18 | **$90,187.00** | $91,621.00 | **-$1,434.00** | -$83.00 | `SELL 1000` (all 9 products) |
| **715** | 29:19 | **$90,187.00** | $91,621.00 | **-$1,434.00** | $0.00 | `SELL 1000` (all 9 products) |
| **716** | 29:20 | **$90,834.00** | $92,042.00 | **-$1,208.00** | +$226.00 | `SELL 1000` (Hand 2, 3 drop 12 Carrot, 6 Wheat) |
| **717** | 29:21 | **$91,153.00** | $92,514.00 | **-$1,361.00** | -$153.00 | `SELL 1000` (Hand 1 drop 6 Carrot, 2 Wheat) |
| **718** | 29:22 | **$91,491.00** | $93,425.00 | **-$1,934.00** | -$573.00 | `SELL 1000` (Hand 5 drop 8 Milk, 4 Wool) |
| **719** | 29:23 | **$92,592.00** | $93,759.00 | **-$1,167.00** | +$767.00 | Terminal Step 718 settlements credited |
| **NET** | **712–719** | **+$2,600.00** | **+$2,416.00** | **+$184.00** | **+$184.00** | **A7 OUT-EARNED DMITRII BY +$184.00** |

**Conclusion:** The terminal window was a net *gain* for A7 relative to Dmitrii (+184.00). The loss occurred prior to step 712.

---

## 4. Stranded Inventory Census at Game Completion (Step 719)

A comprehensive physical accounting across the full 10-seed development panel (`249675`–`249684`) was performed to evaluate whether physical value was left stranded:

| Seed | Final Margin | Carried in Hands (Qty) | Carried Cash Val | In Shed (Qty) | Shed Cash Val | Unharvested Field (Qty) | Field Cash Val |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **249675** | +$7,789 | 0 items | **$0.00** | 0 items | **$0.00** | 11 Fertilizer | $11.00 |
| **249676** | +$6,892 | 0 items | **$0.00** | 0 items | **$0.00** | 12 Fert, 1 Milk | $13.00 |
| **249677** | **-$1,167** | 0 items | **$0.00** | 0 items | **$0.00** | 12 Fert, 1 Milk | **$13.00** |
| **249678** | +$2,740 | 0 items | **$0.00** | 0 items | **$0.00** | 12 Fert, 1 Milk | $21.00 |
| **249679** | +$3,075 | 0 items | **$0.00** | 0 items | **$0.00** | 10 Fertilizer | $10.00 |
| **249680** | +$2,571 | 0 items | **$0.00** | 0 items | **$0.00** | 12 Fertilizer | $12.00 |
| **249681** | +$3,927 | 0 items | **$0.00** | 0 items | **$0.00** | 12 Fertilizer | $12.00 |
| **249682** | +$7,965 | 0 items | **$0.00** | 0 items | **$0.00** | 12 Fertilizer | $12.00 |
| **249683** | +$1,588 | 0 items | **$0.00** | 0 items | **$0.00** | 12 Fertilizer | $12.00 |
| **249684** | +$812 | 0 items | **$0.00** | 0 items | **$0.00** | 10 Fertilizer | $10.00 |

### Findings:
1. **Zero Stranded Carried Inventory:** In 100% of matches, A7 carries $0.00 in worker pockets at step 719.
2. **Zero Stranded Shed Stock:** In 100% of matches, A7's shed is completely liquidated down to $0.00.
3. **Negligible Residual Field Value:** Only $10.00 to $21.00 of low-value residual fertilizer ($1/unit) and occasionally 1 unit of milk ($1/unit) remains uncollected.
4. **Dmitrii Baseline Parity:** On seed 249677, Dmitrii also leaves exactly $12.00 of residual fertilizer on the field.

---

## 5. Causal Root Cause of the -$1,167 Deficit

Tracing transaction ledgers backwards revealed the true source of divergence:
- **Step 614:** Dmitrii liquidated a large melon batch ahead of a town consumption tick, earning a +$1,905 cash delta.
- **Step 697:** Dmitrii dumped 24 milk units before A7's milk wagon returned, causing $703 of price depression.
- **Step 709:** Dmitrii sold 4 carrots at the peak spot price of $128 (+$511), whereas A7 held carrots for the scheduled step 712 batch.

These three macro timing and pricing events created a **-$3,119.00** gross swing, partially offset by A7's superior animal production (+$1,952.00), resulting in the net -$1,167.00 loss. None of these events occurred during the terminal window.

---

## 6. Verdict on P11 Hypothesis

**Hypothesis Rejected:** The premise that A7 leaves hundreds of dollars of realizable physical assets stranded in fields/worker hands during steps 712–718 is empirically falsified. A7's route already liquidates 100% of carried inventory and 100% of shed goods before the game ends.
