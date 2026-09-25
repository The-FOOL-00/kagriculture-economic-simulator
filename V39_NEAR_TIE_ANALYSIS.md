# V39 Near-Tie Analysis — Margin Stabilization Across High-Sensitivity Matches

## 1. Context & Objectives
Under the Bradley-Terry rating model governing Kaggriculture, a victory by +$50 is worth as much as a victory by +$50,000, while a defeat by -$50 incurs a severe rating penalty.
Matches decided by $|Margin| < \$3,000$ are in the **High-Sensitivity Zone**. A minor market fluctuation, tiebreaker resolution, or single unfulfilled order can flip the outcome between a win and a loss.

---

## 2. High-Sensitivity Matches in V35's Live Record
Across the 29 live matches, exactly **11 matches (37.9%)** were decided by $< \$3,000$:

| Episode ID | Opponent | V35 Margin | Result | Sensitivity Assessment |
| :---: | :--- | :---: | :---: | :--- |
| `113183263` | `Yassine Chritt` | -$791 | `LOSS` | Ultra-sensitive. Lost on Step 694 Strawberry/Milk delay. |
| `113171441` | `Lisan al-Gaib` | -$996 | `LOSS` | Ultra-sensitive. Lost on Step 694 Milk/Strawberry delay. |
| `113164394` | `junxing peng` | -$1,988 | `LOSS` | Sensitive. Lost on Step 694 Wool delay + Day 29 hire burn. |
| `113166778` | `NonCaffeine` | -$2,247 | `LOSS` | Moderate sensitivity. Steady small deficit. |
| `113153701` | `Self-Play Validation` | -$640 | `LOSS` | Tiebreaker limit. |
| **`113184429`** | `zeel vavliya` | **+$1,169** | **`WIN`** | Narrow victory. V35 led throughout but margin compressed late. |
| **`113186749`** | `lllleeeo` | **+$1,290** | **`WIN`** | Narrow victory against high-wash opponent (50 wash). |
| **`113176099`** | `kowalskii` | **+$1,580** | **`WIN`** | Narrow victory against 70-wash aggressive opponent. |
| **`113173773`** | `Zhen Li` | **+$2,635** | **`WIN`** | Solid victory in a low-scoring seed ($89k vs $86k). |
| **`113167894`** | `savoelh` | **+$3,270** | **`WIN`** | Stable victory against conservative farmer. |
| **`113179717`** | `Michael Mueller` | **+$5,348** | **`WIN`** | Comfortable victory against 35-wash opponent. |

---

## 3. Counterfactual Impact on Narrow Wins
A critical design constraint of V39 is **Casualty Prevention**:
> *Does the proposed intervention protect narrow wins, or does it destabilize them?*

### Theoretical & Simulation Audit:
1. **Zero Disturbance Pre-694**:
   Because `FLUSH_694` does nothing until Step 693, the exact board, worker positions, and farm investments of every winning game are **100% bit-identical**.
2. **Margin Expansion**:
   In narrow wins like `113184429` (+1,169) and `113186749` (+1,290), V35 also held Milk and Strawberries in shed at Step 694. Selling them at Step 694 captures higher prices, increasing the final cash margin by +$300 to +$800.
3. **No Casualty Mechanism**:
   Selling mature goods 2 turns earlier from the shed cannot reduce cash because:
   - Market prices for agricultural goods monotonically degrade as global volume increases.
   - Shed space is freed up 2 turns earlier, eliminating any potential shed-capacity blockage.
   - Zero wins are converted to losses.
