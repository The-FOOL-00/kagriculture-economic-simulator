# V36 Pairing Audit: Complete Reconstruction of 120 Paired Matches

**Status:** COMPLETE & VERIFIED  
**Candidate Under Audit:** `V35_A7_OPENING` (`wash_buy=25, wash_sell=25`)  
**Baseline / Incumbent:** `A7_BASELINE` (`E9_AST` standalone)  
**Artifact Analyzed:** `benchmark_results.json` (SHA-256 verified)  
**Total Paired Matches:** 120 matches (10 seeds x 6 league opponents x 2 seats)  

---

## 1. Executive Summary & Verification Findings

1. **Exact 1-to-1 Matchup Pairing:** All 120 keys `(seed, opponent, seat)` match identically between `A7_BASELINE` and `V35_FULL`.
2. **Independently Recomputed Outcome Breakdown:**
   * **A7 Incumbent:**
     * Pure Wins (`cand_cash > opp_cash`): **100**
     * Pure Ties (`cand_cash == opp_cash`): **16**
     * Pure Losses (`cand_cash < opp_cash`): **4**
     * Tournament Points (Win=1.0, Tie=0.5): **108.0 / 120** (**90.00%**)
   * **V35 Candidate:**
     * Pure Wins (`cand_cash > opp_cash`): **117**
     * Pure Ties (`cand_cash == opp_cash`): **0**
     * Pure Losses (`cand_cash < opp_cash`): **3**
     * Tournament Points (Win=1.0, Tie=0.5): **117.0 / 120** (**97.50%**)
   * **Net Improvement:** **+9.0 tournament points (+7.50 percentage points)**.
3. **Casualty Audit:** **0 casualties** (no A7 win was degraded to a tie or loss; no paired match experienced negative cash delta).
4. **Rescue Audit:** **17 rescues** (16 A7 ties -> V35 wins; 1 A7 loss -> V35 win).
5. **Worst Paired Delta:** **+$0.00** across all 120 matches.
6. **Mean Paired Cash Delta:** **+$60.19** (median: **+$4.00**, max: **+$3339.00**).

---

## 2. Investigation of Harness Encoding: Wins, Losses, and Ties

The benchmark harness in `candidates/v35_a7_opening/run_expanded_validation.py` computes:
```python
win = 1.0 if cand_cash > opp_cash else (0.5 if cand_cash == opp_cash else 0.0)
```
In the summary table calculation:
```python
"wins": wins,                  # sum(x["win"] for x in legs) -> 108.0 for A7, 117.0 for V35
"losses": tot - int(wins),     # 120 - 108 = 12 for A7, 120 - 117 = 3 for V35
"ties": sum(1 for x in legs if x["win"] == 0.5) # 16 for A7, 0 for V35
```

### Forensic Finding on Summary Field Encoding:
* In standard tournament chess scoring, wins are worth 1.0 and draws/ties are worth 0.5.
* The summary field `"wins": 108.0` for A7 is **fractional tournament points**, NOT 108 pure wins.
* Specifically:
  $$\text{Tournament Points} = 100 \times 1.0 + 16 \times 0.5 + 4 \times 0.0 = 108.0$$
* The summary field `"losses": 12` represents **non-win points lost** ($120 - 108 = 12$), which comprises the 4 outright losses plus half-points dropped on 16 ties ($4 + 16 \times 0.5 = 12.0$).
* For V35, all 117 wins are **decisive pure wins**, 0 ties, and 3 pure losses ($117 \times 1.0 + 0 \times 0.5 = 117.0$, losses = 3).
* Therefore, the apparent discrepancy in the summary between "wins + losses = 120" while "ties = 16" is completely resolved: **ties were counted fractionally (0.5) in the win column and their lost half-points in the loss column.**

---

## 3. Transition Matrix (A7 -> V35)

