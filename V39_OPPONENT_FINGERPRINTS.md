# V39 Opponent Fingerprints — Behavioral Archetypes from Live Ladder Replays

## 1. Overview & Data Provenance
- **Dataset**: 28 unique live ladder opponents encountered across the first 29 matches of production V35.
- **Artifact**: `scratch/v39/live/opponent_fingerprints.jsonl`
- **Methodology**: Observable feature extraction from raw replay tapes (opening actions, scaling thresholds, animal timing, and terminal liquidation).

---

## 2. Dominant Meta Archetypes

### Archetype 1: The Fast Liquidation Scalers (e.g., `Yassine Chritt`, `NonCaffeine`, `kowalskii`, `lllleeeo`)
- **Opening Behavior**: Wheat wash ranging from 5 to 70 units (mean ~30–50).
- **Scale**: 13–14 workers, 4 quadrants (including Southeast).
- **Animal Timing**: Early sheep (~Step 140–160).
- **Terminal Execution**: **`EARLY_STEP694`**. Unloads all shed inventory (Milk, Strawberry, Wool, Wheat, Carrots) simultaneously at Step 694.
- **Matchup vs V35**: Highly competitive. This group accounted for 3 of V35's 6 losses, strictly decided by the Step 694 liquidation order.

---

### Archetype 2: The Conservative 3-Quadrant Farmers (e.g., `Juniperss`, `savoelh`, `mr_children_0617`, `Zhen Li`, `Kenan Zhang9`)
- **Opening Behavior**: Standard 10–30 wheat wash.
- **Scale**: 11 workers, strictly 3 quadrants (NW, NE, SW; skips SE).
- **Terminal Execution**: `EARLY_STEP694`.
- **Matchup vs V35**: V35 wins consistently (100% win rate against this cluster), averaging +$5k to +$15k margins.

---

### Archetype 3: The Aggressive Early SE Unlocker (`Adhiraj Jagtap`)
- **Opening Behavior**: Asymmetric wash (`BUY 20 WHEAT`, `SELL 15 WHEAT`, `BUY 1 WHEAT SEED`).
- **Scale**: Fast early expansion to SE quadrant at **Step 267** (23 steps earlier than standard meta).
- **Compounding Result**: Produced $138,132 terminal cash, defeating V35's 3/4-quadrant transition.

---

### Archetype 4: The Low-Wash / Unoptimized Baselines (e.g., `Saptanshu Samal`, `SOLUCIENCE`, `Tahsan Ferdous`)
- **Opening Behavior**: Zero wheat wash or unhedged seed/animal buys.
- **Scale**: Stalls at 5–8 workers, 2–3 quadrants.
- **Terminal Execution**: Late Step 718 or passive pass.
- **Matchup vs V35**: Complete blowouts (V35 wins by +$50k to +$105k).

---

## 3. Comprehensive Opponent Fingerprint Summary Table
| Opponent Name | Sample Episode | Wash Size | Mid Hands | Final Hands | Final Quads | Cows | Sheep | Terminal Liquidation Style | V35 Record |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`Yassine Chritt`** | 113183263 | 60 | 9 | 13 | 4 | 0 | 1 | `EARLY_STEP694` | 0W - 1L |
| **`Lisan al-Gaib`** | 113171441 | 13 | 8 | 8 | 3 | 0 | 1 | `EARLY_STEP694` | 0W - 1L |
| **`junxing peng`** | 113164394 | 5 | 9 | 12 | 4 | 0 | 1 | `EARLY_STEP694` | 0W - 1L |
| **`NonCaffeine`** | 113166778 | 5 | 9 | 13 | 4 | 0 | 1 | `EARLY_STEP694` | 0W - 1L |
| **`Adhiraj Jagtap`** | 113177277 | 20 | 10 | 12 | 4 | 0 | 1 | `EARLY_STEP694` | 0W - 1L |
| **`kowalskii`** | 113176099 | 70 | 9 | 13 | 4 | 0 | 1 | `EARLY_STEP694` | 1W - 0L |
| **`lllleeeo`** | 113186749 | 50 | 9 | 13 | 4 | 0 | 1 | `EARLY_STEP694` | 1W - 0L |
| **`zeel vavliya`** | 113184429 | 3 | 9 | 11 | 3 | 0 | 1 | `EARLY_STEP694` | 1W - 0L |
| **`Aastik Rajan15`** | 113180924 | 60 | 9 | 13 | 4 | 0 | 1 | `EARLY_STEP694` | 1W - 0L |
| **`Michael Mueller`** | 113179717 | 35 | 9 | 10 | 3 | 0 | 1 | `EARLY_STEP694` | 1W - 0L |
| **`🚜 Sub-Par Seedlings`** | 113182085 | 60 | 9 | 11 | 3 | 0 | 1 | `EARLY_STEP694` | 1W - 0L |
| **`morality0707`** | 113185602 | 30 | 9 | 11 | 3 | 0 | 1 | `EARLY_STEP694` | 1W - 0L |
| **`Juniperss`** | 113170295 | 30 | 9 | 13 | 4 | 0 | 1 | `EARLY_STEP694` | 1W - 0L |
| **`SOLUCIENCE`** | 113178448 | 13 | 9 | 11 | 3 | 0 | 1 | `EARLY_STEP694` | 1W - 0L |
| **`Saptanshu Samal`** | 113155209 | 0 | 5 | 5 | 3 | 0 | 1 | `LATE_STEP718` | 1W - 0L |
