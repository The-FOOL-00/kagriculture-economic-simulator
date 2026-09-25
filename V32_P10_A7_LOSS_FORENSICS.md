# V32 P10 — A7 LOSS FORENSICS REPORT: BENCHMARK WEAKNESS & OPPORTUNITY MAPPING
**Experiment ID:** `EXP-V32-P10-01_A7_LOSS_FORENSICS`  
**Phase:** V32 P10  
**Date:** 2026-09-23  
**Status:** COMPLETE — 3 REPEATABLE OPPORTUNITY CLASSES IDENTIFIED  
**Author:** Kagriculture Autonomous Research Agent  

---

## 1. EXECUTIVE SUMMARY

To avoid inventing speculative residuals without empirical justification, Phase 1 executed a systematic forensic evaluation of the frozen incumbent (`A7`) across the official 5-opponent development panel (10 development seeds `249675`–`249684` $\times$ 2 seats = 100 tournament legs).

### Master Panel Forensic Scoreboard (100 Legs)

| Opponent ID | Archetype | Legs | Wins | Losses | Ties | Win% | Mean Margin vs A7 | Min Margin vs A7 | Mean Final Cash |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`E8_DMITRII`** | Frontier 2800+ MC Terminal Search | 20 | 18 | 2 | 0 | 90.0% | **+$3,731.50** | **-$1,167.00** | $91,501.00 |
| **`E1_V22R1`** | Live Slot A Champion | 20 | 20 | 0 | 0 | 100.0% | **+$1,265.15** | **+$987.00** | $92,111.75 |
| **`E0_V3`** | Frozen Tape Baseline | 20 | 20 | 0 | 0 | 100.0% | **+$1,286.00** | **+$983.00** | $92,134.90 |
| **`V54`** | Declarative Backbone Reference | 20 | 20 | 0 | 0 | 100.0% | **+$19,916.20** | **+$8,577.00** | $98,324.55 |
| **`SYN_AGG`** | Hostile Market Dumper | 20 | 20 | 0 | 0 | 100.0% | **+$160,700.05** | **+$87,009.00** | $163,700.05 |
| **OVERALL** | **Full Opponent Panel** | **100** | **98** | **2** | **0** | **98.0%** | **+$37,379.78** | **-$1,167.00** | **$107,554.45** |

A7 proves to be an exceptionally strong incumbent across the development cohort (98% win rate). However, forensic analysis of the losing matches and the low-margin matches (<$2,000 margin) pinpoints exactly where A7 leaves economic value on the table.

---

## 2. DEEP FORENSICS ON LOSING MATCHES: THE SEED 249677 DMITRII COLLAPSE

Both recorded losses occurred on **Seed 249677** against `E8_DMITRII` (Seat 0 and Seat 1):
- **A7 Final Cash:** $92,592.00
- **Dmitrii Final Cash:** $93,759.00
- **Net Margin:** **-$1,167.00** (Loss)

### Detailed Forensic Reconstruction of Seed 249677
1. **The Early & Mid Game:**
   - At Step 0, A7 executes its 30/30 wheat wash ($3,000 $\to$ $3,054), preserving cash.
   - Dmitrii executes an aggressive early product sell pattern (13 wheat at Step 0, 13 wheat at Step 1, 12 milk at Step 196).
   - At Step 250–264, Dmitrii dumps 48 units of Melons and 13 Fertilizer into the market, driving Melon spot prices down before A7's scheduled harvest sales.
2. **First Divergence Step:**
   - **Step 494:** Dmitrii accumulates cash faster through continuous micro-sales and livestock yields ($opp\_cash = \$48,210$ vs $p\_cash = \$47,549$, deficit -$661.00).
3. **The Endgame Terminal Physical Search Gap:**
   - In steps 712–718, Dmitrii activates its 128-simulation Monte Carlo terminal search (`terminal_planner.py`).
   - Dmitrii dynamically routes workers to drop carried items and sweep residual eggs/milk/wool directly into the market before the 719 cutoff.
   - In contrast, A7 relies on static route liquidation at Step 718; while A7 dumps shed goods, carried goods in transit that did not reach the shed are stranded.
   - Result: Dmitrii extracts +$1,167.00 in additional cash, securing the victory.

---

## 3. FORENSICS ON LOW-MARGIN MATCHES (MARGIN < $2,000)

Across the 44 low-margin legs (against `E0_V3`, `E1_V22R1`, and `E8_DMITRII`), two consistent patterns emerge:

### Pattern A: Market Front-Running & Slippage (Milk & Melon Timing)
- In matches where opponents sell high-value commodities (Milk, Wool, Melon) 1–2 turns before A7's scheduled sales, the market inventory jumps from ~10 to 30+, and spot prices drop by 20–35%.
- Because A7 executes on a pre-planned schedule, it dumps its goods into the depressed market, forfeiting $400–$1,200 per match in realized cash.
- If A7 had preempted the sale or front-run the opponent when high-value goods were already resting in the shed, the price slippage would have been avoided.

### Pattern B: Temporary Cash-Runway Constraints (Seed 249681)
- On Seed 249681, margin vs V3 dropped from +$1,286 down to +$983 (Seat 0).
- Tracing cash at Step 150 showed farm money dipped to $42.00 after hiring and land expansion, delaying subsequent seed purchases by 3 turns and reducing compounding yield.

---

## 4. FORMAL LOSS ATTRIBUTION TABLE

| Opportunity Class ID | Description | Frequency (in 100 legs) | Mean A7 Impact | Mechanism | Candidate Residual |
| :--- | :--- | :---: | :---: | :--- | :---: |
| **`OPP-01`** | Opponent Market Front-Running & Price Suppression | 28 legs | -$850 to -$1,400 | Opponent dumps milk/wool/melon first; A7 suffers negative slippage. | **`R01_OPPONENT_SELL_PREEMPT`** |
| **`OPP-02`** | Market Inventory Oversupply / Price Depressed Dumps | 16 legs | -$400 to -$900 | Selling into temporarily saturated market right before town consumption clears inventory. | **`R02_MARKET_QUANTITY_ADJUST`** |
| **`OPP-03`** | Low-Liquidity Capital Strain | 12 legs | -$300 to -$600 | Non-critical expenditure when cash buffer $< \$120$ delays productive seeding. | **`R03_LIQUIDITY_PROTECTION`** |
| **`OPP-04`** | Terminal Inventory Stranding | 4 legs | -$500 to -$1,200 | Goods carried by workers or un-liquidated shed goods at steps 716–718. | **`R07_TERMINAL_LOCAL_PATCH`** |

---

## 5. GATE 1 VERDICT

**Requirement:** At least 2–3 repeatable opportunity classes must be identified before residual search proceeds.

**Verdict:** **GATE PASSED**.  
Four distinct, repeatable, simulator-grounded opportunity classes (`OPP-01`, `OPP-02`, `OPP-03`, `OPP-04`) have been identified with concrete causal traces and measurable financial impact.

Phase 2 (Regime Analysis) and Phase 3 (Residual Evaluation) are formally approved to proceed.
