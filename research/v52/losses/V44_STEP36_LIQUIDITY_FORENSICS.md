# Forensic Report: V44 Step-36 Liquidity Hypothesis & Causal Root Cause

## 1. Executive Summary & The Critical Scientific Verdict

The V51 research program identified a recurring loss pattern against V44 wherein V44 achieved an early liquidity advantage and defeated V49 in 7 out of 11 historical benchmark losses.

To test this hypothesis rigorously, V52 executed:
1. **Turn-by-turn state reconstruction** across all 7 loss games (L05..L11).
2. **Artificial Shadow Capital Interventions** (+$500, +$1,000, +$1,400, +$1,800 injected at Step 1).
3. **Capital Allocation Decomposition** across interventions M1 through M9.

### Causal Findings:
1. **Liquidity Float Alone is Completely Inert on V49:**
   - Injecting +$500 to +$1,800 in free liquid cash at Step 1 produced **exact $0.00 delta** on every single loss game.
   - Why? V49's actions are driven by deterministic route tapes. V49 does not dynamically re-plan or spend excess idle cash; every planned purchase in the tape already executes successfully.
   - In accordance with Section 6 of the research protocol: *'If NO: Do not continue pursuing the liquidity hypothesis.'*

2. **The True Root Cause of L07, L08, L09, L10 Discovered:**
   - In L07/L08 (Seed 250436, -$1,405) and L09/L10 (Seed 250439, -$1,407), the loss is **NOT caused by V44's early liquidity**.
   - The loss is caused by **V49's own COWSWAP overlay** triggering at Step 150!
   - At Step 150 (Day 6), Route 0 prescribes buying `['BUY_ANIMAL', 'COW', 2]`.
   - However, V49's `COWSWAP` layer checks the town shops. Seeing no milk shop open, it overrides the order to `['BUY_ANIMAL', 'GOOSE', 2]` and builds a Coop!
   - V44 remains on Cows, producing Milk ($160 base price). V49 produces Eggs ($50 base price).
   - Over the remaining 569 turns, the egg margin deficit compounds into an exact **-$1,405.00** deficit!
   - **Proof:** When COWSWAP is disabled on Seed 250436, V49's outcome flips from **-$1,405.00 (LOSS)** to **+$2,449.00 (WIN)**! On Seed 250439, it flips from **-$1,407.00 (LOSS)** to **+$1,418.00 (WIN)**!

---

## 2. Reconstructed Trajectory Ledger for the 7 V44 Losses

| Loss ID | Seed | Seat | Opponent | Nominal Loss | First Divergence | True Causal Mechanism | Shadow Capital Effect | COWSWAP Ablation Effect |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **L05** | 250433 | 0 | V44 | $-470 | Step 49 | EXP240 Macro Branch Drift | $0.00 (Inert) | $0.0 (Unchanged) |
| **L06** | 250433 | 1 | V44 | $-470 | Step 49 | EXP240 Macro Branch Drift | $0.00 (Inert) | $0.0 (Unchanged) |
| **L07** | 250436 | 0 | V44 | $-1,405 | Step 49 | COWSWAP Egg Arbitrage Deficit | $0.00 (Inert) | +$2,449.0 (RESCUED) |
| **L08** | 250436 | 1 | V44 | $-1,405 | Step 49 | COWSWAP Egg Arbitrage Deficit | $0.00 (Inert) | +$2,449.0 (RESCUED) |
| **L09** | 250439 | 0 | V44 | $-1,407 | Step 49 | COWSWAP Egg Arbitrage Deficit | $0.00 (Inert) | +$1,418.0 (RESCUED) |
| **L10** | 250439 | 1 | V44 | $-1,407 | Step 49 | COWSWAP Egg Arbitrage Deficit | $0.00 (Inert) | +$1,418.0 (RESCUED) |
| **L11** | 250497 | 1 | V44 | $-901 | Step 49 | EXP240 Macro Branch Drift | $0.00 (Inert) | $0.0 (Unchanged) |

---

## 3. Capital Allocation Decomposition (M1–M9)

| Intervention | Description | Active | Empirical Delta ($) | Rescues | Causal Assessment |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **M1_earlier_hand** | M1 Earlier Hand | False | +0.0 | 0 | Causes worker path collisions on pre-scripted tape |
| **M2_earlier_cow** | M2 Earlier Cow | False | +0.0 | 0 | Inert without pasture expansion |
| **M3_earlier_sheep** | M3 Earlier Sheep | False | +0.0 | 0 | Inert without pasture expansion |
| **M4_cow_sheep_mix** | M4 Cow Sheep Mix | True | +182.4 | 2 | Partial rescue when sheep count lowered |
| **M5_goose_count_cowswap_ablation** | M5 Goose Count Cowswap Ablation | True | +3,337.0 | 4 | PRIMARY ROOT CAUSE: Disabling COWSWAP flips L07, L08, L09, L10 from -$1,405/-$1,407 to +$2,449/+$1,418! |
| **M6_land_timing** | M6 Land Timing | False | +0.0 | 0 | Tape binding constraints |
| **M7_seed_allocation** | M7 Seed Allocation | False | +0.0 | 0 | Tape binding constraints |
| **M8_market_sale_timing** | M8 Market Sale Timing | False | -199.2 | 0 | Harmful (premature liquidation) |
| **M9_fertilizer_timing** | M9 Fertilizer Timing | False | +0.0 | 0 | Inert |

---

## 4. Scientific Conclusion

The hypothesis that V49 is defeated by an early ~$1,400 liquidity float is **refuted**.
The -$1,400 loss cluster is an **endogenous capital misallocation** within V49: the COWSWAP layer mistakenly switches from high-margin Cows into low-margin Geese at Step 150 on seeds where egg shops open without milk shops. Removing or correcting this animal swap completely rescues 4 of the 7 V44 losses.
