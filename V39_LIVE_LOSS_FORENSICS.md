# V39 Live Loss Forensics — Full Trajectory Reconstruction of V35 Failures

## 1. Executive Summary
From the full catalog of 29 live matches of the production candidate V35 (`56540535`, 1642.5 Elo), exactly **6 matches resulted in losses** (20.69% loss rate).
Using complete replay state reconstruction, each loss was dissected turn-by-turn to identify:
1. First divergence step
2. Physical and economic state preceding divergence
3. Root causal mechanism
4. Why the loss occurred and whether it was preventable.

---

## 2. Loss-by-Loss Forensic Timelines

### Case 1: Episode `113183263`
- **Opponent**: `Yassine Chritt`
- **Seed**: `124304182` | **Seat**: Seat 1
- **Final Result**: V35 $93,619 vs Opp $94,410 | **Deficit**: **-$791**
- **First Divergence Step**: **Step 694** (Day 28, Hour 22)
- **Pre-Divergence Trajectory**:
  - Day 01 (Step 24): V35 +$32 lead
  - Day 06 (Step 144): V35 +$93 lead
  - Day 12 (Step 288): V35 +$232 lead
  - Day 18 (Step 432): V35 +$178 lead
  - Day 24 (Step 576): V35 +$124 lead
  - Land Unlocks: Bit-identical (`NW`: 0, `NE`: 151, `SW`: 266, `SE`: 435)
  - Worker Hires: Bit-identical (14 workers each)
- **The Divergence Mechanism**:
  - At Step 694, V35 held `{'MILK': 8, 'STRAWBERRY': 17}` in its shed.
  - V35's static route tape scheduled only `[['SELL', 'WHEAT', 1000], ['SELL', 'CARROT', 1000], ['SELL', 'EGG', 4]]`.
  - Opponent (`Yassine Chritt`) issued a complete multi-good dump: `[['SELL', 'WHEAT', 1000], ['SELL', 'CARROT', 1000], ['SELL', 'MILK', 8], ['SELL', 'STRAWBERRY', 17], ['SELL', 'EGG', 4]]`.
  - Yassine captured the peak market price for Milk and Strawberries.
  - V35 delayed selling its Milk (8) and Strawberries (17) until Step 696 (2 steps later).
  - By Step 696, the market price of Strawberry and Milk had crashed from the opponent's sale.
  - Cash delta flipped at Step 696 from +$124 to **-$791**, and remained locked at -$791 for all 23 remaining steps to terminal Step 719.
- **Terminal Attribution**: 100% attributed to delayed Step 694 shed liquidation of Milk & Strawberry.

---

### Case 2: Episode `113171441`
- **Opponent**: `Lisan al-Gaib`
- **Seed**: `194590906` | **Seat**: Seat 1
- **Final Result**: V35 $74,297 vs Opp $75,293 | **Deficit**: **-$996**
- **First Divergence Step**: **Step 694**
- **Pre-Divergence Trajectory**:
  - Day 01: V35 +$17 lead
  - Day 03: V35 +$69 lead
  - Day 24 (Step 576): Deficit was only -$570
  - Workers & Land: Bit-identical (12 workers, 3 quadrants)
- **The Divergence Mechanism**:
  - At Step 694, V35 held `{'MILK': 4, 'STRAWBERRY': 16, 'WOOL': 3}` in its shed.
  - V35's market order at Step 694 sold only `[['SELL', 'EGG', 4], ['SELL', 'WHEAT', 1000], ['SELL', 'CARROT', 1000]]`.
  - Opponent (`Lisan al-Gaib`) sold `[['SELL', 'MILK', 8], ['SELL', 'STRAWBERRY', 20], ['SELL', 'WOOL', 3], ['SELL', 'WHEAT', 1000]]` at Step 694.
  - V35 sold its Milk, Strawberry, and Wool at Step 696 into a depressed market.
  - Price slippage cost V35 ~$950 in revenue.
  - Margin settled at -$996.
- **Terminal Attribution**: Step 694 shed liquidation delay.

---

