# V39 Candidate Report — Targeted Endgame Liquidation Guard

## 1. Candidate Identification & Governance
* **Candidate ID**: `V39_LIVE_TARGETED`
* **Source Location**: [`candidates/v39_live_targeted/main.py`](file:///c:/Users/Sundareswaran/Kagriculture/candidates/v39_live_targeted/main.py)
* **Baseline Reference**: `V35_A7_OPENING` ([`candidates/v35_a7_opening/main.py`](file:///c:/Users/Sundareswaran/Kagriculture/candidates/v35_a7_opening/main.py), SHA-256 `1959021bdb1aeff720732aec866f5c9f3c9fa0b259ee0ab25982bda367593249`)
* **Live Submission Reference**: Submission `56540535` (1642.5 Elo, 29 games, 79.31% win rate)
* **Primary Objective**: Minimal deterministic intervention to eliminate late liquidation price slippage without downstream worker desynchronization or win casualties.
* **Submission Status**: **RESEARCH CANDIDATE ONLY — DO NOT SUBMIT** (Per strict instruction, V35 remains live on Kaggle).

---

## 2. Forensic Discovery: The Liquidation Gap
Across all 29 live matches of V35 on the active competition ladder:
1. **The Phenomenon**: In 100% of analyzed losses, V35 held perishable, high-value goods (`MILK`, `STRAWBERRY`, `WOOL`) in its shed at Step 693/694.
2. **The Disconnect**: V35's static route tape scheduled market sell orders only for Wheat, Carrot, and Egg at Step 694. It delayed selling Milk and Strawberry until Step 696.
3. **The Penalty**: Top opponents (`Yassine Chritt`, `Lisan al-Gaib`, `junxing peng`) dumped their full shed at Step 694 at peak prices ($37/strawberry, $19/milk). When V35 sold 2 turns later, market prices had crashed to $1, causing $600 to $1,500 in price slippage.
4. **The Margin Impact**: 4 of the 6 losses had margins under $2,000 (-$791, -$996, -$1,988, -$640).

---

## 3. Architecture & Intervention Mechanism

V39 wraps the frozen production V35 controller with a surgical, 2-turn safety guard:

```text
                           Step Observation
                                  │
                   ┌──────────────┴──────────────┐
                   │                             │
             Step in (693, 694)?            Other Steps (0..692, 695..719)
                   │                             │
           ┌───────┴───────┐                     │
          YES              NO                    │
           │               │                     │
    Shed contains          │                     │
  Milk/Straw/Wool?         │                     │
           │               │                     │
       ┌───┴───┐           │                     │
      YES      NO          │                     │
       │       │           │                     │
    Append     │           │                     │
  Sell Orders  │           │                     │
       │       │           │                     │
       └───────┼───────────┴─────────────────────┘
               │
               ▼
   100% Base V35 Execution
   (Fail-Closed Safety Gate)
```

### Deterministic Code Implementation
```python
if step in (693, 694):
    shed = observation.get("private", {}).get("shed", {})
    if shed:
        for item in ("STRAWBERRY", "MILK", "WOOL"):
            qty = shed.get(item, 0)
            if qty > 0 and item not in already_selling and len(mkt) < 10:
                mkt.append(["SELL", item, qty])
```

---

## 4. Invariant Guarantees
1. **Zero Worker Coupling**: Interacts exclusively with `action['market']`. Farmer paths and worker hand schedules are 100% untouched.
2. **Zero Order Bouncing**: Explicit check `len(mkt) < 10` prevents market buffer overflow.
3. **Strict Fail-Closed Fallback**: Any unexpected exception in the guard immediately returns the raw V35 action.
4. **Legally Observable**: Zero knowledge of seeds, opponent IDs, or future replay tapes.

---

## 5. Comprehensive Empirical Results

### A. Direct Head-to-Head: V39 vs V35 (20 Matches)
* **Matchup**: 10 Safe Seeds (5 Dev + 5 Fresh) $\times$ Both Seats
* **Score**: **20 Wins, 0 Losses, 0 Ties (100.0% Win Rate)**
* **Mean Margin**: **+$491.70**
* **Statistical Significance**: $p = 9.54 \times 10^{-7}$

### B. Paired Benchmark League Tournament (100 Matches)
* **Opponents**: `E2_A7`, `E1_V22R1`, `E8_DMITRII`, `V54`, `SYN_AGG`
* **V35 Baseline Wins**: 97 / 100 (97.0%)
* **V39 Candidate Wins**: **98 / 100 (98.0%)**
* **Rescues**: **1** (`E2_A7`, Seed 249679 Seat 0, converted from Loss to Win)
* **Casualties**: **0** (0 / 97 baseline wins compromised)
* **Mean Paired Cash Delta**: **+$67.59**
* **95% Bootstrap CI**: **[+$43.02, $+92.10]**

### C. Live Replay Counterfactual Gauntlet (17 Matches)
* **Target Losses Researched**: 6
* **Cash Recovered**: +$631 on Ep 113183263 (Yassine Chritt), +$604 on Ep 113164394, +$569 on Ep 113153701
* **Narrow Wins Preserved**: 11 / 11 (100.0%)
* **Live Replay Casualties**: 0
