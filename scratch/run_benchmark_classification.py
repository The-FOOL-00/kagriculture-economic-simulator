import json

with open('scratch/dynamic_opponent_suite_results.json', 'r') as f:
    dynamic_data = json.load(f)

classification = {
    "Live Flooder": "C. Dynamic Closed-Loop",
    "Adversarial Champion Killer": "C. Dynamic Closed-Loop",
    "Market Aggressor": "B. Synthetic Specialization",
    "Anti-Melon": "B. Synthetic Specialization",
    "Top Meta Adaptive": "C. Dynamic Closed-Loop",
    "Melon Specialist": "B. Synthetic Specialization",
    "Fast Crop": "B. Synthetic Specialization",
    "Replay Whyme Labs": "A. Frozen Historical Replay",
    "Replay Crop Dusta": "D. Real Extracted Competitor Replay"
}

print("==========================================================================================")
print("PHASE 1: BENCHMARK DESIGN AUDIT & SEPARATED OPPONENT CLASSIFICATION TABLES")
print("==========================================================================================")

for cat in sorted(set(classification.values())):
    opps_in_cat = [opp for opp, c in classification.items() if c == cat]
    print(f"\n### CATEGORY: {cat} (Opponents: {', '.join(opps_in_cat)})")
    print(f"{'Candidate':<25} | {'W-L-T':<10} | {'Win Rate':<10} | {'Cand Score':<15} | {'Mean Margin':<15}")
    print("-" * 85)
    for cand in ["Frozen V2", "CL-Aethel Prime", "CL-Aethel Grandmaster"]:
        per_opp = dynamic_data[cand]["per_opponent"]
        cat_wins = 0
        cat_losses = 0
        cat_ties = 0
        cat_scores = []
        cat_margins = []
        for opp in opps_in_cat:
            w, l, t = map(int, per_opp[opp]["W-L-T"].split('-'))
            cat_wins += w
            cat_losses += l
            cat_ties += t
            cat_scores.append(per_opp[opp]["mean_cand_score"])
            cat_margins.append(per_opp[opp]["mean_margin"])
        n_games = len(opps_in_cat) * 10
        wr = cat_wins / n_games
        mean_s = sum(cat_scores) / len(cat_scores)
        mean_m = sum(cat_margins) / len(cat_margins)
        wlt_str = f"{cat_wins}-{cat_losses}-{cat_ties}"
        print(f"{cand:<25} | {wlt_str:<10} | {wr*100:6.1f}%    | ${mean_s:>12.2f} | ${mean_m:>12.2f}")
