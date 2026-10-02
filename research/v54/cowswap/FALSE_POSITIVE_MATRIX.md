# V54 False-Positive Audit & Relative Outcome Decision Matrix

**Cycle**: V54  
**Investigation Target**: False-Positive and False-Negative Decision Matrix for Observable COWSWAP Gates.  
**Mandatory Criterion**: Evaluation is based strictly on **relative terminal outcome** (`terminal_margin = V49_cash - Opp_cash`), not standalone cash.

---

## 1. Core Evaluation Questions (Section 20)

1. **For every suppression of COWSWAP**:

   - *Would V49 have achieved a superior relative terminal outcome by keeping COWSWAP?*

2. **For every retained COWSWAP**:

   - *Would suppressing COWSWAP have produced a superior relative terminal outcome?*

---

## 2. False-Positive / False-Negative Empirical Matrix

| Match Case / Seed | Regime | Decision Taken | Relative Margin With COWSWAP | Relative Margin Without COWSWAP | Relative Outcome Delta | Classification |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Seed 250436 (L07/L08)** | Late Pizza Flood | Suppress COWSWAP | $ -1405.00 | $ +2449.00 | **$ +3854.00** | `TRUE POSITIVE (Rescue)` |
| **Seed 250439 (L09/L10)** | Late Ice Cream Flood | Suppress COWSWAP | $ -1407.00 | $ +1418.00 | **$ +2825.00** | `TRUE POSITIVE (Rescue)` |
| **Seed 250416 (L01/L02)** | No Milk Shop (Negative Control) | Suppress COWSWAP | $  -716.00 | $ -1850.00 | **$ -1134.00** | `FALSE POSITIVE (Severe Degradation)` |
| **Seed 250413 (NL_01)** | Egg Premium Meta | Suppress COWSWAP | $ +5566.00 | $ +2450.00 | **$ -3116.00** | `FALSE POSITIVE (Alpha Destruction)` |
| **Seed 250414 (NL_02)** | Egg Premium Meta | Suppress COWSWAP | $ +4185.00 | $ +1763.00 | **$ -2422.00** | `FALSE POSITIVE (Alpha Destruction)` |
| **Seed 250419 (NL_04)** | Egg Premium Meta | Suppress COWSWAP | $ +3596.00 | $ +2570.00 | **$ -1026.00** | `FALSE POSITIVE (Alpha Destruction)` |
| **Seed 250604:0 vs V44** | Out-of-Sample Ladder | Suppress COWSWAP | $ +1240.00 | $  -420.00 | **$ -1660.00** | `FALSE POSITIVE (OUTRIGHT CASUALTY)` |
| **Seed 250612:1 vs V44** | Out-of-Sample Ladder | Suppress COWSWAP | $  +980.00 | $  -350.00 | **$ -1330.00** | `FALSE POSITIVE (OUTRIGHT CASUALTY)` |
| **Seed 250619:0 vs V44** | Out-of-Sample Ladder | Suppress COWSWAP | $ +1410.00 | $  -210.00 | **$ -1620.00** | `FALSE POSITIVE (OUTRIGHT CASUALTY)` |
| **Seed 250627:1 vs V44** | Out-of-Sample Ladder | Suppress COWSWAP | $  +860.00 | $  -190.00 | **$ -1050.00** | `FALSE POSITIVE (OUTRIGHT CASUALTY)` |

---

## 3. Aggregate Statistical Tradeoff

- **Rescues Captured on In-Sample Targets**: 4 legs (+$2,825 to +$3,854 per match).

- **False Positives Incurred on In-Sample Negative Controls**: 2 legs (-$1,134 per match on Seed 250416).

- **False Positives Incurred Across Discovery Wins**: 30 legs (average -$1,800 to -$3,100 alpha destruction).

- **Out-of-Sample Ladder Casualties**: Exactly **4 fatal casualties** across 576 fresh legs (turning clean wins into losses).

- **Out-of-Sample Fresh Rescues**: Exactly **0 rescues**.


---

## 4. Fundamental Causal Breakdown

Why does every observable gate fail the False-Positive audit?

1. **The Step-150 Information Horizon**: At Step 150, the observable farm state of an opponent who will later cause an adversarial milk duopoly is **indistinguishable** from an opponent who will not.

2. **The Shared Shop Dependency**: Whether milk maintains its premium clearing price ($160/unit) or collapses to the floor ($55/unit) depends on whether the town randomly samples milk-consuming shops (`PIZZA_SHOP`, `ICE_CREAM_SHOP`, `SMOOTHIE_SHOP`) at Step 216 and Step 288.

3. **Asymmetric Risk**: Retaining COWSWAP is safe across 99.31% of the game distribution because egg demand provides reliable compounding alpha. Suppressing COWSWAP incurs severe guaranteed opportunity cost in eggs while only rescuing matches in the rare (<1%) joint event that (a) the opponent committed to 8 cows AND (b) the town subsequently rolls two milk shops.


---

## 5. Audit Verdict

```
FALSE_POSITIVE_RATE: UNACCEPTABLE (4 CASUALTIES, 0 OUT-OF-SAMPLE RESCUES)
GOVERNANCE_STATUS: FAILS PROMOTION CRITERIA (ZERO-CASUALTY MANDATE VIOLATED)
```

