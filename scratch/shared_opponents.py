import os
import sys
import json
import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

v1_df = pd.read_csv("scratch/analyzed_episodes_55944418.csv")
v2_df = pd.read_csv("scratch/analyzed_episodes_55958978.csv")

v1_opp = pd.read_csv("scratch/opponent_breakdown_55944418.csv")
v2_opp = pd.read_csv("scratch/opponent_breakdown_55958978.csv")

print("=" * 80)
print("SHARED OPPONENTS ANALYSIS: V1 vs V2")
print("=" * 80)

shared_teams = set(v1_df['opp_team_id']).intersection(set(v2_df['opp_team_id']))
print(f"Total Unique Opponents V1 faced: {v1_df['opp_team_id'].nunique()}")
print(f"Total Unique Opponents V2 faced: {v2_df['opp_team_id'].nunique()}")
print(f"Total Shared Opponents: {len(shared_teams)}")

if shared_teams:
    shared_rows = []
    for team_id in shared_teams:
        t1 = v1_df[v1_df['opp_team_id'] == team_id]
        t2 = v2_df[v2_df['opp_team_id'] == team_id]
        
        t_name = t1.iloc[0]['opp_team_name']
        t_rank = t1.iloc[0]['opp_rank']
        t_score = t1.iloc[0]['opp_score']
        t_tier = t1.iloc[0]['opp_tier']
        
        v1_wr = t1['win'].mean() * 100
        v2_wr = t2['win'].mean() * 100
        diff = v2_wr - v1_wr
        
        shared_rows.append({
            'Opponent': t_name,
            'Rank': t_rank,
            'Score': t_score,
            'Tier': t_tier,
            'V1 Games': len(t1),
            'V1 WR': f"{v1_wr:.0f}%",
            'V1 Margin': f"{t1['margin'].mean():+,.0f}",
            'V2 Games': len(t2),
            'V2 WR': f"{v2_wr:.0f}%",
            'V2 Margin': f"{t2['margin'].mean():+,.0f}",
            'Difference (V2-V1)': f"{diff:+.0f}%"
        })
    shared_df = pd.DataFrame(shared_rows).sort_values(by=['Rank', 'Score'], ascending=[True, False]).reset_index(drop=True)
    print(shared_df.to_string(index=False))
else:
    print("\nNo direct shared opponents in the 39-40 game sample due to large player pool (7,306 teams).")
    print("Comparing statistical distributions of opponent strength and bot performance:")

print("\n" + "=" * 80)
print("OPPONENT STRENGTH DISTRIBUTION COMPARISON")
print("=" * 80)

print(f"{'Metric':<25} | {'V1 Opponents':<20} | {'V2 Opponents':<20}")
print("-" * 70)
print(f"{'Mean Opponent Score':<25} | {v1_df['opp_score'].mean():<20.1f} | {v2_df['opp_score'].mean():<20.1f}")
print(f"{'Median Opponent Score':<25} | {v1_df['opp_score'].median():<20.1f} | {v2_df['opp_score'].median():<20.1f}")
print(f"{'Max Opponent Score':<25} | {v1_df['opp_score'].max():<20.1f} | {v2_df['opp_score'].max():<20.1f}")
print(f"{'Min Opponent Score':<25} | {v1_df['opp_score'].min():<20.1f} | {v2_df['opp_score'].min():<20.1f}")
print(f"{'Opponents > 1000 Elo':<25} | {(v1_df['opp_score'] >= 1000).sum():<20} | {(v2_df['opp_score'] >= 1000).sum():<20}")
print(f"{'Opponents > 1200 Elo':<25} | {(v1_df['opp_score'] >= 1200).sum():<20} | {(v2_df['opp_score'] >= 1200).sum():<20}")

print("\n" + "=" * 80)
print("AGENT OUTPUT METRICS COMPARISON (Gold / Crop / Livestock Revenue)")
print("=" * 80)
print(f"{'Metric':<25} | {'V1 (Aethel-Prime)':<20} | {'V2 (Aethel-Refined)':<20}")
print("-" * 70)
print(f"{'Overall Win Rate':<25} | {v1_df['win'].mean()*100:<19.1f}% | {v2_df['win'].mean()*100:<19.1f}%")
print(f"{'Mean Reward':<25} | {v1_df['our_reward'].mean():<20,.0f} | {v2_df['our_reward'].mean():<20,.0f}")
print(f"{'Median Reward':<25} | {v1_df['our_reward'].median():<20,.0f} | {v2_df['our_reward'].median():<20,.0f}")
print(f"{'Opponent Mean Reward':<25} | {v1_df['opp_reward'].mean():<20,.0f} | {v2_df['opp_reward'].mean():<20,.0f}")
print(f"{'Mean Margin':<25} | {v1_df['margin'].mean():<+20,.0f} | {v2_df['margin'].mean():<+20,.0f}")

print("\n" + "=" * 80)
print("MATCHMAKING & ELO TRAJECTORY FORENSICS")
print("=" * 80)

print("\nV1 Progression (first 20 games, 21-40, 41-end):")
print(f"  Games 1-20:  WR {v1_df.iloc[:20]['win'].mean()*100:.1f}%, Mean Reward {v1_df.iloc[:20]['our_reward'].mean():,.0f}, Mean Opp {v1_df.iloc[:20]['opp_reward'].mean():,.0f}, Margin {v1_df.iloc[:20]['margin'].mean():+,.0f}")
print(f"  Games 21-40: WR {v1_df.iloc[20:40]['win'].mean()*100:.1f}%, Mean Reward {v1_df.iloc[20:40]['our_reward'].mean():,.0f}, Mean Opp {v1_df.iloc[20:40]['opp_reward'].mean():,.0f}, Margin {v1_df.iloc[20:40]['margin'].mean():+,.0f}")
if len(v1_df) > 40:
    print(f"  Games 41-{len(v1_df)}: WR {v1_df.iloc[40:]['win'].mean()*100:.1f}%, Mean Reward {v1_df.iloc[40:]['our_reward'].mean():,.0f}, Mean Opp {v1_df.iloc[40:]['opp_reward'].mean():,.0f}, Margin {v1_df.iloc[40:]['margin'].mean():+,.0f}")

print("\nV2 Progression (games 1-20, 21-end):")
print(f"  Games 1-20:  WR {v2_df.iloc[:20]['win'].mean()*100:.1f}%, Mean Reward {v2_df.iloc[:20]['our_reward'].mean():,.0f}, Mean Opp {v2_df.iloc[:20]['opp_reward'].mean():,.0f}, Margin {v2_df.iloc[:20]['margin'].mean():+,.0f}")
print(f"  Games 21-{len(v2_df)}: WR {v2_df.iloc[20:]['win'].mean()*100:.1f}%, Mean Reward {v2_df.iloc[20:]['our_reward'].mean():,.0f}, Mean Opp {v2_df.iloc[20:]['opp_reward'].mean():,.0f}, Margin {v2_df.iloc[20:]['margin'].mean():+,.0f}")

