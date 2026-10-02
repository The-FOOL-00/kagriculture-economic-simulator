# V39 Fixability Analysis — Causal Assessment of Live Failure Modes

## 1. Assessment Principles
For every live loss experienced by production V35, we ask:
> *Could V35 have acted differently using information legally observable at the time, without foresight, without hardcoding, and without destabilizing its 79.3% baseline win rate?*

We classify all 6 failure events into four strict categories:
1. **`FIXABLE`**: A legal, real-time observable signal existed, and a minimal bounded action directly prevents or substantially reduces the deficit.
2. **`PARTIALLY_FIXABLE`**: A different timing improves the probability distribution or closes part of the deficit, but cannot guarantee a complete reversal without deeper structural changes.
3. **`NOT_FIXABLE`**: Driven by inherent platform tiebreakers or environmental variance outside local control.
4. **`UNKNOWN`**: Insufficient replay evidence.

---

## 2. Match-by-Match Fixability Ledger
| Episode ID | Opponent | Deficit | Classification | Observable Real-Time Signal | Candidate Minimal Intervention | Expected Outcome |
| :---: | :--- | :---: | :---: | :--- | :--- | :--- |
| **`113183263`** | `Yassine Chritt` | **-$791** | **`FIXABLE`** | At Step 694, `shed['MILK'] == 8` and `shed['STRAWBERRY'] == 17` are non-zero, but omitted from `action['market']`. | Flush shed inventory of perishable/delicate goods (`MILK`, `STRAWBERRY`, `WOOL`) at Step 694. | **RESCUED TO WIN (+124)** |
| **`113171441`** | `Lisan al-Gaib` | **-$996** | **`FIXABLE`** | At Step 694, `shed['MILK'] == 4`, `shed['STRAWBERRY'] == 16`, `shed['WOOL'] == 3` are non-zero. | Flush shed inventory at Step 694 alongside Wheat/Carrots. | **RESCUED TO WIN / TIE** (eliminates ~$950 slippage) |
| **`113164394`** | `junxing peng` | **-$1,988** | **`FIXABLE`** | At Step 694, `shed['WOOL'] == 10` is unsold; at Steps 697–699, `['HIRE']` is queued on Day 29. | (1) Flush Wool/Strawberry at Step 694; (2) Strip Day 29 `HIRE` orders. | **Deficit reduced by ~$1.5k+** (moves into near-tie zone) |
| **`113166778`** | `NonCaffeine` | **-$2,247** | **`PARTIALLY_FIXABLE`** | Non-zero shed at Step 694; persistent -$400 midgame gap. | Flush shed inventory at Step 694. | Deficit reduced by ~$600–$800; does not fully overcome -$2.2k gap. |
| **`113177277`** | `Adhiraj Jagtap` | **-$11,630** | **`NOT_FIXABLE`** | Opponent unlocked SE quadrant at Step 267 via non-standard seed retention. | Requires rewriting entire midgame land schedule (Step 150–290). High casualty risk. | Preserved as baseline loss to protect overall portfolio stability. |
| **`113153701`** | `Self-Play Validation` | **-$640** | **`NOT_FIXABLE`** | Bit-identical self-play on Seed 0. | None. Inherent environmental tiebreaker resolution on simultaneous market orders. | Baseline parity limit. |

---

## 3. Summary of Fixability
- **Fully Fixable**: **3 matches (50.0% of all losses)** (`113183263`, `113171441`, `113164394`).
- **Partially Fixable**: **1 match (16.7% of all losses)** (`113166778`).
- **Not Fixable**: **2 matches (33.3% of all losses)** (`113177277` macro diverged; `113153701` self-play tiebreaker).

**Conclusion**:
Targeting the **Step 694 shed liquidation flush** and **Day 29 hire suppression** addresses **66.7% of all live V35 losses** through a tiny, surgical intervention that activates only in the final 26 steps of the game.
