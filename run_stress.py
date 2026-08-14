"""
=============================================================================
ADVERSARIAL STRESS TEST SCRIPT
=============================================================================
"""
from evaluate_suite import evaluate_matchup


def main():
    print(">>> RUNNING ADVERSARIAL STRESS TEST (50 Matches vs Golden Control) <<<")
    res = evaluate_matchup("main.py", "agents/golden_v1.py", "benchmarks/seeds/stress.txt", max_matches=50)

    print("\n" + "=" * 70)
    print(f"ADVERSARIAL STRESS SUMMARY (50 Matches on Seeds 30000–30049)")
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
