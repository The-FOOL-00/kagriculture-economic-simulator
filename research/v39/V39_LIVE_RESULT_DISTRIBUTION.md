# V39 Live Result Distribution — Ground-Truth Verified V35 Performance

## 1. Overall Outcome Distribution (N = 29)
| Outcome | Count | Percentage | Mean Bank (V35) | Mean Bank (Opp) | Mean Margin | Median Margin |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **WIN** | 23 | 79.31% | $117,390 | $90,131 | +$27,259 | +$10,291 |
| **LOSS** | 6 | 20.69% | $95,464 | $98,524 | -$3,060 | -$1,492 |
| **TIE** | 0 | 0.00% | — | — | — | — |
| **TOTAL** | **29** | **100.0%** | **$112,902** | **$91,732** | **+$21,170** | **+$6,909** |

---

## 2. Severity Classification Framework (Empirical Grounding)
Thresholds are grounded in the empirical distribution of the 29 live V35 competition matches:
- **Win Margins**:
  - `Large Win` ($Margin > \$50,000$): Blowout industrial dominance (4 matches).
  - `Medium Win` ($\$10,000 \le Margin \le \$50,000$): Solid compound growth victories (8 matches).
  - `Narrow Win` ($Margin < \$10,000$): Tense tactical games decided by late-game liquidation timing or micro-arbitrage (11 matches).
- **Loss Deficits** ($|Margin|$):
  - `Narrow Loss` ($Deficit < \$2,000$): 4 matches (66.7% of losses). Ultra-tight races decided by less than 2 turns of output.
  - `Medium Loss` ($\$2,000 \le Deficit \le \$10,000$): 1 match (16.7% of losses).
  - `Severe Loss` ($Deficit > \$10,000$): 1 match (16.7% of losses).

---

## 3. Stratified Breakdown

### A. Wins (N = 23)
| Tier | Criteria | Count | Share of Wins | Episodes | Representative Match |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **Large Win** | Margin > +$50,000 | 4 | 17.4% | `113155209` (+$105.7k), `113156362` (+$50.1k), `113157531` (+$51.9k), `113158665` (+$68.5k), `113178448` (+$101.6k) | SOLUCIENCE: $157.4k vs $55.8k (+101.6k) |
| **Medium Win** | +$10k to +$50k | 7 | 30.4% | `113159827` (+$30.7k), `113160962` (+$36.5k), `113162119` (+$25.1k), `113163245` (+$44.4k), `113165586` (+$13.4k), `113169085` (+$10.3k), `113182085` (+$41.5k) | 🚜 Sub-Par Seedlings: $158.4k vs $117.0k (+41.5k) |
| **Narrow Win** | Margin < +$10,000 | 12 | 52.2% | `113167894`, `113170295`, `113172595`, `113173773`, `113174935`, `113176099`, `113179717`, `113180924`, `113184429`, `113185602`, `113186749` | kowalskii: $125.8k vs $124.2k (+1,580); zeel vavliya: $135.6k vs $134.5k (+1,169) |

*Key Finding*: 52.2% of V35's wins are narrow (<$10k margin). V35's disciplined late-game liquidation and 25/25 wheat wash give it an edge in tight finishes across the ladder.

---

### B. Losses (N = 6)
| Tier | Criteria | Count | Share of Losses | Episode IDs | Opponents | Margin |
| :--- | :--- | :---: | :---: | :--- | :--- | :---: |
| **Narrow Loss** | Deficit < $2,000 | 4 | 66.7% | `113153701`, `113164394`, `113171441`, `113183263` | Self-Play (-$640), junxing peng (-$1,988), Lisan al-Gaib (-$996), Yassine Chritt (-$791) | **-$1,103.8** |
| **Medium Loss** | $2,000 to $10,000 | 1 | 16.7% | `113166778` | NonCaffeine (-$2,247) | **-$2,247.0** |
| **Severe Loss** | Deficit > $10,000 | 1 | 16.7% | `113177277` | Adhiraj Jagtap (-$11,630) | **-$11,630.0** |

*Key Finding*: **66.7% of all V35 losses are under $2,000 deficit**, and 83.3% are under $2,250! Only a single match in 29 games (`113177277`) exceeded an $11k deficit.

---

### C. Near-Tie / High-Sensitivity Zone ($|Margin| < \$3,000$)
There are **11 matches** (37.9% of the entire sample) in the ultra-sensitive $|Margin| < \$3,000$ band:
- **Narrow Losses (5 games)**:
  1. `113153701`: -$640 (Self-play validation)
  2. `113183263`: -$791 (Loss vs Yassine Chritt)
  3. `113171441`: -$996 (Loss vs Lisan al-Gaib)
  4. `113164394`: -$1,988 (Loss vs junxing peng)
  5. `113166778`: -$2,247 (Loss vs NonCaffeine)
- **Narrow Wins (6 games)**:
  6. `113184429`: +$1,169 (Win vs zeel vavliya)
  7. `113186749`: +$1,290 (Win vs lllleeeo)
  8. `113176099`: +$1,580 (Win vs kowalskii)
  9. `113173773`: +$2,635 (Win vs Zhen Li)
  10. `113167894`: +$3,270 (Win vs savoelh)
  11. `113179717`: +$5,348 (Win vs Michael Mueller)

**Strategic Implication**: A tiny deterministic intervention that increases terminal cash by just **+$1,000 to +$2,000** without disturbing earlier choreography could rescue up to **4 of the 6 losses** while solidifying narrow wins!
