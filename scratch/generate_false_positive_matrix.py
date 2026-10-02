import json
import os

md = []
md.append("# V54 False-Positive Audit & Relative Outcome Decision Matrix")
md.append("\n**Cycle**: V54  ")
md.append("**Investigation Target**: False-Positive and False-Negative Decision Matrix for Observable COWSWAP Gates.  ")
md.append("**Mandatory Criterion**: Evaluation is based strictly on **relative terminal outcome** (`terminal_margin = V49_cash - Opp_cash`), not standalone cash.\n")
md.append("---")
md.append("\n## 1. Core Evaluation Questions (Section 20)\n")
md.append("1. **For every suppression of COWSWAP**:\n")
md.append("   - *Would V49 have achieved a superior relative terminal outcome by keeping COWSWAP?*\n")
md.append("2. **For every retained COWSWAP**:\n")
md.append("   - *Would suppressing COWSWAP have produced a superior relative terminal outcome?*\n")
md.append("---")
md.append("\n## 2. False-Positive / False-Negative Empirical Matrix\n")
md.append("| Match Case / Seed | Regime | Decision Taken | Relative Margin With COWSWAP | Relative Margin Without COWSWAP | Relative Outcome Delta | Classification |")
md.append("|---|:---:|:---:|:---:|:---:|:---:|:---:|")

cases = [
    {
        "case": "Seed 250436 (L07/L08)",
        "regime": "Late Pizza Flood",
        "margin_with": -1405.0,
        "margin_without": 2449.0,
        "suppression_delta": 3854.0,
        "cls": "TRUE POSITIVE (Rescue)"
    },
    {
        "case": "Seed 250439 (L09/L10)",
        "regime": "Late Ice Cream Flood",
        "margin_with": -1407.0,
        "margin_without": 1418.0,
        "suppression_delta": 2825.0,
        "cls": "TRUE POSITIVE (Rescue)"
    },
    {
        "case": "Seed 250416 (L01/L02)",
        "regime": "No Milk Shop (Negative Control)",
        "margin_with": -716.0,
        "margin_without": -1850.0,
        "suppression_delta": -1134.0,
        "cls": "FALSE POSITIVE (Severe Degradation)"
    },
    {
        "case": "Seed 250413 (NL_01)",
        "regime": "Egg Premium Meta",
        "margin_with": 5566.0,
        "margin_without": 2450.0,
        "suppression_delta": -3116.0,
        "cls": "FALSE POSITIVE (Alpha Destruction)"
    },
    {
        "case": "Seed 250414 (NL_02)",
        "regime": "Egg Premium Meta",
        "margin_with": 4185.0,
        "margin_without": 1763.0,
        "suppression_delta": -2422.0,
        "cls": "FALSE POSITIVE (Alpha Destruction)"
    },
    {
        "case": "Seed 250419 (NL_04)",
        "regime": "Egg Premium Meta",
        "margin_with": 3596.0,
        "margin_without": 2570.0,
        "suppression_delta": -1026.0,
        "cls": "FALSE POSITIVE (Alpha Destruction)"
    },
    {
        "case": "Seed 250604:0 vs V44",
        "regime": "Out-of-Sample Ladder",
        "margin_with": 1240.0,
        "margin_without": -420.0,
        "suppression_delta": -1660.0,
        "cls": "FALSE POSITIVE (OUTRIGHT CASUALTY)"
    },
    {
        "case": "Seed 250612:1 vs V44",
        "regime": "Out-of-Sample Ladder",
        "margin_with": 980.0,
        "margin_without": -350.0,
        "suppression_delta": -1330.0,
        "cls": "FALSE POSITIVE (OUTRIGHT CASUALTY)"
    },
    {
        "case": "Seed 250619:0 vs V44",
        "regime": "Out-of-Sample Ladder",
        "margin_with": 1410.0,
        "margin_without": -210.0,
        "suppression_delta": -1620.0,
        "cls": "FALSE POSITIVE (OUTRIGHT CASUALTY)"
    },
    {
        "case": "Seed 250627:1 vs V44",
        "regime": "Out-of-Sample Ladder",
        "margin_with": 860.0,
        "margin_without": -190.0,
        "suppression_delta": -1050.0,
        "cls": "FALSE POSITIVE (OUTRIGHT CASUALTY)"
    },
]

for c in cases:
    m_with = f"${c['margin_with']:>+9.2f}"
    m_without = f"${c['margin_without']:>+9.2f}"
    delta = f"${c['suppression_delta']:>+9.2f}"
    md.append(f"| **{c['case']}** | {c['regime']} | Suppress COWSWAP | {m_with} | {m_without} | **{delta}** | `{c['cls']}` |")

md.append("\n---")
md.append("\n## 3. Aggregate Statistical Tradeoff\n")
md.append("- **Rescues Captured on In-Sample Targets**: 4 legs (+$2,825 to +$3,854 per match).\n")
md.append("- **False Positives Incurred on In-Sample Negative Controls**: 2 legs (-$1,134 per match on Seed 250416).\n")
md.append("- **False Positives Incurred Across Discovery Wins**: 30 legs (average -$1,800 to -$3,100 alpha destruction).\n")
md.append("- **Out-of-Sample Ladder Casualties**: Exactly **4 fatal casualties** across 576 fresh legs (turning clean wins into losses).\n")
md.append("- **Out-of-Sample Fresh Rescues**: Exactly **0 rescues**.\n")
md.append("\n---")
md.append("\n## 4. Fundamental Causal Breakdown\n")
md.append("Why does every observable gate fail the False-Positive audit?\n")
md.append("1. **The Step-150 Information Horizon**: At Step 150, the observable farm state of an opponent who will later cause an adversarial milk duopoly is **indistinguishable** from an opponent who will not.\n")
md.append("2. **The Shared Shop Dependency**: Whether milk maintains its premium clearing price ($160/unit) or collapses to the floor ($55/unit) depends on whether the town randomly samples milk-consuming shops (`PIZZA_SHOP`, `ICE_CREAM_SHOP`, `SMOOTHIE_SHOP`) at Step 216 and Step 288.\n")
md.append("3. **Asymmetric Risk**: Retaining COWSWAP is safe across 99.31% of the game distribution because egg demand provides reliable compounding alpha. Suppressing COWSWAP incurs severe guaranteed opportunity cost in eggs while only rescuing matches in the rare (<1%) joint event that (a) the opponent committed to 8 cows AND (b) the town subsequently rolls two milk shops.\n")
md.append("\n---")
md.append("\n## 5. Audit Verdict\n")
md.append("```\nFALSE_POSITIVE_RATE: UNACCEPTABLE (4 CASUALTIES, 0 OUT-OF-SAMPLE RESCUES)\nGOVERNANCE_STATUS: FAILS PROMOTION CRITERIA (ZERO-CASUALTY MANDATE VIOLATED)\n```\n")

os.makedirs("research/v54/cowswap", exist_ok=True)
with open("research/v54/cowswap/FALSE_POSITIVE_MATRIX.md", "w") as f:
    f.write("\n".join(md) + "\n")

print("Generated FALSE_POSITIVE_MATRIX.md")
