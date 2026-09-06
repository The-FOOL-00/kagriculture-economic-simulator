import pandas as pd
import json

df_v2 = pd.read_csv("scratch/opponent_breakdown_55958978.csv")
df_v1 = pd.read_csv("scratch/opponent_breakdown_55944418.csv")

def summarize_live_slot(df, name):
    total_games = df['Games'].sum()
    total_wins = df['Wins'].sum()
    total_losses = df['Losses'].sum()
    total_draws = df['Draws'].sum()
    win_rate = round(total_wins / total_games * 100, 2)
    
    mean_our = round(df['MeanOur'].mean(), 1)
    mean_opp = round(df['MeanOpp'].mean(), 1)
    mean_margin = round(df['MeanMargin'].mean(), 1)
    
    # By tier
    tier_stats = df.groupby('Tier').agg({
        'Games': 'sum',
        'Wins': 'sum',
        'Losses': 'sum',
        'MeanOur': 'mean',
        'MeanOpp': 'mean',
        'MeanMargin': 'mean'
    }).round(1)
    tier_stats['WinRate'] = (tier_stats['Wins'] / tier_stats['Games'] * 100).round(1)
    
    print(f"\n=======================================================")
    print(f"LIVE PERFORMANCE AUDIT: {name}")
    print(f"=======================================================")
    print(f"Total Games: {total_games} | Wins: {total_wins} | Losses: {total_losses} | Draws: {total_draws}")
    print(f"Win Rate: {win_rate}% | Mean Score: ${mean_our:,.1f} | Mean Opp: ${mean_opp:,.1f} | Net Margin: +${mean_margin:,.1f}")
    print("\nBreakdown by Opponent Tier:")
    print(tier_stats)
    
    return {
        "name": name,
        "total_games": int(total_games),
        "total_wins": int(total_wins),
        "total_losses": int(total_losses),
        "win_rate": float(win_rate),
        "mean_our_score": float(mean_our),
        "mean_opp_score": float(mean_opp),
        "mean_margin": float(mean_margin),
        "tier_breakdown": tier_stats.to_dict(orient="index")
    }

v2_summary = summarize_live_slot(df_v2, "Slot 2: Aethel-Refined V2 (55958978)")
v1_summary = summarize_live_slot(df_v1, "Slot 1: Aethel-Prime V1 (55944418)")

# Save artifact
df_v2.to_csv("scratch/current_v2_live_performance.csv", index=False)
with open("scratch/live_portfolio_summary.json", "w", encoding="utf-8") as f:
    json.dump({"v2": v2_summary, "v1": v1_summary}, f, indent=2)