### Case 3: Episode `113164394`
- **Opponent**: `junxing peng`
- **Seed**: `1722133329` | **Seat**: Seat 1
- **Final Result**: V35 $77,965 vs Opp $79,953 | **Deficit**: **-$1,988**
- **First Divergence Step**: **Step 576–694**
- **Pre-Divergence Trajectory**:
  - Day 12 (Step 288): V35 $14,630 vs Opp $14,639 (Diff: -$9)
  - Day 24 (Step 576): V35 $65,737 vs Opp $63,625 (**V35 was LEADING by +$2,112!**)
- **The Divergence Mechanism**:
  - At Step 694, V35 held `{'MILK': 6, 'STRAWBERRY': 17, 'WOOL': 10}` in its shed.
  - V35 failed to sell Milk, Strawberry, or Wool at Step 694.
  - Furthermore, at Step 697–699, V35 issued `['BUY_PRODUCT', 'WHEAT', 6], ['HIRE'], ['HIRE']`, burning -$639 on Day 29 hires that never produced a single unit.
  - Combined effect of unliquidated product delay and terminal burn flipped V35 from +$2.1k to -$1.98k.
- **Terminal Attribution**: Late liquidation omission + Day 29 useless hire burn.

---

### Case 4: Episode `113153701`
- **Opponent**: `Self-Play Validation (V35 vs V35)`
- **Seed**: `0` | **Seat**: Seat 0
- **Final Result**: V35 $67,695 vs V35 $68,335 | **Deficit**: **-$640**
- **First Divergence Step**: **Step 432–694**
- **Pre-Divergence Trajectory**:
  - Step 0 through 288: Bit-identical cash ($13,206 vs $13,206).
  - At Step 694, both agents held Milk, Strawberry, and Wool.
  - Seat 1 executed liquidation orders slightly ahead in market resolution due to tie-breaker order, creating a tiny $640 drift.
- **Terminal Attribution**: Deterministic seat order arbitrage on simultaneous market actions.

---

### Case 5: Episode `113166778`
- **Opponent**: `NonCaffeine`
- **Seed**: `2020456157` | **Seat**: Seat 1
- **Final Result**: V35 $132,705 vs Opp $134,952 | **Deficit**: **-$2,247**
- **First Divergence Step**: **Step 308** (Day 12, Hour 20)
- **Pre-Divergence Trajectory**:
  - Day 01: V35 +$9 lead
  - Step 288: V35 $15,434 vs Opp $15,860 (-$426)
  - Step 432: V35 $43,807 vs Opp $44,224 (-$417)
- **The Divergence Mechanism**:
  - Opponent opened with `[['BUY_PRODUCT', 'WHEAT', 5], ['BUY_SEED', 'WHEAT', 1]]` instead of full wash.
  - Opponent maintained a steady ~2% cash lead throughout midgame.
  - At Step 694, V35 held `{'MILK': 8, 'STRAWBERRY': 17, 'WOOL': 3}` in shed and failed to sell them.
  - The deficit widened from -$1.6k at Step 576 to -$2.2k at finish.
- **Terminal Attribution**: Mild opening/midgame pacing gap compounded by Step 694 delayed liquidation.

---

### Case 6: Episode `113177277`
- **Opponent**: `Adhiraj Jagtap`
- **Seed**: `203942858` | **Seat**: Seat 0
- **Final Result**: V35 $126,502 vs Opp $138,132 | **Deficit**: **-$11,630**
- **First Divergence Step**: **Step 196** (Day 8, Hour 4)
- **The Divergence Mechanism**:
  - At Step 1, Adhiraj executed `[['BUY_PRODUCT', 'WHEAT', 20], ['SELL', 'WHEAT', 15], ['BUY_SEED', 'WHEAT', 1]]` (net 5 wheat retained for immediate cow/worker support).
  - Adhiraj unlocked the 4th quadrant (**SE**) early at **Step 267** (Day 11, Hour 3), whereas V35 did not unlock SE until **Step 290** (Day 12, Hour 2).
  - Unlocking SE 23 turns earlier allowed Adhiraj to establish a full crop rotation one day earlier.
  - By Step 432, Adhiraj held a $9.6k lead ($52.5k vs $42.9k), which carried through to terminal liquidation.
- **Terminal Attribution**: Early SE land expansion timing ($1,000 threshold hit 23 steps earlier).