| A7 Outcome | V35 Outcome | Match Count | Share of Total | Nature of Transition |
|:---|:---|:---:|:---:|:---|
| **WIN** | **WIN** | 100 | 83.33% | Retained Victory (Invariant / Accelerated) |
| **TIE** | **WIN** | 16 | 13.33% | Rescued Tie (Symmetry broken by Step-0 25/25 wash) |
| **LOSS** | **WIN** | 1 | 0.83% | Rescued Loss (Seed 249681 vs E2_A7, Seat 0) |
| **LOSS** | **LOSS** | 3 | 2.50% | Unmodified Structural Losses |
| **WIN** | **TIE** | 0 | 0.00% | *Zero Casualties* |
| **WIN** | **LOSS** | 0 | 0.00% | *Zero Casualties* |
| **TIE** | **LOSS** | 0 | 0.00% | *Zero Casualties* |

---

## 4. Recomputed Summary Comparison Table

| Metric | Raw A7 Recomputed | A7 Summary JSON | Raw V35 Recomputed | V35 Summary JSON | Discrepancy |
|:---|:---:|:---:|:---:|:---:|:---:|
| **Total Matches** | 120 | 120 | 120 | 120 | None |
| **Decisive Pure Wins** | 100 | -- | 117 | -- | Resolved (Fractional) |
| **Pure Ties** | 16 | 16 | 0 | 0 | None |
| **Pure Losses** | 4 | -- | 3 | -- | Resolved (Fractional) |
| **Tournament Win Pts** | 108.0 | 108.0 | 117.0 | 117.0 | None |
| **Win Rate** | 90.00% | 90.00% | 97.50% | 97.50% | None |
| **Rescued Non-Wins** | -- | -- | 17 | 17 | None |
| **Casualties** | -- | -- | 0 | 0 | None |
| **Mean Paired Cash Delta** | $0.00 | $0.00 | +$60.19 | +$60.19 | None |
| **Median Paired Delta** | $0.00 | $0.00 | +$4.00 | +$4.00 | None |
| **Worst Paired Delta** | $0.00 | $0.00 | +$0.00 | +$0.00 | None |

---

## 5. Complete 120 Paired Match Records

