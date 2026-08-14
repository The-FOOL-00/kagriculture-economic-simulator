"""
=============================================================================
UNTOUCHED HOLDOUT VALIDATION SCRIPT
=============================================================================
"""
from evaluate_suite import evaluate_matchup


def main():
    print(">>> RUNNING UNTOUCHED HOLDOUT VALIDATION (100 Matches vs Golden Control) <<<")
    res = evaluate_matchup("main.py", "agents/golden_v1.py", "benchmarks/seeds/holdout.txt", max_matches=100)

    print("\n" + "=" * 70)
    print(f"HOLDOUT VALIDATION SUMMARY (100 Matches on Seeds 20000–20099)")
    print("=" * 70)
    print(f"Matches:     {res['matches']}")
    print(f"Wins:        {res['wins']} ({res['win_rate']:.1f}%)")
    print(f"Losses:      {res['losses']}")
    print(f"95% CI:      [{res['ci_95'][0]:.1f}%, {res['ci_95'][1]:.1f}%]")
    print(f"Mean Cash:   ${res['mean_r0']:,.2f}")
    print(f"Opp Cash:    ${res['mean_r1']:,.2f}")
    print(f"Net Margin:  ${res['mean_diff']:,.2f}")
    print(f"Rating:      {res['classification']}")
    print("=" * 70)


if __name__ == "__main__":
    main()
