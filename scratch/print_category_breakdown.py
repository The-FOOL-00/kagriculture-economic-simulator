import json

with open("scratch/scoreboard_qualification_results.json") as f:
    res = json.load(f)

for match in res.get("matchups", []):
    if match.get("cand") == "CLOSED_LOOP_V2" and match.get("opp") == "DMITRII_BASE":
        print("=== CLOSED_LOOP_V2 vs DMITRII_BASE (QUALIFICATION) ===")
        print(f"Win Rate: {match['win_rate']*100:.1f}% ({match['wins']}W / {match['ties']}T / {match['losses']}L)")
        print(f"Mean Cash: Cand ${match['mean_cand_cash']:,.0f} vs Opp ${match['mean_opp_cash']:,.0f}")
        print(f"Mean Margin: ${match['mean_margin']:+,.2f} (95% CI: [${match['ci_lower']:+,.2f}, ${match['ci_upper']:+,.2f}])")
        print(f"Worst Loss: ${match['worst_loss']:+,.2f} | Best Win: ${match['best_win']:+,.2f}")
        print("\nCategory Breakdown:")
        for cat, data in match.get("category_breakdown", {}).items():
            print(f"  {cat:<12}: Wins {data['wins']}/{data['n']} ({data['win_rate']*100:.1f}%) | Margin: ${data['mean_margin']:+,.2f}")
        print("\nSeat Breakdown:")
        for seat, data in match.get("seat_breakdown", {}).items():
            print(f"  Seat {seat}: Wins {data['wins']}/{data['n']} ({data['win_rate']*100:.1f}%) | Margin: ${data['mean_margin']:+,.2f}")