| # | Seed | Opponent | Seat | A7 Cash | Opp (vs A7) | A7 Result | V35 Cash | Opp (vs V35) | V35 Result | Paired Delta | Transition |
|---:|:---:|:---|:---:|---:|---:|:---:|---:|---:|:---:|---:|:---|
|   1 | 249675 | E0_V3      | 0 | $59,603 | $58,317 | WIN | $59,607 | $58,317 | WIN | +4 | WIN -> WIN |
|   2 | 249675 | E0_V3      | 1 | $59,603 | $58,317 | WIN | $59,607 | $58,317 | WIN | +4 | WIN -> WIN |
|   3 | 249676 | E0_V3      | 0 | $80,884 | $79,598 | WIN | $80,888 | $79,598 | WIN | +4 | WIN -> WIN |
|   4 | 249676 | E0_V3      | 1 | $80,884 | $79,598 | WIN | $80,888 | $79,598 | WIN | +4 | WIN -> WIN |
|   5 | 249677 | E0_V3      | 0 | $142,499 | $141,213 | WIN | $142,503 | $141,213 | WIN | +4 | WIN -> WIN |
|   6 | 249677 | E0_V3      | 1 | $142,499 | $141,213 | WIN | $142,503 | $141,213 | WIN | +4 | WIN -> WIN |
|   7 | 249678 | E0_V3      | 0 | $66,200 | $64,914 | WIN | $66,204 | $64,914 | WIN | +4 | WIN -> WIN |
|   8 | 249678 | E0_V3      | 1 | $66,200 | $64,914 | WIN | $66,204 | $64,914 | WIN | +4 | WIN -> WIN |
|   9 | 249679 | E0_V3      | 0 | $71,274 | $70,107 | WIN | $71,278 | $70,107 | WIN | +4 | WIN -> WIN |
|  10 | 249679 | E0_V3      | 1 | $71,393 | $69,988 | WIN | $71,397 | $69,988 | WIN | +4 | WIN -> WIN |
|  11 | 249680 | E0_V3      | 0 | $107,741 | $106,455 | WIN | $107,745 | $106,455 | WIN | +4 | WIN -> WIN |
|  12 | 249680 | E0_V3      | 1 | $107,741 | $106,455 | WIN | $107,745 | $106,455 | WIN | +4 | WIN -> WIN |
|  13 | 249681 | E0_V3      | 0 | $88,319 | $87,336 | WIN | $88,323 | $87,336 | WIN | +4 | WIN -> WIN |
|  14 | 249681 | E0_V3      | 1 | $88,622 | $87,033 | WIN | $88,626 | $87,033 | WIN | +4 | WIN -> WIN |
|  15 | 249682 | E0_V3      | 0 | $69,126 | $67,840 | WIN | $69,130 | $67,840 | WIN | +4 | WIN -> WIN |
|  16 | 249682 | E0_V3      | 1 | $69,126 | $67,840 | WIN | $69,130 | $67,840 | WIN | +4 | WIN -> WIN |
|  17 | 249683 | E0_V3      | 0 | $96,756 | $95,470 | WIN | $96,760 | $95,470 | WIN | +4 | WIN -> WIN |
|  18 | 249683 | E0_V3      | 1 | $96,756 | $95,470 | WIN | $96,760 | $95,470 | WIN | +4 | WIN -> WIN |
|  19 | 249684 | E0_V3      | 0 | $138,736 | $137,450 | WIN | $138,740 | $137,450 | WIN | +4 | WIN -> WIN |
|  20 | 249684 | E0_V3      | 1 | $138,736 | $137,450 | WIN | $138,740 | $137,450 | WIN | +4 | WIN -> WIN |
|  21 | 249675 | E1_V22R1   | 0 | $59,578 | $58,310 | WIN | $59,582 | $58,310 | WIN | +4 | WIN -> WIN |
|  22 | 249675 | E1_V22R1   | 1 | $59,578 | $58,310 | WIN | $59,582 | $58,310 | WIN | +4 | WIN -> WIN |
|  23 | 249676 | E1_V22R1   | 0 | $80,865 | $79,586 | WIN | $80,869 | $79,586 | WIN | +4 | WIN -> WIN |
|  24 | 249676 | E1_V22R1   | 1 | $80,865 | $79,586 | WIN | $80,869 | $79,586 | WIN | +4 | WIN -> WIN |
|  25 | 249677 | E1_V22R1   | 0 | $142,502 | $141,207 | WIN | $142,506 | $141,207 | WIN | +4 | WIN -> WIN |
|  26 | 249677 | E1_V22R1   | 1 | $142,502 | $141,207 | WIN | $142,506 | $141,207 | WIN | +4 | WIN -> WIN |
|  27 | 249678 | E1_V22R1   | 0 | $66,182 | $64,902 | WIN | $66,186 | $64,902 | WIN | +4 | WIN -> WIN |
|  28 | 249678 | E1_V22R1   | 1 | $66,043 | $64,776 | WIN | $66,047 | $64,776 | WIN | +4 | WIN -> WIN |
|  29 | 249679 | E1_V22R1   | 0 | $71,274 | $70,107 | WIN | $71,278 | $70,107 | WIN | +4 | WIN -> WIN |
|  30 | 249679 | E1_V22R1   | 1 | $71,393 | $69,988 | WIN | $71,397 | $69,988 | WIN | +4 | WIN -> WIN |
|  31 | 249680 | E1_V22R1   | 0 | $107,636 | $106,534 | WIN | $107,640 | $106,534 | WIN | +4 | WIN -> WIN |
|  32 | 249680 | E1_V22R1   | 1 | $107,636 | $106,534 | WIN | $107,640 | $106,534 | WIN | +4 | WIN -> WIN |
|  33 | 249681 | E1_V22R1   | 0 | $88,321 | $87,334 | WIN | $88,325 | $87,334 | WIN | +4 | WIN -> WIN |
|  34 | 249681 | E1_V22R1   | 1 | $88,624 | $87,031 | WIN | $88,628 | $87,031 | WIN | +4 | WIN -> WIN |
|  35 | 249682 | E1_V22R1   | 0 | $69,126 | $67,840 | WIN | $69,130 | $67,840 | WIN | +4 | WIN -> WIN |
|  36 | 249682 | E1_V22R1   | 1 | $69,126 | $67,840 | WIN | $69,130 | $67,840 | WIN | +4 | WIN -> WIN |
|  37 | 249683 | E1_V22R1   | 0 | $96,756 | $95,470 | WIN | $96,760 | $95,470 | WIN | +4 | WIN -> WIN |
|  38 | 249683 | E1_V22R1   | 1 | $96,756 | $95,470 | WIN | $96,760 | $95,470 | WIN | +4 | WIN -> WIN |
|  39 | 249684 | E1_V22R1   | 0 | $138,736 | $137,450 | WIN | $138,740 | $137,450 | WIN | +4 | WIN -> WIN |
|  40 | 249684 | E1_V22R1   | 1 | $138,736 | $137,450 | WIN | $138,740 | $137,450 | WIN | +4 | WIN -> WIN |
|  41 | 249675 | E2_A7      | 0 | $103,299 | $103,299 | TIE | $103,316 | $103,288 | WIN | +17 | TIE -> WIN |
|  42 | 249675 | E2_A7      | 1 | $103,299 | $103,299 | TIE | $103,316 | $103,288 | WIN | +17 | TIE -> WIN |
|  43 | 249676 | E2_A7      | 0 | $78,101 | $78,101 | TIE | $78,118 | $78,090 | WIN | +17 | TIE -> WIN |
|  44 | 249676 | E2_A7      | 1 | $78,101 | $78,101 | TIE | $78,118 | $78,090 | WIN | +17 | TIE -> WIN |
|  45 | 249677 | E2_A7      | 0 | $85,524 | $85,524 | TIE | $85,541 | $85,513 | WIN | +17 | TIE -> WIN |
|  46 | 249677 | E2_A7      | 1 | $85,524 | $85,524 | TIE | $85,541 | $85,513 | WIN | +17 | TIE -> WIN |
|  47 | 249678 | E2_A7      | 0 | $85,336 | $85,336 | TIE | $85,353 | $85,325 | WIN | +17 | TIE -> WIN |
|  48 | 249678 | E2_A7      | 1 | $85,336 | $85,336 | TIE | $85,353 | $85,325 | WIN | +17 | TIE -> WIN |
|  49 | 249679 | E2_A7      | 0 | $73,402 | $73,525 | LOSS | $73,419 | $73,514 | LOSS | +17 | LOSS -> LOSS |
|  50 | 249679 | E2_A7      | 1 | $73,525 | $73,402 | WIN | $73,542 | $73,391 | WIN | +17 | WIN -> WIN |
|  51 | 249680 | E2_A7      | 0 | $109,366 | $109,366 | TIE | $109,383 | $109,355 | WIN | +17 | TIE -> WIN |
|  52 | 249680 | E2_A7      | 1 | $109,366 | $109,366 | TIE | $109,383 | $109,355 | WIN | +17 | TIE -> WIN |
|  53 | 249681 | E2_A7      | 0 | $92,826 | $93,016 | LOSS | $96,164 | $92,235 | WIN | +3,338 | LOSS -> WIN |
|  54 | 249681 | E2_A7      | 1 | $93,016 | $92,826 | WIN | $96,355 | $92,044 | WIN | +3,339 | WIN -> WIN |
|  55 | 249682 | E2_A7      | 0 | $74,331 | $74,331 | TIE | $74,348 | $74,320 | WIN | +17 | TIE -> WIN |
|  56 | 249682 | E2_A7      | 1 | $74,331 | $74,331 | TIE | $74,348 | $74,320 | WIN | +17 | TIE -> WIN |
|  57 | 249683 | E2_A7      | 0 | $96,416 | $96,416 | TIE | $96,433 | $96,405 | WIN | +17 | TIE -> WIN |
|  58 | 249683 | E2_A7      | 1 | $96,416 | $96,416 | TIE | $96,433 | $96,405 | WIN | +17 | TIE -> WIN |
|  59 | 249684 | E2_A7      | 0 | $103,184 | $103,184 | TIE | $103,201 | $103,173 | WIN | +17 | TIE -> WIN |
|  60 | 249684 | E2_A7      | 1 | $103,184 | $103,184 | TIE | $103,201 | $103,173 | WIN | +17 | TIE -> WIN |
|  61 | 249675 | E8_DMITRII | 0 | $66,903 | $59,114 | WIN | $66,907 | $59,107 | WIN | +4 | WIN -> WIN |
|  62 | 249675 | E8_DMITRII | 1 | $66,903 | $59,114 | WIN | $66,907 | $59,107 | WIN | +4 | WIN -> WIN |
|  63 | 249676 | E8_DMITRII | 0 | $95,512 | $88,620 | WIN | $95,516 | $88,613 | WIN | +4 | WIN -> WIN |
|  64 | 249676 | E8_DMITRII | 1 | $95,512 | $88,620 | WIN | $95,516 | $88,613 | WIN | +4 | WIN -> WIN |
|  65 | 249677 | E8_DMITRII | 0 | $92,592 | $93,759 | LOSS | $92,596 | $93,752 | LOSS | +4 | LOSS -> LOSS |
|  66 | 249677 | E8_DMITRII | 1 | $92,592 | $93,759 | LOSS | $92,596 | $93,752 | LOSS | +4 | LOSS -> LOSS |
|  67 | 249678 | E8_DMITRII | 0 | $106,799 | $104,059 | WIN | $106,803 | $104,052 | WIN | +4 | WIN -> WIN |
|  68 | 249678 | E8_DMITRII | 1 | $106,799 | $104,059 | WIN | $106,803 | $104,052 | WIN | +4 | WIN -> WIN |
|  69 | 249679 | E8_DMITRII | 0 | $72,124 | $69,049 | WIN | $72,128 | $69,042 | WIN | +4 | WIN -> WIN |
|  70 | 249679 | E8_DMITRII | 1 | $94,638 | $90,104 | WIN | $94,642 | $90,097 | WIN | +4 | WIN -> WIN |
|  71 | 249680 | E8_DMITRII | 0 | $70,910 | $68,339 | WIN | $70,914 | $68,332 | WIN | +4 | WIN -> WIN |
|  72 | 249680 | E8_DMITRII | 1 | $70,910 | $68,339 | WIN | $70,914 | $68,332 | WIN | +4 | WIN -> WIN |
|  73 | 249681 | E8_DMITRII | 0 | $76,807 | $72,880 | WIN | $76,811 | $72,873 | WIN | +4 | WIN -> WIN |
|  74 | 249681 | E8_DMITRII | 1 | $62,413 | $57,699 | WIN | $62,417 | $57,692 | WIN | +4 | WIN -> WIN |
|  75 | 249682 | E8_DMITRII | 0 | $76,250 | $68,285 | WIN | $76,254 | $68,278 | WIN | +4 | WIN -> WIN |
|  76 | 249682 | E8_DMITRII | 1 | $76,250 | $68,285 | WIN | $76,254 | $68,278 | WIN | +4 | WIN -> WIN |
|  77 | 249683 | E8_DMITRII | 0 | $121,281 | $119,693 | WIN | $121,285 | $119,686 | WIN | +4 | WIN -> WIN |
|  78 | 249683 | E8_DMITRII | 1 | $121,281 | $119,693 | WIN | $121,285 | $119,686 | WIN | +4 | WIN -> WIN |
|  79 | 249684 | E8_DMITRII | 0 | $131,772 | $130,960 | WIN | $131,776 | $130,953 | WIN | +4 | WIN -> WIN |
|  80 | 249684 | E8_DMITRII | 1 | $131,772 | $130,960 | WIN | $131,776 | $130,953 | WIN | +4 | WIN -> WIN |
|  81 | 249675 | SYN_AGG    | 0 | $144,114 | $3,000 | WIN | $144,114 | $3,000 | WIN | +0 | WIN -> WIN |
|  82 | 249675 | SYN_AGG    | 1 | $144,114 | $3,000 | WIN | $144,114 | $3,000 | WIN | +0 | WIN -> WIN |
|  83 | 249676 | SYN_AGG    | 0 | $148,390 | $3,000 | WIN | $148,390 | $3,000 | WIN | +0 | WIN -> WIN |
|  84 | 249676 | SYN_AGG    | 1 | $148,390 | $3,000 | WIN | $148,390 | $3,000 | WIN | +0 | WIN -> WIN |
|  85 | 249677 | SYN_AGG    | 0 | $189,650 | $3,000 | WIN | $189,650 | $3,000 | WIN | +0 | WIN -> WIN |
|  86 | 249677 | SYN_AGG    | 1 | $189,650 | $3,000 | WIN | $189,650 | $3,000 | WIN | +0 | WIN -> WIN |
|  87 | 249678 | SYN_AGG    | 0 | $182,752 | $3,000 | WIN | $182,752 | $3,000 | WIN | +0 | WIN -> WIN |
|  88 | 249678 | SYN_AGG    | 1 | $182,752 | $3,000 | WIN | $182,752 | $3,000 | WIN | +0 | WIN -> WIN |
|  89 | 249679 | SYN_AGG    | 0 | $163,086 | $3,000 | WIN | $163,086 | $3,000 | WIN | +0 | WIN -> WIN |
|  90 | 249679 | SYN_AGG    | 1 | $170,342 | $3,000 | WIN | $170,342 | $3,000 | WIN | +0 | WIN -> WIN |
|  91 | 249680 | SYN_AGG    | 0 | $180,469 | $3,000 | WIN | $180,469 | $3,000 | WIN | +0 | WIN -> WIN |
|  92 | 249680 | SYN_AGG    | 1 | $180,469 | $3,000 | WIN | $180,469 | $3,000 | WIN | +0 | WIN -> WIN |
|  93 | 249681 | SYN_AGG    | 0 | $90,009 | $3,000 | WIN | $90,009 | $3,000 | WIN | +0 | WIN -> WIN |
|  94 | 249681 | SYN_AGG    | 1 | $106,094 | $3,000 | WIN | $106,094 | $3,000 | WIN | +0 | WIN -> WIN |
|  95 | 249682 | SYN_AGG    | 0 | $172,009 | $3,000 | WIN | $172,009 | $3,000 | WIN | +0 | WIN -> WIN |
|  96 | 249682 | SYN_AGG    | 1 | $172,009 | $3,000 | WIN | $172,009 | $3,000 | WIN | +0 | WIN -> WIN |
|  97 | 249683 | SYN_AGG    | 0 | $200,039 | $3,000 | WIN | $200,039 | $3,000 | WIN | +0 | WIN -> WIN |
|  98 | 249683 | SYN_AGG    | 1 | $200,039 | $3,000 | WIN | $200,039 | $3,000 | WIN | +0 | WIN -> WIN |
|  99 | 249684 | SYN_AGG    | 0 | $154,812 | $3,000 | WIN | $154,812 | $3,000 | WIN | +0 | WIN -> WIN |
| 100 | 249684 | SYN_AGG    | 1 | $154,812 | $3,000 | WIN | $154,812 | $3,000 | WIN | +0 | WIN -> WIN |
| 101 | 249675 | V54        | 0 | $97,358 | $84,292 | WIN | $97,358 | $84,292 | WIN | +0 | WIN -> WIN |
| 102 | 249675 | V54        | 1 | $97,358 | $84,292 | WIN | $97,358 | $84,292 | WIN | +0 | WIN -> WIN |
| 103 | 249676 | V54        | 0 | $106,910 | $98,078 | WIN | $106,910 | $98,078 | WIN | +0 | WIN -> WIN |
| 104 | 249676 | V54        | 1 | $106,910 | $98,078 | WIN | $106,910 | $98,078 | WIN | +0 | WIN -> WIN |
| 105 | 249677 | V54        | 0 | $92,296 | $69,146 | WIN | $92,296 | $69,146 | WIN | +0 | WIN -> WIN |
| 106 | 249677 | V54        | 1 | $92,296 | $69,146 | WIN | $92,296 | $69,146 | WIN | +0 | WIN -> WIN |
| 107 | 249678 | V54        | 0 | $119,658 | $111,081 | WIN | $119,658 | $111,081 | WIN | +0 | WIN -> WIN |
| 108 | 249678 | V54        | 1 | $119,658 | $111,081 | WIN | $119,658 | $111,081 | WIN | +0 | WIN -> WIN |
| 109 | 249679 | V54        | 0 | $94,267 | $79,034 | WIN | $94,267 | $79,034 | WIN | +0 | WIN -> WIN |
| 110 | 249679 | V54        | 1 | $108,636 | $75,938 | WIN | $108,636 | $75,938 | WIN | +0 | WIN -> WIN |
| 111 | 249680 | V54        | 0 | $80,355 | $65,834 | WIN | $80,355 | $65,834 | WIN | +0 | WIN -> WIN |
| 112 | 249680 | V54        | 1 | $80,355 | $65,834 | WIN | $80,355 | $65,834 | WIN | +0 | WIN -> WIN |
| 113 | 249681 | V54        | 0 | $90,373 | $55,193 | WIN | $90,373 | $55,193 | WIN | +0 | WIN -> WIN |
| 114 | 249681 | V54        | 1 | $102,357 | $54,476 | WIN | $102,357 | $54,476 | WIN | +0 | WIN -> WIN |
| 115 | 249682 | V54        | 0 | $93,047 | $79,159 | WIN | $93,047 | $79,159 | WIN | +0 | WIN -> WIN |
| 116 | 249682 | V54        | 1 | $93,047 | $79,159 | WIN | $93,047 | $79,159 | WIN | +0 | WIN -> WIN |
| 117 | 249683 | V54        | 0 | $87,118 | $70,880 | WIN | $87,118 | $70,880 | WIN | +0 | WIN -> WIN |
| 118 | 249683 | V54        | 1 | $87,118 | $70,880 | WIN | $87,118 | $70,880 | WIN | +0 | WIN -> WIN |
| 119 | 249684 | V54        | 0 | $108,687 | $73,293 | WIN | $108,687 | $73,293 | WIN | +0 | WIN -> WIN |
| 120 | 249684 | V54        | 1 | $108,687 | $73,293 | WIN | $108,687 | $73,293 | WIN | +0 | WIN -> WIN |

---

## 6. Audit Conclusion for Phase 1

1. **Reconstruction Accuracy:** The paired match records reconstructed directly from raw simulation terminal rewards completely confirm the reported 108.0 vs 117.0 win points (+7.50 percentage points).
2. **Zero Inversion Artifacts:** There are no inverted records, duplicate keys, or missing legs.
3. **No Casualties:** Zero A7 wins were sacrificed.
4. **Exact Mechanism of the 17 Rescues:** 16 ties converted to wins and 1 loss converted to win. All 17 occurred against mirror opponent `E2_A7`.
